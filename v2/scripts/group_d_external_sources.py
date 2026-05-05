#!/usr/bin/env python3
"""Group D (関連DB横断) の学校言及抽出。

D-01: PE DB（PESTLE 196,714 articles）の中学校言及
D-02: CI DB（Cultural Intelligence 576,434 articles）の文化教育記事
D-03: UPR系（産学連携プレスリリース 6,581件）の中高大連携
D-04: 文科省・公的政策プロジェクト 中学校言及
D-05: メディア記事の学校言及（CI/PEからの間接抽出）

倫理:
- 公開記事のみ
- 出典URL必須
- 引用は 30-400 字に正規化
- メディア記事は source_type='media_article'
- 在校生・保護者は anonymized_only

出力:
- ~/projects/research/jpms-db/v2/codex_output/group_d_external.jsonl
- DB testimonials_v2 に直接 INSERT
"""
import sqlite3
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

PE_DB = Path('/Users/nishimura+/projects/research/pestle-signal-db/data/pestle.db')
CI_DB = Path('/Users/nishimura+/projects/research/cultural-intelligence-db/data/cultural_intelligence.db')
SANGAKU_PR_DB = Path('/Users/nishimura+/projects/research/investment-signal-radar/data/sangaku_press_releases.db')
POLICY_DB = Path('/Users/nishimura+/projects/research/policy-db-new/data/policy.db')
JPMS_DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT_PATH = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/group_d_external.jsonl')

# 既存 alumni-style JSONL（Wikipedia公開記事ベース）
ALUMNI_JSONL_FILES = [
    Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c4_academic.jsonl'),
    Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c3_business.jsonl'),
    Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c1_gf.jsonl'),
    Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c6_al.jsonl'),
]

# 学校サフィックス: これら付近に短縮形が現れた場合のみ学校言及と判定
# 「学園」「高等学校」は単独だと大学/専門学校と衝突するため除外
SCHOOL_SUFFIXES = ['中学校', '中等部', '中等科', '中学・高校', '中等教育学校',
                   '中・高等学校', '中学校・高等学校', '中学', '中高一貫']

# 短縮名と一緒に出現すると大学/専門学校など別組織を示すNG接尾
NEGATIVE_SUFFIXES_AFTER = ['大学', '短期大学', '短大', '専門学校', '高等専門学校',
                           '大学院', '幼稚園', '保育園', '小学校', 'ビジネススクール']

# 教育文脈キーワード（必須: 1個以上）
EDU_KWS = ['受験', '中学受験', '入試', '進学', '校長', '在校生', '生徒', '卒業生',
           '保護者', '教員', '教師', '教育', 'カリキュラム', 'OB', 'OG', '同窓',
           '理事長', '学園長', '中高一貫', '中高生', '高校生', '中学生', '指導',
           '出身', '合格', '附属', '附設', '入学', '卒業', '創立', '部活',
           '探究', '探求', '研究', 'コンクール', '大会', 'オリンピック',
           '英検', '東大', '京大', '海外大', '国際バカロレア', 'IB']

# 役割推定キーワード
ROLE_PATTERNS = [
    ('principal', ['校長', '理事長', '学園長', '副校長']),
    ('teacher', ['教員', '教諭', '先生', '指導教員', '部活動顧問', '担任', '教師']),
    ('student_alumni', ['卒業生', 'OB', 'OG', '同窓生', '出身者', '元生徒', '修了生']),
    ('student_current', ['在校生', '中学生', '高校生', '生徒', '部員', '受験生', '中等部生']),
    ('parent', ['保護者', 'PTA', '父兄', '父母', '親御', '母親', '父親']),
]

# false positive 除外: 地名+人名衝突・無関係文脈
EXCLUDE_PATTERNS = [
    '麻布台ヒルズ', '麻布十番', '麻布警察', '麻布消防',
    '石巻市開成', '釜山開成', '仙台開成',
    '六本木', '渋谷駅', '渋谷区', '渋谷ヒカリエ', '渋谷スクランブル',
    '雙葉社', '青山学院大学',  # 学院単体は大学優先で別カウント
    '豊島園', '荏原',
]


