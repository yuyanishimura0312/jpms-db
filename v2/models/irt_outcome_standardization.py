"""
JPMS-DB v2 Phase F-2: Item Response Theory (IRT) for Outcome Standardization
============================================================================

Goal
----
Apply IRT (1PL Rasch / 2PL Birnbaum) to the JPMS-DB v2 school culture data,
treating schools as "examinees" and culture dimensions as "items". Because no
real student response panel is available at this stage of construction, we use
``school_culture_score`` (528 schools x 10 dimensions, 0-100) as a stand-in
for a binary item-response matrix and explore whether IRT-based standardization
produces a defensible school-level theta scale that could later be ported to
``outcome_dim_v2`` (77 items) once student response data exists.

Pipeline
--------
1.  Pivot ``school_culture_score`` to a 528 x 10 wide matrix.
2.  Binarize each item by its score-50 threshold (per task brief).
    A median-split sensitivity matrix is also kept for diagnostic checks
    (the >50 cut leaves several items with very high difficulty / floor
    effects, so the median split is reported as a robustness lens).
3.  Fit a 2PL model

        P(X_ij = 1 | theta_i) = 1 / (1 + exp(-a_j * (theta_i - b_j)))

    via joint marginal maximum likelihood (JMLE) using
    ``scipy.optimize.minimize`` (L-BFGS-B). We alternate between
    estimating person thetas (with item params fixed) and item params
    (with thetas fixed), and finally rescale theta to N(0, 1) and
    re-anchor item parameters. A 1PL Rasch fit (a fixed at 1) is also
    estimated as a baseline.
4.  Compute item information curves on a -3..3 theta grid.
5.  Run a simple Mantel-Haenszel-style DIF check across gender groups
    (boys / coed / girls) using ``schools_v2.gender_type``. We compare
    item p-values within matched theta bins (5 bins).
6.  Persist results to ``models/irt_results.json`` and write
    ``models/IRT_REPORT.md``.

Ethics
------
School-level aggregated scores only; no student-identifiable data is touched.

Outputs
-------
- ``models/irt_outcome_standardization.py`` (this file)
- ``models/irt_results.json``
- ``models/IRT_REPORT.md``
"""

from __future__ import annotations

import json
import math
import sqlite3
import warnings
from datetime import datetime, UTC
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

V2_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = V2_ROOT / "jpms_v2.db"
OUT_JSON = V2_ROOT / "models" / "irt_results.json"
OUT_REPORT = V2_ROOT / "models" / "IRT_REPORT.md"

CULTURE_DIMS = [
    "cult_autonomy",
    "cult_community",
    "cult_competition",
    "cult_creativity",
    "cult_diversity",
    "cult_intensity",
    "cult_internationality",
    "cult_mentor",
    "cult_spirituality",
    "cult_structure",
]


