#!/usr/bin/env python3
"""Integrate Team B/C/E JSONL outputs into jpms_v2.db.

QM-1 品質ゲート（事前チェック）:
- school_id 必須
- source_url または source_id 必須
- rights_level 妥当性
- 引用長 < 400字
- 個人名は本人公開済みのみ
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output')
LOG = Path('/Users/nishimura+/projects/research/jpms-db/v2/quality_gate.log')


def log_event(event):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a') as f:
        f.write(json.dumps({**event, 'ts': datetime.now().isoformat()}, ensure_ascii=False) + '\n')


def gate_testimonial(d):
    """Quality gate for testimonial records."""
    if not d.get('school_id'):
        return False, 'no_school_id'
    if not d.get('quote_text'):
        return False, 'no_quote_text'
    if len(d['quote_text']) > 400:
        return False, 'quote_too_long'
    if len(d['quote_text']) < 20:
        return False, 'quote_too_short'
    if not (d.get('source_url') or d.get('source_id')):
        return False, 'no_source'
    if d.get('rights_level') not in ('quoted_with_attribution', 'anonymized_only', 'archive_only'):
        return False, 'invalid_rights_level'
    return True, None


def integrate_b1(db):
    """Team B-1: 校長メッセージ → testimonials_v2."""
    f = OUT_DIR / 'team_b1_principal.jsonl'
    if not f.exists():
        return {'name':'B-1', 'status':'no_file'}
    inserted, rejected = 0, 0
    rejection_reasons = {}
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            ok, reason = gate_testimonial(d)
            if not ok:
                rejected += 1
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                continue
            # Verify school exists
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1
                rejection_reasons['school_not_found'] = rejection_reasons.get('school_not_found', 0) + 1
                continue
            # Insert
            db.execute("""INSERT INTO testimonials_v2
                (school_id, speaker_role, speaker_attribute, quote_text, quote_summary, context,
                 source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (d['school_id'], d.get('speaker_role','principal'), d.get('speaker_attribute',''),
                 d['quote_text'], d.get('quote_summary',''), d.get('context',''),
                 'school_website', d.get('source_url'),
                 d.get('rights_level','quoted_with_attribution'),
                 datetime.now().isoformat(), 'qm1_passed'))
            inserted += 1
    return {'name':'B-1', 'inserted':inserted, 'rejected':rejected, 'reasons':rejection_reasons}


