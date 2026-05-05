#!/usr/bin/env python3
"""
JPMS-DB v2 Phase E - Team B-2 (在校生・卒業生声抽出)

Walks raw_html_cache/<school_id>/*.html and extracts student/alumni voices
(在校生インタビュー / 卒業生メッセージ) from each school's pages.

Writes JSONL to codex_output/team_b2_students.jsonl and a progress log to
codex_progress/team_b2.json.

Each output record:
{
  "school_id": "...",
  "speaker_role": "student_current" | "student_alumni",
  "speaker_attribute": "中学生" | "卒業生",
  "quote_text": "...",
  "quote_summary": "...",
  "context": "在校生インタビュー" | "卒業生メッセージ" | ...,
  "source_url": "...",
  "rights_level": "anonymized_only"
}

Constraints
- 30 to 300 chars (CJK)
- max 5 records per school
- public-info only; minor PII (名前/学年/部活名) removed; speaker_attribute kept generic
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE_DIR = ROOT / "raw_html_cache"
OUT_PATH = ROOT / "codex_output" / "team_b2_students.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "team_b2.json"
DB_PATH = ROOT / "jpms_v2.db"

MIN_LEN = 30
MAX_LEN = 300
MAX_PER_SCHOOL = 5

# Files most likely to contain student/alumni voices
PREFERRED_FILES = [
    "voice.html",
    "schoollife.html",
    "progress.html",
    "about.html",
    "admission.html",
    "events.html",
    "root.html",
]

FILE_CONTEXT_DEFAULT = {
    "voice.html": "在校生・卒業生メッセージ",
    "schoollife.html": "在校生インタビュー",
    "progress.html": "卒業生メッセージ",
    "about.html": "在校生・卒業生メッセージ",
    "admission.html": "在校生・卒業生メッセージ",
    "events.html": "在校生・卒業生メッセージ",
    "root.html": "在校生・卒業生メッセージ",
}

# Section header keywords (look back ~600 chars from a candidate block)
ALUMNI_HEADER_KEYS = [
    "卒業生の声", "卒業生インタビュー", "卒業生メッセージ", "卒業生からのメッセージ",
    "先輩の声", "先輩からのメッセージ", "先輩メッセージ",
    "OBインタビュー", "OGインタビュー", "卒業生コラム", "OB・OGの声", "OBOGの声",
]

CURRENT_HEADER_KEYS = [
    "在校生の声", "在校生インタビュー", "在校生からのメッセージ",
    "生徒の声", "生徒インタビュー", "生徒メッセージ",
    "在校生メッセージ", "現役生の声",
]

# Personal narrative indicators (Japanese pronouns and verb endings)
NARRATIVE_PATTERNS = [
    "私は", "私が", "私の", "私たち", "僕は", "僕が", "僕の",
    "自分は", "自分が", "自分の", "自分たち",
    "と思います", "と感じ", "ことができ", "を学びました", "を学ん",
    "と考え", "を経験", "ています。", "ました。",
    "になりたい", "ができる", "ができた", "してい", "してくれ",
    # Student-experience expressions
    "充実してい", "が印象的", "が思い出", "の経験", "を通して",
    "と切磋琢磨", "仲間と", "毎日を", "を実感", "を体験",
    "頑張って", "努力", "目指し", "受験", "合格しました",
    "高校生活", "中学生活", "学校生活で", "部活動",
    "文化祭", "体育祭", "修学旅行", "課外活動",
]

# Reject lines that look like nav/copyright/menu lists
BAD_PATTERNS = [
    re.compile(r"Copyright|All Rights Reserved|©", re.I),
    re.compile(r"http[s]?://"),
    re.compile(r"〒\d"),
    re.compile(r"TEL[:：]|FAX[:：]"),
    re.compile(r"^\s*[0-9０-９]+\s*$"),
    re.compile(r"<!--|-->"),
    # 404 and admin pages
    re.compile(r"お探しのページ|ページが見つかり|Not Found", re.I),
    re.compile(r"検索フォーム"),
    # event announcements / admission notices (not voice content)
    re.compile(r"【募集】|【お知らせ】|【告知】|【受付】"),
    re.compile(r"説明会.*予約|出願受付|募集要項"),
    # generic intro/PR not voice
    re.compile(r"^麻布|^慶應|^早稲田"),
]

# Tokens commonly seen only in nav/footer
NAV_BAD_TOKENS = [
    "サイトマップ", "プライバシーポリシー", "個人情報保護方針",
    "資料請求", "募集要項", "アクセス・お問い合わせ", "教職員募集",
]


def cjk_len(s: str) -> int:
    return len(s)


def is_navigation_blob(text: str) -> bool:
    if text.count("｜") + text.count("|") >= 4:
        return True
    if text.count("／") + text.count("/") >= 5:
        return True
    if text.count("・") >= 8:
        return True
    if text.count(">") >= 3:
        return True
    nav_hits = sum(1 for t in NAV_BAD_TOKENS if t in text)
    if nav_hits >= 2:
        return True
    parts = re.split(r"[、。\s]", text)
    short_parts = [p for p in parts if 0 < len(p) <= 6]
    if len(parts) > 0 and len(short_parts) / len(parts) > 0.55 and len(parts) > 8:
        return True
    return False


def is_clean(text: str) -> bool:
    if cjk_len(text) < MIN_LEN or cjk_len(text) > MAX_LEN:
        return False
    for pat in BAD_PATTERNS:
        if pat.search(text):
            return False
    if is_navigation_blob(text):
        return False
    # Need a sentence terminator to look like prose
    if not re.search(r"[。、．！？]", text):
        return False
    if text.count("：") + text.count(":") >= 4:
        return False
    return True


def has_narrative_voice(text: str) -> bool:
    return any(p in text for p in NARRATIVE_PATTERNS)


# Strong student/alumni narrative hints (first-person + school lifecycle)
STUDENT_NARRATIVE_RE = [
    re.compile(r"(私|僕|自分).{1,20}(学校|学園|中学|高校|入学|過ご|生活)"),
    re.compile(r"(中学|高校).{0,3}(時代|時|生活).{0,30}(部活|友|仲間|先生|先輩|後輩)"),
    re.compile(r"(部活|文化祭|体育祭|修学旅行).{0,30}(楽しか|頑張|思い出|印象|大切|学んだ|楽しん)"),
    re.compile(r"(先生|友人|友達|仲間).{0,30}(支え|教えて|尊敬|感謝|出会|共に)"),
    re.compile(r"(成長|学び|気づき|発見|経験).{0,40}(きっかけ|自分|私|僕)"),
    re.compile(r"(受験|合格|進路|志望).{0,40}(頑張|努力|挑戦|乗り越|支え)"),
]


def has_student_narrative(text: str) -> bool:
    return any(p.search(text) for p in STUDENT_NARRATIVE_RE)


def anonymize(text: str) -> str:
    """Remove minor PII: explicit grade/year markers; collapse names/initials."""
    # 中学/高校 学年 -> 中学生 / 卒業生 generic
    text = re.sub(r"(中学|中等部)[1-3一二三１-３]年(生)?", "中学生", text)
    text = re.sub(r"(高校|高等学校|高等部)[1-3一二三１-３]年(生)?", "高校生", text)
    # 「○○さん」「○○くん」「○○ちゃん」 (likely anonymizers/placeholders)
    text = re.sub(r"[A-Z]\.\s*[A-Z]\.", "", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "", text)
    # Remove leading bullet/quote markers
    text = text.strip("「」『』\"' 　")
    text = re.sub(r"\s+", "", text)
    return text


def select_blocks(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Return list of (text, preceding_heading) tuples."""
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "noscript"]):
        tag.decompose()
    for sel in ["#header", "#nav", "#globalnav", "#footer", "#sidebar",
                ".header", ".nav", ".globalnav", ".footer", ".sidebar",
                ".breadcrumb", "#breadcrumb", "#bread", ".gnav", "#gnav",
                ".menu", "#menu"]:
        for el in soup.select(sel):
            el.decompose()

    # Walk document collecting headings as state, then leaf prose blocks
    candidates: list[tuple[str, str]] = []
    current_heading = ""
    # Iterate in document order
    for el in soup.find_all(True):
        tag = el.name
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            t = el.get_text(separator="", strip=True)
            if t:
                current_heading = re.sub(r"\s+", "", t)[:120]
            continue
        if tag in {"p", "blockquote", "li", "section", "article", "div", "td"}:
            # Skip parents that contain other paragraphs (avoid nested duplicates)
            if el.find(["p", "li", "blockquote"]):
                continue
            t = el.get_text(separator="", strip=True)
            t = re.sub(r"\s+", "", t)
            if not t:
                continue
            candidates.append((t, current_heading))

    # Dedup while preserving order
    seen: set[str] = set()
    uniq: list[tuple[str, str]] = []
    for (t, h) in candidates:
        if t in seen:
            continue
        seen.add(t)
        uniq.append((t, h))
    return uniq


