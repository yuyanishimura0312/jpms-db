#!/usr/bin/env python3
"""Team B-4: Extract curriculum & event structures from cached school HTML.

Inputs:
  - /Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache/<school_id>/{curriculum,events,schoollife,about,principal,philosophy,root}.html
  - /Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db (schools_v2.homepage_url)

Outputs:
  - codex_output/team_b4_curriculum.jsonl
  - codex_output/team_b4_events.jsonl
  - codex_progress/team_b4.json
"""
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path('/Users/nishimura+/projects/research/jpms-db/v2')
CACHE = ROOT / 'raw_html_cache'
DB = ROOT / 'jpms_v2.db'
OUT_DIR = ROOT / 'codex_output'
PROG_DIR = ROOT / 'codex_progress'
CURR_OUT = OUT_DIR / 'team_b4_curriculum.jsonl'
EVT_OUT = OUT_DIR / 'team_b4_events.jsonl'
PROG_OUT = PROG_DIR / 'team_b4.json'

OUT_DIR.mkdir(parents=True, exist_ok=True)
PROG_DIR.mkdir(parents=True, exist_ok=True)

PAGE_PATHS = {
    'curriculum': '/curriculum/',
    'events': '/events/',
    'schoollife': '/schoollife/',
    'about': '/about/',
    'principal': '/principal/',
    'philosophy': '/philosophy/',
    'root': '/',
}

# --------------------------- Helpers ---------------------------

def load_school_urls():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT id, name_ja, homepage_url FROM schools_v2')
    out = {row[0]: {'name': row[1], 'hp': row[2]} for row in cur.fetchall()}
    conn.close()
    return out


def read_html(path):
    try:
        return path.read_text(errors='ignore')
    except Exception:
        return ''


def soup_text(html, drop=('script', 'style', 'noscript')):
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(list(drop)):
        s.decompose()
    return soup


def is_404(soup):
    title = (soup.title.string if soup.title and soup.title.string else '').strip()
    return ('404' in title) or ('Not Found' in title) or ('見つかりません' in title)


def clean_lines(text, max_len=120):
    lines = [re.sub(r'\s+', ' ', l).strip() for l in text.split('\n')]
    return [l for l in lines if l and len(l) <= max_len]


# Boilerplate patterns to strip from results
NAV_TOKENS = (
    'ホーム', 'TOP PAGE', 'SCHOOL INFORMATION', 'SCHOOL LIFE', 'CAREER GUIDANCE',
    'ADMISSIONS', 'TOP', 'SITE', 'SEARCH', 'お問い合わせ', '個人情報', 'サイトマップ',
    'メディア', '塾関係', '在校生', '卒業生', '父母と先生', 'プライバシー',
    '当サイトについて', '教職員募集', 'Copyright', 'All Rights Reserved',
    '学園案内', '学園のあらまし', '学園長', '学校長挨拶', '創立記念', '創立',
    '生徒会組織図', '生徒会', '部・同好会紹介', '部活', '入試Q&A', '入試概要',
    '入試状況', '出願', '募集要項', '帰国生', '寮・下宿', '学園説明会',
    '奨学金', '学費', '通学時間', '交通アクセス', '校歌・校章・制服', '施設・アクセス',
    '校史資料室', '図書館', '施設', '取組み', 'カレッジフェア', 'ようこそ先輩',
    '大学入試結果', '進路', '中高入試', '教育内容', '教育理念', '教育方針',
    '中高カリキュラム', '各教科の特色', 'カレンダー・行事', '学校生活Q&A',
    '高校新校舎', '事業所', '採用情報', 'サイト内検索', 'お知らせ', 'ニュース',
    '受験生', '保護者', '在校生・保護者', '学校案内',
)

EXACT_NAV_LINES = {
    'TOP', 'HOME', 'SITE MAP', 'SEARCH', 'ホーム', '進路', '入試', '学校生活',
    '行事予定', '行事', 'イベント', '一覧', '次へ', '前へ', 'ページトップ',
    '中学校', '高等学校', '中高一貫', '中学', '高校',
}


def is_nav(line):
    s = line.strip()
    if len(s) < 2 or len(s) > 80:
        return True
    if s in EXACT_NAV_LINES:
        return True
    for tok in NAV_TOKENS:
        if tok == s:
            return True
    if re.fullmatch(r'[A-Za-z0-9 \-_/&·]+', s):
        return True
    if re.fullmatch(r'[0-9０-９\-/\.、,，年月日 ]+', s):
        return True
    # ascii single nav words
    if re.fullmatch(r'[A-Z][A-Z ]{2,}', s):
        return True
    return False


