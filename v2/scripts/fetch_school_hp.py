#!/usr/bin/env python3
"""School HP one-shot fetcher with strict ethics compliance.

倫理規律:
- robots.txt 厳守
- 同一ドメインへ最低5秒/req
- User-Agent 明示
- 主要10ページまで/校
- 取得失敗はログに記録、再試行は1回のみ

Usage:
  python3 fetch_school_hp.py --school-id <id> [--max <N>]
  python3 fetch_school_hp.py --batch <csv> [--workers 1]
  python3 fetch_school_hp.py --top12  # 12 sample schools
"""
import argparse
import sqlite3
import urllib.request
import urllib.parse
import urllib.robotparser
import time
import re
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')
LOG_FILE = Path('/Users/nishimura+/projects/research/jpms-db/v2/fetch_log.jsonl')

USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org; https://yuyanishimura0312.github.io/jpms-db/)'
MIN_DELAY = 5.0  # seconds per same domain
TIMEOUT = 20

# Subpage URL patterns to try (relative to root)
PRIORITY_PATHS = [
    ('about', ['/about/', '/about/index.html', '/gakuen/', '/about/principle/']),
    ('philosophy', ['/about/philosophy/', '/philosophy/', '/about/philosophy.html', '/philosophy.html']),
    ('principal', ['/principal/', '/about/principal/', '/about/principal.html', '/message/principal/']),
    ('mission', ['/mission/', '/about/mission/', '/vision/']),
    ('curriculum', ['/curriculum/', '/education/', '/curriculum/index.html']),
    ('schoollife', ['/schoollife/', '/school_life/', '/life/']),
    ('events', ['/events/', '/event/', '/calendar/']),
    ('progress', ['/progress/', '/career/', '/results/']),
    ('voice', ['/voice/', '/message/', '/interview/']),
    ('admission', ['/admission/', '/exam/', '/nyushi/']),
]

def log(event):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a') as f:
        f.write(json.dumps({**event, 'ts': datetime.now().isoformat()}, ensure_ascii=False) + '\n')

def get_domain(url):
    return urllib.parse.urlparse(url).netloc

class DomainRateLimiter:
    """Per-domain rate limit tracker."""
    def __init__(self, min_delay=MIN_DELAY):
        self.last_fetch = {}
        self.min_delay = min_delay
        self.robots_cache = {}

    def can_fetch(self, url):
        domain = get_domain(url)
        if domain not in self.robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{urllib.parse.urlparse(url).scheme}://{domain}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except Exception:
                self.robots_cache[domain] = None  # No robots.txt = OK
        rp = self.robots_cache[domain]
        if rp is None:
            return True
        return rp.can_fetch(USER_AGENT, url)

    def wait_if_needed(self, url):
        domain = get_domain(url)
        last = self.last_fetch.get(domain, 0)
        elapsed = time.time() - last
        if elapsed < self.min_delay:
            sleep_s = self.min_delay - elapsed
            time.sleep(sleep_s)
        self.last_fetch[domain] = time.time()


def fetch_url(url, limiter):
    """Fetch URL with ethics guard. Returns (status, content_bytes, content_type) or (None, None, None)."""
    if not limiter.can_fetch(url):
        log({'event':'robots_blocked', 'url':url})
        return None, None, None
    limiter.wait_if_needed(url)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept-Language':'ja,en;q=0.5'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ct = r.headers.get('Content-Type', '')
            if 'text/html' not in ct.lower():
                log({'event':'non_html', 'url':url, 'content_type':ct})
                return r.status, None, ct
            data = r.read()
            return r.status, data, ct
    except urllib.error.HTTPError as e:
        log({'event':'http_error', 'url':url, 'status':e.code})
        return e.code, None, None
    except Exception as e:
        log({'event':'fetch_error', 'url':url, 'err':str(e)[:200]})
        return None, None, None


