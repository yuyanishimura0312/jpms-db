#!/usr/bin/env python3
"""JPMS-DB v2 Phase E - Team B-5: 保護者声 / PTA・後援会情報抽出

戦略:
- 新規取得した parent.html / pta.html を最優先で対象とする
- すでに取得済みのページ (about / voice / schoollife / root / events) も
  保護者言及の段落のみフィルタして拾う
- 出力: codex_output/team_b5_parent.jsonl
- 進捗: codex_progress/team_b5.json
- 倫理: 公開情報のみ・引用400字以内
"""
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

BASE = Path('/Users/nishimura+/projects/research/jpms-db/v2')
CACHE = BASE / 'raw_html_cache'
DB = BASE / 'jpms_v2.db'
OUT = BASE / 'codex_output' / 'team_b5_parent.jsonl'
PROGRESS = BASE / 'codex_progress' / 'team_b5.json'

# 優先順位: parent / pta は専用、それ以外は保護者言及があれば抽出
PARENT_DEDICATED = ['parent', 'pta']
SECONDARY_PAGES = ['voice', 'schoollife', 'events', 'about', 'admission', 'root']

# 保護者カテゴリのアンカー語
PARENT_ANCHORS = [
    '保護者', '保護者会', '保護者の声', '保護者の方',
    'PTA', '父母会', '父母の会', '後援会', '育友会',
    '父兄', '母の会', 'ファミリー', '家庭と学校',
]

# 役割推定用
ROLE_HINTS = {
    'parent': ['保護者', '父母', 'お母さま', 'お父さま', 'お母様', 'お父様', '母', '父',
               'PTA', '父母会', '後援会', '育友会', 'ご家庭'],
}

# ナビ・メタ系の弾きキーワード（B-1 と同方針）
NEGATIVE_HINTS = [
    'プライバシー', 'cookie', 'クッキー', '著作権', 'サイトマップ',
    'お問い合わせ', '個人情報保護', '採用情報', '会社概要',
    '利用規約', 'twitter', 'facebook', 'instagram', 'youtube',
    'all rights', 'copyright', '一覧へ', 'もっと見る', '詳しく見る',
    'メニュー', 'navigation', 'breadcrumb', 'ログイン',
    'メールアドレス', 'パスワード', 'ダウンロード',
    'ホーム>', 'TOP>',
    'ID／パスワード', 'IDとパスワード', '保護中',
]

# 説明会・申込告知系 (parent 関連でも除外)
EVENT_NEGATIVE = [
    '実施します', '開催します', '開催中', '受付中',
    'お申し込み', '申し込みフォーム', '入試説明',
    '受験生のみなさま', '受験生の方へ',
]


def get_url_map():
    if not DB.exists():
        return {}, {}
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT school_id, page_path, full_url FROM school_homepage_assets")
    m = {}
    for sid, page, url in cur.fetchall():
        m[(sid, page)] = url
    cur.execute("SELECT id, homepage_url FROM schools_v2")
    fb = {}
    for sid, url in cur.fetchall():
        if url:
            fb[sid] = url
    conn.close()
    return m, fb


def read_html(fpath):
    """HTML ファイルを読み込み（charset 自動判定）"""
    raw = fpath.read_bytes()
    m = re.search(rb'charset=[\'"]?([a-zA-Z0-9_-]+)', raw[:2000], re.IGNORECASE)
    enc = 'utf-8'
    if m:
        detected = m.group(1).decode('ascii', errors='ignore').lower()
        if detected in ('utf-8', 'utf8'):
            enc = 'utf-8'
        elif detected in ('shift_jis', 'sjis', 'shift-jis', 'cp932', 'ms932', 'x-sjis'):
            enc = 'cp932'
        elif detected in ('euc-jp', 'eucjp', 'euc_jp'):
            enc = 'euc-jp'
        elif detected in ('iso-2022-jp', 'jis'):
            enc = 'iso-2022-jp'
        else:
            enc = detected
    try:
        return raw.decode(enc, errors='ignore')
    except Exception:
        for fb in ('utf-8', 'cp932', 'euc-jp'):
            try:
                return raw.decode(fb, errors='ignore')
            except Exception:
                continue
        return raw.decode('utf-8', errors='ignore')


