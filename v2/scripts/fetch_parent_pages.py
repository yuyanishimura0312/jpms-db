#!/usr/bin/env python3
"""Team B-5: Parent/PTA page fetcher with strict ethics compliance.

Builds on fetch_school_hp.py but targets parent-facing subpages
(保護者会・PTA・後援会・父母会) for the 223 schools with URLs.

倫理規律:
- robots.txt 厳守
- 同一ドメインへ最低5秒/req
- User-Agent: JPMS-DB-Research/2.0 (+research-contact@miratuku.org)
- 公開情報のみ
- 引用 < 400字（後段抽出側で保証）

Usage:
  python3 fetch_parent_pages.py            # all 223 schools
  python3 fetch_parent_pages.py --limit 50 # first 50
  python3 fetch_parent_pages.py --offset 100 --limit 100
  python3 fetch_parent_pages.py --school-id jpms_s_0001
"""
import argparse
import sqlite3
import urllib.request
import urllib.parse
import urllib.robotparser
import time
import sys
import json
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
CACHE_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/raw_html_cache')
LOG_FILE = Path('/Users/nishimura+/projects/research/jpms-db/v2/fetch_log.jsonl')

USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org)'
MIN_DELAY = 5.0
TIMEOUT = 20

# Parent / PTA oriented subpages
# Discovered patterns from real-world Japanese school sites: /student/, /guardian/,
# /current/, /students/, /support/, /about/family/, /outline/pta/, /outline/supporter/
PARENT_PRIORITY_PATHS = [
    ('parent', [
        '/parents/', '/parent/', '/guardian/',
        '/student/', '/students/', '/current/',
        '/about/parents/', '/about/family/',
        '/info/parents/', '/support/',
        '/admission/parents/',
    ]),
    ('pta', [
        '/pta/', '/PTA/',
        '/outline/pta/', '/outline/supporter/',
        '/about/pta/', '/info/pta/',
        '/parents/pta/', '/parent/pta/',
        '/foster/', '/koenkai/', '/fubokai/',
    ]),
]


def log(event):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a') as f:
        f.write(json.dumps({**event, 'ts': datetime.now().isoformat()}, ensure_ascii=False) + '\n')


def get_domain(url):
    return urllib.parse.urlparse(url).netloc


class DomainRateLimiter:
    """Per-domain rate limiter with robots.txt cache."""

    def __init__(self, min_delay=MIN_DELAY):
        self.last_fetch = {}
        self.min_delay = min_delay
        self.robots_cache = {}

    def can_fetch(self, url):
        domain = get_domain(url)
        if domain not in self.robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            scheme = urllib.parse.urlparse(url).scheme
            robots_url = f"{scheme}://{domain}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except Exception:
                self.robots_cache[domain] = None
        rp = self.robots_cache[domain]
        if rp is None:
            return True
        try:
            return rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True

    def wait_if_needed(self, url):
        domain = get_domain(url)
        last = self.last_fetch.get(domain, 0)
        elapsed = time.time() - last
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_fetch[domain] = time.time()