# --------------------------- Curriculum ---------------------------

# Signature programs/special subjects keywords
SIGNATURE_KEYWORDS = [
    '探究', '探求', 'STEAM', 'SDGs', 'グローバル', '国際', '英語', '海外',
    'ICT', 'IT', 'プログラミング', 'AI', 'IB', 'バカロレア', 'サイエンス',
    'リベラルアーツ', 'リーダー', 'プロジェクト', 'PBL', 'アクティブラーニング',
    '哲学', '宗教', '聖書', '礼拝', '茶道', '華道', '能楽', '邦楽',
    '理数', '医歯薬', '看護', '医学', '芸術', '美術', '音楽', '体育',
    '習熟度', '少人数', '個別', 'ゼミ', '選択', '課外', 'サタデー',
    '自由研究', '卒業研究', '論文', 'プレゼン', 'ディベート',
    '中高一貫', '一貫教育', '文理', '総合', '特進', '特設',
]

# Sub-categorisation hints
ELECTIVE_HINTS = ['選択', '選択科目', 'ゼミ', '講座']
EXTRACURR_HINTS = ['部活', '同好会', '課外', 'クラブ', '部・', '委員会']
SPECIAL_HINTS = ['特別', '特設', '特進', '特化', '一貫', '探究科', 'コース', 'プログラム',
                 '課程', 'カリキュラム', '研修', '海外', 'IB', 'バカロレア', '留学']

# Standard subject names to identify regular courses
STANDARD_SUBJECTS = ['国語', '数学', '英語', '理科', '社会', '保健体育', '体育',
                     '音楽', '美術', '技術', '家庭', '情報', '道徳', '総合', '外国語',
                     '物理', '化学', '生物', '地学', '日本史', '世界史', '地理',
                     '公民', '現代社会', '倫理', '政治・経済', '古典', '現代文']


def categorize_program(name, context=''):
    """Classify a program/subject into category."""
    full = f'{name} {context}'
    if any(h in full for h in EXTRACURR_HINTS):
        return 'extracurricular'
    if any(h in full for h in ELECTIVE_HINTS):
        return 'elective'
    if any(h in full for h in SPECIAL_HINTS):
        return 'special_program'
    if any(name.startswith(s) for s in STANDARD_SUBJECTS):
        return 'regular'
    return 'special_program'  # default for non-standard items found in curriculum pages


def is_signature(name, description):
    text = f'{name} {description}'
    return 1 if any(kw in text for kw in SIGNATURE_KEYWORDS) else 0


def extract_curriculum(school_id, school_dir, hp_url, page_files):
    """Yield curriculum dicts."""
    seen = set()
    items = []

    candidate_pages = ['curriculum', 'about', 'principal', 'philosophy', 'schoollife', 'root']
    for pname in candidate_pages:
        f = school_dir / f'{pname}.html'
        if not f.exists() or f.stat().st_size < 5000:
            continue
        soup = soup_text(read_html(f))
        if is_404(soup):
            continue
        page_url = urljoin(hp_url or '', PAGE_PATHS.get(pname, '/')) if hp_url else None

        # Strategy 1: heading-based extraction (h2, h3, h4, dt, strong)
        for tag in soup.find_all(['h2', 'h3', 'h4', 'dt', 'th']):
            heading = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            if not heading or len(heading) < 3 or len(heading) > 50:
                continue
            if is_nav(heading):
                continue
            if not _looks_curriculum(heading):
                continue
            # Description = next sibling text
            desc = ''
            sib = tag.find_next_sibling()
            if sib:
                desc = re.sub(r'\s+', ' ', sib.get_text(strip=True))[:300]
            key = (school_id, heading)
            if key in seen:
                continue
            seen.add(key)
            items.append(_make_curr(school_id, heading, desc, page_url, pname))
            if len(items) >= 12:
                break
        if len(items) >= 12:
            break

        # Strategy 2: list items if no headings yielded
        if not items:
            for li in soup.find_all('li'):
                text = re.sub(r'\s+', ' ', li.get_text(' ', strip=True))
                if 5 < len(text) < 80 and _looks_curriculum(text) and not is_nav(text):
                    key = (school_id, text)
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(_make_curr(school_id, text, '', page_url, pname))
                    if len(items) >= 8:
                        break

    return items[:15]


