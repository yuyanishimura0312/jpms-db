#!/usr/bin/env python3
"""Seed initial data: era_definition, outcome_cluster_v2, person_trait_dim, person_archetype, school_culture_dim."""
import sqlite3
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

ERAS = [
    ('meiji', '明治', 'Meiji', 1868, 1912, '近代国家形成。立身出世・実学・国民国家。'),
    ('taisho', '大正', 'Taisho', 1912, 1926, '大正デモクラシー。教養主義・自由主義教育。'),
    ('showa_pre', '昭和前期', 'Showa-Early', 1926, 1945, '国家主義・軍国主義教育。'),
    ('showa_post', '昭和後期', 'Showa-Late', 1945, 1989, '高度成長・受験競争・偏差値主義。'),
    ('heisei', '平成', 'Heisei', 1989, 2019, 'バブル崩壊・ゆとり教育・多様化模索。'),
    ('reiwa', '令和', 'Reiwa', 2019, 2030, '令和の日本型学校教育・GIGAスクール・個別最適化。'),
    ('2030s', '2030年代', '2030s', 2030, 2040, 'AGI普及・気候危機対応・人間性再定義。'),
    ('2050s', '2050年代', '2050s', 2050, 2070, '長寿命社会・ポストAGI・地球外活動。'),
]

OUTCOME_CLUSTERS = [
    ('cognitive', '認知・学術', 'Cognitive', '批判的思考・創造性・学際的知識。', 1),
    ('social_emotional', '社会情動', 'Social-Emotional', 'CASEL5要素・PERMA人間関係・PISA友人関係。', 2),
    ('values_morals', '価値観・道徳', 'Values & Morals', 'OECD価値観・道徳倫理・地域貢献・集団協調。', 3),
    ('agency_civic', '主体性・市民性', 'Agency & Civic', 'OECD変革コンピテンシー・社会的自立・協働。', 4),
    ('wellbeing', 'ウェルビーイング', 'Wellbeing', 'PERMA・PISA学校環境・達成意欲。', 5),
    ('creative_excellence', '創造・卓越', 'Creative Excellence', '偉人研究・天才研究・Flow・Domain Mastery。', 6),
    ('market_management', '市場・経営', 'Market & Management', 'リーダーシップ・起業家精神・Effectuation・組織開発。', 7),
]

