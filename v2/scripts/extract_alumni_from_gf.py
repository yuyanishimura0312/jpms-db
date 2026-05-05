#!/usr/bin/env python3
"""Extract alumni-school candidates from GF DB → JSONL output.

GF DB の childhood_profiles の notes_ja / formative_events_ja に学校名が記載されている可能性。
Persons の summary_ja にも学校名が含まれることがある。
全件JSONL出力 → 後続セッションでJPMS DBに統合。
"""
import sqlite3
import json
import re
from pathlib import Path

GF_DB = Path('/Users/nishimura+/projects/research/great-figures-db/great_figures.db')
JPMS_DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output/alumni_candidates_from_gf.jsonl')

# Common school names (from JPMS schools_v2)
def load_school_names():
    db = sqlite3.connect(JPMS_DB, timeout=120.0)
    db.execute('PRAGMA busy_timeout=120000')
    rows = db.execute("SELECT id, name_ja FROM schools_v2").fetchall()
    db.close()
    # Build map: short name → school_id
    schools = {}
    for sid, name in rows:
        if not name or name == '_全国集計_':
            continue
        # Try multiple short forms
        forms = [name]
        if name.endswith('中学校'):
            forms.append(name[:-3])  # 開成
        if name.endswith('中等部'):
            forms.append(name[:-3])
        if name.endswith('中等教育学校'):
            forms.append(name[:-6])
        for f in forms:
            if f and len(f) >= 2:
                schools[f] = sid
    return schools


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    schools = load_school_names()
    print(f"School name patterns: {len(schools)}")

    gf = sqlite3.connect(GF_DB)
    gf.row_factory = sqlite3.Row

    # Search persons.summary_ja and childhood_profiles for school names
    rows = gf.execute("""
        SELECT p.id, p.name_ja, p.birth_year, p.death_year, p.category_primary,
               p.summary_ja, p.entrepreneur_score,
               cp.formal_education, cp.notes_ja, cp.formative_events_ja, cp.formative_influences_ja
        FROM persons p
        LEFT JOIN childhood_profiles cp ON p.id = cp.person_id
        WHERE p.country_modern = 'Japan' AND p.birth_year >= 1850
    """).fetchall()

    print(f"Persons to scan: {len(rows)}")

    matches = 0
    with OUT.open('w') as f:
        for r in rows:
            text = ' '.join(filter(None, [r['summary_ja'], r['notes_ja'], r['formative_events_ja'], r['formative_influences_ja']]))
            if not text:
                continue
            for school_name, sid in schools.items():
                if school_name in text:
                    out = {
                        'gf_person_id': r['id'],
                        'name': r['name_ja'],
                        'birth': r['birth_year'],
                        'death': r['death_year'],
                        'category': r['category_primary'],
                        'matched_school_name': school_name,
                        'matched_school_id': sid,
                        'evidence_text': text[:300],
                        'entrepreneur_score': r['entrepreneur_score'],
                        'formal_education': r['formal_education'],
                        'source_db': 'GF',
                    }
                    f.write(json.dumps(out, ensure_ascii=False) + '\n')
                    matches += 1
                    break  # one match per person
    print(f"Matches written: {matches}")
    gf.close()

    # Show sample
    if matches > 0:
        print("\n=== Sample matches ===")
        with OUT.open() as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                d = json.loads(line)
                print(f"  {d['name']} ({d['birth']}) → {d['matched_school_name']} [{d['category']}]")


if __name__ == '__main__':
    main()
