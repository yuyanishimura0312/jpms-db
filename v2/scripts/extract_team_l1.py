#!/usr/bin/env python3
"""Team L1 extractor: school_admission_v2 / school_progress_record_v2 / school_facility_v2.

Reads HTML caches under raw_html_cache/<school_id>/ and extracts:
- admission.html → school_admission_v2 (募集人数, 受験者数, 合格者数, 倍率, 試験回数)
- progress.html → school_progress_record_v2 (大学名×人数)
- about.html (and root.html fallback) + admission/progress text → school_facility_v2

Output JSONL files under codex_output/:
  team_l1_admission.jsonl
  team_l1_progress.jsonl
  team_l1_facility.jsonl

Progress log: codex_progress/team_l1.json
"""
from __future__ import annotations
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path('/Users/nishimura+/projects/research/jpms-db/v2')
CACHE = ROOT / 'raw_html_cache'
DB_PATH = ROOT / 'jpms_v2.db'
OUT_DIR = ROOT / 'codex_output'
PROG_DIR = ROOT / 'codex_progress'

OUT_DIR.mkdir(parents=True, exist_ok=True)
PROG_DIR.mkdir(parents=True, exist_ok=True)

# Try BeautifulSoup, but fall back to regex strip
try:
    from bs4 import BeautifulSoup  # type: ignore
    HAVE_BS4 = True
except Exception:
    HAVE_BS4 = False


# ---- Helpers ----------------------------------------------------------------

def normalize_text(html: str) -> str:
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    # Skip HTML comment removal — many sites use <!-- to disable LIs while leaving content visible.
    # The tag-strip pass below preserves the inner text without losing it.
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def to_int(s: str) -> Optional[int]:
    s = s.replace(',', '').replace('，', '').strip()
    try:
        return int(s)
    except ValueError:
        return None


def to_float(s: str) -> Optional[float]:
    s = s.replace(',', '').replace('，', '').strip()
    try:
        return float(s)
    except ValueError:
        return None


def find_year(text: str) -> Optional[int]:
    """Extract a recent year hint from page text (2018-2027)."""
    # Prefer first western year in 2018-2027
    m = re.search(r'(20[12][0-9])\s*年', text)
    if m:
        y = int(m.group(1))
        if 2018 <= y <= 2027:
            return y
    # Reiwa N → 2018+N
    m = re.search(r'令和\s*(\d+)', text)
    if m:
        return 2018 + int(m.group(1))
    return None


def load_school_url(db: sqlite3.Connection, sid: str) -> Optional[str]:
    row = db.execute("SELECT homepage_url FROM schools_v2 WHERE id=?", (sid,)).fetchone()
    return row[0] if row and row[0] else None


# ---- Admission --------------------------------------------------------------

EXAM_TYPE_HINTS = [
    ('帰国', '帰国生'),
    ('特別', '特別選抜'),
    ('インター', 'インター特別'),
    ('英語型', '英語選抜'),
    ('適性検査', '適性検査型'),
]


