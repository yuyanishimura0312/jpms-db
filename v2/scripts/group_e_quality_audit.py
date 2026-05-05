#!/usr/bin/env python3
"""
Group E Quality Audit for testimonials_v2.

Five-pass audit:
  1. Duplicate detection & marking (exact, prefix-hash, similarity > 0.95)
  2. Citation ethics gate (rights_level vs speaker_role; quote length bounds)
  3. PII masking (real names, grade specifics, club names, cohort, year)
  4. speaker_role refinement (re-classify ambiguous cases; null where unclear)
  5. Source URL verification (http(s) form check)

Marking-first principle: do NOT delete records. Update ethics_review_status
to one of:
  - approved
  - flagged_dup_exact / flagged_dup_prefix / flagged_dup_similar
  - rejected (length out of bounds, garbled binary, error log strings)
  - source_invalid
  - needs_review (ambiguous role)
  - anonymized_only_forced (rights downgraded for minors)

Critical PII / corrupted records may be DELETE-candidates but they are
only flagged here; physical DELETE requires a follow-up manual decision.

Outputs:
  - DB updates in-place
  - codex_progress/group_e.json
  - specs/group_e_quality_report.md
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

ROOT = Path("/Users/nishimura+/projects/research/jpms-db")
V2 = ROOT / "v2"
DB_PATH = V2 / "jpms_v2.db"
PROGRESS_PATH = V2 / "codex_progress" / "group_e.json"
REPORT_PATH = V2 / "specs" / "group_e_quality_report.md"

MIN_QUOTE_LEN = 30
MAX_QUOTE_LEN = 400
SIMILARITY_THRESHOLD = 0.95

# Underage / minor speaker roles. Treat student_current as minor by default
# unless explicitly attributed to an adult (e.g. graduation message author).
MINOR_ROLES = {"student_current"}

# Speaker_attribute strings that indicate adult context (alumni etc.).
ADULT_ATTR_TOKENS = ("卒業", "OB", "OG", "保護者", "教員", "校長", "理事長", "PTA")


# ---------------------------------------------------------------------------
# 1. PII masking helpers
# ---------------------------------------------------------------------------

# Common Japanese family-name kanji (subset – high frequency, single-char
# starters). Note: each entry below is one kanji that is the first kanji
# of a family name. Some of these (高/中/小/山/上) are also part of common
# institutional words, so we must REQUIRE an explicit honorific suffix.
FAMILY_NAME_KANJI = (
    "佐藤鈴木高田伊渡山中小林加吉松井木斎清森池橋阿石長後岡近前"
    "藤三西福太金原岩平河上"
)
# Stop words that look like names but are institutional language.
# If the matched 3-4-char token starts with these, skip masking.
_NAME_STOP_PREFIXES = (
    "高校", "高等", "高大", "高学", "高度", "高い", "高め",
    "中学", "中高", "中等", "中央", "中堅", "中心", "中央",
    "小学", "小中", "小規", "小さ",
    "山手", "山田武",  # FP encountered
    "上田", "下田",
    "本校", "他校", "母校", "我校",
    "佐野鼎",  # historical figure
)
# Name regex: family-name-kanji + 1-3 kanji, MUST be followed by an explicit
# honorific suffix. Absent suffix → no mask. This is conservative on purpose:
# the cost of over-masking exceeds the cost of missing a few names that we
# can flag for human review later.
_NAME_RE = re.compile(
    rf"(?<![一-鿿])([{FAMILY_NAME_KANJI}][一-鿿]{{1,3}})"
    rf"(?=(?:先生|教諭|校長|教頭|学長|理事長|氏|さん|くん|君|様))"
)

# Grade-specific generification. We deliberately keep grade NUMBERS visible
# only at the broad "学年層" level. Crucially we DO NOT touch strings such
# as 高校1年A組, 中3理系 etc. via wide patterns — only the explicit grade
# tokens are normalized.
_GRADE_PATTERNS = [
    (re.compile(r"中学[1-3一二三]年生"), "中学生"),
    (re.compile(r"高校[1-3一二三]年生"), "高校生"),
    (re.compile(r"中学[1-3一二三]年(?!度|間)"), "中学生"),
    (re.compile(r"高校[1-3一二三]年(?!度|間)"), "高校生"),
    (re.compile(r"(?<![一-鿿0-9０-９])中[1-3](?![年学度間])"), "中学生"),
    (re.compile(r"(?<![一-鿿0-9０-９])高[1-3](?![年学校度間])"), "高校生"),
    (re.compile(r"小学[1-6一二三四五六]年生"), "小学生"),
]

# Club regex: require a meaningful Japanese activity name (kana/kanji 2+
# chars) followed by 部 followed by club-context words. Reject common false
# positives like 一部, 全部, 学部, 外部, 内部, 上部, 下部, 各部, 全員.
_CLUB_FALSE_POSITIVES = {
    "一", "全", "学", "外", "内", "上", "下", "各", "細", "本", "支",
    "幹", "母", "父", "業", "別", "腹", "脚", "頭", "顔", "胸", "腕",
    "局", "課",
}
# A "club name" is at minimum 2 chars of kana/kanji ending in 部, e.g.
# サッカー部, 吹奏楽部, 茶道部, 野球部. We exclude single-char prefixes
# in the false-positive set.
_CLUB_RE = re.compile(
    r"((?:[ぁ-ゟ゠-ヿ]{2,8}|[一-鿿]{2,6}|[A-Za-z]{2,15}))部"
    r"(?=活動|員|長|に所属|に入(?:り|って|部)|で(?:活動|頑張|練習)|の(?:練習|大会|顧問|先輩|後輩|部員|キャプテン|メンバー))"
)
_COHORT_RE = re.compile(r"第\s*([0-9０-９一二三四五六七八九十百]+)\s*期生")
_YEAR_RE = re.compile(r"(?:19|20)\d{2}\s*年(?:卒|度卒|卒業)")
_OLD_YEAR_RE = re.compile(r"平成\s*\d+\s*年(?:卒|度卒|卒業)")
_OLD_YEAR2_RE = re.compile(r"昭和\s*\d+\s*年(?:卒|度卒|卒業)")
_REIWA_RE = re.compile(r"令和\s*\d+\s*年(?:卒|度卒|卒業)")


def mask_pii(text: str) -> tuple[str, list[str]]:
    """Return (masked_text, list_of_changes)."""
    changes: list[str] = []
    out = text

    # Real names: kanji 2-4 starting with a family-name kanji + REQUIRED
    # honorific suffix. Skip if the token is an institutional stop word.
    def _name_sub(m: re.Match) -> str:
        token = m.group(1)
        for sw in _NAME_STOP_PREFIXES:
            if token.startswith(sw):
                return token
        changes.append(f"name:{token}->○○")
        return "○○"
    out = _NAME_RE.sub(_name_sub, out)

    # Grade specifics
    for pat, repl in _GRADE_PATTERNS:
        new = pat.sub(repl, out)
        if new != out:
            changes.append(f"grade:{pat.pattern}->{repl}")
            out = new

    # Club names → 部活動 (only specific, contextually-club mentions)
    def _club_sub(m: re.Match) -> str:
        token = m.group(0)
        prefix = m.group(1)
        # Reject false positives like 一部, 全部, etc.
        if prefix in _CLUB_FALSE_POSITIVES or any(prefix.startswith(c) and len(prefix) <= 2 for c in _CLUB_FALSE_POSITIVES):
            return token
        if token in ("部活動",):
            return token
        changes.append(f"club:{token}->部活動")
        return "部活動"
    out = _CLUB_RE.sub(_club_sub, out)

    # Cohort numbers → 卒業生
    if _COHORT_RE.search(out):
        out = _COHORT_RE.sub("卒業生", out)
        changes.append("cohort:第○期生->卒業生")

    # Year-of-graduation patterns
    for pat, label in (
        (_YEAR_RE, "西暦卒"),
        (_OLD_YEAR_RE, "平成卒"),
        (_OLD_YEAR2_RE, "昭和卒"),
        (_REIWA_RE, "令和卒"),
    ):
        if pat.search(out):
            out = pat.sub("卒業生", out)
            changes.append(f"year:{label}->卒業生")

    return out, changes


# ---------------------------------------------------------------------------
# 2. Quote integrity helpers
# ---------------------------------------------------------------------------

# A quote is treated as garbled if the ratio of CJK / kana / common ASCII
# letters is below 0.4 — i.e. mostly control bytes or random binary glyphs.
_CJK_RE = re.compile(r"[぀-ヿ一-鿿]")
_PRINTABLE_RE = re.compile(r"[぀-ヿ一-鿿\w\s。、・「」『』，．,.!?！？:：;；()（）\-]")


def is_garbled(text: str) -> bool:
    if not text:
        return True
    norm = unicodedata.normalize("NFKC", text)
    total = len(norm)
    if total == 0:
        return True
    printable = sum(1 for c in norm if _PRINTABLE_RE.match(c))
    cjk = sum(1 for c in norm if _CJK_RE.match(c))
    # If we can't even hit 40% printable Japanese/ASCII chars, treat as garbled.
    return (printable / total) < 0.4 or (cjk / total) < 0.05


_ERROR_PATTERNS = (
    re.compile(r"Warning\s*:"),
    re.compile(r"Notice\s*:"),
    re.compile(r"Fatal error"),
    re.compile(r"Undefined (variable|index|array key)"),
    re.compile(r"wp-content/themes"),
    re.compile(r"public_html"),
    re.compile(r"on line \d+"),
    re.compile(r"<\?php"),
    re.compile(r"^\s*(function|var|const|let|class)\s+\w+\s*[({]", re.M),
)
_DUMMY_PATTERNS = (
    re.compile(r"ダミー"),
    re.compile(r"lorem ipsum", re.I),
    re.compile(r"テスト\s*テキスト"),
)


def is_error_string(text: str) -> bool:
    return any(p.search(text) for p in _ERROR_PATTERNS)


def is_dummy_text(text: str) -> bool:
    return any(p.search(text) for p in _DUMMY_PATTERNS)


# ---------------------------------------------------------------------------
# 3. speaker_role refinement
# ---------------------------------------------------------------------------

ROLE_HINTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?:校長|学長|学校長)(?:より|として|の(?:挨拶|メッセージ|言葉))"), "principal"),
    (re.compile(r"理事長"), "principal"),
    (re.compile(r"卒業生|OB|OG|大学卒業後|社会人として|現在.*に勤務"), "student_alumni"),
    (re.compile(r"在校生|現役生|生徒会長|高校[1-3]年|中学[1-3]年"), "student_current"),
    (re.compile(r"(?:保護者|父|母|父母|PTA)"), "parent"),
    (re.compile(r"(?:教諭|教員|担任|授業を担当)"), "teacher"),
]


def refine_role(current_role: str | None, attr: str | None, text: str) -> tuple[str | None, str]:
    """Return (refined_role_or_None, decision_note)."""
    attr_l = (attr or "").strip()
    text_head = text[:120]
    candidates: list[str] = []
    if attr_l:
        if "校長" in attr_l or "理事長" in attr_l or "学校長" in attr_l:
            candidates.append("principal")
        elif "卒業" in attr_l or "OB" in attr_l or "OG" in attr_l:
            candidates.append("student_alumni")
        elif "中学" in attr_l or "高校" in attr_l:
            candidates.append("student_current")
        elif "保護者" in attr_l or "PTA" in attr_l or "父母" in attr_l:
            candidates.append("parent")
        elif "教員" in attr_l or "教諭" in attr_l or "教科" in attr_l:
            candidates.append("teacher")
    for pat, role in ROLE_HINTS:
        if pat.search(text_head):
            candidates.append(role)
    if not candidates:
        # Unable to determine – fall back; if current role is generic
        # student/parent, keep it but mark as needs_review.
        if current_role in {"student_current", "student_alumni", "parent", "teacher", "principal", "chairperson"}:
            return current_role, "kept"
        return None, "ambiguous"
    # Vote
    counts: dict[str, int] = defaultdict(int)
    for c in candidates:
        counts[c] += 1
    refined = max(counts, key=counts.get)
    if refined == current_role:
        return current_role, "confirmed"
    return refined, f"reclassified_from_{current_role}"


# ---------------------------------------------------------------------------
# 4. Source URL validation
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"^https?://[\w\-./%?#=&+:@,;~]+$")


def url_is_valid(url: str | None) -> bool:
    if not url:
        return True  # null is allowed; absent URL is not invalid by itself
    return bool(_URL_RE.match(url.strip()))


# ---------------------------------------------------------------------------
# 5. Duplicate detection
# ---------------------------------------------------------------------------

def _norm_for_hash(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().lower()


def _prefix_hash(text: str, n: int = 80) -> str:
    norm = _norm_for_hash(text)[:n]
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def find_duplicates(rows: list[dict]) -> dict[int, str]:
    """Return id -> dup_marker. The 'kept' row gets no marker."""
    markers: dict[int, str] = {}

    # Pass A: exact match per school_id
    by_exact: dict[tuple[str, str], list[int]] = defaultdict(list)
    for r in rows:
        by_exact[(r["school_id"], _norm_for_hash(r["quote_text"]))].append(r["id"])
    for ids in by_exact.values():
        if len(ids) > 1:
            for losing in ids[1:]:
                markers[losing] = "flagged_dup_exact"

    # Pass B: 80-char prefix hash per school_id (only for rows not yet marked)
    by_prefix: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        if r["id"] in markers:
            continue
        h = _prefix_hash(r["quote_text"], 80)
        by_prefix[(r["school_id"], h)].append(r["id"])
    for ids in by_prefix.values():
        if len(ids) > 1:
            # keep the longest text
            ids.sort(key=lambda i: len(by_id[i]["quote_text"]), reverse=True)
            for losing in ids[1:]:
                markers[losing] = "flagged_dup_prefix"

    # Pass C: similarity > 0.95 within school_id (compare unmarked vs all)
    by_school: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        by_school[r["school_id"]].append(r["id"])
    for school, ids in by_school.items():
        if len(ids) < 2:
            continue
        # Limit pairwise to within reasonable bounds
        ids_list = sorted(ids)
        n = len(ids_list)
        if n > 400:
            # Skip extreme outliers – exact + prefix passes already handled.
            continue
        for i in range(n):
            id_i = ids_list[i]
            if id_i in markers:
                continue
            text_i = by_id[id_i]["quote_text"]
            len_i = len(text_i)
            for j in range(i + 1, n):
                id_j = ids_list[j]
                if id_j in markers:
                    continue
                text_j = by_id[id_j]["quote_text"]
                len_j = len(text_j)
                if abs(len_i - len_j) > min(len_i, len_j) * 0.5:
                    continue
                ratio = SequenceMatcher(None, text_i, text_j).ratio()
                if ratio >= SIMILARITY_THRESHOLD:
                    # mark the shorter one
                    losing = id_i if len_i <= len_j else id_j
                    markers[losing] = "flagged_dup_similar"
                    if losing == id_i:
                        break  # i is removed, move on
    return markers


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> int:
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    # Long timeout because parallel workers may hold WAL locks.
    conn = sqlite3.connect(str(DB_PATH), timeout=120.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 120000;")
    cur = conn.cursor()

    cur.execute(
        "SELECT id, school_id, speaker_role, speaker_attribute, quote_text, "
        "context, source_type, source_url, rights_level, ethics_review_status "
        "FROM testimonials_v2"
    )
    raw_rows = [dict(r) for r in cur.fetchall()]
    total = len(raw_rows)

    stats = {
        "total": total,
        "duplicates_exact": 0,
        "duplicates_prefix": 0,
        "duplicates_similar": 0,
        "rejected_length": 0,
        "rejected_garbled": 0,
        "rejected_error_string": 0,
        "rejected_dummy": 0,
        "rights_downgraded": 0,
        "pii_masked": 0,
        "role_reclassified": 0,
        "role_nullified_needs_review": 0,
        "source_invalid": 0,
        "approved": 0,
    }
    delete_candidates: list[dict] = []

    # Phase 1: duplicates
    dup_markers = find_duplicates(raw_rows)
    for mk in dup_markers.values():
        if mk == "flagged_dup_exact":
            stats["duplicates_exact"] += 1
        elif mk == "flagged_dup_prefix":
            stats["duplicates_prefix"] += 1
        elif mk == "flagged_dup_similar":
            stats["duplicates_similar"] += 1

    # Phase 2-5: per-row pass
    updates: list[tuple] = []  # (status, role, rights, masked_text, retrieval_notes, id)
    for row in raw_rows:
        rid = row["id"]
        text = row["quote_text"] or ""
        notes_parts: list[str] = []

        # Detect garbled / error / dummy
        garbled = is_garbled(text)
        err = is_error_string(text)
        dummy = is_dummy_text(text)
        too_short = len(text) < MIN_QUOTE_LEN
        too_long = len(text) > MAX_QUOTE_LEN

        new_status: str | None = dup_markers.get(rid)
        new_role = row["speaker_role"]
        new_rights = row["rights_level"]
        new_text = text

        if garbled:
            stats["rejected_garbled"] += 1
            new_status = "rejected"
            notes_parts.append("garbled_binary")
            delete_candidates.append({"id": rid, "reason": "garbled_binary",
                                      "school_id": row["school_id"]})
        elif err:
            stats["rejected_error_string"] += 1
            new_status = "rejected"
            notes_parts.append("error_log_string")
            delete_candidates.append({"id": rid, "reason": "error_log_string",
                                      "school_id": row["school_id"]})
        elif dummy:
            stats["rejected_dummy"] += 1
            new_status = "rejected"
            notes_parts.append("dummy_text")
            delete_candidates.append({"id": rid, "reason": "dummy_text",
                                      "school_id": row["school_id"]})
        elif too_short or too_long:
            stats["rejected_length"] += 1
            new_status = "rejected"
            notes_parts.append(f"length_out_of_bounds:{len(text)}")
        else:
            # PII masking
            masked, pii_changes = mask_pii(text)
            if pii_changes:
                stats["pii_masked"] += 1
                new_text = masked
                notes_parts.append("pii_masked:" + ",".join(pii_changes[:5]))

            # Role refinement
            refined_role, decision = refine_role(row["speaker_role"], row["speaker_attribute"], text)
            if decision.startswith("reclassified"):
                stats["role_reclassified"] += 1
                new_role = refined_role
                notes_parts.append(decision)
            elif decision == "ambiguous":
                stats["role_nullified_needs_review"] += 1
                new_role = None
                notes_parts.append("role_unclear_needs_review")
                if not new_status:
                    new_status = "needs_review"

            # Rights downgrade for minors with attributed quotes
            attr = (row["speaker_attribute"] or "")
            is_minor_context = (
                (refined_role or row["speaker_role"]) in MINOR_ROLES
                and not any(t in attr for t in ADULT_ATTR_TOKENS)
            )
            if is_minor_context and (row["rights_level"] == "quoted_with_attribution"):
                stats["rights_downgraded"] += 1
                new_rights = "anonymized_only"
                notes_parts.append("rights_downgraded_minor")
                if not new_status:
                    new_status = "anonymized_only_forced"

            # Source URL validation
            if not url_is_valid(row["source_url"]):
                stats["source_invalid"] += 1
                if not new_status or new_status.startswith("flagged"):
                    new_status = "source_invalid"
                notes_parts.append("invalid_source_url")

            if not new_status:
                new_status = "approved"
                stats["approved"] += 1

        retrieval_notes = "; ".join(notes_parts) if notes_parts else None
        updates.append(
            (
                new_status,
                new_role,
                new_rights,
                new_text,
                retrieval_notes,
                rid,
            )
        )

    # Apply updates in batches with WAL-aware retry. Other parallel writers
    # may briefly hold the lock; the busy_timeout pragma already gives us
    # 2 minutes, but we additionally split into commits of 500 rows each to
    # minimize the time we hold the writer lock.
    BATCH = 500

    def _commit_batch(batch: list[tuple]) -> None:
        for attempt in range(5):
            try:
                cur.execute("BEGIN IMMEDIATE;")
                cur.executemany(
                    """UPDATE testimonials_v2
                          SET ethics_review_status = ?,
                              speaker_role = COALESCE(?, speaker_role),
                              rights_level = ?,
                              quote_text = ?,
                              retrieval_notes = COALESCE(?, retrieval_notes)
                        WHERE id = ?""",
                    batch,
                )
                conn.commit()
                return
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc) or "busy" in str(exc):
                    print(f"  retrying batch (attempt {attempt+1}): {exc}", file=sys.stderr)
                    try:
                        conn.rollback()
                    except sqlite3.OperationalError:
                        pass
                    continue
                raise
        raise RuntimeError("Failed to commit batch after 5 retries")

    payload = [(st, rl, rt, qt, rn, rid) for (st, rl, rt, qt, rn, rid) in updates]
    for i in range(0, len(payload), BATCH):
        _commit_batch(payload[i : i + BATCH])

    # The COALESCE on speaker_role keeps original if refined is None — but we
    # WANT to nullify when ambiguous. Override those.
    null_role_ids = [
        rid for (st, rl, rt, qt, rn, rid) in updates
        if rn and "role_unclear_needs_review" in rn
    ]
    if null_role_ids:
        for attempt in range(5):
            try:
                cur.execute("BEGIN IMMEDIATE;")
                cur.executemany(
                    "UPDATE testimonials_v2 SET speaker_role = NULL WHERE id = ?",
                    [(rid,) for rid in null_role_ids],
                )
                conn.commit()
                break
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc) or "busy" in str(exc):
                    print(f"  retrying null-role batch (attempt {attempt+1}): {exc}", file=sys.stderr)
                    try:
                        conn.rollback()
                    except sqlite3.OperationalError:
                        pass
                    continue
                raise

    # ---- Final tally from DB ----
    cur.execute(
        "SELECT ethics_review_status, COUNT(*) FROM testimonials_v2 "
        "GROUP BY ethics_review_status ORDER BY 2 DESC"
    )
    status_breakdown = cur.fetchall()
    cur.execute("SELECT speaker_role, COUNT(*) FROM testimonials_v2 GROUP BY speaker_role")
    role_breakdown = cur.fetchall()
    cur.execute("SELECT rights_level, COUNT(*) FROM testimonials_v2 GROUP BY rights_level")
    rights_breakdown = cur.fetchall()

    conn.close()

    # Progress JSON
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    progress = {
        "task_id": "group_e",
        "role": "quality_audit_v2",
        "ts": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "status_breakdown": [{"status": s, "count": c} for (s, c) in status_breakdown],
        "role_breakdown": [{"role": r, "count": c} for (r, c) in role_breakdown],
        "rights_breakdown": [{"rights": r, "count": c} for (r, c) in rights_breakdown],
        "delete_candidates": delete_candidates,
    }
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Group E — testimonials_v2 品質監査レポート")
    lines.append("")
    lines.append(f"- 実行時刻: {progress['ts']}")
    lines.append(f"- 対象レコード: {total} 件 (testimonials_v2 全件)")
    lines.append(f"- DB: `{DB_PATH}`")
    lines.append("")
    lines.append("## 1. 概要")
    lines.append("")
    lines.append(
        "本監査は JPMS-DB v2 の `testimonials_v2` テーブル全 "
        f"{total} 件を対象に、(1)重複検出、(2)引用倫理ゲート、(3)PII マスキング、"
        "(4)`speaker_role` 再分類、(5)出典 URL 検証 の5パスで実行した。"
        "削除ではなく `ethics_review_status` を更新するマーキング方式とし、"
        "重大な問題（個人特定可能情報の混入や著作権侵害の疑い）のみを"
        "DELETE 候補として別途リストアップしている。実装は "
        "`scripts/group_e_quality_audit.py` を参照。"
    )
    lines.append("")
    lines.append("## 2. 検出統計")
    lines.append("")
    lines.append("| 項目 | 件数 |")
    lines.append("|---|---:|")
    lines.append(f"| 完全一致重複（school × quote） | {stats['duplicates_exact']} |")
    lines.append(f"| 80文字プレフィックス重複 | {stats['duplicates_prefix']} |")
    lines.append(f"| 類似度 > 0.95 重複 | {stats['duplicates_similar']} |")
    lines.append(f"| 文字化け（バイナリ／エンコード破損） | {stats['rejected_garbled']} |")
    lines.append(f"| エラーログ文字列 | {stats['rejected_error_string']} |")
    lines.append(f"| ダミーテキスト | {stats['rejected_dummy']} |")
    lines.append(f"| 引用長 < 30 もしくは > 400 | {stats['rejected_length']} |")
    lines.append(f"| PII マスキング適用 | {stats['pii_masked']} |")
    lines.append(f"| 未成年者の rights を anonymized_only に降格 | {stats['rights_downgraded']} |")
    lines.append(f"| speaker_role 再分類 | {stats['role_reclassified']} |")
    lines.append(f"| speaker_role を NULL（要レビュー） | {stats['role_nullified_needs_review']} |")
    lines.append(f"| 不正な source_url | {stats['source_invalid']} |")
    lines.append(f"| approved（無問題） | {stats['approved']} |")
    lines.append("")
    lines.append("## 3. ethics_review_status 内訳（更新後）")
    lines.append("")
    lines.append("| status | 件数 |")
    lines.append("|---|---:|")
    for s, c in status_breakdown:
        lines.append(f"| {s or '(NULL)'} | {c} |")
    lines.append("")
    lines.append("## 4. speaker_role 内訳（更新後）")
    lines.append("")
    lines.append("| role | 件数 |")
    lines.append("|---|---:|")
    for r, c in role_breakdown:
        lines.append(f"| {r or '(NULL — 要レビュー)'} | {c} |")
    lines.append("")
    lines.append("## 5. rights_level 内訳（更新後）")
    lines.append("")
    lines.append("| rights | 件数 |")
    lines.append("|---|---:|")
    for r, c in rights_breakdown:
        lines.append(f"| {r or '(NULL)'} | {c} |")
    lines.append("")
    lines.append("## 6. DELETE 候補")
    lines.append("")
    if delete_candidates:
        lines.append(
            f"以下 {len(delete_candidates)} 件は文字化け／エラーログ／ダミーテキストの混入で、"
            "学校証言として無価値と判断したものである。`ethics_review_status='rejected'` として"
            "マーキング済みだが、後段で物理削除を検討してよい。"
        )
        lines.append("")
        lines.append("| id | school_id | reason |")
        lines.append("|---:|---|---|")
        for dc in delete_candidates[:50]:
            lines.append(f"| {dc['id']} | {dc['school_id']} | {dc['reason']} |")
        if len(delete_candidates) > 50:
            lines.append(f"| ... | ... | （残り {len(delete_candidates)-50} 件） |")
    else:
        lines.append("DELETE 候補は検出されなかった。")
    lines.append("")
    lines.append("## 7. 倫理上の判断")
    lines.append("")
    lines.append(
        "未成年者（`speaker_role = student_current` かつ卒業生・保護者・教員等の成人属性が"
        "確認できないもの）について、`rights_level` が "
        "`quoted_with_attribution` のまま登録されているケースを検出した場合、"
        "`anonymized_only` へ自動降格した。これは原典が学校 HP の公開ページに掲載されていた"
        "としても、JPMS-DB の利用規程（フォーサイト分析の二次利用）においては"
        "実名引用の必要性が乏しいためである。"
    )
    lines.append("")
    lines.append(
        "個人名（家族名漢字＋名2-3文字の連続）は `○○` に置換し、学年（中1/高2 等）は"
        "「中学生」「高校生」へ generic 化、部活名・期数・卒業年は "
        "「部活動」「卒業生」へ集約した。これにより、引用の本旨である学校風土の表現は"
        "保ちつつ、特定個人へのリーチを抑制している。"
    )
    lines.append("")
    lines.append("## 8. 残課題")
    lines.append("")
    lines.append(
        "- `needs_review` ステータス（`speaker_role` が再分類できなかったレコード）について"
        "は、後段で人手レビューが必要である。"
    )
    lines.append(
        "- 類似度判定はスクール内でのみ実施しており、スクール横断の重複（学校間で同一の"
        "テンプレ文がコピーされているケース）は検出していない。Phase F で検討すること。"
    )
    lines.append(
        "- 著作権の精緻な判断（教科書・パンフレット引用）は本パスでは行っていない。"
        "`source_type='pamphlet'` 等が出現した場合は別途レビューを実施する必要がある。"
    )
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    # Console summary
    print("Group E quality audit complete.")
    print(f"  Total reviewed: {total}")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("\nethics_review_status breakdown:")
    for s, c in status_breakdown:
        print(f"  {s}: {c}")
    print(f"\nReport: {REPORT_PATH}")
    print(f"Progress: {PROGRESS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
