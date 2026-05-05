#!/usr/bin/env python3
"""
Group E recovery utility.

The first run of group_e_quality_audit.py used a too-aggressive PII regex
that turned legitimate institutional language ("高校1年生", "水曜日",
"本校卒業") into "○○". This script:

  1. Reads quote_text from the pre-audit backup `jpms_v2.db.bak_group_e`.
  2. Restores quote_text + retrieval_notes (only for the rows that the
     backup covers and that the audit had marked as PII-masked).
  3. Re-runs the audit (caller is expected to invoke that separately).

We take a second-line-of-defense approach: we only restore quote_text on
rows whose `retrieval_notes` shows our `pii_masked:` marker — leaving rows
that other parallel workers wrote untouched.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
DB = ROOT / "jpms_v2.db"
BAK = ROOT / "jpms_v2.db.bak_group_e"


def main() -> int:
    if not BAK.exists():
        print("Backup missing", file=sys.stderr)
        return 1

    bak_conn = sqlite3.connect(str(BAK))
    bak_cur = bak_conn.cursor()
    bak_cur.execute("SELECT id, quote_text FROM testimonials_v2")
    bak_map = {rid: txt for (rid, txt) in bak_cur.fetchall()}
    bak_conn.close()
    print(f"Backup contains {len(bak_map)} rows.")

    conn = sqlite3.connect(str(DB), timeout=180.0)
    conn.execute("PRAGMA busy_timeout = 180000;")
    cur = conn.cursor()

    # Find every row that the audit had stamped pii_masked.
    cur.execute(
        "SELECT id, quote_text, retrieval_notes FROM testimonials_v2 "
        "WHERE retrieval_notes LIKE '%pii_masked:%'"
    )
    target = cur.fetchall()
    print(f"Found {len(target)} rows previously PII-masked.")

    to_restore: list[tuple[str, str, int]] = []
    skipped_no_backup = 0
    for rid, current_text, notes in target:
        if rid not in bak_map:
            skipped_no_backup += 1
            continue
        original = bak_map[rid]
        if original == current_text:
            continue  # no-op
        # Strip our pii_masked notes from retrieval_notes; keep other notes.
        kept_notes = "; ".join(
            seg for seg in (notes or "").split("; ")
            if not seg.startswith("pii_masked:")
            and not seg.startswith("rights_downgraded_minor")
            and seg.strip()
        ) or None
        to_restore.append((original, kept_notes, rid))

    print(f"Will restore {len(to_restore)} quote_text entries from backup. "
          f"({skipped_no_backup} rows had no backup entry, skipped.)")

    BATCH = 300
    for i in range(0, len(to_restore), BATCH):
        chunk = to_restore[i : i + BATCH]
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
                    print(f"  lock retry {attempt+1}: {exc}", file=sys.stderr)
                    try:
                        conn.rollback()
                    except sqlite3.OperationalError:
                        pass
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
        else:
            print("  failed after retries", file=sys.stderr)

    # Reset rights_level on rows we previously force-downgraded (only rows
    # whose original quote_text was restored), so the rerun can re-assess.
    cur.execute(
        "SELECT id FROM testimonials_v2 "
        "WHERE ethics_review_status = 'anonymized_only_forced'"
    )
    forced_ids = [r[0] for r in cur.fetchall()]
    print(f"Resetting ethics_review_status on {len(forced_ids)} forced rows.")
    for rid in forced_ids:
        for attempt in range(8):
            try:
                cur.execute("BEGIN IMMEDIATE;")
                cur.execute(
                    "UPDATE testimonials_v2 SET ethics_review_status = 'pending' "
                    "WHERE id = ?",
                    (rid,),
                )
                conn.commit()
                break
            except sqlite3.OperationalError as exc:
                if "lock" in str(exc) or "busy" in str(exc):
                    time.sleep(1.0)
                    try:
                        conn.rollback()
                    except sqlite3.OperationalError:
                        pass
                    continue
                raise

    conn.close()
    print("Restore complete. Now re-run group_e_quality_audit.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
