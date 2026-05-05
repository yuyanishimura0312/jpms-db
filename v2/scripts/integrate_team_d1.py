#!/usr/bin/env python3
"""Integrate Team D-1 output (公的統計104件) into school_official_stats.

QM-1 倫理レビュー（事前チェック）:
- 全件公開データのみ
- source_url 必須
- school_id は NATIONAL_AGG または NATIONAL_AGG_<pref>
"""
import sqlite3
import json
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_d1_stats.jsonl')

def main():
    db = sqlite3.connect(DB, timeout=120.0)
    db.execute('PRAGMA busy_timeout=120000')

    # Ensure pref-level pseudo-schools exist for NATIONAL_AGG_<pref>
    refs = set()
    with JSONL.open() as f:
        for line in f:
            d = json.loads(line)
            sid = d['school_id']
            if sid.startswith('NATIONAL_AGG_'):
                refs.add(sid)

    for sid in refs:
        pref = sid.replace('NATIONAL_AGG_', '')
        db.execute("""INSERT OR IGNORE INTO schools_v2
            (id, name_ja, location_pref, notes)
            VALUES (?, ?, ?, ?)""",
            (sid, f'_{pref}集計_', pref, 'pref-level aggregate pseudo-school for stats reference'))

    # Insert stats
    inserted = 0
    skipped = 0
    rejected = 0
    with JSONL.open() as f:
        for line in f:
            d = json.loads(line)
            # Quality gate
            if not d.get('source_url'):
                rejected += 1
                print(f"  REJECTED (no source_url): {d.get('stat_name','?')}")
                continue
            # Check duplicate
            existing = db.execute("""SELECT id FROM school_official_stats
                WHERE school_id=? AND stat_year=? AND stat_source=? AND stat_name=?""",
                (d['school_id'], d['stat_year'], d['stat_source'], d['stat_name'])).fetchone()
            if existing:
                skipped += 1
                continue
            db.execute("""INSERT INTO school_official_stats
                (school_id, stat_year, stat_source, stat_name, stat_value, stat_unit, source_url)
                VALUES (?,?,?,?,?,?,?)""",
                (d['school_id'], d['stat_year'], d['stat_source'], d['stat_name'],
                 d['stat_value'], d['stat_unit'], d['source_url']))
            inserted += 1

    db.commit()
    print(f"\nInserted: {inserted}")
    print(f"Skipped (duplicate): {skipped}")
    print(f"Rejected (quality gate): {rejected}")
    print(f"\nTotal stats now: {db.execute('SELECT COUNT(*) FROM school_official_stats').fetchone()[0]}")

    # Sample by source
    print("\n=== By stat_source ===")
    for r in db.execute("""SELECT stat_source, COUNT(*) FROM school_official_stats
        GROUP BY stat_source ORDER BY COUNT(*) DESC""").fetchall():
        print(f"  {r[0]:20s}: {r[1]}")

    # By prefecture
    print("\n=== By prefecture (NATIONAL_AGG_*) ===")
    for r in db.execute("""SELECT s.location_pref, COUNT(*) FROM school_official_stats s
        WHERE s.school_id LIKE 'NATIONAL_AGG_%'
        GROUP BY s.location_pref ORDER BY COUNT(*) DESC LIMIT 10""").fetchall():
        print(f"  {r[0]:10s}: {r[1]}")

    db.close()

if __name__ == '__main__':
    main()
