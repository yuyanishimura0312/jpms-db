#!/usr/bin/env python3
"""Integrate Team B-5 (parent voices) into testimonials_v2."""
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_b5_parent.jsonl')


def main():
    if not JSONL.exists():
        print(f"No file: {JSONL}")
        return
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')
    inserted, rejected = 0, 0
    batch = 0
    with JSONL.open() as f:
        for line in f:
            d = json.loads(line)
            if not d.get('school_id') or not d.get('quote_text'):
                rejected += 1; continue
            if not d.get('source_url'):
                rejected += 1; continue
            if len(d['quote_text']) > 400 or len(d['quote_text']) < 20:
                rejected += 1; continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1; continue
            try:
                db.execute("""INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text, quote_summary, context,
                     source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (d['school_id'], 'parent', d.get('speaker_attribute','保護者'),
                     d['quote_text'], d.get('quote_summary',''), d.get('context',''),
                     'school_website', d['source_url'],
                     d.get('rights_level','quoted_with_attribution'),
                     datetime.now().isoformat(), 'qm1_passed'))
                inserted += 1
                batch += 1
                if batch >= 50:
                    db.commit(); batch = 0; time.sleep(0.3)
            except sqlite3.OperationalError:
                rejected += 1
    db.commit()
    print(f"Inserted: {inserted}, Rejected: {rejected}")
    print(f"Total parent testimonials: {db.execute(\"SELECT COUNT(*) FROM testimonials_v2 WHERE speaker_role='parent'\").fetchone()[0]}")
    db.close()


if __name__ == '__main__':
    main()
