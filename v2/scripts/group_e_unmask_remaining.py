#!/usr/bin/env python3
"""
Reverse the pii_masked substitutions for rows that have NO backup entry.

For each row whose retrieval_notes contains entries of the form
`name:<original>->○○` or `club:<token>->部活動` or `grade:<pat>-><gen>`
or `cohort:第○期生->卒業生` or `year:<pat>-><label>`, we undo the
replacements one by one. We process notes in REVERSE order so that the
last substitution in the original audit pipeline is undone first.

Limitation: if the original text legitimately contained `○○` or `部活動`,
this undoing might over-restore. We accept that as the lesser evil –
shipping pre-audit text untouched is better than shipping institutional
nonsense.

We only operate on rows whose retrieval_notes still contains "pii_masked:".
After undoing we strip the pii_masked notes from retrieval_notes so the
re-run can re-decide cleanly.
"""
from __future__ import annotations

import re
import sqlite3
import sys
import time
from pathlib import Path

DB = Path("/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db")

_NOTE_RE = re.compile(r"(name|club|grade|cohort|year):([^,;]+?)->(\S+?)(?=,|;|$)")


def _undo_one(text: str, kind: str, original: str, replacement: str) -> str:
    """Replace the FIRST occurrence of `replacement` with `original`."""
    if replacement and replacement in text:
        return text.replace(replacement, original, 1)
    return text


def main() -> int:
    conn = sqlite3.connect(str(DB), timeout=180.0)
    conn.execute("PRAGMA busy_timeout = 180000;")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, quote_text, retrieval_notes FROM testimonials_v2 "
        "WHERE retrieval_notes LIKE '%pii_masked:%'"
    )
    rows = cur.fetchall()
    print(f"Processing {len(rows)} rows still bearing pii_masked notes.")

    updates: list[tuple[str, str, int]] = []
    for rid, text, notes in rows:
        if not notes or not text:
            continue
        # Extract the pii_masked segment (between "pii_masked:" and the next ;)
        m = re.search(r"pii_masked:([^;]+)", notes)
        if not m:
            continue
        body = m.group(1).strip()
        # The body is a comma-separated list of K:V->R triplets that we
        # captured. They were applied in left-to-right order in mask_pii.
        triplets = list(_NOTE_RE.finditer(body))
        # Undo in REVERSE order
        new_text = text
        for tri in reversed(triplets):
            kind = tri.group(1)
            original = tri.group(2)
            replacement = tri.group(3)
            # Sanitize grade patterns (the "original" is a regex)
            if kind == "grade":
                # we can't easily reconstruct the grade — skip
                continue
            if kind == "cohort":
                # Original could be 第1期生 etc., we don't know which.
                continue
            if kind == "year":
                # Same – original year is lost
                continue
            new_text = _undo_one(new_text, kind, original, replacement)
        if new_text == text:
            continue
        # Strip pii_masked + rights_downgraded_minor lines from notes
        kept = "; ".join(
            seg for seg in notes.split("; ")
            if not seg.startswith("pii_masked:")
            and not seg.startswith("rights_downgraded_minor")
            and seg.strip()
        ) or None
        updates.append((new_text, kept, rid))

    print(f"Will undo masking on {len(updates)} rows.")
    BATCH = 200
    for i in range(0, len(updates), BATCH):
        chunk = updates[i : i + BATCH]
        for attempt in range(8):
            try:
                cur.execute("BEGIN IMMEDIATE;")
                cur.executemany(
                    "UPDATE testimonials_v2 SET quote_text = ?, "
                    "retrieval_notes = ? WHERE id = ?",
                    chunk,
                )
                conn.commit()
                break
            except sqlite3.OperationalError as exc:
                if "lock" in str(exc) or "busy" in str(exc):
                    time.sleep(1.0 * (attempt + 1))
                    try:
                        conn.rollback()
                    except sqlite3.OperationalError:
                        pass
                    continue
                raise

    conn.close()
    print("Un-masking complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
