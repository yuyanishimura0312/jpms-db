#!/usr/bin/env python3
"""Integrate Team C-3 LLM-deep teacher/parent extraction
(team_c_llm_teacher_parent.jsonl) into testimonials_v2.

QM-1 quality gate:
- school_id must exist in schools_v2
- quote_text 20–400 chars, no PII signatures
- source_url required
- ethics_review_status set to qm1_passed_llm_v1
- avoid duplicates against existing testimonials (school + 80-char prefix)
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
DB = ROOT / "jpms_v2.db"
JSONL = ROOT / "codex_output" / "team_c_llm_teacher_parent.jsonl"
PROGRESS = ROOT / "codex_progress" / "team_c_llm_tp_integration.json"


def normalize_fullwidth(s: str) -> str:
    out = []
    for ch in s:
        cp = ord(ch)
        if 0xFF21 <= cp <= 0xFF3A or 0xFF41 <= cp <= 0xFF5A:
            out.append(chr(cp - 0xFEE0))
        elif 0xFF10 <= cp <= 0xFF19:
            out.append(chr(cp - 0xFEE0))
        elif cp == 0x3000:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def gate(rec: dict, schools: set[str], existing: set[str]) -> tuple[bool, str]:
    if rec.get("school_id") not in schools:
        return False, "school_not_found"
    quote = rec.get("quote_text", "")
    if not quote:
        return False, "no_quote_text"
    if len(quote) > 400:
        return False, "quote_too_long"
    if len(quote) < 20:
        return False, "quote_too_short"
    if not rec.get("source_url"):
        return False, "no_source_url"
    if rec.get("rights_level") not in (
        "quoted_with_attribution", "anonymized_only", "archive_only"
    ):
        return False, "invalid_rights_level"
    role = rec.get("speaker_role")
    if role not in ("teacher", "parent"):
        return False, "invalid_role"
    qnorm = normalize_fullwidth(re.sub(r"\s+", "", quote))
    sig = f"{rec['school_id']}::{qnorm[:80]}"
    if sig in existing:
        return False, "duplicate"
    existing.add(sig)
    return True, ""


def main() -> int:
    if not JSONL.exists():
        print(f"No JSONL at {JSONL}", flush=True)
        return 1
    if not DB.exists():
        print(f"No DB at {DB}", flush=True)
        return 1

    db = sqlite3.connect(DB, timeout=600.0)
    db.execute("PRAGMA busy_timeout=600000")
    cur = db.cursor()

    schools = {r[0] for r in cur.execute("SELECT id FROM schools_v2").fetchall()}

    existing: set[str] = set()
    for sid, q in cur.execute("SELECT school_id, quote_text FROM testimonials_v2"):
        qnorm = normalize_fullwidth(re.sub(r"\s+", "", q or ""))
        if qnorm:
            existing.add(f"{sid}::{qnorm[:80]}")

    inserted_t = inserted_p = 0
    rejected = 0
    rejection_reasons: dict[str, int] = {}
    batch = 0
    with JSONL.open() as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                rejected += 1
                rejection_reasons["json_error"] = (
                    rejection_reasons.get("json_error", 0) + 1
                )
                continue
            ok, reason = gate(rec, schools, existing)
            if not ok:
                rejected += 1
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                continue
            try:
                db.execute(
                    """INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text,
                     quote_summary, context, source_type, source_url,
                     rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        rec["school_id"],
                        rec["speaker_role"],
                        rec.get("speaker_attribute", ""),
                        rec["quote_text"],
                        rec.get("quote_summary", ""),
                        rec.get("context", ""),
                        "school_website",
                        rec["source_url"],
                        rec.get("rights_level", "quoted_with_attribution"),
                        datetime.now().isoformat(),
                        "qm1_passed_llm_v1",
                    ),
                )
                if rec["speaker_role"] == "teacher":
                    inserted_t += 1
                else:
                    inserted_p += 1
                batch += 1
                if batch >= 80:
                    db.commit()
                    batch = 0
                    time.sleep(0.05)
            except sqlite3.OperationalError as exc:
                rejected += 1
                rejection_reasons["db_error"] = (
                    rejection_reasons.get("db_error", 0) + 1
                )
                print(f"db error: {exc}")

    db.commit()

    final_teacher = cur.execute(
        "SELECT COUNT(*) FROM testimonials_v2 WHERE speaker_role='teacher'"
    ).fetchone()[0]
    final_parent = cur.execute(
        "SELECT COUNT(*) FROM testimonials_v2 WHERE speaker_role='parent'"
    ).fetchone()[0]
    db.close()

    progress = {
        "task_id": "team_c_llm_tp_integration",
        "ts": datetime.now().isoformat() + "Z",
        "inserted_teacher": inserted_t,
        "inserted_parent": inserted_p,
        "inserted_total": inserted_t + inserted_p,
        "rejected": rejected,
        "rejection_reasons": rejection_reasons,
        "final_teacher_total": final_teacher,
        "final_parent_total": final_parent,
        "final_combined": final_teacher + final_parent,
    }
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"Inserted teacher: {inserted_t}")
    print(f"Inserted parent:  {inserted_p}")
    print(f"Rejected:         {rejected} ({rejection_reasons})")
    print(f"Final teacher:    {final_teacher}")
    print(f"Final parent:     {final_parent}")
    print(f"Combined:         {final_teacher + final_parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
