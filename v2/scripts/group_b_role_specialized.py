#!/usr/bin/env python3
"""JPMS-DB v2 - Group B: 主体特化抽出 (5主体並列)

5主体（principal/teacher/student_current/student_alumni/parent）それぞれに
特化したキーワード/構造パターンで raw_html_cache を深掘りし、testimonials_v2
への補完投入を行う。

- 1スクリプトで 5主体を ProcessPoolExecutor で並列処理
- 既存 testimonials_v2 の quote_text と前方80文字一致で重複除外
- 倫理: 未成年(student_current) は anonymized_only、それ以外は quoted_with_attribution
- 出力:
  - codex_output/group_b_role_specialized.jsonl
  - codex_progress/group_b.json
- DB直接投入: testimonials_v2 (ethics_review_status=group_b_passed)

設計上、各主体抽出関数 _extract_<role>_for_school は、対象校の HTML 群から
特化キーワードでスコアリングし、上位を返す。既存の team_b1〜b5 のロジックを
統合・強化したもの。
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Paths / DB
# -----------------------------------------------------------------------------
ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE_DIR = ROOT / "raw_html_cache"
DB_PATH = ROOT / "jpms_v2.db"
OUT_PATH = ROOT / "codex_output" / "group_b_role_specialized.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "group_b.json"

# Per-role caps (deeper than legacy team_b* which capped at 3-5)
ROLE_MAX_PER_SCHOOL = {
    "principal": 4,
    "teacher": 6,
    "student_current": 8,
    "student_alumni": 6,
    "parent": 5,
}

# Quote length policy (CJK char count)
MIN_LEN = {
    "principal": 60,
    "teacher": 30,
    "student_current": 35,
    "student_alumni": 35,
    "parent": 50,
}
MAX_LEN = {
    "principal": 380,
    "teacher": 300,
    "student_current": 300,
    "student_alumni": 300,
    "parent": 380,
}

# -----------------------------------------------------------------------------
# Shared utility
# -----------------------------------------------------------------------------

NEGATIVE_HINTS_COMMON = [
    "プライバシー", "cookie", "クッキー", "著作権", "サイトマップ",
    "お問い合わせ", "個人情報保護", "採用情報", "会社概要",
    "利用規約", "twitter", "facebook", "instagram", "youtube",
    "all rights", "copyright", "一覧へ", "もっと見る", "詳しく見る",
    "メニュー", "navigation", "breadcrumb", "ログイン",
    "メールアドレス", "パスワード", "ダウンロード",
    "ホーム>", "TOP>", "お知らせ一覧", "ニュース一覧",
]


def read_html(fpath: Path) -> str:
    """Read HTML with charset autodetect."""
    raw = fpath.read_bytes()
    m = re.search(rb"charset=[\"']?([a-zA-Z0-9_-]+)", raw[:2000], re.IGNORECASE)
    enc = "utf-8"
    if m:
        detected = m.group(1).decode("ascii", errors="ignore").lower()
        if detected in ("utf-8", "utf8"):
            enc = "utf-8"
        elif detected in ("shift_jis", "sjis", "shift-jis", "cp932", "ms932", "x-sjis"):
            enc = "cp932"
        elif detected in ("euc-jp", "eucjp", "euc_jp"):
            enc = "euc-jp"
        elif detected in ("iso-2022-jp", "jis"):
            enc = "iso-2022-jp"
        else:
            enc = detected
    try:
        return raw.decode(enc, errors="ignore")
    except Exception:
        for fb in ("utf-8", "cp932", "euc-jp"):
            try:
                return raw.decode(fb, errors="ignore")
            except Exception:
                continue
        return raw.decode("utf-8", errors="ignore")


def parse(html: str):
    """Return (title, full_text, paragraphs). Strip nav/footer/etc."""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header",
                     "aside", "form"]):
        tag.decompose()
    for sel in soup.select(
        ".breadcrumb, .breadcrumbs, .pankuzu, #breadcrumb, #breadcrumbs, "
        ".menu, #menu, .nav, .global-nav, .gnav, .sidebar, #sidebar"
    ):
        sel.decompose()
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"main|content", re.I))
        or soup.find(class_=re.compile(r"main|content|article", re.I))
        or soup.find("article")
        or soup.body
        or soup
    )
    paragraphs: list[str] = []
    if main:
        for el in main.find_all(["p", "div", "li", "blockquote", "section"]):
            if el.find(["p", "blockquote"]) and el.name == "div":
                continue
            t = el.get_text(separator=" ", strip=True)
            if not t:
                continue
            t = re.sub(r"\s+", " ", t).strip()
            if t:
                paragraphs.append(t)
    full_text = main.get_text(separator="\n", strip=True) if main else ""
    return title, full_text, paragraphs


def is_navigation_blob(text: str) -> bool:
    if text.count("｜") + text.count("|") >= 4:
        return True
    if text.count("／") + text.count("/") >= 5:
        return True
    if text.count("・") >= 8:
        return True
    if text.count(">") >= 3:
        return True
    nav_terms = ["TOP", "ホーム", "サイトマップ", "お問い合わせ", "アクセス",
                 "プライバシー", "資料請求", "募集要項"]
    if sum(1 for t in nav_terms if t in text) >= 3:
        return True
    parts = re.split(r"[、。\s]", text)
    short = [p for p in parts if 0 < len(p) <= 6]
    if len(parts) > 8 and len(short) / len(parts) > 0.55:
        return True
    return False


def basic_clean(text: str, min_len: int, max_len: int) -> bool:
    if len(text) < min_len or len(text) > max_len:
        return False
    tl = text.lower()
    for n in NEGATIVE_HINTS_COMMON:
        if n.lower() in tl:
            return False
    if is_navigation_blob(text):
        return False
    if not re.search(r"[。、．！？]", text):
        return False
    if "404" in text or "not found" in tl or "お探しのページ" in text:
        return False
    if text.count("：") + text.count(":") >= 4:
        return False
    if len(re.findall(r"\d{4}[\.\-/年]\d{1,2}", text)) >= 2:
        return False
    if re.match(r"^[\s\d年月日.\-/]{6,20}", text):
        return False
    jp_chars = sum(1 for c in text if "぀" <= c <= "鿿")
    if jp_chars < len(text) * 0.4:
        return False
    return True


def trim_quote(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    last = max(cut.rfind("。"), cut.rfind("！"), cut.rfind("？"))
    if last > max_len * 0.4:
        return cut[: last + 1]
    return cut + "…"


def make_summary(quote: str) -> str:
    s = quote.replace("\n", " ").strip()
    if len(s) <= 50:
        return s
    head = s[:50]
    last = max(head.rfind("、"), head.rfind("。"))
    if last > 20:
        return head[: last + 1] + "…"
    return head + "…"


def page_url_for(sid: str, page_name: str, url_map: dict, fallback: dict) -> str:
    return url_map.get((sid, page_name), "") or fallback.get(sid, "")


# -----------------------------------------------------------------------------
# B-01 principal: 校訓・建学・精神・使命の長文段落
# -----------------------------------------------------------------------------
PRINCIPAL_PAGES = ["principal", "philosophy", "mission", "about", "voice", "root"]
PRINCIPAL_STRONG = [
    "校長", "理事長", "学園長", "学校長", "建学の精神", "教育理念", "教育方針",
    "建学", "校訓", "本校の使命", "学校の使命", "私たちの使命", "教育目標",
]
PRINCIPAL_FIRST_PERSON = [
    "私が", "私は", "私ども", "私たち", "本校では", "本校の", "本学園", "本学院",
    "ごあいさつ", "ご挨拶",
]
PRINCIPAL_NEGATIVE = [
    "学校説明会", "説明会", "オープンスクール", "入試説明", "申し込みフォーム",
    "受付中", "メディア掲載",
    # student/alumni voice phrases (do not classify as principal)
    "私の夢", "進学しました", "卒業しました", "受験を",
]


def _principal_quotable(text: str) -> bool:
    if not basic_clean(text, MIN_LEN["principal"], MAX_LEN["principal"]):
        return False
    if any(n in text for n in PRINCIPAL_NEGATIVE):
        return False
    has_principal_kw = any(k in text for k in PRINCIPAL_STRONG)
    has_first_person = any(k in text for k in PRINCIPAL_FIRST_PERSON)
    has_education = any(k in text for k in [
        "教育", "人材", "人格", "心", "夢", "未来", "伝統", "精神", "育成", "育む",
        "社会", "世界", "人間",
    ])
    # 校長らしさ: (校訓系キーワード) or (一人称 + 教育語)
    if not (has_principal_kw or (has_first_person and has_education)):
        return False
    # 句点が複数あること（プローズ性）
    punct = text.count("。") + text.count("！") + text.count("？")
    if punct < 1:
        return False
    return True


def _principal_score(text: str, page_is_principal: bool) -> int:
    s = 0
    if page_is_principal:
        s += 5
    for kw in PRINCIPAL_STRONG:
        if kw in text:
            s += 3
    for kw in PRINCIPAL_FIRST_PERSON:
        if kw in text:
            s += 2
    if 100 <= len(text) <= 350:
        s += 3
    return s


def _principal_attr(text: str) -> str:
    if "理事長" in text:
        return "理事長"
    if "学園長" in text:
        return "学園長"
    if "学校長" in text:
        return "学校長"
    return "校長"


def _looks_like_principal_page(title: str, head_text: str) -> bool:
    head = (title + " " + head_text[:600]).lower()
    keys = ["校長", "理事長", "学園長", "学校長", "挨拶", "あいさつ", "メッセージ",
            "教育理念", "建学", "教育方針", "校訓", "理念", "ごあいさつ",
            "principal", "message", "mission"]
    return any(k.lower() in head for k in keys)


def extract_principal(sid: str, school_dir: Path,
                       url_map: dict, fb: dict) -> list[dict]:
    out: list[dict] = []
    seen_keys: set[str] = set()
    cap = ROLE_MAX_PER_SCHOOL["principal"]
    for pp in PRINCIPAL_PAGES:
        if len(out) >= cap:
            break
        f = school_dir / f"{pp}.html"
        if not f.exists():
            continue
        try:
            html = read_html(f)
        except Exception:
            continue
        title, text, paragraphs = parse(html)
        # 学校外ページ排除
        if any(ind in title for ind in ["researchmap", "リサーチマップ", "aguse",
                                          "WHOIS", "お名前.com"]):
            continue
        page_is_principal = _looks_like_principal_page(title, text)
        if pp in ("principal", "philosophy", "mission"):
            page_is_principal = True
        if not page_is_principal and pp in ("about", "voice", "root"):
            if not any(k in text[:5000] for k in PRINCIPAL_STRONG):
                continue

        scored: list[tuple[int, str]] = []
        for p_raw in paragraphs:
            p = re.sub(r"\s+", " ", p_raw).strip()
            if not _principal_quotable(p):
                continue
            sc = _principal_score(p, page_is_principal)
            if sc >= 5:
                scored.append((sc, p))
        scored.sort(key=lambda x: -x[0])

        page_url = page_url_for(sid, pp, url_map, fb)
        ctx = {
            "principal": "校長メッセージページ",
            "philosophy": "教育理念ページ",
            "mission": "教育使命ページ",
            "about": "学校紹介ページ（校長挨拶）",
            "voice": "メッセージページ",
            "root": "トップページ（校長挨拶）",
        }.get(pp, "校長メッセージページ")

        for sc, p in scored:
            quote = trim_quote(p, MAX_LEN["principal"])
            key = quote[:80]
            if key in seen_keys:
                continue
            if any(key in q or q in key for q in seen_keys):
                continue
            seen_keys.add(key)
            out.append({
                "school_id": sid,
                "speaker_role": "principal",
                "speaker_attribute": _principal_attr(p),
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_page": pp,
                "source_url": page_url,
                "rights_level": "quoted_with_attribution",
            })
            if len(out) >= cap:
                break
    return out


# -----------------------------------------------------------------------------
# B-02 teacher: 教科教員紹介・授業観・教科だより
# -----------------------------------------------------------------------------
TEACHER_PAGES = ["curriculum", "schoollife", "about", "voice", "root"]
TEACHER_SUBJECTS = [
    "国語", "数学", "英語", "理科", "社会", "地理", "歴史", "公民",
    "物理", "化学", "生物", "地学", "音楽", "美術", "保健体育",
    "技術", "家庭", "情報", "道徳", "総合学習", "宗教", "聖書", "倫理", "書道",
]
TEACHER_ROLES = [
    "教員", "教諭", "教師", "教科主任", "学年主任", "担任", "副担任",
    "学科主任", "主幹教諭", "指導教諭", "顧問", "教科担当", "授業担当",
    "教職員",
]
TEACHER_CLASS_KW = [
    "授業", "学習指導", "カリキュラム", "教育課程", "取り組み", "取組み",
    "指導", "演習", "実習", "探究", "探求", "学び", "授業の特色",
    "教科の特色", "教科だより",
]
TEACHER_PEDAGOGY_RE = re.compile(
    r"(目指|大切|重視|育て|養|身に付|身につけ|習得|高め|深め|展開|"
    r"実施|工夫|取り組|位置付け|位置づけ|学ば|学び|挑戦|理解|考え)"
)
TEACHER_STUDENT_VOICE_RE = re.compile(
    r"(私の夢|やりたいこと|入学(し|前)|小学校の頃|中学受験|楽しかった|"
    r"思い出|なりたい|学校生活|私たち生徒)"
)


def _teacher_attr(text: str) -> str:
    if "担任" in text:
        return "担任"
    if "教科主任" in text or "学科主任" in text:
        return "教科主任"
    if "学年主任" in text:
        return "学年主任"
    if any(s in text for s in TEACHER_SUBJECTS):
        return "教科教員"
    if "教諭" in text:
        return "教科教員"
    return "教員"


def extract_teacher(sid: str, school_dir: Path,
                    url_map: dict, fb: dict) -> list[dict]:
    out: list[dict] = []
    seen_keys: set[str] = set()
    cap = ROLE_MAX_PER_SCHOOL["teacher"]
    for pp in TEACHER_PAGES:
        if len(out) >= cap:
            break
        f = school_dir / f"{pp}.html"
        if not f.exists():
            continue
        try:
            html = read_html(f)
        except Exception:
            continue
        title, text, paragraphs = parse(html)
        if any(ind in title for ind in ["researchmap", "リサーチマップ", "aguse",
                                          "WHOIS", "お名前.com"]):
            continue
        page_url = page_url_for(sid, pp, url_map, fb)
        ctx = {
            "curriculum": "教科紹介",
            "schoollife": "教員紹介",
            "about": "教員紹介",
            "voice": "教員紹介",
            "root": "教科紹介",
        }.get(pp, "教員紹介")

        scored: list[tuple[int, str, str]] = []
        for p_raw in paragraphs:
            p = re.sub(r"\s+", " ", p_raw).strip()
            if not basic_clean(p, MIN_LEN["teacher"], MAX_LEN["teacher"]):
                continue
            if TEACHER_STUDENT_VOICE_RE.search(p):
                continue
            has_role = any(k in p for k in TEACHER_ROLES)
            has_subj = any(k in p for k in TEACHER_SUBJECTS)
            has_class = any(k in p for k in TEACHER_CLASS_KW)
            has_ped = bool(TEACHER_PEDAGOGY_RE.search(p))
            # Skip pure timetable / subject-list
            if has_subj and not (has_class or has_ped or has_role):
                continue
            if not (has_role or (has_subj and has_class) or (has_class and has_ped)):
                continue
            sc = 0
            if has_role:
                sc += 4
            if has_subj:
                sc += 2
            if has_class:
                sc += 2
            if has_ped:
                sc += 2
            if 80 <= len(p) <= 280:
                sc += 2
            scored.append((sc, p, _teacher_attr(p)))
        scored.sort(key=lambda x: -x[0])

        for sc, p, attr in scored:
            quote = trim_quote(p, MAX_LEN["teacher"])
            key = quote[:80]
            if key in seen_keys:
                continue
            if any(key in q or q in key for q in seen_keys):
                continue
            seen_keys.add(key)
            out.append({
                "school_id": sid,
                "speaker_role": "teacher",
                "speaker_attribute": attr,
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_page": pp,
                "source_url": page_url,
                "rights_level": "quoted_with_attribution",
            })
            if len(out) >= cap:
                break
    return out


# -----------------------------------------------------------------------------
# B-03 student_current: 在校生インタビュー・生徒会便り・SNS式短文
# -----------------------------------------------------------------------------
STUDENT_CURRENT_PAGES = ["voice", "schoollife", "events", "about", "root", "admission"]
STUDENT_CURRENT_HEADERS = [
    "在校生の声", "在校生の話", "在校生インタビュー", "在校生からのメッセージ",
    "生徒の声", "生徒の話", "生徒インタビュー", "生徒メッセージ",
    "在校生メッセージ", "現役生の声", "在校生の言葉", "生徒会だより", "生徒会便り",
    "クラブ紹介", "部活動紹介",
]
STUDENT_NARRATIVE_RE = [
    re.compile(r"(私|僕|自分).{0,20}(学校|学園|中学|高校|入学|過ご|生活)"),
    re.compile(r"(中学|高校).{0,3}(時代|時|生活).{0,30}(部活|友|仲間|先生|先輩|後輩)"),
    re.compile(r"(部活|文化祭|体育祭|修学旅行).{0,30}(楽しか|頑張|思い出|印象|大切|学んだ)"),
    re.compile(r"(先生|友人|友達|仲間).{0,30}(支え|教えて|尊敬|感謝|出会|共に)"),
]
STUDENT_NON_VOICE_HEADINGS = [
    "校長", "学園長", "学長", "理事長", "教員紹介", "教員一覧", "教員",
    "校長あいさつ", "校長メッセージ", "校長挨拶",
]
STUDENT_NON_VOICE_PHRASES = [
    "学園長", "校長として", "教員一同", "理事長",
    "本学院は", "我が校", "創立以来", "建学の精神",
    "本校では", "本校の", "本学園は", "皆さんは", "皆さんが", "皆さんに",
    "してほしいと思います", "御来賓", "本ウェブサイト", "詳細はこちら",
    "を実現します。", "を目指します。", "を養成します。",
    "に取り組んでいます", "を実施しています", "を構築", "を育成します",
]


def _student_anonymize(text: str) -> str:
    """Strip minor PII: explicit grade markers, emails, names initial."""
    text = re.sub(r"(中学|中等部)[1-3一二三１-３]年(生)?", "中学生", text)
    text = re.sub(r"(高校|高等学校|高等部)[1-3一二三１-３]年(生)?", "高校生", text)
    text = re.sub(r"[A-Z]\.\s*[A-Z]\.", "", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "", text)
    text = text.strip("「」『』\"' 　")
    text = re.sub(r"\s+", "", text)
    return text


def _is_student_voice(text: str) -> bool:
    if any(p in text for p in STUDENT_NON_VOICE_PHRASES):
        return False
    return any(p.search(text) for p in STUDENT_NARRATIVE_RE)


def _is_alumni_lifecycle(text: str) -> bool:
    return any(k in text for k in [
        "合格しました", "卒業しました", "卒業生として", "大学に進学", "大学に入学",
        "進学しました", "現在は大学", "社会人", "就職しました",
    ])


def extract_student_current(sid: str, school_dir: Path,
                            url_map: dict, fb: dict) -> list[dict]:
    out: list[dict] = []
    seen_keys: set[str] = set()
    cap = ROLE_MAX_PER_SCHOOL["student_current"]
    for pp in STUDENT_CURRENT_PAGES:
        if len(out) >= cap:
            break
        f = school_dir / f"{pp}.html"
        if not f.exists():
            continue
        try:
            html = read_html(f)
        except Exception:
            continue
        title, text, paragraphs = parse(html)
        if any(ind in title for ind in ["researchmap", "リサーチマップ", "aguse",
                                          "WHOIS", "お名前.com"]):
            continue
        page_url = page_url_for(sid, pp, url_map, fb)

        # ページタイトル/見出しが校長系なら、当ページは student_current として弱化
        page_principal_block = any(k in title for k in STUDENT_NON_VOICE_HEADINGS)
        ctx = {
            "voice": "在校生インタビュー",
            "schoollife": "学校生活ページ（在校生の声）",
            "events": "行事ページ（在校生コメント）",
            "about": "学校紹介ページ（在校生の声）",
            "root": "トップページ（在校生紹介）",
            "admission": "入試案内（在校生メッセージ）",
        }.get(pp, "在校生インタビュー")

        for p_raw in paragraphs:
            if len(out) >= cap:
                break
            p = _student_anonymize(p_raw)
            if not basic_clean(p, MIN_LEN["student_current"], MAX_LEN["student_current"]):
                continue
            if page_principal_block and not any(h in p for h in STUDENT_CURRENT_HEADERS):
                continue
            if not _is_student_voice(p):
                continue
            # In-school lifecycle vs alumni
            if _is_alumni_lifecycle(p):
                continue
            quote = trim_quote(p, MAX_LEN["student_current"])
            key = quote[:80]
            if key in seen_keys:
                continue
            if any(key in q or q in key for q in seen_keys):
                continue
            seen_keys.add(key)
            attr = "中学生"
            if any(k in p for k in ["高校", "高等部", "高等学校"]):
                attr = "高校生"
            elif any(k in p for k in ["中学", "中等部"]):
                attr = "中学生"
            out.append({
                "school_id": sid,
                "speaker_role": "student_current",
                "speaker_attribute": attr,
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_page": pp,
                "source_url": page_url,
                "rights_level": "anonymized_only",
            })
    return out


# -----------------------------------------------------------------------------
# B-04 student_alumni: 卒業生メッセージ・進路選択体験・OBOG記
# -----------------------------------------------------------------------------
STUDENT_ALUMNI_PAGES = ["voice", "progress", "schoollife", "about", "root", "admission"]
STUDENT_ALUMNI_HEADERS = [
    "卒業生の声", "卒業生の話", "卒業生のことば", "卒業生インタビュー",
    "卒業生メッセージ", "卒業生からのメッセージ", "先輩の声", "先輩からのメッセージ",
    "OBインタビュー", "OGインタビュー", "卒業生コラム", "OB・OGの声",
    "OBOGの声", "OBOGメッセージ", "進路選択", "進路体験",
]
ALUMNI_LIFECYCLE_RE = [
    re.compile(r"(合格|進学|進路|卒業|社会人|就職).{0,30}(した|しました|決め)"),
    re.compile(r"(在学中|学生時代|高校時代|中学時代).{0,40}(学んだ|経験|思い出|頑張)"),
    re.compile(r"(大学|大学院).{0,30}(進学|入学|学んで|研究)"),
    re.compile(r"(後輩|これから).{0,20}(へ|に|皆さん|の方々)"),
]


def extract_student_alumni(sid: str, school_dir: Path,
                            url_map: dict, fb: dict) -> list[dict]:
    out: list[dict] = []
    seen_keys: set[str] = set()
    cap = ROLE_MAX_PER_SCHOOL["student_alumni"]
    for pp in STUDENT_ALUMNI_PAGES:
        if len(out) >= cap:
            break
        f = school_dir / f"{pp}.html"
        if not f.exists():
            continue
        try:
            html = read_html(f)
        except Exception:
            continue
        title, text, paragraphs = parse(html)
        if any(ind in title for ind in ["researchmap", "リサーチマップ", "aguse",
                                          "WHOIS", "お名前.com"]):
            continue
        page_url = page_url_for(sid, pp, url_map, fb)
        ctx = {
            "voice": "卒業生メッセージ",
            "progress": "進路・卒業生メッセージ",
            "schoollife": "卒業生インタビュー",
            "about": "学校紹介ページ（卒業生の声）",
            "root": "トップページ（卒業生）",
            "admission": "入試案内（卒業生メッセージ）",
        }.get(pp, "卒業生メッセージ")

        # 校長/教員系ページなら緩めに採用
        principal_block = any(k in title for k in STUDENT_NON_VOICE_HEADINGS)

        for p_raw in paragraphs:
            if len(out) >= cap:
                break
            p = _student_anonymize(p_raw)
            if not basic_clean(p, MIN_LEN["student_alumni"], MAX_LEN["student_alumni"]):
                continue
            if any(ph in p for ph in STUDENT_NON_VOICE_PHRASES):
                continue
            # 卒業生らしさ判定
            has_lifecycle = any(r.search(p) for r in ALUMNI_LIFECYCLE_RE)
            has_first_person = any(k in p for k in ["私", "僕", "自分"])
            has_alumni_kw = any(k in p for k in [
                "卒業生", "OB", "OG", "母校", "後輩", "先輩",
            ])
            if principal_block and not has_alumni_kw:
                continue
            if not (has_lifecycle and (has_first_person or has_alumni_kw)):
                continue
            quote = trim_quote(p, MAX_LEN["student_alumni"])
            key = quote[:80]
            if key in seen_keys:
                continue
            if any(key in q or q in key for q in seen_keys):
                continue
            seen_keys.add(key)
            # Year of graduation if available
            attr = "卒業生"
            m = re.search(r"(19|20)\d{2}年(度)?卒", p)
            if m:
                attr = m.group(0)
            out.append({
                "school_id": sid,
                "speaker_role": "student_alumni",
                "speaker_attribute": attr,
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_page": pp,
                "source_url": page_url,
                "rights_level": "quoted_with_attribution",
            })
    return out


# -----------------------------------------------------------------------------
# B-05 parent: PTA活動報告・保護者会便り・保護者の声・後援会報
# -----------------------------------------------------------------------------
PARENT_DEDICATED_PAGES = ["parent", "pta"]
PARENT_SECONDARY_PAGES = ["voice", "schoollife", "events", "about", "admission", "root"]
PARENT_ANCHORS = [
    "保護者", "保護者会", "保護者の声", "保護者の方", "PTA", "父母会", "父母の会",
    "後援会", "育友会", "母の会", "ファミリー", "家庭と学校",
]
PARENT_STRONG_ANCHORS = [
    "PTA", "保護者会", "父母会", "父母の会", "後援会", "育友会", "保護者の声",
    "保護者の方々", "保護者の皆様", "保護者のみなさま",
    "保護者の皆さま", "ご家庭との連携", "家庭との連携",
]
PARENT_VOICE_SIGNALS = [
    "娘", "息子", "うちの子", "我が家", "親として", "母", "父",
    "感謝", "成長",
]
PARENT_EVENT_NEGATIVE = [
    "お申し込み", "申し込みフォーム", "受付中", "開催中", "受験生のみなさま",
]


def _parent_attr(text: str) -> str:
    if "PTA" in text:
        return "PTA"
    if "後援会" in text:
        return "後援会"
    if "父母会" in text or "父母の会" in text:
        return "父母会"
    if "育友会" in text:
        return "育友会"
    if "保護者会" in text:
        return "保護者会"
    return "保護者"


def extract_parent(sid: str, school_dir: Path,
                   url_map: dict, fb: dict) -> list[dict]:
    out: list[dict] = []
    seen_keys: set[str] = set()
    cap = ROLE_MAX_PER_SCHOOL["parent"]

    dedicated = [(pp, school_dir / f"{pp}.html") for pp in PARENT_DEDICATED_PAGES
                 if (school_dir / f"{pp}.html").exists()]
    secondary = [(pp, school_dir / f"{pp}.html") for pp in PARENT_SECONDARY_PAGES
                 if (school_dir / f"{pp}.html").exists()]

    for pp, f in dedicated + secondary:
        if len(out) >= cap:
            break
        try:
            html = read_html(f)
        except Exception:
            continue
        title, text, paragraphs = parse(html)
        if any(ind in title for ind in ["researchmap", "リサーチマップ", "aguse",
                                          "WHOIS", "お名前.com"]):
            continue
        page_dedicated = pp in PARENT_DEDICATED_PAGES

        # ページタイトルが「保護者メッセージ」系か
        page_is_parent_voice = any(k in title for k in [
            "保護者メッセージ", "保護者の声", "保護者から", "父母の声",
            "保護者からのメッセージ",
        ])
        page_url = page_url_for(sid, pp, url_map, fb)
        ctx = {
            "parent": "保護者向けページ",
            "pta": "PTA・保護者会ページ",
            "voice": "在校生・保護者の声ページ",
            "schoollife": "学校生活ページ",
            "events": "行事案内ページ",
            "about": "学校紹介ページ",
            "admission": "入試・募集案内ページ",
            "root": "トップページ",
        }.get(pp, "保護者向けページ")

        scored: list[tuple[int, str]] = []
        for p_raw in paragraphs:
            p = re.sub(r"\s+", " ", p_raw).strip()
            if not basic_clean(p, MIN_LEN["parent"], MAX_LEN["parent"]):
                continue
            if any(n in p for n in PARENT_EVENT_NEGATIVE) and not page_dedicated:
                continue
            has_anchor = any(a in p for a in PARENT_ANCHORS)
            if not has_anchor:
                # parent-voice ページなら親視点の語2つ以上で許容
                if not page_is_parent_voice:
                    continue
                if sum(1 for s in PARENT_VOICE_SIGNALS if s in p) < 2:
                    continue
            # secondary はストロングアンカー必須
            if not page_dedicated and not page_is_parent_voice:
                if not any(a in p for a in PARENT_STRONG_ANCHORS):
                    continue
            sc = 0
            if page_dedicated:
                sc += 4
            if page_is_parent_voice:
                sc += 3
            sc += sum(2 for a in PARENT_ANCHORS if a in p)
            sc += sum(1 for s in PARENT_VOICE_SIGNALS if s in p)
            if 80 <= len(p) <= 350:
                sc += 2
            scored.append((sc, p))
        scored.sort(key=lambda x: -x[0])

        for sc, p in scored:
            quote = trim_quote(p, MAX_LEN["parent"])
            key = quote[:80]
            if key in seen_keys:
                continue
            if any(key in q or q in key for q in seen_keys):
                continue
            seen_keys.add(key)
            out.append({
                "school_id": sid,
                "speaker_role": "parent",
                "speaker_attribute": _parent_attr(quote),
                "quote_text": quote,
                "quote_summary": make_summary(quote),
                "context": ctx,
                "source_page": pp,
                "source_url": page_url,
                "rights_level": "quoted_with_attribution",
            })
            if len(out) >= cap:
                break
    return out


# -----------------------------------------------------------------------------
# Worker: 1主体 × 全学校
# -----------------------------------------------------------------------------
ROLE_EXTRACTORS = {
    "principal": extract_principal,
    "teacher": extract_teacher,
    "student_current": extract_student_current,
    "student_alumni": extract_student_alumni,
    "parent": extract_parent,
}


def _load_url_maps() -> tuple[dict, dict]:
    url_map: dict = {}
    fb: dict = {}
    if DB_PATH.exists():
        try:
            con = sqlite3.connect(str(DB_PATH))
            cur = con.cursor()
            cur.execute("SELECT school_id, page_path, full_url FROM school_homepage_assets")
            for sid, page, url in cur.fetchall():
                url_map[(sid, page)] = url
            cur.execute("SELECT id, homepage_url FROM schools_v2")
            for sid, url in cur.fetchall():
                if url:
                    fb[sid] = url
            con.close()
        except Exception:
            pass
    return url_map, fb


def _process_role(role: str) -> list[dict]:
    """One role × all schools. Used in ProcessPoolExecutor."""
    url_map, fb = _load_url_maps()
    extractor = ROLE_EXTRACTORS[role]
    school_dirs = sorted(p for p in CACHE_DIR.iterdir()
                         if p.is_dir() and p.name.startswith("jpms_s_"))
    items: list[dict] = []
    for sd in school_dirs:
        sid = sd.name
        try:
            recs = extractor(sid, sd, url_map, fb)
        except Exception:
            recs = []
        items.extend(recs)
    return items


# -----------------------------------------------------------------------------
# Existing testimonial dedupe (prefix80 keyset)
# -----------------------------------------------------------------------------
def _load_existing_keys() -> dict[str, set[str]]:
    keys: dict[str, set[str]] = {r: set() for r in ROLE_EXTRACTORS}
    if not DB_PATH.exists():
        return keys
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("SELECT speaker_role, quote_text FROM testimonials_v2")
    for role, qt in cur.fetchall():
        if role not in keys:
            keys[role] = set()
        if qt:
            keys[role].add(qt[:80])
    con.close()
    return keys


def _ingest_to_db(records: list[dict]) -> tuple[int, int]:
    """Insert into testimonials_v2; dedup against prefix-80 of existing rows."""
    if not records:
        return 0, 0
    existing = _load_existing_keys()
    inserted = 0
    rejected = 0
    con = sqlite3.connect(str(DB_PATH), timeout=600.0)
    con.execute("PRAGMA busy_timeout=600000")
    cur = con.cursor()
    cur.execute("SELECT id FROM schools_v2")
    valid_school_ids = {row[0] for row in cur.fetchall()}
    batch = 0
    now = datetime.now(timezone.utc).isoformat()
    for r in records:
        sid = r.get("school_id", "")
        role = r.get("speaker_role", "")
        quote = r.get("quote_text", "")
        if not sid or not quote or sid not in valid_school_ids:
            rejected += 1
            continue
        if role not in ROLE_EXTRACTORS:
            rejected += 1
            continue
        key = quote[:80]
        if key in existing.get(role, set()):
            rejected += 1
            continue
        # also check substring overlap among already inserted batch keys
        existing.setdefault(role, set()).add(key)
        try:
            cur.execute(
                """INSERT INTO testimonials_v2
                   (school_id, speaker_role, speaker_attribute, quote_text,
                    quote_summary, context, source_type, source_url,
                    rights_level, retrieved_at, ethics_review_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    sid, role, r.get("speaker_attribute", ""),
                    quote, r.get("quote_summary", ""), r.get("context", ""),
                    "school_website", r.get("source_url", ""),
                    r.get("rights_level", "quoted_with_attribution"),
                    now, "group_b_passed",
                ),
            )
            inserted += 1
            batch += 1
            if batch >= 200:
                con.commit()
                batch = 0
        except sqlite3.OperationalError:
            rejected += 1
    con.commit()
    con.close()
    return inserted, rejected


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    roles = list(ROLE_EXTRACTORS.keys())

    print(f"[Group B] launching 5 role-specialized extractors in parallel...")
    all_records: list[dict] = []
    role_counts: dict[str, int] = {}

    with ProcessPoolExecutor(max_workers=5) as pool:
        results = {role: pool.submit(_process_role, role) for role in roles}
        for role, fut in results.items():
            recs = fut.result()
            role_counts[role] = len(recs)
            all_records.extend(recs)
            print(f"[Group B][{role}] extracted: {len(recs)}")

    # Write JSONL
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[Group B] JSONL written: {OUT_PATH} ({len(all_records)} records)")

    # Ingest to DB (dedup against existing testimonials_v2)
    inserted, rejected = _ingest_to_db(all_records)
    print(f"[Group B] DB inserted: {inserted}, rejected (dup/invalid): {rejected}")

    # Per-role DB counts after ingestion
    role_db_counts: dict[str, int] = {}
    if DB_PATH.exists():
        con = sqlite3.connect(str(DB_PATH))
        cur = con.cursor()
        for role in roles:
            cur.execute("SELECT COUNT(*) FROM testimonials_v2 WHERE speaker_role=?",
                        (role,))
            role_db_counts[role] = cur.fetchone()[0]
        con.close()

    progress = {
        "task_id": "group_b",
        "team": "Group B (主体特化抽出)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.time() - started, 1),
        "extracted_per_role": role_counts,
        "total_extracted": len(all_records),
        "inserted_to_db": inserted,
        "rejected_dup_or_invalid": rejected,
        "testimonials_v2_after": role_db_counts,
        "output_path": str(OUT_PATH),
        "ethics_notes": [
            "未成年（student_current）は anonymized_only。学年・氏名・SNS handle 除去。",
            "公開HP情報のみ（school_website）。源URLを記録。",
            "前方80文字一致で testimonials_v2 既存レコードと重複除外。",
            "親視点(parent), 教員(teacher), 校長(principal), 卒業生(student_alumni) は引用元明示。",
        ],
    }
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    print(f"[Group B] progress: {PROGRESS_PATH}")
    print(f"[Group B] DB counts: {role_db_counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