def extract_paragraphs(html):
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()
    for sel in soup.select(
        '.breadcrumb, .breadcrumbs, .pankuzu, #breadcrumb, #breadcrumbs, '
        '.menu, #menu, .nav, .global-nav, .gnav, .sidebar, #sidebar'
    ):
        sel.decompose()
    title = ''
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    main = (
        soup.find('main')
        or soup.find(id=re.compile(r'main|content', re.I))
        or soup.find(class_=re.compile(r'main|content|article', re.I))
        or soup.find('article')
        or soup.body
        or soup
    )
    paragraphs = []
    if main:
        for el in main.find_all(['p', 'div', 'li', 'blockquote', 'section']):
            if el.find(['p', 'blockquote']) and el.name == 'div':
                continue
            t = el.get_text(separator=' ', strip=True)
            if not t:
                continue
            t = re.sub(r'\s+', ' ', t).strip()
            if t:
                paragraphs.append(t)
    full_text = main.get_text(separator='\n', strip=True) if main else ''
    return title, full_text, paragraphs


def is_quotable_parent(p, page_dedicated, page_is_parent_voice=False):
    """保護者向け段落として抽出できるか判定

    page_is_parent_voice: True のとき、ページタイトル等から「保護者メッセージ」
    のセクションだと判明している場合。アンカー語が無くても採用する。
    """
    if len(p) < 50 or len(p) > 600:
        return False
    pl = p.lower()
    for n in NEGATIVE_HINTS:
        if n.lower() in pl:
            return False
    for n in EVENT_NEGATIVE:
        if n in p:
            # 専用ページなら「説明会」言及自体は許容（PTA総会の告知など）するが
            # 開催中/受付中/申し込みの強い告知は除外
            if not page_dedicated:
                return False
            if any(strong in p for strong in ['お申し込み', '申し込みフォーム', '受付中', '開催中']):
                return False
    if p.count('|') >= 3 or p.count('・') >= 8:
        return False
    if p.count('>') >= 2:
        return False
    if len(re.findall(r'\d{4}[\.\-/年]\d{1,2}', p)) >= 2:
        return False
    if re.match(r'^[\s\d年月日.\-/]{6,20}', p):
        return False
    if '404' in p or 'not found' in pl or 'お探しのページ' in p:
        return False
    if p.count('　') >= 4:
        return False
    # 「お知らせ」「ニュース」リスト形式
    if 'お知らせ' in p[:20] and re.search(r'\d{4}/\d{1,2}/\d{1,2}', p):
        return False
    # メニュー羅列: 連続スペース区切り or 多数の見出し
    if p.count(' ') / max(1, len(p)) > 0.15:
        return False
    # 見出し的な短文連結（句点ほぼなしで全角スペース多用）
    headings_count = len(re.findall(r'POLICY|学園案内|学園概要|建学の精神|沿革|学校紹介|トップ', p))
    if headings_count >= 3:
        return False
    jp_chars = sum(1 for c in p if '぀' <= c <= '鿿')
    if jp_chars < len(p) * 0.4:
        return False
    punct = p.count('、') + p.count('。') + p.count('，')
    if len(p) >= 80 and punct < 2:
        return False
    if '。' not in p and '！' not in p and '？' not in p and '」' not in p:
        return False
    # 必須: 保護者・PTA系のアンカー語が含まれていること
    # ただし page_is_parent_voice=True (ページタイトルが「保護者メッセージ」等) なら
    # 個別段落にアンカー語が無くても OK（親自身の体験談の引用が想定されるため）
    if not page_is_parent_voice and not any(a in p for a in PARENT_ANCHORS):
        return False
    # page_is_parent_voice の場合、自己紹介や保護者メッセージとして
    # 「娘」「息子」「子ども」「我が家」「親」などの親視点の語が必要
    if page_is_parent_voice and not any(a in p for a in PARENT_ANCHORS):
        parent_voice_signals = ['娘', '息子', 'うちの子', '我が家', '親として',
                                '母', '父', '入学', '卒業', '本校', '貴校',
                                '感謝', '成長']
        # 親視点の語が2つ以上必要
        if sum(1 for s in parent_voice_signals if s in p) < 2:
            return False
    # secondary ページの場合は、以下のいずれかを満たす必要あり:
    # (A) 強アンカー (PTA/保護者会/父母会/後援会/育友会/保護者の声) 含む
    # (B) 「保護者の皆様/方々」等の呼びかけ + 教育的内容（学校から保護者へのメッセージ）
    strong_parent_anchors = [
        'PTA', '保護者会', '父母会', '父母の会',
        '後援会', '育友会', '保護者の声',
        '保護者の方々', '保護者の皆様', '保護者のみなさま',
        '保護者の皆さま', 'ご家庭との連携', '家庭との連携',
        '家庭と学校', '学校と家庭', '家庭の協力',
    ]
    if not page_dedicated:
        if not any(a in p for a in strong_parent_anchors):
            return False
        # 入試・出願・受験系の告知文は除外（PTA等強アンカーがあれば許容）
        admission_kws = [
            '受験生', '入試', '出願', '入学試験',
            '受験番号', '合格発表', '合否', '受験票',
        ]
        admission_hits = sum(1 for k in admission_kws if k in p)
        org_anchors = ['PTA', '保護者会', '父母会', '後援会', '育友会']
        if admission_hits >= 1 and not any(a in p for a in org_anchors):
            return False
        # トリップレポート系（修学旅行・ホームステイ）は除外
        trip_kws = [
            'ホストファミリー', 'ホームステイ', 'お別れ会', 'farewell',
            'ブリスベン', '現地校', '現地の生徒', 'group 1',
        ]
        if any(k.lower() in p.lower() for k in trip_kws):
            return False
        # 「お弁当」など日常生活レポート
        if 'お弁当' in p and not any(a in p for a in org_anchors):
            return False
    return True


