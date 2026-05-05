#!/usr/bin/env python3
"""
JPMS-DB v2 Quality Gate Review Script
Team QM-1: 引用倫理・個人情報保護・著作権 レビューフレームワーク

検査項目:
  1. 引用長  : testimonials の quote_text が 300字以内か
  2. 個人情報: 未成年の個人名・住所・写真情報が含まれていないか
  3. rights_level: 妥当な値が設定されているか
  4. 出典明示: source_url または source_id が空でないか
  5. 著作権  : HP公式ページ以外（個人ブログ等）からの引用がないか

Usage:
  python3 quality_gate_review.py [--input-dir <path>] [--output <path>] [--dry-run]
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# 定数・設定
# ============================================================

BASE_DIR          = Path("/Users/nishimura+/projects/research/jpms-db/v2")
DEFAULT_INPUT_DIR = BASE_DIR / "codex_output"
DEFAULT_OUTPUT    = BASE_DIR / "quality_gate_results.json"
PROGRESS_DIR      = BASE_DIR / "codex_progress"

TESTIMONIAL_TABLE_HINT = {"quote_text", "speaker_role", "rights_level"}
ALUMNI_TABLE_HINT      = {"gf_person_id", "matched_school_id", "evidence_text"}

# 有効な rights_level 値 (schema_v2.sql / PUBLIC.md 準拠)
VALID_RIGHTS_LEVELS = {
    "quoted_with_attribution",
    "anonymized_only",
    "archive_only",
    "cc-by-nc",
    "permission_obtained",
    "quote_paraphrase_only",
    "internal_only",
}

MINOR_ROLES = {"student_current"}
QUOTE_LENGTH_LIMIT = 300

PERSONAL_NAME_PATTERN = re.compile(r"[一-龥々]{2,4}[\s　][一-龥々]{2,4}")
ADDRESS_PATTERN = re.compile(
    r"(東京都|大阪府|京都府|北海道|[^\s]{2,3}県)[^\s]{1,10}(市|区|町|村)|"
    r"\d{1,4}[丁目番地号]"
)
PHOTO_PATTERN = re.compile(r"data:image/|\.jpg|\.jpeg|\.png|\.gif|\.webp", re.IGNORECASE)

NON_OFFICIAL_DOMAIN_PATTERNS = [
    re.compile(r"(ameblo\.jp|amebaownd\.com)", re.IGNORECASE),
    re.compile(r"(blog\.livedoor\.jp|livedoor\.blog)", re.IGNORECASE),
    re.compile(r"(hatena\.ne\.jp|hatenablog\.com)", re.IGNORECASE),
    re.compile(r"(note\.com)", re.IGNORECASE),
    re.compile(r"(twitter\.com|x\.com|instagram\.com|facebook\.com)", re.IGNORECASE),
    re.compile(r"(5ch\.net|2ch\.net|2ch\.sc|open2ch\.net)", re.IGNORECASE),
    re.compile(r"(chanto\.jp|mamari\.jp|shinga\.com|gakkou\.cl-events\.com)", re.IGNORECASE),
    re.compile(r"(jyuken-lab|nakamuramemo)", re.IGNORECASE),
    re.compile(r"(\.cocolog-nifty\.com|jugem\.jp|seesaa\.net|fc2\.com)", re.IGNORECASE),
    re.compile(r"(medium\.com)", re.IGNORECASE),
]


# ============================================================
# 検査ロジック
# ============================================================

def check_quote_length(record):
    issues = []
    qt = record.get("quote_text", "") or ""
    if len(qt) > QUOTE_LENGTH_LIMIT:
        issues.append({
            "check": "quote_length",
            "severity": "medium",
            "message": f"quote_text が {len(qt)} 字（上限 {QUOTE_LENGTH_LIMIT} 字超過）",
            "field": "quote_text",
            "value_preview": qt[:80] + "...",
        })
    return issues


def check_personal_info(record):
    issues = []
    role = record.get("speaker_role", "") or ""
    attr = record.get("speaker_attribute", "") or ""
    qt   = record.get("quote_text", "") or ""
    ctx  = record.get("context", "") or ""

    for field_name, text in [("quote_text", qt), ("context", ctx)]:
        if PHOTO_PATTERN.search(text):
            issues.append({
                "check": "personal_info_photo",
                "severity": "high",
                "message": f"画像参照が含まれている可能性（{field_name}）",
                "field": field_name,
                "value_preview": text[:60],
            })

    if role in MINOR_ROLES:
        for field_name, text in [("quote_text", qt), ("speaker_attribute", attr)]:
            matches = PERSONAL_NAME_PATTERN.findall(text)
            if matches:
                issues.append({
                    "check": "personal_info_minor_name",
                    "severity": "critical",
                    "message": f"未成年ロール({role})に個人名パターンが含まれている可能性: {matches[:3]}",
                    "field": field_name,
                    "value_preview": text[:80],
                })
        for field_name, text in [("quote_text", qt), ("context", ctx)]:
            if ADDRESS_PATTERN.search(text):
                issues.append({
                    "check": "personal_info_minor_address",
                    "severity": "high",
                    "message": f"未成年ロール({role})に住所的文字列が含まれている可能性（{field_name}）",
                    "field": field_name,
                    "value_preview": text[:80],
                })
    return issues


def check_rights_level(record):
    issues = []
    rl = record.get("rights_level") or ""
    if not rl:
        issues.append({
            "check": "rights_level_missing",
            "severity": "high",
            "message": "rights_level が未設定",
            "field": "rights_level",
            "value_preview": repr(rl),
        })
    elif rl not in VALID_RIGHTS_LEVELS:
        issues.append({
            "check": "rights_level_invalid",
            "severity": "medium",
            "message": f"rights_level の値 '{rl}' が規定外",
            "field": "rights_level",
            "value_preview": rl,
        })
    return issues


def check_source_attribution(record):
    issues = []
    src_url = record.get("source_url", "") or ""
    src_id  = record.get("source_id", "") or ""
    if not src_url.strip() and not src_id.strip():
        issues.append({
            "check": "source_missing",
            "severity": "high",
            "message": "source_url と source_id が両方未設定（出典不明）",
            "field": "source_url / source_id",
            "value_preview": "(empty)",
        })
    return issues


def check_copyright_source(record):
    issues = []
    src_url = record.get("source_url", "") or ""
    if not src_url:
        return issues
    for pattern in NON_OFFICIAL_DOMAIN_PATTERNS:
        if pattern.search(src_url):
            issues.append({
                "check": "copyright_non_official_source",
                "severity": "high",
                "message": f"非公式ソース（個人ブログ等）からの引用の可能性: {src_url}",
                "field": "source_url",
                "value_preview": src_url,
            })
            break
    return issues


# ============================================================
# ファイル種別の判定
# ============================================================

def detect_table_type(records):
    if not records:
        return "unknown"
    keys = set(records[0].keys())
    if TESTIMONIAL_TABLE_HINT & keys:
        return "testimonials"
    if ALUMNI_TABLE_HINT & keys:
        return "alumni"
    return "unknown"


# ============================================================
# レコード単位のレビュー
# ============================================================

def review_record(record, table_type, index):
    issues = []
    if table_type == "testimonials":
        issues += check_quote_length(record)
        issues += check_personal_info(record)
        issues += check_rights_level(record)
        issues += check_source_attribution(record)
        issues += check_copyright_source(record)
    elif table_type == "alumni":
        issues += check_source_attribution(record)

    severities = [i["severity"] for i in issues]
    if "critical" in severities:
        status = "rejected"
    elif issues:
        status = "flagged"
    else:
        status = "approved"

    return {"index": index, "status": status, "issues": issues}


# ============================================================
# ファイル単位のレビュー
# ============================================================

def review_file(jsonl_path):
    records, parse_errors = [], []
    with open(jsonl_path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError as e:
                parse_errors.append({"lineno": lineno, "error": str(e), "raw_preview": raw[:80]})

    table_type = detect_table_type(records)
    results = [review_record(r, table_type, i) for i, r in enumerate(records)]

    approved = sum(1 for r in results if r["status"] == "approved")
    flagged  = sum(1 for r in results if r["status"] == "flagged")
    rejected = sum(1 for r in results if r["status"] == "rejected")

    issue_summary = [
        {"record_index": r["index"], "status": r["status"], "issues": r["issues"]}
        for r in results if r["issues"]
    ]

    return {
        "file": jsonl_path.name,
        "table_type": table_type,
        "total": len(records),
        "approved": approved,
        "flagged": flagged,
        "rejected": rejected,
        "parse_errors": parse_errors,
        "issues": issue_summary,
    }


# ============================================================
# サンプルデータ生成
# ============================================================

def build_sample_data(output_dir):
    """各検査項目を網羅した代表的なサンプルレコードを生成する"""
    samples = [
        # OK レコード
        {
            "school_id": "jpms_s_0001", "speaker_role": "principal", "speaker_attribute": "校長",
            "quote_text": "本校は建学の精神に基づき、生徒一人ひとりの可能性を最大限に引き出す教育を行っています。",
            "source_url": "https://example-school.ed.jp/about/", "rights_level": "quoted_with_attribution",
        },
        # 検査1: 引用長超過 (medium)
        {
            "school_id": "jpms_s_0002", "speaker_role": "principal", "speaker_attribute": "校長",
            "quote_text": "ア" * 310,
            "source_url": "https://example-school2.ed.jp/principal/", "rights_level": "quoted_with_attribution",
        },
        # 検査2: 未成年ロール + 氏名パターン (critical)
        {
            "school_id": "jpms_s_0003", "speaker_role": "student_current",
            "speaker_attribute": "中学3年 田中 花子",
            "quote_text": "学校生活はとても充実しています。",
            "source_url": "https://example-school3.ed.jp/students/", "rights_level": "anonymized_only",
        },
        # 検査3: rights_level 欠損 (high)
        {
            "school_id": "jpms_s_0004", "speaker_role": "principal", "speaker_attribute": "校長",
            "quote_text": "教育の充実を目指しています。",
            "source_url": "https://example-school4.ed.jp/", "rights_level": "",
        },
        # 検査4: source_url / source_id 両方欠損 (high)
        {
            "school_id": "jpms_s_0005", "speaker_role": "teacher", "speaker_attribute": "英語担当教諭",
            "quote_text": "英語教育に力を入れています。",
            "source_url": "", "rights_level": "quoted_with_attribution",
        },
        # 検査5: 個人ブログからの引用 (high)
        {
            "school_id": "jpms_s_0006", "speaker_role": "parent", "speaker_attribute": "保護者",
            "quote_text": "子どもを通わせて満足しています。",
            "source_url": "https://ameblo.jp/some-parent-blog/entry-12345.html",
            "rights_level": "quoted_with_attribution",
        },
        # 検査3: rights_level が規定外の値 (medium)
        {
            "school_id": "jpms_s_0007", "speaker_role": "principal", "speaker_attribute": "校長",
            "quote_text": "本校の教育方針を説明します。",
            "source_url": "https://example-school7.ed.jp/", "rights_level": "public_domain",
        },
        # OK レコード（source_url のみ）
        {
            "school_id": "jpms_s_0008", "speaker_role": "principal", "speaker_attribute": "校長",
            "quote_text": "生徒の成長を見守ることが私の使命です。",
            "source_url": "https://example-school8.ac.jp/about/", "rights_level": "quoted_with_attribution",
        },
    ]
    sample_path = output_dir / "team_sample_qm1_test.jsonl"
    with open(sample_path, "w", encoding="utf-8") as f:
        for rec in samples:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[INFO] サンプルデータを生成: {sample_path} ({len(samples)} レコード)")
    return sample_path


# ============================================================
# メイン処理
# ============================================================

def run_review(input_dir, output_path, dry_run=False):
    jsonl_files = sorted(input_dir.glob("team_*.jsonl"))
    generated_sample = False

    if not jsonl_files:
        print("[WARN] codex_output/ に team_*.jsonl が存在しません。サンプルデータで動作確認を行います。")
        sample_path = build_sample_data(input_dir)
        jsonl_files = [sample_path]
        generated_sample = True

    reviewed_files = []
    for jsonl_path in jsonl_files:
        print(f"[INFO] レビュー中: {jsonl_path.name} ...")
        result = review_file(jsonl_path)
        reviewed_files.append(result)
        rate = result["approved"] / result["total"] * 100 if result["total"] else 0
        print(
            f"       total={result['total']}, approved={result['approved']}, "
            f"flagged={result['flagged']}, rejected={result['rejected']}, "
            f"承認率={rate:.1f}%"
        )

    total_records  = sum(r["total"]    for r in reviewed_files)
    total_approved = sum(r["approved"] for r in reviewed_files)
    total_flagged  = sum(r["flagged"]  for r in reviewed_files)
    total_rejected = sum(r["rejected"] for r in reviewed_files)
    approved_rate  = total_approved / total_records if total_records else 0.0

    output = {
        "reviewed_files": reviewed_files,
        "summary": {
            "total":              total_records,
            "approved":           total_approved,
            "flagged":            total_flagged,
            "rejected":           total_rejected,
            "approved_rate":      round(approved_rate, 4),
            "input_dir":          str(input_dir),
            "sample_data_used":   generated_sample,
        },
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n[INFO] 結果を出力: {output_path}")
    else:
        print("\n[DRY-RUN] 出力はスキップされました。")

    return output


def write_progress_log(result, progress_dir):
    progress_dir.mkdir(parents=True, exist_ok=True)
    log = {
        "task_id":           "team_qm1",
        "role":              "quality_gate_review",
        "checks":            ["quote_length", "personal_info", "rights_level", "source_attribution", "copyright_source"],
        "reviewed_files":    len(result["reviewed_files"]),
        "total_records":     result["summary"]["total"],
        "approved":          result["summary"]["approved"],
        "flagged":           result["summary"]["flagged"],
        "rejected":          result["summary"]["rejected"],
        "approved_rate":     result["summary"]["approved_rate"],
        "sample_data_used":  result["summary"]["sample_data_used"],
        "ts":                result["ts"],
    }
    log_path = progress_dir / "team_qm1.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 進捗ログを更新: {log_path}")


# ============================================================
# CLI エントリーポイント
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(description="JPMS-DB v2 QM-1 Quality Gate Review")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR,
                        help="JSONL ファイルが格納されたディレクトリ（デフォルト: codex_output/）")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="レビュー結果の出力先 JSON（デフォルト: quality_gate_results.json）")
    parser.add_argument("--dry-run", action="store_true",
                        help="結果ファイルを書き込まずにレビューのみ実行")
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 60)
    print("JPMS-DB v2 / Team QM-1 Quality Gate Review")
    print("=" * 60)
    print(f"  入力ディレクトリ : {args.input_dir}")
    print(f"  出力ファイル     : {args.output}")
    print(f"  ドライラン       : {args.dry_run}")
    print()

    result = run_review(args.input_dir, args.output, dry_run=args.dry_run)
    write_progress_log(result, PROGRESS_DIR)

    s = result["summary"]
    print("\n===== 集計 =====")
    print(f"  総レコード数    : {s['total']}")
    print(f"  承認            : {s['approved']}")
    print(f"  要確認(flagged) : {s['flagged']}")
    print(f"  却下(rejected)  : {s['rejected']}")
    print(f"  承認率          : {s['approved_rate']*100:.1f}%")

    has_critical = any(
        any(i["severity"] == "critical" for issue_rec in fr["issues"] for i in issue_rec["issues"])
        for fr in result["reviewed_files"]
    )
    if has_critical:
        print("\n[CRITICAL] Critical 判定のレコードが存在します。即時対応が必要です。")
        sys.exit(2)
    elif s["flagged"] > 0 or s["rejected"] > 0:
        print("\n[WARN] 要確認・却下レコードがあります。quality_gate_results.json を確認してください。")
        sys.exit(1)
    else:
        print("\n[PASS] 全レコードが品質ゲートを通過しました。")
        sys.exit(0)


if __name__ == "__main__":
    main()