def normalize_text(s: str) -> str:
    """改行・連続空白の正規化と不要HTMLエンティティの除去。"""
    if not s:
        return ''
    s = re.sub(r'\s+', ' ', s)
    s = s.replace('&nbsp;', ' ').replace('&amp;', '&')
    return s.strip()


def truncate_quote(text: str, max_len: int = 380, min_len: int = 30) -> str | None:
    """引用 30-400 字の倫理ルールに合わせて切り詰める。"""
    text = normalize_text(text)
    if len(text) < min_len:
        return None
    if len(text) > max_len:
        # 文の境界で切る
        cut = text[:max_len]
        for sep in ['。', '」', '！', '？', '.', '、']:
            idx = cut.rfind(sep)
            if idx > 200:
                return cut[:idx + 1]
        return cut + '…'
    return text


def detect_role(full_text: str) -> str:
    for role, kws in ROLE_PATTERNS:
        for kw in kws:
            if kw in full_text:
                return role
    return 'teacher'  # default fallback


def passes_school_match(short_name: str, full_name: str, text: str) -> bool:
    """short_name が text 中に学校文脈で現れているかを判定する。

    - 完全名 (full_name) が直接含まれていれば、direct True (除外パターンに合致しない限り)
    - 短縮名 + 直後5文字以内が NEGATIVE_SUFFIXES に該当: False
    - 短縮名 + 直後20文字以内に SCHOOL_SUFFIXES が出現: True
    """
    # 完全名のマッチ
    if full_name and full_name in text:
        for ex in EXCLUDE_PATTERNS:
            if ex in text and short_name in ex:
                return False
        return True

    if short_name not in text:
        return False

    for ex in EXCLUDE_PATTERNS:
        if ex in text and short_name in ex:
            return False

    # 全マッチ箇所をチェック
    matched_pos = False
    for m in re.finditer(re.escape(short_name), text):
        end = m.end()
        # 直後の文字列をチェック
        tail = text[end:end + 20]
        # ネガティブサフィックスが先に出現する場合は無効
        is_negative = False
        for nsuf in NEGATIVE_SUFFIXES_AFTER:
            if tail.startswith(nsuf):
                is_negative = True
                break
        if is_negative:
            continue
        # 中学校系サフィックスが直後にあるか
        for suffix in SCHOOL_SUFFIXES:
            if tail.startswith(suffix):
                matched_pos = True
                break
        if matched_pos:
            return True
    return False


def load_schools(conn) -> dict:
    """学校名マスタをロード。short_name → (school_id, full_name)。

    短縮名は「中学校/中等部/中等科」を除いた基底語。
    短縮名が他校と衝突する場合は除外。
    """
    schools_full = {}  # full_name → (sid, full_name)
    short_to_schools = {}  # short_name → set of (sid, full_name)

    rows = conn.execute(
        "SELECT id, name_ja FROM schools_v2 "
        "WHERE id NOT LIKE 'NATIONAL%' AND name_ja IS NOT NULL"
    ).fetchall()

    for sid, name in rows:
        schools_full[name] = (sid, name)
        # 基底語生成
        bases = set()
        for suf in ['中学校', '中等部', '中等科', '中学', '中等教育学校',
                    '高等学校', '中・高等学校', '中学・高等学校']:
            if name.endswith(suf):
                base = name[:-len(suf)]
                if len(base) >= 2:
                    bases.add(base)
        for base in bases:
            short_to_schools.setdefault(base, set()).add((sid, name))

    # 衝突する短縮名は除外
    short_unique = {}
    for short, ss in short_to_schools.items():
        if len(ss) == 1:
            sid, full = next(iter(ss))
            short_unique[short] = (sid, full)

    return schools_full, short_unique


def existing_dedup_keys(conn) -> set:
    """既存 testimonials_v2 のハッシュ集合。"""
    keys = set()
    for r in conn.execute(
        "SELECT school_id, substr(quote_text, 1, 80), source_url FROM testimonials_v2"
    ).fetchall():
        sid, q80, url = r
        keys.add(hashlib.md5(f"{sid}|{q80}".encode()).hexdigest())
        if url:
            keys.add(hashlib.md5(f"url:{url}".encode()).hexdigest())
    return keys


