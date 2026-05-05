#!/usr/bin/env python3
"""Team C-3: Extract business entrepreneur/executive alumni from Wikipedia.

Strategy:
  1. Pick TOP-30 traditional/prestigious schools from JPMS-DB v2
  2. Fetch each school's ja-Wikipedia article via API (action=parse, prop=wikitext)
  3. Locate alumni/「著名な卒業生」/「出身者」section
  4. For each linked person in that section, fetch their Wikipedia article
  5. Decide if they are an entrepreneur/executive based on lead text or category links
  6. Emit JSONL records

Rules:
  - User-Agent: JPMS-DB-Research/2.0 (+research-contact@miratuku.org)
  - 5 sec sleep between requests to ja.wikipedia.org
  - Cache fetched wikitext on disk to allow resumption
"""
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

JPMS_DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT_PATH = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c3_business.jsonl')
PROGRESS_PATH = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_progress/team_c3.json')
CACHE_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache/wp_team_c3')
LOG_PATH = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_logs/team_c3.log')

USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org)'
WP_API = 'https://ja.wikipedia.org/w/api.php'
SLEEP_SEC = 5.0

# Curated list of 30 schools known to have notable business alumni
# Mix of: 御三家 + 関西難関 + 慶應/早稲田系 + 立教/学習院 + 東海/南山(愛知) + 大阪府主要校
TARGET_SCHOOLS = [
    # 男子御三家 + 上位校 (東京)
    'jpms_s_0001',  # 開成中学校
    'jpms_s_0002',  # 麻布中学校
    'jpms_s_0034',  # 海城中学校
    'jpms_s_0025',  # 芝中学校
    'jpms_s_0067',  # 攻玉社中学校
    'jpms_s_0479',  # 桐朋中学校
    'jpms_s_0405',  # 巣鴨中学校
    'jpms_s_0401',  # 本郷中学校
    'jpms_s_0417',  # 城北中学校
    'jpms_s_0062',  # 駒場東邦中学校
    # 慶應/早稲田/立教/学習院 (東京・神奈川)
    'jpms_s_0023',  # 慶應義塾中等部
    'jpms_s_0133',  # 慶應義塾普通部 (神奈川)
    'jpms_s_0039',  # 早稲田中学校
    'jpms_s_0472',  # 早稲田実業学校中等部
    'jpms_s_0404',  # 学習院中等科
    'jpms_s_0402',  # 立教池袋中学校
    'jpms_s_0040',  # 青山学院中等部
    'jpms_s_0457',  # 明治大学付属明治中学校
    'jpms_s_0473',  # 中央大学附属中学校
    'jpms_s_0450',  # 成蹊中学校
    'jpms_s_0063',  # 成城学園中学校
    'jpms_s_0013',  # 暁星中学校
    # 神奈川 御三家・名門
    'jpms_s_p3_001', # 栄光学園中学校
    'jpms_s_p3_003', # 聖光学院中学校
    'jpms_s_0122',  # 浅野中学校
    # 愛知
    'jpms_s_0700',  # 東海中学校
    'jpms_s_0703',  # 滝中学校
    'jpms_s_0701',  # 南山中学校男子部
    # 大阪
    'jpms_s_0600',  # 大阪星光学院中学校
    'jpms_s_0601',  # 清風南海中学校
]


def log(msg):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open('a') as f:
        f.write(line + '\n')


def http_get(url):
    """Fetch URL with proper UA. Caller is responsible for rate limiting."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')


def wp_fetch_wikitext(title: str) -> str:
    """Fetch wikitext for given page title. Cached on disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^\w\-_.]', '_', title)[:100]
    cache = CACHE_DIR / f"{safe}.wikitext"
    if cache.exists() and cache.stat().st_size > 0:
        return cache.read_text(encoding='utf-8')

    params = {
        'action': 'parse',
        'page': title,
        'prop': 'wikitext',
        'format': 'json',
        'redirects': '1',
    }
    url = WP_API + '?' + urllib.parse.urlencode(params)
    try:
        raw = http_get(url)
    except Exception as e:
        log(f"  fetch error for '{title}': {e}")
        cache.write_text('', encoding='utf-8')  # empty cache to avoid retry storms
        time.sleep(SLEEP_SEC)
        return ''
    time.sleep(SLEEP_SEC)
    try:
        j = json.loads(raw)
        wt = j.get('parse', {}).get('wikitext', {}).get('*', '')
    except Exception:
        wt = ''
    cache.write_text(wt, encoding='utf-8')
    return wt


