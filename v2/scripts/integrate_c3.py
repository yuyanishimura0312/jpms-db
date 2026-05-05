#!/usr/bin/env python3
"""Integrate Team C-3 (Wikipedia entrepreneur/executive alumni) into alumni_career."""
import sqlite3
import json
import hashlib
import time
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c3_business.jsonl')

def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    inserted, rejected = 0, 0
    rej_reasons = {}
    seen = set()
    batch = 0

    with JSONL.open() as f:
        for line in f:
            d = json.loads(line)
            if not d.get('matched_school_id'):
                rejected += 1
                rej_reasons['no_school_id'] = rej_reasons.get('no_school_id',0)+1
                continue
            if not d.get('source_url'):
                rejected += 1
                rej_reasons['no_source_url'] = rej_reasons.get('no_source_url',0)+1
                continue
            if not d.get('name'):
                rejected += 1
                continue

            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['matched_school_id'],)).fetchone()
            if not sch:
                rejected += 1
                rej_reasons['school_not_found'] = rej_reasons.get('school_not_found',0)+1
                continue

            anon_key = f"WPC3_{d['name']}_{d['matched_school_id']}"
            if anon_key in seen:
                rejected += 1
                rej_reasons['dup'] = rej_reasons.get('dup',0)+1
                continue
            seen.add(anon_key)

            anon_id = hashlib.md5(anon_key.encode()).hexdigest()[:16]

            try:
                db.execute("""INSERT INTO alumni_career
                    (school_id, alumni_anonymous_id, career_field, achievement_level,
                     source_db_ref, source_record_id, source_url,
                     evidence_count, privacy_status)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (d['matched_school_id'], anon_id,
                     d.get('category','entrepreneur'),
                     d.get('confidence', 3),
                     'WP_C3', d['name'][:50],
                     d.get('source_url',''),
                     1, 'public_record'))
                inserted += 1
                batch += 1
                if batch >= 50:
                    db.commit()
                    batch = 0
                    time.sleep(0.3)
            except sqlite3.OperationalError as e:
                rejected += 1
                rej_reasons['db_lock'] = rej_reasons.get('db_lock', 0) + 1

    db.commit()
    print(f"Inserted: {inserted}")
    print(f"Rejected: {rejected}")
    print(f"Reasons: {rej_reasons}")
    print(f"\nTotal alumni_career: {db.execute('SELECT COUNT(*) FROM alumni_career').fetchone()[0]}")

    print("\n=== Top 10 schools by alumni count ===")
    for r in db.execute("""SELECT s.name_ja, COUNT(*) FROM alumni_career a
        JOIN schools_v2 s ON s.id=a.school_id
        GROUP BY a.school_id ORDER BY COUNT(*) DESC LIMIT 10""").fetchall():
        print(f"  {r[0]}: {r[1]}")

    print("\n=== By category ===")
    for r in db.execute("""SELECT career_field, COUNT(*) FROM alumni_career
        GROUP BY career_field ORDER BY COUNT(*) DESC""").fetchall():
        print(f"  {r[0]}: {r[1]}")

    db.close()

if __name__ == '__main__':
    main()
