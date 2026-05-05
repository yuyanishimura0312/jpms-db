#!/usr/bin/env python3
"""Team E-1: 家庭関係データ抽出

各校の raw_html_cache/<school_id>/*.html から家庭・保護者関係の言及を抽出し、
Hoover-Dempsey & Sandler 3層モデル + Epstein 6 Types で分類して JSONL に書き出す。

Output:
  - codex_output/team_e1_family.jsonl
  - codex_progress/team_e1.json
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE_DIR = ROOT / "raw_html_cache"
DB_PATH = ROOT / "jpms_v2.db"
OUT_PATH = ROOT / "codex_output" / "team_e1_family.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "team_e1.json"


# -- Classification rules -------------------------------------------------
#
# Each rule maps a regex pattern to (epstein_type, hoover_layer, base_score).
# Matching is greedy; a single sentence may match multiple rules and produce
# multiple records.  Patterns are deliberately conservative (must contain a
# parent/family marker) to avoid false positives from generic school text.

# Anchor terms that must appear in the surrounding sentence to qualify as a
# family-related signal.
FAMILY_ANCHORS = [
    "保護者", "父母", "家庭", "ご家族", "ご家庭", "PTA",
    "父兄", "親御", "お父さま", "お母さま", "三者懇談", "後援会",
    "母の会", "父の会",
]

# Specific signal patterns. Order matters: earlier rules win when a sentence
# matches multiple. Each rule is (regex, epstein_type, hoover_layer, score, label).
RULES: list[tuple[re.Pattern, str, str, int, str]] = [
    # ----- Decision Making — formal governance bodies -----
    (re.compile(r"PTA(?:活動|総会|本部|役員|の活動|の取り組み|会(?:長|議)|通信|から)"), "Decision Making", "効力感", 4, "PTA活動"),
    (re.compile(r"(?:父母と先生の会|父母会|保護者会)(?:総会|役員|本部|の運営|の活動)"), "Decision Making", "効力感", 4, "保護者会組織"),
    (re.compile(r"後援会"), "Decision Making", "効力感", 3, "後援会"),
    (re.compile(r"(?:母の会|父の会|母親委員会)"), "Decision Making", "効力感", 3, "母の会/父の会"),
    (re.compile(r"\bPTA\b"), "Decision Making", "効力感", 2, "PTA言及"),

    # ----- Volunteering — parent participation in school activities -----
    (re.compile(r"保護者(?:による|の)?(?:ボランティア|協力|お手伝い|サポート|支援)"), "Volunteering", "効力感", 4, "保護者ボランティア"),
    (re.compile(r"(?:バザー|文化祭|体育祭|学園祭|学校行事).{0,20}(?:保護者|父母|PTA)"), "Volunteering", "効力感", 3, "行事への保護者参加"),
    (re.compile(r"(?:保護者|父母|PTA).{0,20}(?:バザー|文化祭|体育祭|学園祭|行事|観覧|参観|見学)"), "Volunteering", "効力感", 3, "行事への保護者参加"),
    (re.compile(r"保護者(?:の(?:皆様|方々|方))(?:にも|に)?(?:ご来場|ご観覧|ご参加|お越し)"), "Volunteering", "効力感", 3, "行事保護者来場"),

    # ----- Communicating — bidirectional school↔family channels -----
    (re.compile(r"(?:三者|二者)?面談"), "Communicating", "効力感", 4, "個人面談"),
    (re.compile(r"(?:保護者会|懇談会|学級懇談|地区懇談会)"), "Communicating", "効力感", 3, "保護者会・懇談会"),
    (re.compile(r"(?:学校|学園|授業|公開)(?:説明会|参観日|参観)"), "Communicating", "効力感", 3, "授業参観・説明会"),
    (re.compile(r"(?:学園便り|学校便り|父母通信|PTA通信|保護者向け(?:情報|お知らせ|連絡|ページ))"), "Communicating", "効力感", 2, "保護者向け通信"),
    (re.compile(r"保護者(?:と|への|あて)(?:連絡|お知らせ|情報提供|の(?:意思疎通|連携))"), "Communicating", "効力感", 2, "保護者連絡"),
    (re.compile(r"(?:在校生(?:・|、|や)?)?保護者(?:の(?:方|皆様|皆さま|皆さん))(?:へ|の方へ|向け)"), "Communicating", "効力感", 2, "保護者向け案内"),
    (re.compile(r"(?:中学生|児童|生徒)(?:及び|・|や)保護者(?:の)?(?:方|皆様)?(?:を)?対象"), "Communicating", "効力感", 3, "親子向け説明会"),
    (re.compile(r"入(?:学|試)説明会"), "Communicating", "効力感", 2, "入学説明会"),
    (re.compile(r"オープン(?:キャンパス|スクール)"), "Communicating", "効力感", 2, "オープンキャンパス"),
    (re.compile(r"(?:学校評価|保護者評価|保護者アンケート)"), "Communicating", "効力感", 3, "保護者評価"),

    # ----- Parenting — school supports family upbringing -----
    (re.compile(r"家庭(?:教育|の(?:しつけ|教育|養育|協力))"), "Parenting", "役割構成", 3, "家庭教育"),
    (re.compile(r"(?:子育て|育児)(?:講座|セミナー|相談|支援)"), "Parenting", "役割構成", 4, "子育て講座"),
    (re.compile(r"(?:学校|教員|担任|スクールカウンセラー)(?:による|が)?(?:家庭|保護者)(?:相談|支援|サポート)"), "Parenting", "資源", 3, "家庭相談"),
    (re.compile(r"(?:保護者|父母|ご家庭)(?:向け|対象)(?:の)?(?:講座|セミナー|勉強会|研修)"), "Parenting", "資源", 4, "保護者向け講座"),
    (re.compile(r"家庭(?:的な)(?:雰囲気|校風|環境|空気)"), "Parenting", "役割構成", 2, "家庭的校風"),

    # ----- Learning at Home — home study support -----
    (re.compile(r"家庭学習(?:支援|の(?:習慣|手引き|サポート|指導))?"), "Learning at Home", "資源", 4, "家庭学習"),
    (re.compile(r"宿題(?:や|と)?(?:家庭学習|家庭との連携)"), "Learning at Home", "資源", 3, "宿題・家庭学習"),
    (re.compile(r"(?:保護者|ご家庭)(?:と|への)(?:学習(?:支援|連携|サポート|相談)|学習面の)"), "Learning at Home", "資源", 3, "学習支援連携"),
    (re.compile(r"家庭(?:で|に)(?:課題|宿題|予習|復習)"), "Learning at Home", "資源", 3, "家庭課題"),

    # ----- Collaborating with Community — community ties involving parents -----
    (re.compile(r"(?:地域|コミュニティ).{0,20}(?:保護者|父母|家庭|PTA)"), "Collaborating with Community", "効力感", 3, "地域連携"),
    (re.compile(r"(?:保護者|父母|家庭|PTA).{0,20}(?:地域|コミュニティ)"), "Collaborating with Community", "効力感", 3, "地域連携"),

    # ----- Role construction — school's expectation of family -----
    (re.compile(r"(?:学校|学園)(?:と|・)(?:家庭|保護者)(?:が|の)(?:連携|協力|協働|手を携え|一体)"), "Parenting", "役割構成", 4, "学校家庭連携"),
    (re.compile(r"(?:家庭|保護者)(?:の(?:理解|協力|ご支援|ご支持|ご賛同|ご協力))"), "Parenting", "役割構成", 3, "保護者の理解と協力"),
    (re.compile(r"(?:三位一体|学校・家庭・地域|家庭と学校)"), "Parenting", "役割構成", 4, "三位一体"),
    (re.compile(r"保護者(?:の(?:皆様|皆さま))(?:に(?:は)?|方には).{0,30}(?:感謝|御礼|お礼|御理解|ご理解)"), "Parenting", "役割構成", 3, "保護者への謝意"),
]

# Fallback: any sentence with a family anchor that didn't match a specific
# rule still constitutes a (weak) signal of school↔family interaction. We map
# it to Communicating / 効力感 with the lowest score so the dataset reflects
# overall family-orientation breadth across schools without overweighting it.
FALLBACK = ("Communicating", "効力感", 1, "保護者言及（汎用）")


def html_to_sentences(html: str) -> list[str]:
    """Parse HTML and return a list of sentence-like text fragments."""
    # Prefer lxml (tolerant of malformed numeric char refs); fall back gracefully.
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:  # pragma: no cover
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return []
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # First split by line, then by punctuation
    sentences: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 10:
            continue
        # Split on Japanese sentence punctuation while keeping reasonable length
        parts = re.split(r"(?<=[。！？])\s*", line)
        for p in parts:
            p = p.strip()
            if 10 <= len(p) <= 400:
                sentences.append(p)
    return sentences


def has_family_anchor(s: str) -> bool:
    return any(a in s for a in FAMILY_ANCHORS)


def classify_sentence(sentence: str) -> list[tuple[str, str, int, str]]:
    """Return list of (epstein_type, hoover_layer, score, label) hits."""
    if not has_family_anchor(sentence):
        return []
    seen: set[tuple[str, str]] = set()
    hits: list[tuple[str, str, int, str]] = []
    for pattern, etype, hlayer, score, label in RULES:
        if pattern.search(sentence):
            key = (etype, hlayer)
            if key in seen:
                continue
            seen.add(key)
            hits.append((etype, hlayer, score, label))
    if not hits:
        etype, hlayer, score, label = FALLBACK
        hits.append((etype, hlayer, score, label))
    return hits


def load_url_map(conn: sqlite3.Connection) -> dict[tuple[str, str], str]:
    """Map (school_id, page_slug) -> source_url from school_homepage_assets."""
    cur = conn.execute(
        "SELECT school_id, page_path, full_url FROM school_homepage_assets"
    )
    out: dict[tuple[str, str], str] = {}
    for sid, slug, url in cur.fetchall():
        if sid and slug and url:
            out[(sid, slug)] = url
    return out


def iter_school_files() -> Iterable[tuple[str, str, Path]]:
    for sid_dir in sorted(CACHE_DIR.iterdir()):
        if not sid_dir.is_dir():
            continue
        sid = sid_dir.name
        if not sid.startswith("jpms_s_"):
            continue
        for fp in sorted(sid_dir.glob("*.html")):
            yield sid, fp.stem, fp


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    url_map: dict[tuple[str, str], str] = {}
    if DB_PATH.exists():
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                url_map = load_url_map(conn)
        except sqlite3.Error as e:  # pragma: no cover
            print(f"warn: could not read DB ({e})", file=sys.stderr)

    schools_processed: set[str] = set()
    schools_with_html: set[str] = set()
    records_written = 0
    rule_counts: dict[str, int] = {}
    epstein_counts: dict[str, int] = {}
    hoover_counts: dict[str, int] = {}

    # All schools (even those without HTML) count toward "processed"
    all_schools = sorted(
        d.name
        for d in CACHE_DIR.iterdir()
        if d.is_dir() and d.name.startswith("jpms_s_")
    )

    with OUT_PATH.open("w", encoding="utf-8") as out:
        for sid, slug, fp in iter_school_files():
            schools_with_html.add(sid)
            try:
                html = fp.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print(f"warn: read {fp}: {e}", file=sys.stderr)
                continue
            try:
                sentences = html_to_sentences(html)
            except Exception as e:  # pragma: no cover
                print(f"warn: parse {fp}: {e}", file=sys.stderr)
                sentences = []
            source_url = url_map.get((sid, slug), "")
            seen_evidence: set[str] = set()  # de-dupe per school
            for sent in sentences:
                hits = classify_sentence(sent)
                if not hits:
                    continue
                for etype, hlayer, score, label in hits:
                    dedupe_key = f"{etype}|{hlayer}|{sent[:120]}"
                    if dedupe_key in seen_evidence:
                        continue
                    seen_evidence.add(dedupe_key)
                    record = {
                        "school_id": sid,
                        "epstein_type": etype,
                        "hoover_layer": hlayer,
                        "evidence_text": sent[:400],
                        "context": f"{slug}ページ / {label}",
                        "source_url": source_url,
                        "score": score,
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    records_written += 1
                    rule_counts[label] = rule_counts.get(label, 0) + 1
                    epstein_counts[etype] = epstein_counts.get(etype, 0) + 1
                    hoover_counts[hlayer] = hoover_counts.get(hlayer, 0) + 1
            schools_processed.add(sid)

    progress = {
        "task_id": "team_e1",
        "team": "E-1",
        "subject": "家庭関係データ抽出",
        "total_schools_in_cache": len(all_schools),
        "schools_with_html": len(schools_with_html),
        "schools_processed": len(schools_processed),
        "schools_with_records": sum(
            1 for _ in [None]  # placeholder, computed below
        ),
        "records_written": records_written,
        "epstein_counts": epstein_counts,
        "hoover_counts": hoover_counts,
        "top_rules": sorted(rule_counts.items(), key=lambda x: -x[1])[:10],
        "output_path": str(OUT_PATH.relative_to(ROOT)),
        "status": "completed",
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    # Compute schools_with_records by re-reading the JSONL (cheap)
    schools_with_records: set[str] = set()
    if OUT_PATH.exists():
        with OUT_PATH.open() as f:
            for line in f:
                try:
                    schools_with_records.add(json.loads(line)["school_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    progress["schools_with_records"] = len(schools_with_records)

    PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"Done. schools_processed={len(schools_processed)} "
        f"records={records_written} "
        f"schools_with_records={len(schools_with_records)}"
    )
    print(f"  output: {OUT_PATH}")
    print(f"  progress: {PROGRESS_PATH}")


if __name__ == "__main__":
    main()