PERSON_TRAITS = [
    # Big Five (中学生段階測定可能)
    ('trait_o', '開放性', 'Openness', 'BigFive', 'O', None, 11, 'BFI-J', 0.78, 'McCrae & Costa 1992', '新しい体験・知的探求への開放度。'),
    ('trait_c', '誠実性', 'Conscientiousness', 'BigFive', 'C', None, 11, 'BFI-J', 0.81, 'McCrae & Costa 1992', '計画性・自己規律。'),
    ('trait_e', '外向性', 'Extraversion', 'BigFive', 'E', None, 11, 'BFI-J', 0.79, 'McCrae & Costa 1992', '社交性・活動性・刺激希求。'),
    ('trait_a', '協調性', 'Agreeableness', 'BigFive', 'A', None, 11, 'BFI-J', 0.74, 'McCrae & Costa 1992', '他者との協調・利他性。'),
    ('trait_n', '神経症傾向', 'Neuroticism', 'BigFive', 'N', None, 11, 'BFI-J', 0.83, 'McCrae & Costa 1992', '情動反応性・不安。'),
    # Growth & Self-Regulation
    ('trait_growth_mindset', 'グロースマインドセット', 'Growth Mindset', 'Dweck', None, 'mindset', 10, 'MSCI', 0.80, 'Dweck 2006', '能力は努力で伸びるという信念。'),
    ('trait_grit', 'GRIT', 'GRIT', 'Duckworth', None, 'persistence', 12, 'Grit-S', 0.84, 'Duckworth 2007', '長期目標への情熱と忍耐。'),
    ('trait_self_regulation', '自己調整学習', 'Self-Regulated Learning', 'Zimmerman', None, 'meta_cognition', 10, 'SRL-Q', 0.77, 'Zimmerman 2002', '計画-モニタ-評価のメタ認知サイクル。'),
    # Motivation (SDT)
    ('trait_intrinsic_mot', '内発的動機', 'Intrinsic Motivation', 'SDT', None, 'motivation', 10, 'AMS-J', 0.86, 'Deci & Ryan 1985', '内的関心からの行動傾向。'),
    ('trait_autonomy', '自律性', 'Autonomy', 'SDT', None, 'motivation', 10, 'BPNS-J', 0.79, 'Deci & Ryan 2000', '自己決定感。'),
    ('trait_competence', '有能感', 'Competence', 'SDT', None, 'motivation', 10, 'BPNS-J', 0.81, 'Deci & Ryan 2000', '効力感・達成期待。'),
    ('trait_relatedness', '関係性', 'Relatedness', 'SDT', None, 'motivation', 10, 'BPNS-J', 0.78, 'Deci & Ryan 2000', '他者との繋がりの感覚。'),
    # Identity (Marcia)
    ('trait_identity_explore', 'アイデンティティ探求', 'Identity Exploration', 'Marcia', None, 'identity', 12, 'EIPQ', 0.82, 'Marcia 1966', '自己同一性形成のための探索。'),
    ('trait_identity_commit', 'アイデンティティ確約', 'Identity Commitment', 'Marcia', None, 'identity', 12, 'EIPQ', 0.80, 'Marcia 1966', '自己同一性形成のための確約。'),
    # Five Cs (PYD)
    ('trait_pyd_competence', '能力(PYD)', 'PYD Competence', 'Lerner', None, 'pyd', 11, 'PYD-Five-Cs', 0.85, 'Lerner 2005', 'ポジティブな能力認識。'),
    ('trait_pyd_confidence', '自信', 'PYD Confidence', 'Lerner', None, 'pyd', 11, 'PYD-Five-Cs', 0.83, 'Lerner 2005', '自己肯定感。'),
    ('trait_pyd_connection', 'つながり', 'PYD Connection', 'Lerner', None, 'pyd', 11, 'PYD-Five-Cs', 0.82, 'Lerner 2005', '関係性の質。'),
    ('trait_pyd_character', '人格', 'PYD Character', 'Lerner', None, 'pyd', 11, 'PYD-Five-Cs', 0.78, 'Lerner 2005', '倫理性・責任感。'),
    ('trait_pyd_caring', '思いやり', 'PYD Caring', 'Lerner', None, 'pyd', 11, 'PYD-Five-Cs', 0.80, 'Lerner 2005', '共感・利他性。'),
]

PERSON_ARCHETYPES = [
    # 神話アーキタイプ × Big Five パターン
    ('arch_explorer', '探究者', 'Explorer', '{"O": ">75", "C": ">60"}', '知的好奇心が強く、新領域への探求を好む。研究者・学者の若年期典型。', 'MY_archetype_seeker', 0.12),
    ('arch_creator', '創造者', 'Creator', '{"O": ">80", "N": ">55"}', '内的世界が豊かで創作・表現に向かう。芸術家・作家の若年期典型。', 'MY_archetype_artist', 0.08),
    ('arch_leader', 'リーダー型', 'Leader', '{"E": ">70", "C": ">65", "A": "<60"}', '対人影響力と達成志向。経営者・政治家の若年期典型。', 'MY_archetype_ruler', 0.10),
    ('arch_caregiver', '養育者', 'Caregiver', '{"A": ">75", "E": ">55"}', '他者ケア志向。教師・医療専門家・NPO人の若年期典型。', 'MY_archetype_caregiver', 0.15),
    ('arch_warrior', '挑戦者', 'Warrior', '{"E": ">70", "C": ">70", "N": "<40"}', '困難に立ち向かう型。アスリート・起業家の若年期典型。', 'MY_archetype_hero', 0.07),
    ('arch_mediator', '調停者', 'Mediator', '{"A": ">75", "O": ">65"}', '対立調整・価値統合志向。外交官・調停者・コミュニティリーダーの若年期典型。', 'MY_archetype_sage', 0.06),
    ('arch_craftsman', '職人型', 'Craftsman', '{"C": ">80", "O": "40-65"}', '専門技能の磨き上げ志向。技術者・職人・専門家の若年期典型。', 'MY_archetype_creator', 0.12),
    ('arch_introvert_thinker', '内省思索者', 'Introvert Thinker', '{"E": "<40", "O": ">70", "N": ">55"}', '内向的な思索・観察志向。哲学者・研究者の若年期典型。', 'MY_archetype_sage', 0.09),
    ('arch_social_creator', '社交創造者', 'Social Creator', '{"E": ">70", "O": ">75"}', '社交性と創造性の両立。クリエイター・プロデューサーの若年期典型。', 'MY_archetype_creator', 0.06),
    ('arch_steady', '堅実型', 'Steady', '{"C": ">70", "A": ">65", "N": "<45"}', '安定志向の堅実型。専門職・公務員の若年期典型。', 'general', 0.15),
]

