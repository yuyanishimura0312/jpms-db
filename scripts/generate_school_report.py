#!/usr/bin/env python3
"""
JPMS-DB Phase 3: 学校レポートHTML自動生成エンジン

Usage:
  python3 generate_school_report.py <school_id_or_name>
  python3 generate_school_report.py --all              # testimonials 5件以上の全校を生成
  python3 generate_school_report.py --index            # インデックスHTMLのみ再生成

Examples:
  python3 generate_school_report.py jpms_s_0001
  python3 generate_school_report.py 浅野中学校

学校IDまたは学校名から jpms.db を引き、赤白CIテンプレートに流し込んで
docs/schools/{school_id}.html を生成する。
"""
from __future__ import annotations

import argparse
import html
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable

ROOT = Path("/Users/nishimura+/projects/research/jpms-db")
DB_PATH = ROOT / "jpms.db"
OUT_DIR = ROOT / "docs" / "schools"
INDEX_PATH = OUT_DIR / "index.html"

MIN_TESTIMONIALS = 5  # 品質ゲート閾値

# ------------------------------------------------------------
# データ取得層
# ------------------------------------------------------------

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def resolve_school_id(conn: sqlite3.Connection, key: str) -> str | None:
    """学校IDまたは学校名（部分一致可）からIDを解決"""
    if key.startswith("jpms_s_"):
        row = conn.execute(
            "SELECT id FROM jpms_schools WHERE id=?", (key,)
        ).fetchone()
        return row["id"] if row else None
    # 名前で部分一致検索
    row = conn.execute(
        "SELECT id, name_ja FROM jpms_schools WHERE name_ja LIKE ? LIMIT 1",
        (f"%{key}%",),
    ).fetchone()
    return row["id"] if row else None


def fetch_school(conn: sqlite3.Connection, school_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM jpms_schools WHERE id=?", (school_id,)
    ).fetchone()
    return dict(row) if row else None


def fetch_curriculum(conn: sqlite3.Connection, school_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM jpms_school_curriculum WHERE school_id=?", (school_id,)
    ).fetchone()
    return dict(row) if row else None