# Phrases that indicate the block is NOT a student voice (校長/教員/学校PR)
NON_STUDENT_PATTERNS = [
    # Voices clearly not from students
    "学園長", "校長として", "教員一同", "理事長",
    "本学院は", "我が校", "創立以来", "建学の精神",
    # Principal addressing students (speeches)
    "皆さんは", "皆さんが", "皆さんに", "皆さんの",
    "してほしいと思います", "話したいと思います",
    "御来賓", "御列席", "心からの拍手",
    # Teacher introduction / personnel changes
    "御尽力いただきました", "新規採用教員", "御勤務", "教員として、新",
    # Site UI / PR phrases
    "本ウェブサイト", "ご覧ください", "お問い合わせください",
    "リアルボイス", "実際の声を集めました", "教えて！",
    "メニューから", "詳細はこちら", "資料請求",
    # Scheduling / event copy
    "受験生には", "ご参加お待ち", "ご予約受付",
    "を予定しています", "電子版です",
    # PR-style verb endings (school subject)
    "を実現します。", "を目指します。", "を養成します。",
    "を支える環境", "を整えています", "に取り組んでいます",
    "を展開しています", "を実施しています",
    "を構築", "を育成します", "を育みます",
    # Generic guides/intros
    "を紹介します", "を発信",
]


