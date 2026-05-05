#!/usr/bin/env python3
"""Integrate team_c_llm_students.jsonl into testimonials_v2 with QM-1 gates.

Quality gate (per record):
- school_id present and exists in schools_v2
- quote_text 25..400 chars
- source_url or source_id present
- rights_level=anonymized_only
- speaker_role in (student_current, student_alumni)
- speaker_attribute in (中学生, 卒業生)

Cross-table dedup:
- Reject if school_id × quote_text[:60] already exists in testimonials_v2
"""
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path("/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db")
SRC = Path("/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c_llm_students.jsonl")
LOG = Path("/Users/nishimura+/projects/research/jpms-db/v2/quality_gate.log")
PROGRESS = Path("/Users/nishimura+/projects/research/jpms-db/v2/codex_progress/team_c_llm_students.json")


def log_event(event):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({**event, "ts": datetime.now().isoformat()}, ensure_ascii=False) + "\n")


def gate(d):
    if not d.get("school_id"):
        return False, "no_school_id"
    if not d.get("quote_text"):
        return False, "no_quote_text"
    qt = d["quote_text"]
    if len(qt) > 400:
        return False, "quote_too_long"
    if len(qt) < 25:
        return False, "quote_too_short"
    if not (d.get("source_url") or d.get("source_id")):
        return False, "no_source"
    if d.get("rights_level") != "anonymized_only":
        return False, "invalid_rights_level"
    if d.get("speaker_role") not in ("student_current", "student_alumni"):
        return False, "invalid_speaker_role"
    if d.get("speaker_attribute") not in ("中学生", "卒業生"):
        return False, "invalid_speaker_attribute"
    return True, None


def main():
    if not SRC.exists():
        print("source missing:", SRC)
        return 1
    db = sqlite3.connect(str(DB))
    db.execute("PRAGMA journal_mode=WAL;")

    inserted = 0
    rejected = 0
    reasons = {}

    # Pre-load existing (school_id, quote_text[:60]) keys for cross-table dedup
    existing = set()
    cur = db.execute(
        "SELECT school_id, quote_text FROM testimonials_v2 "
        "WHERE quote_text IS NOT NULL"
    )
    for sid, qt in cur.fetchall():
        if qt:
            existing.add((sid, qt[:60]))

    with SRC.open() as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                rejected += 1
                reasons["bad_json"] = reasons.get("bad_json", 0) + 1
                continue
            ok, reason = gate(d)
            if not ok:
                rejected += 1
                reasons[reason] = reasons.get(reason, 0) + 1
                continue

            sch = db.execute(
                "SELECT 1 FROM schools_v2 WHERE id=?", (d["school_id"],)
            ).fetchone()
            if not sch:
                rejected += 1
                reasons["school_not_found"] = reasons.get("school_not_found", 0) + 1
                continue

            key = (d["school_id"], d["quote_text"][:60])
            if key in existing:
                rejected += 1
                reasons["duplicate"] = reasons.get("duplicate", 0) + 1
                continue
            existing.add(key)

            db.execute(
                """INSERT INTO testimonials_v2
                (school_id, speaker_role, speaker_attribute, quote_text, quote_summary,
                 context, source_type, source_url, rights_level, retrieved_at,
                 ethics_review_status, retrieval_notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    d["school_id"],
                    d["speaker_role"],
                    d["speaker_attribute"],
                    d["quote_text"],
                    d.get("quote_summary", ""),
                    d.get("context", ""),
                    d.get("source_type", "school_website"),
                    d.get("source_url"),
                    d.get("rights_level", "anonymized_only"),
                    datetime.now().isoformat(),
                    "qm1_passed",
                    "team_c_llm_students_v2",
                ),
            )
            inserted += 1
    db.commit()

    # update progress
    progress = {}
    if PROGRESS.exists():
        try:
            with PROGRESS.open() as f:
                progress = json.load(f)
        except Exception:
            pass
    progress["integration_status"] = "completed"
    progress["integration_inserted"] = inserted
    progress["integration_rejected"] = rejected
    progress["integration_reasons"] = reasons
    progress["integration_completed_at"] = datetime.now().isoformat()

    # post-state counts
    cur = db.execute(
        "SELECT speaker_role, COUNT(*) FROM testimonials_v2 "
        "WHERE speaker_role IN ('student_current','student_alumni') "
        "GROUP BY speaker_role"
    )
    progress["testimonials_v2_post_state"] = dict(cur.fetchall())
    cur = db.execute("SELECT COUNT(*) FROM testimonials_v2")
    progress["testimonials_v2_total"] = cur.fetchone()[0]

    with PROGRESS.open("w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    log_event({
        "task": "integrate_team_c_llm_students",
        "inserted": inserted,
        "rejected": rejected,
        "reasons": reasons,
    })

    db.close()
    print("inserted:", inserted)
    print("rejected:", rejected)
    print("reasons:", reasons)
    print("post-state:", progress.get("testimonials_v2_post_state"))
    print("total testimonials:", progress.get("testimonials_v2_total"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
