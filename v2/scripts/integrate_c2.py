#!/usr/bin/env python3
"""Integrate Team C-2 (IC = EDINET listed-company executives) into alumni_career.

Notes:
- Source records originated from Wikipedia narratives (team_c3_business /
  team_c4_academic), but were filtered to only those that mention a listed
  company present in the EDINET-derived company master in ir.db.
- These records are therefore "IC-context" and treated as public_record.
- alumni_anonymous_id namespace is prefixed "IC_" to keep it disjoint from
  the c3_business "WP_C3_..." records, even when the same person appears
  in both contexts.
"""
import sqlite3
import json
import hashlib
import time
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c2_ic.jsonl')


def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    inserted = 0
    rejected = 0
    rej_reasons = {}
    seen = set()
    batch_size = 50
    batch_count = 0

    with JSONL.open() as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            if not d.get('matched_school_id'):
                rejected += 1
                rej_reasons['no_school_id'] = rej_reasons.get('no_school_id', 0) + 1
                continue
            if not d.get('name'):
                rejected += 1
                rej_reasons['no_name'] = rej_reasons.get('no_name', 0) + 1
                continue

            sch = db.execute(
                "SELECT 1 FROM schools_v2 WHERE id=?",
                (d['matched_school_id'],),
            ).fetchone()
            if not sch:
                rejected += 1
                rej_reasons['school_not_found'] = rej_reasons.get('school_not_found', 0) + 1
                continue

            # IC namespace key includes company so the same exec appearing in
            # multiple companies generates multiple IC records intentionally.
            anon_key = f"IC_{d['name']}_{d['matched_school_id']}_{d.get('company','')}"
            if anon_key in seen:
                rejected += 1
                rej_reasons['dup'] = rej_reasons.get('dup', 0) + 1
                continue
            seen.add(anon_key)

            anon_id = hashlib.md5(anon_key.encode()).hexdigest()[:16]

            # Derive career_field: business by default, but tag executives explicitly
            position = d.get('position') or ''
            if any(k in position for k in ('社長', '会長', '頭取', 'CEO', '創業')):
                career_field = 'executive'
            elif position:
                career_field = 'executive'
            else:
                career_field = d.get('category') or 'business'

            try:
                db.execute(
                    """INSERT INTO alumni_career
                       (school_id, alumni_anonymous_id, career_field, achievement_level,
                        source_db_ref, source_record_id, source_url,
                        evidence_count, privacy_status)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        d['matched_school_id'],
                        anon_id,
                        career_field,
                        d.get('confidence', 3),
                        'IC',
                        (d['name'] + '@' + (d.get('company') or ''))[:50],
                        d.get('source_url', ''),
                        1,
                        'public_record',
                    ),
                )
                inserted += 1
                batch_count += 1
                if batch_count >= batch_size:
                    db.commit()
                    batch_count = 0
                    time.sleep(0.3)
            except sqlite3.OperationalError as e:
                rejected += 1
                rej_reasons['db_lock'] = rej_reasons.get('db_lock', 0) + 1

    db.commit()

    print(f"Inserted: {inserted}")
    print(f"Rejected: {rejected}")
    print(f"Reasons: {rej_reasons}")
    print(
        f"\nTotal alumni_career rows: "
        f"{db.execute('SELECT COUNT(*) FROM alumni_career').fetchone()[0]}"
    )

    print("\n=== alumni_career rows by source_db_ref ===")
    for r in db.execute(
        "SELECT source_db_ref, COUNT(*) FROM alumni_career "
        "GROUP BY source_db_ref ORDER BY 2 DESC"
    ):
        print(f"  {r[0]}: {r[1]}")

    print("\n=== Top 10 schools by IC alumni count ===")
    for r in db.execute(
        "SELECT s.name_ja, COUNT(*) FROM alumni_career a "
        "JOIN schools_v2 s ON s.id=a.school_id "
        "WHERE a.source_db_ref='IC' "
        "GROUP BY a.school_id ORDER BY 2 DESC LIMIT 10"
    ):
        print(f"  {r[0]}: {r[1]}")

    db.close()


if __name__ == '__main__':
    main()