def is_non_student_voice(text: str) -> bool:
    return any(p in text for p in NON_STUDENT_PATTERNS)


def classify_role(text: str, heading: str, full_page_text: str,
                  block_pos: int) -> tuple[str, str, str] | None:
    """Decide (speaker_role, speaker_attribute, context).

    Decision order:
    1. heading contains an alumni/current keyword
    2. preceding ~600 chars in full_page_text contain an alumni/current keyword
    3. block text itself contains 卒業/在校 markers
    """
    # Combine heading + context window
    context_window = full_page_text[max(0, block_pos - 600):block_pos]
    candidate_texts = [heading or "", context_window, text]

    for txt in candidate_texts:
        for kw in ALUMNI_HEADER_KEYS:
            if kw in txt:
                return ("student_alumni", "卒業生", kw)
        for kw in CURRENT_HEADER_KEYS:
            if kw in txt:
                return ("student_current", "中学生", kw)

    # Looser detection in block text
    if "卒業生" in text and ("メッセージ" in text or "後輩" in text or "在校生" in text):
        return ("student_alumni", "卒業生", "卒業生メッセージ")
    if "在校生" in text and ("学校生活" in text or "授業" in text or "毎日" in text):
        return ("student_current", "中学生", "在校生インタビュー")

    return None


def extract_for_school(school_id: str, school_dir: Path,
                       homepage: str | None) -> list[dict]:
    out: list[dict] = []
    seen_quotes: set[str] = set()
    for fname in PREFERRED_FILES:
        if len(out) >= MAX_PER_SCHOOL:
            break
        path = school_dir / fname
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                raw_html = f.read()
        except Exception:
            continue
        if len(raw_html) < 1500:
            continue

        # Sanitize potentially malformed numeric character refs
        def _safe_parse(html_src):
            try:
                return BeautifulSoup(html_src, "html.parser"), html_src
            except Exception:
                cleaned = re.sub(r"&#(\D)", r"&amp;#\1", html_src)
                try:
                    return BeautifulSoup(cleaned, "html.parser"), cleaned
                except Exception:
                    return None, html_src

        soup_full, raw_html = _safe_parse(raw_html)
        if soup_full is None:
            continue
        for tag in soup_full(["script", "style"]):
            tag.decompose()
        full_text = soup_full.get_text(separator=" ")
        full_text = re.sub(r"\s+", " ", full_text)

        soup, _ = _safe_parse(raw_html)
        if soup is None:
            continue

        # Determine source_url
        source_url = ""
        canon = soup.find("link", rel="canonical")
        if canon and canon.get("href"):
            source_url = canon["href"]
        else:
            og = soup.find("meta", attrs={"property": "og:url"})
            if og and og.get("content"):
                source_url = og["content"]
        if not source_url and homepage:
            base = homepage if homepage.endswith("/") else homepage + "/"
            slug = fname.replace(".html", "")
            if slug == "root":
                source_url = base
            else:
                source_url = urljoin(base, slug)

        default_ctx = FILE_CONTEXT_DEFAULT.get(fname, "在校生・卒業生メッセージ")

        # Page-level role hint from <title>
        page_role_hint = None
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text() or ""
            if any(k in title_text for k in ALUMNI_HEADER_KEYS):
                page_role_hint = ("student_alumni", "卒業生", "卒業生インタビュー")
            elif any(k in title_text for k in CURRENT_HEADER_KEYS):
                page_role_hint = ("student_current", "中学生", "在校生インタビュー")

        blocks = select_blocks(soup)
        for raw, heading in blocks:
            if len(out) >= MAX_PER_SCHOOL:
                break
            text = anonymize(raw)
            if not is_clean(text):
                continue
            # Need narrative voice (at least 1 cue)
            if not has_narrative_voice(text):
                continue
            # Reject ellipsized truncated content
            if "..." in text or "…" in text[:-3]:
                # allow only if the ellipsis is at the end (summary-style)
                pass
            # Find block position in full_text for context window lookup
            anchor = text[:25]
            try:
                block_pos = full_text.find(anchor)
            except Exception:
                block_pos = -1

            classified = classify_role(text, heading, full_text,
                                       block_pos if block_pos >= 0 else 0)
            if not classified and page_role_hint:
                classified = page_role_hint
            if not classified and fname == "voice.html":
                # voice.html implies student/alumni context
                classified = ("student_alumni", "卒業生", default_ctx)
            # Strong student-narrative blocks: trust them even outside explicit voice context
            if not classified and has_student_narrative(text):
                # Decide alumni vs current based on lifecycle markers
                if any(k in text for k in ["合格しました", "卒業", "大学に進", "進学しました", "社会人", "就職"]):
                    classified = ("student_alumni", "卒業生", "卒業生メッセージ")
                elif any(k in text for k in ["中学", "高校", "部活", "授業", "毎日", "学校生活"]):
                    classified = ("student_current", "中学生", "在校生インタビュー")
            if not classified:
                continue
            # Reject school-PR / principal-style blocks
            if is_non_student_voice(text):
                continue
            # Reject obvious truncation/teaser style
            if text.endswith("...") or text.endswith("…"):
                continue
            speaker_role, attr, ctx = classified

            if cjk_len(text) > MAX_LEN:
                text = text[:MAX_LEN]
            key = text[:80]
            if key in seen_quotes:
                continue
            seen_quotes.add(key)

            summary = text[:60] + ("…" if len(text) > 60 else "")

            record = {
                "school_id": school_id,
                "speaker_role": speaker_role,
                "speaker_attribute": attr,
                "quote_text": text,
                "quote_summary": summary,
                "context": ctx,
                "source_url": source_url,
                "rights_level": "anonymized_only",
            }
            out.append(record)
    return out