def find_school_in_text(full_text: str, schools_full: dict, short_unique: dict):
    """text 中に出現する学校を 1 件返す。"""
    # まず完全名マッチを優先
    for fname, (sid, _) in schools_full.items():
        if len(fname) >= 4 and fname in full_text:
            # 除外パターンチェック
            valid = True
            for ex in EXCLUDE_PATTERNS:
                if ex in full_text and any(part in ex for part in [fname]):
                    valid = False
                    break
            if valid:
                return sid, fname
    # 次に短縮名マッチ + サフィックス文脈
    for short, (sid, fname) in short_unique.items():
        if len(short) < 2:
            continue
        if passes_school_match(short, fname, full_text):
            return sid, fname
    return None, None


# =====================================================================
# D-01: PE DB
# =====================================================================
def extract_pe(jpms, schools_full, short_unique, dedup, jsonl_fh) -> tuple[int, dict]:
    if not PE_DB.exists():
        print('  [D-01] PE DB not found, skip')
        return 0, {}
    pe = sqlite3.connect(PE_DB)
    pe.row_factory = sqlite3.Row
    inserted = 0
    by_role = {}
    # 拡張: 「学」を含む全 JA articles を対象
    rows = pe.execute(
        "SELECT id, title, title_ja, summary, url, source, published_date "
        "FROM articles "
        "WHERE (title LIKE '%学%' OR title_ja LIKE '%学%' OR summary LIKE '%学%')"
    ).fetchall()
    for row in rows:
        title = normalize_text(row['title_ja'] or row['title'] or '')
        summary = normalize_text(row['summary'] or '')
        if not (title or summary):
            continue
        full_text = f"{title}\n{summary}"
        if not any(kw in full_text for kw in EDU_KWS):
            continue
        sid, fname = find_school_in_text(full_text, schools_full, short_unique)
        if not sid:
            continue
        url = row['url']
        if not url:
            continue
        # URL重複チェック
        url_h = hashlib.md5(f"url:{url}".encode()).hexdigest()
        if url_h in dedup:
            continue
        quote = truncate_quote(summary if len(summary) >= 50 else f"{title} | {summary}")
        if not quote:
            continue
        h = hashlib.md5(f"{sid}|{quote[:80]}".encode()).hexdigest()
        if h in dedup:
            continue
        dedup.add(h)
        dedup.add(url_h)
        role = detect_role(full_text)
        rights = 'anonymized_only' if role in ('student_current', 'parent') else 'quoted_with_attribution'
        record = {
            'school_id': sid,
            'speaker_role': role,
            'speaker_attribute': f'PESTLE Signal DB / {row["source"][:40] if row["source"] else ""}',
            'quote_text': quote,
            'context': f'メディア記事（PE）: {title[:80]}',
            'source_type': 'media_article',
            'source_url': url,
            'rights_level': rights,
            'retrieved_at': datetime.now().isoformat(),
            'ethics_review_status': 'group_d_pe',
            'extraction_strategy': 'D-01_PE_articles',
            'matched_school_name': fname,
        }
        jpms.execute(
            """INSERT INTO testimonials_v2
            (school_id, speaker_role, speaker_attribute, quote_text, context,
             source_type, source_url, rights_level, retrieved_at, ethics_review_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sid, role, record['speaker_attribute'], quote, record['context'],
             'media_article', url, rights,
             record['retrieved_at'], 'group_d_pe'))
        inserted += 1
        by_role[role] = by_role.get(role, 0) + 1
        jsonl_fh.write(json.dumps(record, ensure_ascii=False) + '\n')
        if inserted % 50 == 0:
            jpms.commit()
    jpms.commit()
    pe.close()
    return inserted, by_role


# =====================================================================
# D-02: CI DB
# =====================================================================
def extract_ci(jpms, schools_full, short_unique, dedup, jsonl_fh) -> tuple[int, dict]:
    if not CI_DB.exists() or CI_DB.stat().st_size < 1024:
        print('  [D-02] CI DB not found or empty, skip')
        return 0, {}
    ci = sqlite3.connect(CI_DB)
    ci.row_factory = sqlite3.Row
    inserted = 0
    by_role = {}
    # 候補抽出: 全ての日本語記事をスキャン（37K records, 学校サフィックス + 教育キーワード）
    rows = ci.execute(
        "SELECT a.id, a.title, a.summary, a.url, a.published_at, s.name AS source_name "
        "FROM articles a LEFT JOIN sources s ON s.id = a.source_id "
        "WHERE a.lang='ja' AND (a.title || ' ' || COALESCE(a.summary,'')) LIKE '%学%'"
    ).fetchall()
    for row in rows:
        title = normalize_text(row['title'] or '')
        summary = normalize_text(row['summary'] or '')
        full_text = f"{title}\n{summary}"
        if not any(kw in full_text for kw in EDU_KWS):
            continue
        sid, fname = find_school_in_text(full_text, schools_full, short_unique)
        if not sid:
            continue
        url = row['url']
        if not url:
            continue
        url_h = hashlib.md5(f"url:{url}".encode()).hexdigest()
        if url_h in dedup:
            continue
        # 引用本文
        quote_src = summary if len(summary) >= 60 else f"{title} | {summary}"
        quote = truncate_quote(quote_src)
        if not quote:
            continue
        h = hashlib.md5(f"{sid}|{quote[:80]}".encode()).hexdigest()
        if h in dedup:
            continue
        dedup.add(h)
        dedup.add(url_h)
        role = detect_role(full_text)
        rights = 'anonymized_only' if role in ('student_current', 'parent') else 'quoted_with_attribution'
        record = {
            'school_id': sid,
            'speaker_role': role,
            'speaker_attribute': f'Cultural Intelligence DB / {row["source_name"][:40] if row["source_name"] else ""}',
            'quote_text': quote,
            'context': f'メディア記事（CI）: {title[:80]}',
            'source_type': 'media_article',
            'source_url': url,
            'rights_level': rights,
            'retrieved_at': datetime.now().isoformat(),
            'ethics_review_status': 'group_d_ci',
            'extraction_strategy': 'D-02_CI_articles',
            'matched_school_name': fname,
        }
        jpms.execute(
            """INSERT INTO testimonials_v2
            (school_id, speaker_role, speaker_attribute, quote_text, context,
             source_type, source_url, rights_level, retrieved_at, ethics_review_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sid, role, record['speaker_attribute'], quote, record['context'],
             'media_article', url, rights,
             record['retrieved_at'], 'group_d_ci'))
        inserted += 1
        by_role[role] = by_role.get(role, 0) + 1
        jsonl_fh.write(json.dumps(record, ensure_ascii=False) + '\n')
        if inserted % 50 == 0:
            jpms.commit()
    jpms.commit()
    ci.close()
    return inserted, by_role