def detect_subrole(p):
    """段落内容から具体的サブカテゴリを推定 (DB上の speaker_role は parent)"""
    if 'PTA' in p:
        return 'PTA'
    if '後援会' in p:
        return '後援会'
    if '父母会' in p or '父母の会' in p:
        return '父母会'
    if '育友会' in p:
        return '育友会'
    if '保護者会' in p:
        return '保護者会'
    return '保護者'


def score_paragraph(p, page_dedicated):
    s = 0
    if page_dedicated:
        s += 4
    for kw in PARENT_ANCHORS:
        if kw in p:
            s += 2
    for kw in ['本校', '私たち', '生徒', '教育', '人材', '心', '夢', '未来',
               '活動', '支援', '協力']:
        if kw in p:
            s += 1
    if p.endswith(('。', '」')):
        s += 1
    if 80 <= len(p) <= 350:
        s += 2
    return s


def trim_quote(p, max_len=380):
    """引用 < 400字 を保証（余裕をもたせて 380 字でカット）"""
    if len(p) <= max_len:
        return p
    cut = p[:max_len]
    last = max(cut.rfind('。'), cut.rfind('！'), cut.rfind('？'))
    if last > 60:
        return cut[:last + 1]
    return cut + '…'


def make_summary(quote):
    s = quote.replace('\n', ' ').strip()
    if len(s) <= 50:
        return s
    head = s[:50]
    last = max(head.rfind('、'), head.rfind('。'))
    if last > 20:
        return head[:last] + '…'
    return head + '…'


