#!/usr/bin/env python3
"""Seed era_required_traits and outcome_era_relevance based on FK/MT/FS/CLA/AA/AD knowledge."""
import sqlite3
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# era × outcome dimensions の関連度（FK/MT/CLA/AA/AD ベース）
# 1-10 で評価。低い = 当時重視されなかった、高い = 当時もしくは将来重視される
ERA_OUTCOME_RELEVANCE = [
    # ---- meiji（1868-1912）: 立身出世・実学・国民国家
    ('meiji', 'od_cog_001', 6, '批判的思考は限定的', 'CLA_meiji'),
    ('meiji', 'od_cog_005', 9, '論理的思考＝近代化のエンジン', 'CLA_meiji'),
    ('meiji', 'od_val_010', 10, '伝統文化尊重と国家統合', 'CLA_meiji'),
    ('meiji', 'od_ag_002', 7, '殖産興業の社会的自立', 'CLA_meiji'),
    ('meiji', 'od_se_004', 5, '対人スキルは家制度内', 'CLA_meiji'),
    ('meiji', 'od_ce_005', 9, '早期独立心は近代家族論', 'CLA_meiji'),

    # ---- taisho（1912-1926）: 大正デモクラシー・教養主義
    ('taisho', 'od_cog_002', 9, '教養主義における創造性', 'CLA_taisho'),
    ('taisho', 'od_val_007', 7, '自由主義・寛容性', 'CLA_taisho'),
    ('taisho', 'od_ag_006', 8, '市民参画思想', 'CLA_taisho'),

    # ---- showa_pre（1926-1945）: 国家主義・軍国主義
    ('showa_pre', 'od_val_001', 4, '画一的価値観', 'CLA_showa_pre'),
    ('showa_pre', 'od_val_004', 10, '集団協調性の極端化', 'CLA_showa_pre'),
    ('showa_pre', 'od_ce_002', 6, '熟練重視', 'CLA_showa_pre'),

    # ---- showa_post（1945-1989）: 高度成長・受験競争・偏差値主義
    ('showa_post', 'od_cog_005', 10, '受験競争で論理思考重視', 'CLA_showa_post'),
    ('showa_post', 'od_cog_007', 10, '数学リテラシー＝経済成長', 'CLA_showa_post'),
    ('showa_post', 'od_se_004', 6, '会社共同体の対人スキル', 'CLA_showa_post'),
    ('showa_post', 'od_val_004', 9, '集団主義的協調', 'CLA_showa_post'),
    ('showa_post', 'od_mm_004', 8, 'Level 5 Leadership 萌芽', 'CLA_showa_post'),

    # ---- heisei（1989-2019）: バブル崩壊・ゆとり・多様化
    ('heisei', 'od_cog_001', 8, '生きる力＝批判的思考', 'CLA_heisei'),
    ('heisei', 'od_cog_002', 7, '創造性教育の模索', 'CLA_heisei'),
    ('heisei', 'od_se_001', 7, 'SEL導入', 'CLA_heisei'),
    ('heisei', 'od_ag_003', 8, '協働学習', 'CLA_heisei'),
    ('heisei', 'od_wb_007', 7, '自己肯定感問題化', 'CLA_heisei'),
    ('heisei', 'od_mm_002', 7, 'IT革命と機会認識', 'CLA_heisei'),

    # ---- reiwa（2019-2030）: 個別最適化・GIGA・令和型学校
    ('reiwa', 'od_cog_001', 10, 'AI時代の批判的思考', 'MEXT_reiwa'),
    ('reiwa', 'od_cog_002', 10, '個別最適化×協働的学び', 'MEXT_reiwa'),
    ('reiwa', 'od_cog_009', 10, 'GIGAスクール', 'MEXT_reiwa'),
    ('reiwa', 'od_cog_010', 9, '生成AI協働', 'MEXT_2024'),
    ('reiwa', 'od_se_002', 8, 'SEL本格導入', 'MEXT_reiwa'),
    ('reiwa', 'od_wb_005', 9, 'ウェルビーイング基本方針', '第4期教育振興'),
    ('reiwa', 'od_ag_001', 9, '変革コンピテンシー', 'OECD_2030'),
    ('reiwa', 'od_ag_002', 10, '社会の創り手', '第4期教育振興'),
    ('reiwa', 'od_ag_007', 8, '起業家精神育成', 'METI'),
    ('reiwa', 'od_val_007', 9, '多様性理解', '令和の日本型学校'),
    ('reiwa', 'od_mm_011', 7, '顧客理解（探究学習）', None),

    # ---- 2030s: AGI普及・気候危機対応・人間性再定義
    ('2030s', 'od_cog_010', 10, 'AI協働必須', 'AA_AD'),
    ('2030s', 'od_cog_002', 10, 'AI時代の創造性', 'WEF_2025'),
    ('2030s', 'od_ag_001', 10, '変革コンピテンシー必須', 'OECD_2030'),
    ('2030s', 'od_se_009', 9, '共感力＝人間固有', 'AA'),
    ('2030s', 'od_wb_008', 9, 'レジリエンス必須', 'WEF_2025'),
    ('2030s', 'od_ag_007', 9, '起業家精神＝AI時代', 'IT_AD'),
    ('2030s', 'od_ce_006', 9, '学際的統合志向', 'OECD'),
    ('2030s', 'od_mm_001', 8, 'Effectuation必須', 'IT'),
    ('2030s', 'od_val_002', 8, 'AI時代の倫理判断', 'AD'),
    ('2030s', 'od_wb_009', 8, 'マインドフルネス需要', 'AN'),

    # ---- 2050s: 長寿命社会・ポストAGI・地球外活動
    ('2050s', 'od_ag_008', 10, '社会変革志向', 'SIF_FK'),
    ('2050s', 'od_se_010', 9, '愛着安定性＝長寿命', 'AK'),
    ('2050s', 'od_ce_006', 10, '学際統合の極致', 'FS'),
    ('2050s', 'od_wb_003', 10, 'PERMA意味追求', 'FK'),
    ('2050s', 'od_val_007', 10, '寛容性＝多様性社会', 'OECD'),
    ('2050s', 'od_mm_006', 9, '破壊的イノベーション継続', 'IT'),
]

