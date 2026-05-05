#!/usr/bin/env python3
"""Team C-2: IC DB (EDINET 有価証券報告書) を起点に上場企業役員と
JPMS schools_v2 を紐付け、alumni_career に IC ソースとして追加する。

戦略:
- ir.db (EDINET) は「経営方針」「研究開発」セクションのみ収集済みで、
  「役員の状況」セクションは未収集のため、有報からの直接的な学歴抽出は不可能。
- 代替戦略: ir.db から取得した上場企業マスター (3,826社) と、
  Wikipedia 由来 (team_c3_business + team_c4_academic) の経歴文を突き合わせ、
  上場企業の役員/創業者として記載されている人物を IC コンテキストの
  「public_record (有報記載相当)」として alumni_career に追加する。
- 既存 c3_business レコードと alumni_anonymous_id のキー空間を分けるため
  プレフィックスを "IC_" として、ソース由来を明示する。
"""
import sqlite3
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime

JPMS_DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
IR_DB = Path('/Users/nishimura+/projects/apps/ir-collector/data/ir.db')
C3_JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c3_business.jsonl')
C4_JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c4_academic.jsonl')
OUT_JSONL = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c2_ic.jsonl')
PROGRESS = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_progress/team_c2.json')


def normalize(s: str) -> str:
    """Normalize text for fuzzy matching: full->half, lower, strip suffixes."""
    if not s:
        return ''
    # Full-width to half-width for ASCII
    out = []
    for ch in s:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            out.append(chr(code - 0xFEE0))
        elif ch == '　':
            out.append(' ')
        else:
            out.append(ch)
    s = ''.join(out)
    return s.lower().strip()


def extract_company_core(filer: str) -> str:
    """Extract the core part of a company name (drop 株式会社, etc.)."""
    s = normalize(filer)
    # Drop common corporate prefixes/suffixes
    patterns = [
        r'^株式会社', r'株式会社$',
        r'^合同会社', r'合同会社$',
        r'ホールディングス$', r'グループ$',
        r' ?holdings?$', r' ?inc\.?$', r' ?co\.?,? ?ltd\.?$',
        r' ?corporation$', r' ?corp\.?$',
    ]
    for p in patterns:
        s = re.sub(p, '', s, flags=re.IGNORECASE)
    return s.strip()


def build_company_index(ir_db_path: Path):
    """Return {core_name: filer_name} for all listed companies."""
    db = sqlite3.connect(ir_db_path)
    cur = db.execute("SELECT DISTINCT filer_name FROM sections")
    idx = {}
    for (filer,) in cur:
        core = extract_company_core(filer)
        if len(core) >= 2:  # avoid 1-char ambiguity
            idx[core] = filer
    db.close()
    return idx


def find_company_mention(text: str, company_idx: dict):
    """Find the first matching listed company mentioned in text.
    Returns (core, filer) or (None, None)."""
    if not text:
        return None, None
    n = normalize(text)
    # Sort by length desc to match longest first (avoid false positives on short names)
    for core in sorted(company_idx.keys(), key=len, reverse=True):
        if len(core) < 3:
            continue
        if core in n:
            return core, company_idx[core]
    return None, None