def extract_admission(text: str, school_id: str, source_url: str, year_hint: Optional[int]) -> list[dict]:
    """Heuristic admission extraction.

    Strategies:
      1. Look for 募集 ... 男子/女子 NN 名 → admitted (the recruitment quota).
      2. Look for 受験者 NN / 合格者 NN / 倍率 X.X for applicants/admitted/ratio.
      3. Detect exam types (帰国生/特別/一般) by surrounding keywords.
    """
    rows: list[dict] = []
    year = year_hint or find_year(text)

    # ---- Pattern A: 募集 (quota) lines (ex: "◇募集 男子 300 名")
    for m in re.finditer(r'募集[^。、]{0,40}?([0-9][0-9, ]{0,5})\s*名', text):
        admitted = to_int(m.group(1))
        if admitted is None or admitted < 5 or admitted > 1500:
            continue
        # Detect exam type by left context (~40 chars)
        left = text[max(0, m.start() - 40):m.start()]
        etype = '一般'
        for kw, label in EXAM_TYPE_HINTS:
            if kw in left:
                etype = label
                break
        rows.append({
            'school_id': school_id,
            'year': year,
            'exam_type': etype,
            'exam_count': None,
            'applicants': None,
            'admitted': admitted,
            'competition_ratio': None,
            'scoring_summary': None,
            'source_url': source_url,
            'rights_level': 'public',
            'extraction_method': 'regex_quota',
        })
        if len(rows) >= 4:
            break

    # ---- Pattern B: 受験者 NN / 合格者 NN / 倍率 X.X tuples in close proximity
    # We split into windows of 200 chars looking for at least two of these.
    for win_match in re.finditer(r'(受験者[^\n]{0,200})|(志願者[^\n]{0,200})', text):
        win = text[max(0, win_match.start()-50):win_match.end()+200]
        applicants = None
        admitted = None
        ratio = None
        m1 = re.search(r'(?:受験者|志願者)[^0-9]{0,10}([0-9][0-9, ]{1,5})\s*[名人]', win)
        m2 = re.search(r'合格者[^0-9]{0,10}([0-9][0-9, ]{1,5})\s*[名人]', win)
        m3 = re.search(r'(?:倍率|実質倍率|競争率)[^0-9]{0,6}([0-9]\.[0-9]{1,2})', win)
        if m1:
            applicants = to_int(m1.group(1))
        if m2:
            admitted = to_int(m2.group(1))
        if m3:
            ratio = to_float(m3.group(1))
        if applicants or admitted or ratio:
            # Filter implausible
            if applicants and (applicants < 5 or applicants > 5000):
                applicants = None
            if admitted and (admitted < 1 or admitted > 1500):
                admitted = None
            if ratio and (ratio < 0.5 or ratio > 30):
                ratio = None
            if not (applicants or admitted or ratio):
                continue
            rows.append({
                'school_id': school_id,
                'year': year,
                'exam_type': '一般',
                'exam_count': None,
                'applicants': applicants,
                'admitted': admitted,
                'competition_ratio': ratio,
                'scoring_summary': None,
                'source_url': source_url,
                'rights_level': 'public',
                'extraction_method': 'regex_results',
            })
            if len(rows) >= 6:
                break

    # ---- Pattern C: 試験日 + 教科 metadata (always, supplements quota rows)
    if True:
        scoring: dict = {}
        # Exam dates near 入試/試験/学力試験
        date_matches = re.findall(
            r'(?:学力試験|入試|入学試験|試験日)[^。]{0,30}?(\d{1,2}\s*月\s*\d{1,2}\s*日)',
            text)
        if date_matches:
            scoring['exam_dates'] = date_matches[:4]
        # Subjects + minutes (国語 50分, 算数 60分 …)
        subj_matches = re.findall(r'(国語|算数|理科|社会|数学|英語)\s*(\d{2,3})\s*分', text)
        if subj_matches:
            # Dedupe by subject
            seen = set()
            uniq = []
            for s, mn in subj_matches:
                if s in seen:
                    continue
                seen.add(s)
                uniq.append({'subject': s, 'minutes': int(mn)})
            scoring['subjects'] = uniq
        # Points (合計 NNN 点)
        pt = re.search(r'合計[^0-9]{0,5}([0-9]{2,4})\s*点', text)
        if pt:
            tp = to_int(pt.group(1))
            if tp and 50 <= tp <= 1500:
                scoring['total_points'] = tp
        # Application fee
        feem = re.search(r'(?:検定料|入学検定料|受験料)[^0-9]{0,15}([0-9][0-9, ]{2,7})\s*円', text)
        if feem:
            fee = to_int(feem.group(1))
            if fee and 1000 <= fee <= 200000:
                scoring['exam_fee_jpy'] = fee
        if scoring and not any(r.get('extraction_method') == 'regex_metadata' for r in rows):
            rows.append({
                'school_id': school_id,
                'year': year,
                'exam_type': '一般',
                'exam_count': 1 if scoring.get('exam_dates') else None,
                'applicants': None,
                'admitted': None,
                'competition_ratio': None,
                'scoring_summary': json.dumps(scoring, ensure_ascii=False),
                'source_url': source_url,
                'rights_level': 'public',
                'extraction_method': 'regex_metadata',
            })

    # Cap to 1-3 rows per school
    return rows[:3]