def extract_alumni_section(wikitext: str) -> str:
    """Find the alumni / 出身者 / 卒業生 section and return its text.

    Returns the WHOLE page if the page itself looks like a "人物一覧" sub-page
    (i.e. contains 出身者 section as primary content).
    """
    # If the page has clear alumni-listing style headers AND short overall
    # (typical of "の人物一覧" pages), use the whole text.
    if re.search(r'==\s*出身者\s*==', wikitext) and re.search(r'===\s*(政治|商社|実業家|金融|学者|文学|スポーツ|芸術)', wikitext):
        return wikitext

    # Match section headers like ==著名な卒業生==, ==出身者==, ==卒業生==, ===著名な出身者===
    # then capture until next same-level == header.
    headers = [
        '著名な卒業生', '主な卒業生', '主な出身者', '著名な出身者', '出身者',
        '卒業生', '関係者', '主な関係者', '主な人物', '主な校友', '校友', 'OB', 'OG', 'OB・OG',
        '中学・高等学校関係者一覧',
    ]
    pattern = r'==+\s*(' + '|'.join(re.escape(h) for h in headers) + r')\s*==+'
    matches = list(re.finditer(pattern, wikitext))
    if not matches:
        return ''
    chunks = []
    for m in matches:
        start = m.end()
        # find next == header at same level
        nxt = re.search(r'\n==[^=]', wikitext[start:])
        end = start + nxt.start() if nxt else len(wikitext)
        chunks.append(wikitext[start:end])
    return '\n'.join(chunks)


# School name → list of Wikipedia title candidates to try, in order.
# The script always tries the school's own ja-WP article last. If a "人物一覧"
# sub-page exists we prefer it as it lists more alumni and is structured.
SCHOOL_TITLE_OVERRIDES = {
    'jpms_s_0001': ['開成中学校・高等学校の人物一覧', '開成中学校・高等学校'],
    'jpms_s_0002': ['麻布中学校・高等学校の人物一覧', '麻布中学校・高等学校'],
    'jpms_s_0034': ['海城中学校・高等学校'],
    'jpms_s_0025': ['芝中学校・高等学校'],
    'jpms_s_0067': ['攻玉社中学校・高等学校'],
    'jpms_s_0479': ['桐朋中学校・高等学校'],
    'jpms_s_0405': ['巣鴨中学校・高等学校'],
    'jpms_s_0401': ['本郷中学校・高等学校'],
    'jpms_s_0417': ['城北中学校・高等学校 (東京都)', '城北中学校・高等学校'],
    'jpms_s_0062': ['駒場東邦中学校・高等学校'],
    'jpms_s_0023': ['慶應義塾中等部', '慶應義塾'],
    'jpms_s_0133': ['慶應義塾普通部', '慶應義塾'],
    'jpms_s_0039': ['早稲田中学校・高等学校'],
    'jpms_s_0472': ['早稲田実業学校', '早稲田実業学校中等部・高等部'],
    'jpms_s_0404': ['学習院中等科', '学習院'],
    'jpms_s_0402': ['立教池袋中学校・高等学校'],
    'jpms_s_0040': ['青山学院中等部'],
    'jpms_s_0457': ['明治大学付属明治高等学校・中学校'],
    'jpms_s_0473': ['中央大学附属中学校・高等学校'],
    'jpms_s_0450': ['成蹊中学校・高等学校'],
    'jpms_s_0063': ['成城学園中学校高等学校', '成城学園'],
    'jpms_s_0013': ['暁星中学校・高等学校'],
    'jpms_s_p3_001': ['栄光学園中学校・高等学校'],
    'jpms_s_p3_003': ['聖光学院中学校・高等学校'],
    'jpms_s_0122': ['浅野中学校・高等学校'],
    'jpms_s_0700': ['東海中学校・高等学校 (愛知県)', '東海中学校・高等学校'],
    'jpms_s_0703': ['滝中学校・高等学校'],
    'jpms_s_0701': ['南山中学校男子部・高等学校男子部', '南山中学校・高等学校男子部'],
    'jpms_s_0600': ['大阪星光学院中学校・高等学校'],
    'jpms_s_0601': ['清風南海中学校・高等学校'],
}


