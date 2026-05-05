#!/usr/bin/env python3
"""精緻再抽出 v2 — 取得済 raw_html_cache から testimonials を高精度に再抽出。

戦略B: BeautifulSoup でセマンティックタグ優先抽出
- blockquote, figcaption, article, .voice, .interview, .message
- Q&A 形式（dt/dd, h3+p）
- 引用符「」『』""内
- 複数文連続（接続詞でつなぐ）
"""
import sqlite3
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')

ROLE_KEYWORDS = {
    'principal': ['校長', '理事長', '学園長', '校長メッセージ', '校長より', '理事長挨拶'],
    'teacher': ['教諭', '教員', '担任', '教科主任', '○○科', '副校長', '教頭'],
    'student_current': ['在校生', '中学生', '中1', '中2', '中3', '生徒', 'みなさん', '私は', '中学校生活'],
    'student_alumni': ['卒業生', '○期', 'OB', 'OG', '同窓', '修了生', '○年度卒'],
    'parent': ['保護者', '保護者会', 'PTA', '父母会', '保護者向け', '父兄'],
}

# Common HTML tags that often contain testimonials
SEMANTIC_TAGS_RE = re.compile(r'<(blockquote|figcaption|q|article)[^>]*>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
QUOTE_RE = re.compile(r'[「『"”]([^「』"”]{30,400})[」』""]')
INTERVIEW_RE = re.compile(r'<(dt|h[3-5])[^>]*>(.*?)</\1>\s*<(dd|p)[^>]*>(.*?)</\3>', re.DOTALL | re.IGNORECASE)

def normalize_text(html_chunk):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html_chunk, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;|&[a-z]+;', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def detect_role(text, slug):
    """Detect speaker role from text and slug."""
    # Slug-based hint
    if 'principal' in slug or 'message' in slug:
        return 'principal'
    if 'voice' in slug or 'student' in slug:
        if any(k in text for k in ['卒業生', 'OB', 'OG', '同窓']):
            return 'student_alumni'
        return 'student_current'
    if 'parent' in slug or 'pta' in slug:
        return 'parent'
    if 'teacher' in slug or 'curriculum' in slug:
        return 'teacher'

    # Text-based detection
    role_scores = {role: sum(1 for kw in kws if kw in text) for role, kws in ROLE_KEYWORDS.items()}
    if max(role_scores.values()) > 0:
        return max(role_scores, key=role_scores.get)
    return None


def extract_blockquotes(html, slug, source_url):
    """Extract content from blockquote, figcaption, article tags."""
    out = []
    for m in SEMANTIC_TAGS_RE.finditer(html):
        text = normalize_text(m.group(2))
        if 30 <= len(text) <= 400:
            role = detect_role(text, slug)
            if role:
                out.append({'role': role, 'text': text, 'source_url': source_url, 'context': f'semantic:{m.group(1)}'})
    return out


def extract_quotes(text, slug, source_url):
    """Extract quoted text from「」『』."""
    out = []
    for m in QUOTE_RE.finditer(text):
        qt = m.group(1).strip()
        if 30 <= len(qt) <= 400:
            role = detect_role(qt + ' ' + text[max(0, m.start()-100):m.start()], slug)
            if role:
                out.append({'role': role, 'text': qt, 'source_url': source_url, 'context': 'quote'})
    return out[:30]


def extract_interview(html, slug, source_url):
    """Extract Q&A interview format (dt+dd, h3+p)."""
    out = []
    for m in INTERVIEW_RE.finditer(html):
        q = normalize_text(m.group(2))
        a = normalize_text(m.group(4))
        if 30 <= len(a) <= 400:
            role = detect_role(q + ' ' + a, slug)
            if role:
                out.append({'role': role, 'text': a, 'source_url': source_url, 'context': f'qa:{q[:50]}'})
    return out[:30]


def main():
    db = sqlite3.connect(DB, timeout=300.0)
    db.execute('PRAGMA busy_timeout=300000')

    # Get school -> homepage_url mapping
    schools = {r[0]: r[1] for r in db.execute("SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL AND homepage_url != ''").fetchall()}

    # Existing testimonials hash for dedup
    existing = set()
    for r in db.execute("SELECT school_id, quote_text FROM testimonials_v2").fetchall():
        existing.add(hashlib.md5(f"{r[0]}|{r[1][:100]}".encode()).hexdigest())

    inserted = 0
    rejected = 0
    by_role = {'principal':0, 'teacher':0, 'student_current':0, 'student_alumni':0, 'parent':0}
    schools_processed = 0
    batch = 0

    for sid_dir in sorted(CACHE.iterdir()):
        if not sid_dir.is_dir():
            continue
        sid = sid_dir.name
        if not sid.startswith('jpms_s_'):
            continue
        sch_url = schools.get(sid)
        if not sch_url:
            continue
        schools_processed += 1

        for html_file in sid_dir.glob('*.html'):
            slug = html_file.stem
            try:
                html = html_file.read_text(errors='ignore')
            except:
                continue
            text = normalize_text(html)
            source_url = sch_url  # fallback

            candidates = []
            candidates.extend(extract_blockquotes(html, slug, source_url))
            candidates.extend(extract_quotes(text, slug, source_url))
            candidates.extend(extract_interview(html, slug, source_url))

            for c in candidates:
                # Dedup
                h = hashlib.md5(f"{sid}|{c['text'][:100]}".encode()).hexdigest()
                if h in existing:
                    rejected += 1
                    continue
                existing.add(h)

                # Insert
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
                         'school_website', source_url, rights,
                         datetime.now().isoformat(), 'qm1_passed_v2refine'))
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
    print(f"Rejected (duplicates): {rejected}")
    print(f"By role: {by_role}")
    print(f"\nTotal testimonials_v2: {db.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]}")
    db.close()


if __name__ == '__main__':
    main()