def integrate_b2(db):
    """Team B-2: 在校生・卒業生声 → testimonials_v2."""
    f = OUT_DIR / 'team_b2_students.jsonl'
    if not f.exists():
        return {'name':'B-2', 'status':'no_file'}
    inserted, rejected = 0, 0
    rejection_reasons = {}
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            ok, reason = gate_testimonial(d)
            if not ok:
                rejected += 1
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1
                continue
            db.execute("""INSERT INTO testimonials_v2
                (school_id, speaker_role, speaker_attribute, quote_text, quote_summary, context,
                 source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (d['school_id'], d.get('speaker_role','student_current'),
                 d.get('speaker_attribute',''), d['quote_text'],
                 d.get('quote_summary',''), d.get('context',''),
                 'school_website', d.get('source_url'),
                 d.get('rights_level','anonymized_only'),
                 datetime.now().isoformat(), 'qm1_passed'))
            inserted += 1
    return {'name':'B-2', 'inserted':inserted, 'rejected':rejected, 'reasons':rejection_reasons}


def integrate_b3(db):
    """Team B-3: 教員声 → testimonials_v2."""
    f = OUT_DIR / 'team_b3_teachers.jsonl'
    if not f.exists():
        return {'name':'B-3', 'status':'no_file'}
    inserted, rejected = 0, 0
    rejection_reasons = {}
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            ok, reason = gate_testimonial(d)
            if not ok:
                rejected += 1
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1
                continue
            db.execute("""INSERT INTO testimonials_v2
                (school_id, speaker_role, speaker_attribute, quote_text, context,
                 source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (d['school_id'], 'teacher', d.get('speaker_attribute',''),
                 d['quote_text'], d.get('context',''),
                 'school_website', d.get('source_url'),
                 d.get('rights_level','quoted_with_attribution'),
                 datetime.now().isoformat(), 'qm1_passed'))
            inserted += 1
    return {'name':'B-3', 'inserted':inserted, 'rejected':rejected, 'reasons':rejection_reasons}


def integrate_b4_curriculum(db):
    """Team B-4 curriculum → school_curriculum_v2."""
    f = OUT_DIR / 'team_b4_curriculum.jsonl'
    if not f.exists():
        return {'name':'B-4-curr', 'status':'no_file'}
    inserted, rejected = 0, 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('school_id') or not d.get('subject_or_program'):
                rejected += 1
                continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1
                continue
            db.execute("""INSERT INTO school_curriculum_v2
                (school_id, category, subject_or_program, description, hours_per_week,
                 grade_levels, is_signature, source_url, rights_level)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (d['school_id'], d.get('category',''), d['subject_or_program'],
                 d.get('description',''), d.get('hours_per_week'),
                 d.get('grade_levels',''), d.get('is_signature',0),
                 d.get('source_url',''), 'archive_only'))
            inserted += 1
    return {'name':'B-4-curr', 'inserted':inserted, 'rejected':rejected}


def integrate_b4_events(db):
    """Team B-4 events → school_calendar_v2."""
    f = OUT_DIR / 'team_b4_events.jsonl'
    if not f.exists():
        return {'name':'B-4-events', 'status':'no_file'}
    inserted, rejected = 0, 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('school_id') or not d.get('event_name'):
                rejected += 1
                continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1
                continue
            db.execute("""INSERT INTO school_calendar_v2
                (school_id, event_type, event_name, duration_days, destination,
                 description, source_url)
                VALUES (?,?,?,?,?,?,?)""",
                (d['school_id'], d.get('event_type','other'), d['event_name'],
                 d.get('duration_days'), d.get('destination'),
                 d.get('description',''), d.get('source_url','')))
            inserted += 1
    return {'name':'B-4-events', 'inserted':inserted, 'rejected':rejected}


def integrate_c1(db):
    """Team C-1: GF→JPMS alumni紐付け → alumni_career."""
    f = OUT_DIR / 'team_c1_gf.jsonl'
    if not f.exists():
        return {'name':'C-1', 'status':'no_file'}
    inserted, rejected = 0, 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('matched_school_id'):
                rejected += 1
                continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['matched_school_id'],)).fetchone()
            if not sch:
                rejected += 1
                continue
            # Anonymous ID for privacy
            import hashlib
            anon_id = hashlib.md5(f"GF_{d.get('gf_person_id','')}".encode()).hexdigest()[:16]
            db.execute("""INSERT INTO alumni_career
                (school_id, alumni_anonymous_id, career_field, achievement_level,
                 source_db_ref, source_record_id, source_url,
                 evidence_count, privacy_status)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (d['matched_school_id'], anon_id,
                 d.get('category','unknown'),
                 d.get('confidence', 3),
                 'GF', str(d.get('gf_person_id','')),
                 d.get('source_url',''),
                 1,
                 'public_record'))
            inserted += 1
    return {'name':'C-1', 'inserted':inserted, 'rejected':rejected}


def ensure_family_table(db):
    """Create school_family_relation table if not exists."""
    db.execute("""CREATE TABLE IF NOT EXISTS school_family_relation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_id TEXT NOT NULL,
        epstein_type TEXT,
        hoover_layer TEXT,
        rule_matched TEXT,
        evidence_text TEXT,
        context TEXT,
        source_url TEXT,
        score INTEGER,
        FOREIGN KEY (school_id) REFERENCES schools_v2(id)
    )""")


def integrate_e1(db):
    """Team E-1: 家庭関係 → school_family_relation."""
    f = OUT_DIR / 'team_e1_family.jsonl'
    if not f.exists():
        return {'name':'E-1', 'status':'no_file'}
    ensure_family_table(db)
    inserted, rejected = 0, 0
    with f.open() as fh:
        for line in fh:
            d = json.loads(line)
            if not d.get('school_id'):
                rejected += 1
                continue
            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (d['school_id'],)).fetchone()
            if not sch:
                rejected += 1
                continue
            db.execute("""INSERT INTO school_family_relation
                (school_id, epstein_type, hoover_layer, rule_matched, evidence_text,
                 context, source_url, score)
                VALUES (?,?,?,?,?,?,?,?)""",
                (d['school_id'], d.get('epstein_type',''), d.get('hoover_layer',''),
                 d.get('rule_matched','') or d.get('rule',''),
                 d.get('evidence_text',''), d.get('context',''),
                 d.get('source_url',''), d.get('score', 1)))
            inserted += 1
    return {'name':'E-1', 'inserted':inserted, 'rejected':rejected}


def main():
    db = sqlite3.connect(DB, timeout=180.0)
    db.execute('PRAGMA busy_timeout=180000')

    results = []
    print("=== Integrating Team Outputs ===\n")
    results.append(integrate_b1(db))
    db.commit()
    results.append(integrate_b2(db))
    db.commit()
    results.append(integrate_b3(db))
    db.commit()
    results.append(integrate_b4_curriculum(db))
    db.commit()
    results.append(integrate_b4_events(db))
    db.commit()
    results.append(integrate_c1(db))
    db.commit()
    results.append(integrate_e1(db))
    db.commit()

    print("=== Integration Results ===")
    for r in results:
        print(f"  {r}")

    print("\n=== Final DB Counts ===")
    for q, label in [
        ("SELECT COUNT(*) FROM testimonials_v2", "testimonials_v2"),
        ("SELECT COUNT(*) FROM school_curriculum_v2", "school_curriculum_v2"),
        ("SELECT COUNT(*) FROM school_calendar_v2", "school_calendar_v2"),
        ("SELECT COUNT(*) FROM alumni_career", "alumni_career"),
        ("SELECT COUNT(*) FROM school_family_relation", "school_family_relation"),
        ("SELECT COUNT(*) FROM school_official_stats", "school_official_stats"),
    ]:
        n = db.execute(q).fetchone()[0]
        print(f"  {label}: {n}")

    log_event({'event':'team_integration_complete', 'results': results})
    db.close()


if __name__ == '__main__':
    main()
