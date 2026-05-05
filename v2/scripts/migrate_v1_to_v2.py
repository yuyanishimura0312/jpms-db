#!/usr/bin/env python3
"""Migrate v1 jpms.db schools data into v2 jpms_v2.db schools_v2 table."""
import sqlite3
import sys
from pathlib import Path

V1 = Path('/Users/nishimura+/projects/research/jpms-db/jpms.db')
V2 = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

def main():
    src = sqlite3.connect(V1)
    dst = sqlite3.connect(V2)
    src.row_factory = sqlite3.Row

    rows = src.execute("SELECT * FROM jpms_schools").fetchall()
    cols = list(rows[0].keys()) if rows else []
    print(f"v1 schools: {len(rows)} rows, cols={cols}")

    inserted = 0
    for r in rows:
        d = dict(r)
        try:
            dst.execute("""
                INSERT OR REPLACE INTO schools_v2
                (id, legacy_id, name_ja, name_kana, establishment_year, school_corporation,
                 religious_affiliation, gender_type, integrated_type,
                 location_pref, location_city, homepage_url,
                 data_completeness_v2, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d['id'], d['id'], d.get('name_ja'), d.get('name_kana'),
                d.get('establishment_year'), d.get('school_corporation'),
                d.get('religious_affiliation'), d.get('gender_type'), d.get('integrated_type'),
                d.get('location_pref'), d.get('location_city'),
                d.get('website_url'),
                d.get('data_completeness'),
                f"migrated from v1 founding_philosophy: {d.get('founding_philosophy') or ''}"[:500] if d.get('founding_philosophy') else None
            ))
            inserted += 1
            # If philosophy text exists, copy to school_philosophy_v2
            if d.get('founding_philosophy'):
                dst.execute("""
                    INSERT INTO school_philosophy_v2
                    (school_id, philosophy_type, text_full, word_count, rights_level, language)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (d['id'], 'founding_philosophy', d['founding_philosophy'],
                      len(d['founding_philosophy']), 'quoted_with_attribution', 'ja'))
            if d.get('education_principle'):
                dst.execute("""
                    INSERT INTO school_philosophy_v2
                    (school_id, philosophy_type, text_full, word_count, rights_level, language)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (d['id'], 'education_principle', d['education_principle'],
                      len(d['education_principle']), 'quoted_with_attribution', 'ja'))
        except Exception as e:
            print(f"Error on {d.get('id')}: {e}")

    dst.commit()
    print(f"Migrated: {inserted} schools")
    print(f"Philosophy entries: {dst.execute('SELECT COUNT(*) FROM school_philosophy_v2').fetchone()[0]}")

    src.close()
    dst.close()

if __name__ == '__main__':
    main()