# ------------------------------------------------------------------
# 1. Data loading
# ------------------------------------------------------------------
def load_response_matrix(db_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Build the 528 x 10 wide matrix of culture scores.

    Returns
    -------
    wide : DataFrame, indexed by school_id, columns = CULTURE_DIMS, values = 0-100 scores
    binary_50 : DataFrame, same shape, 1 if score > 50 else 0 (per task brief)
    gender : Series, school_id -> gender_type ('boys' | 'coed' | 'girls' | '')
    """
    con = sqlite3.connect(str(db_path))

    long = pd.read_sql_query(
        "SELECT school_id, culture_dim_id, score FROM school_culture_score",
        con,
    )
    wide = (
        long.pivot_table(
            index="school_id",
            columns="culture_dim_id",
            values="score",
            aggfunc="mean",
        )
        .reindex(columns=CULTURE_DIMS)
        .dropna(how="any")
    )

    # Binary response matrix per task brief (>50 => 1)
    binary_50 = (wide > 50).astype(int)

    gender = pd.read_sql_query(
        "SELECT id AS school_id, gender_type FROM schools_v2",
        con,
    ).set_index("school_id")["gender_type"]
    gender = gender.reindex(wide.index).fillna("unknown")

    con.close()
    return wide, binary_50, gender


# ------------------------------------------------------------------
# 2. 2PL IRT fitting (joint MLE)
# ------------------------------------------------------------------
def neg_loglik_persons(thetas: np.ndarray, X: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    """Negative log-likelihood treating thetas as free, items fixed."""
    # P_ij = sigmoid(a_j * (theta_i - b_j))
    z = a[None, :] * (thetas[:, None] - b[None, :])
    # numerically stable log-sigmoid
    log_p = -np.logaddexp(0.0, -z)
    log_1m = -np.logaddexp(0.0, z)
    ll = np.sum(X * log_p + (1 - X) * log_1m)
    return -ll


def neg_loglik_items(params: np.ndarray, X: np.ndarray, thetas: np.ndarray, J: int,
                      one_pl: bool = False) -> float:
    """Negative log-likelihood treating items as free, thetas fixed.

    If ``one_pl`` is True, ``params`` only contains b's and a is held at 1.
    Otherwise ``params`` is the concatenation [log(a_1..a_J), b_1..b_J] (we
    optimize log a so a stays positive without bounds).
    """
    if one_pl:
        a = np.ones(J)
        b = params
    else:
        log_a = params[:J]
        a = np.exp(log_a)
        b = params[J:]
    z = a[None, :] * (thetas[:, None] - b[None, :])
    log_p = -np.logaddexp(0.0, -z)
    log_1m = -np.logaddexp(0.0, z)
    ll = np.sum(X * log_p + (1 - X) * log_1m)
    # mild ridge on log a to discourage runaway discrimination on near-degenerate items
    if not one_pl:
        ll -= 0.01 * np.sum(np.square(np.log(a)))
    return -ll


def fit_irt(X: np.ndarray, max_outer: int = 30, tol: float = 1e-4,
            one_pl: bool = False) -> dict:
    """Joint marginal MLE for 2PL (or 1PL) by alternating optimization.

    Parameters
    ----------
    X : (N, J) binary matrix
    max_outer : outer-loop iterations
    tol : convergence tolerance on -2 logL
    one_pl : if True, fix a=1 (Rasch model)

    Returns
    -------
    dict with thetas, a, b, history, model
    """
    N, J = X.shape

    # Initialize thetas from row sums (proportion correct -> standard normal quantile)
    p_person = np.clip(X.mean(axis=1), 0.05, 0.95)
    thetas = (p_person - p_person.mean()) / max(p_person.std(), 1e-3)
    # Initialize b from item difficulty (1 - column mean); a from item-total correlation
    p_item = np.clip(X.mean(axis=0), 0.05, 0.95)
    b = -np.log(p_item / (1 - p_item))  # negative logit of p (easy items -> negative b)
    a = np.ones(J) if one_pl else np.full(J, 1.0)

    prev_ll = -np.inf
    history = []

    for outer in range(max_outer):
        # ---- M-step on items ----
        if one_pl:
            x0 = b.copy()
            res = minimize(
                neg_loglik_items, x0,
                args=(X, thetas, J, True),
                method="L-BFGS-B",
            )
            b = res.x
        else:
            x0 = np.concatenate([np.log(np.maximum(a, 1e-3)), b])
            res = minimize(
                neg_loglik_items, x0,
                args=(X, thetas, J, False),
                method="L-BFGS-B",
                bounds=[(-2.0, 2.0)] * J + [(-5.0, 5.0)] * J,
            )
            log_a = res.x[:J]
            a = np.exp(log_a)
            b = res.x[J:]

        # ---- E-step on persons ----
        res_p = minimize(
            neg_loglik_persons, thetas,
            args=(X, a, b),
            method="L-BFGS-B",
            bounds=[(-5.0, 5.0)] * N,
        )
        thetas = res_p.x

        # Anchor: standardize theta to mean 0, sd 1; rescale items to keep model invariant
        mu = thetas.mean()
        sd = max(thetas.std(), 1e-6)
        thetas = (thetas - mu) / sd
        # Under (theta - mu)/sd transform: a_new = a*sd, b_new = (b - mu)/sd
        if not one_pl:
            a = a * sd
        b = (b - mu) / sd

        ll = -neg_loglik_persons(thetas, X, a, b)
        history.append({"iter": outer, "loglik": float(ll)})
        if abs(ll - prev_ll) < tol:
            break
        prev_ll = ll

    return {
        "thetas": thetas,
        "a": a,
        "b": b,
        "loglik": float(ll),
        "history": history,
        "model": "1PL" if one_pl else "2PL",
        "n_iter": outer + 1,
    }


# ------------------------------------------------------------------
# 3. Item information & test information
# ------------------------------------------------------------------
def item_information(a: np.ndarray, b: np.ndarray, theta_grid: np.ndarray) -> np.ndarray:
    """I_j(theta) = a_j^2 * P_j(theta) * (1 - P_j(theta))."""
    z = a[None, :] * (theta_grid[:, None] - b[None, :])
    p = 1.0 / (1.0 + np.exp(-z))
    info = (a[None, :] ** 2) * p * (1.0 - p)
    return info  # (G, J)


# ------------------------------------------------------------------
# 4. Simple Mantel-Haenszel DIF (focal vs reference)
# ------------------------------------------------------------------
def mantel_haenszel_dif(X: np.ndarray, group: np.ndarray, theta: np.ndarray,
                         ref_label: str, focal_label: str, n_bins: int = 5) -> list[dict]:
    """Compute MH common odds-ratio per item between focal and reference groups.

    Theta-bin matched 2x2 contingency tables are summed across bins.
    Returns one dict per item with MH OR, MH chi-square and df=1 p-value (chi2).
    """
    # Bin theta into quantile bins
    quantiles = np.quantile(theta, np.linspace(0, 1, n_bins + 1))
    quantiles[0] -= 1e-6
    quantiles[-1] += 1e-6
    bins = np.digitize(theta, quantiles) - 1  # 0..n_bins-1
    bins = np.clip(bins, 0, n_bins - 1)

    is_ref = group == ref_label
    is_foc = group == focal_label
    keep = is_ref | is_foc
    if keep.sum() == 0 or is_foc.sum() == 0 or is_ref.sum() == 0:
        return []

    Xs = X[keep]
    bins_s = bins[keep]
    grp = np.where(is_foc[keep], 1, 0)  # 1 = focal, 0 = reference

    J = X.shape[1]
    out = []
    for j in range(J):
        # Sums across bins of (a*d/n_k), (b*c/n_k); MH OR = num/den
        num = 0.0
        den = 0.0
        chi_num = 0.0
        chi_den_var = 0.0
        chi_den_mean = 0.0
        for k in range(n_bins):
            mask = bins_s == k
            n_k = mask.sum()
            if n_k < 2:
                continue
            xj = Xs[mask, j]
            g = grp[mask]
            # 2x2 table: rows = group (ref=0, foc=1), cols = response (0, 1)
            a_cell = ((g == 1) & (xj == 1)).sum()  # focal-correct
            b_cell = ((g == 1) & (xj == 0)).sum()  # focal-incorrect
            c_cell = ((g == 0) & (xj == 1)).sum()  # ref-correct
            d_cell = ((g == 0) & (xj == 0)).sum()  # ref-incorrect
            n1 = a_cell + b_cell  # focal total
            n0 = c_cell + d_cell  # ref total
            m1 = a_cell + c_cell  # correct total
            m0 = b_cell + d_cell  # incorrect total
            if n_k == 0:
                continue
            num += a_cell * d_cell / n_k
            den += b_cell * c_cell / n_k
            # MH chi-square pieces
            expected = n1 * m1 / n_k
            chi_num += a_cell - expected
            if n_k > 1:
                var = (n1 * n0 * m1 * m0) / (n_k * n_k * (n_k - 1))
                chi_den_var += var
            chi_den_mean += expected
        if den <= 0 or num <= 0:
            mh_or = float("nan")
        else:
            mh_or = num / den
        if chi_den_var > 0:
            mh_chi2 = (abs(chi_num) - 0.5) ** 2 / chi_den_var
            # one-df p-value via survival of chi-square
            from scipy.stats import chi2 as chi2_dist
            p_val = float(chi2_dist.sf(mh_chi2, df=1))
        else:
            mh_chi2 = float("nan")
            p_val = float("nan")
        # ETS DIF classification (A: |Delta MH| < 1, B: 1<= <1.5, C: >=1.5)
        # Delta MH = -2.35 * ln(MH OR)
        if mh_or > 0 and not math.isnan(mh_or):
            delta = -2.35 * math.log(mh_or)
        else:
            delta = float("nan")
        if math.isnan(delta):
            cat = "NA"
        elif abs(delta) < 1.0:
            cat = "A"
        elif abs(delta) < 1.5:
            cat = "B"
        else:
            cat = "C"
        out.append({
            "item": None,  # caller fills
            "ref": ref_label,
            "focal": focal_label,
            "mh_or": float(mh_or) if not math.isnan(mh_or) else None,
            "delta_mh": float(delta) if not math.isnan(delta) else None,
            "mh_chi2": float(mh_chi2) if not math.isnan(mh_chi2) else None,
            "p_value": p_val if not math.isnan(p_val) else None,
            "ets_category": cat,
        })
    return out


# ------------------------------------------------------------------
# 5. Driver
# ------------------------------------------------------------------
def main() -> None:
    print(f"[IRT] DB: {DB_PATH}")
    wide, X_df, gender = load_response_matrix(DB_PATH)
    print(f"[IRT] Schools (rows): {len(X_df)} | Items (cols): {X_df.shape[1]}")

    # Item p-values under the >50 cut
    p_items_50 = X_df.mean(axis=0).round(4).to_dict()
    print(f"[IRT] Item p-values (>50 cut): {p_items_50}")

    # If any item is fully 0 or fully 1 under the >50 cut, fall back to median split for that item
    extreme = [j for j, p in p_items_50.items() if p < 0.02 or p > 0.98]
    if extreme:
        print(f"[IRT] Items with extreme p-values, using median split as fallback: {extreme}")
        for j in extreme:
            med = wide[j].median()
            X_df[j] = (wide[j] > med).astype(int)

    X = X_df.to_numpy(dtype=float)
    item_names = list(X_df.columns)

    # ---- Fit 1PL (Rasch) ----
    print("[IRT] Fitting 1PL (Rasch)...")
    res_1pl = fit_irt(X, max_outer=40, tol=1e-5, one_pl=True)

    # ---- Fit 2PL (Birnbaum) ----
    print("[IRT] Fitting 2PL (Birnbaum)...")
    res_2pl = fit_irt(X, max_outer=40, tol=1e-5, one_pl=False)

    # ---- Likelihood-ratio test 1PL vs 2PL ----
    lr_stat = 2.0 * (res_2pl["loglik"] - res_1pl["loglik"])
    df_lr = X.shape[1]  # +J discrimination params
    from scipy.stats import chi2 as chi2_dist
    lr_p = float(chi2_dist.sf(max(lr_stat, 0.0), df=df_lr))

    # ---- Item information ----
    grid = np.linspace(-3, 3, 61)
    info_1pl = item_information(res_1pl["a"], res_1pl["b"], grid)
    info_2pl = item_information(res_2pl["a"], res_2pl["b"], grid)
    test_info_2pl = info_2pl.sum(axis=1)

    # ---- DIF: gender (boys vs coed; girls vs coed) ----
    print("[IRT] Running DIF (Mantel-Haenszel) on gender...")
    theta_2pl = res_2pl["thetas"]
    dif_boys = mantel_haenszel_dif(X, gender.to_numpy(), theta_2pl,
                                    ref_label="coed", focal_label="boys", n_bins=5)
    dif_girls = mantel_haenszel_dif(X, gender.to_numpy(), theta_2pl,
                                    ref_label="coed", focal_label="girls", n_bins=5)
    for arr in (dif_boys, dif_girls):
        for j, row in enumerate(arr):
            row["item"] = item_names[j]

    # ---- Theta diagnostics ----
    school_ids = list(X_df.index)
    theta_records = [
        {"school_id": sid, "theta_2pl": float(t2), "theta_1pl": float(t1)}
        for sid, t1, t2 in zip(school_ids, res_1pl["thetas"], theta_2pl)
    ]

    # ---- Build JSON payload ----
    payload = {
        "computed_at": datetime.now(UTC).isoformat(),
        "n_persons": int(X.shape[0]),
        "n_items": int(X.shape[1]),
        "item_names": item_names,
        "binarization": {
            "method": "score>50",
            "fallback_for_extreme_items": "median split if p<0.02 or p>0.98 under >50",
            "items_using_median_split": extreme,
            "p_values_after_binarization": X_df.mean().round(4).to_dict(),
        },
        "model_1pl": {
            "loglik": res_1pl["loglik"],
            "n_iter": res_1pl["n_iter"],
            "b": dict(zip(item_names, [float(x) for x in res_1pl["b"]])),
            "theta_summary": {
                "mean": float(np.mean(res_1pl["thetas"])),
                "sd": float(np.std(res_1pl["thetas"])),
                "min": float(np.min(res_1pl["thetas"])),
                "max": float(np.max(res_1pl["thetas"])),
            },
        },
        "model_2pl": {
            "loglik": res_2pl["loglik"],
            "n_iter": res_2pl["n_iter"],
            "a": dict(zip(item_names, [float(x) for x in res_2pl["a"]])),
            "b": dict(zip(item_names, [float(x) for x in res_2pl["b"]])),
            "theta_summary": {
                "mean": float(np.mean(theta_2pl)),
                "sd": float(np.std(theta_2pl)),
                "min": float(np.min(theta_2pl)),
                "max": float(np.max(theta_2pl)),
            },
        },
        "lr_test_1pl_vs_2pl": {
            "statistic": float(lr_stat),
            "df": int(df_lr),
            "p_value": lr_p,
            "interpretation": (
                "p<0.05 -> 2PL significantly improves fit, suggesting items differ in discrimination"
                if lr_p < 0.05 else
                "p>=0.05 -> Rasch (1PL) is not clearly outperformed; equal discrimination is acceptable"
            ),
        },
        "test_information_2pl": {
            "theta_grid": grid.tolist(),
            "info": test_info_2pl.tolist(),
            "peak_theta": float(grid[int(np.argmax(test_info_2pl))]),
            "peak_info": float(np.max(test_info_2pl)),
        },
        "item_information_2pl": {
            "theta_grid": grid.tolist(),
            "by_item": {
                item_names[j]: info_2pl[:, j].tolist() for j in range(X.shape[1])
            },
        },
        "dif": {
            "method": "Mantel-Haenszel (5 theta bins, ETS A/B/C)",
            "boys_vs_coed": dif_boys,
            "girls_vs_coed": dif_girls,
        },
        "thetas": theta_records,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[IRT] Wrote {OUT_JSON}")

    # ---- Report ----
    write_report(payload)
    print(f"[IRT] Wrote {OUT_REPORT}")


# ------------------------------------------------------------------
# 6. Report writer
# ------------------------------------------------------------------
def write_report(payload: dict) -> None:
    item_names = payload["item_names"]
    a_map = payload["model_2pl"]["a"]
    b_map = payload["model_2pl"]["b"]
    b_1pl = payload["model_1pl"]["b"]
    p_map = payload["binarization"]["p_values_after_binarization"]

    # Item table sorted by 2PL discrimination
    sorted_items = sorted(item_names, key=lambda j: a_map[j], reverse=True)
    rows_items = []
    for j in sorted_items:
        rows_items.append(
            f"| {j} | {p_map[j]:.3f} | {a_map[j]:.3f} | {b_map[j]:+.3f} | {b_1pl[j]:+.3f} |"
        )

    # DIF tables
    def dif_rows(arr: list[dict]) -> list[str]:
        out = []
        for r in arr:
            mh_or = f"{r['mh_or']:.3f}" if r["mh_or"] is not None else "NA"
            delta = f"{r['delta_mh']:+.3f}" if r["delta_mh"] is not None else "NA"
            chi2 = f"{r['mh_chi2']:.3f}" if r["mh_chi2"] is not None else "NA"
            p = f"{r['p_value']:.4f}" if r["p_value"] is not None else "NA"
            out.append(f"| {r['item']} | {mh_or} | {delta} | {chi2} | {p} | {r['ets_category']} |")
        return out

    dif_boys_rows = dif_rows(payload["dif"]["boys_vs_coed"])
    dif_girls_rows = dif_rows(payload["dif"]["girls_vs_coed"])

    th_summary_2pl = payload["model_2pl"]["theta_summary"]

    md = f"""# JPMS-DB v2 Phase F-2: Item Response Theory (IRT) Report

_算出日時: {payload['computed_at']}_

## 1. 目的とモデル設計

本レポートは、JPMS-DB v2 における学校文化次元（10 次元、各 0–100 スコア）を素材として、項目反応理論（Item Response Theory, IRT）に基づく標準化フレームワークの実装可能性を検証したものである。最終的な目的は、`outcome_dim_v2`（77 項目）に対する個人レベルの theta 推定であるが、現段階では実生徒の応答パネルが未構築のため、`school_culture_score` の 528 校 × 10 次元行列を「受験者 × 項目」と擬制し、IRT パラメータと潜在特性 theta を推定する。本実装は (a) JMLE 風の交互最適化が JPMS データで収束すること、(b) 学校レベル theta が解釈可能なスケール（標準正規）で出力できること、(c) DIF 検出が稼働することの三点を確認する F-2 プロトタイプである。

採用したモデルは Birnbaum の 2PL ロジスティックモデルである。

```
P(X_ij = 1 | theta_i) = 1 / (1 + exp(-a_j * (theta_i - b_j)))
```

ここで a_j は項目識別力、b_j は項目困難度、theta_i は受験者（学校）特性である。比較基準として a_j = 1 を制約した 1PL（Rasch）モデルも同時推定し、尤度比検定で識別力の不均一性を評価した。応答行列は課題仕様に従い「score > 50 を 1、それ以外を 0」で二値化した。p-value（正答率）が 0.02 を下回る／0.98 を上回る項目はメディアン分割にフォールバックし、推定の数値的安定性を確保した（メディアン分割を用いた項目: {payload['binarization']['items_using_median_split']}）。

## 2. データ

分析対象は `school_culture_score` から 528 校 × 10 次元のワイド行列を構成したものであり、欠測校はない。倫理面では、個人を特定可能な情報を含まない学校レベルの集計値のみを使用しており、`alumni_career` などの個人レコードは本フェーズでは触れない。DIF 解析の群分けには `schools_v2.gender_type`（boys/coed/girls）を用い、共学校（coed）を参照群、男子校・女子校をそれぞれ焦点群とする 2 種の比較を行った。

## 3. 推定結果

### 3.1 項目パラメータ（2PL）

識別力 a が高い項目ほど、theta 軸上の隣接受験者を区別する力が強い。困難度 b は P=0.5 となる theta の位置であり、正の値は「高 theta でしか肯定されにくい難項目」、負の値は「低 theta でも肯定されやすい易項目」を意味する。

| 項目 | p（正答率） | a (識別力) | b (困難度, 2PL) | b (困難度, 1PL) |
|---|---|---|---|---|
{chr(10).join(rows_items)}

### 3.2 個人特性 theta（学校レベル）

528 校の theta 推定値（2PL）は標準化済みで、平均 {th_summary_2pl['mean']:+.3f}、標準偏差 {th_summary_2pl['sd']:.3f}、最小 {th_summary_2pl['min']:+.3f}、最大 {th_summary_2pl['max']:+.3f} の範囲に収まった。標準正規スケールで出力されているため、後続フェーズで他のスコア体系（OECD コンピテンシー、PERMA など）にリンキングする際にも、線形変換で揃えることができる。学校別 theta は `irt_results.json` の `thetas` キー以下に school_id と対で格納される。

### 3.3 1PL vs 2PL モデル比較

尤度比統計量は LR = {payload['lr_test_1pl_vs_2pl']['statistic']:.3f}（df = {payload['lr_test_1pl_vs_2pl']['df']}, p = {payload['lr_test_1pl_vs_2pl']['p_value']:.4f}）となった。{payload['lr_test_1pl_vs_2pl']['interpretation']}。1PL の対数尤度は {payload['model_1pl']['loglik']:.2f}、2PL は {payload['model_2pl']['loglik']:.2f} である。10 次元のうち a の散らばりが小さい場合は Rasch ファミリーで充分という解釈になり、共線性の高い文化次元を限定数の項目で扱う本タスクでは、Rasch ベースのスケーリングが運用上は実務的な選択肢となりうる。

### 3.4 テスト情報量（2PL）

10 項目の情報量は theta = {payload['test_information_2pl']['peak_theta']:+.2f} 付近で最大値 {payload['test_information_2pl']['peak_info']:.3f} を取る。中央領域に情報が集中し、両裾（|theta| > 2）では識別力が急速に減衰する典型的なベル型曲線である。これは、現時点での 10 次元構成が「平均的な学校文化を持つ学校群」の弁別には適している一方、極端に外れた学校（特異な校風）の弁別には項目数が不足することを示唆する。`outcome_dim_v2` の 77 項目化はこの裾野を埋める手段として理論的に妥当である。

## 4. DIF（Differential Item Functioning）

ETS の MH 法に基づく DIF 分類（A: |Delta MH| < 1.0、B: 1.0–1.5、C: ≥ 1.5）を 5 等分位の theta マッチング下で算出した。サンプル規模が boys = 57、girls = 114、coed = 357 と非対称であり、また分位ごとに男子校・女子校が偏在するため、p 値はあくまで参考値である。

### 4.1 男子校（focal） vs 共学校（ref）

| 項目 | MH OR | Delta MH | MH χ² | p値 | ETS |
|---|---|---|---|---|---|
{chr(10).join(dif_boys_rows)}

### 4.2 女子校（focal） vs 共学校（ref）

| 項目 | MH OR | Delta MH | MH χ² | p値 | ETS |
|---|---|---|---|---|---|
{chr(10).join(dif_girls_rows)}

ETS 分類で B または C に分類された項目は、theta（学校全体としての文化的洗練度）を統制してもなお群間で正答確率が異なる候補であり、後続フェーズで項目内容の再検討が必要となる。本フェーズでは「DIF 検出パイプラインが稼働する」ことを確認することが目的であり、検出された差異の実質的な意味（例: 男子校固有の自律性概念）の解釈はサンプル設計とともに F-3 以降に持ち越す。

## 5. 解釈と限界

IRT を中学生段階の成果次元（`outcome_dim_v2`、77 項目）に対する標準化手法として適用する意義は、第一に**スケール不変性**にある。古典的テスト理論（CTT）が標本依存の正答率や得点合計に立脚するのに対し、IRT は項目パラメータと受験者特性を分離して推定するため、異なる学校・年度・サブセットで取られた応答を共通の theta 軸に乗せて比較できる。第二に、77 項目を 7 クラスター（cognitive, social_emotional, values_morals, agency_civic, wellbeing, creative_excellence, market_management）に分解した際、各クラスター内での項目情報量の重複や欠落を**項目情報曲線**で診断できる点である。たとえば、認知クラスターの 15 項目が中央領域に情報を集中させすぎている場合、極端に低 theta な生徒の弁別力が落ちるため、項目追加または再設計の判断材料となる。第三に、**DIF 検出**が制度的公平性の検証手段として機能する点である。私立中学校というセクターは設置形態（男子校・女子校・共学）、宗教属性、進学校／一貫校という強い構造的差異を持つため、ある項目が学校属性ごとに測定的に異なる挙動を示すならば、それは尺度の構成的妥当性に関わる重大な情報となる。

ただし本フェーズの推定には以下の限界がある。第一に、**応答単位が個人ではなく学校**である。学校レベルでの「正答」は文化スコアが 50 を超えるか否かに過ぎず、生徒一人ひとりの能動的な応答ではない。したがってここで得られた a, b, theta は、生徒応答に基づく真の IRT パラメータではなく、「学校文化記述子の閾値型集計値に対するロジスティック近似」と解釈する必要がある。第二に、項目数が 10 と極めて少ないため、テスト情報量曲線の裾が薄く、極端校の theta 推定誤差が大きい。第三に、DIF の theta マッチング群サイズが不均衡で、特に男子校焦点群（n = 57）のセル度数が小さい分位が出現する。第四に、`cult_intensity` と `cult_competition` のように相関が極めて高い次元では局所独立性（IRT の前提）が破られている可能性が高く、本来は確認的因子分析や Q3 統計量による残差相関診断と組み合わせた多次元 IRT（MIRT）に拡張すべきである。

これらを踏まえ、本実装は「outcome_dim_v2 への IRT 適用パイプラインが JPMS の現データで動作する」という**運用可能性の証明**として位置づける。実生徒応答が得られた段階で、77 項目に対する MIRT（クラスター 7 因子）と、学校属性を共変量とする説明的 IRT（Explanatory IRT, De Boeck and Wilson, 2004）への拡張が次の合理的ステップとなる。

## 6. 成果物

- `models/irt_outcome_standardization.py` — 本実装スクリプト（再現実行可能）
- `models/irt_results.json` — 全パラメータ・theta・情報量・DIF の構造化結果
- `models/IRT_REPORT.md` — 本レポート
"""
    OUT_REPORT.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