def normalize_text(html):
    """Strip tags and condense whitespace."""
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_philosophy(text, school_name):
    """Heuristic extraction of philosophy/principle sentences from page text."""
    keywords = ['建学', '創立', '理念', '精神', '校訓', '使命', 'mission', '目標', '教育方針', '人材育成']
    sentences = re.split(r'[。\n]', text)
    matches = []
    for s in sentences:
        s = s.strip()
        if len(s) < 20 or len(s) > 400:
            continue
        if any(kw in s for kw in keywords):
            matches.append(s + '。')
    return matches[:5]


def extract_testimonials(text):
    """Heuristic extraction of testimonials."""
    keywords_role = {
        'principal': ['校長', '理事長', '学園長'],
        'teacher': ['教諭', '教員', '担任', '教科'],
        'student_current': ['在校生', '中学生', '生徒'],
        'student_alumni': ['卒業生', 'OB', 'OG', '同窓'],
        'parent': ['保護者', '保護者会', 'PTA'],
    }
    sentences = re.split(r'[。\n]', text)
    out = []
    for s in sentences:
        s = s.strip()
        if len(s) < 30 or len(s) > 350:
            continue
        for role, kws in keywords_role.items():
            if any(kw in s for kw in kws):
                out.append({'role':role, 'text':s+'。'})
                break
    return out[:20]