SCHOOL_CULTURE_DIMS = [
    ('cult_autonomy', '自律性', 'Autonomy', '規律', '自律', '生徒に与えられる自己決定の度合。', 'カリキュラム選択肢数 / 生徒自治会の活発度 / 校則の柔軟性キーワード'),
    ('cult_structure', '構造度', 'Structure', '緩やか', '明確な構造', 'ルール・カリキュラムの明示性。', '校則文字数 / カリキュラム明示度 / 評価基準明示度'),
    ('cult_diversity', '多様性', 'Diversity', '同質', '多様', '生徒・教育内容の多様性。', '帰国子女比率 / 国際プログラム数 / 進路多様性'),
    ('cult_intensity', '学業強度', 'Academic Intensity', '緩やか', '高強度', '学業負荷・課題量・宿題量。', '授業時間/週 / 課題出題頻度 / 模試頻度'),
    ('cult_mentor', 'メンター密度', 'Mentor Density', '希薄', '濃密', '教員-生徒関係の親密度。', '教員1人あたり生徒数 / 1on1頻度 / 担任体制'),
    ('cult_creativity', '創造性奨励', 'Creativity Encouragement', '抑制的', '奨励的', '創造的活動の奨励度。', '芸術活動時間 / 探究学習時間 / 創作系部活数'),
    ('cult_competition', '競争性', 'Competition', '協調的', '競争的', '校内競争・成績序列の強調度。', '成績順位公表 / 模試順位 / 校内コンペ'),
    ('cult_community', '共同体性', 'Community', '個人主義', '共同体', '学校を共同体として運営する度合。', '行事頻度 / 縦割り活動 / 卒業生ネットワーク'),
    ('cult_internationality', '国際性', 'Internationality', '内向き', '国際志向', '国際的視野・経験の重視度。', '留学プログラム / 海外修学旅行 / 英語授業時間'),
    ('cult_spirituality', '精神性', 'Spirituality', '世俗的', '精神性重視', '宗教的・哲学的内省の重視度。', '宗教科目 / 朝礼瞑想 / 哲学対話'),
]

def main():
    db = sqlite3.connect(DB)
    db.executemany("INSERT OR REPLACE INTO era_definition VALUES (?,?,?,?,?,?)", ERAS)
    db.executemany("INSERT OR REPLACE INTO outcome_cluster_v2 (id, name_ja, name_en, description, display_order) VALUES (?,?,?,?,?)", OUTCOME_CLUSTERS)
    db.executemany("""INSERT OR REPLACE INTO person_trait_dim
        (id, name_ja, name_en, theory_origin, big_five_axis, growth_dimension,
         age_floor, measurement_tool, reliability_score, literature_ref, description)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", PERSON_TRAITS)
    db.executemany("""INSERT OR REPLACE INTO person_archetype
        (id, name_ja, name_en, trait_pattern, description, origin_theory, prevalence_estimate)
        VALUES (?,?,?,?,?,?,?)""", PERSON_ARCHETYPES)
    db.executemany("""INSERT OR REPLACE INTO school_culture_dim
        (id, name_ja, name_en, axis_negative, axis_positive, description, measurement_proxy)
        VALUES (?,?,?,?,?,?,?)""", SCHOOL_CULTURE_DIMS)
    db.commit()

    print(f"era_definition: {db.execute('SELECT COUNT(*) FROM era_definition').fetchone()[0]}")
    print(f"outcome_cluster_v2: {db.execute('SELECT COUNT(*) FROM outcome_cluster_v2').fetchone()[0]}")
    print(f"person_trait_dim: {db.execute('SELECT COUNT(*) FROM person_trait_dim').fetchone()[0]}")
    print(f"person_archetype: {db.execute('SELECT COUNT(*) FROM person_archetype').fetchone()[0]}")
    print(f"school_culture_dim: {db.execute('SELECT COUNT(*) FROM school_culture_dim').fetchone()[0]}")
    db.close()

if __name__ == '__main__':
    main()
