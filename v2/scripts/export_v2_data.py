#!/usr/bin/env python3
"""Export jpms_v2.db data to JSON for the v2 dashboard."""
import sqlite3
import json
from pathlib import Path
from collections import defaultdict

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
OUT = Path('/Users/nishimura+/projects/research/jpms-db/v2/docs/v2_data.js')

def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    out = {
        'meta': {},
        'schools': [],
        'culture_dims': [],
        'culture_scores': {},
        'outcome_clusters': [],
        'outcome_dims': [],
        'era_relevance': [],
        'eras': [],
        'person_traits': [],
        'person_archetypes': [],
        'philosophy': {},
    }

    # Meta
    for r in db.execute("SELECT key, value FROM schema_metadata").fetchall():
        out['meta'][r['key']] = r['value']

    # Schools
    for r in db.execute("""SELECT id, legacy_id, name_ja, name_kana, establishment_year,
                                  school_corporation, religious_affiliation, gender_type,
                                  integrated_type, location_pref, location_city, homepage_url,
                                  data_completeness_v2 FROM schools_v2""").fetchall():
        out['schools'].append(dict(r))

    # Culture dims
    for r in db.execute("SELECT * FROM school_culture_dim").fetchall():
        out['culture_dims'].append(dict(r))

    # Culture scores - aggregate by school
    for r in db.execute("SELECT school_id, culture_dim_id, score FROM school_culture_score").fetchall():
        sid = r['school_id']
        if sid not in out['culture_scores']:
            out['culture_scores'][sid] = {}
        out['culture_scores'][sid][r['culture_dim_id']] = r['score']

    # Outcome clusters
    for r in db.execute("SELECT * FROM outcome_cluster_v2 ORDER BY display_order").fetchall():
        out['outcome_clusters'].append(dict(r))

    # Outcome dims
    for r in db.execute("SELECT * FROM outcome_dim_v2 ORDER BY cluster_id").fetchall():
        out['outcome_dims'].append(dict(r))

    # Era relevance
    for r in db.execute("SELECT * FROM outcome_era_relevance").fetchall():
        out['era_relevance'].append(dict(r))

    # Eras
    for r in db.execute("SELECT * FROM era_definition").fetchall():
        out['eras'].append(dict(r))

    # Person traits
    for r in db.execute("SELECT * FROM person_trait_dim").fetchall():
        out['person_traits'].append(dict(r))

    # Archetypes
    for r in db.execute("SELECT * FROM person_archetype").fetchall():
        out['person_archetypes'].append(dict(r))

    # Philosophy texts (only first 200 chars per school for size)
    for r in db.execute("SELECT school_id, philosophy_type, substr(text_full,1,300) as snippet FROM school_philosophy_v2").fetchall():
        sid = r['school_id']
        if sid not in out['philosophy']:
            out['philosophy'][sid] = {}
        out['philosophy'][sid][r['philosophy_type']] = r['snippet']

    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = "window.JPMS_V2 = " + json.dumps(out, ensure_ascii=False) + ";\n"
    OUT.write_text(text)
    print(f"Wrote {len(text)} bytes to {OUT}")
    print(f"  schools: {len(out['schools'])}")
    print(f"  culture_dims: {len(out['culture_dims'])}")
    print(f"  culture_scores: {len(out['culture_scores'])}")
    print(f"  outcome_clusters: {len(out['outcome_clusters'])}")
    print(f"  outcome_dims: {len(out['outcome_dims'])}")
    print(f"  era_relevance: {len(out['era_relevance'])}")
    print(f"  eras: {len(out['eras'])}")
    print(f"  person_traits: {len(out['person_traits'])}")
    print(f"  philosophy: {len(out['philosophy'])}")

    db.close()

if __name__ == '__main__':
    main()
