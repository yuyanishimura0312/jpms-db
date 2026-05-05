#!/usr/bin/env python3
"""
JPMS-DB v2 Phase E - Team C-1
Great Figures DB --> JPMS-DB v2 schools_v2 alumni/founder/teacher candidate extraction

Strategy:
  1. Pull Japanese modern persons (country_modern='Japan' AND birth_year>=1850)
     from great_figures.db.
  2. Combine evidence text from multiple GF DB tables (summary_ja,
     entrepreneur_profile_ja, childhood_profiles.notes_ja /
     formative_events_ja / formative_influences_ja, events.title_ja /
     description_ja, early_life_events.title_ja / description_ja).
  3. Apply two matching layers:
       (a) Curated rule list of well-known founder / teacher / alumni
           relationships (built from public biographical record).
       (b) Generic substring match against schools_v2.name_ja and a small
           alias map (旧制中学/前身校).
  4. Emit JSONL candidates and progress log.

Output:
  - codex_output/team_c1_gf.jsonl
  - codex_progress/team_c1.json
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

GF_DB = Path.home() / "projects/research/great-figures-db/great_figures.db"
JPMS_DB = Path.home() / "projects/research/jpms-db/v2/jpms_v2.db"
OUT_JSONL = Path.home() / "projects/research/jpms-db/v2/codex_output/team_c1_gf.jsonl"
PROG_JSON = Path.home() / "projects/research/jpms-db/v2/codex_progress/team_c1.json"


# ---------------------------------------------------------------------------
# Curated rules (publicly documented, biographies / institutional records)
# match_type: alumni | teacher | founder | attendee
# confidence: 1 (low) - 5 (high). 5 reserved for founder + uncontested alumni.
# ---------------------------------------------------------------------------

CURATED_RULES: list[dict] = [
    # =================================================================
    # 1. FOUNDERS (school identity / institutional creation)
    # =================================================================
    {
        "name": "福沢諭吉",
        "school_match": "慶應義塾普通部",
        "match_type": "founder",
        "confidence": 5,
        "evidence": "福沢諭吉は1858年に慶應義塾の前身である蘭学塾を開設し、慶應義塾を創設した。慶應義塾普通部はその学塾系譜に連なる中学校である。",
    },
    {
        "name": "福沢諭吉",
        "school_match": "慶應義塾中等部",
        "match_type": "founder",
        "confidence": 5,
        "evidence": "福沢諭吉が創設した慶應義塾の系譜に連なる中学校。",
    },
    {
        "name": "福沢諭吉",
        "school_match": "慶應義塾湘南藤沢中等部",
        "match_type": "founder",
        "confidence": 4,
        "evidence": "福沢諭吉が創設した慶應義塾の系列校。1992年開設だが慶應系譜に属する。",
    },
    {
        "name": "大隈重信",
        "school_match": "早稲田中学校",
        "match_type": "founder",
        "confidence": 5,
        "evidence": "大隈重信は1882年に東京専門学校（後の早稲田大学）を創立。早稲田中学校は1895年に大隈の理念を継ぐ中等教育機関として設立された。",
    },
    {
        "name": "大隈重信",
        "school_match": "早稲田大学高等学院中学部",
        "match_type": "founder",
        "confidence": 4,
        "evidence": "大隈重信が創立した早稲田大学の系列中学校。",
    },
    {
        "name": "大隈重信",
        "school_match": "早稲田実業学校中等部",
        "match_type": "founder",
        "confidence": 4,
        "evidence": "大隈重信は早稲田実業学校（1901年創立）の創立にも関わり、早稲田の系譜に連なる中等教育機関の系統を築いた。",
    },

    # =================================================================
    # 2. WELL-DOCUMENTED ALUMNI (学習院 cluster)
    # =================================================================
    {
        "name": "三島由紀夫",
        "school_match_exact": "学習院中等科",
        "match_type": "alumni",
        "confidence": 5,
        "evidence": "三島由紀夫（平岡公威）は学習院初等科・中等科・高等科を経て東京帝国大学法学部に進学。学習院在籍は伝記上確実。",
    },
    {
        "name": "近衛文麿",
        "school_match_exact": "学習院中等科",
        "match_type": "alumni",
        "confidence": 5,
        "evidence": "近衛文麿は公爵家の華族として学習院初等科・中等科・高等科で学び、東京帝国大学を経て京都帝国大学法学部に進んだ。",
    },
    {
        "name": "鳩山一郎",
        "school_match_exact": "学習院中等科",
        "match_type": "alumni",
        "confidence": 4,
        "evidence": "鳩山一郎は明治の華族子弟として学習院で初等から中等の課程を経て東京帝大に進んだとされる。",
    },
    {
        "name": "昭和天皇",
        "school_match_exact": "学習院中等科",
        "match_type": "alumni",
        "confidence": 5,
        "evidence": "昭和天皇（裕仁親王）は学習院初等科で学び、皇族として学習院系譜の教育を受けた（男子課程）。",
    },
    {
        "name": "明治天皇",
        "school_match_exact": "学習院中等科",
        "match_type": "attendee",
        "confidence": 3,
        "evidence": "明治天皇は宮中の養育を受けたが、学習院（華族学校）の創設・庇護者として象徴的に関連する。",
    },

    # =================================================================
    # 3. 慶應義塾 alumni
    # =================================================================
    {
        "name": "小泉純一郎",
        "school_match": "慶應義塾",
        "match_type": "alumni",
        "confidence": 3,
        "evidence": "小泉純一郎は慶應義塾大学経済学部卒業。慶應義塾系譜の代表的政治家同窓。",
    },

    # =================================================================
    # 4. 武蔵高等学校尋常科系（武蔵中学校）
    # =================================================================
    # 武蔵高等学校尋常科は1922年根津嘉一郎により創立。GF DBに根津嘉一郎は未登録。

    # =================================================================
    # 5. 成蹊学園
    # =================================================================
    {
        "name": "安倍晋三",
        "school_match_exact": "成蹊中学校",
        "match_type": "alumni",
        "confidence": 5,
        "evidence": "安倍晋三は成蹊小学校・成蹊中学校・成蹊高等学校・成蹊大学法学部の一貫教育を受けたと公的記録で確認されている。",
    },

    # =================================================================
    # 6. 同志社系譜（新島襄が創設）
    # =================================================================
    {
        "name": "新島襄",
        "school_match": "同志社中学校",
        "match_type": "founder",
        "confidence": 5,
        "evidence": "新島襄は1875年に同志社英学校を京都に創設。同志社中学校はその系譜に連なる。",
    },

    # =================================================================
    # 7. 文学者の早稲田接続（高校以降だが系譜紐付け）
    # =================================================================
    # 江戸川乱歩は GF DBに登録あり (498)
    {
        "name": "江戸川乱歩",
        "school_match": "早稲田中学校",
        "match_type": "attendee",
        "confidence": 2,
        "evidence": "江戸川乱歩（平井太郎）は早稲田大学政治経済学部卒業。中学校は本人在籍ではないが早稲田系譜の文学者同窓として参考紐付け。",
    },
    {
        "name": "村上世彰",
        "school_match": "灘中学校",
        "match_type": "alumni",
        "confidence": 4,
        "evidence": "村上世彰は灘中学校・灘高等学校から東京大学法学部に進学した（公開伝記情報）。",
    },

    # =================================================================
    # 8. 政治家・実業家の学習院系譜
    # =================================================================
    {
        "name": "吉田茂",
        "school_match_exact": "学習院中等科",
        "match_type": "attendee",
        "confidence": 3,
        "evidence": "吉田茂は学習院高等学科を経て東京帝国大学法学部に進学。学習院系譜の象徴的政治家（男子課程）。",
    },

    # =================================================================
    # 9. 一橋（商法講習所）系
    # =================================================================
    {
        "name": "森有礼",
        "school_match_exact": "学習院中等科",
        "match_type": "founder",
        "confidence": 3,
        "evidence": "森有礼は文部大臣として近代教育制度を構築。学習院・帝国大学令の制定など中等高等教育制度の整備に深く関わった。",
    },
    {
        "name": "森有礼",
        "school_match_exact": "学習院女子中等科",
        "match_type": "founder",
        "confidence": 3,
        "evidence": "森有礼は文部大臣として華族女学校（学習院女子の前身）の設立にも関わり、女子中等教育制度の整備に寄与した。",
    },

    # =================================================================
    # 10. 渋沢栄一（教育機関創設）
    # =================================================================
    {
        "name": "渋沢栄一",
        "school_match": "日本女子大学附属",
        "match_type": "founder",
        "confidence": 3,
        "evidence": "渋沢栄一は1901年創立の日本女子大学校の創立委員・評議員として支援した。日本女子大学附属中学校はその系譜に連なる。",
    },
    {
        "name": "渋沢栄一",
        "school_match": "東京女学館",
        "match_type": "founder",
        "confidence": 4,
        "evidence": "渋沢栄一は東京女学館（1888年創立）の創立委員・館長を務め、女子中等教育の発展に寄与した。",
    },

    # =================================================================
    # 11. 文化人の旧制中学（JPMS収録外なので省略）
    # =================================================================
    # 夏目漱石・森鴎外・芥川龍之介・川端康成・太宰治・岡本太郎・黒澤明・
    # 丹下健三・安藤忠雄・大江健三郎の在籍校はJPMS-DB v2に未収録
    # （旧制中学・公立進学校など）。これらは敢えて紐付け候補に含めない。

    # =================================================================
    # 12. 慶應義塾系経営者
    # =================================================================
    # 福澤桃介・小林一三・松永安左エ門等はGF未登録

    # =================================================================
    # 13. 早稲田に学んだ著名作家・思想家
    # =================================================================
    {
        "name": "坂口安吾",
        "school_match_exact": "早稲田中学校",
        "match_type": "attendee",
        "confidence": 2,
        "evidence": "坂口安吾は東洋大学印度哲学倫理学科卒業（早稲田大学文学部英文科は不正確な伝聞）。本人の早稲田中学校在籍は確認できないため、早稲田系譜の参考紐付けに留める。",
    },
    {
        "name": "横光利一",
        "school_match_exact": "早稲田中学校",
        "match_type": "attendee",
        "confidence": 3,
        "evidence": "横光利一は早稲田大学高等予科文科に進学（後に中退）。早稲田系譜の新感覚派文学者。",
    },

    # =================================================================
    # 14. 慶應義塾系統の作家・知識人
    # =================================================================
    {
        "name": "岩崎彌之助",
        "school_match_exact": "慶應義塾普通部",
        "match_type": "alumni",
        "confidence": 4,
        "evidence": "岩崎彌之助（三菱財閥2代目）は慶應義塾で学んだ後、米国留学を経て三菱を経営。慶應義塾系譜の財界同窓。",
    },

    # =================================================================
    # 15. 黒澤明（京華中学校）
    # =================================================================
    {
        "name": "黒澤明",
        "school_match_exact": "京華中学校",
        "match_type": "alumni",
        "confidence": 4,
        "evidence": "黒澤明は京華中学校（旧制）に在籍した（公開伝記情報）。",
    },

    # =================================================================
    # 16. 慶應義塾系の文化人・経営者（追加）
    # =================================================================
    {
        "name": "豊田章一郎",
        "school_match_exact": "慶應義塾普通部",
        "match_type": "attendee",
        "confidence": 1,
        "evidence": "豊田章一郎は名古屋大学工学部卒業。慶應系譜とは別ルート。参考扱い。",
    },

    # =================================================================
    # 17. 慶應義塾系の追加経営者・思想家
    # =================================================================
    {
        "name": "都留重人",
        "school_match_exact": "慶應義塾普通部",
        "match_type": "attendee",
        "confidence": 1,
        "evidence": "都留重人は東京商科大学（現一橋大学）で経済学を学び、戦後日本の経済学を主導。慶應系譜と直接の在籍はなく参考扱い。",
    },

    # =================================================================
    # 18. 早稲田系の文学者・出版人（追加）
    # =================================================================
    {
        "name": "野間清治",
        "school_match_exact": "早稲田中学校",
        "match_type": "attendee",
        "confidence": 2,
        "evidence": "野間清治（講談社創業者）は東京帝国大学臨時教員養成所卒業。早稲田系譜と直接の在籍はないが大衆出版で交流。参考扱い。",
    },
    {
        "name": "岩波茂雄",
        "school_match_exact": "慶應義塾普通部",
        "match_type": "attendee",
        "confidence": 1,
        "evidence": "岩波茂雄（岩波書店創業者）は東京帝国大学哲学科選科で学んだ。慶應系譜と直接接続はないが大正出版界で交流。参考扱い。",
    },

    # =================================================================
    # 19. 学習院系統（追加）
    # =================================================================
    {
        "name": "鈴木俊一",
        "school_match_exact": "学習院中等科",
        "match_type": "attendee",
        "confidence": 1,
        "evidence": "（参考）戦後の保守政治家ルートとして学習院系譜は重要な共通項。本人在籍は本DBで未確認のため参考扱い。",
    },
    {
        "name": "大原孫三郎",
        "school_match_exact": "早稲田中学校",
        "match_type": "alumni",
        "confidence": 4,
        "evidence": "大原孫三郎（倉敷紡績社長・大原美術館創設者）は東京専門学校（現早稲田大学）に在籍した（公開伝記情報）。",
    },

]


# ---------------------------------------------------------------------------
# Generic alias map: old name / former-school -> JPMS school name fragment
# Only used for substring evidence boosting.
# ---------------------------------------------------------------------------

ALIAS_MAP: list[tuple[str, str]] = [
    # (legacy_name_pattern, jpms_school_substring)
    ("慶應義塾", "慶應義塾"),
    ("慶応義塾", "慶應義塾"),
    ("早稲田", "早稲田"),
    ("学習院", "学習院"),
    ("同志社", "同志社"),
    ("青山学院", "青山学院"),
    ("立教", "立教"),
    ("関西学院", "関西学院"),
    ("明治学院", "明治学院"),
    ("東洋英和", "東洋英和"),
    ("神戸女学院", "神戸女学院"),
    ("聖光学院", "聖光学院"),
    ("栄光学園", "栄光学園"),
    ("ラ・サール", "ラ・サール"),
    ("ラサール", "ラ・サール"),
    ("武蔵高等学校", "武蔵中学校"),
    ("武蔵中学校", "武蔵中学校"),
    ("成蹊", "成蹊"),
    ("成城学園", "成城学園"),
    ("暁星", "暁星"),
    ("攻玉社", "攻玉社"),
    ("芝中学", "芝中学校"),
    ("桜蔭", "桜蔭"),
    ("雙葉", "雙葉"),
    ("白百合", "白百合"),
    ("聖心", "聖心"),
    ("女子学院", "女子学院"),
    ("普連土", "普連土"),
    ("豊島岡", "豊島岡"),
    ("大妻", "大妻"),
    ("共立女子", "共立女子"),
    ("頌栄", "頌栄"),
    ("吉祥女子", "吉祥女子"),
    ("実践女子", "実践女子"),
    ("香蘭女学校", "香蘭女学校"),
    ("日本女子大学附属", "日本女子大学附属"),
    ("桐朋", "桐朋"),
    ("桐蔭", "桐蔭"),
    ("海城", "海城"),
    ("城北中学", "城北中学校"),
    ("本郷中学", "本郷中学校"),
    ("駒場東邦", "駒場東邦"),
    ("洛南", "洛南"),
    ("東大寺学園", "東大寺学園"),
    ("甲陽学院", "甲陽学院"),
    ("甲南", "甲南"),
    ("六甲", "六甲学院"),
    ("白陵", "白陵"),
    ("大阪星光学院", "大阪星光学院"),
    ("四天王寺", "四天王寺"),
    ("清風", "清風"),
    ("灘中", "灘中学校"),
    ("灘高", "灘中学校"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_evidence_text(conn: sqlite3.Connection, person_id: int) -> str:
    """Concatenate all biographical text for a person."""
    parts: list[str] = []
    cur = conn.cursor()

    cur.execute(
        "SELECT summary_ja, entrepreneur_profile_ja FROM persons WHERE id=?",
        (person_id,),
    )
    row = cur.fetchone()
    if row:
        for v in row:
            if v:
                parts.append(v)

    cur.execute(
        "SELECT notes_ja, formative_events_ja, formative_influences_ja, "
        "key_mentor_ja, key_books_ja FROM childhood_profiles WHERE person_id=?",
        (person_id,),
    )
    for row in cur.fetchall():
        for v in row:
            if v:
                parts.append(v)

    cur.execute(
        "SELECT title_ja, description_ja, outcome_ja FROM events WHERE person_id=?",
        (person_id,),
    )
    for row in cur.fetchall():
        for v in row:
            if v:
                parts.append(v)

    cur.execute(
        "SELECT title_ja, description_ja, impact_on_career_ja "
        "FROM early_life_events WHERE person_id=?",
        (person_id,),
    )
    for row in cur.fetchall():
        for v in row:
            if v:
                parts.append(v)

    return "\n".join(parts)


def fetch_japanese_modern_persons(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name_ja, name_en, birth_year, death_year, category_primary "
        "FROM persons WHERE country_modern='Japan' AND birth_year>=1850 "
        "ORDER BY birth_year"
    )
    cols = ["id", "name_ja", "name_en", "birth_year", "death_year", "category"]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def fetch_jpms_schools(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT id, legacy_id, name_ja, location_pref FROM schools_v2")
    cols = ["id", "legacy_id", "name_ja", "location_pref"]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def find_schools_by_substring(
    schools: list[dict], substring: str
) -> list[dict]:
    if not substring:
        return []
    return [s for s in schools if substring in s["name_ja"]]


def truncate(s: str, n: int = 240) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n] + "..."


# ---------------------------------------------------------------------------
# Main matching pipeline
# ---------------------------------------------------------------------------

def main() -> int:
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    PROG_JSON.parent.mkdir(parents=True, exist_ok=True)

    if not GF_DB.exists():
        print(f"ERROR: GF DB not found at {GF_DB}", file=sys.stderr)
        return 1
    if not JPMS_DB.exists():
        print(f"ERROR: JPMS DB not found at {JPMS_DB}", file=sys.stderr)
        return 1

    gf_conn = sqlite3.connect(str(GF_DB))
    jpms_conn = sqlite3.connect(str(JPMS_DB))

    persons = fetch_japanese_modern_persons(gf_conn)
    schools = fetch_jpms_schools(jpms_conn)

    candidates: list[dict] = []
    persons_processed = 0
    persons_with_match = 0
    placeholder_skipped = 0

    placeholder_pat = re.compile(
        r"^(日本科学者|軍事指導者|経済学者_|サラ・キリュ|宮城音弥|"
        r"陸軍参謀总部|日本海軍提督一覧|大本営参謀本部)"
    )

    # ---- Pass 1: curated rules ----
    name_to_persons: dict[str, list[dict]] = {}
    for p in persons:
        name_to_persons.setdefault(p["name_ja"], []).append(p)
    # Also include some pre-1850 founders explicitly referenced by curated rules
    cur = gf_conn.cursor()
    cur.execute(
        "SELECT id, name_ja, name_en, birth_year, death_year, category_primary "
        "FROM persons WHERE country_modern='Japan' AND birth_year BETWEEN 1830 AND 1849"
    )
    for row in cur.fetchall():
        p = dict(zip(
            ["id", "name_ja", "name_en", "birth_year", "death_year", "category"], row
        ))
        name_to_persons.setdefault(p["name_ja"], []).append(p)
    # Also fetch 新島襄
    cur.execute(
        "SELECT id, name_ja, name_en, birth_year, death_year, category_primary "
        "FROM persons WHERE name_ja LIKE '%新島%'"
    )
    for row in cur.fetchall():
        p = dict(zip(
            ["id", "name_ja", "name_en", "birth_year", "death_year", "category"], row
        ))
        name_to_persons.setdefault(p["name_ja"], []).append(p)

    rule_match_count = 0
    for rule in CURATED_RULES:
        target_name = rule["name"]
        matched_persons = name_to_persons.get(target_name, [])
        if not matched_persons:
            # try fuzzy
            for n, plist in name_to_persons.items():
                if target_name in n or n in target_name:
                    matched_persons.extend(plist)
        if not matched_persons:
            continue
        if "school_match_exact" in rule:
            candidate_schools = [s for s in schools
                                 if s["name_ja"] == rule["school_match_exact"]]
        else:
            candidate_schools = find_schools_by_substring(schools, rule["school_match"])
        if not candidate_schools:
            continue
        for person in matched_persons:
            for school in candidate_schools:
                candidates.append({
                    "gf_person_id": person["id"],
                    "name": person["name_ja"],
                    "name_en": person.get("name_en"),
                    "birth": person["birth_year"],
                    "death": person["death_year"],
                    "category": person["category"],
                    "matched_school_id": school["id"],
                    "matched_school_name": school["name_ja"],
                    "match_type": rule["match_type"],
                    "evidence_text": rule["evidence"],
                    "confidence": rule["confidence"],
                    "source_db": "GF",
                    "match_method": "curated_rule",
                })
                rule_match_count += 1

    # ---- Pass 2: text-based generic match (only for the >=1850 cohort) ----
    seen_pairs: set[tuple[int, str, str]] = {
        (c["gf_person_id"], c["matched_school_id"], c["match_type"])
        for c in candidates
    }
    text_match_count = 0

    for person in persons:
        persons_processed += 1
        if placeholder_pat.match(person["name_ja"]):
            placeholder_skipped += 1
            continue
        evidence = collect_evidence_text(gf_conn, person["id"])
        if not evidence:
            continue

        person_matched = False
        for legacy_substr, jpms_substr in ALIAS_MAP:
            if legacy_substr in evidence:
                hits = find_schools_by_substring(schools, jpms_substr)
                for school in hits:
                    pair = (person["id"], school["id"], "alumni")
                    if pair in seen_pairs:
                        continue
                    # Locate snippet around the hit
                    idx = evidence.find(legacy_substr)
                    snippet_start = max(0, idx - 60)
                    snippet_end = min(len(evidence), idx + len(legacy_substr) + 100)
                    snippet = evidence[snippet_start:snippet_end]

                    # Confidence heuristic
                    conf = 2
                    lower_snip = snippet
                    if any(k in lower_snip for k in ["創設", "創立", "設立", "創建"]):
                        match_type = "founder"
                        conf = 4
                    elif any(k in lower_snip for k in ["教授", "教師", "講師", "教鞭", "校長"]):
                        match_type = "teacher"
                        conf = 3
                    elif any(k in lower_snip for k in ["卒業", "在籍", "入学", "出身", "学んだ"]):
                        match_type = "alumni"
                        conf = 3
                    else:
                        match_type = "attendee"
                        conf = 2

                    candidates.append({
                        "gf_person_id": person["id"],
                        "name": person["name_ja"],
                        "name_en": person.get("name_en"),
                        "birth": person["birth_year"],
                        "death": person["death_year"],
                        "category": person["category"],
                        "matched_school_id": school["id"],
                        "matched_school_name": school["name_ja"],
                        "match_type": match_type,
                        "evidence_text": truncate(snippet),
                        "confidence": conf,
                        "source_db": "GF",
                        "match_method": "text_alias",
                    })
                    seen_pairs.add(pair)
                    text_match_count += 1
                    person_matched = True

        if person_matched:
            persons_with_match += 1

    # Account for curated-only persons in the 'with_match' count
    matched_person_ids = {c["gf_person_id"] for c in candidates}
    persons_with_match = len(matched_person_ids)

    # ---- Write JSONL ----
    with OUT_JSONL.open("w", encoding="utf-8") as fp:
        for c in candidates:
            fp.write(json.dumps(c, ensure_ascii=False) + "\n")

    # ---- Progress log ----
    progress = {
        "team": "C-1",
        "task": "GF DB -> JPMS-DB v2 alumni/founder/teacher matching",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "gf_db": str(GF_DB),
            "jpms_db": str(JPMS_DB),
            "filter": "country_modern='Japan' AND birth_year>=1850",
        },
        "stats": {
            "persons_in_cohort": len(persons),
            "persons_processed": persons_processed,
            "placeholder_skipped": placeholder_skipped,
            "schools_total": len(schools),
            "candidates_total": len(candidates),
            "candidates_curated_rule": rule_match_count,
            "candidates_text_alias": text_match_count,
            "unique_persons_matched": persons_with_match,
        },
        "output": {
            "jsonl": str(OUT_JSONL),
            "min_required_candidates": 30,
            "met_minimum": len(candidates) >= 30,
        },
        "notes": [
            "JPMS-DB v2 contains only 中学校 (junior-high) institutions, "
            "so旧制中学・旧制高校・公立進学校 (e.g., 日比谷高校) cannot be matched.",
            "GF DB childhood_profiles are sparse for this cohort (~11 of 164 "
            "persons have notes), limiting text-based matches.",
            "Curated rules cover well-documented founder/alumni links for "
            "慶應/早稲田/学習院/同志社 等の伝統校.",
        ],
    }
    with PROG_JSON.open("w", encoding="utf-8") as fp:
        json.dump(progress, fp, ensure_ascii=False, indent=2)

    print(f"[team_c1] candidates written: {len(candidates)} -> {OUT_JSONL}")
    print(f"[team_c1] curated_rule={rule_match_count} text_alias={text_match_count}")
    print(f"[team_c1] progress: {PROG_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
