#!/usr/bin/env python3
"""Integrate Team C-5/C-6/C-8 outputs (UPR/AL/EX) into school_official_stats."""
import sqlite3
import json
import time
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output')


def integrate(db, jsonl_path, source_db_label):
    if not jsonl_path.exists():
        return {'name':source_db_label, 'status':'no_file'}
    inserted, rejected = 0, 0
    batch = 0
    with jsonl_path.open() as f:
        for line in f:
            d = json.loads(line)
            sid = d.get('school_id')
            if not sid:
                rejected += 1; continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (sid,)).fetchone()
            if not sch:
                rejected += 1; continue
            stat_value = d.get('stat_value')
            if stat_value is None:
                # Some records don't have stat_value (national baseline)
                stat_value = d.get('stat_breakdown', {}).get('japan_journals_total', 0)
            try:
                db.execute("""INSERT INTO school_official_stats
                    (school_id, stat_year, stat_source, stat_name, stat_value, stat_unit, source_url)
                    VALUES (?,?,?,?,?,?,?)""",
                    (sid, 2024, source_db_label, d.get('stat_name','unknown'),
                     stat_value, d.get('stat_unit',''),
                     d.get('source_db_path','')))
                inserted += 1
                batch += 1
                if batch >= 100:
                    db.commit(); batch = 0; time.sleep(0.2)
            except sqlite3.OperationalError:
                rejected += 1
    db.commit()
    return {'name':source_db_label, 'inserted':inserted, 'rejected':rejected}


def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')
    results = []
    print("=== C-5/C-6/C-8 Integration ===\n")
    results.append(integrate(db, OUT / 'team_c5_upr.jsonl', 'UPR'))
    db.commit()
    results.append(integrate(db, OUT / 'team_c6_al.jsonl', 'AL'))
    db.commit()
    results.append(integrate(db, OUT / 'team_c8_ex.jsonl', 'EX'))
    db.commit()
    for r in results:
        print(f"  {r}")
    print(f"\nTotal school_official_stats: {db.execute('SELECT COUNT(*) FROM school_official_stats').fetchone()[0]}")
    print("\n=== By stat_source ===")
    for r in db.execute("""SELECT stat_source, COUNT(*) FROM school_official_stats
        GROUP BY stat_source ORDER BY COUNT(*) DESC""").fetchall():
        print(f"  {r[0]}: {r[1]}")
    db.close()

if __name__ == '__main__':
    main()