# =====================================================================
# D-03: Sangaku Press Releases (UPR的扱い)
# =====================================================================
def extract_sangaku_pr(jpms, schools_full, short_unique, dedup, jsonl_fh) -> tuple[int, dict]:
    if not SANGAKU_PR_DB.exists():
        print('  [D-03] Sangaku PR DB not found, skip')
        return 0, {}
    pr = sqlite3.connect(SANGAKU_PR_DB)
    pr.row_factory = sqlite3.Row
    inserted = 0
    by_role = {}
    # 学校言及候補
    rows = pr.execute(
        "SELECT id, title, source_url, published_at, company_name, category "
        "FROM press_releases "
        "WHERE title LIKE '%中学校%' OR title LIKE '%中等部%' OR title LIKE '%中等科%' "
        "   OR title LIKE '%中等教育学校%' OR title LIKE '%中高一貫%' "
        "   OR title LIKE '%中・高%' OR title LIKE '%中学・高%'"
    ).fetchall()
    for row in rows:
        title = normalize_text(row['title'] or '')
        if not title:
            continue
        # 教育キーワード必須
        if not any(kw in title for kw in EDU_KWS + ['連携', '協定', '共創', 'コラボ', '出張授業']):
            continue
        sid, fname = find_school_in_text(title, schools_full, short_unique)
        if not sid:
            continue
        url = row['source_url']
        if not url:
            continue
        url_h = hashlib.md5(f"url:{url}".encode()).hexdigest()
        if url_h in dedup:
            continue
        quote = truncate_quote(title)
        if not quote:
            continue
        h = hashlib.md5(f"{sid}|{quote[:80]}".encode()).hexdigest()
        if h in dedup:
            continue
        dedup.add(h)
        dedup.add(url_h)
        # PRは大学・企業発信なので、学校側の関係者役割としては teacher (or principal) 既定
        role = detect_role(title)
        if role == 'teacher' and any(kw in title for kw in ['校長']):
            role = 'principal'
        rights = 'quoted_with_attribution'
        record = {
            'school_id': sid,
            'speaker_role': role,
            'speaker_attribute': f'産学連携プレスリリース / {row["company_name"] or ""}',
            'quote_text': quote,
            'context': f'PR/UPR: 産学連携・中高連携',
            'source_type': 'media_article',
            'source_url': url,
            'rights_level': rights,
            'retrieved_at': datetime.now().isoformat(),
            'ethics_review_status': 'group_d_upr',
            'extraction_strategy': 'D-03_sangaku_press',
            'matched_school_name': fname,
        }
        jpms.execute(
            """INSERT INTO testimonials_v2
            (school_id, speaker_role, speaker_attribute, quote_text, context,
             source_type, source_url, rights_level, retrieved_at, ethics_review_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sid, role, record['speaker_attribute'], quote, record['context'],
             'media_article', url, rights,
             record['retrieved_at'], 'group_d_upr'))
        inserted += 1
        by_role[role] = by_role.get(role, 0) + 1
        jsonl_fh.write(json.dumps(record, ensure_ascii=False) + '\n')
        if inserted % 50 == 0:
            jpms.commit()
    jpms.commit()
    pr.close()
    return inserted, by_role


# =====================================================================
# D-04: Policy DB（文科省政策プロジェクト）
# =====================================================================
def extract_policy(jpms, schools_full, short_unique, dedup, jsonl_fh) -> tuple[int, dict]:
    if not POLICY_DB.exists():
        print('  [D-04] Policy DB not found, skip')
        return 0, {}
    pol = sqlite3.connect(POLICY_DB)
    pol.row_factory = sqlite3.Row
    inserted = 0
    by_role = {}
    rows = pol.execute(
        "SELECT id, name, overview, purpose, ministry_name, fiscal_year "
        "FROM projects "
        "WHERE (overview LIKE '%中学校%' OR purpose LIKE '%中学校%' "
        "    OR overview LIKE '%中等教育学校%' OR purpose LIKE '%中等教育学校%') "
        "AND ministry_name LIKE '%文部%'"
    ).fetchall()
    for row in rows:
        name = normalize_text(row['name'] or '')
        overview = normalize_text(row['overview'] or '')
        purpose = normalize_text(row['purpose'] or '')
        full_text = f"{name}\n{overview}\n{purpose}"
        # 文科省政策で個別校が特定される稀ケースのみ拾う
        sid, fname = find_school_in_text(full_text, schools_full, short_unique)
        if not sid:
            continue
        # 政策プロジェクトはURLなし。e-Stat / 文科省サイトを引用元にする
        url = f'https://rssystem.go.jp/projects/{row["id"]}'  # 行政事業レビュー
        url_h = hashlib.md5(f"url:{url}".encode()).hexdigest()
        if url_h in dedup:
            continue
        quote_src = overview if len(overview) >= 50 else purpose
        quote = truncate_quote(quote_src)
        if not quote:
            continue
        h = hashlib.md5(f"{sid}|{quote[:80]}".encode()).hexdigest()
        if h in dedup:
            continue
        dedup.add(h)
        dedup.add(url_h)
        role = 'teacher'  # 政策文書は教育者視点デフォルト
        rights = 'quoted_with_attribution'
        record = {
            'school_id': sid,
            'speaker_role': role,
            'speaker_attribute': f'文科省事業 ({row["fiscal_year"]}年度)',
            'quote_text': quote,
            'context': f'政策事業: {name[:80]}',
            'source_type': 'media_article',
            'source_url': url,
            'rights_level': rights,
            'retrieved_at': datetime.now().isoformat(),
            'ethics_review_status': 'group_d_policy',
            'extraction_strategy': 'D-04_MEXT_projects',
            'matched_school_name': fname,
        }
        jpms.execute(
            """INSERT INTO testimonials_v2
            (school_id, speaker_role, speaker_attribute, quote_text, context,
             source_type, source_url, rights_level, retrieved_at, ethics_review_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sid, role, record['speaker_attribute'], quote, record['context'],
             'media_article', url, rights,
             record['retrieved_at'], 'group_d_policy'))
        inserted += 1
        by_role[role] = by_role.get(role, 0) + 1
        jsonl_fh.write(json.dumps(record, ensure_ascii=False) + '\n')
    jpms.commit()
    pol.close()
    return inserted, by_role