def fetch_stats(conn: sqlite3.Connection, school_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM jpms_school_stats WHERE school_id=? ORDER BY fiscal_year DESC",
        (school_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_outcomes(conn: sqlite3.Connection, school_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM jpms_school_outcomes WHERE school_id=? ORDER BY fiscal_year DESC, outcome_type",
        (school_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_testimonials(conn: sqlite3.Connection, school_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT t.*, s.title AS source_title, s.url AS source_url, s.publisher AS source_publisher
        FROM jpms_testimonials t
        LEFT JOIN jpms_sources s ON s.id = t.source_id
        WHERE t.school_id=?
        ORDER BY t.speaker_category, t.id
        """,
        (school_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_sources(conn: sqlite3.Connection, school_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT DISTINCT s.*
        FROM jpms_sources s
        WHERE s.id IN (
            SELECT source_id FROM jpms_testimonials WHERE school_id=?
            UNION
            SELECT primary_source_id FROM jpms_schools WHERE id=?
            UNION
            SELECT source_id FROM jpms_school_curriculum WHERE school_id=?
        )
        ORDER BY s.id
        """,
        (school_id, school_id, school_id),
    ).fetchall()
    return [dict(r) for r in rows if r["id"]]


# ------------------------------------------------------------
# ラベル変換
# ------------------------------------------------------------

GENDER_LABEL = {"coed": "共学", "boys": "男子校", "girls": "女子校"}
RELIGIOUS_LABEL = {
    "catholic": "カトリック",
    "protestant": "プロテスタント",
    "anglican": "聖公会",
    "buddhist": "仏教",
    "shinto": "神道",
    "non_religious": "無宗教",
    "other": "その他",
    "unknown": "不明",
}
INTEGRATED_LABEL = {
    "full": "完全中高一貫",
    "attached": "附属型",
    "linked": "連携型",
    "none": "中学単独",
}
SPEAKER_LABEL = {
    "student_current": "在校生",
    "student_former": "卒業生",
    "parent_current": "保護者（在校）",
    "parent_former": "保護者（卒業）",
    "teacher": "教員",
    "principal": "校長",
    "external_evaluator": "外部評価者",
    "third_party": "第三者",
}
MEDIUM_LABEL = {
    "school_website": "学校公式サイト",
    "school_brochure": "学校案内パンフレット",
    "school_event": "学校イベント",
    "interview": "インタビュー記事",
    "book": "書籍",
    "newspaper": "新聞",
    "x": "X（旧Twitter）",
    "instagram": "Instagram",
    "youtube": "YouTube",
    "blog": "個人ブログ",
    "note": "note",
    "5ch": "5ch",
    "other": "その他",
}
SENTIMENT_LABEL = {
    "positive": "肯定",
    "neutral": "中立",
    "negative": "否定",
    "mixed": "両義",
}
OUTCOME_LABEL = {
    "todai_kyodai": "東大・京大",
    "soukei": "早慶",
    "gmarch": "GMARCH",
    "kankan_doritsu": "関関同立",
    "medical": "医学部",
    "overseas": "海外大学",
    "attached_uni": "系列大学",
    "other": "その他",
}


def label(d: dict, key: str, default: str = "—") -> str:
    val = d.get(key)
    if val is None or val == "":
        return default
    return d[key]


# ------------------------------------------------------------
# テンプレート断片
# ------------------------------------------------------------

def esc(s: str | None) -> str:
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def render_meta_table(school: dict, curriculum: dict | None) -> str:
    """基本情報テーブル"""
    rows = []
    name = esc(school.get("name_ja", ""))
    rows.append(("正式名称", name + (f"（{esc(school['name_kana'])}）" if school.get("name_kana") else "")))
    location = esc(school.get("location_pref") or "")
    if school.get("location_city"):
        location += esc(school["location_city"])
    if school.get("address"):
        location += " " + esc(school["address"])
    if school.get("nearest_station"):
        location += f"（最寄駅：{esc(school['nearest_station'])}）"
    rows.append(("所在地", location or "—"))
    if school.get("establishment_year"):
        founder = f"／創立者：{esc(school['founder'])}" if school.get("founder") else ""
        rows.append(("創立", f"{school['establishment_year']}年{founder}"))
    rows.append(("校種", GENDER_LABEL.get(school.get("gender_type") or "", "—")))
    if school.get("integrated_type"):
        rows.append(("一貫性", INTEGRATED_LABEL.get(school["integrated_type"], "—")))
    if school.get("school_corporation"):
        rows.append(("運営法人", esc(school["school_corporation"])))
    rel = school.get("religious_affiliation")
    if rel and rel != "unknown":
        rel_label = RELIGIOUS_LABEL.get(rel, rel)
        if school.get("religious_subgroup"):
            rel_label += f"（{esc(school['religious_subgroup'])}）"
        rows.append(("宗教的背景", rel_label))
    if school.get("affiliated_university"):
        rows.append(("系列大学", esc(school["affiliated_university"])))
    if school.get("website_url"):
        url = esc(school["website_url"])
        rows.append(("公式サイト", f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'))

    body = "\n".join(
        f"<tr><th>{esc(k)}</th><td>{v}</td></tr>" for k, v in rows
    )
    return f'<table class="meta-table"><caption>基本情報</caption><tbody>\n{body}\n</tbody></table>'


def render_curriculum(curriculum: dict | None) -> str:
    """教育プログラム概要"""
    if not curriculum:
        return (
            "<p>教育プログラムに関する詳細データはJPMS-DBに未登録です。今後の調査で拡充されます。"
            "学校公式サイトおよび学校案内パンフレットを直接ご参照ください。</p>"
        )

    SCALE = {0: "—", 1: "あり", 2: "強み", 3: "特に強い"}
    items = []

    def add(name: str, val):
        if val and isinstance(val, int) and val > 0:
            items.append((name, SCALE.get(val, "あり")))

    add("探究学習", curriculum.get("inquiry_learning"))
    add("STEAM教育", curriculum.get("steam"))
    add("PBL（課題解決型学習）", curriculum.get("pbl"))
    add("ICT・情報教育", curriculum.get("ict_strength"))
    add("芸術・表現", curriculum.get("art_strength"))
    add("スポーツ", curriculum.get("sports_strength"))
    add("宗教教育", curriculum.get("religious_education"))
    if curriculum.get("international_track"):
        items.append(("国際コース", "設置"))
    if curriculum.get("ib_program") and curriculum["ib_program"] != "none":
        items.append(("国際バカロレア", esc(curriculum["ib_program"])))
    if curriculum.get("second_language"):
        items.append(("第二外国語", esc(curriculum["second_language"])))

    intro_parts = []
    if items:
        rows = "\n".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in items)
        intro_parts.append(
            "<p>本校の教育プログラムについて、JPMS-DBに登録されている特性は次のとおりです。"
            "数値は他校との相対比較ではなく、本校が公式に掲げる重点領域を簡易にスケール化したものです。</p>"
            f'<table class="meta-table"><caption>教育プログラム特性</caption><tbody>\n{rows}\n</tbody></table>'
        )
    else:
        intro_parts.append(
            "<p>教育プログラムの特性データは現時点で蓄積が浅いため、概要のみの掲載となっています。"
            "詳細は公式サイトの教育課程ページや、学校説明会・体験授業をご確認ください。</p>"
        )

    if curriculum.get("special_programs"):
        intro_parts.append(
            f"<h3>特色あるプログラム</h3>\n<p>{esc(curriculum['special_programs'])}</p>"
        )

    return "\n".join(intro_parts)


def render_testimonials(testimonials: list[dict]) -> str:
    """関係者の声（blockquoteで列挙）"""
    if not testimonials:
        return (
            "<p>関係者の声はJPMS-DBに未登録です。今後、学校公式サイト・学校案内・"
            "公開インタビュー等から収集を進めていきます。</p>"
        )

    # speaker_category 別に並び替えて出力
    order = [
        "principal", "teacher", "external_evaluator",
        "student_current", "student_former",
        "parent_current", "parent_former", "third_party",
    ]
    grouped: dict[str, list[dict]] = {k: [] for k in order}
    for t in testimonials:
        grouped.setdefault(t.get("speaker_category") or "third_party", []).append(t)

    parts = [
        "<p>JPMS-DBに登録されている関係者の発言を、立場別にご紹介します。"
        "発言は出典明記の上で原文に近い形で引用し、未成年については匿名化を施しています。</p>"
    ]
    for cat in order:
        if not grouped.get(cat):
            continue
        cat_label = SPEAKER_LABEL.get(cat, cat)
        parts.append(f"<h3>{esc(cat_label)}の声</h3>")
        for t in grouped[cat]:
            speaker = t.get("speaker_name") or cat_label
            medium = MEDIUM_LABEL.get(t.get("medium") or "", t.get("medium") or "")
            source_title = t.get("source_title") or ""
            who_parts = [esc(speaker)]
            if medium:
                who_parts.append(esc(medium))
            if source_title:
                who_parts.append(esc(source_title))
            who = "／".join(p for p in who_parts if p)
            sentiment = t.get("sentiment")
            sent_tag = ""
            if sentiment and sentiment != "positive":
                sent_tag = f' <span class="sent-tag sent-{esc(sentiment)}">{esc(SENTIMENT_LABEL.get(sentiment, sentiment))}</span>'
            parts.append(
                f"<blockquote>\n{esc(t.get('excerpt',''))}\n"
                f'<span class="who">— {who}{sent_tag}</span>\n</blockquote>'
            )
    return "\n".join(parts)


def render_outcomes(outcomes: list[dict]) -> str:
    """進学実績"""
    if not outcomes:
        return (
            "<p>進学実績の詳細データはJPMS-DBに未登録です。本校の最新の進学実績は、"
            "公式サイトの進路実績ページまたは学校説明会資料をご確認ください。"
            "JPMS-DBでは公開情報をもとに、今後の調査フェーズで拡充していきます。</p>"
        )
    # 年度別にグルーピング
    by_year: dict[int, list[dict]] = {}
    for o in outcomes:
        by_year.setdefault(o["fiscal_year"], []).append(o)

    parts = ["<p>JPMS-DBに登録されている進学実績は次のとおりです。"
             "数字は本校が公表している合格者数（重複合算を含む）であり、"
             "純粋な進学者数とは異なる場合があることにご留意ください。</p>"]
    for year in sorted(by_year.keys(), reverse=True):
        parts.append(f"<h3>{year}年度</h3>")
        rows = []
        for o in by_year[year]:
            kind = OUTCOME_LABEL.get(o.get("outcome_type") or "", o.get("outcome_type") or "")
            cnt = o.get("count")
            note = o.get("note") or ""
            rows.append(
                f"<tr><th>{esc(kind)}</th>"
                f'<td class="num-cell">{esc(str(cnt) if cnt is not None else "—")}名</td>'
                f"<td>{esc(note)}</td></tr>"
            )
        parts.append(
            '<table class="meta-table">\n<tbody>\n' + "\n".join(rows) + "\n</tbody></table>"
        )
    return "\n".join(parts)


def render_sentiment_summary(testimonials: list[dict]) -> str:
    """元データ量と感情分布"""
    if not testimonials:
        return "<p>関係者発言の集計対象データは現時点ではありません。</p>"

    total = len(testimonials)
    sent_counter = Counter(t.get("sentiment") or "neutral" for t in testimonials)
    speaker_counter = Counter(t.get("speaker_category") or "" for t in testimonials)
    medium_counter = Counter(t.get("medium") or "" for t in testimonials)

    def _bar(label_str: str, n: int, color_class: str) -> str:
        pct = (n / total * 100) if total else 0
        return (
            f'<tr><th>{esc(label_str)}</th>'
            f'<td class="num-cell">{n}件</td>'
            f'<td><div class="bar-wrap"><div class="bar {color_class}" style="width:{pct:.1f}%"></div></div></td>'
            f'<td class="num-cell">{pct:.1f}%</td></tr>'
        )

    parts = [
        f"<p>本ページは、JPMS-DBに登録された関係者発言{total}件をもとに構成しています。"
        "発言の内訳と感情分布を以下に示します。学校選びにおいては、肯定的な声と否定的な声の双方を"
        "等しく参照することが、相性判断の精度を高めることにつながります。</p>",
        "<h3>感情分布</h3>",
        '<table class="meta-table"><tbody>',
    ]
    for sent in ["positive", "mixed", "neutral", "negative"]:
        n = sent_counter.get(sent, 0)
        if n:
            parts.append(_bar(SENTIMENT_LABEL.get(sent, sent), n, f"bar-{sent}"))
    parts.append("</tbody></table>")

    parts.append("<h3>発言者の内訳</h3>")
    parts.append('<table class="meta-table"><tbody>')
    for cat, n in speaker_counter.most_common():
        parts.append(
            f"<tr><th>{esc(SPEAKER_LABEL.get(cat, cat))}</th>"
            f'<td class="num-cell">{n}件</td></tr>'
        )
    parts.append("</tbody></table>")

    parts.append("<h3>媒体の内訳</h3>")
    parts.append('<table class="meta-table"><tbody>')
    for med, n in medium_counter.most_common():
        parts.append(
            f"<tr><th>{esc(MEDIUM_LABEL.get(med, med))}</th>"
            f'<td class="num-cell">{n}件</td></tr>'
        )
    parts.append("</tbody></table>")
    return "\n".join(parts)


def render_sources(sources: list[dict]) -> str:
    if not sources:
        return ""
    rows = []
    for s in sources:
        title = s.get("title") or s.get("id") or ""
        url = s.get("url")
        if url:
            link = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>'
        else:
            link = esc(title)
        meta_bits = []
        if s.get("publisher"):
            meta_bits.append(esc(s["publisher"]))
        if s.get("publication_year"):
            meta_bits.append(str(s["publication_year"]))
        if s.get("source_type"):
            meta_bits.append(esc(s["source_type"]))
        meta = " / ".join(meta_bits)
        rows.append(f"<li>{link}{(' — ' + meta) if meta else ''}</li>")
    return (
        "<h3>主な出典</h3>\n"
        "<ul class=\"source-list\">\n" + "\n".join(rows) + "\n</ul>"
    )


def render_fit_section(school: dict, testimonials: list[dict]) -> str:
    """合うお子さん・慎重に検討すべきお子さん（汎用テキスト）"""
    name = esc(school.get("name_ja", "本校"))
    gender = GENDER_LABEL.get(school.get("gender_type") or "", "")
    rel = school.get("religious_affiliation") or "unknown"
    integrated = INTEGRATED_LABEL.get(school.get("integrated_type") or "", "")

    fit_points = ["自分の関心領域を粘り強く掘り下げたいお子さん"]
    careful_points = ["集団生活より個別最適化された環境を必要とするお子さん"]

    if gender == "男子校":
        fit_points.append("男子集団のなかで切磋琢磨することで力を伸ばせるお子さん")
        careful_points.append("男子集団特有の文化に違和感を抱きやすいお子さん")
    elif gender == "女子校":
        fit_points.append("女子だけの環境で安心して自己表現を伸ばしたいお子さん")
        careful_points.append("男女混在の社会的経験を中学段階から重視したいご家庭")
    else:
        fit_points.append("男女ともに対等な学習文化のなかで関係性を育みたいお子さん")

    if rel == "catholic":
        fit_points.append("祈りや内省の時間を学校生活のリズムに織り込まれることを肯定的に受け止められるご家庭")
        careful_points.append("無宗教家庭で、宗教行事への参加に強い違和感が想定されるお子さん")
    elif rel == "protestant":
        fit_points.append("プロテスタント系の落ち着いた信仰環境を歓迎するご家庭")
        careful_points.append("宗教的価値観の存在自体に距離を取りたいご家庭")
    elif rel == "buddhist":
        fit_points.append("日本の伝統的な精神文化と教育を結びつけて学ばせたいご家庭")
    elif rel == "non_religious":
        fit_points.append("特定の信仰背景を持たない、フラットな進学環境を希望するご家庭")

    if integrated.startswith("完全"):
        fit_points.append("中学受験のあと、高校受験を経ずに6年間を腰を据えて過ごしたいお子さん")
    elif integrated == "附属型":
        fit_points.append("系列大学への進学ルートを視野に、大学受験プレッシャーを抑えた中等教育を望むご家庭")
        careful_points.append("難関大学受験に向けて中学から戦略的に学習を積み上げたいご家庭は、附属型の進路設計が合うか要確認")

    sentiments = [t.get("sentiment") for t in testimonials]
    if sentiments and sentiments.count("negative") + sentiments.count("mixed") >= max(2, len(sentiments) // 5):
        careful_points.append("批判的な声・両義的な声が一定数あるため、説明会で具体的な改善努力を確認することを推奨")

    fit_html = "\n".join(f"<li>{p}</li>" for p in fit_points)
    careful_html = "\n".join(f"<li>{p}</li>" for p in careful_points)

    return (
        f"<p>{name}を志望するうえで、お子さんとの相性を判断するための観点を整理します。"
        "ここで示すのは汎用的な指針であり、最終的にはお子さん本人が学校の空気に触れた感触を最重要視してください。</p>"
        "<h3>合うお子さん・ご家庭</h3>\n"
        f"<ul>\n{fit_html}\n</ul>\n"
        "<h3>慎重に検討すべきお子さん・ご家庭</h3>\n"
        f"<ul>\n{careful_html}\n</ul>\n"
        "<p>これらは「合わない」を意味するものではなく、説明会・体験授業・在校生との対話の中で"
        "重点的に確認すべき観点として、お子さんとご家庭の感覚と照合いただくためのチェックポイントです。</p>"
    )


# ------------------------------------------------------------
# 本体テンプレート
# ------------------------------------------------------------

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} | JPMS-DB 学校レポート</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700;900&family=Noto+Serif+JP:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root{{
    --akashiro-red:#CC1400;
    --akashiro-red-light:#E63D2C;
    --bg:#FFFFFF;
    --ink:#0E0E0E;
    --ink-soft:#3A3A3A;
    --line:#E5E5E5;
    --bg-soft:#FAFAFA;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{
    font-family:'Noto Serif JP',serif;
    background:var(--bg);color:var(--ink);
    line-height:1.95;font-size:15.5px;font-weight:400;
  }}
  header{{
    border-bottom:3px solid var(--akashiro-red);
    padding:36px 56px 24px;background:var(--bg);
  }}
  .brand{{display:flex;align-items:baseline;gap:18px;font-family:'Noto Sans JP',sans-serif}}
  .brand h1{{
    font-family:'Noto Serif JP',serif;font-size:24px;font-weight:700;
    letter-spacing:0.05em;color:var(--akashiro-red);
  }}
  .brand .sub{{font-size:13px;color:var(--ink-soft);font-weight:400}}
  nav{{margin-top:14px;font-family:'Noto Sans JP',sans-serif;font-size:13px}}
  nav a{{color:var(--ink-soft);text-decoration:none;margin-right:24px}}
  nav a:hover{{color:var(--akashiro-red)}}
  main{{max-width:880px;margin:0 auto;padding:48px 56px 100px}}

  .doc-meta{{
    font-family:'Noto Sans JP',sans-serif;font-size:12px;
    color:var(--ink-soft);border-bottom:1px solid var(--line);
    padding-bottom:16px;margin-bottom:32px;letter-spacing:0.05em;
  }}
  h1.title{{font-size:32px;font-weight:700;line-height:1.45;margin-bottom:12px;letter-spacing:0.02em}}
  .subtitle{{
    font-size:15px;color:var(--akashiro-red);font-weight:400;
    margin-bottom:32px;font-family:'Noto Sans JP',sans-serif;
  }}
  .lead{{font-size:15.5px;line-height:2.05;margin-bottom:36px}}

  .school-section{{margin:48px 0 56px;padding-bottom:24px;border-bottom:1px dashed var(--line)}}
  h2{{
    font-size:24px;font-weight:700;margin:0 0 24px;
    padding:12px 0 12px 20px;border-left:6px solid var(--akashiro-red);line-height:1.5;
  }}
  h2 .num{{
    color:var(--akashiro-red);font-size:12px;display:block;letter-spacing:0.15em;
    font-family:'Noto Sans JP',sans-serif;font-weight:500;margin-bottom:6px;
  }}
  h3{{
    font-size:16px;font-weight:700;margin:32px 0 12px;
    color:var(--akashiro-red-light);font-family:'Noto Sans JP',sans-serif;letter-spacing:0.03em;
  }}
  p{{margin-bottom:16px;text-align:justify}}

  .meta-table{{
    width:100%;border-collapse:collapse;
    font-family:'Noto Sans JP',sans-serif;font-size:13px;margin:14px 0 28px;
  }}
  .meta-table caption{{
    text-align:left;font-size:11px;color:var(--akashiro-red);
    margin-bottom:6px;letter-spacing:0.1em;font-weight:500;
  }}
  .meta-table th,.meta-table td{{
    padding:9px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top;
  }}
  .meta-table th{{
    background:var(--bg-soft);color:var(--akashiro-red);
    font-weight:500;width:160px;font-size:12px;letter-spacing:0.05em;
  }}
  .meta-table td.num-cell{{width:80px;text-align:right;font-feature-settings:"tnum"}}
  blockquote{{
    border-left:3px solid var(--akashiro-red);padding:14px 22px;margin:16px 0;
    background:var(--bg-soft);font-size:14.5px;color:var(--ink);font-style:normal;
  }}
  blockquote .who{{
    display:block;font-style:normal;font-size:11px;
    color:var(--akashiro-red);margin-top:10px;letter-spacing:0.05em;
    font-family:'Noto Sans JP',sans-serif;
  }}
  .sent-tag{{
    display:inline-block;font-size:10px;
    padding:1px 6px;margin-left:8px;
    border-radius:2px;border:1px solid var(--akashiro-red);
    color:var(--akashiro-red);background:#fff;
  }}
  .sent-negative{{border-color:#0033AA;color:#0033AA}}
  .sent-mixed{{border-color:#888;color:#555}}
  .sent-neutral{{border-color:#888;color:#555}}

  .bar-wrap{{
    width:100%;height:10px;background:var(--bg-soft);
    border:1px solid var(--line);overflow:hidden;
  }}
  .bar{{height:100%;background:var(--akashiro-red)}}
  .bar-positive{{background:var(--akashiro-red)}}
  .bar-negative{{background:#0033AA}}
  .bar-mixed{{background:#9A6B00}}
  .bar-neutral{{background:#888}}

  ul,ol{{margin:0 0 18px 24px}}
  ul li,ol li{{margin-bottom:6px;line-height:1.85}}
  .source-list{{font-family:'Noto Sans JP',sans-serif;font-size:13px}}
  .source-list a{{color:var(--akashiro-red);text-decoration:none}}
  .source-list a:hover{{text-decoration:underline}}

  .warn{{
    background:#FFF7E6;border:1px solid #E5A300;color:#7A4F00;
    padding:12px 18px;font-family:'Noto Sans JP',sans-serif;font-size:12.5px;
    margin:24px 0;
  }}

  footer{{
    border-top:1px solid var(--line);padding:32px 56px;text-align:center;
    color:var(--ink-soft);font-size:12px;font-family:'Noto Sans JP',sans-serif;
  }}
  .top-link{{
    position:fixed;bottom:24px;right:24px;background:var(--akashiro-red);color:#fff;
    padding:10px 16px;font-size:12px;text-decoration:none;
    font-family:'Noto Sans JP',sans-serif;box-shadow:0 2px 8px rgba(0,0,0,0.15);
  }}
  .db-link-card{{
    background:var(--bg-soft);border:2px solid var(--akashiro-red);
    padding:24px;margin:32px 0;font-family:'Noto Sans JP',sans-serif;
  }}
  .db-link-card a{{
    display:inline-block;background:var(--akashiro-red);color:#fff;
    padding:10px 20px;text-decoration:none;font-size:13px;letter-spacing:0.05em;
    margin-top:12px;
  }}

  @media(max-width:680px){{
    main{{padding:32px 20px 80px}}
    h1.title{{font-size:24px}}
    h2{{font-size:20px}}
    .meta-table th{{width:110px}}
  }}
</style>
</head>
<body id="top">
<header>
  <div class="brand">
    <h1>JPMS-DB</h1>
    <span class="sub">日本私立中学校 包括的基盤データベース</span>
  </div>
  <nav>
    <a href="../index.html">ダッシュボード</a>
    <a href="./index.html">学校レポート一覧</a>
    <a href="../sample-12-schools.html">サンプル12校レポート（拡張版）</a>
  </nav>
</header>

<main>
  <div class="doc-meta">SCHOOL REPORT — {today} | JPMS-DB | {school_id} | 自動生成</div>

  <h1 class="title">{name}</h1>
  <p class="subtitle">{subtitle}</p>

{warning_block}

  <p class="lead">{lead}</p>

{outline_section}

{philosophy_section}

{curriculum_section}

{testimonials_section}

{outcomes_section}

{sentiment_section}

{fit_section}

{db_link_section}

{sources_section}

</main>

<a href="#top" class="top-link">↑ 先頭へ</a>

<footer>
  JPMS-DB | 日本私立中学校 包括的基盤データベース | 学校レポート自動生成エンジン v0.1<br>
  本ページは jpms.db のデータをもとにスクリプトで自動生成されています。
  事実誤認・更新漏れにお気づきの場合は、JPMS-DBプロジェクトまでお知らせください。
</footer>
</body>
</html>
"""


def render_outline(school: dict, testimonials: list[dict]) -> str:
    name = esc(school.get("name_ja", "本校"))
    pref = esc(school.get("location_pref") or "")
    city = esc(school.get("location_city") or "")
    gender = GENDER_LABEL.get(school.get("gender_type") or "", "")
    integrated = INTEGRATED_LABEL.get(school.get("integrated_type") or "", "")
    rel = school.get("religious_affiliation")
    rel_label = RELIGIOUS_LABEL.get(rel or "unknown", "")
    year = school.get("establishment_year")

    sentence_parts = [name + "は"]
    loc_parts = [p for p in [pref, city] if p]
    if loc_parts:
        sentence_parts.append("、" + "".join(loc_parts) + "に位置する")
    school_kind = []
    if gender:
        school_kind.append(gender)
    if integrated:
        school_kind.append(integrated)
    if rel and rel not in ("unknown", "non_religious"):
        school_kind.append(rel_label + "系")
    if school_kind:
        sentence_parts.append("、".join(school_kind) + "の中学校です。")
    else:
        sentence_parts.append("中学校です。")

    if year:
        sentence_parts.append(f"創立は{year}年で、")
        sentence_parts.append("地域社会のなかで長い歴史を積み重ねてきた学校のひとつに数えられます。")

    intro = "".join(sentence_parts)
    body = (
        f"<p>{intro}</p>\n"
        "<p>本ページは、JPMS-DB（日本私立中学校 包括的基盤データベース）が収集している"
        "学校公式情報・関係者発言・公開取材記事をもとに、当該校の輪郭を保護者向けに整理したレポートです。"
        "ランキングや序列で他校と比較するのではなく、教育の設計思想と現場の声から"
        "「お子さんと合うかどうか」を判断する素材を提供することを意図しています。</p>"
    )
    if testimonials:
        body += (
            f"<p>本ページの記述は、JPMS-DBに登録されている関係者発言{len(testimonials)}件と、"
            "公式サイト等の公開情報を主たる根拠としています。"
            "発言は出典明記の上で原文に近い形で引用し、未成年の発言は匿名化しています。</p>"
        )
    return body


def render_philosophy(school: dict) -> str:
    parts = []
    if school.get("founding_philosophy"):
        parts.append(
            f"<p>{esc(school['founding_philosophy'])}</p>"
        )
    if school.get("education_principle"):
        parts.append(
            "<h3>教育目標・教育方針</h3>\n"
            f"<p>{esc(school['education_principle'])}</p>"
        )
    if not parts:
        parts.append(
            "<p>建学の精神と教育目標に関する正規テキストはJPMS-DBに未登録です。"
            "公式サイトの「教育理念」「建学の精神」ページを直接ご参照ください。"
            "今後の調査フェーズで本ページの記述は順次拡充されます。</p>"
        )
    return "\n".join(parts)


# ------------------------------------------------------------
# 1校レポート生成
# ------------------------------------------------------------

def generate_report(school_id: str, *, verbose: bool = True) -> tuple[bool, list[str], dict]:
    """1校のレポートを生成。(成功フラグ, 警告リスト, スクール情報) を返す。"""
    warnings: list[str] = []
    with connect() as conn:
        school = fetch_school(conn, school_id)
        if not school:
            return False, [f"学校IDが見つかりません: {school_id}"], {}
        curriculum = fetch_curriculum(conn, school_id)
        stats = fetch_stats(conn, school_id)
        outcomes = fetch_outcomes(conn, school_id)
        testimonials = fetch_testimonials(conn, school_id)
        sources = fetch_sources(conn, school_id)

    # 品質ゲート
    if len(testimonials) < MIN_TESTIMONIALS:
        warnings.append(
            f"関係者発言が{len(testimonials)}件のみ（推奨{MIN_TESTIMONIALS}件以上）"
        )
    if not school.get("founding_philosophy"):
        warnings.append("建学の精神が未登録")
    if not school.get("education_principle"):
        warnings.append("教育目標が未登録")
    if not curriculum:
        warnings.append("教育プログラム特性データが未登録")

    # 本文構築
    name = school.get("name_ja", school_id)
    today = date.today().isoformat()
    subtitle = []
    if school.get("location_pref"):
        subtitle.append(school["location_pref"] + (school.get("location_city") or ""))
    if school.get("gender_type"):
        subtitle.append(GENDER_LABEL.get(school["gender_type"], ""))
    if school.get("integrated_type"):
        subtitle.append(INTEGRATED_LABEL.get(school["integrated_type"], ""))
    if school.get("religious_affiliation") and school["religious_affiliation"] not in ("unknown", "non_religious"):
        subtitle.append(RELIGIOUS_LABEL.get(school["religious_affiliation"], ""))

    lead = (
        f"本ページは、JPMS-DBが{name}について収集している基本情報・教育プログラム・"
        f"関係者発言・進学実績を一望できる形で整理した、自動生成の学校レポートです。"
        f"全国525校のうち、関係者発言が一定数収集できた学校から順に公開しており、"
        f"記述はランキング目的ではなく、お子さんとの相性判断材料の提供を目的としています。"
    )

    warning_block = ""
    if warnings:
        items = "".join(f"<li>{esc(w)}</li>" for w in warnings)
        warning_block = (
            f'<div class="warn"><strong>本レポートの注意事項：</strong>'
            f"以下の項目はJPMS-DB上で蓄積が浅いため、記述に制約があります。"
            f"<ul style=\"margin:8px 0 0 18px\">{items}</ul></div>"
        )

    meta_table = render_meta_table(school, curriculum)
    outline_html = render_outline(school, testimonials)
    philosophy_html = render_philosophy(school)
    curriculum_html = render_curriculum(curriculum)
    testimonials_html = render_testimonials(testimonials)
    outcomes_html = render_outcomes(outcomes)
    sentiment_html = render_sentiment_summary(testimonials)
    fit_html = render_fit_section(school, testimonials)
    sources_html = render_sources(sources)

    # 各 section をラップ
    def section(num: int, title: str, body: str) -> str:
        return (
            f'<section class="school-section" id="sec-{num}">\n'
            f'<h2><span class="num">SECTION {num:02d}</span>{title}</h2>\n'
            f"{body}\n</section>"
        )

    outline_section = section(1, "学校の輪郭", meta_table + "\n" + outline_html)
    philosophy_section = section(2, "建学の精神", philosophy_html)
    curriculum_section = section(3, "教員と教育プログラム", curriculum_html)
    testimonials_section = section(4, "関係者の声", testimonials_html)
    outcomes_section = section(5, "進学実績", outcomes_html)
    sentiment_section = section(6, "元データ量と感情分布", sentiment_html)
    fit_section = section(7, "合うお子さん・慎重に検討すべきお子さん", fit_html)

    db_link_section = section(
        8,
        "詳細はJPMS-DBへ",
        '<div class="db-link-card">\n'
        f"<p>本レポートは、JPMS-DB（日本私立中学校 包括的基盤データベース）に登録されている"
        f"{esc(name)}のデータから、保護者向けに自動編集したサマリーです。"
        f"発言の原文・出典・関連データの完全版は、JPMS-DBダッシュボードでご確認いただけます。</p>"
        f'<a href="../index.html#school-{esc(school_id)}">ダッシュボードで詳細を見る</a>\n'
        "</div>"
    )

    sources_section = ""
    if sources_html:
        sources_section = section(9, "出典一覧", sources_html)

    html_str = PAGE_TEMPLATE.format(
        name=esc(name),
        subtitle=esc(" / ".join(s for s in subtitle if s)),
        today=today,
        school_id=esc(school_id),
        warning_block=warning_block,
        lead=esc(lead),
        outline_section=outline_section,
        philosophy_section=philosophy_section,
        curriculum_section=curriculum_section,
        testimonials_section=testimonials_section,
        outcomes_section=outcomes_section,
        sentiment_section=sentiment_section,
        fit_section=fit_section,
        db_link_section=db_link_section,
        sources_section=sources_section,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{school_id}.html"
    out_path.write_text(html_str, encoding="utf-8")

    if verbose:
        print(f"  Written: {out_path}  ({len(html_str):,} chars)")
        for w in warnings:
            print(f"    [WARN] {w}")

    return True, warnings, school


# ------------------------------------------------------------
# インデックスページ
# ------------------------------------------------------------

def list_eligible_schools() -> list[dict]:
    """testimonials 5件以上の学校（基本情報含む）"""
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT s.id, s.name_ja, s.location_pref, s.location_city,
                   s.gender_type, s.integrated_type, s.religious_affiliation,
                   s.establishment_year,
                   (SELECT COUNT(*) FROM jpms_testimonials t WHERE t.school_id = s.id) AS n_testimonials
            FROM jpms_schools s
            WHERE (SELECT COUNT(*) FROM jpms_testimonials t WHERE t.school_id = s.id) >= {MIN_TESTIMONIALS}
            ORDER BY s.location_pref, s.id
            """
        ).fetchall()
    return [dict(r) for r in rows]


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>学校レポート一覧 | JPMS-DB</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Noto+Serif+JP:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root{{
    --akashiro-red:#CC1400;--bg:#FFFFFF;--ink:#0E0E0E;
    --ink-soft:#3A3A3A;--line:#E5E5E5;--bg-soft:#FAFAFA;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Noto Sans JP',sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;font-size:14px}}
  header{{border-bottom:3px solid var(--akashiro-red);padding:32px 48px 24px}}
  .brand{{display:flex;align-items:baseline;gap:18px}}
  .brand h1{{font-family:'Noto Serif JP',serif;font-size:24px;color:var(--akashiro-red);letter-spacing:0.05em}}
  .brand .sub{{font-size:13px;color:var(--ink-soft)}}
  nav{{margin-top:14px;font-size:13px}}
  nav a{{color:var(--ink-soft);text-decoration:none;margin-right:24px}}
  nav a:hover{{color:var(--akashiro-red)}}
  main{{max-width:1080px;margin:0 auto;padding:32px 48px 80px}}
  h2{{font-family:'Noto Serif JP',serif;font-size:28px;margin-bottom:8px}}
  .lead{{color:var(--ink-soft);margin-bottom:32px;max-width:760px;line-height:1.95}}
  .stats-row{{
    display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:1px;background:var(--line);border:1px solid var(--line);margin:24px 0 40px;
  }}
  .stat{{background:var(--bg);padding:18px}}
  .stat .num{{font-family:'Noto Serif JP',serif;font-size:32px;color:var(--akashiro-red);font-weight:700;line-height:1}}
  .stat .label{{font-size:11px;color:var(--ink-soft);margin-top:8px;letter-spacing:0.05em}}
  .filter-bar{{
    display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;align-items:center;
    padding:14px;background:var(--bg-soft);border:1px solid var(--line);
  }}
  .filter-bar input,.filter-bar select{{
    padding:8px 12px;border:1px solid var(--line);background:var(--bg);
    font-family:inherit;font-size:13px;
  }}
  .filter-bar input{{flex:1;min-width:200px}}
  table{{width:100%;border-collapse:collapse;font-size:13px;background:var(--bg)}}
  th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{background:var(--bg-soft);font-weight:500;color:var(--ink-soft);font-size:12px;letter-spacing:0.05em;position:sticky;top:0}}
  td.right,th.right{{text-align:right;font-feature-settings:"tnum"}}
  td a{{color:var(--akashiro-red);text-decoration:none;font-weight:500}}
  td a:hover{{text-decoration:underline}}
  .tag{{
    display:inline-block;font-size:11px;padding:1px 6px;margin-right:4px;
    border:1px solid var(--line);color:var(--ink-soft);border-radius:2px;background:var(--bg-soft);
  }}
  footer{{border-top:1px solid var(--line);padding:24px 48px;text-align:center;color:var(--ink-soft);font-size:12px}}
</style>
</head>
<body>
<header>
  <div class="brand">
    <h1>JPMS-DB</h1>
    <span class="sub">日本私立中学校 包括的基盤データベース</span>
  </div>
  <nav>
    <a href="../index.html">ダッシュボード</a>
    <a href="./index.html">学校レポート一覧</a>
    <a href="../sample-12-schools.html">サンプル12校レポート（拡張版）</a>
  </nav>
</header>
<main>
  <h2>学校レポート一覧</h2>
  <p class="lead">JPMS-DBに収録されている全525校のうち、基本情報と関係者発言{min_t}件以上が蓄積され、
  自動レポート生成の品質ゲートを通過した学校の一覧です。{count}校が対象となっています。
  各校の詳細レポートは、関係者発言を立場別・感情別に整理し、合うお子さんの観点まで含めて
  自動編集されたサマリーとして閲覧いただけます。データが拡充されるたびに対象校は順次拡大されます。</p>

  <div class="stats-row">
    <div class="stat"><div class="num">{count}</div><div class="label">レポート生成済み校</div></div>
    <div class="stat"><div class="num">525</div><div class="label">JPMS-DB登録校（全国）</div></div>
    <div class="stat"><div class="num">{coverage:.1f}%</div><div class="label">カバー率</div></div>
    <div class="stat"><div class="num">{total_test}</div><div class="label">関係者発言（合計）</div></div>
  </div>

  <div class="filter-bar">
    <input id="search" type="text" placeholder="学校名・都道府県で絞り込み...">
    <select id="filter-pref">
      <option value="">都道府県すべて</option>
      {pref_options}
    </select>
    <select id="filter-gender">
      <option value="">校種すべて</option>
      <option value="boys">男子校</option>
      <option value="girls">女子校</option>
      <option value="coed">共学</option>
    </select>
  </div>

  <table id="school-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>学校名</th>
        <th>所在地</th>
        <th>校種</th>
        <th class="right">創立</th>
        <th class="right">発言数</th>
        <th>レポート</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</main>
<footer>
  JPMS-DB 学校レポート自動生成エンジン v0.1 | 最終更新: {today}
</footer>
<script>
  const search = document.getElementById('search');
  const filterPref = document.getElementById('filter-pref');
  const filterGender = document.getElementById('filter-gender');
  const rows = document.querySelectorAll('#school-table tbody tr');
  function applyFilter(){{
    const q = search.value.trim();
    const pref = filterPref.value;
    const gender = filterGender.value;
    rows.forEach(r => {{
      const name = r.dataset.name || '';
      const p = r.dataset.pref || '';
      const g = r.dataset.gender || '';
      const matches = (!q || name.includes(q) || p.includes(q))
        && (!pref || p === pref)
        && (!gender || g === gender);
      r.style.display = matches ? '' : 'none';
    }});
  }}
  search.addEventListener('input', applyFilter);
  filterPref.addEventListener('change', applyFilter);
  filterGender.addEventListener('change', applyFilter);
</script>
</body>
</html>
"""


def generate_index(eligible: list[dict]) -> Path:
    today = date.today().isoformat()
    count = len(eligible)
    coverage = (count / 525 * 100) if count else 0
    total_test = sum(s["n_testimonials"] for s in eligible)

    prefs = sorted({s["location_pref"] for s in eligible if s.get("location_pref")})
    pref_options = "\n      ".join(
        f'<option value="{esc(p)}">{esc(p)}</option>' for p in prefs
    )

    rows_html = []
    for s in eligible:
        loc = (s.get("location_pref") or "") + (s.get("location_city") or "")
        gender = GENDER_LABEL.get(s.get("gender_type") or "", "")
        integrated = INTEGRATED_LABEL.get(s.get("integrated_type") or "", "")
        rel = s.get("religious_affiliation") or ""
        rel_label = RELIGIOUS_LABEL.get(rel, "") if rel and rel not in ("unknown", "non_religious") else ""

        kind_tags = "".join(
            f'<span class="tag">{esc(t)}</span>' for t in [gender, integrated, rel_label] if t
        )
        rows_html.append(
            f'<tr data-name="{esc(s["name_ja"])}" '
            f'data-pref="{esc(s.get("location_pref") or "")}" '
            f'data-gender="{esc(s.get("gender_type") or "")}">'
            f"<td><code>{esc(s['id'])}</code></td>"
            f"<td><strong>{esc(s['name_ja'])}</strong></td>"
            f"<td>{esc(loc)}</td>"
            f"<td>{kind_tags or '—'}</td>"
            f'<td class="right">{esc(str(s["establishment_year"]) if s.get("establishment_year") else "—")}</td>'
            f'<td class="right">{s["n_testimonials"]}</td>'
            f'<td><a href="./{esc(s["id"])}.html">レポートを見る →</a></td>'
            f"</tr>"
        )

    html_str = INDEX_TEMPLATE.format(
        min_t=MIN_TESTIMONIALS,
        count=count,
        coverage=coverage,
        total_test=total_test,
        pref_options=pref_options,
        rows="\n".join(rows_html) if rows_html else (
            '<tr><td colspan="7" style="text-align:center;color:#888;padding:40px">'
            "対象校がありません。testimonials 収集を進めてください。</td></tr>"
        ),
        today=today,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(html_str, encoding="utf-8")
    return INDEX_PATH


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("school", nargs="?", help="学校ID（jpms_s_0001 等）または学校名（部分一致）")
    parser.add_argument("--all", action="store_true", help="testimonials 5件以上の全校を生成")
    parser.add_argument("--index", action="store_true", help="インデックスHTMLのみ再生成")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    verbose = not args.quiet

    if args.index and not (args.all or args.school):
        eligible = list_eligible_schools()
        idx = generate_index(eligible)
        if verbose:
            print(f"Index regenerated: {idx} ({len(eligible)} schools)")
        return 0

    generated_ok: list[str] = []
    failed: list[str] = []

    if args.all:
        eligible = list_eligible_schools()
        if verbose:
            print(f"--all: {len(eligible)}校を生成します")
        for s in eligible:
            ok, _warns, _meta = generate_report(s["id"], verbose=verbose)
            (generated_ok if ok else failed).append(s["id"])
        idx = generate_index(eligible)
        if verbose:
            print(f"\nIndex: {idx}")
            print(f"成功: {len(generated_ok)}校 / 失敗: {len(failed)}校")
        return 0 if not failed else 1

    if not args.school:
        parser.print_help()
        return 1

    with connect() as conn:
        sid = resolve_school_id(conn, args.school)
    if not sid:
        print(f"学校が見つかりません: {args.school}", file=sys.stderr)
        return 2

    ok, warns, meta = generate_report(sid, verbose=verbose)
    if not ok:
        return 2

    # 単発生成でもインデックスは再生成（既存リストと整合させる）
    eligible = list_eligible_schools()
    generate_index(eligible)
    if verbose:
        print(f"Index updated: {INDEX_PATH} ({len(eligible)} schools eligible)")

    return 0 if not warns else 0  # 警告は exit code に反映しない（出力には含める）


if __name__ == "__main__":
    raise SystemExit(main())