def context_label_for(page_name):
    return {
        'parent': '保護者向けページ',
        'pta': 'PTA・保護者会ページ',
        'voice': '在校生・保護者の声ページ',
        'schoollife': '学校生活ページ',
        'events': '行事案内ページ',
        'about': '学校紹介ページ',
        'admission': '入試・募集案内ページ',
        'root': 'トップページ',
    }.get(page_name, '保護者向けページ')


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)

    url_map, url_fallback = get_url_map()

    school_dirs = sorted([
        d for d in CACHE.iterdir()
        if d.is_dir() and d.name.startswith('jpms_s_')
    ])
    print(f"[Team B-5] schools in cache: {len(school_dirs)}")

    items = []
    completed = 0
    schools_with_parent_quote = 0
    schools_attempted = 0

    for sd in school_dirs:
        sid = sd.name
        completed += 1

        # 取得試行: dedicated と secondary
        dedicated_files = []
        for pp in PARENT_DEDICATED:
            f = sd / f'{pp}.html'
            if f.exists():
                dedicated_files.append((pp, f))
        secondary_files = []
        for pp in SECONDARY_PAGES:
            f = sd / f'{pp}.html'
            if f.exists():
                secondary_files.append((pp, f))

        if dedicated_files or secondary_files:
            schools_attempted += 1

        per_school = []
        seen_quotes = set()
        # まず dedicated、続いて secondary
        # dedicated ページは内容が豊富なため、1校あたり最大5件まで採用
        for page_name, fpath in dedicated_files + secondary_files:
            if len(per_school) >= 5:
                break
            try:
                html = read_html(fpath)
            except Exception:
                continue
            title, text, struct_paras = extract_paragraphs(html)
            # 学校外ページ排除
            non_school_indicators = [
                'researchmap', 'リサーチマップ', 'aguse', 'WHOIS',
                'お名前.com', 'このドメイン',
            ]
            if any(ind in title for ind in non_school_indicators):
                continue
            if any(ind in text[:1000] for ind in non_school_indicators):
                continue

            page_dedicated = page_name in PARENT_DEDICATED

            # ページタイトルから「保護者メッセージ」セクションか判定
            page_is_parent_voice = False
            title_lower = title.lower()
            voice_indicators = [
                '保護者メッセージ', '保護者の声', '保護者から', '父母の声',
                '保護者からのメッセージ', 'メッセージ集', 'voice from parents',
            ]
            if any(ind.lower() in title_lower for ind in voice_indicators):
                page_is_parent_voice = True
            # ページ冒頭にも見出しがある場合
            if any(ind in text[:200] for ind in ['保護者メッセージ', '保護者の声',
                                                   '保護者からのメッセージ',
                                                   '父母からのメッセージ']):
                page_is_parent_voice = True

            scored = []
            for p in struct_paras:
                if not is_quotable_parent(p, page_dedicated, page_is_parent_voice):
                    continue
                s = score_paragraph(p, page_dedicated)
                if page_is_parent_voice:
                    s += 2  # parent-voice ページの段落はスコア加算
                if s >= 4:
                    scored.append((s, p))
            if not scored:
                continue
            scored.sort(key=lambda x: -x[0])

            page_url = url_map.get((sid, page_name), '') or url_fallback.get(sid, '')
            ctx = context_label_for(page_name)

            for sc, para in scored:
                quote = trim_quote(para)
                if quote in seen_quotes:
                    continue
                if any(quote[:80] in q or q[:80] in quote for q in seen_quotes):
                    continue
                seen_quotes.add(quote)
                attr = detect_subrole(quote)
                rec = {
                    'school_id': sid,
                    'speaker_role': 'parent',
                    'speaker_attribute': attr,
                    'quote_text': quote,
                    'quote_summary': make_summary(quote),
                    'context': ctx,
                    'source_url': page_url,
                    'source_page': page_name,
                    'rights_level': 'quoted_with_attribution',
                }
                per_school.append(rec)
                if len(per_school) >= 5:
                    break

        if per_school:
            schools_with_parent_quote += 1
        items.extend(per_school)

    with open(OUT, 'w', encoding='utf-8') as f:
        for r in items:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    progress = {
        'task_id': 'team_b5',
        'completed': completed,
        'schools_attempted': schools_attempted,
        'schools_with_parent_quote': schools_with_parent_quote,
        'items': len(items),
        'ts': datetime.now().isoformat() + 'Z',
    }
    with open(PROGRESS, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"[Team B-5] processed schools: {completed}")
    print(f"[Team B-5] schools attempted (cache hits): {schools_attempted}")
    print(f"[Team B-5] schools with parent quote: {schools_with_parent_quote}")
    print(f"[Team B-5] total parent-voice items: {len(items)}")
    print(f"[Team B-5] output: {OUT}")
    print(f"[Team B-5] progress: {PROGRESS}")


if __name__ == '__main__':
    main()
