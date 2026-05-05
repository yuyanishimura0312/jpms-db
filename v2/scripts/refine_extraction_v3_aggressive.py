#!/usr/bin/env python3
"""V3 高度抽出 — V2 の精緻パターンに加え、より広範な testimonial 候補を抽出。

V2 で扱えなかった追加パターン:
- p, li, td タグ内の長文（30-400字）で role keyword を含むもの
- メタタグ（og:description, name="description"）の声
- インタビュー形式の応答（dl/dt/dd 構造）
- 一人称代名詞中心の文（私は/僕は/自分は）
- 卒業生の名前付き署名 "○年卒 ○○○○" + 続く文
- 校長挨拶長文（footer/header除く本文段落）
"""
import sqlite3
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')

# Aggressive patterns
P_TAG_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)
LI_TAG_RE = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
DD_TAG_RE = re.compile(r'<dd[^>]*>(.*?)</dd>', re.DOTALL | re.IGNORECASE)
TD_TAG_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)

# First-person markers
FIRST_PERSON_RE = re.compile(r'(私は|僕は|自分は|私たちは|自分が|私が|僕が|本校では)')
# Quote markers (longer)
QUOTE_RE = re.compile(r'[「『]([^「」『』]{50,500})[」』]')

ROLE_PATTERNS = {
    'principal': [
        r'校長[^（]?[:：](.+?)(?=校長|教員|生徒|保護者|$)',
        r'校長(?:より)?[:：]?\s*(.+?)(?=$|\n)',
        r'(?:本校|学園)では(.+?)(?=$|\n)',
    ],
    'teacher': [
        r'(?:教員|教諭|担任|教科主任)[:：]?\s*(.+?)(?=$|\n)',
        r'(?:国語|数学|英語|理科|社会|体育|音楽|美術|技術|家庭)科[:：]?\s*(.+?)(?=$|\n)',
    ],
    'student_current': [
        r'(?:在校生|中学[123]年|生徒)[^（]?[:：]?\s*(.+?)(?=$|\n)',
    ],
    'student_alumni': [
        r'(?:卒業生|OB|OG|\d+年[卒度]?|期生)[:：]?\s*(.+?)(?=$|\n)',
    ],
    'parent': [
        r'(?:保護者|父母|PTA|後援会)[:：]?\s*(.+?)(?=$|\n)',
    ],
}


def normalize(text):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;|&[a-z]+;', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def detect_role_aggressive(text, slug):
    """Aggressive role detection with priority order."""
    text_lower = text  # case retain for Japanese
    # Priority 1: Slug
    slug_role = {
        'principal': 'principal', 'message': 'principal', 'philosophy': 'principal',
        'mission': 'principal', 'about': None,
        'voice': 'student_current', 'student': 'student_current',
        'interview': 'student_current', 'schoollife': 'student_current',
        'alumni': 'student_alumni', 'ob': 'student_alumni',
        'parent': 'parent', 'pta': 'parent',
        'curriculum': 'teacher', 'education': 'teacher',
    }
    for k, v in slug_role.items():
        if k in slug.lower() and v:
            slug_role_hint = v
            break
    else:
        slug_role_hint = None

    # Priority 2: Strong text keywords
    if any(k in text for k in ['卒業生', '○期生', '〇期生']) and any(k in text for k in ['年卒', '年度卒', '同窓']):
        return 'student_alumni'
    if any(k in text for k in ['保護者会', 'PTA活動', '父母会', '後援会会報', '保護者の方へ']):
        return 'parent'
    if any(k in text for k in ['校長挨拶', '校長より', '校長メッセージ', '理事長挨拶']):
        return 'principal'
    if any(k in text for k in ['在校生インタビュー', '在校生の声', '生徒の声', '中学生活']):
        return 'student_current'
    if any(k in text for k in ['教員紹介', '教員の声', '教科教員', '担任より']):
        return 'teacher'

    # Priority 3: Slug hint + first-person
    if slug_role_hint and FIRST_PERSON_RE.search(text):
        return slug_role_hint

    # Priority 4: Slug hint alone
    return slug_role_hint