# ---- Progress ---------------------------------------------------------------

UNIVERSITIES = [
    # ---- Core national & elite (national_univ)
    ('東京大学', 'national_univ', '東京大学|東大'),
    ('京都大学', 'national_univ', '京都大学|京大'),
    ('一橋大学', 'national_univ', '一橋大学|一橋大'),
    ('東京工業大学', 'national_univ', '東京工業大学|東工大'),
    ('東京科学大学', 'national_univ', '東京科学大学'),
    ('北海道大学', 'national_univ', '北海道大学|北大'),
    ('東北大学', 'national_univ', '東北大学|東北大'),
    ('名古屋大学', 'national_univ', '名古屋大学|名大'),
    ('大阪大学', 'national_univ', '大阪大学|阪大'),
    ('九州大学', 'national_univ', '九州大学|九大'),
    ('神戸大学', 'national_univ', '神戸大学|神大'),
    ('筑波大学', 'national_univ', '筑波大学'),
    ('お茶の水女子大学', 'national_univ', 'お茶の水女子大学|お茶大'),
    ('東京外国語大学', 'national_univ', '東京外国語大学|東京外大'),
    ('東京医科歯科大学', 'national_univ', '東京医科歯科大学'),
    ('横浜国立大学', 'national_univ', '横浜国立大学|横国'),
    ('千葉大学', 'national_univ', '千葉大学'),
    ('広島大学', 'national_univ', '広島大学'),
    ('東京農工大学', 'national_univ', '東京農工大学|農工大'),
    ('東京海洋大学', 'national_univ', '東京海洋大学'),
    ('東京藝術大学', 'national_univ', '東京藝術大学|東京芸術大学'),
    ('東京学芸大学', 'national_univ', '東京学芸大学'),
    ('電気通信大学', 'national_univ', '電気通信大学|電通大'),
    ('防衛医科大学校', 'national_univ', '防衛医科大学校|防衛医大'),
    ('防衛大学校', 'national_univ', '防衛大学校'),
    ('水産大学校', 'national_univ', '水産大学校'),
    # ---- Other national universities (regional/specialized)
    ('弘前大学', 'national_univ', '弘前大学'),
    ('茨城大学', 'national_univ', '茨城大学'),
    ('埼玉大学', 'national_univ', '埼玉大学'),
    ('新潟大学', 'national_univ', '新潟大学'),
    ('金沢大学', 'national_univ', '金沢大学'),
    ('信州大学', 'national_univ', '信州大学'),
    ('岐阜大学', 'national_univ', '岐阜大学'),
    ('静岡大学', 'national_univ', '静岡大学'),
    ('三重大学', 'national_univ', '三重大学'),
    ('滋賀大学', 'national_univ', '滋賀大学'),
    ('岡山大学', 'national_univ', '岡山大学'),
    ('山口大学', 'national_univ', '山口大学'),
    ('佐賀大学', 'national_univ', '佐賀大学'),
    ('長崎大学', 'national_univ', '長崎大学'),
    ('熊本大学', 'national_univ', '熊本大学'),
    ('鹿児島大学', 'national_univ', '鹿児島大学'),
    ('琉球大学', 'national_univ', '琉球大学'),
    ('奈良女子大学', 'national_univ', '奈良女子大学'),
    ('浜松医科大学', 'national_univ', '浜松医科大学'),
    # ---- Public (公立) — tag as national_univ for simplicity
    ('東京都立大学', 'national_univ', '東京都立大学'),
    ('横浜市立大学', 'national_univ', '横浜市立大学'),
    ('大阪公立大学', 'national_univ', '大阪公立大学|大阪府立大学'),
    ('京都府立大学', 'national_univ', '京都府立大学'),
    ('名古屋市立大学', 'national_univ', '名古屋市立大学'),
    ('北九州市立大学', 'national_univ', '北九州市立大学'),
    ('都留文科大学', 'national_univ', '都留文科大学'),
    ('長野県立大学', 'national_univ', '長野県立大学'),
    # ---- Major private
    ('早稲田大学', 'private_univ', '早稲田大学|早大'),
    ('慶應義塾大学', 'private_univ', '慶應義塾大学|慶應大学|慶應大|慶応大学|慶大'),
    ('上智大学', 'private_univ', '上智大学|上智大'),
    ('国際基督教大学', 'private_univ', '国際基督教大学|ＩＣＵ|ICU'),
    ('東京理科大学', 'private_univ', '東京理科大学|理科大'),
    ('明治大学', 'private_univ', '明治大学|明大'),
    ('立教大学', 'private_univ', '立教大学|立教大'),
    ('青山学院大学', 'private_univ', '青山学院大学|青学'),
    ('中央大学', 'private_univ', '中央大学|中大'),
    ('法政大学', 'private_univ', '法政大学|法大'),
    ('学習院大学', 'private_univ', '学習院大学|学習院大'),
    ('同志社大学', 'private_univ', '同志社大学|同志社大'),
    ('立命館大学', 'private_univ', '立命館大学|立命館大'),
    ('関西学院大学', 'private_univ', '関西学院大学|関学'),
    ('関西大学', 'private_univ', '関西大学|関大'),
    ('成蹊大学', 'private_univ', '成蹊大学'),
    ('成城大学', 'private_univ', '成城大学'),
    ('明治学院大学', 'private_univ', '明治学院大学'),
    ('武蔵大学', 'private_univ', '武蔵大学'),
    ('獨協大学', 'private_univ', '獨協大学'),
    ('國學院大學', 'private_univ', '國學院大學|國學院大学'),
    ('日本大学', 'private_univ', '日本大学|日大'),
    ('東洋大学', 'private_univ', '東洋大学|東洋大'),
    ('駒澤大学', 'private_univ', '駒澤大学|駒澤大'),
    ('専修大学', 'private_univ', '専修大学|専修大'),
    ('順天堂大学', 'private_univ', '順天堂大学'),
    ('日本医科大学', 'private_univ', '日本医科大学|日医大'),
    ('東京慈恵会医科大学', 'private_univ', '東京慈恵会医科大学|慈恵医大'),
    ('東京女子医科大学', 'private_univ', '東京女子医科大学'),
    ('北里大学', 'private_univ', '北里大学'),
    ('昭和大学', 'private_univ', '昭和大学'),
    ('東邦大学', 'private_univ', '東邦大学'),
    ('杏林大学', 'private_univ', '杏林大学'),
    ('東海大学', 'private_univ', '東海大学'),
    ('創価大学', 'private_univ', '創価大学'),
    ('明星大学', 'private_univ', '明星大学'),
    ('芝浦工業大学', 'private_univ', '芝浦工業大学|芝工大'),
    ('東京都市大学', 'private_univ', '東京都市大学'),
    ('東京農業大学', 'private_univ', '東京農業大学|農大'),
    ('武蔵野大学', 'private_univ', '武蔵野大学'),
    ('津田塾大学', 'private_univ', '津田塾大学'),
    ('東京女子大学', 'private_univ', '東京女子大学'),
    ('日本女子大学', 'private_univ', '日本女子大学'),
    # ---- International
    ('Harvard', 'intl_univ', 'Harvard'),
    ('Stanford', 'intl_univ', 'Stanford'),
    ('MIT', 'intl_univ', 'MIT|Massachusetts Institute'),
    ('Oxford', 'intl_univ', 'Oxford'),
    ('Cambridge', 'intl_univ', 'Cambridge'),
    ('Yale', 'intl_univ', 'Yale'),
    ('Princeton', 'intl_univ', 'Princeton'),
    ('Columbia', 'intl_univ', 'Columbia University'),
    ('UCL', 'intl_univ', 'UCL|University College London'),
    ('Imperial College', 'intl_univ', 'Imperial College'),
]


