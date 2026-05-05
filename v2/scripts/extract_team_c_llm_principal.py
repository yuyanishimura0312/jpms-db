#!/usr/bin/env python3
"""JPMS-DB v2 Strategy C-1: LLM-style context extraction - Principal voice depth.
Existing B-1 already extracted 430 principal quotes for ~80 schools.
This C-1 targets the remaining ~144 schools (or schools with <3 quotes).
3-axis scoring: philosophy keyword x personal tone x sentence length.
"""
import os, re, json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

BASE = Path("/Users/nishimura+/projects/research/jpms-db/v2")
CACHE = BASE / "raw_html_cache"
DB = BASE / "jpms_v2.db"
OUT = BASE / "codex_output" / "team_c_llm_principal.jsonl"
PROGRESS = BASE / "codex_progress" / "team_c_llm_principal.json"

PAGE_PRIORITY = [
    "principal", "philosophy", "mission", "about", "voice",
    "root", "curriculum", "schoollife", "parent", "admission",
    "events", "progress",
]

PAGE_TITLE_KEYWORDS = [
    "校長", "理事長", "学園長", "挨拶", "あいさつ", "メッセージ", "message",
    "学校長", "教育理念", "建学", "教育方針", "校訓", "理念",
    "ごあいさつ", "ご挨拶", "principal", "message from", "mission",
    "philosophy", "about", "学校案内",
]

PRINCIPAL_STRONG = [
    "校長", "理事長", "学園長", "学校長",
    "建学の精神", "教育理念", "教育方針", "建学", "校訓",
    "創立者", "創設者", "初代校長",
]

PERSONAL_TONE = [
    "私は", "私たち", "私ども", "わたし",
    "本校", "本学園", "本学院", "当校", "当学園",
    "と思います", "と考えます", "と信じ", "を願って",
    "を目指し", "を育て", "を育み", "はぐくみ",
    "いきたい", "まいります", "おります", "いただきたい",
]

PHILOSOPHY_KW = [
    "人格", "人間", "人材", "使命", "志", "夢", "理想",
    "社会", "世界", "未来", "伝統", "精神", "心",
    "誠実", "誠", "愛", "徳", "善", "真理", "知性",
    "主体的", "自主", "自立", "自律", "創造",
    "探究", "挑戦", "貢献", "奉仕", "尊重", "寛容",
]

NEGATIVE_HINTS = [
    "プライバシー", "cookie", "クッキー", "著作権", "サイトマップ",
    "お問い合わせ", "個人情報保護", "採用情報", "会社概要",
    "利用規約", "twitter", "facebook", "instagram", "youtube",
    "all rights", "copyright", "一覧へ", "もっと見る", "詳しく見る",
    "メニュー", "navigation", "breadcrumb", "ログイン",
    "メールアドレス", "パスワード", "ダウンロード",
    "ホーム>", "TOP>",
    "学校説明会", "体験会", "オープンスクール",
    "入試説明", "入試要項", "お申し込み", "申し込みフォーム",
    "実施します", "開催します", "開催中", "受付中",
    "聖光祭", "体育祭", "文化祭",
    "受験生のみなさま", "受験生の方へ",
    "お知らせ", "NEWS",
    "メディア掲載",
]

NON_SCHOOL_INDICATORS = [
    "ローイング協会", "researchmap", "リサーチマップ",
    "ドメイン", "お名前.com", "aguse", "サクラインターネット",
    "WHOIS", "このページは", "このドメイン",
]

def get_url_map():
    if not DB.exists():
        return {}, {}
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT school_id, page_path, full_url FROM school_homepage_assets")
    m = {}
    for sid, page, url in cur.fetchall():
        m[(sid, page)] = url
    cur.execute("SELECT id, homepage_url FROM schools_v2")
    fb = {}
    for sid, url in cur.fetchall():
        if url:
            fb[sid] = url
    conn.close()
    return m, fb

