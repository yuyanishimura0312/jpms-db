#!/usr/bin/env python3
"""Team C-4: Extract academic / cultural alumni from Wikipedia ja.

Strategy:
- For each top traditional school, try its dedicated alumni list article first
  (e.g. "開成中学校・高等学校の人物一覧"). These pages categorize alumni into
  sections like 政治 / 学者 / 文学 / 芸術・芸能 / マスコミ etc.
- Pull names from sections that match academic / cultural / writer / artist / journalist
  categories. The section header itself provides categorization, so we do NOT need to
  fetch each person's own article — drastically cutting API hits.
- Each person line is parsed for description text (after the wikilink) to populate
  evidence_text and infer birth_year if a parenthesised year is present.
- For people without a clear category (e.g. 共立学校の出身者 lump section), we skip.

Output:
- JSONL: ~/projects/research/jpms-db/v2/codex_output/team_c4_academic.jsonl
- Progress: ~/projects/research/jpms-db/v2/codex_progress/team_c4.json

Ethics:
- User-Agent: JPMS-DB-Research/2.0
- 5 sec/req delay against ja.wikipedia.org
- Wikipedia API permits research / bot use under standard UA + reasonable rate
- Public figures only (Wikipedia notability standard); we exclude minors
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

OUT = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c4_academic.jsonl')
PROGRESS = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_progress/team_c4.json')
LOG = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_logs/team_c4.log')

USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org; https://yuyanishimura0312.github.io/jpms-db/)'
WP_API = 'https://ja.wikipedia.org/w/api.php'
WP_VIEW = 'https://ja.wikipedia.org/wiki/'
DELAY = 5.0  # sec/request to ja.wikipedia.org

# Top 30 traditional / prominent private schools.
# wiki_main = main school article; wiki_alumni = candidate dedicated alumni page (may not exist).
# When alumni page exists with categorized sections, that is the preferred source.
TARGET_SCHOOLS = [
    # (school_id, school_name_for_record, wiki_main_title, wiki_alumni_title)
    ('jpms_s_0001', '開成中学校', '開成中学校・高等学校', '開成中学校・高等学校の人物一覧'),
    ('jpms_s_0002', '麻布中学校', '麻布中学校・高等学校', '麻布中学校・高等学校の人物一覧'),
    ('jpms_s_0003', '桜蔭中学校', '桜蔭中学校・高等学校', '桜蔭中学校・高等学校の人物一覧'),
    ('jpms_s_0006', '灘中学校', '灘中学校・高等学校', '灘中学校・高等学校の人物一覧'),
    ('jpms_s_0034', '海城中学校', '海城中学校・高等学校', '海城中学校・高等学校の人物一覧'),
    ('jpms_s_0035', '学習院女子中等科', '学習院女子中等科・高等科', '学習院女子中等科・高等科の人物一覧'),
    ('jpms_s_0404', '学習院中等科', '学習院中等科・高等科', '学習院中等科・高等科の人物一覧'),
    ('jpms_s_0067', '攻玉社中学校', '攻玉社中学校・高等学校', '攻玉社中学校・高等学校の人物一覧'),
    ('jpms_s_0023', '慶應義塾中等部', '慶應義塾中等部', None),
    ('jpms_s_0133', '慶應義塾普通部', '慶應義塾普通部', '慶應義塾普通部の人物一覧'),
    ('jpms_s_0410', '武蔵中学校', '武蔵高等学校・中学校 (旧制武蔵高等学校)', '武蔵高等学校・中学校 (旧制武蔵高等学校)の人物一覧'),
    ('jpms_s_0479', '桐朋中学校', '桐朋中学校・桐朋高等学校', '桐朋中学校・桐朋高等学校の人物一覧'),
    ('jpms_s_0009', '神戸女学院中学部', '神戸女学院中学部・高等学部', '神戸女学院中学部・高等学部の人物一覧'),
    ('jpms_s_0004', '雙葉中学校', '雙葉中学校・高等学校', '雙葉中学校・高等学校の人物一覧'),
    ('jpms_s_0016', '女子学院中学校', '女子学院中学校・高等学校', '女子学院中学校・高等学校の人物一覧'),
    ('jpms_s_0017', '白百合学園中学校', '白百合学園中学校・高等学校', '白百合学園中学校・高等学校の人物一覧'),
    ('jpms_s_0025', '芝中学校', '芝中学校・高等学校', '芝中学校・高等学校の人物一覧'),
    ('jpms_s_0013', '暁星中学校', '暁星中学校・高等学校', '暁星中学校・高等学校の人物一覧'),
    ('jpms_s_0030', '東洋英和女学院中学部', '東洋英和女学院中学部・高等部', '東洋英和女学院中学部・高等部の人物一覧'),
    ('jpms_s_0039', '早稲田中学校', '早稲田中学校・高等学校', '早稲田中学校・高等学校の人物一覧'),
    ('jpms_s_0062', '駒場東邦中学校', '駒場東邦中学校・高等学校', '駒場東邦中学校・高等学校の人物一覧'),
    ('jpms_s_p3_001', '栄光学園中学校', '栄光学園中学校・高等学校', '栄光学園中学校・高等学校の人物一覧'),
    ('jpms_s_p3_003', '聖光学院中学校', '聖光学院中学校・高等学校 (神奈川県)', '聖光学院中学校・高等学校 (神奈川県)の人物一覧'),
    ('jpms_s_0631', '甲陽学院中学校', '甲陽学院中学校・高等学校', '甲陽学院中学校・高等学校の人物一覧'),
    ('jpms_s_0646', '東大寺学園中学校', '東大寺学園中学校・高等学校', '東大寺学園中学校・高等学校の人物一覧'),
    ('jpms_s_0007', '洛南高等学校附属中学校', '洛南高等学校・附属中学校', '洛南高等学校・附属中学校の人物一覧'),
    ('jpms_s_0906', 'ラ・サール中学校', 'ラ・サール中学校・高等学校', 'ラ・サール中学校・高等学校の人物一覧'),
    ('jpms_s_0622', '同志社中学校', '同志社中学校・高等学校', '同志社中学校・高等学校の人物一覧'),
    ('jpms_s_0635', '関西学院中学部', '関西学院中学部・高等部', '関西学院中学部・高等部の人物一覧'),
    ('jpms_s_0700', '東海中学校', '東海中学校・高等学校 (愛知県)', '東海中学校・高等学校 (愛知県)の人物一覧'),
    ('jpms_s_0027', '聖心女子学院中等科', '聖心女子学院初等科・中等科・高等科', '聖心女子学院初等科・中等科・高等科の人物一覧'),
    ('jpms_s_0400', '豊島岡女子学園中学校', '豊島岡女子学園中学校・高等学校', '豊島岡女子学園中学校・高等学校の人物一覧'),
]

# Section header → category mapping (covers academic/cultural/writer/artist/journalist).
# Sections explicitly skipped (in scope of C-3 or out of scope): 政治, 行政・官僚, 金融, 商社・実業家,
# 経営, 法曹, 軍人, スポーツ, 芸能（俳優中心）, アナウンサー, 信仰（宗教者は cultural として一部拾う）
SECTION_CATEGORY = {
    '学者': 'academic',
    '学界': 'academic',
    '学術': 'academic',
    '学術・教育': 'academic',
    '学術・研究': 'academic',
    '研究者': 'academic',
    '研究': 'academic',
    '学者・研究者': 'academic',
    '教育・学術': 'academic',
    '教育': 'academic',
    '教育者': 'academic',
    '医学': 'academic',
    '医学者': 'academic',
    '医療': 'academic',
    '医師': 'academic',
    '理学': 'academic',
    '工学': 'academic',
    '理工系': 'academic',
    '人文・社会科学': 'academic',
    '人文科学': 'academic',
    '社会科学': 'academic',
    '自然科学': 'academic',
    # 思想 / 信仰 sections often include activists/criminals — only accept clear
    # religious figures or thinkers via per-line keyword filter
    '思想・宗教': 'cultural',
    '宗教': 'cultural',
    '宗教者': 'cultural',
    '信仰': 'cultural',
    '哲学': 'academic',
    '文学': 'writer',
    '小説': 'writer',
    '小説家': 'writer',
    '作家': 'writer',
    '作家・文芸': 'writer',
    '評論家': 'writer',
    '俳人・歌人': 'writer',
    '詩人': 'writer',
    '文学・思想': 'writer',
    '文芸': 'writer',
    '出版': 'cultural',
    '芸術': 'artist',
    '芸術・芸能': 'artist',
    '芸能・芸術': 'artist',
    '美術': 'artist',
    '美術・建築': 'artist',
    '建築': 'artist',
    '建築家': 'artist',
    'デザイン': 'artist',
    '音楽': 'artist',
    '映画': 'artist',
    '映画・テレビ': 'artist',
    '伝統芸能': 'artist',
    '芸能': 'artist',  # but we will further filter by EXCLUDE_KW per line
    'マスコミ': 'cultural',
    'メディア': 'cultural',
    'マスメディア': 'cultural',
    '報道': 'cultural',
    'ジャーナリズム': 'cultural',
    'ジャーナリスト': 'cultural',
}

# Skip these sections entirely
SKIP_SECTIONS = {
    '政治', '行政', '行政・官僚', '官僚', '金融', '商社・実業家', '実業家', '経営', '経営者',
    '法曹', '裁判官', '弁護士', '軍人', '軍隊', 'スポーツ', '体育', '野球', 'サッカー',
    'アスリート', 'プロ野球', '理事長', '理事長・学園長', '教職員', '教職員一覧', '教員',
    '関連項目', '脚注', '注釈', '出典', 'その他', '共立学校の出身者',
    '社会運動', '実業', '財界', 'ビジネス', '武道',
}

# Per-line filter: even within an artist/cultural section, skip people who are
# primarily 俳優・タレント・歌手・お笑い・YouTuber・スポーツ選手・テロリスト・犯罪者 等
LINE_EXCLUDE_KW = [
    '俳優', '女優', 'タレント', 'お笑い', '芸人', 'アイドル', 'グラビア',
    '声優', 'YouTuber', '配信者', 'モデル', 'お笑いコンビ',
    'プロ野球', 'サッカー選手', 'ラグビー', 'ボクサー', 'プロゴルファー', 'プロ棋士',
    'プロレスラー', '競輪選手', '競馬',
    'AV女優', 'AV男優',
    'テロリスト', '死刑囚', '犯罪者', '受刑者', '指名手配',
    'アナキスト', 'ダダイスト', '無政府主義',
    '極左', '極右', '右翼', '左翼活動',
]


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat()
    with LOG.open('a') as f:
        f.write(f'[{ts}] {msg}\n')
    print(msg)


def update_progress(stats):
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps({
        'task_id': 'team_c4',
        **stats,
        'ts': datetime.now().isoformat() + 'Z',
    }, ensure_ascii=False, indent=2))


_last_request = 0.0


def wp_request(params):
    """Hit Wikipedia API with delay + UA. Returns parsed JSON or None."""
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < DELAY:
        time.sleep(DELAY - elapsed)
    _last_request = time.time()
    qs = urllib.parse.urlencode(params)
    url = f'{WP_API}?{qs}'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        log(f'  WP request error: {url[:120]} :: {e}')
        return None


def get_page_wikitext(title):
    """Fetch raw wikitext for a page. Returns None if missing."""
    data = wp_request({
        'action': 'parse',
        'page': title,
        'prop': 'wikitext',
        'format': 'json',
        'redirects': 1,
    })
    if not data or 'parse' not in data:
        return None
    return data['parse'].get('wikitext', {}).get('*')


def normalize_section_name(raw):
    """Strip wiki markup, collapse whitespace, drop trailing notes."""
    s = re.sub(r"'''?", '', raw)  # bold/italic markers
    s = re.sub(r'\[\[([^\[\]\|]+\|)?([^\[\]]+)\]\]', r'\2', s)  # [[link|text]] -> text
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    s = re.sub(r'\s+', '', s).strip()
    return s


def parse_sections(wikitext):
    """Return list of (level, section_name, body_text)."""
    if not wikitext:
        return []
    pattern = re.compile(r'^(={2,4})\s*(.+?)\s*\1\s*$', re.MULTILINE)
    sections = []
    matches = list(pattern.finditer(wikitext))
    for i, m in enumerate(matches):
        level = len(m.group(1))
        name = normalize_section_name(m.group(2))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(wikitext)
        body = wikitext[start:end]
        sections.append((level, name, body))
    return sections


def parse_alumni_lines(body):
    """From a section body, parse list lines (* or # or *) and pull link + description.

    Returns list of dicts: {name, description, raw_line}
    """
    out = []
    seen = set()
    # Match list items starting with '*' optionally with leading spaces
    for raw in body.split('\n'):
        line = raw.strip()
        if not line.startswith('*'):
            continue
        # Strip the leading '*' and any sub-bullet markers
        stripped = re.sub(r'^[\*#:\s]+', '', line)
        # First [[wikilink]] is the person; subsequent text is the description
        m = re.search(r'\[\[([^\[\]\|]+?)(?:\|([^\[\]]+))?\]\]', stripped)
        if not m:
            continue
        page_name = m.group(1).strip()
        if '#' in page_name:
            page_name = page_name.split('#')[0].strip()
        if not page_name:
            continue
        if page_name.startswith(('Category:', 'File:', 'ファイル:', 'カテゴリ:', '画像:', ':File:', ':Category:')):
            continue
        # Skip year/date-only links
        if re.match(r'^\d{1,4}年', page_name):
            continue
        if page_name in seen:
            continue
        seen.add(page_name)
        # Description: text after the closing ]] of the first link
        rest = stripped[m.end():].strip()
        # Strip remaining wikitext to plain text
        desc_clean = re.sub(r'\[\[([^\[\]\|]+\|)?([^\[\]]+)\]\]', r'\2', rest)
        desc_clean = re.sub(r'\{\{[^{}]*\}\}', '', desc_clean)
        desc_clean = re.sub(r"'{2,}", '', desc_clean)
        desc_clean = re.sub(r'<ref[^>]*?(?:>.*?</ref>|/>)', '', desc_clean, flags=re.DOTALL)
        desc_clean = re.sub(r'<[^>]+>', '', desc_clean)
        desc_clean = re.sub(r'\s+', ' ', desc_clean).strip(' -–—\t')
        out.append({'name': page_name, 'description': desc_clean[:240], 'raw_line': stripped[:280]})
    return out


def extract_birth_from_line(desc, raw_line):
    """Pull a 4-digit year from common patterns:
    '*[[名前]] (1958) - 経済学者'
    '生年: 1955年'
    """
    text = raw_line + ' ' + desc
    # Pattern: '(1958)' typically = graduation year, NOT birth.
    # We do NOT use parenthesised year because in 人物一覧 pages it usually means
    # graduation year. Birth year is rarely present here.
    # Look for '生年 1955' or '1955年生'
    m = re.search(r'(\d{4})年生(?:まれ)?', text)
    if m:
        y = int(m.group(1))
        if 1800 <= y <= 2026:
            return y
    return None


def is_excluded_line(desc):
    if not desc:
        return False
    return any(kw in desc for kw in LINE_EXCLUDE_KW)


def derive_subcategory(section_name, desc):
    """Refine category: e.g. someone in '芸術・芸能' could be 俳優 (excluded) vs 画家 (artist).
    Returns category or None (None = skip).
    """
    base = SECTION_CATEGORY.get(section_name)
    if base is None:
        return None
    if is_excluded_line(desc):
        return None
    # Extra cultural-vs-writer adjustments
    if base == 'artist':
        # If description suggests writer/journalist primarily, adjust
        if any(kw in desc for kw in ['作家', '小説家', '詩人', '随筆家', '俳人', '歌人']):
            return 'writer'
        if any(kw in desc for kw in ['ジャーナリスト', '評論家', '記者', 'コラムニスト']):
            return 'cultural'
    if base == 'writer':
        if any(kw in desc for kw in ['画家', '彫刻家', '建築家', '作曲家', '指揮者']):
            return 'artist'
    if base == 'cultural':
        # If it's a section like マスコミ but description says 学者, prefer academic
        if any(kw in desc for kw in ['学者', '名誉教授', '教授', '研究者']):
            return 'academic'
    return base


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    log(f'=== Team C-4 start: {len(TARGET_SCHOOLS)} schools ===')

    # Resume: load already-emitted (name, school_id) pairs
    emitted = set()
    if OUT.exists():
        try:
            for line in OUT.read_text().splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                emitted.add((rec.get('name'), rec.get('matched_school_id')))
            log(f'Resume: {len(emitted)} records already in output')
        except Exception as e:
            log(f'Could not resume: {e}')

    schools_processed = 0
    schools_with_data = 0
    total_records = len(emitted)

    out_f = OUT.open('a')

    for sid, sname, wp_main, wp_alumni in TARGET_SCHOOLS:
        log(f'\n--- {sid} {sname} ---')

        wikitext = None
        source_title = None
        # Try dedicated alumni page first
        if wp_alumni:
            wikitext = get_page_wikitext(wp_alumni)
            if wikitext:
                source_title = wp_alumni
                log(f'  [alumni page] {wp_alumni}: {len(wikitext)} chars')
        # Fallback to main school article
        if not wikitext:
            wikitext = get_page_wikitext(wp_main)
            if wikitext:
                source_title = wp_main
                log(f'  [main page]   {wp_main}: {len(wikitext)} chars')
        if not wikitext:
            log(f'  ! page missing for {sname}')
            schools_processed += 1
            update_progress({
                'completed': schools_processed,
                'with_data': schools_with_data,
                'total_schools': len(TARGET_SCHOOLS),
                'records': total_records,
            })
            continue

        sections = parse_sections(wikitext)
        added_for_school = 0

        # Track current top-level alumni group (e.g. 出身者 vs 教職員)
        in_alumni_group = False
        for level, name, body in sections:
            # Top-level (level == 2): determine if we are inside alumni or skip group
            if level == 2:
                if name in {'出身者', '主な出身者', '主な卒業生', '著名な卒業生',
                            '主な人物', '関連人物', '関係者', '中学・高等学校関係者一覧',
                            '関連団体・関係者一覧', '関連人物・関係者'}:
                    in_alumni_group = True
                else:
                    in_alumni_group = False
                # When the level-2 section itself has list items, also process if it maps to a category
                cat_l2 = SECTION_CATEGORY.get(name)
                if cat_l2:
                    in_alumni_group = True  # treat level-2 categorized section as alumni
                else:
                    # Don't process body of unmapped level-2 sections directly
                    continue

            if not in_alumni_group:
                continue

            # Skip excluded sub-sections
            if name in SKIP_SECTIONS:
                continue

            cat_for_section = SECTION_CATEGORY.get(name)
            if not cat_for_section:
                continue  # unmapped sub-section: skip

            lines = parse_alumni_lines(body)
            for line_info in lines:
                pname = line_info['name']
                desc = line_info['description']
                raw_line = line_info['raw_line']
                if (pname, sid) in emitted:
                    continue
                cat = derive_subcategory(name, desc)
                if not cat:
                    continue
                birth = extract_birth_from_line(desc, raw_line)
                evidence = (desc or raw_line)[:220].strip()
                if not evidence:
                    evidence = f'Wikipedia「{source_title}」{name}の節に掲載'
                source_url = WP_VIEW + urllib.parse.quote(source_title)
                rec = {
                    'name': pname,
                    'birth': birth,
                    'category': cat,
                    'matched_school_id': sid,
                    'matched_school_name': sname,
                    'match_type': 'alumni',
                    'evidence_text': evidence,
                    'source': 'Wikipedia ja',
                    'source_url': source_url,
                    'confidence': 3,
                }
                out_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                out_f.flush()
                emitted.add((pname, sid))
                total_records += 1
                added_for_school += 1

        if added_for_school:
            schools_with_data += 1
        schools_processed += 1
        log(f'  → +{added_for_school} records (total: {total_records})')
        update_progress({
            'completed': schools_processed,
            'with_data': schools_with_data,
            'total_schools': len(TARGET_SCHOOLS),
            'records': total_records,
        })

    out_f.close()

    update_progress({
        'completed': schools_processed,
        'with_data': schools_with_data,
        'total_schools': len(TARGET_SCHOOLS),
        'records': total_records,
        'status': 'completed',
    })
    log(f'\n=== DONE === records: {total_records} | schools w/data: {schools_with_data}/{schools_processed}')


if __name__ == '__main__':
    main()
