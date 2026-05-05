#!/usr/bin/env python3
"""
JPMS-DB Phase 3: Testimonials 品質チェッカー
============================================

各校の testimonials の品質を可視化する。
- 件数（>=5 件あるか）
- ネガティブ発言の有無
- 立場の多様性（在校生/卒業生/保護者の3種以上が含まれているか）
- メディア（出典タイプ）の多様性

使い方:
    # 全校のサマリー（>= 1件のある校だけ）
    python3 quality_check.py

    # 全校（0件含む）
    python3 quality_check.py --all

    # 特定校のみ
    python3 quality_check.py --school jpms_s_0001

    # 全体の達成度ダッシュボード
    python3 quality_check.py --dashboard

Author: Claude Code (Phase 3)
Date: 2026-05-04
"""
from __future__ import annotations

import argparse
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "jpms.db"

# 「立場の多様性」をカウントするための集約クラス
DIVERSITY_BUCKETS: dict[str, str] = {
    "student_current": "在校生",
    "student_former": "卒業生",
    "parent_current": "保護者",
    "parent_former": "保護者",
    "teacher": "教員",
    "principal": "校長",
    "external_evaluator": "第三者",
    "third_party": "第三者",
}


def fetch_school_data(conn: sqlite3.Connection, school_id: Optional[str] = None):
    sql = """
        SELECT s.id, s.name_ja, s.location_pref, t.speaker_category, t.sentiment, t.medium
        FROM jpms_schools s
        LEFT JOIN jpms_testimonials t ON t.school_id = s.id
    """
    if school_id:
        sql += " WHERE s.id = ?"
        return conn.execute(sql, (school_id,)).fetchall()
    return conn.execute(sql).fetchall()


def evaluate_school(rows: list[tuple]) -> dict:
    """1校分の testimonials データを集計"""
    sid = rows[0][0]
    name = rows[0][1]
    pref = rows[0][2]

    # t がない（LEFT JOIN で NULL）行も含まれる
    spkrs: Counter[str] = Counter()
    sents: Counter[str] = Counter()
    media: Counter[str] = Counter()
    total = 0
    for _, _, _, spk, sen, med in rows:
        if spk is None:
            continue
        total += 1
        spkrs[spk] += 1
        sents[sen] += 1
        if med:
            media[med] += 1

    diversity_groups = {DIVERSITY_BUCKETS.get(k, k) for k in spkrs.keys()}
    has_negative = sents.get("negative", 0) > 0
    # 「在校生 + 卒業生 + 保護者」のうち2種以上 → 多様
    core = {"在校生", "卒業生", "保護者"} & diversity_groups
    has_3groups = len(core) >= 2

    return {
        "id": sid,
        "name": name,
        "pref": pref,
        "total": total,
        "speakers": dict(spkrs),
        "sentiments": dict(sents),
        "media": dict(media),
        "diversity_groups": sorted(diversity_groups),
        "has_negative": has_negative,
        "has_diverse_speakers": has_3groups,
        "ge5": total >= 5,
    }


def print_school_report(report: dict) -> None:
    flags = []
    flags.append("OK 件数" if report["ge5"] else "  件数不足")
    flags.append("OK ネガ" if report["has_negative"] else "  ネガなし")
    flags.append("OK 多様" if report["has_diverse_speakers"] else "  立場偏り")
    print(f"[{report['id']}] {report['name']} ({report['pref']})")
    print(f"  件数={report['total']}  | " + " / ".join(flags))
    print(f"  立場 : {report['speakers']}")
    print(f"  感情 : {report['sentiments']}")
    print(f"  媒体 : {report['media']}")
    print(f"  カテゴリ多様性: {report['diversity_groups']}")


def print_dashboard(reports: list[dict]) -> None:
    total_schools = len(reports)
    with_t = [r for r in reports if r["total"] > 0]
    ge5 = [r for r in reports if r["ge5"]]
    has_neg = [r for r in reports if r["has_negative"]]
    has_div = [r for r in reports if r["has_diverse_speakers"]]
    full_quality = [r for r in reports if r["ge5"] and r["has_negative"] and r["has_diverse_speakers"]]

    print("=" * 64)
    print("品質ダッシュボード")
    print("=" * 64)
    print(f"対象学校数               : {total_schools}")
    print(f"testimonial >= 1 件      : {len(with_t)}  ({100*len(with_t)/max(total_schools,1):.1f}%)")
    print(f"testimonial >= 5 件      : {len(ge5)}  ({100*len(ge5)/max(total_schools,1):.1f}%)")
    print(f"ネガティブ発言を含む     : {len(has_neg)}")
    print(f"立場が多様（2種以上)     : {len(has_div)}")
    print(f"全条件クリア（5件・ネガ・多様）: {len(full_quality)}")
    print()
    # 都道府県別
    by_pref: dict[str, list[dict]] = defaultdict(list)
    for r in reports:
        by_pref[r["pref"]].append(r)
    print("都道府県別 (有/全):")
    for pref in sorted(by_pref.keys()):
        rs = by_pref[pref]
        n_with = sum(1 for r in rs if r["total"] > 0)
        n_ge5 = sum(1 for r in rs if r["ge5"])
        print(f"  {pref:<6}  全={len(rs):>3}  有={n_with:>3}  5件以上={n_ge5:>3}")


def main() -> int:
    parser = argparse.ArgumentParser(description="JPMS testimonials quality check")
    parser.add_argument("--all", action="store_true", help="0件の学校もすべて表示")
    parser.add_argument("--school", help="特定 school_id のみ詳細表示")
    parser.add_argument("--dashboard", action="store_true", help="全体の達成度ダッシュボード")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = fetch_school_data(conn, args.school)
    finally:
        conn.close()

    if not rows:
        print("該当データなし")
        return 1

    # 学校ごとにグループ化
    grouped: dict[str, list[tuple]] = defaultdict(list)
    for r in rows:
        grouped[r[0]].append(r)

    reports = [evaluate_school(g) for g in grouped.values()]

    if args.dashboard:
        print_dashboard(reports)
        return 0

    if args.school:
        for rep in reports:
            print_school_report(rep)
        return 0

    # 一覧（件数>0 を表示。--all なら0件も含む）
    visible = sorted(reports, key=lambda r: -r["total"])
    if not args.all:
        visible = [r for r in visible if r["total"] > 0]

    for rep in visible:
        print_school_report(rep)
        print()

    print(f"--- 表示: {len(visible)} 校 (全 {len(reports)} 校中) ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