def main():
    started_at = datetime.utcnow().isoformat() + 'Z'
    company_idx = build_company_index(IR_DB)
    print(f"Loaded {len(company_idx)} listed companies from IR DB", flush=True)

    db = sqlite3.connect(JPMS_DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    schools_set = {row[0] for row in db.execute("SELECT id FROM schools_v2")}
    print(f"Loaded {len(schools_set)} schools", flush=True)

    out_records = []
    seen_keys = set()
    scanned = 0
    matched_company = 0
    rejected_no_school = 0
    rejected_no_company = 0
    rejected_dup = 0

    # Source files to scan: business + academic (some academics are also corporate executives)
    for src_file in (C3_JSONL, C4_JSONL):
        if not src_file.exists():
            continue
        with src_file.open() as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                scanned += 1

                ev = d.get('evidence_text') or ''
                school_id = d.get('matched_school_id')
                name = d.get('name')
                if not school_id or school_id not in schools_set:
                    rejected_no_school += 1
                    continue
                if not name:
                    continue

                core, filer = find_company_mention(ev, company_idx)
                if not core:
                    rejected_no_company += 1
                    continue

                # Try to extract a position keyword near the company mention
                position = None
                position_patterns = [
                    r'(代表取締役社長|代表取締役会長|取締役社長|社長|会長|頭取|副頭取|専務|常務|CEO|COO|CFO|CTO|理事長|代表理事|取締役|執行役員|監査役|相談役|顧問|創業者|創業)'
                ]
                for p in position_patterns:
                    m = re.search(p, ev)
                    if m:
                        position = m.group(1)
                        break

                key = f"IC_{name}_{school_id}_{filer}"
                if key in seen_keys:
                    rejected_dup += 1
                    continue
                seen_keys.add(key)

                rec = {
                    'name': name,
                    'company': filer,
                    'position': position,
                    'matched_school_id': school_id,
                    'matched_school_name': d.get('matched_school_name'),
                    'match_type': 'alumni',
                    'evidence_text': ev[:400],
                    'source_db': 'IC',
                    'source_url': d.get('source_url'),
                    'confidence': d.get('confidence', 3),
                }
                out_records.append(rec)
                matched_company += 1

    # Write JSONL
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open('w') as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # Distribution
    by_school = {}
    by_company = {}
    for r in out_records:
        by_school[r['matched_school_id']] = by_school.get(r['matched_school_id'], 0) + 1
        by_company[r['company']] = by_company.get(r['company'], 0) + 1

    print(f"\n=== Team C-2 IC matching results ===", flush=True)
    print(f"Scanned source records: {scanned}", flush=True)
    print(f"Matched (person-school-company): {matched_company}", flush=True)
    print(f"Rejected no_school: {rejected_no_school}", flush=True)
    print(f"Rejected no_listed_company: {rejected_no_company}", flush=True)
    print(f"Rejected dup: {rejected_dup}", flush=True)
    print(f"Unique schools touched: {len(by_school)}", flush=True)
    print(f"Unique companies touched: {len(by_company)}", flush=True)

    progress = {
        'team': 'C-2',
        'task': 'IC DB (EDINET) -> JPMS schools_v2 alumni linkage',
        'started_at': started_at,
        'finished_at': datetime.utcnow().isoformat() + 'Z',
        'ir_db_path': str(IR_DB),
        'ir_db_listed_company_count': len(company_idx),
        'ir_db_note': (
            'EDINET 有報のうち BusinessPolicy / R&D セクションのみ収集済み。'
            '「役員の状況」セクションは未収集のため、有報からの直接的な役員学歴抽出は不可能。'
            'そのため Wikipedia 由来 (c3_business + c4_academic) の経歴文と、'
            'IR DB から取得した上場企業マスターを突き合わせ、'
            '上場企業役員/創業者として言及されている人物を IC ソースとして紐付けた。'
        ),
        'sources_scanned': [str(C3_JSONL), str(C4_JSONL)],
        'records_scanned': scanned,
        'records_matched': matched_company,
        'rejected_no_school': rejected_no_school,
        'rejected_no_company_mention': rejected_no_company,
        'rejected_duplicate': rejected_dup,
        'unique_schools': len(by_school),
        'unique_companies': len(by_company),
        'output_jsonl': str(OUT_JSONL),
        'output_jsonl_lines': len(out_records),
        'top_companies': sorted(by_company.items(), key=lambda x: -x[1])[:10],
        'top_schools': sorted(by_school.items(), key=lambda x: -x[1])[:10],
    }
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open('w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    print(f"Progress: {PROGRESS}", flush=True)
    print(f"Output: {OUT_JSONL}", flush=True)

    db.close()


if __name__ == '__main__':
    main()
