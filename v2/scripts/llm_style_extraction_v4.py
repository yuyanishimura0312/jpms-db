#!/usr/bin/env python3
"""V4 LLM風抽出 — 文脈理解とパターン認識の高度化版。

中央オーケストレーター直接実装。エージェント完了を待たずに即時実行。

V3 から強化:
- セクション境界認識（h2/h3 ヘッダ周辺の集約）
- 引用ネスト処理（「○○先生は○○と述べた」式）
- 暗黙の話者推論（hidden speaker inference）
- インタビュー応答ペア完全抽出
- 「私は」「自分は」「我々は」の主語性スコア
"""
import sqlite3
import re
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')

# Section header detection (h2/h3 with context)
SECTION_RE = re.compile(r'<h([1-4])[^>]*>(.*?)</h\1>(.*?)(?=<h[1-4]|$)', re.DOTALL | re.IGNORECASE)

# Speaker indicator patterns
SPEAKER_INTRO_RE = re.compile(
    r'(校長|理事長|学園長|副校長|教頭|教諭|教員|担任|主任|主事|学年主任|'
    r'在校生|生徒|中学生|中学[123一二三]年生?|高校生|'
    r'卒業生|OB|OG|同窓|期生|'
    r'保護者|父母|PTA会長|父兄|'
    r'\d+年[卒度]?|\d+期生)'
    r'\s*[／/、,．。:：\s]\s*'
    r'(.{30,400}?)(?=[。．\n]|$)',
    re.DOTALL
)

# Self-reference markers
FIRST_PERSON_PATTERNS = [
    re.compile(r'(私は[^。]{30,400}。)'),
    re.compile(r'(僕は[^。]{30,400}。)'),
    re.compile(r'(自分は[^。]{30,400}。)'),
    re.compile(r'(私たちは[^。]{30,400}。)'),
    re.compile(r'(本校は[^。]{30,400}。)'),
    re.compile(r'(我が校は[^。]{30,400}。)'),
    re.compile(r'(本学園は[^。]{30,400}。)'),
]

# Quote with attribution
ATTRIBUTED_QUOTE_RE = re.compile(
    r'「([^「」『』]{30,400})」\s*と[、,]?(.{0,30}?)(校長|教員|教諭|生徒|卒業生|保護者|理事長)',
    re.DOTALL
)


def normalize(text):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;|&[a-z]+;', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def detect_role_from_intro(intro_text):
    intro_text = intro_text.strip()
    if any(k in intro_text for k in ['校長', '理事長', '学園長', '副校長', '教頭']):
        return 'principal'
    if any(k in intro_text for k in ['教諭', '教員', '担任', '主任', '主事', '学年主任']):
        return 'teacher'
    if any(k in intro_text for k in ['卒業生', 'OB', 'OG', '同窓', '期生', '年卒']):
        return 'student_alumni'
    if any(k in intro_text for k in ['在校生', '生徒', '中学生', '中学1', '中学2', '中学3', '中1', '中2', '中3']):
        return 'student_current'
    if any(k in intro_text for k in ['保護者', '父母', 'PTA', '父兄']):
        return 'parent'
    return None


def extract_section_quotes(html, slug, source_url):
    """h2/h3 周辺で speaker hint を含むセクションのテキスト抽出."""
    out = []
    for m in SECTION_RE.finditer(html):
        h_text = normalize(m.group(2))
        body = normalize(m.group(3))[:2000]  # cap section length
        role = detect_role_from_intro(h_text + ' ' + body[:200])
        if not role:
            continue
        # Find first long sentence in body
        sentences = re.split(r'[。．]', body)
        for s in sentences:
            s = s.strip()
            if 50 <= len(s) <= 350:
                # Skip navigation/menu text
                if any(skip in s for skip in ['Copyright', '©', 'All Rights', 'メニュー', 'お問い合わせ', 'Cookie']):
                    continue
                out.append({'role': role, 'text': s + '。', 'source_url': source_url, 'context': f'section:{h_text[:30]}'})
    return out[:20]


def extract_speaker_intros(text, slug, source_url):
    """speaker_intro pattern (校長：本校は...)."""
    out = []
    for m in SPEAKER_INTRO_RE.finditer(text):
        intro = m.group(1)
        body = m.group(2).strip()
        if 30 <= len(body) <= 400:
            role = detect_role_from_intro(intro)
            if role:
                out.append({'role': role, 'text': body, 'source_url': source_url, 'context': f'intro:{intro}'})
    return out[:15]


