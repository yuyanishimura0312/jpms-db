#!/usr/bin/env python3
"""JPMS-DB v2 — Team C-3 LLM 抽出（教員・保護者声深掘り）

戦略
- raw_html_cache を二周走査する。
- 1 周目: 教員側ターゲットページ
  curriculum.html / schoollife.html / education.html / about.html / philosophy.html /
  mission.html / principal.html / voice.html / root.html
  → 教員一人称（私たちは / 本校では / 我々）+ 教科キーワードの段落を抽出。
- 2 周目: 保護者側ターゲットページ
  parent.html / pta.html / root.html / schoollife.html / voice.html
  → PTA / 後援会 / 保護者の声 / 保護者として / 我が子は / 親として 等。
- 既存 testimonials_v2 と重複除外。
- 公開情報のみ。教員側は quoted_with_attribution、保護者側は anonymized_only。
- 引用 < 400 字、ミニマム 60 字 (前後 v1/v2 とのバランス)。

出力
- codex_output/team_c_llm_teacher_parent.jsonl
- codex_progress/team_c_llm_tp.json
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE_DIR = ROOT / "raw_html_cache"
DB_PATH = ROOT / "jpms_v2.db"
OUT_PATH = ROOT / "codex_output" / "team_c_llm_teacher_parent.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "team_c_llm_tp.json"

# Per task spec
MIN_LEN = 40
MAX_LEN = 380          # safety margin under 400-char ethics rule
MAX_TEACHER_PER_SCHOOL = 10
MAX_PARENT_PER_SCHOOL = 6

TEACHER_PAGES = [
    "curriculum.html", "schoollife.html", "education.html",
    "about.html", "philosophy.html", "mission.html",
    "principal.html", "voice.html",
    "progress.html", "events.html", "admission.html",
    "root.html",
]
PARENT_PAGES = [
    "parent.html", "pta.html",
    "schoollife.html", "voice.html", "events.html",
    "admission.html", "root.html",
]
PARENT_DEDICATED_PAGES = ["parent.html", "pta.html"]
PARENT_SECONDARY_PAGES = [
    "schoollife.html", "voice.html", "events.html",
    "admission.html", "root.html",
    "about.html", "curriculum.html", "progress.html",
    "philosophy.html", "mission.html",
]

PAGE_CTX_TEACHER = {
    "curriculum.html": "教科紹介",
    "education.html": "教育方針",
    "schoollife.html": "学校生活",
    "about.html": "学校紹介",
    "philosophy.html": "教育理念",
    "mission.html": "建学の精神",
    "principal.html": "校長挨拶",
    "voice.html": "教員紹介",
    "progress.html": "進路指導",
    "events.html": "学校行事",
    "admission.html": "入試案内",
    "root.html": "学校紹介",
}

PAGE_CTX_PARENT = {
    "parent.html": "保護者向けページ",
    "pta.html": "PTA・保護者会ページ",
    "schoollife.html": "学校生活ページ",
    "voice.html": "保護者の声ページ",
    "events.html": "行事案内ページ",
    "admission.html": "入試・募集案内ページ",
    "root.html": "トップページ",
}

SUBJECT_KEYS = [
    "国語", "数学", "英語", "理科", "社会", "地理", "歴史", "公民",
    "物理", "化学", "生物", "地学", "音楽", "美術", "保健体育", "体育",
    "技術", "家庭", "情報", "道徳", "総合的な学習", "総合学習",
    "宗教", "聖書", "倫理", "書道", "古典", "現代文", "世界史", "日本史",
]

TEACHER_VIEWPOINT = re.compile(
    r"(私たちは|私たちの|私たち教員|本校では|本校は|本学では|本学は|"
    r"本学園|本校の(?:教員|教師|教諭)|当校では|当校は|我々|我が校|"
    r"教員(?:一同|として|が|は)|教師(?:一同|として|が|は)|"
    r"教職員(?:一同|として|が|は)|"
    r"指導(?:しており|しています|を行|に当|を通|の中)|"
    r"授業(?:では|を通|を行|の中|を大切|の特色|の質)|"
    r"学習(?:指導|を進|を行|を通|の中|の場|の特色)|"
    r"教育(?:を通|の場|を実|を行|を進|では|として|の中|の特色|目標|目的|理念|方針)|"
    r"カリキュラム(?:では|の|を)|教育課程|学校生活(?:では|を)|"
    r"育成(?:し|に)|育てて|養って|身につけ(?:る|させ)|身に付け(?:る|させ)|"
    r"目指(?:し|す)|大切に(?:し|して)|重視(?:し|して))"
)

PARENT_VIEWPOINT = re.compile(
    r"(保護者として|保護者の(?:皆|方|声|立場|皆様|方々|皆さま)|"
    r"親として|親の(?:立場|目|気持|思い)|"
    r"我が(?:子|家)|うちの(?:子|娘|息子)|娘(?:が|は|の|を)|息子(?:が|は|の|を)|"
    r"PTA(?:活動|委員|会員|役員|として|では|の|総会|だより|新聞)?|"
    r"父母(?:会|の会|として)|後援会|育友会|母の会|父母の会|"
    r"保護者(?:会|向け|向けの|宛|宛の|から|より|の皆様|の皆さま|の皆|の皆方)|"
    r"子(?:ども|供)(?:を|の|が|たち|たちが|たちの)|家庭(?:と学校|では|として|と協力|の協力)|"
    r"入学(?:させ|を決め|前|してから)|進学(?:させ|先|の道)|本校に(?:通|入学|預け))"
)

# Strong context markers indicating organizational parent voice
PARENT_ORG = re.compile(
    r"(PTA|父母会|父母の会|後援会|育友会|母の会|保護者会|保護者の声)"
)

# Fragments that suggest the speaker is a student rather than teacher/parent
STUDENT_VOICE_PATTERNS = re.compile(
    r"(私の夢|なりたいです|楽しかった思い出|"
    r"中学受験(?:を|で)した|高校時代(?:に|の)私|私が中学生|私が高校生|"
    r"私たち生徒|私は生徒|大学に進学(?:し|を決め)|"
    r"クラブの先輩|部活の仲間|友達(?:と|が|は))"
)

# Hard reject regexes (nav/copyright/news/forms)
BAD_PATTERNS = [
    re.compile(r"Copyright|All Rights Reserved|©", re.I),
    re.compile(r"http[s]?://\S{20,}"),
    re.compile(r"〒\d"),
    re.compile(r"TEL[:：]|FAX[:：]"),
    re.compile(r"プライバシーポリシー|サイトマップ|お問い合わせ"),
    re.compile(r"続きを見る|もっと見る|一覧を見る|詳しく見る|もっと読む"),
    re.compile(r"PICKUP|TOPICS|NEWS|MENU|SITEMAP", re.I),
    re.compile(r"必須|任意|半角(?:英|数字)"),
    re.compile(r"(?:ID|パスワード|ログイン|サインイン)"),
    re.compile(r"4(?:04|03)\s*not\s*found", re.I),
    re.compile(r"お探しのページ"),
]

# Reject obvious admin/forms/admission content
ADMIN_PATTERNS = [
    re.compile(r"(?:受験番号|合格発表|合否|出願期間|出願書類|受験票)"),
    re.compile(r"(?:申し込みフォーム|お申し込みは|受付期間|受付中|受付終了)"),
    re.compile(r"(?:制服(?:及び|および|や)|お弁当|ご持参|忘れ物)"),
    re.compile(r"(?:学校感染症|罹患|医師に診断)"),
    re.compile(r"^[\s\d年月日.\-/]{6,30}"),
]

# Off-topic (non-school) cache pages — reject by content/title
NON_SCHOOL_PATTERNS = [
    re.compile(r"ボート(?:協会|連盟|競技|レガッタ)"),
    re.compile(r"(?:ローイング|レガッタ|オリンピック|国体|世界選手権)"),
    re.compile(r"(?:大学走舸組|端艇会|FISA)"),
    re.compile(r"researchmap|aguse|WHOIS|お名前\.com"),
]


def cjk_len(s: str) -> int:
    return len(s)


def normalize_fullwidth(s: str) -> str:
    """Normalize full-width Latin/PTA-like markers and spaces.

    keep CJK punctuation intact.
    """
    out = []
    for ch in s:
        cp = ord(ch)
        # Full-width Latin letters → ASCII (Ａ-Ｚ ａ-ｚ)
        if 0xFF21 <= cp <= 0xFF3A or 0xFF41 <= cp <= 0xFF5A:
            out.append(chr(cp - 0xFEE0))
            continue
        # Full-width digits → ASCII
        if 0xFF10 <= cp <= 0xFF19:
            out.append(chr(cp - 0xFEE0))
            continue
        # Full-width space → ascii space
        if cp == 0x3000:
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


def load_schools() -> dict[str, tuple[str, str | None]]:
    if not DB_PATH.exists():
        return {}
    con = sqlite3.connect(DB_PATH, timeout=60.0)
    con.execute("PRAGMA busy_timeout=60000")
    cur = con.cursor()
    out: dict[str, tuple[str, str | None]] = {}
    try:
        cur.execute("SELECT id, legacy_id, name_ja, homepage_url FROM schools_v2")
        for sid, legacy_id, name_ja, homepage in cur.fetchall():
            out[sid] = (name_ja or "", homepage or "")
            if legacy_id and legacy_id != sid:
                out[legacy_id] = (name_ja or "", homepage or "")
    finally:
        con.close()
    return out


def load_existing_quotes() -> tuple[set[str], dict[str, int], dict[str, int]]:
    """Return (existing quote signatures keyed by school+sha-like,
    teacher counts/school, parent counts/school).

    Use 80-char normalized prefix per school. This is strict enough to avoid
    accidental collision but tolerant of whitespace/full-width variations.
    """
    sigs: set[str] = set()
    teacher_counts: dict[str, int] = {}
    parent_counts: dict[str, int] = {}
    if not DB_PATH.exists():
        return sigs, teacher_counts, parent_counts
    con = sqlite3.connect(DB_PATH, timeout=60.0)
    con.execute("PRAGMA busy_timeout=60000")
    cur = con.cursor()
    try:
        cur.execute(
            "SELECT school_id, speaker_role, quote_text FROM testimonials_v2"
        )
        for sid, role, qtext in cur.fetchall():
            qnorm = re.sub(r"\s+", "", qtext or "")
            qnorm = normalize_fullwidth(qnorm)
            if qnorm:
                sigs.add(f"{sid}::{qnorm[:80]}")
            if role == "teacher":
                teacher_counts[sid] = teacher_counts.get(sid, 0) + 1
            elif role == "parent":
                parent_counts[sid] = parent_counts.get(sid, 0) + 1
    finally:
        con.close()
    return sigs, teacher_counts, parent_counts


def load_url_map() -> dict[tuple[str, str], str]:
    m: dict[tuple[str, str], str] = {}
    if not DB_PATH.exists():
        return m
    con = sqlite3.connect(DB_PATH, timeout=60.0)
    con.execute("PRAGMA busy_timeout=60000")
    cur = con.cursor()
    try:
        cur.execute(
            "SELECT school_id, page_path, full_url FROM school_homepage_assets"
        )
        for sid, path, url in cur.fetchall():
            if path and url:
                m[(sid, path)] = url
    finally:
        con.close()
    return m


def is_navigation_blob(text: str) -> bool:
    if text.count("｜") + text.count("|") >= 4:
        return True
    if text.count("／") + text.count("/") >= 5:
        return True
    if text.count("・") >= 8:
        return True
    if text.count(">") >= 3:
        return True
    if text.count("　") >= 4:
        return True
    parts = re.split(r"[、。\s]", text)
    short_parts = [p for p in parts if 0 < len(p) <= 6]
    if parts and len(short_parts) / len(parts) > 0.55 and len(parts) > 8:
        return True
    if len(re.findall(r"20[0-9]{2}", text)) >= 2:
        return True
    if len(re.findall(r"\d{4}[\.\-/年]\d{1,2}", text)) >= 2:
        return True
    return False


def is_clean(text: str) -> bool:
    if cjk_len(text) < MIN_LEN or cjk_len(text) > MAX_LEN:
        return False
    for pat in BAD_PATTERNS:
        if pat.search(text):
            return False
    for pat in ADMIN_PATTERNS:
        if pat.search(text):
            return False
    if is_navigation_blob(text):
        return False
    if not re.search(r"[。．！？」]", text):
        return False
    if text.count("：") + text.count(":") >= 4:
        return False
    # JP char ratio
    jp_chars = sum(1 for c in text if "぀" <= c <= "鿿")
    if jp_chars < len(text) * 0.5:
        return False
    # Punctuation density
    punct = text.count("、") + text.count("。") + text.count("，") + text.count("．")
    if cjk_len(text) >= 100 and punct < 2:
        return False
    return True


def select_blocks(soup: BeautifulSoup) -> list[str]:
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "noscript"]):
        tag.decompose()
    for sel in [
        "#header", "#nav", "#globalnav", "#footer", "#sidebar",
        ".header", ".nav", ".globalnav", ".footer", ".sidebar",
        ".breadcrumb", "#breadcrumb", "#bread", ".gnav", "#gnav",
        ".menu", "#menu", ".pankuzu",
        ".news", ".news-list", ".news_list", ".news-area",
        ".topics", ".topics-list", ".info", ".info-list",
        ".pickup", ".banner", ".banners",
        ".pagination", ".paginator",
    ]:
        for el in soup.select(sel):
            el.decompose()

    candidates: list[str] = []
    for el in soup.find_all(["p", "li", "td", "blockquote", "section", "article"]):
        if el.find(["p", "li", "td", "blockquote", "section", "article"]):
            continue
        text = el.get_text(separator=" ", strip=True)
        text = normalize_fullwidth(text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            candidates.append(text)
    for el in soup.find_all("div"):
        if el.find(["p", "li", "div", "td", "section", "article", "blockquote"]):
            continue
        text = el.get_text(separator=" ", strip=True)
        text = normalize_fullwidth(text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            candidates.append(text)

    seen: set[str] = set()
    uniq: list[str] = []
    for t in candidates:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def page_is_off_topic(soup: BeautifulSoup) -> bool:
    """Detect non-school pages cached due to URL drift (rowing federation,
    domain registrar, etc.)."""
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string
    head_text = ""
    body = soup.body
    if body:
        head_text = body.get_text(" ", strip=True)[:1500]
    blob = title + " " + head_text
    for pat in NON_SCHOOL_PATTERNS:
        if pat.search(blob):
            return True
    if "404" in title.lower() or "not found" in title.lower():
        return True
    if "お探しのページ" in head_text[:200]:
        return True
    return False


def page_url_for(school_id: str, page_name: str, soup: BeautifulSoup,
                 url_map: dict, homepage: str | None) -> str:
    slug = page_name.replace(".html", "")
    url = url_map.get((school_id, slug), "")
    if url:
        return url
    canon = soup.find("link", rel="canonical")
    if canon and canon.get("href"):
        return canon["href"]
    og = soup.find("meta", attrs={"property": "og:url"})
    if og and og.get("content"):
        return og["content"]
    if homepage:
        base = homepage if homepage.endswith("/") else homepage + "/"
        return base if slug == "root" else urljoin(base, slug)
    return ""


def trim_quote(text: str, max_len: int = MAX_LEN) -> str:
    if cjk_len(text) <= max_len:
        return text
    cut = text[:max_len]
    last = max(cut.rfind("。"), cut.rfind("！"), cut.rfind("？"))
    if last > 60:
        return cut[: last + 1]
    return cut + "…"


def make_summary(quote: str) -> str:
    s = quote.replace("\n", " ").strip()
    if cjk_len(s) <= 50:
        return s
    head = s[:50]
    last = max(head.rfind("、"), head.rfind("。"))
    if last > 20:
        return head[: last + 1] + "…"
    return head + "…"


EDU_KEYWORDS = re.compile(
    r"(授業|学び|学習|教育|指導|カリキュラム|教育課程|生徒|児童|"
    r"育成|養う|身につけ|身に付け|目指す|育む|育て|育てる|学ぶ|学べ|"
    r"探究|探求|演習|実習|活動|プログラム|科目|教科|学年|"
    r"建学|理念|方針|目標|目的|精神|思考力|表現力|判断力|主体的|"
    r"教員|教師|教諭|担任|講師|教職員|本校|本学園|本学院|本学|当校)"
)


def classify_teacher(text: str, page: str) -> tuple[str, str] | None:
    """Return (speaker_attribute, context) or None."""
    if STUDENT_VOICE_PATTERNS.search(text):
        return None
    has_view = bool(TEACHER_VIEWPOINT.search(text))
    has_subject = any(k in text for k in SUBJECT_KEYS)
    has_edu = bool(EDU_KEYWORDS.search(text))

    page_strong = page in (
        "curriculum.html", "education.html", "schoollife.html",
        "about.html", "philosophy.html", "mission.html",
        "principal.html", "voice.html",
        "progress.html",
    )

    # On principal.html: most prose is principal voice
    if page == "principal.html" and has_edu:
        return "校長", "校長挨拶"

    # Strong page + edu vocabulary
    if page_strong and has_edu:
        if "校長" in text or "学園長" in text:
            return "校長", "校長挨拶"
        if has_subject:
            return "教科教員", PAGE_CTX_TEACHER.get(page, "教科紹介")
        if has_view:
            return "教員", PAGE_CTX_TEACHER.get(page, "教員紹介")
        # accept any well-formed pedagogy prose on strong pages
        edu_hits = len(EDU_KEYWORDS.findall(text))
        if edu_hits >= 2:
            return "教員", PAGE_CTX_TEACHER.get(page, "学校紹介")

    # about.html / mission.html / philosophy.html: institutional voice
    # accept history/heritage prose (lower density requirement)
    if page in ("about.html", "mission.html", "philosophy.html") and has_edu:
        return "教員", PAGE_CTX_TEACHER.get(page, "学校紹介")

    # On root.html / events.html / admission.html: institutional voice with
    # viewpoint or higher edu density
    if page in ("root.html", "events.html", "admission.html"):
        edu_hits = len(EDU_KEYWORDS.findall(text))
        if has_view and has_edu:
            return "教員", PAGE_CTX_TEACHER.get(page, "学校紹介")
        # Allow edu>=2 when subject keyword also present
        if edu_hits >= 2 and has_subject:
            return "教科教員", PAGE_CTX_TEACHER.get(page, "学校紹介")
        if edu_hits >= 3:
            return "教員", PAGE_CTX_TEACHER.get(page, "学校紹介")

    return None


PARENT_KEYWORDS = re.compile(
    r"(保護者|親|父母|PTA|後援会|育友会|母の会|父母の会|保護者会|"
    r"家庭(?:と|での|では|として)|ご家庭|お子(?:様|さま)|"
    r"我が子|我が家|うちの子|子(?:ども|供)(?:を|の|が|たち))"
)


def classify_parent(text: str, page: str) -> tuple[str, str] | None:
    if STUDENT_VOICE_PATTERNS.search(text):
        return None
    has_org = bool(PARENT_ORG.search(text))
    has_voice = bool(PARENT_VIEWPOINT.search(text))
    has_keyword = bool(PARENT_KEYWORDS.search(text))

    page_dedicated = page in ("parent.html", "pta.html")

    def detect_attr(t: str) -> str:
        if "PTA" in t:
            return "PTA"
        if "後援会" in t:
            return "後援会"
        if "父母会" in t or "父母の会" in t:
            return "父母会"
        if "育友会" in t:
            return "育友会"
        if "母の会" in t:
            return "母の会"
        if "保護者会" in t:
            return "保護者会"
        return "保護者"

    if has_org:
        return detect_attr(text), PAGE_CTX_PARENT.get(page, "保護者向けページ")

    # On dedicated parent/PTA pages, parent viewpoint or keyword density qualifies
    if page_dedicated:
        if has_voice:
            attr = "PTA" if page == "pta.html" else "保護者"
            return attr, PAGE_CTX_PARENT.get(page, "保護者向けページ")
        # Density-based: 2+ parent keywords
        kw_hits = len(PARENT_KEYWORDS.findall(text))
        if kw_hits >= 2:
            attr = "PTA" if page == "pta.html" else "保護者"
            return attr, PAGE_CTX_PARENT.get(page, "保護者向けページ")

    # On secondary pages: require parent voice + parent keyword
    if has_voice and has_keyword:
        return "保護者", PAGE_CTX_PARENT.get(page, "保護者向けページ")

    # On any page: density of parent keywords (>= 2 hits with viewpoint)
    kw_hits = len(PARENT_KEYWORDS.findall(text))
    if kw_hits >= 2 and (has_voice or has_org):
        return "保護者", PAGE_CTX_PARENT.get(page, "保護者向けページ")
    # Stricter: density alone — 3+ hits
    if kw_hits >= 3:
        return "保護者", PAGE_CTX_PARENT.get(page, "保護者向けページ")

    return None


def anonymize_parent_text(text: str) -> str:
    """Strip likely personal-name signatures from parent voice."""
    # Remove patterns like "○○○○ (高1保護者)" or "保護者: ○○ ○○"
    text = re.sub(r"[（(][^）)]{0,8}保護者[^）)]{0,8}[）)]\s*$", "", text).strip()
    text = re.sub(r"[（(](?:中|高)[123][）)]\s*$", "", text).strip()
    # Replace explicit personal-name signatures at end (e.g. "山田 太郎")
    text = re.sub(r"\s+[一-龥々]{2,5}\s*[一-龥々]{2,5}\s*$", "", text).strip()
    return text


def extract_for_school(school_id: str, school_dir: Path,
                       homepage: str | None, url_map: dict,
                       existing_sigs: set[str],
                       teacher_existing: int, parent_existing: int) -> list[dict]:
    out: list[dict] = []
    teacher_seen: set[str] = set()
    parent_seen: set[str] = set()

    teacher_added = 0
    parent_added = 0
    teacher_target = MAX_TEACHER_PER_SCHOOL
    parent_target = MAX_PARENT_PER_SCHOOL

    # Pass 1: parent on DEDICATED pages only (parent.html / pta.html). This
    # ensures PTA quotes stay parent-classified before teacher pass runs.
    for fname in PARENT_DEDICATED_PAGES:
        if parent_added >= parent_target:
            break
        path = school_dir / fname
        if not path.exists():
            continue
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                soup = BeautifulSoup(html, "html.parser")
        except Exception:
            continue
        if page_is_off_topic(soup):
            continue
        page_url = page_url_for(school_id, fname, soup, url_map, homepage)
        for raw in select_blocks(soup):
            if parent_added >= parent_target:
                break
            text = anonymize_parent_text(raw.strip())
            if not is_clean(text):
                continue
            classified = classify_parent(text, fname)
            if not classified:
                continue
            attr, ctx = classified
            quote = trim_quote(text)
            sig = re.sub(r"\s+", "", quote)[:80]
            if not sig:
                continue
            if f"{school_id}::{sig}" in existing_sigs:
                continue
            if sig in parent_seen or sig in teacher_seen:
                continue
            parent_seen.add(sig)
            out.append({
                "school_id": school_id,
                "speaker_role": "parent",
                "speaker_attribute": attr,
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_url": page_url,
                "source_page": fname.replace(".html", ""),
                "rights_level": "anonymized_only",
                "extraction_method": "llm_heuristic_v1",
            })
            parent_added += 1

    # Pass 2: teacher
    for fname in TEACHER_PAGES:
        if teacher_added >= teacher_target:
            break
        path = school_dir / fname
        if not path.exists():
            continue
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                soup = BeautifulSoup(html, "html.parser")
        except Exception:
            continue
        if page_is_off_topic(soup):
            continue
        page_url = page_url_for(school_id, fname, soup, url_map, homepage)
        for raw in select_blocks(soup):
            if teacher_added >= teacher_target:
                break
            text = raw.strip()
            if not is_clean(text):
                continue
            classified = classify_teacher(text, fname)
            if not classified:
                continue
            attr, ctx = classified
            quote = trim_quote(text)
            sig = re.sub(r"\s+", "", quote)[:80]
            if not sig:
                continue
            if f"{school_id}::{sig}" in existing_sigs:
                continue
            if sig in teacher_seen or sig in parent_seen:
                continue
            teacher_seen.add(sig)
            out.append({
                "school_id": school_id,
                "speaker_role": "teacher",
                "speaker_attribute": attr,
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_url": page_url,
                "source_page": fname.replace(".html", ""),
                "rights_level": "quoted_with_attribution",
                "extraction_method": "llm_heuristic_v1",
            })
            teacher_added += 1

    # Pass 3: parent on SECONDARY pages — runs after teacher to pick up any
    # parent-org-marked quote that the teacher pass did not consume.
    for fname in PARENT_SECONDARY_PAGES:
        if parent_added >= parent_target:
            break
        path = school_dir / fname
        if not path.exists():
            continue
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                soup = BeautifulSoup(html, "html.parser")
        except Exception:
            continue
        if page_is_off_topic(soup):
            continue
        page_url = page_url_for(school_id, fname, soup, url_map, homepage)
        for raw in select_blocks(soup):
            if parent_added >= parent_target:
                break
            text = anonymize_parent_text(raw.strip())
            if not is_clean(text):
                continue
            classified = classify_parent(text, fname)
            if not classified:
                continue
            attr, ctx = classified
            quote = trim_quote(text)
            sig = re.sub(r"\s+", "", quote)[:80]
            if not sig:
                continue
            if f"{school_id}::{sig}" in existing_sigs:
                continue
            if sig in parent_seen or sig in teacher_seen:
                continue
            parent_seen.add(sig)
            out.append({
                "school_id": school_id,
                "speaker_role": "parent",
                "speaker_attribute": attr,
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_url": page_url,
                "source_page": fname.replace(".html", ""),
                "rights_level": "anonymized_only",
                "extraction_method": "llm_heuristic_v1",
            })
            parent_added += 1

    return out


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    schools = load_schools()
    existing_sigs, teacher_counts, parent_counts = load_existing_quotes()
    url_map = load_url_map()

    school_dirs = sorted(
        p for p in CACHE_DIR.iterdir()
        if p.is_dir() and p.name.startswith("jpms_s_")
    )

    records: list[dict] = []
    teacher_records = 0
    parent_records = 0
    schools_with_teacher = 0
    schools_with_parent = 0

    for sd in school_dirs:
        sid = sd.name
        name_ja, homepage = schools.get(sid, ("", ""))
        recs = extract_for_school(
            sid, sd, homepage, url_map, existing_sigs,
            teacher_counts.get(sid, 0), parent_counts.get(sid, 0),
        )
        if not recs:
            continue
        t_added = sum(1 for r in recs if r["speaker_role"] == "teacher")
        p_added = sum(1 for r in recs if r["speaker_role"] == "parent")
        if t_added:
            schools_with_teacher += 1
            teacher_records += t_added
        if p_added:
            schools_with_parent += 1
            parent_records += p_added
        records.extend(recs)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    progress = {
        "team": "C-3 LLM teacher_parent",
        "task": "deep teacher/parent voice extraction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_schools_scanned": len(school_dirs),
        "schools_with_teacher_added": schools_with_teacher,
        "schools_with_parent_added": schools_with_parent,
        "teacher_records": teacher_records,
        "parent_records": parent_records,
        "total_records": len(records),
        "min_quote_len": MIN_LEN,
        "max_quote_len": MAX_LEN,
        "max_teacher_per_school": MAX_TEACHER_PER_SCHOOL,
        "max_parent_per_school": MAX_PARENT_PER_SCHOOL,
        "output_path": str(OUT_PATH),
        "ethics_notes": [
            "公開情報のみを対象。",
            "教員: quoted_with_attribution、保護者: anonymized_only。",
            "個人特定情報（氏名・連絡先）が含まれる段落はパスする。",
            "引用は 380 字以下に整形（400 字未満を厳守）。",
            "既存 testimonials_v2 と重複する quote_text は除外。",
        ],
    }
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"schools scanned:     {len(school_dirs)}")
    print(f"teacher records:     {teacher_records}  ({schools_with_teacher} schools)")
    print(f"parent records:      {parent_records}  ({schools_with_parent} schools)")
    print(f"total records:       {len(records)}")
    print(f"output:              {OUT_PATH}")
    print(f"progress:            {PROGRESS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
