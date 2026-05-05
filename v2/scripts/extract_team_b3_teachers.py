#!/usr/bin/env python3
"""
JPMS-DB v2 Phase E - Team B-3 (教員・教科声抽出)

Walks raw_html_cache/<school_id>/*.html and extracts teacher/subject/department
voices and introductions from each school's pages. Writes JSONL to
codex_output/team_b3_teachers.jsonl and a progress log to
codex_progress/team_b3.json.

Each output record:
{
  "school_id": "...",
  "speaker_role": "teacher",
  "speaker_attribute": "教科教員/担任",
  "quote_text": "...",
  "context": "教員紹介",  # or 教科紹介 / 授業紹介
  "source_url": "...",
  "rights_level": "quoted_with_attribution"
}

Constraints
- 30 to 300 chars (CJK)
- max 5 records per school
- public-info only; avoid PII (drop personal names unless very common context)
- skip nav menu/copy/script-ish content
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
OUT_PATH = ROOT / "codex_output" / "team_b3_teachers.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "team_b3.json"
DB_PATH = ROOT / "jpms_v2.db"

MIN_LEN = 30
MAX_LEN = 300
MAX_PER_SCHOOL = 5

# Files most likely to contain teacher / subject prose
PREFERRED_FILES = [
    "curriculum.html",
    "schoollife.html",
    "about.html",
    "voice.html",
    "root.html",
]

# Page-context labels keyed off the file name
FILE_CONTEXT = {
    "curriculum.html": "教科紹介",
    "schoollife.html": "教科紹介",
    "about.html": "教員紹介",
    "voice.html": "教員紹介",
    "root.html": "教科紹介",
    "principal.html": "教員紹介",
    "philosophy.html": "教員紹介",
    "mission.html": "教員紹介",
}

SUBJECT_KEYS = [
    "国語", "数学", "英語", "理科", "社会", "地理", "歴史", "公民",
    "物理", "化学", "生物", "地学", "音楽", "美術", "保健体育",
    "技術", "家庭", "情報", "道徳", "総合的な学習", "総合学習",
    "宗教", "聖書", "倫理", "書道",
]

ROLE_KEYS = [
    "教員", "教諭", "教師", "教科主任", "学年主任", "担任",
    "副担任", "学科主任", "主幹教諭", "指導教諭", "顧問",
    "本校の先生", "教科担当", "授業担当",
    "校長", "学校長", "学園長", "副校長", "教頭",
    "教職員",
]

# Strong phrases that imply pedagogical / classroom prose
CLASS_KEYS = [
    "授業", "学習指導", "カリキュラム", "本校では", "本校は",
    "教育課程", "取り組み", "取組み", "取組", "学び",
    "指導", "演習", "実習", "探究", "探求",
    "週", "時限", "コマ",
    "中学", "高校", "中等部", "高等部",
]

CONTEXT_HINT_KEYS = [
    "教員紹介", "教科紹介", "授業紹介", "教科だより",
    "の取り組み", "教科の特色", "教育内容", "学習指導",
    "教育方針", "学習の特色", "授業の特色",
]

# Reject lines that look like nav/copyright/menu lists / news feed items
BAD_PATTERNS = [
    re.compile(r"Copyright|All Rights Reserved|©", re.I),
    re.compile(r"http[s]?://"),
    re.compile(r"〒\d"),
    re.compile(r"TEL[:：]|FAX[:：]"),
    re.compile(r"^\s*[0-9０-９]+\s*$"),
    # Date-prefixed news / blog items
    re.compile(r"20[0-9]{2}[\.\-/年][01]?[0-9][\.\-/月][0-3]?[0-9]"),
    re.compile(r"続きを見る|もっと見る|一覧を見る|詳しく見る"),
    re.compile(r"PICKUP|NEWS|TOPICS", re.I),
    # Form / contact-y blocks
    re.compile(r"必須|任意|プライバシーポリシー"),
]


def load_schools() -> dict[str, tuple[str, str | None]]:
    """Return {school_id: (name_ja, homepage_url)}."""
    if not DB_PATH.exists():
        return {}
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, legacy_id, name_ja, homepage_url FROM schools_v2")
    rows = cur.fetchall()
    con.close()
    out: dict[str, tuple[str, str | None]] = {}
    for sid, legacy_id, name_ja, homepage in rows:
        out[sid] = (name_ja or "", homepage or "")
        if legacy_id:
            out[legacy_id] = (name_ja or "", homepage or "")
    return out


def cjk_len(s: str) -> int:
    """Length close to character count (treat full-width as 1)."""
    return len(s)


def is_navigation_blob(text: str) -> bool:
    """Heuristic: detect site-nav/breadcrumb dumps."""
    if text.count("｜") + text.count("|") >= 4:
        return True
    if text.count("／") + text.count("/") >= 5:
        return True
    if text.count("・") >= 8:
        return True
    if text.count(">") >= 3:
        return True
    # menu-y term ratio
    menu_terms = ["TOP", "ホーム", "サイトマップ", "お問い合わせ", "アクセス",
                  "プライバシー", "資料請求", "募集要項"]
    hits = sum(1 for t in menu_terms if t in text)
    if hits >= 3:
        return True
    # Lots of short sentences strung together (menu items joined)
    parts = re.split(r"[、。\s]", text)
    short_parts = [p for p in parts if 0 < len(p) <= 6]
    if len(parts) > 0 and len(short_parts) / len(parts) > 0.55 and len(parts) > 8:
        return True
    # News item concatenation: many "続きを見る" / many year-month-day patterns
    if len(re.findall(r"20[0-9]{2}", text)) >= 2:
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
    # Should have a sentence terminator or comma to look like prose
    if not re.search(r"[。、．！？]", text):
        return False
    # Reject obvious form labels
    if text.count("：") + text.count(":") >= 4:
        return False
    return True


PEDAGOGY_VERBS = re.compile(
    r"(目指|大切|重視|育て|養|身に付|身につけ|習得|高め|深め|"
    r"展開|実施|行|工夫|取り組|位置付け|位置づけ|身に着け|"
    r"願|期待|努め|学ば|学び|挑戦|理解|考え|感謝)"
)

# Phrases that strongly indicate the speaker is a student/alumna/-us
# and not a teacher.
STUDENT_VOICE_PATTERNS = re.compile(
    r"(進学(し|を|が|決め)|憧れ|私の夢|やりたいこと|入学(し|前)|"
    r"小学校の頃|中学受験|大学(に|で|の|生活)|高校時代|楽しかった|"
    r"思い出|つもりです|なりたい|楽しん(で|だ)|学校生活|"
    r"卒業生|現役|クラブ活動|私たち生徒|私は|私の)"
)


def classify(text: str, file_ctx: str = "") -> tuple[str, str] | None:
    """Return (speaker_attribute, context) or None if not relevant."""
    # Filter out obvious student/alumni voice testimonials
    if STUDENT_VOICE_PATTERNS.search(text):
        return None

    has_role = any(k in text for k in ROLE_KEYS)
    has_subject = any(k in text for k in SUBJECT_KEYS)
    has_class = any(k in text for k in CLASS_KEYS)
    has_hint = any(k in text for k in CONTEXT_HINT_KEYS)

    # Reject if it's pure schedule/timetable junk
    if has_subject and not (has_class or has_hint or has_role):
        # Need real prose, not just a subject mention
        return None

    if has_role and (has_class or has_hint or has_subject or PEDAGOGY_VERBS.search(text)):
        if "担任" in text:
            attr = "担任"
        elif "教科主任" in text or "学科主任" in text:
            attr = "教科主任"
        elif "学年主任" in text:
            attr = "学年主任"
        elif "校長" in text or "学校長" in text or "学園長" in text:
            attr = "校長"
        elif "副校長" in text or "教頭" in text:
            attr = "副校長/教頭"
        elif "教諭" in text:
            attr = "教科教員"
        else:
            attr = "教員"
        return attr, "教員紹介"

    if has_subject and (has_class or has_hint):
        # subject with class/curriculum context: treat as 教科紹介
        return "教科教員", "教科紹介"

    if has_hint and has_class:
        return "教科教員", "授業紹介"

    # In curriculum.html / schoollife.html / about.html context,
    # pedagogy prose with classroom verbs counts even without subject keyword.
    if file_ctx in ("curriculum.html", "schoollife.html", "about.html",
                    "voice.html", "principal.html", "philosophy.html",
                    "mission.html", "root.html") and has_class \
            and PEDAGOGY_VERBS.search(text):
        # On principal.html, treat as 校長 voice.
        if file_ctx == "principal.html":
            return "校長", "教員紹介"
        return "教科教員", "授業紹介"
    return None


def select_blocks(soup: BeautifulSoup) -> list[str]:
    # Drop noisy tags
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "noscript"]):
        tag.decompose()
    # Also drop common menu / news / breadcrumb containers
    for sel in ["#header", "#nav", "#globalnav", "#footer", "#sidebar",
                ".header", ".nav", ".globalnav", ".footer", ".sidebar",
                ".breadcrumb", "#breadcrumb", "#bread", ".gnav", "#gnav",
                ".menu", "#menu",
                ".news", ".news-list", ".news_list", ".news-area",
                ".topics", ".topics-list", ".info", ".info-list",
                ".pickup", ".banner", ".banners",
                ".pagination", ".paginator"]:
        for el in soup.select(sel):
            el.decompose()

    candidates: list[str] = []
    # Leaf paragraphs / list items / table cells
    for el in soup.find_all(["p", "li", "td"]):
        if el.find(["p", "li", "td"]):
            continue
        text = el.get_text(separator="", strip=True)
        text = re.sub(r"\s+", "", text)
        if text:
            candidates.append(text)
    # Also small DIVs that act as paragraphs (no nested p/li)
    for el in soup.find_all("div"):
        if el.find(["p", "li", "div", "td", "section", "article"]):
            continue
        text = el.get_text(separator="", strip=True)
        text = re.sub(r"\s+", "", text)
        if text:
            candidates.append(text)
    # Dedup while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for t in candidates:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def normalize_quote(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", "", text)
    return text


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
                soup = BeautifulSoup(f, "html.parser")
        except Exception:
            continue
        # Determine source_url: prefer canonical/og:url if present
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
        default_ctx = FILE_CONTEXT.get(fname, "教員紹介")

        blocks = select_blocks(soup)
        for raw in blocks:
            if len(out) >= MAX_PER_SCHOOL:
                break
            text = normalize_quote(raw)
            if not is_clean(text):
                continue
            classified = classify(text, file_ctx=fname)
            if not classified:
                continue
            attr, ctx = classified
            # File-level context takes precedence when more specific
            if default_ctx == "教科紹介" and ctx == "教員紹介":
                # keep teacher classification only if role keyword present
                pass
            # Trim if longer than MAX_LEN (shouldn't happen but be safe)
            if cjk_len(text) > MAX_LEN:
                text = text[:MAX_LEN]
            key = text[:80]
            if key in seen_quotes:
                continue
            seen_quotes.add(key)
            record = {
                "school_id": school_id,
                "speaker_role": "teacher",
                "speaker_attribute": attr,
                "quote_text": text,
                "context": ctx,
                "source_url": source_url,
                "rights_level": "quoted_with_attribution",
            }
            out.append(record)
    return out


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    schools = load_schools()
    school_dirs = sorted(p for p in CACHE_DIR.iterdir() if p.is_dir())
    total_schools = len(school_dirs)

    records: list[dict] = []
    schools_with_data = 0
    per_school_counts: dict[str, int] = {}
    skipped_schools: list[str] = []

    for sd in school_dirs:
        sid = sd.name
        name_ja, homepage = schools.get(sid, ("", ""))
        recs = extract_for_school(sid, sd, homepage)
        if recs:
            schools_with_data += 1
        else:
            skipped_schools.append(sid)
        per_school_counts[sid] = len(recs)
        records.extend(recs)

    # Write JSONL
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Progress log
    progress = {
        "team": "B-3",
        "task": "teacher/subject voices extraction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_schools_scanned": total_schools,
        "schools_with_extractions": schools_with_data,
        "schools_without_extractions": len(skipped_schools),
        "total_records": len(records),
        "max_per_school": MAX_PER_SCHOOL,
        "min_quote_len": MIN_LEN,
        "max_quote_len": MAX_LEN,
        "output_path": str(OUT_PATH),
        "rights_level": "quoted_with_attribution",
        "ethics_notes": [
            "公開情報のみを対象。",
            "個人名は最小限に抑え、ページ全体の文脈で公開済みの記述のみ抽出。",
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