ERA_REQUIRED_TRAITS = [
    # era_id, outcome_dim_id (or trait_dim_id), weight, reasoning, source_ref
    ('reiwa', 'od_cog_010', None, 0.9, '令和の日本型学校教育のAI協働', 'MEXT_2024'),
    ('reiwa', 'od_ag_002', None, 1.0, '第4期計画の基本方針「持続可能な社会の創り手」', '第4期教育振興'),
    ('2030s', 'od_cog_010', None, 1.0, 'AI協働は2030必須スキル', 'WEF_2025'),
    ('2030s', 'od_ag_001', None, 1.0, '変革コンピテンシー', 'OECD_2030'),
    ('2030s', 'od_wb_008', None, 0.9, 'レジリエンス・柔軟性', 'WEF_2025'),
    ('2050s', 'od_ag_008', None, 1.0, '社会変革志向の中心化', 'SIF_FK'),
]

def main():
    db = sqlite3.connect(DB)
    c = 0
    for era, dim, rel, reason, src in ERA_OUTCOME_RELEVANCE:
        try:
            db.execute("""INSERT INTO outcome_era_relevance
                (outcome_dim_id, era, relevance, reasoning, source_ref)
                VALUES (?,?,?,?,?)""", (dim, era, rel, reason, src))
            c += 1
        except Exception as e:
            print(f"Error {era}/{dim}: {e}")
    print(f"outcome_era_relevance: {c}")

    c2 = 0
    for era, outcome_id, trait_id, weight, reason, src in ERA_REQUIRED_TRAITS:
        try:
            db.execute("""INSERT INTO era_required_traits
                (era_id, outcome_dim_id, trait_dim_id, weight, reasoning, source_ref)
                VALUES (?,?,?,?,?,?)""", (era, outcome_id, trait_id, weight, reason, src))
            c2 += 1
        except Exception as e:
            print(f"Error {era}: {e}")
    print(f"era_required_traits: {c2}")

    db.commit()
    db.close()

if __name__ == '__main__':
    main()
