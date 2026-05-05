#!/usr/bin/env python3
"""
JPMS-DB v2 testimonials_v2 enrichment from external Miratuku DBs.

Pulls educational news/article excerpts from PE DB (PESTLE) and FK DB (Foresight),
matches against private junior-high school names, and inserts as testimonials with
ethics_review_status='qm1_passed_external'.

Constraints:
- 30-400 char quote_text
- school_id strict match (>=4 char short name unique-ish)
- duplicate guard via md5(school_id|quote_text[:80])
- per-school cap to avoid concentration
"""
import os
import re
import sqlite3
import hashlib
from datetime import datetime

JPMS_DB = '/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db'
PE_DB   = '/Users/nishimura+/projects/research/pestle-signal-db/data/pestle.db'
FK_DB   = '/Users/nishimura+/projects/research/foresight-knowledge-base/foresight.db'

# Per-school cap (avoid biasing towards a few famous schools)
PER_SCHOOL_CAP = 80
MIN_LEN = 30
MAX_LEN = 400

# Generic words that should never be used as a school short-name (false-positive guard)
STOPWORDS = {
    '日本', '中央', '東京', '大阪', '京都', '神戸', '横浜', '名古屋',
    '附属', '中等', '中学', '高校', '高等', '学園', '学院', '中学校',
    '聖学', '聖学院', '城北', '城西', '城東', '城南',  # too short / too common alone
    '関西', '関東', '九州', '東北', '北海', '四国',
    '青山', '麻布', '渋谷',  # too generic; allow only with full match
    '清風', '明星', '明治', '昭和', '平成', '帝京',
    '聖光', '光塩', '光英',
    '自由', '共立', '共愛', '相愛',
}

# Names where short-form is a regular word - require full name_ja match
# (handled by length filter and stopwords)


def normalize_short_name(name_ja: str) -> str:
    """Strip common suffixes/prefixes to get a discriminative short name."""
    s = name_ja
    # remove trailing common school-type tokens
    for suf in ['中学校', '中学', '中等部', '中等教育学校',
                '高等学校附属中学校', '高等学校附属', '附属中学校', '附属',
                '中・高等学校', '高等部']:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    s = s.strip()
    return s


def build_school_index(db: sqlite3.Connection):
    schools_short = {}   # short_name -> [(sid, full_name)]
    schools_full = {}    # full_name -> sid
    rows = db.execute('SELECT id, name_ja FROM schools_v2').fetchall()
    for sid, name in rows:
        if not name:
            continue
        schools_full[name] = sid
        sn = normalize_short_name(name)
        if len(sn) < 4:
            continue
        if sn in STOPWORDS:
            continue
        schools_short.setdefault(sn, []).append((sid, name))
    return schools_short, schools_full


def get_school_counts(db: sqlite3.Connection):
    counts = {}
    rows = db.execute(
        "SELECT school_id, COUNT(*) FROM testimonials_v2 "
        "WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue','qm1_passed_v7','qm1_passed_external') "
        "GROUP BY school_id"
    ).fetchall()
    for sid, c in rows:
        counts[sid] = c
    return counts


def build_existing_hashes(db: sqlite3.Connection):
    hashes = set()
    for sid, qt in db.execute('SELECT school_id, quote_text FROM testimonials_v2'):
        if qt is None:
            continue
        hashes.add(hashlib.md5(f'{sid}|{qt[:80]}'.encode()).hexdigest())
    return hashes


def clean_text(t: str) -> str:
    if t is None:
        return ''
    # collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    # strip "|" trailing junk often present in the PE DB
    t = t.split('|')[0].strip() if '|' in t and len(t.split('|')[0]) > 50 else t
    return t


def match_school(text: str, schools_short, schools_full):
    """Return (sid, full_name, matched_str) or None.
    Prefer full_name match, then short_name with disambiguation."""
    if not text:
        return None
    # Pass 1: full-name exact substring (most reliable)
    for full_name, sid in schools_full.items():
        if full_name in text:
            return (sid, full_name, full_name)
    # Pass 2: short-name match, only if unique
    for sn, lst in schools_short.items():
        if sn in text and len(lst) == 1:
            sid, full_name = lst[0]
            return (sid, full_name, sn)
    return None