def extract_linked_persons(section_text: str, business_only: bool = True) -> list:
    """Find [[Person Name]] links in alumni section. Returns list of titles.

    If business_only is True, prefer links that appear inside or near
    '商社・実業家', '金融', '経済', '実業', etc. sub-sections of the alumni page.
    """
    # First, scope down to business-related sub-sections if any exist.
    if business_only:
        biz_pattern = re.compile(
            r'===\s*(?:[^=\n]*(?:商社|実業|経済|経営|金融|産業|起業|ビジネス|財界)[^=\n]*?)\s*===',
        )
        biz_starts = [m.start() for m in biz_pattern.finditer(section_text)]
        if biz_starts:
            chunks = []
            for s in biz_starts:
                # capture until next ==-level header (any level)
                nxt = re.search(r'\n==', section_text[s + 1:])
                e = s + 1 + nxt.start() if nxt else len(section_text)
                chunks.append(section_text[s:e])
            section_text = '\n'.join(chunks)

    persons = []
    seen = set()
    # Person-name heuristic regex (Japanese kanji/hiragana/katakana, 2..10 chars,
    # optionally with '(...)' disambiguation suffix).
    name_re = re.compile(r'^[一-龥ぁ-んァ-ヴー　・]{2,12}(\s*\([^)]{1,30}\))?$')

    for m in re.finditer(r'\[\[([^\[\]\|#]+?)(\|[^\[\]]*)?\]\]', section_text):
        title = m.group(1).strip()
        if not title:
            continue
        if title.startswith(('Category:', 'カテゴリ:', 'File:', 'ファイル:', 'Image:', '画像:')):
            continue
        if title.startswith(('Wikipedia:', 'Help:', 'ヘルプ:', 'Template:', 'Project:')):
            continue
        # Skip obvious institutions / events / lists
        if any(kw in title for kw in [
            '一覧', '株式会社', '有限会社', '高等学校', '中学校', '小学校',
            '内閣', '省庁', '事件', '甲子園', 'リーグ', '駅', '裁判', '条約',
            '財団', '財務省', '通商産業省', '経済産業省', '法務省', '文部科学省',
            '会議', '協会', '連盟', '機構', '法人', '団体',
            '党', '社会党', '自由民主党', '民主党', '共産党',
            '万国博覧会', '日本赤十字',
        ]):
            continue
        # Skip corporate-name-shaped strings (very common in alumni list pages)
        if any(suf in title for suf in [
            '証券', '総研', '研究所', '保険', '監査', '信託', '商事', '物産',
            'ガス', '電力', '鉄道', '海運', '化学', '製薬', '製鉄', '製作所',
            '建設', 'グループ', 'ホールディングス', 'コーポレーション',
            '財閥', '不動産', '金属', '紡績', '食品', '電機', '電気', '工業',
            '銀行', '信用金庫', '信用組合',
        ]):
            continue
        if title.endswith(('大学', '学院', '学校', '学部')):
            continue
        if title.endswith(('賞', '勲章')):
            continue
        if not name_re.match(title):
            continue
        if title in seen:
            continue
        seen.add(title)
        persons.append(title)
    return persons


