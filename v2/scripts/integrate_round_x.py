#!/usr/bin/env python3
"""Integrate Round X testimonials from C-LLM agents.

Sources:
- team_c_llm_principal.jsonl
- team_c_llm_students.jsonl
- team_c_llm_teacher_parent.jsonl

Quality gate:
- school_id 必須
- source_url 必須
- 引用長 30-400字
- 重複除外（school_id × text[:80] hash）
"""
import sqlite3
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output')


def integrate_jsonl(db, jsonl_path, default_role, source_label):
    if not jsonl_path.exists():
        return {'name': source_label, 'status': 'no_file'}
    inserted, rejected = 0, 0
    rej_reasons = {}
    batch = 0

    # Existing dedup
    existing = set()
    for r in db.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2").fetchall():
        existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

    with jsonl_path.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except:
                rejected += 1; continue

            sid = d.get('school_id')
            quote = d.get('quote_text') or d.get('text', '')
            if not sid or not quote:
                rejected += 1; continue

            sch = db.execute("SELECT 1 FROM schools_v2 WHERE id=?", (sid,)).fetchone()
            if not sch:
                rejected += 1; continue

            quote = quote.strip()
            if len(quote) < 30 or len(quote) > 400:
                rejected += 1; continue

            if not (d.get('source_url') or d.get('source_id')):
                rejected += 1; continue

            h = hashlib.md5(f"{sid}|{quote[:80]}".encode()).hexdigest()
            if h in existing:
                rejected += 1; continue
            existing.add(h)

            role = d.get('speaker_role') or default_role

            try:
                rights_default = 'anonymized_only' if role in ('student_current','student_alumni','parent') else 'quoted_with_attribution'
                db.execute("""INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text, quote_summary, context,
                     source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid, role,
                     d.get('speaker_attribute', {'principal':'校長','teacher':'教員','student_current':'中学生','student_alumni':'卒業生','parent':'保護者'}.get(role,'')),
                     quote,
                     d.get('quote_summary',''),
                     d.get('context', source_label),
                     'school_website',
                     d.get('source_url') or d.get('source_id'),
                     d.get('rights_level', rights_default),
                     datetime.now().isoformat(),
                     'qm1_passed_round_x'))
                inserted += 1
                batch += 1
                if batch >= 100:
                    db.commit(); batch = 0; time.sleep(0.2)
            except sqlite3.OperationalError:
                rejected += 1
                rej_reasons['db_lock'] = rej_reasons.get('db_lock',0) + 1

    db.commit()
    return {'name': source_label, 'inserted': inserted, 'rejected': rejected, 'reasons': rej_reasons}


def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    print("=== Round X LLM Integration ===\n")
    results = []
    results.append(integrate_jsonl(db, OUT / 'team_c_llm_principal.jsonl', 'principal', 'C-LLM-principal'))
    db.commit()
    results.append(integrate_jsonl(db, OUT / 'team_c_llm_students.jsonl', 'student_current', 'C-LLM-students'))
    db.commit()
    results.append(integrate_jsonl(db, OUT / 'team_c_llm_teacher_parent.jsonl', 'teacher', 'C-LLM-teacher-parent'))
    db.commit()

    for r in results:
        print(f"  {r}")

    print("\n=== Final testimonials_v2 ===")
    print(f"Total: {db.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]}")
    print(f"Schools: {db.execute('SELECT COUNT(DISTINCT school_id) FROM testimonials_v2').fetchone()[0]}")
    for r in db.execute("SELECT speaker_role, COUNT(*) FROM testimonials_v2 GROUP BY speaker_role ORDER BY COUNT(*) DESC").fetchall():
        print(f"  {r[0]}: {r[1]}")
    db.close()


if __name__ == '__main__':
    main()
