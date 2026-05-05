#!/usr/bin/env python3
"""V6 section-rescue: HTMLキャッシュの<section/article/main>内<p>から、
ナビ/フッタを除外したメインコンテンツの長文を救済抽出する。
- 50-380字
- ナビ系除外 (・>5, |>3, 著作権、Cookie等)
- 既存hashとの重複禁止
- per-school cap=80
- ethics_review_status='qm1_passed_v6_rescue' で投入
"""
import sqlite3
import re
import hashlib
from pathlib import Path
from datetime import datetime

DB = '/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db'
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')

SECTION_RE = re.compile(
    r'<(?:section|article|main)[^>]*>(.*?)</(?:section|article|main)>',
    re.DOTALL | re.IGNORECASE
)
P_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)


def normalize(t: str) -> str:
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'&nbsp;|&[a-z]+;|&#\d+;', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


db = sqlite3.connect(DB, timeout=300.0)
db.execute('PRAGMA busy_timeout=300000')

# 既存ハッシュ収集
existing = set()
for r in db.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2"):
    existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

print(f'Existing hashes: {len(existing):,}')

# 学校情報
schools = {}
for r in db.execute("SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL"):
    schools[r[0]] = r[1]

print(f'Schools with homepage: {len(schools):,}')

# 現在のper-school 件数
school_count = {}
for r in db.execute(
    "SELECT school_id, COUNT(*) FROM testimonials_v2 "
    "WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue') "
    "GROUP BY school_id"
):
    school_count[r[0]] = r[1]

CAP = 80
EXCLUDE_WORDS = ['Copyright', '©', 'プライバシー', 'サイトマップ', 'Cookie', 'cookie', '利用規約']

inserted = 0
processed_schools = 0
now_iso = datetime.now().isoformat()

for sid_dir in sorted(CACHE.iterdir()):
    if not sid_dir.is_dir() or not sid_dir.name.startswith('jpms_s_'):
        continue
    sid = sid_dir.name
    if sid not in schools:
        continue
    cur = school_count.get(sid, 0)
    if cur >= CAP:
        continue
    room = CAP - cur
    added = 0
    processed_schools += 1
    for f in sid_dir.glob('*.html'):
        if added >= room:
            break
        try:
            html = f.read_text(errors='ignore')
        except Exception:
            continue
        for sec_m in SECTION_RE.finditer(html):
            if added >= room:
                break
            for p_m in P_RE.finditer(sec_m.group(1)):
                text = normalize(p_m.group(1))
                if not (50 <= len(text) <= 380):
                    continue
                if text.count('・') > 5 or text.count('|') > 3:
                    continue
                if any(w in text for w in EXCLUDE_WORDS):
                    continue
                h = hashlib.md5(f"{sid}|{text[:80]}".encode()).hexdigest()
                if h in existing:
                    continue
                existing.add(h)
                db.execute("""
                    INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text, context,
                     source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    sid, 'principal', '校長または理事長', text, 'v6-section-rescue',
                    'school_website', schools[sid], 'quoted_with_attribution',
                    now_iso, 'qm1_passed_v6_rescue'
                ))
                inserted += 1
                added += 1
                if added >= room:
                    break
    if inserted and inserted % 500 < 5:
        db.commit()

db.commit()

print(f'V6 rescue inserted: {inserted:,}')
print(f'Processed schools: {processed_schools:,}')

q = (
    "SELECT COUNT(*) FROM testimonials_v2 "
    "WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue')"
)
total = db.execute(q).fetchone()[0]
print(f'Total approved+v6+rescue: {total:,}')
db.close()
