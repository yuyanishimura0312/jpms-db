import sqlite3, re, hashlib
from pathlib import Path
from datetime import datetime

DB = '/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db'
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')
PER_SCHOOL_CAP = 150  # 80 -> 150

ALL_TAGS_RE = re.compile(r'<(p|li|dd|dt|td|th|blockquote|aside|figcaption|h[1-6]|div)[^>]*>(.*?)</\1>', re.DOTALL|re.IGNORECASE)

def normalize(t):
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.DOTALL|re.IGNORECASE)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.DOTALL|re.IGNORECASE)
    t = re.sub(r'<!--.*?-->', ' ', t, flags=re.DOTALL)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'&nbsp;|&[a-zA-Z]+;|&#\d+;', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

BOILER = re.compile(r'Copyright|©|All Rights|プライバシー|サイトマップ|Cookie|JavaScript|読み込み中|PAGE TOP|^MENU$|メニューを|^TOP$|資料請求|オープンスクール|アクセス|^詳細を見る$|^詳しく見る$|^続きを読む$', re.IGNORECASE)

def split_sentences(text):
    """30-400 char sentence/paragraph segmentation"""
    if 30 <= len(text) <= 400:
        yield text
    sents = re.split(r'(?<=[。！？])\s*', text)
    cur = ''
    for s in sents:
        if not s.strip():
            continue
        if len(cur) + len(s) <= 350:
            cur += s
        else:
            if 30 <= len(cur) <= 400:
                yield cur.strip()
            cur = s
    if 30 <= len(cur) <= 400:
        yield cur.strip()

def detect_role(text, slug, source_url):
    if any(k in text for k in ['卒業生','OB','OG','同窓','期生','年卒','出身','卒業して','卒業後']):
        return 'student_alumni'
    if any(k in text for k in ['校長','理事長','学園長','副校長','教頭']):
        return 'principal'
    if any(k in text for k in ['在校生','生徒','中1','中2','中3','中学生','高校生','入学して','本校で','部活動']):
        return 'student_current'
    if any(k in text for k in ['保護者','PTA','父母','後援会','保護者会','我が子','娘','息子']):
        return 'parent'
    if any(k in text for k in ['教諭','教員','担任','主任','生徒たちが','指導','授業を']):
        return 'teacher'
    sl = (slug + ' ' + (source_url or '')).lower()
    if any(k in sl for k in ['principal','kocho','message','aisatsu','rinen','philosophy','mission']):
        return 'principal'
    if any(k in sl for k in ['voice','student','seito','schoollife','koe']):
        return 'student_current'
    if any(k in sl for k in ['alumni','sotsugyo','graduate','ob_og']):
        return 'student_alumni'
    if any(k in sl for k in ['parent','pta','hogo','family']):
        return 'parent'
    if any(k in sl for k in ['curriculum','teacher','kyoin','education','syllabus']):
        return 'teacher'
    return None

db = sqlite3.connect(DB, timeout=600.0)
db.execute('PRAGMA busy_timeout=600000')

# Existing hashes (for global dedup)
existing = set()
for r in db.execute("SELECT school_id, substr(quote_text,1,80) FROM testimonials_v2"):
    existing.add(hashlib.md5(f"{r[0]}|{r[1]}".encode()).hexdigest())

# Per-school current counts
school_count = {}
for r in db.execute("SELECT school_id, COUNT(*) FROM testimonials_v2 WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue','qm1_passed_v7') GROUP BY school_id"):
    school_count[r[0]] = r[1]

schools = {r[0]: r[1] for r in db.execute("SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL AND homepage_url!=''")}

inserted = 0
batch = 0
for sid_dir in sorted(CACHE.iterdir()):
    if not sid_dir.is_dir() or not sid_dir.name.startswith('jpms_s_'):
        continue
    sid = sid_dir.name
    if sid not in schools:
        continue
    cur = school_count.get(sid, 0)
    if cur >= PER_SCHOOL_CAP:
        continue
    room = PER_SCHOOL_CAP - cur
    sch_url = schools[sid]
    added = 0
    candidates = []
    for f in sid_dir.glob('*.html'):
        try:
            html = f.read_text(errors='ignore')
        except Exception:
            continue
        slug = f.stem
        for tag_m in ALL_TAGS_RE.finditer(html):
            text = normalize(tag_m.group(2))
            if not text or BOILER.search(text):
                continue
            for sent in split_sentences(text):
                if BOILER.search(sent):
                    continue
                role = detect_role(sent, slug, sch_url)
                if role:
                    candidates.append({'text': sent, 'role': role, 'slug': slug, 'context': f'v7-{tag_m.group(1)}'})

    seen_local = set()
    for c in candidates:
        if added >= room:
            break
        h = hashlib.md5(f"{sid}|{c['text'][:80]}".encode()).hexdigest()
        if h in existing or h in seen_local:
            continue
        existing.add(h)
        seen_local.add(h)
        rights = 'anonymized_only' if c['role'] in ('student_current','student_alumni','parent') else 'quoted_with_attribution'
        attr = {'principal':'校長または理事長','teacher':'教員','student_current':'中学生','student_alumni':'卒業生','parent':'保護者'}.get(c['role'], '')
        try:
            db.execute("""INSERT INTO testimonials_v2
                (school_id, speaker_role, speaker_attribute, quote_text, context, source_type, source_url, rights_level, retrieved_at, ethics_review_status)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (sid, c['role'], attr, c['text'], c['context'], 'school_website', sch_url, rights, datetime.now().isoformat(), 'qm1_passed_v7'))
            inserted += 1
            added += 1
            batch += 1
            if batch >= 500:
                db.commit()
                batch = 0
        except sqlite3.OperationalError:
            pass

db.commit()
print(f"V7 inserted: {inserted}")

total = db.execute("SELECT COUNT(*) FROM testimonials_v2 WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue','qm1_passed_v7')").fetchone()[0]
print(f"利用可能合計: {total}")

counts = db.execute("SELECT school_id, COUNT(*) FROM testimonials_v2 WHERE ethics_review_status IN ('approved','qm1_passed_v6','qm1_passed_v6_rescue','qm1_passed_v7') GROUP BY school_id").fetchall()
import statistics
ns = [c[1] for c in counts]
print(f"カバー: {len(ns)}/551")
if ns:
    print(f"平均: {statistics.mean(ns):.1f}, 中央値: {statistics.median(ns)}, 最大: {max(ns)}")
db.close()
