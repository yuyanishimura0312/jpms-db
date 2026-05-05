#!/usr/bin/env python3
"""JPMS-DB v2 Phase E - Team B-1: 校長メッセージ抽出 (v2)"""
import os
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

BASE = Path('/Users/nishimura+/projects/research/jpms-db/v2')
CACHE = BASE / 'raw_html_cache'
DB = BASE / 'jpms_v2.db'
OUT = BASE / 'codex_output' / 'team_b1_principal.jsonl'
PROGRESS = BASE / 'codex_progress' / 'team_b1.json'

PAGE_PRIORITY = ['principal', 'philosophy', 'mission', 'about', 'voice', 'root',
                 'schoollife', 'curriculum']

PAGE_TITLE_KEYWORDS = [
    '校長', '理事長', '学園長', '挨拶', 'あいさつ', 'メッセージ', 'message',
    '学校長', '教育理念', '建学', '教育方針', '校訓', '理念',
    'ごあいさつ', 'ご挨拶', 'principal', 'message from', 'mission'
]

# 校長メッセージ性が高まるキーワード（段落内）
PRINCIPAL_STRONG = [
    '校長', '理事長', '学園長', '学校長',
    '建学の精神', '教育理念', '教育方針', '建学',
]

SPEAKER_HINTS = [
    '本校', '本学園', '本学院', '私たち', '私ども',
    '生徒', '児童', '皆さん', 'ご家庭', '保護者',
    'はぐくむ', '育てる', '育成', '人格', '人材', '社会に', '世界',
]

# 段落として弾くべきナビ・メタ系キーワード
NEGATIVE_HINTS = [
    'プライバシー', 'cookie', 'クッキー', '著作権', 'サイトマップ',
    'お問い合わせ', '個人情報保護', '採用情報', '会社概要',
    '利用規約', 'twitter', 'facebook', 'instagram', 'youtube',
    'all rights', 'copyright', '一覧へ', 'もっと見る', '詳しく見る',
    'メニュー', 'navigation', 'breadcrumb', 'ログイン',
    'メールアドレス', 'パスワード', 'ダウンロード',
    'ホーム>', 'TOP>',
    # イベント告知系
    '学校説明会', '説明会', '体験会', '体験入学', 'オープンスクール',
    '入試説明', '入試要項', 'お申し込み', '申し込みフォーム',
    '実施します', '開催します', '開催中', '受付中',
    '聖光祭', '体育祭', '文化祭',
    '受験生のみなさま', '受験生の方へ',
    # ニュース/お知らせリスト
    'お知らせ', 'ニュース', 'NEWS',
]

def get_url_map():
    """Returns: m[(sid, page)] = url, fallback[sid] = homepage_url"""
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

def extract_text_and_paragraphs(html):
    """タイトル, 全文テキスト, 構造的な段落リストを返す"""
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()
    for sel in soup.select('.breadcrumb, .breadcrumbs, .pankuzu, #breadcrumb, #breadcrumbs, .menu, #menu, .nav, .global-nav, .gnav, .sidebar, #sidebar'):
        sel.decompose()
    title = ''
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    main = soup.find('main') or soup.find(id=re.compile(r'main|content', re.I)) \
           or soup.find(class_=re.compile(r'main|content|article', re.I)) \
           or soup.find('article') or soup.body or soup

    # 構造的な段落: <p>, <div>(直下に文章), <li>(本文がある)
    paragraphs = []
    if main:
        for el in main.find_all(['p', 'div', 'li', 'blockquote', 'section']):
            # 子要素が同種ブロックなら親はスキップ（より具体的な子で取得する）
            if el.find(['p', 'blockquote']) and el.name == 'div':
                continue
            t = el.get_text(separator=' ', strip=True)
            if not t:
                continue
            # 改行混入を抑制
            t = re.sub(r'\s+', ' ', t).strip()
            if t:
                paragraphs.append(t)
    full_text = main.get_text(separator='\n', strip=True) if main else ''
    return title, full_text, paragraphs

def extract_text(html):
    title, text, _ = extract_text_and_paragraphs(html)
    return title, text

def looks_like_principal_page(title, text):
    head = (title + ' ' + text[:600]).lower()
    for kw in PAGE_TITLE_KEYWORDS:
        if kw.lower() in head:
            return True
    return False

def split_paragraphs(text):
    """改行区切りで段落候補を作る。"""
    raw = [p.strip() for p in re.split(r'\n+', text) if p.strip()]
    return raw

