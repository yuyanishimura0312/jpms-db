#!/usr/bin/env python3
"""Seed career_archetype table from GF DB Japanese figures (modern era).

戦略:
1. GF DBから country_modern='Japan' かつ 1850年以降の偉人を抽出
2. category_primary でアーキタイプを分類
3. childhood_profiles と紐付けて若年期特性を抽出
4. 各アーキタイプを career_archetype に投入
"""
import sqlite3
import json
from pathlib import Path
from collections import defaultdict, Counter

GF_DB = Path('/Users/nishimura+/projects/research/great-figures-db/great_figures.db')
JPMS_DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# Map GF category → career archetype
CATEGORY_MAP = {
    'monarch': ('arch_career_political', '政治家・首長型', 'political', '統治・首長業'),
    'statesman': ('arch_career_political', '政治家・首長型', 'political', '統治・首長業'),
    'military': ('arch_career_military', '軍人・防衛型', 'military', '軍事・防衛'),
    'merchant': ('arch_career_business', '実業家・経営者型', 'business', '商業・経営'),
    'thinker': ('arch_career_thinker', '思想家・哲学者型', 'academia', '思想・哲学'),
    'religious': ('arch_career_religious', '宗教家・指導者型', 'religion', '宗教指導'),
    'revolutionary': ('arch_career_revolutionary', '社会改革者型', 'social', '社会変革'),
    'explorer': ('arch_career_explorer', '探検・冒険型', 'exploration', '探検・調査'),
    'inventor': ('arch_career_inventor', '発明家・技術者型', 'innovation', '発明・技術'),
    'scientist': ('arch_career_scientist', '科学者・研究者型', 'academia', '研究・科学'),
    'economist': ('arch_career_economist', '経済学者・金融型', 'economy', '経済・金融'),
    'manager': ('arch_career_manager', '経営者・組織管理型', 'business', '組織管理'),
    'diplomat': ('arch_career_diplomat', '外交官・国際型', 'diplomacy', '外交・国際'),
    'legal': ('arch_career_legal', '法曹・法律家型', 'law', '法律・司法'),
    'social_reformer': ('arch_career_social_reformer', '社会改革者・NPO型', 'social', 'NPO・社会変革'),
    'cultural': ('arch_career_cultural', '芸術家・文化人型', 'arts', '芸術・文化'),
    'other': ('arch_career_other', 'その他キャリア', 'other', 'その他'),
}


