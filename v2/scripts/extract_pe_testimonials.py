#!/usr/bin/env python3
"""戦略E: PE DB (PESTLE Signal DB 196,714 articles) から私立中学言及記事を抽出。

対象: title または summary に学校名 + 教育/中学関連キーワードを含む記事。
public_record の articles のみ使用、出典URL明示、引用は短文。
"""
import sqlite3
import re
import hashlib
from pathlib import Path
from datetime import datetime

PE_DB = Path('/Users/nishimura+/projects/research/pestle-signal-db/data/pestle.db')
JPMS_DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')


def main():
    # Load school name patterns
    jpms = sqlite3.connect(JPMS_DB, timeout=300.0)
    jpms.execute('PRAGMA busy_timeout=300000')
    schools = {}
    for sid, name in jpms.execute("SELECT id, name_ja FROM schools_v2 WHERE id NOT LIKE 'NATIONAL%' AND name_ja IS NOT NULL").fetchall():
        # Build short forms
        short_forms = [name]
        if name.endswith('中学校'):
            short_forms.append(name[:-3])
        if name.endswith('中等部'):
            short_forms.append(name[:-3])
        for f in short_forms:
            if f and len(f) >= 2:
                schools[f] = (sid, name)

    pe = sqlite3.connect(PE_DB)
    pe.row_factory = sqlite3.Row

    # Existing dedup
    existing = set()
    for r in jpms.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2").fetchall():
        existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

    # Educational keywords
    edu_kws = ['中学受験', '中学校', '私立', '教育', '学園', '進学', '入試', '校長', '生徒', '在校生', '卒業生', '保護者', '教員', '教師']

    inserted = 0
    rejected = 0
    by_role = {'principal':0, 'teacher':0, 'student_current':0, 'student_alumni':0, 'parent':0}
    batch = 0

    # Search articles for school names
    print("Scanning PE articles for school references...")

    # Use FTS-like approach: search articles where title or summary contains a school name
    for row in pe.execute("""SELECT id, title, title_ja, summary, url, source, published_date
        FROM articles
        WHERE title LIKE '%中学%' OR title_ja LIKE '%中学%' OR summary LIKE '%中学%'
        LIMIT 30000""").fetchall():
        title = (row['title_ja'] or row['title'] or '')
        summary = (row['summary'] or '')
        full_text = f"{title} {summary}"

        if not any(kw in full_text for kw in edu_kws):
            continue

        # Find which school is mentioned
        for short_name, (sid, full_name) in schools.items():
            if len(short_name) < 3:
                continue
            if short_name in title or short_name in summary:
                # Found mention
                # Determine role from text
                role = 'teacher'  # default
                if any(k in full_text for k in ['校長', '理事長', '学園長']):
                    role = 'principal'
                elif any(k in full_text for k in ['卒業生', 'OB', 'OG', '同窓']):
                    role = 'student_alumni'
                elif any(k in full_text for k in ['在校生', '生徒', '中学生']):
                    role = 'student_current'
                elif any(k in full_text for k in ['保護者', 'PTA']):
                    role = 'parent'

                # Use summary as quote (or title if no summary)
                quote_text = summary[:300] if len(summary) >= 30 else title[:300]
                if len(quote_text) < 30:
                    continue

                h = hashlib.md5(f"{sid}|{quote_text[:80]}".encode()).hexdigest()
                if h in existing:
                    rejected += 1
                    continue
                existing.add(h)

                try:
                    rights = 'anonymized_only' if role in ('student_current','parent') else 'quoted_with_attribution'
                    jpms.execute("""INSERT INTO testimonials_v2
                        (school_id, speaker_role, speaker_attribute, quote_text, context,
                         source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (sid, role,
                         {'principal':'メディア言及（校長）', 'teacher':'メディア言及（教員）',
                          'student_current':'メディア言及（在校生）', 'student_alumni':'メディア言及（卒業生）',
                          'parent':'メディア言及（保護者）'}.get(role, ''),
                         quote_text, f'PE/{row["source"][:30]}',
                         'media_article', row['url'], rights,
                         datetime.now().isoformat(), 'qm1_pe_extracted'))
                    inserted += 1
                    by_role[role] = by_role.get(role, 0) + 1
                    batch += 1
                    if batch >= 100:
                        jpms.commit(); batch = 0
                    break  # one match per article
                except sqlite3.OperationalError:
                    rejected += 1

    jpms.commit()
    print(f"Inserted: {inserted}")
    print(f"Rejected (dup or lock): {rejected}")
    print(f"By role: {by_role}")
    print(f"\nTotal testimonials_v2: {jpms.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]}")
    pe.close()
    jpms.close()


if __name__ == '__main__':
    main()
