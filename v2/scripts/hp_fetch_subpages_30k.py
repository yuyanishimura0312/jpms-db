#!/usr/bin/env python3
"""HP fetcher with sub-page discovery — fetches top page + 5-10 priority sub-pages.

Strict ethics:
- robots.txt enforcement via urllib.robotparser
- 5 sec/req delay per domain
- User-Agent disclosed
- Skip if already cached
- Per-school cap: 12 pages max
"""
import sqlite3
import urllib.request
import urllib.parse
import urllib.robotparser
import re
import time
import hashlib
import threading
from pathlib import Path
from collections import defaultdict, deque

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')
USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org)'
DELAY_PER_DOMAIN = 5.0
MAX_PAGES_PER_SCHOOL = 12

PRIORITY_KEYWORDS = [
    'principal', 'kocho', 'message', 'aisatsu', 'rinen', 'philosophy',
    'voice', 'student', 'seito', 'koe', 'schoollife',
    'alumni', 'sotsugyo', 'graduate', 'ob', 'og',
    'parent', 'pta', 'hogo', 'family',
    'curriculum', 'kyoiku', 'education', 'syllabus',
    'progress', 'shinro', 'career',
    'feature', 'tokucho', 'about', 'school',
    'interview',
]


_robots_cache = {}
_last_fetch = defaultdict(float)
_lock = threading.Lock()


def _domain(url):
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return ''


def can_fetch(url):
    d = _domain(url)
    if not d:
        return False
    if d not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(f'{urllib.parse.urlparse(url).scheme}://{d}/robots.txt')
            rp.read()
            _robots_cache[d] = rp
        except Exception:
            _robots_cache[d] = None
    rp = _robots_cache[d]
    if rp is None:
        return True
    try:
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def respectful_fetch(url):
    d = _domain(url)
    with _lock:
        elapsed = time.time() - _last_fetch[d]
        if elapsed < DELAY_PER_DOMAIN:
            time.sleep(DELAY_PER_DOMAIN - elapsed)
        _last_fetch[d] = time.time()
    if not can_fetch(url):
        return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT,
                                                   'Accept-Language': 'ja, en;q=0.5'})
        with urllib.request.urlopen(req, timeout=20) as r:
            ct = r.headers.get('Content-Type', '')
            if 'text' not in ct and 'html' not in ct:
                return None
            data = r.read(2_000_000)  # 2MB cap
        # Decode
        for enc in ['utf-8', 'shift_jis', 'euc-jp', 'iso-2022-jp']:
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return None


def discover_subpages(html, base_url):
    """Find priority sub-pages."""
    if not html:
        return []
    base_d = _domain(base_url)
    candidates = []
    seen = set()
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        href = m.group(1).strip()
        if href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('#'):
            continue
        # Resolve relative
        url = urllib.parse.urljoin(base_url, href)
        # Same domain only
        if _domain(url) != base_d:
            continue
        # Skip non-html
        if any(url.lower().endswith(x) for x in ['.pdf', '.jpg', '.png', '.jpeg', '.gif', '.zip', '.doc', '.xls']):
            continue
        # Strip fragment
        url = url.split('#')[0]
        if url in seen:
            continue
        seen.add(url)
        # Score by priority keywords
        url_l = url.lower()
        score = sum(1 for k in PRIORITY_KEYWORDS if k in url_l)
        if score > 0:
            candidates.append((score, url))
    candidates.sort(reverse=True)
    return [c[1] for c in candidates]


def slug_from_url(url):
    p = urllib.parse.urlparse(url)
    path = p.path.strip('/').replace('/', '_').replace('.', '_')
    if not path:
        path = 'index'
    if len(path) > 60:
        path = path[:60]
    return path or 'page'


def fetch_school(sid, hp_url):
    cache_dir = CACHE / sid
    cache_dir.mkdir(parents=True, exist_ok=True)
    fetched = []
    # Top page
    top_html = respectful_fetch(hp_url)
    if top_html:
        f = cache_dir / 'index.html'
        if not f.exists():
            f.write_text(top_html, errors='ignore')
        fetched.append(f.name)
    else:
        return fetched
    # Sub-pages
    subs = discover_subpages(top_html, hp_url)[:MAX_PAGES_PER_SCHOOL - 1]
    for sub_url in subs:
        slug = slug_from_url(sub_url)
        f = cache_dir / f'{slug}.html'
        if f.exists():
            continue
        sub_html = respectful_fetch(sub_url)
        if sub_html:
            f.write_text(sub_html, errors='ignore')
            fetched.append(f.name)
    return fetched


def main():
    db = sqlite3.connect(DB, timeout=300.0)
    schools = db.execute(
        "SELECT id, homepage_url FROM schools_v2 WHERE homepage_url IS NOT NULL AND homepage_url != ''"
    ).fetchall()
    db.close()

    # Filter to those needing fetch
    targets = []
    for sid, url in schools:
        cache_dir = CACHE / sid
        n_html = len(list(cache_dir.glob('*.html'))) if cache_dir.exists() else 0
        if n_html < MAX_PAGES_PER_SCHOOL:
            targets.append((sid, url, n_html))
    # Prioritize zero-cache schools first
    targets.sort(key=lambda x: x[2])

    print(f"Targets: {len(targets)} schools")
    total_fetched = 0
    for i, (sid, url, n_html) in enumerate(targets, 1):
        try:
            files = fetch_school(sid, url)
        except Exception as e:
            files = []
        total_fetched += len(files)
        if i % 10 == 0 or i == len(targets):
            print(f"  [{i}/{len(targets)}] {sid}: +{len(files)} files (total fetched: {total_fetched})")

    print(f"\nTotal pages fetched: {total_fetched}")


if __name__ == '__main__':
    main()
