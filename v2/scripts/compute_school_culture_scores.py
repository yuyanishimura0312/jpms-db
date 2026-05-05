#!/usr/bin/env python3
"""Compute school_culture_score for all 525 schools using heuristic from existing v1 data.

10次元: cult_autonomy / structure / diversity / intensity / mentor / creativity /
        competition / community / internationality / spirituality
各次元は構造特徴（性別・宗教・接続形態・建学理念キーワード）から推定。
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# 次元別の重み付けルール（構造特徴 → スコア寄与）
RULES = {
    'cult_autonomy': {
        'religion': {'protestant': +12, 'non_religious': +8, 'catholic': -2, 'buddhist': -4},
        'gender': {'boys': +5, 'coed': +3, 'girls': 0},
        'integration': {'none': +10, 'full': +5, 'attached': -2, 'linked': +3},
        'keywords': {
            'pos': ['自由', '自主', '自治', '自立', '個性', '主体'],
            'neg': ['規律', '厳格', '管理']
        }
    },
    'cult_structure': {
        'religion': {'catholic': +6, 'buddhist': +4, 'protestant': +2, 'non_religious': 0},
        'gender': {'girls': +3, 'coed': 0, 'boys': -2},
        'integration': {'attached': +6, 'full': +5, 'none': -3},
        'keywords': {
            'pos': ['規律', '伝統', '秩序', '校則', '徹底'],
            'neg': ['自由', '柔軟']
        }
    },
    'cult_diversity': {
        'religion': {'non_religious': +5, 'protestant': +6, 'catholic': +3, 'buddhist': +1},
        'gender': {'coed': +8, 'boys': -3, 'girls': -3},
        'integration': {'none': +5, 'full': 0, 'attached': -2},
        'keywords': {
            'pos': ['国際', 'グローバル', '多様', '異文化', '帰国'],
            'neg': ['伝統', '純血']
        }
    },
    'cult_intensity': {
        'religion': {'non_religious': +5, 'catholic': +2, 'protestant': +1, 'buddhist': 0},
        'gender': {'boys': +5, 'coed': 0, 'girls': 0},
        'integration': {'attached': +6, 'full': +4, 'none': +3},
        'keywords': {
            'pos': ['学力', '進学', '難関', '徹底', '探究', '高度'],
            'neg': ['ゆとり', 'のびのび']
        }
    },
    'cult_mentor': {
        'religion': {'catholic': +8, 'protestant': +6, 'buddhist': +5, 'non_religious': 0},
        'gender': {'girls': +6, 'boys': +2, 'coed': +1},
        'integration': {'full': +5, 'attached': 0, 'none': +3},
        'keywords': {
            'pos': ['面倒見', '寄り添い', '個別', '少人数', '担任'],
            'neg': []
        }
    },
    'cult_creativity': {
        'religion': {'protestant': +5, 'non_religious': +4, 'catholic': +2, 'buddhist': 0},
        'gender': {'coed': +3, 'girls': +2, 'boys': 0},
        'integration': {'full': +4, 'none': +5, 'attached': 0},
        'keywords': {
            'pos': ['創造', '独自', '探究', '芸術', '表現', '個性'],
            'neg': []
        }
    },
    'cult_competition': {
        'religion': {'non_religious': +6, 'protestant': 0, 'catholic': -2, 'buddhist': -4},
        'gender': {'boys': +6, 'coed': 0, 'girls': -2},
        'integration': {'attached': +4, 'full': +3, 'none': +2},
        'keywords': {
            'pos': ['競争', '挑戦', '上位', '難関', '勝つ'],
            'neg': ['協調', '思いやり']
        }
    },
    'cult_community': {
        'religion': {'catholic': +6, 'buddhist': +6, 'protestant': +4, 'non_religious': 0},
        'gender': {'girls': +4, 'boys': +3, 'coed': +1},
        'integration': {'attached': +5, 'full': +6, 'none': 0},
        'keywords': {
            'pos': ['共同', '一致団結', '絆', '仲間', '兄弟', '姉妹'],
            'neg': []
        }
    },
    'cult_internationality': {
        'religion': {'protestant': +8, 'catholic': +6, 'anglican': +6, 'non_religious': +2, 'buddhist': -2},
        'gender': {'coed': +3, 'girls': +2, 'boys': 0},
        'integration': {'none': +5, 'attached': 0},
        'keywords': {
            'pos': ['国際', 'グローバル', '英語', '海外', '留学'],
            'neg': []
        }
    },
    'cult_spirituality': {
        'religion': {'catholic': +12, 'protestant': +10, 'buddhist': +12, 'anglican': +10, 'non_religious': -2},
        'gender': {'girls': +2, 'boys': +1, 'coed': 0},
        'integration': {'attached': +1, 'full': 0, 'none': 0},
        'keywords': {
            'pos': ['祈り', '信仰', '宗教', '内省', '黙想', '感謝', '報恩'],
            'neg': []
        }
    },
}


def score_dim(school, philosophy_text, rules):
    s = 50  # baseline
    rel = school['religious_affiliation'] or 'unknown'
    gen = school['gender_type'] or 'coed'
    inte = school['integrated_type'] or 'attached'

    s += rules['religion'].get(rel, 0)
    s += rules['gender'].get(gen, 0)
    s += rules['integration'].get(inte, 0)

    if philosophy_text:
        for kw in rules['keywords']['pos']:
            if kw in philosophy_text:
                s += 4
        for kw in rules['keywords']['neg']:
            if kw in philosophy_text:
                s -= 4

    return max(0, min(100, s))


def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    schools = db.execute("SELECT * FROM schools_v2").fetchall()
    print(f"Schools: {len(schools)}")

    # Get philosophy text per school
    phil = {}
    for r in db.execute("SELECT school_id, GROUP_CONCAT(text_full, ' | ') as txt FROM school_philosophy_v2 GROUP BY school_id").fetchall():
        phil[r['school_id']] = r['txt']

    # Clear existing scores
    db.execute("DELETE FROM school_culture_score")

    now = datetime.now().isoformat()
    inserted = 0
    for s in schools:
        text = phil.get(s['id'], '')
        for dim_id, rules in RULES.items():
            score = score_dim(dict(s), text, rules)
            evidence_count = sum(1 for kw in rules['keywords']['pos']+rules['keywords']['neg'] if kw in (text or ''))
            evidence_count += 3  # for structural features
            db.execute("""
                INSERT INTO school_culture_score
                (school_id, culture_dim_id, score, evidence_count, evidence_summary, computed_at, method)
                VALUES (?,?,?,?,?,?,?)
            """, (s['id'], dim_id, score, evidence_count,
                  f"religion={s['religious_affiliation']}/gender={s['gender_type']}/integration={s['integrated_type']}/text_chars={len(text or '')}",
                  now, 'heuristic_v1'))
            inserted += 1

    db.commit()
    print(f"Inserted: {inserted} scores ({inserted/len(schools):.1f} per school)")

    # Sample output
    print("\nSample (top 3 schools by name 開成/桜蔭/麻布):")
    for sample in ['開成', '桜蔭', '麻布', '聖光学院', '雙葉']:
        rows = db.execute("""
            SELECT s.name_ja, c.culture_dim_id, c.score
            FROM schools_v2 s JOIN school_culture_score c ON s.id=c.school_id
            WHERE s.name_ja LIKE ?
            ORDER BY c.culture_dim_id
        """, (f'%{sample}%',)).fetchall()
        if rows:
            name = rows[0]['name_ja']
            scores = {r['culture_dim_id']: r['score'] for r in rows}
            print(f"  {name}: " + " ".join(f"{k.replace('cult_','')}={v}" for k,v in scores.items()))

    db.close()


if __name__ == '__main__':
    main()
