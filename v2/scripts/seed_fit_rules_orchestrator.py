#!/usr/bin/env python3
"""Seed person_school_fit_rule with theory-grounded matching rules.

Implementation by central orchestrator (Claude Opus 4.7).
理論基盤: Holland P-E Fit, Eccles Stage-Environment Fit, Edwards 多次元 P-E Fit,
Hoover-Dempsey & Sandler, Lerner PYD Five Cs, Marcia Identity Status.
"""
import sqlite3
import json
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# Format: (rule_name, person_pattern, school_pattern, formula, expected_outcomes, evidence_from, confidence, rationale)
RULES = [
    # === 探究者・創造者型 ===
    ('探究者×自律性高校',
     {"archetype":"arch_explorer","trait_o":">75","trait_c":">60"},
     {"cult_autonomy":">65","cult_creativity":">60"},
     'P_o*0.4 + P_c*0.3 + S_autonomy*0.2 + S_creativity*0.1',
     {"cognitive":"high","creative_excellence":"high"},
     'Holland P-E Fit + Eccles Stage-Environment Fit',
     4,
     '内的探求志向の生徒は自律性高い学校で創造性を伸ばす傾向。麻布・武蔵・栄光学園型が適合。'),
    ('創造者×創造性奨励校',
     {"archetype":"arch_creator","trait_o":">80","trait_n":">55"},
     {"cult_creativity":">65","cult_autonomy":">60"},
     'P_o*0.5 + S_creativity*0.3 + (1-S_competition/100)*0.2',
     {"creative_excellence":"high","wellbeing":"medium"},
     'Csikszentmihalyi Flow + Howard Gardner Creating Minds',
     4,
     '創造性の高い生徒には Flow 経験を支える環境が必要。競争よりも内発的動機を支える校風。'),

    # === リーダー・経営者型 ===
    ('リーダー×競争性中-高校',
     {"archetype":"arch_leader","trait_e":">70","trait_c":">65"},
     {"cult_competition":"50-75","cult_intensity":">60"},
     'P_e*0.4 + P_c*0.3 + S_competition*0.2 + S_intensity*0.1',
     {"agency_civic":"high","market_management":"high"},
     'Collins Level 5 Leadership + Drucker Management',
     4,
     'リーダー型生徒は適度な競争環境で実力を磨く。開成・桜蔭・聖光学院型が適合。'),
    ('挑戦者×学業強度高校',
     {"archetype":"arch_warrior","trait_e":">70","trait_c":">70","trait_n":"<40"},
     {"cult_intensity":">70","cult_structure":">60"},
     'P_grit*0.5 + S_intensity*0.3 + S_structure*0.2',
     {"cognitive":"high","agency_civic":"high","market_management":"high"},
     'Duckworth GRIT + Sarasvathy Effectuation',
     4,
     '困難に立ち向かう型は強度高い学業環境で粘り強さを伸ばす。難関校型と相性良。'),

    # === 養育者・調停者型 ===
    ('養育者×精神性・共同体校',
     {"archetype":"arch_caregiver","trait_a":">75","trait_e":">55"},
     {"cult_spirituality":">60","cult_community":">60","cult_mentor":">60"},
     'P_a*0.4 + S_community*0.3 + S_mentor*0.2 + S_spirituality*0.1',
     {"social_emotional":"high","values_morals":"high"},
     'Lerner PYD Caring + Hoover-Dempsey Family Engagement',
     5,
     '他者ケア志向の生徒はカトリック・プロテスタント校で価値観を深める。雙葉・聖心・栄光型。'),
    ('調停者×多様性高校',
     {"archetype":"arch_mediator","trait_a":">75","trait_o":">65"},
     {"cult_diversity":">65","cult_internationality":">60"},
     'P_a*0.4 + P_o*0.2 + S_diversity*0.3 + S_internationality*0.1',
     {"social_emotional":"high","agency_civic":"high"},
     'OECD Cross-Cultural Competence + ICAPS',
     4,
     '対立調整志向は多様性高い学校で発揮。国際バカロレア校・帰国子女校型。'),

    # === 職人・内省型 ===
    ('職人×構造度高・専門校',
     {"archetype":"arch_craftsman","trait_c":">80","trait_o":"40-65"},
     {"cult_structure":">65","cult_intensity":">60","cult_mentor":">55"},
     'P_c*0.5 + S_structure*0.2 + S_mentor*0.2 + S_intensity*0.1',
     {"cognitive":"high","creative_excellence":"medium"},
     'Anders Ericsson Domain Mastery + Zuckerman Mentor Quality',
     4,
     '専門技能磨き上げ型はメンター密度高い構造化環境で能力開花。理工系難関校型。'),
    ('内省思索者×精神性校',
     {"archetype":"arch_introvert_thinker","trait_e":"<40","trait_o":">70","trait_n":">55"},
     {"cult_spirituality":">55","cult_autonomy":">55","cult_competition":"<50"},
     'P_o*0.4 + S_autonomy*0.3 + S_spirituality*0.2 + (1-S_competition/100)*0.1',
     {"cognitive":"high","wellbeing":"high","values_morals":"medium"},
     'Marcia Identity Moratorium + Csikszentmihalyi Flow',
     4,
     '内向思索型は静謐で精神性ある環境で深い学びを得る。仏教校・キリスト教校との相性。'),

    # === 社交創造・堅実型 ===
    ('社交創造者×国際・創造性校',
     {"archetype":"arch_social_creator","trait_e":">70","trait_o":">75"},
     {"cult_internationality":">65","cult_creativity":">60","cult_diversity":">60"},
     'P_e*0.3 + P_o*0.3 + S_internationality*0.2 + S_creativity*0.2',
     {"creative_excellence":"high","market_management":"high","agency_civic":"high"},
     'Sarasvathy Effectuation + WEF Future of Jobs',
     4,
     '社交創造型は国際×創造性高い環境で起業家素養を育てる。渋谷教育・広尾学園型。'),
    ('堅実型×構造度・共同体校',
     {"archetype":"arch_steady","trait_c":">70","trait_a":">65","trait_n":"<45"},
     {"cult_structure":">60","cult_community":">60","cult_spirituality":">50"},
     'P_c*0.4 + P_a*0.3 + S_structure*0.2 + S_community*0.1',
     {"values_morals":"high","social_emotional":"high","wellbeing":"high"},
     'Lerner PYD Five Cs + Hoover-Dempsey',
     4,
     '安定志向は伝統校・宗教系で堅実なキャリア基盤を作る。雙葉・白百合・カトリック女子校型。'),

    # === Big Five 単独軸ルール ===
    ('高グロースマインドセット×探究奨励校',
     {"trait_growth_mindset":">70"},
     {"cult_creativity":">55","cult_autonomy":">55"},
     'P_gm*0.6 + S_creativity*0.2 + S_autonomy*0.2',
     {"cognitive":"high","creative_excellence":"medium"},
     'Dweck Mindset 2006 + Self-Determination Theory',
     4,
     'Growth Mindset 高い生徒は試行錯誤を許容する環境で能力伸長率が高い。'),
    ('高GRIT×長期目標明確校',
     {"trait_grit":">70"},
     {"cult_intensity":">60","cult_structure":">55"},
     'P_grit*0.5 + S_intensity*0.3 + S_structure*0.2',
     {"cognitive":"high","creative_excellence":"medium","market_management":"medium"},
     'Duckworth Grit-S 2007',
     4,
     'GRIT 高い生徒は長期目標を明確に設定できる環境で粘り強さを発揮。'),
    ('高自己調整×自律性中-高校',
     {"trait_self_regulation":">65"},
     {"cult_autonomy":"50-75","cult_mentor":">50"},
     'P_sr*0.5 + S_autonomy*0.3 + S_mentor*0.2',
     {"cognitive":"high","agency_civic":"medium"},
     'Zimmerman SRL 2002',
     3,
     '自己調整学習能力高い生徒は適度な自由とメンターの両方を求める。'),

    # === SDT 動機づけ軸 ===
    ('内発的動機×自律性支援校',
     {"trait_intrinsic_mot":">70","trait_autonomy":">65"},
     {"cult_autonomy":">60","cult_creativity":">55"},
     'P_im*0.5 + P_aut*0.2 + S_autonomy*0.2 + S_creativity*0.1',
     {"cognitive":"high","creative_excellence":"high","wellbeing":"high"},
     'Deci & Ryan SDT 2000',
     5,
     '内発的動機型は自律性支援的な環境で持続的な学習を維持。Deci-Ryan理論の中核。'),
    ('関係性ニーズ×共同体性高校',
     {"trait_relatedness":">70"},
     {"cult_community":">60","cult_mentor":">55"},
     'P_rel*0.5 + S_community*0.3 + S_mentor*0.2',
     {"social_emotional":"high","wellbeing":"high"},
     'Deci & Ryan Basic Psychological Needs',
     4,
     '関係性ニーズが強い生徒は共同体性高い学校で帰属感を得る。家庭的雰囲気の校。'),

    # === Marcia アイデンティティ ===
    ('Identity Moratorium×多様性・自律校',
     {"trait_identity_explore":">70","trait_identity_commit":"<50"},
     {"cult_diversity":">60","cult_autonomy":">60"},
     'P_explore*0.5 + S_diversity*0.3 + S_autonomy*0.2',
     {"cognitive":"high","agency_civic":"medium"},
     'Marcia Identity Status 1966',
     4,
     'Moratorium 期は多様性ある環境で探索を継続できる校が適合。麻布・武蔵型。'),
    ('Identity Achievement×目標明確校',
     {"trait_identity_explore":">60","trait_identity_commit":">70"},
     {"cult_intensity":">55","cult_structure":">50"},
     'P_explore*0.3 + P_commit*0.4 + S_intensity*0.3',
     {"cognitive":"high","market_management":"medium"},
     'Marcia Identity Achievement 1966',
     4,
     '目標と行動が一致した生徒は強度ある学業環境で実績を積む。'),

    # === Lerner Five Cs ===
    ('PYD Caring×精神性高校',
     {"trait_pyd_caring":">75"},
     {"cult_spirituality":">55","cult_community":">55"},
     'P_caring*0.5 + S_spirituality*0.3 + S_community*0.2',
     {"social_emotional":"high","values_morals":"high"},
     'Lerner Five Cs Caring + Sixth C Contribution',
     4,
     '思いやり高い生徒は宗教系・精神性高校で社会貢献力を伸ばす。'),
    ('PYD Confidence×多様性校',
     {"trait_pyd_confidence":">75"},
     {"cult_diversity":">60","cult_internationality":">55"},
     'P_conf*0.5 + S_diversity*0.3 + S_internationality*0.2',
     {"agency_civic":"high","market_management":"medium"},
     'Lerner Five Cs Confidence',
     4,
     '自信高い生徒は多様な環境でリーダーシップを発揮。共学校・国際校型。'),

    # === Hoover-Dempsey 家庭適合 ===
    ('Authoritative家庭×自律性校',
     {"family_style":"authoritative"},
     {"cult_autonomy":">60","cult_mentor":">55"},
     'F_auth*0.6 + S_autonomy*0.2 + S_mentor*0.2',
     {"cognitive":"high","social_emotional":"high","wellbeing":"high"},
     'Hoover-Dempsey & Sandler 2005 + Baumrind',
     5,
     '権威的養育（暖かさ＋構造）の家庭は自律性高い学校と相性最良。長期成果でd=0.42。'),
    ('教育熱心家庭×構造度高校',
     {"family_style":"high_involvement","family_education_oriented":"high"},
     {"cult_structure":">60","cult_intensity":">60"},
     'F_inv*0.5 + S_structure*0.3 + S_intensity*0.2',
     {"cognitive":"high"},
     'Epstein Six Types Learning at Home + Hill & Tyson 2009 (d=0.61)',
     4,
     '家庭学習支援の質が高い家庭は強度高い校で短期成績向上。長期は自律性とのバランス必要。'),

    # === 時代適応性 ===
    ('AI時代の探究志向×AI親和校',
     {"trait_o":">70","trait_growth_mindset":">65"},
     {"cult_creativity":">60","cult_internationality":">55","cult_autonomy":">60"},
     'P_o*0.3 + P_gm*0.3 + S_internationality*0.2 + S_creativity*0.2',
     {"cognitive":"high","creative_excellence":"high","market_management":"medium"},
     'WEF Future of Jobs 2025 + OECD Future of Skills 2030',
     4,
     'AI時代に求められる「人間固有」能力（創造性・批判思考・共感）を伸ばす校との適合。'),
    ('社会変革志向×市民性高校',
     {"trait_pyd_caring":">70","trait_identity_explore":">60"},
     {"cult_diversity":">60","cult_internationality":">55","cult_community":">55"},
     'P_caring*0.3 + P_explore*0.2 + S_diversity*0.25 + S_internationality*0.15 + S_community*0.1',
     {"agency_civic":"high","values_morals":"high"},
     'OECD Transformative Competencies + Lerner Contribution',
     4,
     '2030年代以降の社会変革要請に応える人物像。SDGs・キャリア教育充実校型。'),

    # === ウェルビーイング・心理的安全 ===
    ('高神経症傾向×精神性・共同体校',
     {"trait_n":">65"},
     {"cult_spirituality":">55","cult_community":">60","cult_competition":"<45"},
     'S_spirituality*0.3 + S_community*0.3 + (1-S_competition/100)*0.4',
     {"wellbeing":"high","social_emotional":"medium"},
     'Masten Resilience + Ryff Psychological Wellbeing',
     4,
     '繊細な生徒は宗教系・共同体性高校で心理的安全を確保しつつ成長。'),
    ('高Wellbeing志向×心理安全校',
     {"trait_pyd_connection":">70","trait_relatedness":">65"},
     {"cult_mentor":">60","cult_community":">60","cult_competition":"<55"},
     'P_conn*0.4 + P_rel*0.2 + S_mentor*0.2 + S_community*0.2',
     {"wellbeing":"high","social_emotional":"high"},
     'PERMA Seligman + PISA School Wellbeing',
     5,
     'ウェルビーイング志向はメンター密度・共同体性高い校で長期幸福を実現。'),

    # === 補足ルール ===
    ('国際志向×グローバル教育校',
     {"trait_o":">65","cross_cultural_orientation":"high"},
     {"cult_internationality":">70"},
     'P_o*0.4 + S_internationality*0.6',
     {"cognitive":"high","agency_civic":"high"},
     'Bennett Intercultural Sensitivity 1993 + IB MYP',
     4,
     '異文化志向高い生徒は国際バカロレア校・帰国子女校で能力発揮。'),
    ('体育会系×競争性・共同体校',
     {"trait_e":">65","trait_c":">60","physical_activity":"high"},
     {"cult_competition":">55","cult_community":">60"},
     'P_e*0.3 + P_c*0.3 + S_competition*0.2 + S_community*0.2',
     {"agency_civic":"high","social_emotional":"high"},
     'Lerner PYD Competence + 体育・スポーツ心理学',
     3,
     '体育会系生徒は競争と共同体の両立する環境で成長。スポーツ強豪校型。'),
    ('独立独歩×独立校',
     {"trait_o":">70","trait_e":"<50"},
     {"integration_type":"none","cult_creativity":">55"},
     'P_o*0.4 + (S_creativity)*0.3 + Independence_bonus*0.3',
     {"cognitive":"high","creative_excellence":"high"},
     'Steinberg Adolescent Autonomy + Marcia Moratorium',
     3,
     '独立志向の生徒は付属型でなく独立型校で個性を伸ばす。'),
]


def main():
    db = sqlite3.connect(DB, timeout=600.0)
    db.execute('PRAGMA busy_timeout=600000')

    db.execute("DELETE FROM person_school_fit_rule")  # clear existing
    inserted = 0
    for rule_name, p_pat, s_pat, formula, expected, evidence, conf, rationale in RULES:
        db.execute("""INSERT INTO person_school_fit_rule
            (rule_name, person_trait_pattern, school_culture_pattern,
             fit_score_formula, expected_outcomes, evidence_from, confidence, rationale)
            VALUES (?,?,?,?,?,?,?,?)""",
            (rule_name,
             json.dumps(p_pat, ensure_ascii=False),
             json.dumps(s_pat, ensure_ascii=False),
             formula,
             json.dumps(expected, ensure_ascii=False),
             evidence,
             conf, rationale))
        inserted += 1
    db.commit()
    print(f"Inserted {inserted} fit rules")

    print("\n=== Sample rules ===")
    for r in db.execute("""SELECT rule_name, confidence, evidence_from
        FROM person_school_fit_rule ORDER BY confidence DESC, rule_name LIMIT 10""").fetchall():
        print(f"  [{r[1]}] {r[0]} — {r[2]}")
    db.close()


if __name__ == '__main__':
    main()