def fetch_url(url, limiter):
    if not limiter.can_fetch(url):
        log({'event': 'robots_blocked', 'url': url, 'team': 'b5'})
        return None, None, None
    limiter.wait_if_needed(url)
    req = urllib.request.Request(
        url,
        headers={'User-Agent': USER_AGENT, 'Accept-Language': 'ja,en;q=0.5'},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ct = r.headers.get('Content-Type', '')
            if 'text/html' not in ct.lower():
                log({'event': 'non_html', 'url': url, 'content_type': ct, 'team': 'b5'})
                return r.status, None, ct
            data = r.read()
            return r.status, data, ct
    except urllib.error.HTTPError as e:
        log({'event': 'http_error', 'url': url, 'status': e.code, 'team': 'b5'})
        return e.code, None, None
    except Exception as e:
        log({'event': 'fetch_error', 'url': url, 'err': str(e)[:200], 'team': 'b5'})
        return None, None, None


def discover_links_from_root(school_id, base):
    """Discover parent/PTA link targets from cached root.html.

    Returns dict {slug: [absolute_url, ...]} of discovered candidate URLs.
    """
    discovered = {'parent': [], 'pta': []}
    root_file = CACHE_DIR / school_id / 'root.html'
    if not root_file.exists():
        return discovered
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return discovered
    try:
        html = root_file.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return discovered
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        return discovered
    for a in soup.find_all('a', href=True):
        href = a.get('href', '').strip()
        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue
        text = a.get_text(strip=True)
        if not text:
            continue
        # 強アンカー: PTA / 後援会 / 父母会 / 育友会 / 保護者会 → pta
        if any(k in text for k in ['PTA', '後援会', '父母会', '父母の会', '育友会', '保護者会']):
            full = urllib.parse.urljoin(base + '/', href)
            if urllib.parse.urlparse(full).netloc == urllib.parse.urlparse(base).netloc:
                if full not in discovered['pta']:
                    discovered['pta'].append(full)
        # 一般: 在校生・保護者・保護者の方 → parent
        elif any(k in text for k in [
            '保護者', '在校生・', 'ご家庭', 'ファミリー', '父兄', '母の会',
        ]):
            # ログインリンクは除外
            if 'login' in href.lower() or 'ログイン' in text:
                continue
            full = urllib.parse.urljoin(base + '/', href)
            if urllib.parse.urlparse(full).netloc == urllib.parse.urlparse(base).netloc:
                if full not in discovered['parent']:
                    discovered['parent'].append(full)
    return discovered


def fetch_school_parent_pages(school_id, name, homepage_url, db, limiter):
    if not homepage_url:
        return {'school_id': school_id, 'status': 'no_url'}
    url = homepage_url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    school_dir = CACHE_DIR / school_id
    school_dir.mkdir(parents=True, exist_ok=True)

    fetched = []
    skipped = []

    # Discover real URLs from root.html first (best signal)
    discovered = discover_links_from_root(school_id, base)

    for slug, candidate_paths in PARENT_PRIORITY_PATHS:
        target = school_dir / f'{slug}.html'
        if target.exists():
            skipped.append({'slug': slug, 'reason': 'cached'})
            continue
        # Compose candidate URL list: discovered first, then heuristic
        discovered_urls = list(discovered.get(slug, []))
        candidate_urls = list(discovered_urls)
        if discovered_urls:
            # When discovery succeeded, also try top-2 heuristic patterns as backup
            for path in candidate_paths[:2]:
                full = base + path
                if full not in candidate_urls:
                    candidate_urls.append(full)
            candidate_urls = candidate_urls[:3]
        else:
            # No discovery: try only top-1 heuristic pattern to bound cost
            # (most schools without nav-link to PTA don't have those pages)
            for path in candidate_paths[:1]:
                full = base + path
                if full not in candidate_urls:
                    candidate_urls.append(full)

        success = False
        for cand_url in candidate_urls:
            status, content, _ = fetch_url(cand_url, limiter)
            if content and status == 200:
                target.write_bytes(content)
                try:
                    db.execute(
                        """INSERT INTO school_homepage_assets
                        (school_id, page_path, full_url, fetched_at, archive_path,
                         status_code, content_length, rights_level)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (school_id, slug, cand_url, datetime.now().isoformat(),
                         str(target.relative_to(Path('/Users/nishimura+/projects/research/jpms-db/v2'))),
                         status, len(content), 'archive_only'),
                    )
                except Exception as e:
                    log({'event': 'db_insert_error', 'school_id': school_id,
                         'err': str(e)[:200], 'team': 'b5'})
                fetched.append({'slug': slug, 'url': cand_url})
                success = True
                break
        if not success:
            skipped.append({'slug': slug, 'reason': 'not_found'})

    db.commit()
    return {
        'school_id': school_id, 'name': name, 'status': 'ok',
        'fetched': fetched, 'skipped': skipped,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--school-id', help='Fetch a single school by id')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()

    if not DB.exists():
        print(f"DB not found: {DB}")
        sys.exit(1)

    db = sqlite3.connect(DB, timeout=60.0)
    limiter = DomainRateLimiter()

    if args.school_id:
        rows = db.execute(
            "SELECT id, name_ja, homepage_url FROM schools_v2 WHERE id=?",
            (args.school_id,),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT id, name_ja, homepage_url FROM schools_v2
               WHERE homepage_url IS NOT NULL AND homepage_url != ''
               ORDER BY id""",
        ).fetchall()
        if args.offset:
            rows = rows[args.offset:]
        if args.limit:
            rows = rows[:args.limit]

    print(f"[Team B-5] Targets: {len(rows)} schools")
    log({'event': 'b5_batch_start', 'count': len(rows), 'team': 'b5'})

    summary = []
    for i, (sid, name, hp) in enumerate(rows):
        try:
            r = fetch_school_parent_pages(sid, name, hp, db, limiter)
        except Exception as e:
            r = {'school_id': sid, 'status': 'error', 'err': str(e)[:200]}
            log({'event': 'school_error', 'school_id': sid, 'err': str(e)[:200], 'team': 'b5'})
        summary.append(r)
        if (i + 1) % 10 == 0 or i + 1 == len(rows):
            ok = sum(1 for x in summary if x.get('status') == 'ok')
            f_pages = sum(len(x.get('fetched', [])) for x in summary)
            print(f"  [{i+1}/{len(rows)}] processed={ok} new_pages={f_pages}")

    db.close()
    ok = [r for r in summary if r.get('status') == 'ok']
    new_pages = sum(len(r.get('fetched', [])) for r in ok)
    print("\n=== B-5 Summary ===")
    print(f"Processed: {len(summary)} schools")
    print(f"Status OK: {len(ok)}")
    print(f"New parent/pta pages saved: {new_pages}")
    log({'event': 'b5_batch_end', 'success': len(ok), 'pages': new_pages, 'team': 'b5'})


if __name__ == '__main__':
    main()