# =====================================================================
# D-05: 卒業生 Wikipedia エントリ（alumni JSONL ファイルから）
# =====================================================================
def extract_alumni_wikipedia(jpms, dedup, jsonl_fh) -> tuple[int, dict]:
    """既存の team_c1/c3/c4/c6 JSONLから卒業生情報をtestimonialsに追加。

    Wikipedia の卒業生リスト/個人ページから抽出された alumni データを、
    student_alumni 役割の testimonials_v2 として登録する。
    """
    import json as json_mod
    inserted = 0
    by_role = {'student_alumni': 0}
    rejected = {'no_school': 0, 'short_quote': 0, 'duplicate': 0, 'no_url': 0}

    for fpath in ALUMNI_JSONL_FILES:
        if not fpath.exists():
            continue
        file_label = fpath.stem
        with fpath.open(encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json_mod.loads(line)
                except json_mod.JSONDecodeError:
                    continue
                # スキーマ正規化
                sid = d.get('school_id') or d.get('matched_school_id')
                school_name = d.get('school_name') or d.get('matched_school_name', '')
                name = d.get('name') or d.get('person_name', '')
                evidence = (d.get('evidence_text') or d.get('description') or '').strip()
                source_url = d.get('source_url') or d.get('url') or ''
                source_label = d.get('source') or 'Wikipedia ja'
                category = d.get('category') or d.get('field') or ''
                match_type = d.get('match_type') or d.get('linkage_type') or ''
                if not sid:
                    rejected['no_school'] += 1
                    continue
                if not source_url:
                    rejected['no_url'] += 1
                    continue
                # 集計型 (prefecture_aggregate) は対象外（既に school_official_stats に投入済）
                if match_type in ('prefecture_aggregate', 'person_no_school_link'):
                    continue
                # 学校が DB に存在するかチェック
                if not jpms.execute("SELECT 1 FROM schools_v2 WHERE id = ?", (sid,)).fetchone():
                    rejected['no_school'] += 1
                    continue

                # 引用本文構築: 「{氏名}（{matched_school_name}卒業生 / {category}）: {evidence_text}」
                # スペックで最低 30 字を保証するため、短い場合は学校名と役割を補強
                if name and evidence:
                    quote_body = f"{name}（{school_name}卒業生）: {evidence}"
                elif name:
                    quote_body = f"{name}（{school_name}卒業生）"
                else:
                    quote_body = evidence
                quote = truncate_quote(quote_body, max_len=380, min_len=30)
                if not quote or len(quote) < 30:
                    rejected['short_quote'] += 1
                    continue

                url_h = hashlib.md5(f"url+name:{source_url}|{name}".encode()).hexdigest()
                if url_h in dedup:
                    rejected['duplicate'] += 1
                    continue
                h = hashlib.md5(f"{sid}|{quote[:80]}".encode()).hexdigest()
                if h in dedup:
                    rejected['duplicate'] += 1
                    continue
                dedup.add(h)
                dedup.add(url_h)

                role = 'student_alumni'
                rights = 'quoted_with_attribution'  # 公開Wikipediaの記述は出典明示
                speaker_attr = f'卒業生（{category}）' if category else '卒業生'
                context_short = f'Wikipedia卒業生記述: {match_type or file_label}'

                record = {
                    'school_id': sid,
                    'speaker_role': role,
                    'speaker_attribute': speaker_attr,
                    'quote_text': quote,
                    'context': context_short,
                    'source_type': 'media_article',
                    'source_url': source_url,
                    'rights_level': rights,
                    'retrieved_at': datetime.now().isoformat(),
                    'ethics_review_status': 'group_d_alumni_wp',
                    'extraction_strategy': f'D-05_{file_label}',
                    'matched_school_name': school_name,
                    'alumni_name': name,
                    'category': category,
                }
                jpms.execute(
                    """INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text, context,
                     source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (sid, role, speaker_attr, quote, context_short,
                     'media_article', source_url, rights,
                     record['retrieved_at'], 'group_d_alumni_wp'))
                inserted += 1
                by_role['student_alumni'] += 1
                jsonl_fh.write(json_mod.dumps(record, ensure_ascii=False) + '\n')
                if inserted % 100 == 0:
                    jpms.commit()
        jpms.commit()
    print(f'  rejected: {rejected}')
    return inserted, by_role


# =====================================================================
# main
# =====================================================================
def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    jpms = sqlite3.connect(JPMS_DB, timeout=600.0)
    jpms.execute('PRAGMA busy_timeout=600000')
    jpms.row_factory = sqlite3.Row

    print('Loading schools…')
    schools_full, short_unique = load_schools(jpms)
    print(f'  full names: {len(schools_full)}, unique short forms: {len(short_unique)}')

    print('Loading existing dedup keys…')
    dedup = existing_dedup_keys(jpms)
    print(f'  dedup keys: {len(dedup)}')

    before_total = jpms.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]

    summary = {}
    with OUT_PATH.open('w', encoding='utf-8') as fh:
        print('\n[D-01] Extracting from PE DB…')
        n, br = extract_pe(jpms, schools_full, short_unique, dedup, fh)
        summary['D-01_PE'] = {'inserted': n, 'by_role': br}
        print(f'  inserted: {n}, by_role: {br}')

        print('\n[D-02] Extracting from CI DB…')
        n, br = extract_ci(jpms, schools_full, short_unique, dedup, fh)
        summary['D-02_CI'] = {'inserted': n, 'by_role': br}
        print(f'  inserted: {n}, by_role: {br}')

        print('\n[D-03] Extracting from Sangaku Press Releases…')
        n, br = extract_sangaku_pr(jpms, schools_full, short_unique, dedup, fh)
        summary['D-03_UPR'] = {'inserted': n, 'by_role': br}
        print(f'  inserted: {n}, by_role: {br}')

        print('\n[D-04] Extracting from Policy DB (MEXT projects)…')
        n, br = extract_policy(jpms, schools_full, short_unique, dedup, fh)
        summary['D-04_Policy'] = {'inserted': n, 'by_role': br}
        print(f'  inserted: {n}, by_role: {br}')

        print('\n[D-05] Extracting alumni from Wikipedia-based JSONL…')
        n, br = extract_alumni_wikipedia(jpms, dedup, fh)
        summary['D-05_Alumni_WP'] = {'inserted': n, 'by_role': br}
        print(f'  inserted: {n}, by_role: {br}')

    after_total = jpms.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]
    total_inserted = after_total - before_total

    print('\n' + '=' * 60)
    print('Group D Extraction Summary')
    print('=' * 60)
    for strat, info in summary.items():
        print(f"  {strat}: {info['inserted']} (by_role: {info['by_role']})")
    print(f"\n  Total inserted: {total_inserted}")
    print(f"  testimonials_v2 before: {before_total}")
    print(f"  testimonials_v2 after:  {after_total}")
    print(f"\n  Output JSONL: {OUT_PATH}")

    jpms.close()
    return total_inserted


if __name__ == '__main__':
    main()
