#!/usr/bin/env python3
"""Integrate Team C-2 (IC DB executives) into alumni_career."""
import sqlite3
import json
import hashlib
import time
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c2_ic.jsonl')


def main():
    if not JSONL.exists():
        print(f"No file: {JSONL}")
        return
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')
    inserted, rejected = 0, 0
    seen = set()
    batch = 0
    with JSONL.open() as f:
        for line in f:
            d = json.loads(line)
            if not d.get('matched_school_id') or not d.get('source_url') or not d.get('name'):
                rejected += 1; continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['matched_school_id'],)).fetchone()
            if not sch:
                rejected += 1; continue
            anon_key = f"IC_{d['name']}_{d['matched_school_id']}"
            if anon_key in seen:
                rejected += 1; continue
            seen.add(anon_key)
            anon_id = hashlib.md5(anon_key.encode()).hexdigest()[:16]
            try:
                db.execute("""INSERT INTO alumni_career
                    (school_id, alumni_anonymous_id, career_field, achievement_level,
                     source_db_ref, source_record_id, source_url,
                     evidence_count, privacy_status)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (d['matched_school_id'], anon_id,
                     d.get('career_field', d.get('category','executive')),
                     d.get('confidence', 3),
                     'IC', d['name'][:50],
                     d['source_url'], 1, 'public_record'))
                inserted += 1
                batch += 1
                if batch >= 50:
                    db.commit(); batch = 0; time.sleep(0.3)
            except sqlite3.OperationalError:
                rejected += 1
    db.commit()
    print(f"Inserted: {inserted}, Rejected: {rejected}")
    print(f"alumni_career total: {db.execute('SELECT COUNT(*) FROM alumni_career').fetchone()[0]}")
    print(f"alumni_career IC: {db.execute(\"SELECT COUNT(*) FROM alumni_career WHERE source_db_ref='IC'\").fetchone()[0]}")
    db.close()


if __name__ == '__main__':
    main()