CURR_BLOCKLIST = (
    'お問い合わせ', 'プライバシー', 'サイトマップ', '入試Q', '受験生', '保護者',
    'リンク', 'アクセス', '校歌', '校章', '制服', '寮', '下宿', '採用情報',
    '募集要項', '出願', '入試状況', '入試結果', '奨学金', '学費', '通学時間',
    '校史資料', '図書館', 'カレンダー・行事', 'カレンダー', 'お知らせ',
    'ニュース', 'ブログ', '日記', '組織図', 'お問合せ', 'のご案内',
    'はじめに', 'について', 'リクルート',
)


def _looks_curriculum(text):
    """Filter for curriculum-relevant headings."""
    if len(text) < 3 or len(text) > 50:
        return False
    if any(b in text for b in CURR_BLOCKLIST):
        return False
    # reject lines that look like aggregated navs (multiple labels separated by spaces)
    if text.count(' ') >= 4:
        return False
    keywords = ['カリキュラム', '教育課程', '教育内容', '科目', '授業', 'コース',
                'プログラム', '探究', '探求', '研修', '実習', 'ゼミ', '選択',
                '部活動', '同好会', 'クラブ', '課外', '特進', '特設', '特別活動',
                'リベラル', 'グローバル', '国際', '英語', 'STEAM', 'SDGs', 'ICT',
                'AI教育', 'IB', 'バカロレア', '習熟度', '少人数', 'PBL', '哲学',
                '宗教', '聖書', '礼拝', '茶道', '華道', '能楽', '邦楽',
                '医歯薬', '看護', '医学', '理数', '文理', '一貫', '探究科',
                '時間割', '時数', '総合学習', '総合的な学習', '総合的な探究',
                '中高一貫', 'アクティブラーニング', '海外', '留学', '英会話',
                'ネイティブ', '討論', 'プレゼン', '卒業研究', '卒業論文']
    return any(kw in text for kw in keywords)


def _make_curr(school_id, name, description, source_url, pname):
    cat = categorize_program(name, description)
    return {
        'school_id': school_id,
        'category': cat,
        'subject_or_program': name[:80],
        'description': description[:300] if description else f'{pname}ページから抽出',
        'grade_levels': '1-3',  # default; specific grade info rare in HTML
        'is_signature': is_signature(name, description),
        'source_url': source_url or '',
    }


# --------------------------- Events ---------------------------

MONTH_PAT = re.compile(r'^(?:[0-9０-９]{1,2}|[一二三四五六七八九十]+)\s*月')
MONTH_HEAD_PAT = re.compile(r'^[0-9０-９]{1,2}月')

EVENT_TYPE_RULES = [
    ('festival', ['文化祭', '学園祭', '学校祭', '学芸会', '発表会', '芸術祭', '音楽祭', '合唱祭', '合唱コンクール']),
    ('sports_day', ['運動会', '体育祭', '体育大会', '球技大会', 'スポーツ大会', 'スポーツデイ', 'マラソン大会', '持久走']),
    ('study_trip', ['修学旅行']),
    ('excursion', ['遠足', '校外学習', '社会科見学', '宿泊', '林間', '臨海', 'オリエンテーション合宿',
                   '研修旅行', '宿泊研修', 'スキー教室', '林間学校', '臨海学校']),
    ('other', []),  # default
]

# Common shared events to classify
KNOWN_EVENTS = {
    '入学式': 'other', '卒業式': 'other', '始業式': 'other', '終業式': 'other',
    '修了式': 'other', '創立記念日': 'other', '創立記念': 'other', '防災訓練': 'other',
    '避難訓練': 'other', '生徒総会': 'other', 'オープンスクール': 'other',
    '芸術鑑賞': 'other', '芸術鑑賞会': 'other', '定期考査': 'other',
    '中間考査': 'other', '期末考査': 'other', '保護者会': 'other',
}


def classify_event(name):
    if not name:
        return 'other'
    for et, kws in EVENT_TYPE_RULES:
        for kw in kws:
            if kw in name:
                return et
    for kw, et in KNOWN_EVENTS.items():
        if kw in name:
            return et
    return 'other'