def clean_paragraph(p):
    """段落先頭のパンくず/見出しを取り除く"""
    # 「ホーム>○○>○○」を削除
    p = re.sub(r'^[^。]*?(ホーム|TOP|HOME)\s*[>＞»]\s*[^。]*?[>＞»]\s*[^。]*?(?=[一-龯ぁ-んァ-ヶ])', '', p)
    # 連続する「>」区切りの先頭ナビ
    p = re.sub(r'^[^。]{0,40}[>＞»][^。]{0,40}[>＞»][^。]{0,40}(?=[一-龯])', '', p)
    return p.strip()

def is_quotable(p):
    if len(p) < 60 or len(p) > 600:
        return False
    pl = p.lower()
    for n in NEGATIVE_HINTS:
        if n.lower() in pl:
            return False
    if p.count('|') >= 3 or p.count('・') >= 8:
        return False
    if p.count('>') >= 2:
        return False
    # 日付パターンが2つ以上、またはYYYY.MM.DD的な日付が含まれる→ニュース系
    if len(re.findall(r'\d{4}[\.\-/年]\d{1,2}', p)) >= 2:
        return False
    if re.search(r'20\d{2}[\.\-/年]\s?\d{1,2}[\.\-/月]', p):
        return False
    # イベント告知（年月日が文頭付近）
    if re.match(r'^[\s\d年月日.\-/]{6,20}', p):
        return False
    # 本校・私たちなど主語性のあるキーワード or 校長キーワードが入っていない場合は弱い
    has_personal = any(k in p for k in ['本校', '本学園', '本学院', '私たち', '私ども', '当校', '当学園',
                                          '創立', '建学', '教育', '校訓', '理念', '生徒', '児童', '学園',
                                          '校長', '理事長', '学園長', '人格', '人間', '育成', '育む', '心',
                                          '世界', '社会', '未来', '伝統', '精神'])
    if not has_personal:
        return False
    # 「メディア掲載」「掲載」のみの記事
    if 'メディア掲載' in p:
        return False
    # ニュース・実績文（生徒の活動報告など）
    news_indicators = ['成果報告会を実施', 'ベスト8', '優勝', '第1位', '第2位', '第3位', '入賞',
                       '出場決定', '出場しました', '大会において', '選手権',
                       '掲載されました', 'ご報告', '実施しました']
    if sum(1 for ind in news_indicators if ind in p) >= 1:
        return False
    # 卒業生の声 (個人の体験談)
    voice_indicators = ['学園生活を振り返', '高校時代', '思い出', '卒業生として',
                        '頂きました', '頂いた', '進学しましたが', '進路を選ぶ']
    if sum(1 for ind in voice_indicators if ind in p) >= 2:
        return False
    # 404
    if '404' in p or 'not found' in pl or 'お探しのページ' in p:
        return False
    # 「新年のご挨拶」「校長日記」などラベル連発
    if p.count('校長日記') >= 1 or p.count('新年のご挨拶') >= 2:
        return False
    # メニュー羅列っぽい（短いキーワードを「・」「、」で並べた段落）
    if p.count('　') >= 4:
        return False
    jp_chars = sum(1 for c in p if '぀' <= c <= '鿿')
    if jp_chars < len(p) * 0.4:
        return False
    # 句読点（読点+句点）比率が低い場合はメニュー羅列の可能性
    punct = p.count('、') + p.count('。') + p.count('，')
    if len(p) >= 80 and punct < 2:
        return False
    # 句点が1つもない＝本文ではなく見出し/メニュー
    if '。' not in p and '！' not in p and '？' not in p:
        return False
    return True

def score_paragraph(p, page_is_principal):
    s = 0
    if page_is_principal:
        s += 4
    for kw in PRINCIPAL_STRONG:
        if kw in p:
            s += 3
    for kw in ['本校', '私たち', '生徒', '教育', '人材', '人格', '心', '夢', '未来']:
        if kw in p:
            s += 1
    if p.endswith(('。', '」')):
        s += 1
    if 80 <= len(p) <= 350:
        s += 2
    return s

def trim_quote(p, max_len=290):
    if len(p) <= max_len:
        return p
    cut = p[:max_len]
    last = max(cut.rfind('。'), cut.rfind('！'), cut.rfind('？'))
    if last > 50:
        return cut[:last+1]
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

