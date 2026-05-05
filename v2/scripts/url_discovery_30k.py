#!/usr/bin/env python3
"""URL discovery for schools with no homepage_url.

Uses Wikipedia API (Japanese) to find official school URLs.
Strict ethics: 1 req/sec to Wikipedia.
"""
import sqlite3
import urllib.request
import urllib.parse
import json
import re
import time
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org; Python urllib)'
WIKI_API = 'https://ja.wikipedia.org/w/api.php'
DELAY = 1.0


def wiki_search(name):
    """Search Wikipedia for school name and find official URL in article."""
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': f'"{name}" 中学校',
        'format': 'json',
        'srlimit': 3,
    }
    try:
        url = WIKI_API + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        results = data.get('query', {}).get('search', [])
        if not results:
            return None
        return results[0]['title']
    except Exception:
        return None


def wiki_get_extract(title):
    """Get article text and parse external links."""
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'extlinks',
        'ellimit': 50,
        'format': 'json',
    }
    try:
        url = WIKI_API + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        pages = data.get('query', {}).get('pages', {})
        for p in pages.values():
            links = [el.get('*') for el in p.get('extlinks', [])]
            return links
    except Exception:
        pass
    return []


def pick_official(name, links):
    """Pick most likely official URL."""
    if not links:
        return None
    # Filter out wikipedia, archive, social media
    excluded = ['wikipedia.org', 'wikimedia', 'twitter.com', 'facebook.com',
                'instagram.com', 'youtube.com', 'archive.org', 'mext.go.jp',
                'shijokisei.jp', 'goo.gl', 'amazon', 'google.com', 'yahoo.co']
    candidates = [l for l in links if not any(e in l for e in excluded)]
    if not candidates:
        return None
    # Prefer .ed.jp, .ac.jp, school-specific domains
    for c in candidates:
        if '.ed.jp' in c or '.ac.jp' in c:
            return c
    # Then prefer http(s) without query/fragment
    for c in candidates:
        if c.startswith('http') and '?' not in c and '#' not in c.split('/')[-1]:
            return c
    return candidates[0]


def main():
    db = sqlite3.connect(DB, timeout=300.0)
    db.execute('PRAGMA busy_timeout=300000')
    no_url = db.execute(
        "SELECT id, name_ja FROM schools_v2 WHERE homepage_url IS NULL OR homepage_url=''"
    ).fetchall()
    print(f"対象: {len(no_url)}校")
    found = 0
    for i, (sid, name) in enumerate(no_url, 1):
        title = wiki_search(name)
        time.sleep(DELAY)
        if not title:
            if i % 20 == 0:
                print(f"  [{i}/{len(no_url)}] {sid} {name}: no Wikipedia article")
            continue
        links = wiki_get_extract(title)
        time.sleep(DELAY)
        url = pick_official(name, links)
        if url:
            db.execute("UPDATE schools_v2 SET homepage_url=? WHERE id=?", (url, sid))
            db.commit()
            found += 1
            if found % 20 == 0:
                print(f"  [{i}/{len(no_url)}] found={found} ← {sid} {name}: {url}")
        else:
            if i % 30 == 0:
                print(f"  [{i}/{len(no_url)}] {sid} {name} (article={title}): no URL match")
    print(f"\nDiscovered: {found} URLs")
    db.close()


if __name__ == '__main__':
    main()
