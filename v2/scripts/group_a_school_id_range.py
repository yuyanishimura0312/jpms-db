#!/usr/bin/env python3
"""
JPMS-DB v2 — Group A: School ID Range Re-Scan & Deep Extraction

全 528 校を学校ID範囲で 10 分割し、各範囲で raw_html_cache の HTML を再走査して
追加の testimonials (校長/教員/在校生/卒業生/保護者) を抽出する。

戦略:
- 既存抽出 (team_b1/b2/b3/b5, team_c_llm_*) でカバーされなかった HTML 内の長文を拾う
- 見出し配下のブロック (在校生インタビュー / 卒業生メッセージ / 保護者の声) と
  <article>, <section> 内の長文段落を強化抽出
- Q&A 形式の応答全文 (Q. ... A. ...) を一段落として抽出
- JSON-LD schema:Person / schema:Review / schema:InterviewObject の content を抽出
- school_id × text[:80] hash で既存テストimonialsとの重複を除去
- DB に直接投入 (busy_timeout=600000、batch=50 commit)
- ID 範囲 10 分割で順次処理 (並列なし、DB lock 衝突防止)

倫理:
- 未成年 (中学生): rights_level=anonymized_only、speaker_attribute は generic
- 公開HP: rights_level=quoted_with_attribution + 出典URL
- 引用は 30〜400 字、重複除去
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE_DIR = ROOT / "raw_html_cache"
DB_PATH = ROOT / "jpms_v2.db"
OUT_PATH = ROOT / "codex_output" / "group_a_consolidated.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "group_a.json"

MIN_LEN = 25
MAX_LEN = 400
MAX_PER_SCHOOL_PER_ROLE = 16   # role 別の上限
COMMIT_BATCH = 50
NUM_RANGES = 10

# -------------------------------------------------------------------
# Page slug → context default + role hint
# -------------------------------------------------------------------
ALL_HTML_FILES = [
    "voice.html", "voice2.html", "voice3.html", "voices.html",
    "schoollife.html", "school-life.html", "school_life.html",
    "student.html", "student-voice.html", "student_voice.html",
    "students.html", "interview.html", "interview2.html", "interviews.html",
    "alumni.html", "graduates.html", "ob-og.html", "obog.html",
    "progress.html", "career.html", "careers.html",
    "parent.html", "parent2.html", "pta.html", "guardian.html",
    "principal.html", "message.html", "greeting.html", "chairman.html",
    "philosophy.html", "mission.html", "about.html", "outline.html",
    "events.html", "curriculum.html", "admission.html",
    "root.html", "index.html", "top.html",
]

# -------------------------------------------------------------------
# Role detection: heading & in-text speaker keywords
# -------------------------------------------------------------------
PRINCIPAL_HEADER = [
    "校長挨拶", "校長あいさつ", "校長メッセージ", "校長からのメッセージ",
    "校長の言葉", "校長より", "学園長挨拶", "学園長メッセージ",
    "学長挨拶", "学長メッセージ", "理事長挨拶", "理事長メッセージ",
    "学校長挨拶", "学校長メッセージ",
]

TEACHER_HEADER = [
    "教員紹介", "先生紹介", "教員からのメッセージ", "教師の声",
    "先生の声", "教員インタビュー", "先生インタビュー",
    "教師からのメッセージ", "先生からのメッセージ",
]

STUDENT_CURRENT_HEADER = [
    "在校生の声", "在校生インタビュー", "在校生からのメッセージ",
    "在校生メッセージ", "生徒の声", "生徒インタビュー", "生徒メッセージ",
    "現役生の声", "在校生の言葉",
]

STUDENT_ALUMNI_HEADER = [
    "卒業生の声", "卒業生メッセージ", "卒業生からのメッセージ",
    "卒業生インタビュー", "OB・OGの声", "OBOGの声", "OB/OGの声",
    "OBインタビュー", "OGインタビュー", "先輩の声", "先輩からのメッセージ",
    "卒業生からの言葉", "卒業生コラム",
]

PARENT_HEADER = [
    "保護者の声", "保護者からのメッセージ", "保護者メッセージ",
    "保護者インタビュー", "保護者の言葉", "PTAより", "PTAの声",
    "保護者の方より", "ご家族の声", "ファミリーボイス",
]

ROLE_HEADERS = [
    ("principal", PRINCIPAL_HEADER, "校長メッセージ"),
    ("teacher", TEACHER_HEADER, "教員メッセージ"),
    ("student_alumni", STUDENT_ALUMNI_HEADER, "卒業生メッセージ"),
    ("student_current", STUDENT_CURRENT_HEADER, "在校生インタビュー"),
    ("parent", PARENT_HEADER, "保護者の声"),
]

# -------------------------------------------------------------------
# Patterns
# -------------------------------------------------------------------
NARRATIVE_PATTERNS = [
    "私は", "私が", "私の", "私たち", "僕は", "僕が", "僕の",
    "自分は", "自分が", "自分の",
    "と思います", "と感じ", "ことができ", "を学びました", "を学ん",
    "と考え", "を経験", "ています。", "ました。",
    "してい", "してくれ", "充実してい", "が印象的", "が思い出",
    "を通して", "仲間と", "毎日を", "を実感", "を体験",
    "頑張って", "目指し", "受験", "合格しました",
    "高校生活", "中学生活", "学校生活", "部活動",
    "文化祭", "体育祭", "修学旅行",
    # parent narrative
    "息子", "娘", "我が子", "子どもの", "親として", "保護者として",
    "通わせて", "通うこと", "入学させ", "通学",
    # principal/teacher
    "本校は", "本校の", "本校では", "我が校", "本校生徒",
    "建学", "教育方針", "を育てる", "を育成",
    "皆さん", "皆様", "生徒たち", "生徒の皆さん", "受験生の皆様",
]

# Reject lines that look like nav/copyright/menu/promotional
BAD_PATTERNS = [
    re.compile(r"Copyright|All Rights Reserved|©", re.I),
    re.compile(r"http[s]?://"),
    re.compile(r"〒\d"),
    re.compile(r"TEL[:：]|FAX[:：]"),
    re.compile(r"^\s*[0-9０-９]+\s*$"),
    re.compile(r"<!--|-->"),
    re.compile(r"お探しのページ|ページが見つかり|Not Found", re.I),
    re.compile(r"検索フォーム"),
    re.compile(r"【募集】|【お知らせ】|【告知】|【受付】"),
    re.compile(r"説明会.*予約|出願受付|募集要項"),
    re.compile(r"^©|^Copyright"),
]

NAV_BAD_TOKENS = [
    "サイトマップ", "プライバシーポリシー", "個人情報保護方針",
    "資料請求", "募集要項", "アクセス・お問い合わせ", "教職員募集",
    "Cookie", "JavaScript",
]


# -------------------------------------------------------------------
# Utility
# -------------------------------------------------------------------
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
    if len(parts) > 0 and len(short_parts) / max(1, len(parts)) > 0.55 and len(parts) > 8:
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
    if not re.search(r"[。、．！？]", text):
        return False
    if text.count("：") + text.count(":") >= 4:
        return False
    return True


def has_narrative_voice(text: str) -> bool:
    return any(p in text for p in NARRATIVE_PATTERNS)


def anonymize_minor(text: str) -> str:
    """Remove minor PII for student records."""
    text = re.sub(r"(中学|中等部)[1-3一二三１-３]年(生)?", "中学生", text)
    text = re.sub(r"(高校|高等学校|高等部)[1-3一二三１-３]年(生)?", "高校生", text)
    text = re.sub(r"[A-Z]\.\s*[A-Z]\.", "", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "", text)
    text = text.strip("「」『』\"' 　")
    text = re.sub(r"\s+", "", text)
    return text


def normalize_text(text: str) -> str:
    text = text.strip("「」『』\"' 　")
    text = re.sub(r"\s+", "", text)
    return text


# -------------------------------------------------------------------
# JSON-LD parsing
# -------------------------------------------------------------------
def extract_jsonld_quotes(soup: BeautifulSoup) -> list[tuple[str, str, str]]:
    """Extract (text, role_hint, ctx) from JSON-LD blocks."""
    out: list[tuple[str, str, str]] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            if t in ("Person", "InterviewObject", "Review"):
                desc = item.get("description") or item.get("text") or ""
                if isinstance(desc, str) and desc.strip():
                    out.append((desc.strip(), "", "JSON-LD"))
            if t == "QAPage" or t == "FAQPage":
                for q in item.get("mainEntity", []) or []:
                    if isinstance(q, dict):
                        ans = q.get("acceptedAnswer", {})
                        if isinstance(ans, dict):
                            t2 = ans.get("text", "")
                            if isinstance(t2, str) and t2.strip():
                                out.append((t2.strip(), "", "Q&A"))
    return out


# -------------------------------------------------------------------
# Block extraction
# -------------------------------------------------------------------
def select_blocks(soup: BeautifulSoup) -> list[tuple[str, str, str]]:
    """Return list of (text, preceding_heading, parent_section_heading)."""
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "noscript"]):
        tag.decompose()
    for sel in ["#header", "#nav", "#globalnav", "#footer", "#sidebar",
                ".header", ".nav", ".globalnav", ".footer", ".sidebar",
                ".breadcrumb", "#breadcrumb", "#bread", ".gnav", "#gnav",
                ".menu", "#menu", "#search", ".search"]:
        for el in soup.select(sel):
            el.decompose()

    candidates: list[tuple[str, str, str]] = []
    section_heading = ""
    current_heading = ""

    # Iterate document order
    for el in soup.find_all(True):
        tag = el.name
        if tag in {"h1", "h2"}:
            t = el.get_text(separator="", strip=True)
            if t:
                section_heading = re.sub(r"\s+", "", t)[:120]
                current_heading = section_heading
            continue
        if tag in {"h3", "h4", "h5", "h6"}:
            t = el.get_text(separator="", strip=True)
            if t:
                current_heading = re.sub(r"\s+", "", t)[:120]
            continue
        if tag in {"p", "blockquote", "li", "td"}:
            if el.find(["p", "li", "blockquote"]):
                continue
            t = el.get_text(separator="", strip=True)
            t = re.sub(r"\s+", "", t)
            if not t:
                continue
            candidates.append((t, current_heading, section_heading))
        elif tag in {"article", "section", "div"}:
            # Allow article/section with no nested p (some pages put text in div directly)
            if el.find(["p", "li", "blockquote", "article", "section"]):
                continue
            t = el.get_text(separator="", strip=True)
            t = re.sub(r"\s+", "", t)
            if not t:
                continue
            candidates.append((t, current_heading, section_heading))

    # Dedup
    seen: set[str] = set()
    uniq: list[tuple[str, str, str]] = []
    for (t, h, sh) in candidates:
        if t in seen:
            continue
        seen.add(t)
        uniq.append((t, h, sh))
    return uniq


# -------------------------------------------------------------------
# Role classification
# -------------------------------------------------------------------
NON_VOICE_HEADINGS = [
    "お知らせ", "ニュース", "トピックス", "イベント", "アクセス",
    "ダウンロード", "問い合わせ", "プライバシー", "サイトマップ",
]


def classify_role(text: str, heading: str, section_heading: str,
                  page_role_hint: tuple[str, str, str] | None
                  ) -> tuple[str, str, str] | None:
    """Decide (speaker_role, speaker_attribute, context)."""
    # 1) Heading-based (highest priority)
    for h in (heading, section_heading):
        if not h:
            continue
        if any(nh in h for nh in NON_VOICE_HEADINGS):
            continue
        for role, kws, ctx_default in ROLE_HEADERS:
            for kw in kws:
                if kw in h:
                    attr = _attr_for_role(role)
                    return (role, attr, kw)

    # 2) Block intrinsic signals
    if "校長" in text and ("です。" in text or "考えます" in text or "願って" in text):
        if any(k in text for k in ["皆さん", "生徒", "本校", "我が校"]):
            return ("principal", "校長", "校長メッセージ")
    if ("卒業生" in text and ("メッセージ" in text or "後輩へ" in text or "在学中" in text)) \
            or (("大学に進" in text or "社会人になって" in text) and "私" in text):
        return ("student_alumni", "卒業生", "卒業生メッセージ")
    if "在校生" in text and ("毎日" in text or "学校生活" in text):
        return ("student_current", "中学生", "在校生インタビュー")
    if any(k in text for k in ["保護者として", "親として", "我が子", "息子は", "娘は", "通わせて"]):
        return ("parent", "保護者", "保護者の声")
    if any(k in text for k in ["教員として", "教師として", "授業では", "私の担当"]):
        return ("teacher", "教員", "教員メッセージ")

    # 3) Page-level hint fallback (filename or title/h1 derived)
    if page_role_hint:
        role = page_role_hint[0]
        # For principal-page hint, require statesman/welcome wording
        if role == "principal":
            if any(k in text for k in [
                "皆さん", "皆様", "生徒の", "本校", "本学園", "我が校",
                "建学", "教育理念", "創立", "願っ", "目指し", "育てて",
                "育成", "歩んで", "育んで", "実践し", "考えて",
            ]):
                return page_role_hint
            return None
        # For parent-page hint, require parent-perspective wording
        if role == "parent":
            if any(k in text for k in [
                "保護者", "息子", "娘", "我が子", "親", "子ども", "子供",
                "PTA", "通わせ", "通学", "入学させ", "ファミリ",
            ]):
                return page_role_hint
            return None
        # For student_*: require first-person + school-life words
        if role in ("student_current", "student_alumni"):
            if any(k in text for k in [
                "私", "僕", "自分",
            ]) and any(k in text for k in [
                "学校", "学園", "中学", "高校", "授業", "部活",
                "先生", "友人", "友達", "仲間", "毎日", "生活",
                "受験", "合格", "卒業", "進学", "成長", "経験",
                "学びました", "学んだ", "を学ぶ", "頑張",
            ]):
                return page_role_hint
            return None

    return None


def _attr_for_role(role: str) -> str:
    return {
        "principal": "校長",
        "teacher": "教員",
        "student_current": "中学生",
        "student_alumni": "卒業生",
        "parent": "保護者",
    }.get(role, "")


# File-slug → role hint (used when title/h1 unclear)
FILE_ROLE_HINT = {
    "principal.html": ("principal", "校長", "校長メッセージ"),
    "message.html": ("principal", "校長", "校長メッセージ"),
    "greeting.html": ("principal", "校長", "校長メッセージ"),
    "chairman.html": ("principal", "理事長", "理事長メッセージ"),
    "philosophy.html": ("principal", "校長", "教育理念メッセージ"),
    "mission.html": ("principal", "校長", "ミッションメッセージ"),
    "voice.html": ("student_alumni", "卒業生", "在校生・卒業生メッセージ"),
    "voice2.html": ("student_alumni", "卒業生", "在校生・卒業生メッセージ"),
    "schoollife.html": ("student_current", "中学生", "在校生インタビュー"),
    "school-life.html": ("student_current", "中学生", "在校生インタビュー"),
    "student.html": ("student_current", "中学生", "在校生インタビュー"),
    "student-voice.html": ("student_current", "中学生", "在校生インタビュー"),
    "alumni.html": ("student_alumni", "卒業生", "卒業生メッセージ"),
    "graduates.html": ("student_alumni", "卒業生", "卒業生メッセージ"),
    "ob-og.html": ("student_alumni", "卒業生", "卒業生メッセージ"),
    "obog.html": ("student_alumni", "卒業生", "卒業生メッセージ"),
    "parent.html": ("parent", "保護者", "保護者の声"),
    "parent2.html": ("parent", "保護者", "保護者の声"),
    "guardian.html": ("parent", "保護者", "保護者の声"),
    "pta.html": ("parent", "保護者", "PTAより"),
    "interview.html": ("student_alumni", "卒業生", "インタビュー"),
}


def detect_page_role_hint(soup: BeautifulSoup,
                          fname: str | None = None) -> tuple[str, str, str] | None:
    """Inspect <title>, <h1>, filename for page-level role."""
    title_tag = soup.find("title")
    title_text = title_tag.get_text().strip() if title_tag else ""
    page_subject = re.split(r"[|｜\-－〜:：]", title_text)[0].strip()

    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""

    # Reject NotFound / search pages by title
    if any(t in title_text for t in ["404", "Not Found", "見つかり", "お探しのページ"]):
        return None

    for source in (page_subject, h1_text):
        if not source:
            continue
        for role, kws, ctx_default in ROLE_HEADERS:
            for kw in kws:
                if kw in source:
                    return (role, _attr_for_role(role), kw)

    # Fallback: filename-based hint
    if fname and fname in FILE_ROLE_HINT:
        return FILE_ROLE_HINT[fname]
    return None


# -------------------------------------------------------------------
# Main extraction per HTML file
# -------------------------------------------------------------------
def safe_parse(html_src: str):
    try:
        return BeautifulSoup(html_src, "html.parser"), html_src
    except Exception:
        cleaned = re.sub(r"&#(\D)", r"&amp;#\1", html_src)
        try:
            return BeautifulSoup(cleaned, "html.parser"), cleaned
        except Exception:
            return None, html_src


def extract_for_file(school_id: str, fname: str, path: Path,
                     homepage: str | None,
                     existing_keys: set[str]
                     ) -> list[dict]:
    out: list[dict] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw_html = f.read()
    except Exception:
        return out
    if len(raw_html) < 1200:
        return out

    soup, _ = safe_parse(raw_html)
    if soup is None:
        return out

    # Source URL
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
        if slug in ("root", "index", "top"):
            source_url = base
        else:
            source_url = urljoin(base, slug)

    page_role_hint = detect_page_role_hint(soup, fname)

    # Pull JSON-LD quotes first (high signal)
    for ld_text, _, ld_ctx in extract_jsonld_quotes(soup):
        ld_text = normalize_text(ld_text)
        if not is_clean(ld_text):
            continue
        if not has_narrative_voice(ld_text):
            continue
        classified = classify_role(ld_text, ld_ctx, "", page_role_hint)
        if not classified:
            continue
        out.append(_to_record(school_id, classified, ld_text, source_url,
                              existing_keys))

    blocks = select_blocks(soup)
    for raw, heading, section_heading in blocks:
        if heading and any(nh in heading for nh in NON_VOICE_HEADINGS):
            continue
        text = normalize_text(raw)
        if not is_clean(text):
            continue
        if not has_narrative_voice(text):
            continue

        classified = classify_role(text, heading, section_heading,
                                   page_role_hint)
        if not classified:
            continue
        speaker_role = classified[0]

        # Anonymize for student roles
        if speaker_role in ("student_current", "student_alumni"):
            text = anonymize_minor(text)
            if not is_clean(text):
                continue

        rec = _to_record(school_id, classified, text, source_url, existing_keys)
        if rec:
            out.append(rec)
    return [r for r in out if r is not None]


def _to_record(school_id: str,
               classified: tuple[str, str, str],
               text: str,
               source_url: str,
               existing_keys) -> dict | None:
    speaker_role, attr, ctx = classified
    if cjk_len(text) > MAX_LEN:
        text = text[:MAX_LEN]
    # existing_keys may be set (legacy) or dict (new)
    head = text[:50]
    if isinstance(existing_keys, dict):
        prior = existing_keys.get(school_id, [])
        for p in prior:
            if not p:
                continue
            # Exact 50-char prefix match → duplicate
            if head == p:
                return None
        prior.append(head)
        existing_keys[school_id] = prior
    else:
        key = f"{school_id}::{text[:80]}"
        if key in existing_keys:
            return None
        existing_keys.add(key)
    summary = text[:60] + ("…" if len(text) > 60 else "")

    rights_level = "anonymized_only" if speaker_role.startswith("student_") \
        else "quoted_with_attribution"

    return {
        "school_id": school_id,
        "speaker_role": speaker_role,
        "speaker_attribute": attr,
        "quote_text": text,
        "quote_summary": summary,
        "context": ctx,
        "source_type": "school_website",
        "source_url": source_url,
        "rights_level": rights_level,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_notes": "Group A: school_id range re-scan",
    }


def extract_for_school(school_id: str, school_dir: Path,
                       homepage: str | None,
                       existing_keys: set[str]) -> list[dict]:
    out: list[dict] = []
    role_counts: dict[str, int] = {}

    # Walk every .html file in directory (not just preferred list)
    html_files = sorted(school_dir.glob("*.html"))
    for path in html_files:
        fname = path.name
        recs = extract_for_file(school_id, fname, path, homepage, existing_keys)
        for r in recs:
            role = r["speaker_role"]
            if role_counts.get(role, 0) >= MAX_PER_SCHOOL_PER_ROLE:
                continue
            role_counts[role] = role_counts.get(role, 0) + 1
            out.append(r)
    return out


# -------------------------------------------------------------------
# DB / loaders
# -------------------------------------------------------------------
def load_schools() -> dict[str, tuple[str, str | None]]:
    if not DB_PATH.exists():
        return {}
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("SELECT id, legacy_id, name_ja, homepage_url FROM schools_v2")
    rows = cur.fetchall()
    con.close()
    out: dict[str, tuple[str, str]] = {}
    for sid, legacy_id, name_ja, homepage in rows:
        out[sid] = (name_ja or "", homepage or "")
        if legacy_id:
            out[legacy_id] = (name_ja or "", homepage or "")
    return out


def load_existing_testimonial_keys() -> dict[str, list[str]]:
    """Build school_id -> [first 50 chars of every existing testimonial] index.

    Used to detect sub-string overlap with already stored testimonials.
    """
    out: dict[str, list[str]] = {}
    if not DB_PATH.exists():
        return out
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("SELECT school_id, quote_text FROM testimonials_v2")
    for sid, qt in cur.fetchall():
        if not sid or not qt:
            continue
        normalized = re.sub(r"\s+", "", qt)
        out.setdefault(sid, []).append(normalized[:50])
    con.close()
    return out


def insert_records(records: list[dict]) -> int:
    """Insert records into testimonials_v2; return inserted count."""
    if not records:
        return 0
    con = sqlite3.connect(str(DB_PATH), timeout=600)
    con.execute("PRAGMA busy_timeout = 600000")
    cur = con.cursor()
    inserted = 0
    rows = []
    for r in records:
        rows.append((
            r["school_id"], r["speaker_role"], r["speaker_attribute"],
            r["quote_text"], r["quote_summary"], r["context"],
            r["source_type"], r["source_url"], None,
            r["rights_level"], r["retrieved_at"], r["retrieval_notes"],
            "pending",
        ))
    sql = """
        INSERT INTO testimonials_v2
        (school_id, speaker_role, speaker_attribute, quote_text,
         quote_summary, context, source_type, source_url, source_id,
         rights_level, retrieved_at, retrieval_notes, ethics_review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for i in range(0, len(rows), COMMIT_BATCH):
        batch = rows[i:i + COMMIT_BATCH]
        cur.executemany(sql, batch)
        con.commit()
        inserted += len(batch)
    con.close()
    return inserted


# -------------------------------------------------------------------
# Range partitioning
# -------------------------------------------------------------------
def partition_school_dirs(school_dirs: list[Path], n: int) -> list[list[Path]]:
    """Split sorted school dir list into n roughly equal ranges."""
    school_dirs = sorted(school_dirs)
    total = len(school_dirs)
    base = total // n
    rem = total % n
    out: list[list[Path]] = []
    idx = 0
    for i in range(n):
        size = base + (1 if i < rem else 0)
        out.append(school_dirs[idx: idx + size])
        idx += size
    return out


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    schools = load_schools()
    existing_keys = load_existing_testimonial_keys()
    print(f"[init] schools loaded: {len(schools)}", flush=True)
    print(f"[init] existing testimonial keys: {len(existing_keys)}", flush=True)

    school_dirs = [p for p in CACHE_DIR.iterdir() if p.is_dir()]
    ranges = partition_school_dirs(school_dirs, NUM_RANGES)
    print(f"[init] school dirs: {len(school_dirs)}; ranges: {NUM_RANGES}",
          flush=True)

    all_records: list[dict] = []
    range_stats: list[dict] = []

    # PHASE 1: Extract all (no DB writes yet) → JSONL
    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for ri, range_dirs in enumerate(ranges):
            range_records: list[dict] = []
            t0 = time.time()
            for sd in sorted(range_dirs):
                sid = sd.name
                name_ja, homepage = schools.get(sid, ("", ""))
                recs = extract_for_school(sid, sd, homepage, existing_keys)
                if recs:
                    range_records.extend(recs)
            for r in range_records:
                out_f.write(json.dumps(r, ensure_ascii=False) + "\n")
            out_f.flush()
            elapsed = time.time() - t0
            range_stats.append({
                "range_index": ri,
                "schools_in_range": len(range_dirs),
                "extracted_records": len(range_records),
                "db_inserted": 0,
                "elapsed_sec": round(elapsed, 1),
            })
            all_records.extend(range_records)
            print(f"[range {ri}] schools={len(range_dirs)} "
                  f"extracted={len(range_records)} "
                  f"elapsed={elapsed:.1f}s", flush=True)

            progress = {
                "task_id": "group_a_school_id_range",
                "team": "Group A",
                "task": "School ID range deep re-scan",
                "phase": "extract",
                "ts": datetime.now(timezone.utc).isoformat(),
                "ranges_completed": ri + 1,
                "ranges_total": NUM_RANGES,
                "total_extracted": len(all_records),
                "range_stats": range_stats,
                "output_path": str(OUT_PATH),
            }
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

    # PHASE 2: Bulk DB insert (single connection, batched commits)
    print(f"[phase 2] DB insert begin: {len(all_records)} records", flush=True)
    inserted = insert_records(all_records)
    print(f"[phase 2] DB inserted: {inserted}", flush=True)

    progress["phase"] = "complete"
    progress["db_inserted_total"] = inserted
    progress["ts"] = datetime.now(timezone.utc).isoformat()
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"[done] total extracted: {len(all_records)}")
    print(f"[done] db inserted: {inserted}")
    print(f"[done] output: {OUT_PATH}")
    print(f"[done] progress: {PROGRESS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