def detect_speaker_role(title, text_head):
    h = title + ' ' + text_head[:400]
    if '理事長' in h:
        return 'chairperson'
    if '学園長' in h:
        return 'school_director'
    return 'principal'

def role_attribute(role, title):
    if role == 'chairperson':
        return '理事長'
    if role == 'school_director':
        return '学園長'
    if '学校長' in title:
        return '学校長'
    return '校長'

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)

    url_map, url_fallback = get_url_map()

    school_dirs = sorted([d for d in CACHE.iterdir() if d.is_dir() and d.name.startswith('jpms_s_')])
    print(f"[Team B-1] schools: {len(school_dirs)}")

    items = []
    completed = 0

    for sd in school_dirs:
        sid = sd.name
        candidates = []
        for pp in PAGE_PRIORITY:
            f = sd / f'{pp}.html'
            if f.exists():
                candidates.append((pp, f))

        per_school = []
        seen_quotes = set()
        for page_name, fpath in candidates:
            if len(per_school) >= 3:
                break
            try:
                html = fpath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            title, text, struct_paragraphs = extract_text_and_paragraphs(html)
            # 学校外のページ(誤フェッチ)を除外
            non_school_indicators = [
                'ローイング協会', 'researchmap', 'リサーチマップ',
                'ドメイン', 'お名前.com', 'aguse', 'サクラインターネット',
                'WHOIS', 'このページは', 'このドメイン',
            ]
            if any(ind in title for ind in non_school_indicators):
                continue
            if any(ind in text[:1000] for ind in non_school_indicators):
                continue
            page_is_principal = looks_like_principal_page(title, text)

            if page_name in ('principal', 'philosophy', 'mission'):
                page_is_principal = True

            if not page_is_principal and page_name in ('root', 'voice', 'schoollife', 'curriculum'):
                hits = sum(1 for k in PRINCIPAL_STRONG if k in text[:5000])
                # SPA/JSページなど本文が極端に短い場合はスキップ
                if hits < 1 and len(text) < 1500:
                    continue

            # 構造的段落 + 改行段落の両方を候補に
            paragraphs = list(dict.fromkeys(struct_paragraphs + split_paragraphs(text)))
            scored = []
            for p in paragraphs:
                p = clean_paragraph(p)
                if not is_quotable(p):
                    continue
                s = score_paragraph(p, page_is_principal)
                if s >= 3:
                    scored.append((s, p))
            if not scored:
                continue
            scored.sort(key=lambda x: -x[0])

            role = detect_speaker_role(title, text)
            attr = role_attribute(role, title)
            page_url = url_map.get((sid, page_name), '')
            if not page_url:
                page_url = url_fallback.get(sid, '')
            context_label = {
                'principal': '校長メッセージページ',
                'philosophy': '教育理念ページ',
                'mission': 'ミッション/教育方針ページ',
                'about': '学校紹介ページ（校長挨拶）',
                'voice': 'メッセージページ',
                'root': 'トップページ（校長挨拶）',
                'schoollife': '学校生活ページ（校長挨拶）',
                'curriculum': 'カリキュラムページ（校長挨拶）',
            }.get(page_name, '校長メッセージページ')

            for sc, para in scored:
                quote = trim_quote(para)
                if quote in seen_quotes:
                    continue
                # 既存と前方一致重複もスキップ
                if any(quote[:80] in q or q[:80] in quote for q in seen_quotes):
                    continue
                seen_quotes.add(quote)
                rec = {
                    'school_id': sid,
                    'speaker_role': role,
                    'speaker_attribute': attr,
                    'quote_text': quote,
                    'quote_summary': make_summary(quote),
                    'context': context_label,
                    'source_url': page_url,
                    'rights_level': 'quoted_with_attribution',
                }
                per_school.append(rec)
                if len(per_school) >= 3:
                    break

        items.extend(per_school)
        completed += 1

    with open(OUT, 'w', encoding='utf-8') as f:
        for r in items:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    progress = {
        'task_id': 'team_b1',
        'completed': completed,
        'items': len(items),
        'ts': datetime.now().isoformat() + 'Z',
    }
    with open(PROGRESS, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    schools_covered = len(set(r['school_id'] for r in items))
    print(f"[Team B-1] processed schools: {completed}")
    print(f"[Team B-1] schools covered: {schools_covered}")
    print(f"[Team B-1] total quotes: {len(items)}")
    print(f"[Team B-1] output: {OUT}")
    print(f"[Team B-1] progress: {PROGRESS}")

if __name__ == '__main__':
    main()