def main():
    gf = sqlite3.connect(GF_DB)
    gf.row_factory = sqlite3.Row
    jpms = sqlite3.connect(JPMS_DB)

    # Get Japanese modern-era persons with childhood profile
    rows = gf.execute("""
        SELECT p.id, p.name_ja, p.birth_year, p.death_year, p.category_primary,
               p.entrepreneur_profile_ja, p.entrepreneur_score,
               cp.formal_education, cp.education_quality, cp.social_class,
               cp.prodigy_indicator, cp.first_achievement_age,
               cp.key_mentor_ja, cp.notes_ja
        FROM persons p
        LEFT JOIN childhood_profiles cp ON p.id = cp.person_id
        WHERE p.country_modern = 'Japan' AND p.birth_year >= 1850
        ORDER BY p.birth_year
    """).fetchall()

    print(f"Japanese modern-era persons: {len(rows)}")

    # Aggregate by archetype
    archetypes = defaultdict(lambda: {
        'persons': [],
        'count': 0,
        'avg_entrepreneur_score': 0,
        'prodigy_count': 0,
        'social_classes': Counter(),
        'formal_educations': Counter(),
    })

    for r in rows:
        cat = r['category_primary']
        arch_id, ja_name, en_id, ja_dom = CATEGORY_MAP.get(cat, CATEGORY_MAP['other'])
        a = archetypes[(arch_id, ja_name, en_id, ja_dom)]
        a['persons'].append({
            'id': r['id'],
            'name': r['name_ja'],
            'birth': r['birth_year'],
            'death': r['death_year'],
            'mentor': r['key_mentor_ja'],
        })
        a['count'] += 1
        if r['entrepreneur_score']:
            a['avg_entrepreneur_score'] += r['entrepreneur_score']
        if r['prodigy_indicator']:
            a['prodigy_count'] += 1
        if r['social_class']:
            a['social_classes'][r['social_class']] += 1
        if r['formal_education']:
            a['formal_educations'][r['formal_education']] += 1

    # Insert into career_archetype
    inserted = 0
    for (arch_id, ja_name, domain, ja_dom), data in archetypes.items():
        n = data['count']
        if n == 0:
            continue
        avg_score = data['avg_entrepreneur_score'] / n if n else 0

        # Predicting traits (中学生時に観察可能な特性) - heuristic per archetype
        traits = {
            'arch_career_political': {'agreeableness':'high', 'extraversion':'high', 'leadership':'observed_early'},
            'arch_career_business': {'conscientiousness':'high', 'risk_taking':'high', 'effectuation':'observed'},
            'arch_career_thinker': {'openness':'high', 'metacognition':'high', 'introvert_thinker':'observed'},
            'arch_career_scientist': {'openness':'high', 'conscientiousness':'high', 'curiosity':'observed_early'},
            'arch_career_inventor': {'openness':'high', 'creativity':'observed_early', 'self_regulation':'high'},
            'arch_career_cultural': {'openness':'very_high', 'creativity':'observed_early', 'aesthetic':'high'},
            'arch_career_social_reformer': {'agreeableness':'high', 'agency':'high', 'civic':'observed'},
            'arch_career_economist': {'conscientiousness':'high', 'logical_reasoning':'high'},
            'arch_career_diplomat': {'agreeableness':'high', 'cross_cultural':'high'},
            'arch_career_legal': {'conscientiousness':'high', 'logical_reasoning':'high'},
            'arch_career_military': {'conscientiousness':'high', 'grit':'high'},
            'arch_career_religious': {'agreeableness':'high', 'spirituality':'high'},
            'arch_career_explorer': {'openness':'high', 'risk_taking':'high'},
            'arch_career_revolutionary': {'agency':'very_high', 'risk_taking':'high'},
            'arch_career_manager': {'conscientiousness':'high', 'leadership':'observed_early'},
            'arch_career_other': {},
        }.get(arch_id, {})

        notable = sorted(data['persons'], key=lambda x: x['birth'] or 9999)[:5]

        jpms.execute("""INSERT OR REPLACE INTO career_archetype
            (id, name_ja, name_en, domain, description, predicting_traits, development_path,
             source_db, case_count, notable_examples)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                arch_id, ja_name, arch_id.replace('arch_career_','').replace('_',' ').title(),
                domain,
                f"GF DBから抽出した日本人近代以降{ja_dom}従事者{n}名のアーキタイプ。"
                f"prodigy_indicator={data['prodigy_count']}名、平均起業家スコア={avg_score:.1f}。"
                f"主要な社会階級: {dict(data['social_classes'].most_common(3))}, "
                f"formal_education: {dict(data['formal_educations'].most_common(3))}",
                json.dumps(traits, ensure_ascii=False),
                f"中学生時の観察可能特性 → 後年の{ja_dom}キャリアに発達。GF DB childhood_profiles と persons テーブルに依拠。",
                'GF',
                n,
                json.dumps([f"{p['name']}({p['birth']})" for p in notable], ensure_ascii=False),
            ))
        inserted += 1

    jpms.commit()
    print(f"\ncareer_archetype inserted: {inserted}")
    for r in jpms.execute("SELECT id, name_ja, case_count, notable_examples FROM career_archetype ORDER BY case_count DESC").fetchall():
        examples = json.loads(r[3] or '[]')
        print(f"  {r[0]:30s} {r[1]:25s} {r[2]:>4d}件  例: {', '.join(examples[:3])}")

    gf.close()
    jpms.close()


if __name__ == '__main__':
    main()