def load_existing_quote_hashes():
    if not DB.exists():
        return set(), {}
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT school_id, quote_text FROM testimonials_v2")
    s = set()
    head_map = {}
    for sid, q in cur.fetchall():
        if not q:
            continue
        head = q.strip()[:80]
        h = hashlib.md5(f"{sid}|{head}".encode("utf-8")).hexdigest()
        s.add(h)
        head_map.setdefault(sid, []).append(head)
    conn.close()
    return s, head_map

def load_existing_principal_count_per_school():
    if not DB.exists():
        return {}
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT school_id, COUNT(*) FROM testimonials_v2 WHERE speaker_role IN (\"principal\",\"chairperson\",\"school_director\") GROUP BY school_id")
    d = dict(cur.fetchall())
    conn.close()
    return d

def make_hash(sid, quote):
    head = quote.strip()[:80]
    return hashlib.md5(f"{sid}|{head}".encode("utf-8")).hexdigest()

def extract_text_and_paragraphs(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    for sel in soup.select(".breadcrumb, .breadcrumbs, .pankuzu, #breadcrumb, #breadcrumbs, .menu, #menu, .nav, .global-nav, .gnav, .sidebar, #sidebar"):
        sel.decompose()
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    main = soup.find("main") or soup.find(id=re.compile(r"main|content", re.I)) \
           or soup.find(class_=re.compile(r"main|content|article", re.I)) \
           or soup.find("article") or soup.body or soup
    paragraphs = []
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

def looks_like_principal_page(title, text):
    head = (title + " " + text[:600]).lower()
    for kw in PAGE_TITLE_KEYWORDS:
        if kw.lower() in head:
            return True
    return False

def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n+", text) if p.strip()]

def clean_paragraph(p):
    p = re.sub(r"^[^。]*?(ホーム|TOP|HOME)\s*[>＞»]\s*[^。]*?[>＞»]\s*[^。]*?(?=[一-龯ぁ-んァ-ヶ])", "", p)
    p = re.sub(r"^[^。]{0,40}[>＞»][^。]{0,40}[>＞»][^。]{0,40}(?=[一-龯])", "", p)
    return p.strip()

def is_quotable(p):
    if len(p) < 60 or len(p) > 700:
        return False
    pl = p.lower()
    for n in NEGATIVE_HINTS:
        if n.lower() in pl:
            return False
    if p.count("|") >= 3 or p.count("・") >= 8:
        return False
    if p.count(">") >= 2:
        return False
    if len(re.findall(r"\d{4}[\.\-/年]\d{1,2}", p)) >= 2:
        return False
    if re.search(r"20\d{2}[\.\-/年]\s?\d{1,2}[\.\-/月]", p):
        return False
    if re.match(r"^[\s\d年月日.\-/]{6,20}", p):
        return False
    news_indicators = ["成果報告会を実施", "ベスト8", "優勝", "第1位", "第2位", "第3位", "入賞",
                       "出場決定", "出場しました", "大会において", "選手権",
                       "掲載されました", "ご報告", "実施しました"]
    if sum(1 for ind in news_indicators if ind in p) >= 1:
        return False
    voice_indicators = ["学園生活を振り返", "高校時代", "思い出", "卒業生として",
                        "頂きました", "頂いた", "進学しましたが", "進路を選ぶ"]
    if sum(1 for ind in voice_indicators if ind in p) >= 2:
        return False
    if "404" in p or "not found" in pl or "お探しのページ" in p:
        return False
    if p.count("校長日記") >= 1 or p.count("新年のご挨拶") >= 2:
        return False
    if p.count("　") >= 4:
        return False
    jp_chars = sum(1 for c in p if "぀" <= c <= "鿿")
    if jp_chars < len(p) * 0.4:
        return False
    punct = p.count("、") + p.count("。") + p.count("，")
    if len(p) >= 80 and punct < 2:
        return False
    if "。" not in p and "！" not in p and "？" not in p:
        return False
    if re.search(r"[\w\.\-]+@[\w\.\-]+", p):
        return False
    if re.search(r"\d{2,4}-\d{2,4}-\d{4}", p):
        return False
    return True

def score_paragraph_3axis(p, page_is_principal):
    axis1 = 0
    for kw in PRINCIPAL_STRONG:
        if kw in p:
            axis1 += 3
    for kw in PHILOSOPHY_KW:
        if kw in p:
            axis1 += 1
    if page_is_principal:
        axis1 += 4
    axis2 = 0
    for kw in PERSONAL_TONE:
        if kw in p:
            axis2 += 1
    if p.endswith(("。", "」")):
        axis2 += 1
    L = len(p)
    if 120 <= L <= 400:
        axis3 = 4
    elif 80 <= L < 120 or 400 < L <= 500:
        axis3 = 2
    elif 60 <= L < 80 or 500 < L <= 700:
        axis3 = 1
    else:
        axis3 = 0
    if axis1 == 0:
        return 0
    if axis2 == 0:
        return 0
    return axis1 + axis2 + axis3

def trim_quote(p, max_len=380):
    if len(p) <= max_len:
        return p
    cut = p[:max_len]
    last = max(cut.rfind("。"), cut.rfind("！"), cut.rfind("？"))
    if last > 80:
        return cut[:last+1]
    return cut + "…"

def make_summary(quote):
    s = quote.replace("\n", " ").strip()
    if len(s) <= 50:
        return s
    head = s[:50]
    last = max(head.rfind("、"), head.rfind("。"))
    if last > 20:
        return head[:last] + "…"
    return head + "…"

def detect_speaker_role(title, text_head):
    h = title + " " + text_head[:400]
    if "理事長" in h:
        return "chairperson"
    if "学園長" in h:
        return "school_director"
    return "principal"

def role_attribute(role, title):
    if role == "chairperson":
        return "理事長"
    if role == "school_director":
        return "学園長"
    if "学校長" in title:
        return "学校長"
    return "校長"

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    url_map, url_fallback = get_url_map()
    existing_hashes, existing_heads = load_existing_quote_hashes()
    existing_count = load_existing_principal_count_per_school()
    print(f"[Team C-1 LLM] existing testimonials hashes: {len(existing_hashes)}")
    print(f"[Team C-1 LLM] schools with existing principal: {len(existing_count)}")
    school_dirs = sorted([d for d in CACHE.iterdir() if d.is_dir() and d.name.startswith("jpms_s_")])
    print(f"[Team C-1 LLM] cached schools: {len(school_dirs)}")
    items = []
    completed = 0
    schools_zero_existing = 0
    schools_low_existing = 0
    for sd in school_dirs:
        sid = sd.name
        existing_n = existing_count.get(sid, 0)
        if existing_n >= 5:
            completed += 1
            continue
        max_per_school = 5 - existing_n
        candidates = []
        for pp in PAGE_PRIORITY:
            f = sd / f"{pp}.html"
            if f.exists():
                candidates.append((pp, f))
        per_school = []
        seen_quotes = set()
        for page_name, fpath in candidates:
            if len(per_school) >= max_per_school:
                break
            try:
                html = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            title, text, struct_paragraphs = extract_text_and_paragraphs(html)
            if any(ind in title for ind in NON_SCHOOL_INDICATORS):
                continue
            if any(ind in text[:1000] for ind in NON_SCHOOL_INDICATORS):
                continue
            page_is_principal = looks_like_principal_page(title, text)
            if page_name in ("principal", "philosophy", "mission"):
                page_is_principal = True
            if not page_is_principal and page_name in ("root","voice","schoollife","curriculum","parent","about","events","progress","admission"):
                hits = sum(1 for k in PRINCIPAL_STRONG if k in text[:6000])
                if hits < 1 and len(text) < 1500:
                    continue
            paragraphs = list(dict.fromkeys(struct_paragraphs + split_paragraphs(text)))
            scored = []
            for p in paragraphs:
                p = clean_paragraph(p)
                if not is_quotable(p):
                    continue
                s = score_paragraph_3axis(p, page_is_principal)
                if s >= 5:
                    scored.append((s, p))
            if not scored:
                continue
            scored.sort(key=lambda x: -x[0])
            role = detect_speaker_role(title, text)
            attr = role_attribute(role, title)
            page_url = url_map.get((sid, page_name), "")
            if not page_url:
                page_url = url_fallback.get(sid, "")
            context_label = {
                "principal": "校長メッセージページ",
                "philosophy": "教育理念ページ",
                "mission": "ミッション/教育方針ページ",
                "about": "学校紹介ページ（校長挨拶）",
                "voice": "メッセージページ",
                "root": "トップページ（校長挨拶）",
                "schoollife": "学校生活ページ",
                "curriculum": "カリキュラムページ",
                "parent": "保護者向けページ",
                "admission": "入試案内ページ",
                "events": "行事ページ",
                "progress": "進学ページ",
            }.get(page_name, "校長メッセージページ")
            for sc, para in scored:
                if len(per_school) >= max_per_school:
                    break
                quote = trim_quote(para)
                if len(quote) >= 400:
                    quote = trim_quote(para, max_len=395)
                if len(quote) < 60:
                    continue
                if quote in seen_quotes:
                    continue
                if any(quote[:80] in q or q[:80] in quote for q in seen_quotes):
                    continue
                h = make_hash(sid, quote)
                if h in existing_hashes:
                    continue
                # Also check substring overlap with existing heads
                head60 = quote[:60]
                if any(head60 in h0 or h0[:60] in quote for h0 in existing_heads.get(sid, [])):
                    continue
                seen_quotes.add(quote)
                rec = {
                    "school_id": sid,
                    "speaker_role": role,
                    "speaker_attribute": attr,
                    "quote_text": quote,
                    "quote_summary": make_summary(quote),
                    "context": context_label,
                    "source_type": "school_website",
                    "source_url": page_url,
                    "rights_level": "quoted_with_attribution",
                    "retrieval_notes": "team_c_llm_principal: 3-axis(philosophy x personal-tone x length)",
                    "extraction_score": sc,
                }
                per_school.append(rec)
        if per_school:
            if existing_n == 0:
                schools_zero_existing += 1
            elif existing_n < 3:
                schools_low_existing += 1
            items.extend(per_school)
        completed += 1
    dedup = {}
    for r in items:
        key = (r["school_id"], r["quote_text"][:80])
        if key not in dedup:
            dedup[key] = r
    final_items = list(dedup.values())
    with open(OUT, "w", encoding="utf-8") as f:
        for r in final_items:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    schools_covered = len(set(r["school_id"] for r in final_items))
    progress = {
        "task_id": "team_c_llm_principal",
        "completed_schools": completed,
        "schools_covered_new": schools_covered,
        "schools_zero_existing_now_covered": schools_zero_existing,
        "schools_low_existing_now_augmented": schools_low_existing,
        "total_new_quotes": len(final_items),
        "ts": datetime.now().isoformat() + "Z",
        "method": "3-axis context scoring (philosophy x personal-tone x length)",
        "thresholds": {"min_score": 5, "min_len": 60, "max_len": 700, "quote_max": 395},
    }
    with open(PROGRESS, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    print(f"[Team C-1 LLM] processed schools: {completed}")
    print(f"[Team C-1 LLM] new schools covered: {schools_covered}")
    print(f"[Team C-1 LLM] zero->covered: {schools_zero_existing}")
    print(f"[Team C-1 LLM] augmented(<3): {schools_low_existing}")
    print(f"[Team C-1 LLM] total new quotes: {len(final_items)}")
    print(f"[Team C-1 LLM] output: {OUT}")
    print(f"[Team C-1 LLM] progress: {PROGRESS}")

if __name__ == "__main__":
    main()