def extract_progress(text: str, school_id: str, source_url: str, year_hint: Optional[int]) -> list[dict]:
    """Extract university destinations from progress page text.

    Two-pass strategy:
      1) Number pass: 'XX大学 N' (within 8 chars, N=1..999) captures table rows.
      2) Mention pass: for any university not yet emitted, add a count=None row.
    Cap at 15 rows; one row per university.
    """
    rows: list[dict] = []
    year = year_hint or find_year(text) or 2024  # default to 2024
    seen_canon: set[str] = set()
    MAX_ROWS = 15

    # ---- Pass 1: number-based
    for canon, dtype, pat in UNIVERSITIES:
        if canon in seen_canon:
            continue
        rx = re.compile(rf'(?:{pat})\s*(?:[\(（][^\)）]{{0,10}}[\)）]\s*)?([0-9]{{1,3}})(?![0-9.])')
        m = rx.search(text)
        if not m:
            continue
        cnt = to_int(m.group(1))
        if cnt is None or cnt < 1 or cnt > 999:
            continue
        if 1900 <= cnt <= 2100:
            continue
        right = text[m.end():m.end() + 8]
        if 'PDF' in right or 'ページ' in right or 'kB' in right or 'MB' in right:
            continue
        rows.append({
            'school_id': school_id,
            'year': year,
            'destination_type': dtype,
            'destination_name': canon,
            'count': cnt,
            'share_pct': None,
            'source_url': source_url,
            'source_id': None,
            'rights_level': 'public',
            'extraction_method': 'regex_univ_count',
        })
        seen_canon.add(canon)
        if len(rows) >= MAX_ROWS:
            return rows[:MAX_ROWS]

    # ---- Pass 2: mention-only for remaining univs
    for canon, dtype, pat in UNIVERSITIES:
        if canon in seen_canon:
            continue
        if re.search(rf'(?:{pat})', text):
            rows.append({
                'school_id': school_id,
                'year': year,
                'destination_type': dtype,
                'destination_name': canon,
                'count': None,
                'share_pct': None,
                'source_url': source_url,
                'source_id': None,
                'rights_level': 'public',
                'extraction_method': 'regex_univ_mention',
            })
            seen_canon.add(canon)
            if len(rows) >= MAX_ROWS:
                return rows[:MAX_ROWS]

    # ---- Pass 3: PDF year list fallback if still empty
    if not rows:
        year_pdf = re.findall(r'(20[12][0-9])\s*[（(]?(?:令和|平成)?[^（()]{0,8}[)）]?\s*年[^（()]{0,8}?[（(]?\s*PDF', text)
        if year_pdf:
            for ys in year_pdf[:3]:
                y = int(ys)
                rows.append({
                    'school_id': school_id,
                    'year': y,
                    'destination_type': 'aggregate',
                    'destination_name': 'PDF公開（年次集計）',
                    'count': None,
                    'share_pct': None,
                    'source_url': source_url,
                    'source_id': None,
                    'rights_level': 'public',
                    'extraction_method': 'pdf_year_list',
                })
    return rows[:MAX_ROWS]


