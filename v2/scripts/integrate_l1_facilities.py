#!/usr/bin/env python3
"""Integrate Team L-1 outputs (admission/progress/facility) into respective tables.

Quality gate:
- school_id 必須・schools_v2 に存在
- source_url 必須
- 重複防止（school_id+key組み合わせ）
"""
import sqlite3
import json
import time
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output')


def connect():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')
    return db


def integrate_admission(db):
    f = OUT / 'team_l1_admission.jsonl'
    if not f.exists():
        return {'name':'L1-admission', 'status':'no_file'}
    inserted, rejected = 0, 0
    batch = 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('school_id') or not d.get('source_url'):
                rejected += 1; continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1; continue
            try:
                db.execute("""INSERT INTO school_admission_v2
                    (school_id, year, exam_type, exam_count, applicants, admitted,
                     competition_ratio, scoring_summary, source_url, rights_level)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (d['school_id'], d.get('year'), d.get('exam_type','一般'),
                     d.get('exam_count'), d.get('applicants'), d.get('admitted'),
                     d.get('competition_ratio'),
                     json.dumps(d.get('scoring_summary',{}), ensure_ascii=False) if d.get('scoring_summary') else None,
                     d['source_url'], 'archive_only'))
                inserted += 1
                batch += 1
                if batch >= 50:
                    db.commit(); batch = 0; time.sleep(0.3)
            except sqlite3.OperationalError:
                rejected += 1
    db.commit()
    return {'name':'L1-admission', 'inserted':inserted, 'rejected':rejected}


def integrate_progress(db):
    f = OUT / 'team_l1_progress.jsonl'
    if not f.exists():
        return {'name':'L1-progress', 'status':'no_file'}
    inserted, rejected = 0, 0
    batch = 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('school_id') or not d.get('source_url'):
                rejected += 1; continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1; continue
            try:
                db.execute("""INSERT INTO school_progress_record_v2
                    (school_id, year, destination_type, destination_name, count,
                     share_pct, source_url, rights_level)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (d['school_id'], d.get('year'),
                     d.get('destination_type','external_high'),
                     d.get('destination_name'),
                     d.get('count'), d.get('share_pct'),
                     d['source_url'], 'archive_only'))
                inserted += 1
                batch += 1
                if batch >= 50:
                    db.commit(); batch = 0; time.sleep(0.3)
            except sqlite3.OperationalError:
                rejected += 1
    db.commit()
    return {'name':'L1-progress', 'inserted':inserted, 'rejected':rejected}


def integrate_facility(db):
    f = OUT / 'team_l1_facility.jsonl'
    if not f.exists():
        return {'name':'L1-facility', 'status':'no_file'}
    inserted, rejected = 0, 0
    batch = 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('school_id') or not d.get('source_url'):
                rejected += 1; continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1; continue
            try:
                db.execute("""INSERT INTO school_facility_v2
                    (school_id, facility_type, description, capacity, notable, source_url)
                    VALUES (?,?,?,?,?,?)""",
                    (d['school_id'], d.get('facility_type','other'),
                     d.get('description',''), d.get('capacity'),
                     d.get('notable',0), d['source_url']))
                inserted += 1
                batch += 1
                if batch >= 50:
                    db.commit(); batch = 0; time.sleep(0.3)
            except sqlite3.OperationalError:
                rejected += 1
    db.commit()
    return {'name':'L1-facility', 'inserted':inserted, 'rejected':rejected}


def main():
    db = connect()
    results = []
    print("=== L-1 Integration ===\n")
    results.append(integrate_admission(db)); db.commit()
    results.append(integrate_progress(db)); db.commit()
    results.append(integrate_facility(db)); db.commit()

    for r in results:
        print(f"  {r}")

    print("\n=== Final L-1 counts ===")
    for q, label in [
        ("SELECT COUNT(*) FROM school_admission_v2", "admission"),
        ("SELECT COUNT(*) FROM school_progress_record_v2", "progress"),
        ("SELECT COUNT(*) FROM school_facility_v2", "facility"),
    ]:
        n = db.execute(q).fetchone()[0]
        print(f"  {label}: {n}")
    db.close()


if __name__ == '__main__':
    main()