def fetch_school(school_id, db, limiter):
    """Fetch a single school's homepages."""
    s = db.execute("SELECT id, name_ja, homepage_url FROM schools_v2 WHERE id=?", (school_id,)).fetchone()
    if not s:
        return {'school_id':school_id, 'status':'not_found'}
    school_id, name, url = s
    if not url:
        log({'event':'no_url', 'school_id':school_id, 'name':name})
        return {'school_id':school_id, 'name':name, 'status':'no_url'}

    # Normalize URL
    if not url.startswith(('http://','https://')):
        url = 'https://' + url
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    school_dir = CACHE_DIR / school_id
    school_dir.mkdir(parents=True, exist_ok=True)

    pages_fetched = []
    philosophies = []
    testimonials = []

    # Fetch root + each priority path
    pages_to_try = [('root', [url])]
    pages_to_try.extend([(slug, [base + p for p in paths]) for slug, paths in PRIORITY_PATHS])

    for slug, candidate_urls in pages_to_try:
        for cand in candidate_urls[:2]:  # try max 2 paths per slug
            status, content, ct = fetch_url(cand, limiter)
            if content and status == 200:
                # Save raw HTML
                fname = school_dir / f"{slug}.html"
                fname.write_bytes(content)
                # Decode and extract
                try:
                    html = content.decode('utf-8', errors='ignore')
                except:
                    html = content.decode('shift_jis', errors='ignore')
                text = normalize_text(html)
                # Update homepage_assets
                db.execute("""INSERT INTO school_homepage_assets
                    (school_id, page_path, full_url, fetched_at, archive_path, status_code, content_length, rights_level)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (school_id, slug, cand, datetime.now().isoformat(),
                     str(fname.relative_to(Path('/Users/nishimura+/projects/research/jpms-db/v2'))),
                     status, len(content), 'archive_only'))
                pages_fetched.append(slug)
                # Extract philosophy
                p = extract_philosophy(text, name)
                if p:
                    for ptext in p:
                        philosophies.append({'slug':slug, 'text':ptext, 'url':cand})
                # Extract testimonials (only from voice/message/interview pages)
                if slug in ('voice','principal','schoollife'):
                    t = extract_testimonials(text)
                    for tt in t:
                        testimonials.append({**tt, 'slug':slug, 'url':cand})
                break  # success, don't try other candidates for this slug
            elif status == 404:
                continue  # try next candidate

    # Insert philosophies (deduplicated)
    seen_phil = set()
    phil_inserted = 0
    for p in philosophies:
        h = hashlib.md5(p['text'].encode()).hexdigest()[:16]
        if h in seen_phil:
            continue
        seen_phil.add(h)
        # Check if already exists in school_philosophy_v2
        exists = db.execute("SELECT 1 FROM school_philosophy_v2 WHERE school_id=? AND text_full=?",
                            (school_id, p['text'])).fetchone()
        if exists:
            continue
        db.execute("""INSERT INTO school_philosophy_v2
            (school_id, philosophy_type, text_full, word_count, source_url, rights_level, retrieved_at, language)
            VALUES (?,?,?,?,?,?,?,?)""",
            (school_id, 'extracted_'+p['slug'], p['text'], len(p['text']), p['url'],
             'quoted_with_attribution', datetime.now().isoformat(), 'ja'))
        phil_inserted += 1

    # Insert testimonials
    seen_tt = set()
    tt_inserted = 0
    for t in testimonials:
        h = hashlib.md5(t['text'].encode()).hexdigest()[:16]
        if h in seen_tt:
            continue
        seen_tt.add(h)
        db.execute("""INSERT INTO testimonials_v2
            (school_id, speaker_role, quote_text, source_type, source_url, rights_level, retrieved_at, ethics_review_status)
            VALUES (?,?,?,?,?,?,?,?)""",
            (school_id, t['role'], t['text'], 'school_website', t['url'],
             'quoted_with_attribution', datetime.now().isoformat(), 'pending'))
        tt_inserted += 1

    # Update data_completeness
    completeness = min(100, 30 + len(pages_fetched)*7 + phil_inserted*3 + tt_inserted*2)
    db.execute("UPDATE schools_v2 SET data_completeness_v2=?, homepage_archived_at=? WHERE id=?",
               (completeness, datetime.now().isoformat(), school_id))
    db.commit()

    return {
        'school_id': school_id, 'name': name, 'status':'ok',
        'pages_fetched': pages_fetched,
        'philosophies_added': phil_inserted,
        'testimonials_added': tt_inserted,
        'completeness': completeness,
    }


def get_top12_school_ids(db):
    names = ['聖光学院','開成','麻布','駒場東邦','桜蔭','女子学院','雙葉','栄光学園','海城','芝中','浅野','慶應義塾普通部']
    ids = []
    for n in names:
        r = db.execute("SELECT id, name_ja FROM schools_v2 WHERE name_ja LIKE ?", (f'%{n}%',)).fetchone()
        if r:
            ids.append((r[0], r[1]))
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--school-id', help='Single school id')
    parser.add_argument('--top12', action='store_true', help='Run on 12 sample schools')
    parser.add_argument('--limit', type=int, default=None, help='Max schools to process')
    parser.add_argument('--with-url-only', action='store_true', help='Only schools that have homepage_url')
    args = parser.parse_args()

    db = sqlite3.connect(DB, timeout=60.0)
    limiter = DomainRateLimiter()

    if args.school_id:
        targets = [(args.school_id, None)]
    elif args.top12:
        targets = get_top12_school_ids(db)
    else:
        # All schools with URL
        rows = db.execute("SELECT id, name_ja FROM schools_v2 WHERE homepage_url IS NOT NULL AND homepage_url != ''").fetchall()
        if args.limit:
            rows = rows[:args.limit]
        targets = rows

    print(f"Targets: {len(targets)} schools")
    log({'event':'batch_start', 'count':len(targets)})

    summary = []
    for i, (sid, name) in enumerate(targets):
        print(f"\n[{i+1}/{len(targets)}] {sid} {name or ''}")
        try:
            r = fetch_school(sid, db, limiter)
            print(f"  → {r}")
            summary.append(r)
        except Exception as e:
            print(f"  ERROR: {e}")
            log({'event':'school_error', 'school_id':sid, 'err':str(e)[:300]})

    db.close()

    print("\n=== Summary ===")
    ok = [r for r in summary if r.get('status')=='ok']
    print(f"Successful: {len(ok)}/{len(summary)}")
    if ok:
        total_phil = sum(r.get('philosophies_added',0) for r in ok)
        total_tt = sum(r.get('testimonials_added',0) for r in ok)
        print(f"Philosophies added: {total_phil}")
        print(f"Testimonials added: {total_tt}")

    log({'event':'batch_end', 'success':len(ok), 'total':len(summary)})

if __name__ == '__main__':
    main()