# ---- Facility ---------------------------------------------------------------

FACILITY_KEYWORDS = [
    # (regex pattern, type, default description)
    (r'図書館|ライブラリー|library', 'library', '図書館'),
    (r'体育館|アリーナ|ジム(?!ナジウム)|gymnasium', 'gym', '体育館'),
    (r'(?:理科)?実験室|サイエンス\s*ラボ|ラボラトリー|サイエンスラボ', 'lab', '実験室・ラボ'),
    (r'プール|水泳場|スイミング', 'pool', 'プール'),
    (r'(?<![校宿])寮(?![制度])|学生寮|宿舎|ドミトリ', 'dorm', '寮'),
    (r'食堂|カフェテリア|ランチルーム|学食', 'cafeteria', '食堂'),
    (r'講堂|大講堂|チャペル|礼拝堂|ホール(?!ディング)', 'hall', '講堂・ホール'),
    (r'グラウンド|運動場|校庭|フィールド|球技場', 'ground', 'グラウンド'),
    (r'天文台|プラネタリウム|観測ドーム', 'observatory', '天文台'),
    (r'コンピュータ\s*ルーム|PC\s*ルーム|ICT\s*ルーム|情報室|メディアセンター', 'computer_room', 'コンピュータルーム'),
    (r'美術室|アート\s*ルーム|アトリエ', 'art_room', '美術室'),
    (r'音楽室|ミュージック\s*ルーム|音楽ホール', 'music_room', '音楽室'),
    (r'校史資料室|歴史資料館|資料館|博物館', 'archive', '校史資料室'),
    (r'(?:多目的|多機能)ホール|多目的室|多目的スペース', 'multipurpose_hall', '多目的ホール'),
    (r'武道場|柔道場|剣道場|弓道場', 'martial_arts', '武道場'),
    (r'テニスコート|庭球場', 'tennis_court', 'テニスコート'),
    (r'校舎|新校舎|学舎', 'building', '校舎'),
    (r'保健室|医務室|医療室', 'nurse_room', '保健室'),
    (r'カウンセリング(?:ルーム|室)?|相談室', 'counseling_room', 'カウンセリング室'),
    (r'和室|茶室|作法室', 'tea_room', '和室・茶室'),
    (r'庭園|中庭|外庭|ガーデン', 'garden', '庭園'),
    (r'進路指導室|キャリア(?:ルーム|教室)', 'career_room', '進路指導室'),
    (r'スタジオ|録音室', 'studio', 'スタジオ'),
]