EVENT_BLOCKLIST = (
    '案内', '紹介', '一覧', '組織図', '挨拶', '指導', '受験', '募集', '申込',
    '連絡', '結果', '速報', 'について', 'のご案内', 'のお知らせ', 'はじめに',
    'コラム', 'ブログ', '日記', '入試', 'メニュー', 'タブ', 'もっと見る',
    '校歌', '校章', '制服', '寮', '下宿', '校内案内', '個別相談', 'Q&A',
    'リンク', 'ダウンロード', '資料請求', 'アクセス', '理念', '方針',
    '読み込み', 'JavaScript', '校長', '学長', '理事長', 'サイト', 'ホームページ',
    '保護者会', '父母会', 'PTA', '大学', '進学', '進路指導',
    'ページを更新', '情報を更新', 'を更新しました', '説明会', '見学会',
    '相談会', '体験会', 'の様子', 'は終了', 'ー1', 'ー2', 'ー3', 'ー4',
    '日目の様子', '▶', '・・・', '...',
)

EVENT_STRONG_KEYWORDS = (
    # event-specific compound terms
    '入学式', '卒業式', '始業式', '終業式', '修了式', '創立記念日', '記念式典',
    '文化祭', '学園祭', '学校祭', '体育祭', '運動会', '球技大会', 'スポーツ大会',
    'スポーツデイ', 'マラソン大会', '持久走', '修学旅行', '研修旅行', '宿泊研修',
    '林間学校', '林間', '臨海学校', '臨海', 'スキー教室', 'スキー実習',
    '音楽祭', '合唱祭', '合唱コンクール', '芸術祭', '芸術鑑賞会', '芸術鑑賞',
    '校外学習', '社会科見学', '工場見学', '宿泊学習', 'オリエンテーション',
    '中間考査', '期末考査', '定期考査', '実力考査', '模試', '校内模試',
    '防災訓練', '避難訓練', '英語暗誦', 'スピーチコンテスト', 'ディベート大会',
    '学芸会', '発表会', '展覧会', '献堂式', 'ミサ', '礼拝', 'クリスマス',
    'スポーツテスト', '生徒総会', 'クラブ発表', '研究旅行', '研究発表会',
    '遠足', '見学', '修養会', '体験学習', '海外研修', '海外語学',
    '弁論大会', 'コンサート', '定期演奏会', '父母と先生の会総会',
)


def is_event_name(line):
    s = line.strip()
    if len(s) < 3 or len(s) > 30:
        return False
    if is_nav(s):
        return False
    if any(b in s for b in EVENT_BLOCKLIST):
        return False
    # avoid pure dates / numeric noise
    if re.fullmatch(r'[0-9０-９/.\-月日 　]+', s):
        return False
    # avoid lines that are mostly numeric (dates)
    if re.search(r'^[0-9０-９]{4}[/\-.]', s):
        return False
    # require strong event keyword
    return any(kw in s for kw in EVENT_STRONG_KEYWORDS)


def parse_duration(line):
    """Detect 'N泊' or '日間' patterns near the line, default 1.0."""
    m = re.search(r'(\d+)\s*泊\s*(\d+)\s*日', line)
    if m:
        return float(m.group(2))
    m = re.search(r'(\d+)\s*日間', line)
    if m:
        return float(m.group(1))
    if '修学旅行' in line:
        return 4.0
    if '林間' in line or '臨海' in line or '宿泊' in line:
        return 3.0
    return 1.0


def extract_destination(line):
    # Capture place names in parentheses or after で/に for trips
    m = re.search(r'[（(]([^）)]{2,30})[)）]', line)
    if m:
        place = m.group(1)
        # rough sanity check
        if not re.search(r'[年月日0-9０-９]', place):
            return place
    # specific patterns: "シンガポール" etc - leave None for safety
    return None