# Keywords that indicate entrepreneur / executive
ENTREPRENEUR_KW = [
    '創業者', '創設者', '創立者', '設立者', '創業', '起業家',
    'ファウンダー', '創立', '創始者', '創設',
]
EXECUTIVE_KW = [
    '社長', '会長', '代表取締役', '最高経営責任者', 'CEO', 'COO', 'CFO',
    '取締役', '頭取', '理事長', '相談役', '名誉会長', '実業家',
    'ビジネスパーソン', '経営者', '元社長', '元会長',
]


def classify_person(wikitext: str):
    """Return ('entrepreneur'|'executive', evidence_snippet, confidence) or (None, ...).

    Look at first ~1200 chars (intro) plus categories (last ~2000 chars).
    """
    if not wikitext:
        return None, '', 0
    intro = wikitext[:1500]
    tail = wikitext[-2500:]  # categories usually at bottom

    # Strip common wiki markup for cleaner snippet
    intro_clean = re.sub(r'\{\{[^{}]*\}\}', '', intro)
    intro_clean = re.sub(r'<[^>]+>', '', intro_clean)
    intro_clean = re.sub(r'\[\[(?:[^\[\]\|]+\|)?([^\[\]]+)\]\]', r'\1', intro_clean)

    # Decide category
    category_text = ''
    cats = re.findall(r'\[\[Category:([^\[\]\|]+)(?:\|[^\[\]]*)?\]\]', tail)
    if not cats:
        cats = re.findall(r'\[\[カテゴリ:([^\[\]\|]+)(?:\|[^\[\]]*)?\]\]', tail)
    category_text = ' '.join(cats)

    text_for_match = intro_clean + ' ' + category_text

    # Determine entrepreneur first (more specific)
    is_entrepreneur = any(kw in text_for_match for kw in ENTREPRENEUR_KW)
    is_executive = any(kw in text_for_match for kw in EXECUTIVE_KW)

    if not (is_entrepreneur or is_executive):
        # Also accept "X の創業者" patterns even if KW above missed (extra safety)
        if re.search(r'(株式会社|有限会社).{0,40}(創業|創設|設立|創立)', text_for_match):
            is_entrepreneur = True

    if not (is_entrepreneur or is_executive):
        return None, '', 0

    category = 'entrepreneur' if is_entrepreneur else 'executive'

    # Extract evidence snippet (a sentence around a keyword)
    evidence = ''
    for kw in (ENTREPRENEUR_KW if is_entrepreneur else EXECUTIVE_KW):
        idx = intro_clean.find(kw)
        if idx >= 0:
            s = max(0, idx - 50)
            e = min(len(intro_clean), idx + 120)
            evidence = intro_clean[s:e].strip()
            evidence = re.sub(r'\s+', ' ', evidence)
            break
    if not evidence:
        evidence = intro_clean[:200].strip()
        evidence = re.sub(r'\s+', ' ', evidence)

    # Confidence:
    #   5 = entrepreneur with explicit "創業者/創設者" + clear company
    #   4 = entrepreneur or executive with rich category match
    #   3 = single keyword match in intro (default)
    confidence = 3
    if is_entrepreneur and re.search(r'(創業者|創設者|創立者)', text_for_match):
        confidence = 4
        if re.search(r'(株式会社|有限会社|Inc\.|Corp\.)', text_for_match):
            confidence = 5
    elif is_executive and ('実業家' in category_text or '経営者' in category_text):
        confidence = 4

    return category, evidence, confidence


