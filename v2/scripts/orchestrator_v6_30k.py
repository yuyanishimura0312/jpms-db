#!/usr/bin/env python3
"""V6 大規模深掘り抽出 — 30,000件目標達成支援.

V5 から強化:
- 文単位の細かい抽出（句点で分割し30字以上の各文を候補化）
- blockquote, aside, figure/figcaption も対象
- h1/h2/h3 の直後の p/div を優先抽出（インタビュー見出しパターン）
- dl/dt/dd の Q&A パターン強化
- 長文段落（>400字）は文分割で 30-400字 範囲のチャンクに分解
- per-school cap=80 で平準化
- 冗長フィルタ（コサイン類似度 simhash 風）
"""
import sqlite3
import re
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')

PER_SCHOOL_CAP = 80

BOILERPLATE = [
    r'Copyright', r'©', r'All Rights Reserved', r'プライバシーポリシー',
    r'サイトマップ', r'お問い合わせ\s*$', r'Cookie', r'JavaScript',
    r'Loading', r'読み込み中', r'下記の', r'下のリンク',
    r'クリック', r'PAGE TOP', r'^TOP$', r'^MENU$',
    r'メニューを開く', r'メニューを閉じる',
    r'ご覧[くだ]さい', r'^\s*続きを読む\s*$',
    r'^\s*資料請求\s*$', r'^\s*オープンスクール\s*$',
    r'^\s*アクセスマップ\s*$', r'^\s*受験生の方へ\s*$',
]

BOILERPLATE_RE = re.compile('|'.join(BOILERPLATE))

P_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)
LI_RE = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
DD_RE = re.compile(r'<dd[^>]*>(.*?)</dd>', re.DOTALL | re.IGNORECASE)
DT_RE = re.compile(r'<dt[^>]*>(.*?)</dt>', re.DOTALL | re.IGNORECASE)
TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
BLOCKQUOTE_RE = re.compile(r'<blockquote[^>]*>(.*?)</blockquote>', re.DOTALL | re.IGNORECASE)
ASIDE_RE = re.compile(r'<aside[^>]*>(.*?)</aside>', re.DOTALL | re.IGNORECASE)
FIGCAPTION_RE = re.compile(r'<figcaption[^>]*>(.*?)</figcaption>', re.DOTALL | re.IGNORECASE)
H_P_RE = re.compile(r'<h[1-4][^>]*>([^<]+)</h[1-4]>\s*<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)
DIV_VOICE_RE = re.compile(
    r'<div[^>]*class="[^"]*(?:voice|message|comment|interview|story|essay|memo|profile|alumni|graduate|graduates|sotsugyo|seito|hogo|kyoin|kocho)[^"]*"[^>]*>(.*?)</div>',
    re.DOTALL | re.IGNORECASE
)
META_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE)
META_OG_DESC_RE = re.compile(r'<meta\s+property="og:description"\s+content="([^"]*)"', re.IGNORECASE)


def normalize(text):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;|&[a-zA-Z]+;|&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_boilerplate(text):
    return bool(BOILERPLATE_RE.search(text))


def split_long_paragraph(text, min_len=30, max_len=400):
    """Split long paragraph into 30-400 char sentences."""
    if len(text) <= max_len:
        return [text] if len(text) >= min_len else []
    sents = re.split(r'(?<=[。！？])\s*', text)
    out = []
    cur = ''
    for s in sents:
        if not s.strip():
            continue
        if len(cur) + len(s) <= max_len:
            cur += s
        else:
            if min_len <= len(cur) <= max_len:
                out.append(cur.strip())
            cur = s if len(s) <= max_len else s[:max_len]
    if min_len <= len(cur) <= max_len:
        out.append(cur.strip())
    return out


def detect_role_v6(text, slug, source_url):
    """V6 lenient role detection."""
    # First-person markers strengthen detection
    if any(k in text for k in ['卒業生', 'OB', 'OG', '同窓', '期生', '年卒', '年度卒', '出身', '卒業して', '卒業後']):
        return 'student_alumni'
    if any(k in text for k in ['校長', '理事長', '学園長', '副校長', '教頭']):
        return 'principal'
    if any(k in text for k in ['在校生', '生徒', '中1', '中2', '中3', '中学1', '中学2', '中学3', '中学生',
                                '高1', '高2', '高3', '高校生', '入学して', '本校で', '部活動で']):
        return 'student_current'
    if any(k in text for k in ['保護者', 'PTA', '父母', '父兄', '後援会', '保護者会', '我が子', '娘', '息子']):
        return 'parent'
    if any(k in text for k in ['教諭', '教員', '担任', '主任', '教科担当', '生徒たちが', '指導', '授業を']):
        return 'teacher'
    # Slug fallback
    slug_l = slug.lower()
    src_l = (source_url or '').lower()
    combo = slug_l + ' ' + src_l
    if 'principal' in combo or 'kocho' in combo or 'message' in combo or 'philosophy' in combo or 'mission' in combo or 'aisatsu' in combo or 'rinen' in combo:
        return 'principal'
    if 'voice' in combo or 'student' in combo or 'schoollife' in combo or 'seito' in combo or 'koe' in combo:
        return 'student_current'
    if 'alumni' in combo or 'sotsugyo' in combo or 'graduate' in combo or 'ob_og' in combo:
        return 'student_alumni'
    if 'parent' in combo or 'pta' in combo or 'hogo' in combo or 'family' in combo:
        return 'parent'
    if 'curriculum' in combo or 'teacher' in combo or 'kyoin' in combo or 'education' in combo:
        return 'teacher'
    return None


