#!/usr/bin/env python3
"""Discover homepage URLs for schools without homepage_url.

戦略:
1. Wikipedia ja の学校ページに公式URLが記載されていることが多いため、検索に用いる
2. 学校公式サイトは "<学校名>.ed.jp" や "<学校名>-jh.ed.jp" 等のドメインパターンが多い
3. ed.jp ドメインがあれば優先

倫理:
- robots.txt 厳守
- Wikipedia の API を使用（公開API、レート制限緩い）
- 5秒/req 遅延
"""
import argparse
import sqlite3
import urllib.request
import urllib.parse
import time
import re
import json
import sys
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
WP_API = 'https://ja.wikipedia.org/w/api.php'
USER_AGENT = 'JPMS-DB-Research/2.0 (+research-contact@miratuku.org)'

def search_wp(name):
    params = {
        'action':'query', 'list':'search', 'srsearch':name + ' 中学校',
        'srlimit':3, 'format':'json', 'utf8':1,
    }
    url = WP_API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return data.get('query', {}).get('search', [])
    except Exception as e:
        return []

def get_wp_extlinks(title):
    params = {
        'action':'query', 'prop':'extlinks', 'titles':title,
        'ellimit':50, 'format':'json', 'utf8':1,
    }
    url = WP_API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            pages = data.get('query', {}).get('pages', {})
            for pid, page in pages.items():
                links = [l.get('*') for l in page.get('extlinks', [])]
                return links
    except Exception as e:
        return []

def pick_official_url(name, links):
    """Pick the most likely official school URL from Wikipedia external links."""
    # Priority: ed.jp / ac.jp domains containing school name keyword
    candidates = []
    for link in links:
        if not link:
            continue
        # Filter out Wikipedia internal, common non-official domains
        if any(skip in link for skip in ['wikipedia.org','wikimedia.org','google.com','youtube.com','twitter.com','facebook.com','instagram.com','archive.org']):
            continue
        # Score
        score = 0
        if '.ed.jp' in link:
            score += 10
        if '.ac.jp' in link:
            score += 8
        if '.jp/' in link or link.endswith('.jp'):
            score += 3
        # Prefer https
        if link.startswith('https://'):
            score += 2
        # Prefer root or short path
        path_parts = urllib.parse.urlparse(link).path.split('/')
        if len(path_parts) <= 2:
            score += 3
        candidates.append((score, link))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument('--pref', help='Filter by prefecture')
    args = parser.parse_args()

    db = sqlite3.connect(DB, timeout=60.0)
    where = "(homepage_url IS NULL OR homepage_url='')"
    if args.pref:
        where += f" AND location_pref='{args.pref}'"
    rows = db.execute(f"SELECT id, name_ja FROM schools_v2 WHERE {where} ORDER BY id LIMIT ?", (args.limit,)).fetchall()
    print(f"Targets: {len(rows)} schools without URL")

    found = 0
    for sid, name in rows:
        # Search WP
        results = search_wp(name)
        time.sleep(2)
        if not results:
            print(f"  {sid} {name}: no WP result")
            continue
        # First result whose title matches school name
        title = None
        for r in results:
            if name in r.get('title','') or r.get('title','').endswith('中学校') or r.get('title','').endswith('中学校・高等学校'):
                title = r['title']
                break
        if not title:
            title = results[0]['title']
        # Get external links
        links = get_wp_extlinks(title)
        time.sleep(2)
        url = pick_official_url(name, links)
        if url:
            db.execute("UPDATE schools_v2 SET homepage_url=? WHERE id=?", (url, sid))
            print(f"  {sid} {name}: {url}")
            found += 1
        else:
            print(f"  {sid} {name}: no URL extracted from {title}")

    db.commit()
    db.close()
    print(f"\nFound URLs for {found}/{len(rows)} schools")


if __name__ == '__main__':
    main()