def extract_birth_year(wikitext: str):
    """Try to pull birth year from infobox or first sentence."""
    if not wikitext:
        return None
    # Pattern 1: 生年月日 = ... YYYY年
    m = re.search(r'生年月日\s*=\s*\{\{[^}]*?\|(\d{4})\|', wikitext[:3000])
    if m:
        y = int(m.group(1))
        if 1700 < y < 2025:
            return y
    # Pattern 2: ＜生＞ YYYY年(...)
    m = re.search(r'(\d{4})年\s*\d{1,2}月\s*\d{1,2}日\s*[-－‐]', wikitext[:1500])
    if m:
        y = int(m.group(1))
        if 1700 < y < 2025:
            return y
    # Pattern 3: |生年|YYYY|MM|DD (death-date or birth-date templates)
    m = re.search(r'(?:生年月日|誕生日)?\s*(?:=|：)?\s*\{\{(?:生年月日と年齢|生年月日|死亡年月日と没年齢|没年齢|死亡年月日)[^}]*?\|(\d{4})\|', wikitext[:3000])
    if m:
        y = int(m.group(1))
        if 1700 < y < 2025:
            return y
    return None


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(JPMS_DB)
    db.row_factory = sqlite3.Row
    placeholders = ','.join('?' * len(TARGET_SCHOOLS))
    rows = db.execute(
        f"SELECT id, name_ja FROM schools_v2 WHERE id IN ({placeholders})",
        TARGET_SCHOOLS,
    ).fetchall()
    db.close()

    schools = {r['id']: r['name_ja'] for r in rows}
    log(f"Loaded {len(schools)} target schools")

    progress = {
        'started_at': datetime.now().isoformat(timespec='seconds'),
        'schools_total': len(schools),
        'schools_done': 0,
        'records_emitted': 0,
        'requests_made': 0,
        'per_school': {},
    }

    out_f = OUT_PATH.open('w')
    seen_persons = set()  # avoid duplicates across schools

    try:
        for sid, sname in schools.items():
            log(f"--- Processing {sid} {sname} ---")

            # Build candidate page titles. Prefer override list, then fall back
            # to a few default patterns derived from the school name.
            candidates = list(SCHOOL_TITLE_OVERRIDES.get(sid, []))
            if sname not in candidates:
                candidates.append(sname)
            base = re.sub(r'中学校$', '', sname)
            for extra in [f"{base}中学校・高等学校", base]:
                if extra and extra not in candidates:
                    candidates.append(extra)

            section = ''
            tried = []
            used_title = None
            for cand in candidates:
                tried.append(cand)
                wt = wp_fetch_wikitext(cand)
                progress['requests_made'] += 1
                if not wt:
                    continue
                sec = extract_alumni_section(wt)
                if sec and len(sec) > 200:
                    section = sec
                    used_title = cand
                    break

            if not section:
                log(f"  no alumni section in {tried}")
                progress['schools_done'] += 1
                progress['per_school'][sid] = {'name': sname, 'persons_checked': 0, 'persons_matched': 0, 'note': 'no alumni section', 'tried': tried}
                continue

            persons = extract_linked_persons(section)
            log(f"  {sname} (page='{used_title}'): {len(persons)} candidate persons")

            checked = 0
            matched = 0
            # Cap per school to keep within time budget
            for ptitle in persons[:25]:
                if ptitle in seen_persons:
                    continue
                seen_persons.add(ptitle)
                checked += 1

                pwt = wp_fetch_wikitext(ptitle)
                progress['requests_made'] += 1
                if not pwt:
                    continue
                category, evidence, conf = classify_person(pwt)
                if not category:
                    continue
                birth = extract_birth_year(pwt)

                rec = {
                    'name': ptitle,
                    'birth': birth,
                    'category': category,
                    'matched_school_id': sid,
                    'matched_school_name': sname,
                    'match_type': 'alumni',
                    'evidence_text': evidence[:300],
                    'source': 'Wikipedia ja',
                    'source_url': f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(ptitle)}",
                    'confidence': conf,
                }
                out_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                out_f.flush()
                matched += 1
                progress['records_emitted'] += 1
                log(f"    + {ptitle} ({category}, conf={conf}, birth={birth})")

            progress['schools_done'] += 1
            progress['per_school'][sid] = {
                'name': sname, 'persons_checked': checked, 'persons_matched': matched,
                'used_title': used_title,
            }
            # Save progress after each school
            PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8')
            log(f"  done: {matched}/{checked} matched (total {progress['records_emitted']})")
    finally:
        out_f.close()
        progress['finished_at'] = datetime.now().isoformat(timespec='seconds')
        PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8')
        log(f"DONE. emitted={progress['records_emitted']} schools_done={progress['schools_done']}/{progress['schools_total']}")


if __name__ == '__main__':
    main()