def extract_facility(text: str, school_id: str, source_url: str) -> list[dict]:
    rows: list[dict] = []
    seen = set()
    for pat, ftype, default_desc in FACILITY_KEYWORDS:
        rx = re.compile(pat)
        m = rx.search(text)
        if not m:
            continue
        if ftype in seen:
            continue
        # Try to grab a slightly bigger snippet for description
        s, e = m.start(), m.end()
        snippet = text[max(0, s-20):min(len(text), e+60)]
        snippet = snippet.strip()
        # Truncate
        if len(snippet) > 120:
            snippet = snippet[:120] + '…'
        # Detect notable: surrounded by 充実/最新/設備/誇る/特色 etc.
        notable = 1 if re.search(r'充実|最新|誇|特色|note|highlight|大学並み', snippet) else 0
        # Capacity
        cap = None
        capm = re.search(r'(\d{2,4})\s*(?:席|名|人)', snippet)
        if capm:
            cv = to_int(capm.group(1))
            if cv and 5 <= cv <= 5000:
                cap = cv
        rows.append({
            'school_id': school_id,
            'facility_type': ftype,
            'description': snippet or default_desc,
            'capacity': cap,
            'notable': notable,
            'source_url': source_url,
            'extraction_method': 'keyword_match',
        })
        seen.add(ftype)
        if len(rows) >= 10:
            break
    return rows


# ---- Main -------------------------------------------------------------------

def slug_url(base_url: Optional[str], slug: str) -> str:
    if not base_url:
        return f'cache://{slug}'
    base = base_url.rstrip('/')
    return f"{base}/{slug}/"


def read_html(p: Path) -> Optional[str]:
    if not p.exists():
        return None
    try:
        raw = p.read_bytes()
    except Exception:
        return None
    for enc in ('utf-8', 'shift_jis', 'euc-jp', 'cp932'):
        try:
            return raw.decode(enc, errors='ignore')
        except Exception:
            continue
    return raw.decode('utf-8', errors='ignore')