def extract_pe(jpms_db, schools_short, schools_full, school_count, existing_hashes):
    if not os.path.exists(PE_DB):
        print('PE DB not found, skip')
        return 0
    print('=== PE DB extraction ===')
    pe = sqlite3.connect(PE_DB)
    inserted = 0
    skipped_cap = 0
    skipped_dup = 0
    skipped_len = 0

    rows = pe.execute(
        """SELECT title, title_ja, summary, url, published_date, source
           FROM articles
           WHERE lang='ja' AND pestle_category IN ('Social','Political')
           AND (title LIKE '%中学%' OR title LIKE '%学園%' OR title LIKE '%学院%'
                OR title LIKE '%中等%' OR summary LIKE '%中学%' OR summary LIKE '%学園%'
                OR summary LIKE '%学院%' OR summary LIKE '%中等%')
        """
    ).fetchall()
    print(f'PE candidate articles: {len(rows)}')

    for title, title_ja, summary, url, pub, source in rows:
        # Pick the searchable & quotable text body
        body = clean_text(summary) or clean_text(title_ja) or clean_text(title)
        if not body:
            continue
        # Find school in title or summary (title preferred for precision)
        match = (
            match_school(title or '', schools_short, schools_full)
            or match_school(title_ja or '', schools_short, schools_full)
            or match_school(summary or '', schools_short, schools_full)
        )
        if not match:
            continue
        sid, full_name, _matched = match
        if school_count.get(sid, 0) >= PER_SCHOOL_CAP:
            skipped_cap += 1
            continue
        # Build quote
        text = body[:MAX_LEN]
        if len(text) < MIN_LEN:
            skipped_len += 1
            continue
        h = hashlib.md5(f'{sid}|{text[:80]}'.encode()).hexdigest()
        if h in existing_hashes:
            skipped_dup += 1
            continue
        existing_hashes.add(h)
        jpms_db.execute(
            """INSERT INTO testimonials_v2
               (school_id, speaker_role, speaker_attribute, quote_text, context,
                source_type, source_url, rights_level, retrieved_at, ethics_review_status,
                retrieval_notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                'media',
                f'PE DB({source})',
                text,
                'pe-news-extract',
                'news_article',
                url,
                'quoted_with_attribution',
                pub or datetime.now().isoformat(),
                'qm1_passed_external',
                f'matched_school={full_name}',
            ),
        )
        inserted += 1
        school_count[sid] = school_count.get(sid, 0) + 1
        if inserted % 200 == 0:
            jpms_db.commit()
            print(f'  ...inserted {inserted}')
    jpms_db.commit()
    pe.close()
    print(f'PE inserted={inserted} skipped(cap)={skipped_cap} skipped(dup)={skipped_dup} skipped(len)={skipped_len}')
    return inserted


def extract_fk(jpms_db, schools_short, schools_full, school_count, existing_hashes):
    if not os.path.exists(FK_DB):
        print('FK DB not found, skip')
        return 0
    print('=== FK DB extraction ===')
    fk = sqlite3.connect(FK_DB)
    inserted = 0

    # Reports - title/summary may mention specific schools (rare)
    try:
        rows = fk.execute(
            """SELECT title, title_ja, summary, summary_ja, url, published_date
               FROM reports
               WHERE summary LIKE '%中学%' OR summary_ja LIKE '%中学%'
                  OR title LIKE '%中学%' OR title_ja LIKE '%中学%'
                  OR summary LIKE '%学園%' OR summary_ja LIKE '%学園%'
                  OR summary LIKE '%学院%' OR summary_ja LIKE '%学院%'"""
        ).fetchall()
    except Exception as e:
        print(f'FK reports skip: {e}')
        rows = []
    for title, title_ja, summary, summary_ja, url, pub in rows:
        body = clean_text(summary_ja) or clean_text(summary) or clean_text(title_ja) or clean_text(title)
        if not body:
            continue
        match = (
            match_school(title_ja or title or '', schools_short, schools_full)
            or match_school(summary_ja or summary or '', schools_short, schools_full)
        )
        if not match:
            continue
        sid, full_name, _ = match
        if school_count.get(sid, 0) >= PER_SCHOOL_CAP:
            continue
        text = body[:MAX_LEN]
        if len(text) < MIN_LEN:
            continue
        h = hashlib.md5(f'{sid}|{text[:80]}'.encode()).hexdigest()
        if h in existing_hashes:
            continue
        existing_hashes.add(h)
        jpms_db.execute(
            """INSERT INTO testimonials_v2
               (school_id, speaker_role, speaker_attribute, quote_text, context,
                source_type, source_url, rights_level, retrieved_at, ethics_review_status,
                retrieval_notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                'foresight_report',
                'FK DB report',
                text,
                'fk-report-extract',
                'foresight_report',
                url,
                'quoted_with_attribution',
                pub or datetime.now().isoformat(),
                'qm1_passed_external',
                f'matched_school={full_name}',
            ),
        )
        inserted += 1
        school_count[sid] = school_count.get(sid, 0) + 1
    jpms_db.commit()
    fk.close()
    print(f'FK inserted={inserted}')
    return inserted


def main():
    db = sqlite3.connect(JPMS_DB, timeout=300.0)
    schools_short, schools_full = build_school_index(db)
    print(f'Schools indexed: full={len(schools_full)} short={len(schools_short)}')
    school_count = get_school_counts(db)
    existing_hashes = build_existing_hashes(db)
    print(f'Existing approved testimonials covering schools: {len(school_count)}')
    print(f'Existing hashes: {len(existing_hashes)}')

    pe_in = extract_pe(db, schools_short, schools_full, school_count, existing_hashes)
    fk_in = extract_fk(db, schools_short, schools_full, school_count, existing_hashes)

    db.commit()

    # Final summary
    total = db.execute(
        "SELECT COUNT(*) FROM testimonials_v2 "
        "WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue','qm1_passed_v7','qm1_passed_external')"
    ).fetchone()[0]
    schools_covered = db.execute(
        "SELECT COUNT(DISTINCT school_id) FROM testimonials_v2 "
        "WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue','qm1_passed_v7','qm1_passed_external')"
    ).fetchone()[0]
    new_external = db.execute(
        "SELECT COUNT(*) FROM testimonials_v2 WHERE ethics_review_status='qm1_passed_external'"
    ).fetchone()[0]
    db.close()
    print('\n=== FINAL ===')
    print(f'PE inserted     : {pe_in}')
    print(f'FK inserted     : {fk_in}')
    print(f'Total external  : {new_external}')
    print(f'Total available : {total}')
    print(f'Schools covered : {schools_covered}/551 ({100*schools_covered/551:.1f}%)')


if __name__ == '__main__':
    main()