def extract_events(school_id, school_dir, hp_url, page_files):
    items = []
    seen = set()

    candidate_pages = ['events', 'schoollife', 'about', 'root']
    for pname in candidate_pages:
        f = school_dir / f'{pname}.html'
        if not f.exists() or f.stat().st_size < 5000:
            continue
        soup = soup_text(read_html(f))
        if is_404(soup):
            continue
        page_url = urljoin(hp_url or '', PAGE_PATHS.get(pname, '/')) if hp_url else None

        text = soup.get_text(separator='\n', strip=True)
        lines = clean_lines(text, max_len=80)

        # Strategy: look for month headings followed by event names
        current_month = None
        for i, line in enumerate(lines):
            # strip BOM-like artefacts
            line = line.strip()
            if not line:
                continue
            if MONTH_HEAD_PAT.match(line):
                current_month = line
                continue
            if MONTH_PAT.match(line) and len(line) <= 6:
                current_month = line
                continue
            if current_month and is_event_name(line):
                # normalize: strip parentheticals, leading dates, emojis
                norm = re.sub(r'[（(].*?[)）]', '', line).strip()
                norm = re.sub(r'^[0-9０-９]{2,4}[/\.\-][0-9０-９]{1,2}([/\.\-][0-9０-９]{1,2})?\s*', '', norm)
                norm = re.sub(r'^第[0-9０-９]+回\s*', '', norm)
                norm = re.sub(r'[🌸🎉🌟📣💐🎓🎊]+', '', norm).strip()
                norm = re.sub(r'(を行いました|が行われました|を挙行しました|を実施しました|・・・|…)$', '', norm).strip()
                if not norm or len(norm) < 3:
                    continue
                key = (school_id, norm)
                if key in seen:
                    continue
                seen.add(key)
                # contextual description: try next non-month line
                desc = ''
                if i + 1 < len(lines):
                    nxt = lines[i + 1]
                    if not MONTH_PAT.match(nxt) and not is_event_name(nxt) and len(nxt) < 80:
                        desc = nxt
                items.append({
                    'school_id': school_id,
                    'event_type': classify_event(line),
                    'event_name': norm[:60],
                    'duration_days': parse_duration(line + ' ' + desc),
                    'destination': extract_destination(line + ' ' + desc),
                    'description': (current_month + '実施。' + desc)[:200] if desc else f'{current_month}実施',
                    'source_url': page_url or '',
                })
                if len(items) >= 15:
                    return items[:15]

        # Fallback: keyword extraction without month context
        if len(items) < 5:
            for line in lines:
                if is_event_name(line):
                    norm = re.sub(r'[（(].*?[)）]', '', line).strip()
                    norm = re.sub(r'^[0-9０-９]{2,4}[/\.\-][0-9０-９]{1,2}([/\.\-][0-9０-９]{1,2})?\s*', '', norm)
                    norm = re.sub(r'^第[0-9０-９]+回\s*', '', norm)
                    norm = re.sub(r'[🌸🎉🌟📣💐🎓🎊]+', '', norm).strip()
                    norm = re.sub(r'(を行いました|が行われました|を挙行しました|を実施しました|・・・|…)$', '', norm).strip()
                    if not norm or len(norm) < 3:
                        continue
                    key = (school_id, norm)
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append({
                        'school_id': school_id,
                        'event_type': classify_event(line),
                        'event_name': norm[:60],
                        'duration_days': parse_duration(line),
                        'destination': extract_destination(line),
                        'description': f'{pname}ページより抽出',
                        'source_url': page_url or '',
                    })
                    if len(items) >= 12:
                        return items[:15]

    return items[:15]


# --------------------------- Main ---------------------------

def main():
    school_meta = load_school_urls()
    school_dirs = sorted([d for d in CACHE.iterdir() if d.is_dir()])

    curr_records = []
    evt_records = []
    schools_with_curr = 0
    schools_with_evt = 0

    for sd in school_dirs:
        sid = sd.name
        meta = school_meta.get(sid, {})
        hp_url = meta.get('hp', '')
        page_files = {f.stem: f for f in sd.iterdir() if f.is_file() and f.suffix == '.html'}

        c_items = extract_curriculum(sid, sd, hp_url, page_files)
        e_items = extract_events(sid, sd, hp_url, page_files)

        if c_items:
            schools_with_curr += 1
            curr_records.extend(c_items)
        if e_items:
            schools_with_evt += 1
            evt_records.extend(e_items)

    # Write output
    with CURR_OUT.open('w', encoding='utf-8') as f:
        for rec in curr_records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    with EVT_OUT.open('w', encoding='utf-8') as f:
        for rec in evt_records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    progress = {
        'task_id': 'team_b4',
        'completed': len(school_dirs),
        'curriculum_records': len(curr_records),
        'event_records': len(evt_records),
        'schools_with_curriculum': schools_with_curr,
        'schools_with_events': schools_with_evt,
        'ts': datetime.now(timezone.utc).isoformat(),
    }
    PROG_OUT.write_text(json.dumps(progress, ensure_ascii=False, indent=2))

    print('=== Team B-4 Extraction Summary ===')
    print(f'Schools scanned: {len(school_dirs)}')
    print(f'Curriculum records: {len(curr_records)} (across {schools_with_curr} schools)')
    print(f'Event records: {len(evt_records)} (across {schools_with_evt} schools)')
    print(f'Output:\n  {CURR_OUT}\n  {EVT_OUT}')
    print(f'Progress: {PROG_OUT}')


if __name__ == '__main__':
    main()