def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    school_ids = sorted([d.name for d in CACHE.iterdir() if d.is_dir() and d.name.startswith('jpms_s_')])
    print(f"[team_l1] Scanning {len(school_ids)} school dirs", file=sys.stderr)

    out_admission = OUT_DIR / 'team_l1_admission.jsonl'
    out_progress = OUT_DIR / 'team_l1_progress.jsonl'
    out_facility = OUT_DIR / 'team_l1_facility.jsonl'

    n_adm = n_prog = n_fac = 0
    n_schools_with_any = 0

    with out_admission.open('w') as fa, out_progress.open('w') as fp, out_facility.open('w') as ff:
        for sid in school_ids:
            school_dir = CACHE / sid
            base_url = load_school_url(db, sid)
            wrote_any = False

            # ---- Admission: merge across pages with method preference
            adm_rows: list[dict] = []
            method_seen: set[str] = set()
            # Priority: dedicated admission page first, then root, etc.
            for slug in ('admission', 'root', 'curriculum', 'principal', 'about'):
                p = school_dir / f'{slug}.html'
                html = read_html(p)
                if not html:
                    continue
                text = normalize_text(html)
                rows = extract_admission(text, sid, slug_url(base_url, slug), find_year(text))
                for r in rows:
                    # Avoid emitting identical method twice for same school
                    key = (r['extraction_method'], r.get('admitted'), r.get('exam_type'))
                    if key in method_seen:
                        continue
                    method_seen.add(key)
                    adm_rows.append(r)
                    if len(adm_rows) >= 3:
                        break
                if len(adm_rows) >= 3:
                    break
            for r in adm_rows:
                fa.write(json.dumps(r, ensure_ascii=False) + '\n')
                n_adm += 1
                wrote_any = True

            # ---- Progress: merge across all pages, dedupe by destination_name.
            prog_rows: list[dict] = []
            seen_destinations: set[str] = set()
            # First pass: progress.html (highest-trust source)
            for slug in ('progress', 'root', 'curriculum', 'principal', 'about'):
                p = school_dir / f'{slug}.html'
                html = read_html(p)
                if not html:
                    continue
                text = normalize_text(html)
                rows = extract_progress(text, sid, slug_url(base_url, slug), find_year(text))
                for r in rows:
                    if r['destination_name'] in seen_destinations:
                        continue
                    seen_destinations.add(r['destination_name'])
                    prog_rows.append(r)
                    if len(prog_rows) >= 15:
                        break
                if len(prog_rows) >= 15:
                    break
            for r in prog_rows:
                fp.write(json.dumps(r, ensure_ascii=False) + '\n')
                n_prog += 1
                wrote_any = True

            # ---- Facility: aggregate across all available pages
            facility_rows: list[dict] = []
            seen_types: set[str] = set()
            for slug in ('about', 'philosophy', 'principal', 'mission', 'curriculum',
                         'schoollife', 'events', 'voice', 'admission', 'progress', 'root'):
                p = school_dir / f'{slug}.html'
                html = read_html(p)
                if not html:
                    continue
                text = normalize_text(html)
                rows = extract_facility(text, sid, slug_url(base_url, slug))
                for r in rows:
                    if r['facility_type'] in seen_types:
                        continue
                    seen_types.add(r['facility_type'])
                    facility_rows.append(r)
                    if len(facility_rows) >= 10:
                        break
                if len(facility_rows) >= 10:
                    break
            for r in facility_rows:
                ff.write(json.dumps(r, ensure_ascii=False) + '\n')
                n_fac += 1
                wrote_any = True

            if wrote_any:
                n_schools_with_any += 1

    progress = {
        'team': 'team_l1',
        'updated_at': datetime.now().isoformat(),
        'counts': {
            'schools_scanned': len(school_ids),
            'schools_with_extractions': n_schools_with_any,
            'admission_rows': n_adm,
            'progress_rows': n_prog,
            'facility_rows': n_fac,
        },
        'output_files': {
            'admission': str(out_admission),
            'progress': str(out_progress),
            'facility': str(out_facility),
        },
    }
    (PROG_DIR / 'team_l1.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2))
    print(json.dumps(progress, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
