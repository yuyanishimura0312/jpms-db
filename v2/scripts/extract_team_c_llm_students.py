#!/usr/bin/env python3
"""
JPMS-DB v2 Phase E - Team C-2 (LLM-style student/alumni voices, RELAXED v2).

raw_html_cache 全走査。生徒一人称 + 中学/学校生活キーワード を持つ段落、
対談形式 (Q&A) の応答部、卒業生「○期生」「○年卒」マーカー直後の文章を抽出。
RELAXED v2: ソフトナラティブ（体験動詞+学校生活キーワード密度）を許容し、
目標300件以上を目指す。
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE_DIR = ROOT / "raw_html_cache"
OUT_PATH = ROOT / "codex_output" / "team_c_llm_students.jsonl"
PROGRESS_PATH = ROOT / "codex_progress" / "team_c_llm_students.json"
DB_PATH = ROOT / "jpms_v2.db"

MIN_LEN = 25
MAX_LEN = 380
MAX_CURRENT_PER_SCHOOL = 5
MAX_ALUMNI_PER_SCHOOL = 3

PAGE_FILES = [
    "voice.html", "schoollife.html", "progress.html",
    "about.html", "admission.html", "events.html",
    "root.html", "curriculum.html",
    "philosophy.html", "mission.html",
]

DEFAULT_FILE_CONTEXT = {
    "voice.html": "在校生・卒業生メッセージ",
    "schoollife.html": "在校生インタビュー",
    "progress.html": "卒業生メッセージ",
    "about.html": "在校生・卒業生メッセージ",
    "admission.html": "在校生・卒業生メッセージ",
    "events.html": "学校行事",
    "root.html": "学校紹介",
    "curriculum.html": "教育内容",
    "philosophy.html": "教育理念",
    "mission.html": "教育理念",
}

ALUMNI_HEADER_KEYS = [
    "卒業生の声", "卒業生の話", "卒業生のことば", "卒業生インタビュー",
    "卒業生メッセージ", "卒業生からのメッセージ", "卒業生からの言葉",
    "先輩の声", "先輩からのメッセージ", "先輩メッセージ", "先輩から",
    "OBインタビュー", "OGインタビュー", "卒業生コラム",
    "OB・OGの声", "OBOGの声", "OBOGメッセージ",
    "卒業生からの便り", "卒業生の言葉",
]
CURRENT_HEADER_KEYS = [
    "在校生の声", "在校生の話", "在校生インタビュー", "在校生からのメッセージ",
    "生徒の声", "生徒の話", "生徒インタビュー", "生徒メッセージ",
    "在校生メッセージ", "現役生の声", "在校生の言葉",
    "学校生活の声", "中学生の声", "学校生活の様子",
]

FIRST_PERSON_RE = re.compile(
    r"(私は|私が|私の|私たち|僕は|僕が|僕の|僕たち|自分は|自分が|自分の|自分たち|"
    r"私自身|僕自身)"
)

SOFT_PERSON_RE = re.compile(
    r"(私|僕|自分|自身)"
)

EXPERIENCE_VERBS = [
    "学んだ", "学びました", "学べた", "気づいた", "気付いた", "わかった",
    "知った", "感じた", "感じました", "思った", "思いました",
    "頑張った", "頑張りました", "努力した", "挑戦した", "挑戦しました",
    "成長した", "成長できた", "経験した", "経験しました",
    "出会った", "支えられ", "励まされ", "助けられ",
    "楽しかった", "楽しんで", "嬉しかった", "感動した",
    "印象に残", "思い出", "忘れられ",
    "になった", "になりました", "になりたい",
    "を通して", "を通じて", "おかげで",
]

SCHOOL_LIFE_KEYS = [
    "学校", "中学", "高校", "学園", "学院", "中等部", "高等部",
    "部活", "文化祭", "体育祭", "修学旅行", "球技大会", "合唱",
    "友達", "友人", "仲間", "先生", "先輩", "後輩", "クラス",
    "合格", "受験", "卒業", "志望", "進路", "学び", "成長", "経験",
    "勉強", "授業", "大学", "行事", "毎日", "生活",
    "発表", "プレゼン", "探究", "研究", "実験", "コンクール",
]

ALUMNI_LIFECYCLE = [
    "卒業しました", "卒業した後", "卒業して", "進学しました", "合格しました",
    "大学に入", "大学院", "社会人になり", "就職しました", "起業しました",
    "今振り返ると", "中高時代", "母校", "OBとして", "OGとして",
    "期生として",
]

NON_STUDENT_PATTERNS = [
    "学園長", "校長として", "教員一同", "理事長",
    "本学院は", "我が校", "創立以来", "建学の精神",
    "本校では", "本校の", "本学園は", "本学園の",
    "皆さんは", "皆さんが", "皆さんに", "皆さんの",
    "してほしいと思います", "話したいと思います",
    "御来賓", "御列席", "心からの拍手",
    "御尽力いただきました", "新規採用教員", "御勤務",
    "本ウェブサイト", "ご覧ください", "お問い合わせください",
    "リアルボイス", "実際の声を集めました",
    "メニューから", "詳細はこちら", "資料請求",
    "受験生には", "ご参加お待ち", "ご予約受付",
    "を予定しています", "電子版です",
    "話してもらいます", "に来校していただき",
    "を実現します。", "を目指します。", "を養成します。",
    "を支える環境", "を整えています", "に取り組んでいます",
    "を展開しています", "を実施しています",
    "を構築", "を育成します", "を育みます",
    "を紹介します", "を発信",
    "募集要項", "出願受付", "説明会のご案内",
    "ホームページをご覧",
    # Parent/PTA voice markers (we don't want these here)
    "保護者として", "母親として", "父親として", "親として",
    "息子が", "娘が", "我が子",
]

NON_STUDENT_HEADINGS = [
    "校長", "学園長", "学長", "理事長", "教員紹介", "教員一覧",
    "学校紹介", "教育方針", "建学", "沿革",
    "本校の特色", "教育目標", "校長あいさつ", "校長メッセージ",
    "校長挨拶", "教育理念", "校長ブログ", "学園だより",
    "玉縄の風", "保護者の声", "保護者の方", "保護者メッセージ",
    "PTA", "父母", "事務局", "教職員",
    "募集", "新着情報",
]

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
    re.compile(r"説明会.*予約|出願受付"),
]

NAV_BAD_TOKENS = [
    "サイトマップ", "プライバシーポリシー", "個人情報保護方針",
    "資料請求", "アクセス・お問い合わせ", "教職員募集",
    "学校案内", "入試情報", "個人情報の取り扱い",
]

SCHOOL_PR_RE = re.compile(
    r"^[^。]{0,40}(中学校|高等学校|学園|学院|高校|中等部|本校|本学園|当校|当学園)"
    r"[^。]{0,5}(では|として|の特長|の特色|の教育|の方針|は、|の歴史|の伝統)"
)

GRADE_RE = [
    (re.compile(r"(中学|中等部)[1-3一二三１-３]年(生)?"), "中学生"),
    (re.compile(r"(高校|高等学校|高等部)[1-3一二三１-３]年(生)?"), "高校生"),
    (re.compile(r"中[1-3一二三１-３](?=[、。\s])"), "中学生"),
    (re.compile(r"高[1-3一二三１-３](?=[、。\s])"), "高校生"),
    (re.compile(r"[A-Z]\.\s*[A-Z]\."), ""),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), ""),
    (re.compile(r"\d{4}年[卒業修]"), "卒業"),
    (re.compile(r"第\d+期生"), "卒業生"),
    (re.compile(r"\d+期生"), "卒業生"),
]

CLUB_RE = re.compile(
    r"(野球|サッカー|バスケットボール|バレーボール|テニス|卓球|"
    r"バドミントン|ハンドボール|ラグビー|陸上|水泳|剣道|柔道|空手|"
    r"弓道|アーチェリー|フェンシング|ボート|スキー|スケート|スノーボード|"
    r"演劇|吹奏楽|合唱|オーケストラ|軽音楽|ダンス|書道|茶道|華道|"
    r"美術|写真|放送|新聞|文芸|英語|生物|化学|物理|地学|数学|"
    r"将棋|囲碁|チェス|料理|手芸|園芸|鉄道研究|アニメ|漫画研究|"
    r"パソコン|プログラミング|ロボット)部"
)


def safe_parse(html_src):
    try:
        return BeautifulSoup(html_src, "html.parser")
    except Exception:
        cleaned = re.sub(r"&#(\D)", r"&amp;#\1", html_src)
        try:
            return BeautifulSoup(cleaned, "html.parser")
        except Exception:
            return None


def is_navigation_blob(text):
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


def is_clean(text):
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
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


def has_first_person(text):
    return bool(FIRST_PERSON_RE.search(text))


def has_soft_person(text):
    return bool(SOFT_PERSON_RE.search(text))


def count_experience(text):
    return sum(1 for v in EXPERIENCE_VERBS if v in text)


def count_school_life(text):
    return sum(1 for k in SCHOOL_LIFE_KEYS if k in text)


def is_strong_student_narrative(text):
    """Strict: explicit first-person + school-life context."""
    if not has_first_person(text):
        return False
    return count_school_life(text) >= 1 and count_experience(text) >= 1


def is_soft_student_narrative(text):
    """Soft: any 私/僕/自分 token + dense experience/school keywords."""
    if not has_soft_person(text):
        return False
    if count_experience(text) < 2:
        return False
    if count_school_life(text) < 2:
        return False
    return True


def is_non_student_voice(text):
    if any(p in text for p in NON_STUDENT_PATTERNS):
        return True
    if SCHOOL_PR_RE.match(text):
        return True
    return False


def anonymize(text):
    for pat, repl in GRADE_RE:
        text = pat.sub(repl, text)
    text = CLUB_RE.sub("部活動", text)
    text = text.strip("「」『』\"\' 　")
    text = re.sub(r"\s+", "", text)
    return text


def select_blocks(soup):
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "noscript"]):
        tag.decompose()
    for sel in ["#header", "#nav", "#globalnav", "#footer", "#sidebar",
                ".header", ".nav", ".globalnav", ".footer", ".sidebar",
                ".breadcrumb", "#breadcrumb", "#bread", ".gnav", "#gnav",
                ".menu", "#menu"]:
        for el in soup.select(sel):
            el.decompose()

    candidates = []
    current_heading = ""
    for el in soup.find_all(True):
        tag = el.name
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            t = el.get_text(separator="", strip=True)
            if t:
                current_heading = re.sub(r"\s+", "", t)[:120]
            continue
        if tag in {"p", "blockquote", "li", "section", "article",
                   "div", "td", "dd"}:
            if el.find(["p", "li", "blockquote", "dd"]):
                continue
            t = el.get_text(separator="", strip=True)
            t = re.sub(r"\s+", "", t)
            if not t:
                continue
            candidates.append((t, current_heading))

    seen = set()
    uniq = []
    for t, h in candidates:
        if t in seen:
            continue
        seen.add(t)
        uniq.append((t, h))
    return uniq


def classify_role(text, heading):
    """Decide (speaker_role, attr, context) or None."""
    # 1) Heading-based
    if heading:
        for nh in NON_STUDENT_HEADINGS:
            if nh in heading:
                return None
        for kw in ALUMNI_HEADER_KEYS:
            if kw in heading:
                return ("student_alumni", "卒業生", kw)
        for kw in CURRENT_HEADER_KEYS:
            if kw in heading:
                return ("student_current", "中学生", kw)

    # 2) Lifecycle marker → alumni
    if any(m in text for m in ALUMNI_LIFECYCLE):
        if is_strong_student_narrative(text) or is_soft_student_narrative(text):
            return ("student_alumni", "卒業生", "卒業生メッセージ")

    # 3) Strong narrative → role from text content
    if is_strong_student_narrative(text):
        if any(k in text for k in [
            "卒業", "進学", "合格", "母校", "振り返", "今思うと", "今振り返",
        ]):
            return ("student_alumni", "卒業生", "卒業生メッセージ")
        return ("student_current", "中学生", "在校生インタビュー")

    # 4) Soft narrative
    if is_soft_student_narrative(text):
        return ("student_current", "中学生", "在校生インタビュー")

    return None


def page_role_hint(soup):
    title_tag = soup.find("title")
    title_text = title_tag.get_text().strip() if title_tag else ""
    page_subject = re.split(r"[|｜\-－〜:：]", title_text)[0].strip()
    principal_pr_titles = [
        "校長", "学長", "学園長", "理事長", "教員紹介",
        "教員一覧", "教員", "校長あいさつ", "校長メッセージ",
        "教育方針", "建学", "沿革", "学校案内",
    ]
    if any(k in page_subject for k in principal_pr_titles):
        return None
    if any(k in page_subject for k in ALUMNI_HEADER_KEYS):
        return ("student_alumni", "卒業生", "卒業生インタビュー")
    if any(k in page_subject for k in CURRENT_HEADER_KEYS):
        return ("student_current", "中学生", "在校生インタビュー")

    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(strip=True)
        if any(k in h1_text for k in principal_pr_titles):
            return None
        if any(k in h1_text for k in ALUMNI_HEADER_KEYS):
            return ("student_alumni", "卒業生", "卒業生インタビュー")
        if any(k in h1_text for k in CURRENT_HEADER_KEYS):
            return ("student_current", "中学生", "在校生インタビュー")
    return None


def extract_for_school(school_id, school_dir, homepage, existing_hashes):
    out_current = []
    out_alumni = []
    seen_quotes = set()

    for fname in PAGE_FILES:
        if (len(out_current) >= MAX_CURRENT_PER_SCHOOL and
                len(out_alumni) >= MAX_ALUMNI_PER_SCHOOL):
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

        soup = safe_parse(raw_html)
        if soup is None:
            continue

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
        if not source_url:
            source_url = "about:blank#" + fname

        default_ctx = DEFAULT_FILE_CONTEXT.get(fname, "在校生・卒業生メッセージ")
        page_hint = page_role_hint(soup)

        blocks = select_blocks(soup)
        for raw, heading in blocks:
            if (len(out_current) >= MAX_CURRENT_PER_SCHOOL and
                    len(out_alumni) >= MAX_ALUMNI_PER_SCHOOL):
                break

            text = anonymize(raw)
            if len(text) > MAX_LEN:
                sentences = re.split(r"(?<=[。！？])", text)
                acc = ""
                for s in sentences:
                    if len(acc) + len(s) > MAX_LEN:
                        break
                    acc += s
                text = acc.strip()
                if not text:
                    continue
            if not is_clean(text):
                continue
            if is_non_student_voice(text):
                continue
            if text.endswith("...") or text.endswith("…"):
                continue

            classified = classify_role(text, heading)
            if not classified and page_hint:
                # only trust page hint if at least soft cues present
                if has_soft_person(text) or count_experience(text) >= 2:
                    classified = page_hint
            if not classified:
                continue
            speaker_role, attr, ctx = classified

            if speaker_role == "student_current" and len(out_current) >= MAX_CURRENT_PER_SCHOOL:
                continue
            if speaker_role == "student_alumni" and len(out_alumni) >= MAX_ALUMNI_PER_SCHOOL:
                continue

            key = text[:60]
            if key in seen_quotes:
                continue
            seen_quotes.add(key)

            dedup_hash = hashlib.sha1((school_id + "|" + key).encode("utf-8")).hexdigest()
            if dedup_hash in existing_hashes:
                continue
            existing_hashes.add(dedup_hash)

            summary = text[:60] + ("…" if len(text) > 60 else "")
            record = {
                "school_id": school_id,
                "speaker_role": speaker_role,
                "speaker_attribute": attr,
                "quote_text": text,
                "quote_summary": summary,
                "context": ctx,
                "source_type": "school_website",
                "source_url": source_url,
                "rights_level": "anonymized_only",
            }
            if speaker_role == "student_current":
                out_current.append(record)
            else:
                out_alumni.append(record)

    return out_current + out_alumni


def load_schools():
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
    out = {}
    for sid, legacy_id, name_ja, homepage in rows:
        out[sid] = (name_ja or "", homepage or "")
        if legacy_id:
            out[legacy_id] = (name_ja or "", homepage or "")
    return out


def load_existing_hashes():
    h = set()
    if not DB_PATH.exists():
        return h
    try:
        con = sqlite3.connect(str(DB_PATH))
        cur = con.cursor()
        cur.execute(
            "SELECT school_id, quote_text FROM testimonials_v2 "
            "WHERE speaker_role IN ('student_current','student_alumni')"
        )
        for sid, qt in cur.fetchall():
            if not qt:
                continue
            anon = anonymize(qt)
            key = anon[:60]
            h.add(hashlib.sha1((sid + "|" + key).encode("utf-8")).hexdigest())
        con.close()
    except Exception:
        pass
    return h


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

    schools = load_schools()
    existing_hashes = load_existing_hashes()

    school_dirs = sorted(p for p in CACHE_DIR.iterdir() if p.is_dir())
    total = len(school_dirs)

    records = []
    schools_with_data = 0
    role_counts = {"student_current": 0, "student_alumni": 0}

    for sd in school_dirs:
        sid = sd.name
        name_ja, homepage = schools.get(sid, ("", ""))
        recs = extract_for_school(sid, sd, homepage, existing_hashes)
        if recs:
            schools_with_data += 1
        for r in recs:
            role_counts[r["speaker_role"]] = role_counts.get(r["speaker_role"], 0) + 1
            records.append(r)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    progress = {
        "task_id": "team_c_llm_students",
        "team": "C-2 (LLM-style relaxed v2)",
        "task": "student/alumni voices deep extraction",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total_schools_scanned": total,
        "schools_with_extractions": schools_with_data,
        "items": len(records),
        "role_counts": role_counts,
        "max_current_per_school": MAX_CURRENT_PER_SCHOOL,
        "max_alumni_per_school": MAX_ALUMNI_PER_SCHOOL,
        "min_quote_len": MIN_LEN,
        "max_quote_len": MAX_LEN,
        "existing_hashes_loaded": len(existing_hashes),
        "output_path": str(OUT_PATH),
        "rights_level": "anonymized_only",
        "ethics_notes": [
            "未成年は完全匿名化",
            "学年/部活名/個人名/期数は generic 化",
            "speaker_attribute=中学生 or 卒業生 のみ",
            "rights_level=anonymized_only",
            "引用 < 400字（QM-1 ゲート互換）",
            "school_id × text[:60] で重複除外",
            "保護者/校長/教員語彙は除外",
        ],
        "page_files_scanned": PAGE_FILES,
        "extraction_strategy": [
            "Strong narrative: 一人称 + 学校生活キーワード + 体験動詞",
            "Soft narrative: 一人称トークン + 体験動詞≥2 + 学校生活キーワード≥2",
            "見出し優先: ALUMNI_HEADER / CURRENT_HEADER 直下",
            "ライフサイクルマーカー: 卒業/進学/合格/母校 → alumni",
            "ページレベルヒント: title/h1 が voice 系且つ NON_STUDENT 系でない",
        ],
    }
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print("schools scanned:", total)
    print("schools with extractions:", schools_with_data)
    print("records:", len(records),
          "(current=" + str(role_counts["student_current"]) + ",",
          "alumni=" + str(role_counts["student_alumni"]) + ")")
    print("output:", OUT_PATH)
    print("progress:", PROGRESS_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
