#!/usr/bin/env python3
"""Build outcome-dimension profiles for all 525 schools using rule-based heuristics.

Output: school_profiles.json with two coordinate systems per school:
  - process_axis: how do they educate (religious tradition × gender × integration)
  - outcome_axis: what outcomes are emphasized (5 outcome clusters)
"""
import json
from pathlib import Path

DATA = Path('/Users/nishimura+/projects/research/jpms-db/dashboards/data.json')
OUT  = Path('/Users/nishimura+/projects/research/jpms-db/dashboards/school_profiles.json')

OUTCOME_CLUSTERS = {
    'cognitive': '認知・学術 (批判的思考・創造性・学際的知識)',
    'social_emotional': '社会情動 (CASEL5要素・PERMA人間関係)',
    'values_morals': '価値観・道徳 (japanese_independent・倫理観・地域貢献)',
    'agency_civic': '主体性・市民性 (OECD変革コンピテンシー・社会的自立)',
    'wellbeing': 'ウェルビーイング (PERMA・PISA_WB・心理的安全)',
}

PROCESS_AXES = {
    'religion':       ['catholic','protestant','anglican','buddhist','non_religious','unknown','other'],
    'gender':         ['boys','girls','coed'],
    'integration':    ['attached','full','linked','none'],
}

def profile_outcome(school):
    """Heuristic outcome emphasis (0-100) per cluster, based on profile + philosophy text."""
    rel = school.get('religious_affiliation') or 'unknown'
    gen = school.get('gender_type') or 'coed'
    inte = school.get('integrated_type') or 'attached'
    text = ((school.get('founding_philosophy') or '') + ' ' + (school.get('education_principle') or '')).strip()

    # Base rates by archetype
    p = {k: 50 for k in OUTCOME_CLUSTERS}

    # Religion influence
    if rel == 'catholic':
        p['values_morals'] += 22; p['social_emotional'] += 12; p['wellbeing'] += 6
    elif rel == 'protestant':
        p['values_morals'] += 18; p['agency_civic'] += 12; p['social_emotional'] += 10
    elif rel == 'anglican':
        p['values_morals'] += 18; p['social_emotional'] += 10
    elif rel == 'buddhist':
        p['values_morals'] += 20; p['wellbeing'] += 12; p['social_emotional'] += 4
    elif rel == 'non_religious':
        p['cognitive'] += 6
    elif rel in ('unknown','other'):
        p['cognitive'] += 2

    # Gender influence (literature: boys' schools emphasize more academic+agency,
    # girls' schools more social/emotional+wellbeing, coed broader balance)
    if gen == 'boys':
        p['cognitive'] += 10; p['agency_civic'] += 8
    elif gen == 'girls':
        p['social_emotional'] += 14; p['wellbeing'] += 10; p['values_morals'] += 4
    elif gen == 'coed':
        p['agency_civic'] += 6; p['social_emotional'] += 4

    # Integration influence
    if inte in ('attached','full'):
        p['cognitive'] += 6
    elif inte == 'none':
        p['agency_civic'] += 8; p['cognitive'] += 4
    elif inte == 'linked':
        p['agency_civic'] += 4

    # Philosophy text keyword boost
    if text:
        kw = {
            'cognitive': ['学術','学問','知性','学力','批判','探究','科学','研究','思考'],
            'social_emotional': ['友愛','友','友情','心','共感','他者','人間関係','寄り添'],
            'values_morals': ['道徳','倫理','人格','品性','奉仕','信仰','規律','感謝','報恩'],
            'agency_civic': ['自立','自主','社会','貢献','リーダー','創造','自治','変革','使命'],
            'wellbeing': ['幸福','健康','明るい','ウェルビーイング','安心','希望','個性','尊重'],
        }
        for cluster, keys in kw.items():
            for k in keys:
                if k in text:
                    p[cluster] += 6

    # Cap 0-100
    for k in p:
        p[k] = max(0, min(100, p[k]))

    # Pick primary outcome (max) and secondary
    sorted_p = sorted(p.items(), key=lambda x: -x[1])
    primary = sorted_p[0][0]
    secondary = sorted_p[1][0]
    return p, primary, secondary

def archetype_label(school):
    """Process-side archetype: e.g. 'カトリック女子・付属型'."""
    rel = school.get('religious_affiliation') or 'unknown'
    gen = school.get('gender_type') or 'coed'
    inte = school.get('integrated_type') or 'attached'
    rel_ja = {
        'catholic':'カトリック','protestant':'プロテスタント','anglican':'聖公会',
        'buddhist':'仏教','non_religious':'無宗教','unknown':'不明','other':'他'
    }[rel]
    gen_ja = {'boys':'男子','girls':'女子','coed':'共学'}[gen]
    inte_ja = {'attached':'付属','full':'完全一貫','linked':'連携','none':'独立'}[inte]
    return f"{rel_ja}・{gen_ja}・{inte_ja}"

def main():
    with DATA.open() as f:
        data = json.load(f)

    profiles = []
    for s in data['schools']:
        outcomes, primary, secondary = profile_outcome(s)
        profiles.append({
            'id': s['id'],
            'name': s['name_ja'],
            'pref': s.get('location_pref'),
            'gender': s.get('gender_type'),
            'religion': s.get('religious_affiliation'),
            'integration': s.get('integrated_type'),
            'establishment_year': s.get('establishment_year'),
            'archetype': archetype_label(s),
            'outcomes': outcomes,
            'primary': primary,
            'secondary': secondary,
            'has_text': bool(s.get('founding_philosophy') or s.get('education_principle')),
        })

    out = {
        'meta': data['meta'],
        'outcome_clusters': OUTCOME_CLUSTERS,
        'profiles': profiles,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"Wrote {len(profiles)} profiles to {OUT}")

    # Quick stats
    from collections import Counter
    arch = Counter(p['archetype'] for p in profiles)
    print("\nTop archetypes:")
    for a,c in arch.most_common(15):
        print(f"  {c:4d}  {a}")
    primary = Counter(p['primary'] for p in profiles)
    print("\nPrimary outcome:")
    for k,c in primary.most_common():
        print(f"  {c:4d}  {k}")

if __name__ == '__main__':
    main()