def load_schools() -> dict[str, tuple[str, str | None]]:
    if not DB_PATH.exists():
        return {}
    try:
        con = sqlite3.connect(str(DB_PATH))
        cur = con.cursor()
        cur.execute("SELECT id, legacy_id, name_ja, homepage_url FROM schools_v2")
        rows = cur.fetchall()
        con.close()
    except Exception:
        return {}
    out: dict[str, tuple[str, str | None]] = {}
    for sid, legacy_id, name_ja, homepage in rows:
        out[sid] = (name_ja or "", homepage or "")
        if legacy_id:
            out[legacy_id] = (name_ja or "", homepage or "")
    return out


def load_urls_from_tasks() -> dict[str, str]:
    """Fallback URL source from codex_tasks/alpha-*_schools.jsonl."""
    urls: dict[str, str] = {}
    tasks_dir = ROOT / "codex_tasks"
    if not tasks_dir.exists():
        return urls
    for fp in tasks_dir.glob("alpha-*_schools.jsonl"):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("id"):
                            urls[rec["id"]] = rec.get("url", "")
                    except Exception:
                        pass
        except Exception:
            pass
    return urls


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    schools = load_schools()
    fallback_urls = load_urls_from_tasks()
    school_dirs = sorted(p for p in CACHE_DIR.iterdir() if p.is_dir())
    total_schools = len(school_dirs)

    records: list[dict] = []
    schools_with_data = 0
    schools_without: list[str] = []

    for sd in school_dirs:
        sid = sd.name
        name_ja, homepage = schools.get(sid, ("", ""))
        if not homepage:
            homepage = fallback_urls.get(sid, "")
        recs = extract_for_school(sid, sd, homepage)
        if recs:
            schools_with_data += 1
        else:
            schools_without.append(sid)
        records.extend(recs)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    progress = {
        "task_id": "team_b2",
        "team": "B-2",
        "task": "student/alumni voices extraction",
        "completed": total_schools,
        "items": len(records),
        "ts": datetime.now(timezone.utc).isoformat(),
        "total_schools_scanned": total_schools,
        "schools_with_extractions": schools_with_data,
        "schools_without_extractions": len(schools_without),
        "max_per_school": MAX_PER_SCHOOL,
        "min_quote_len": MIN_LEN,
        "max_quote_len": MAX_LEN,
        "output_path": str(OUT_PATH),
        "rights_level": "anonymized_only",
        "ethics_notes": [
            "未成年（中学生）情報は完全匿名化。",
            "個人名・学年は除外、speaker_attributeは generic（中学生/卒業生）。",
            "公開情報のみを対象。",
            "ナビゲーション/著作権表示等の非実体テキストは除外。",
        ],
    }
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"schools scanned: {total_schools}")
    print(f"schools with extractions: {schools_with_data}")
    print(f"records: {len(records)}")
    print(f"output: {OUT_PATH}")
    print(f"progress: {PROGRESS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