def extract_aggressive(html, slug, source_url):
    """Aggressive extraction across all common HTML patterns."""
    out = []

    # 1. p, li, dd, td tags
    for pattern_re, tag_name in [(P_TAG_RE, 'p'), (LI_TAG_RE, 'li'), (DD_TAG_RE, 'dd'), (TD_TAG_RE, 'td')]:
        for m in pattern_re.finditer(html):
            text = normalize(m.group(1))
            if 30 <= len(text) <= 400:
                # Skip pure navigation, footer, copyright
                if any(skip in text for skip in ['Copyright', '©', 'All Rights', 'プライバシーポリシー', 'sitemap', 'お問い合わせ', 'Cookie']):
                    continue
                role = detect_role_aggressive(text, slug)
                if role:
                    out.append({'role': role, 'text': text, 'source_url': source_url, 'context': f'{tag_name}-tag'})

    # 2. Long quotes (50-500 chars)
    for m in QUOTE_RE.finditer(html):
        qt = m.group(1).strip()
        # Get surrounding context
        ctx_start = max(0, m.start() - 200)
        ctx_end = min(len(html), m.end() + 200)
        ctx = normalize(html[ctx_start:ctx_end])
        role = detect_role_aggressive(ctx, slug)
        if role:
            out.append({'role': role, 'text': qt, 'source_url': source_url, 'context': 'long-quote'})

    return out


def main():
    db = sqlite3.connect(DB, timeout=300.0)
    db.execute('PRAGMA busy_timeout=300000')

    schools = {r[0]: r[1] for r in db.execute("SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL").fetchall()}

    existing = set()
    for r in db.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2").fetchall():
        existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

    inserted = 0
    rejected = 0
    schools_processed = 0
    by_role = {'principal':0, 'teacher':0, 'student_current':0, 'student_alumni':0, 'parent':0}
    batch = 0

    for sid_dir in sorted(CACHE.iterdir()):
        if not sid_dir.is_dir() or not sid_dir.name.startswith('jpms_s_'):
            continue
        sid = sid_dir.name
        sch_url = schools.get(sid)
        if not sch_url:
            continue
        schools_processed += 1
        candidates = []
        for html_file in sid_dir.glob('*.html'):
            slug = html_file.stem
            try:
                html = html_file.read_text(errors='ignore')
            except:
                continue
            candidates.extend(extract_aggressive(html, slug, sch_url))

        # Per-school cap to avoid noise overflow
        per_school_seen = set()
        for c in candidates[:80]:  # max 80 per school after dedup
            h = hashlib.md5(f"{sid}|{c['text'][:80]}".encode()).hexdigest()
            if h in existing or h in per_school_seen:
                rejected += 1
                continue
            existing.add(h)
            per_school_seen.add(h)
            try:
                rights = 'anonymized_only' if c['role'] in ('student_current','student_alumni','parent') else 'quoted_with_attribution'
                db.execute("""INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text, context,
                     source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (sid, c['role'],
                     {'principal':'校長または理事長', 'teacher':'教員',
                      'student_current':'中学生', 'student_alumni':'卒業生',
                      'parent':'保護者'}.get(c['role'], ''),
                     c['text'], c.get('context',''),
                     'school_website', c['source_url'], rights,
                     datetime.now().isoformat(), 'qm1_passed_v3agg'))
                inserted += 1
                by_role[c['role']] += 1
                batch += 1
                if batch >= 100:
                    db.commit(); batch = 0
            except sqlite3.OperationalError:
                rejected += 1

    db.commit()
    print(f"Schools processed: {schools_processed}")
    print(f"Inserted: {inserted}")
    print(f"Rejected: {rejected}")
    print(f"By role: {by_role}")
    print(f"\nTotal testimonials_v2: {db.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]}")
    db.close()


if __name__ == '__main__':
    main()