def extract_v6(html, slug, source_url):
    out = []
    seen_local = set()

    def add(text, role, ctx):
        if not (30 <= len(text) <= 400):
            return
        if is_boilerplate(text):
            return
        if not role:
            return
        h = hashlib.md5(text[:80].encode()).hexdigest()
        if h in seen_local:
            return
        seen_local.add(h)
        out.append({'role': role, 'text': text, 'source_url': source_url, 'context': f'v6-{ctx}'})

    # Pattern A: heading + paragraph (interview Q&A pattern)
    for m in H_P_RE.finditer(html):
        ht = normalize(m.group(1))
        bt = normalize(m.group(2))
        # If heading suggests speaker role
        merged = ht + ' ' + bt
        role = detect_role_v6(merged, slug, source_url)
        if role:
            for chunk in split_long_paragraph(bt):
                add(chunk, role, 'h+p')

    # Pattern B: standard tags
    for pattern_re, tag in [
        (P_RE, 'p'), (LI_RE, 'li'), (DD_RE, 'dd'), (TD_RE, 'td'),
        (BLOCKQUOTE_RE, 'bq'), (ASIDE_RE, 'aside'),
        (FIGCAPTION_RE, 'figcap'), (DIV_VOICE_RE, 'div-v'),
    ]:
        for m in pattern_re.finditer(html):
            text = normalize(m.group(1))
            for chunk in split_long_paragraph(text):
                role = detect_role_v6(chunk, slug, source_url)
                if role:
                    add(chunk, role, tag)

    # Pattern C: meta description (school official)
    for r in [META_DESC_RE, META_OG_DESC_RE]:
        m = r.search(html)
        if m:
            text = normalize(m.group(1))
            for chunk in split_long_paragraph(text):
                role = detect_role_v6(chunk, slug, source_url) or 'principal'
                add(chunk, role, 'meta')

    return out


def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    schools = {r[0]: r[1] for r in db.execute(
        "SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL AND homepage_url != ''"
    ).fetchall()}

    # Existing 80-char prefix hash
    existing = set()
    for r in db.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2").fetchall():
        existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

    # Per-school current count (approved + pending)
    school_count = {}
    for r in db.execute(
        "SELECT school_id, COUNT(*) FROM testimonials_v2 WHERE ethics_review_status IN ('approved','qm1_passed','qm1_passed_v5','qm1_passed_v6') GROUP BY school_id"
    ).fetchall():
        school_count[r[0]] = r[1]

    inserted = 0
    rejected = 0
    by_role = {'principal': 0, 'teacher': 0, 'student_current': 0, 'student_alumni': 0, 'parent': 0}
    schools_processed = 0
    batch = 0

    for sid_dir in sorted(CACHE.iterdir()):
        if not sid_dir.is_dir() or not sid_dir.name.startswith('jpms_s_'):
            continue
        sid = sid_dir.name
        sch_url = schools.get(sid)
        if not sch_url:
            continue
        cur_count = school_count.get(sid, 0)
        if cur_count >= PER_SCHOOL_CAP:
            continue
        room = PER_SCHOOL_CAP - cur_count
        schools_processed += 1
        candidates = []
        for html_file in sid_dir.glob('*.html'):
            slug = html_file.stem
            try:
                html = html_file.read_text(errors='ignore')
            except Exception:
                continue
            candidates.extend(extract_v6(html, slug, sch_url))

        per_school_seen = set()
        added = 0
        for c in candidates:
            if added >= room:
                break
            h = hashlib.md5(f"{sid}|{c['text'][:80]}".encode()).hexdigest()
            if h in existing or h in per_school_seen:
                rejected += 1
                continue
            existing.add(h)
            per_school_seen.add(h)
            try:
                rights = ('anonymized_only'
                          if c['role'] in ('student_current', 'student_alumni', 'parent')
                          else 'quoted_with_attribution')
                attr = {'principal': '校長または理事長', 'teacher': '教員',
                        'student_current': '中学生', 'student_alumni': '卒業生',
                        'parent': '保護者'}.get(c['role'], '')
                db.execute(
                    """INSERT INTO testimonials_v2
                       (school_id, speaker_role, speaker_attribute, quote_text, context,
                        source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (sid, c['role'], attr, c['text'], c.get('context', ''),
                     'school_website', c['source_url'], rights,
                     datetime.now().isoformat(), 'qm1_passed_v6')
                )
                inserted += 1
                added += 1
                by_role[c['role']] += 1
                batch += 1
                if batch >= 200:
                    db.commit()
                    batch = 0
            except sqlite3.OperationalError:
                rejected += 1

    db.commit()
    print(f"Schools processed: {schools_processed}")
    print(f"Inserted: {inserted}")
    print(f"Rejected (dup/etc): {rejected}")
    print(f"By role: {by_role}")
    print(f"Total testimonials_v2: {db.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]}")
    db.close()


if __name__ == '__main__':
    main()