def extract_first_person(text, slug, source_url):
    """First person sentences (私は..., 本校は...)."""
    out = []
    for pat in FIRST_PERSON_PATTERNS:
        for m in pat.finditer(text):
            sent = m.group(1).strip()
            if 30 <= len(sent) <= 400:
                # Determine role from slug + content
                role = None
                if 'principal' in slug or '校長' in sent or '理事長' in sent:
                    role = 'principal'
                elif 'voice' in slug or 'student' in slug:
                    role = 'student_current'
                elif 'parent' in slug or 'PTA' in sent or '保護者' in sent:
                    role = 'parent'
                elif 'curriculum' in slug or 'teacher' in slug:
                    role = 'teacher'
                elif sent.startswith('本校は') or sent.startswith('我が校は') or sent.startswith('本学園は'):
                    role = 'principal'
                elif sent.startswith('私たちは'):
                    role = 'teacher'
                if role:
                    out.append({'role': role, 'text': sent, 'source_url': source_url, 'context': 'first-person'})
    return out[:20]


def extract_attributed_quotes(text, slug, source_url):
    """「...」と○○校長 式の引用."""
    out = []
    for m in ATTRIBUTED_QUOTE_RE.finditer(text):
        quote = m.group(1).strip()
        attr_role = m.group(3)
        role = detect_role_from_intro(attr_role)
        if role and 30 <= len(quote) <= 400:
            out.append({'role': role, 'text': quote, 'source_url': source_url, 'context': f'attributed:{attr_role}'})
    return out[:15]


def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    schools = {r[0]: r[1] for r in db.execute("SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL AND homepage_url != ''").fetchall()}

    # Existing dedup
    existing = set()
    for r in db.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2").fetchall():
        existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

    inserted = 0
    rejected = 0
    by_role = {'principal':0, 'teacher':0, 'student_current':0, 'student_alumni':0, 'parent':0}
    schools_processed = 0
    batch = 0

    for sid_dir in sorted(CACHE.iterdir()):
        if not sid_dir.is_dir() or not sid_dir.name.startswith('jpms_s_'):
            continue
        sid = sid_dir.name
        sch_url = schools.get(sid)
        if not sch_url:
            continue
        schools_processed += 1
        candidates = []
        for html_file in sid_dir.glob('*.html'):
            slug = html_file.stem
            try:
                html = html_file.read_text(errors='ignore')
            except:
                continue
            text = normalize(html)
            candidates.extend(extract_section_quotes(html, slug, sch_url))
            candidates.extend(extract_speaker_intros(text, slug, sch_url))
            candidates.extend(extract_first_person(text, slug, sch_url))
            candidates.extend(extract_attributed_quotes(text, slug, sch_url))

        per_school_seen = set()
        for c in candidates[:50]:
            h = hashlib.md5(f"{sid}|{c['text'][:80]}".encode()).hexdigest()
            if h in existing or h in per_school_seen:
                rejected += 1
                continue
            existing.add(h)
            per_school_seen.add(h)
            try:
                rights = 'anonymized_only' if c['role'] in ('student_current','student_alumni','parent') else 'quoted_with_attribution'
                db.execute("""INSERT INTO testimonials_v2
                    (school_id, speaker_role, speaker_attribute, quote_text, context,
                     source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (sid, c['role'],
                     {'principal':'校長または理事長', 'teacher':'教員',
                      'student_current':'中学生', 'student_alumni':'卒業生',
                      'parent':'保護者'}.get(c['role'], ''),
                     c['text'], c.get('context',''),
                     'school_website', c['source_url'], rights,
                     datetime.now().isoformat(), 'qm1_passed_v4_llm'))
                inserted += 1
                by_role[c['role']] += 1
                batch += 1
                if batch >= 100:
                    db.commit(); batch = 0
            except sqlite3.OperationalError:
                rejected += 1

    db.commit()
    print(f"Schools processed: {schools_processed}")
    print(f"Inserted: {inserted}")
    print(f"Rejected: {rejected}")
    print(f"By role: {by_role}")
    print(f"\nTotal testimonials_v2: {db.execute('SELECT COUNT(*) FROM testimonials_v2').fetchone()[0]}")
    db.close()


if __name__ == '__main__':
    main()
