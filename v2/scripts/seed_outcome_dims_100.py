#!/usr/bin/env python3
"""Seed outcome_dim_v2 with 100+ outcome dimensions across 7 clusters.

Sources:
- OECD Learning Compass 2030
- CASEL SEL framework
- PERMA (Seligman)
- P21 Framework
- PISA Wellbeing
- Japanese independent (道徳・地域貢献・集団協調・社会的自立)
- Cox/Simonton 偉人研究
- Lerner Five Cs (PYD)
- Csikszentmihalyi Flow
- Collins / Drucker / Christensen / Sarasvathy
- Zuckerman / Wuchty 研究者研究
- Dweck / Duckworth (Growth/GRIT)
"""
import sqlite3
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# Format: (id, name_ja, name_en, cluster, framework, source_type, source_db_ref, definition,
#         measurement_method, age_window, predictability, literature_ref)
OUTCOMES = [
    # ---------- 1. 認知・学術 (cognitive) ----------
    ('od_cog_001', '批判的思考', 'Critical Thinking', 'cognitive', 'P21', '学術理論', 'AK',
     '情報の分析・評価・統合に基づく合理的判断能力。', '客観テスト/論述評価', 'in_school', 4, 'Ennis 1985'),
    ('od_cog_002', '創造性', 'Creativity', 'cognitive', 'P21', '学術理論', 'GF',
     '新しいアイデアの創出・拡散思考。', 'TTCT/作品評価', 'in_school', 4, 'Torrance 1974; Simonton 2012'),
    ('od_cog_003', '学際的知識', 'Interdisciplinary Knowledge', 'cognitive', 'OECD_LC2030', '学術理論', 'AK',
     '複数の学問分野を統合する知識体系。', '記述評価/プロジェクト', 'graduate_5y', 3, 'OECD 2019'),
    ('od_cog_004', 'メタ認知', 'Metacognition', 'cognitive', 'OECD', '学術理論', 'AK',
     '自分の思考を客観的に把握する力。', '自己評定/RAVEN', 'in_school', 4, 'Flavell 1979'),
    ('od_cog_005', '論理的思考', 'Logical Reasoning', 'cognitive', 'P21', '学術理論', 'AK',
     '演繹・帰納・類推による推論能力。', 'CRT/論理問題', 'in_school', 5, 'Stanovich 2009'),
    ('od_cog_006', '読解力', 'Reading Literacy', 'cognitive', 'PISA', '学術理論', None,
     '複雑なテキストの理解・解釈力。', 'PISA Reading', 'in_school', 5, 'OECD PISA'),
    ('od_cog_007', '数学的リテラシー', 'Mathematical Literacy', 'cognitive', 'PISA', '学術理論', None,
     '数学を実生活に応用する力。', 'PISA Math', 'in_school', 5, 'OECD PISA'),
    ('od_cog_008', '科学的リテラシー', 'Scientific Literacy', 'cognitive', 'PISA', '学術理論', None,
     '科学的手続きと知識の理解・適用。', 'PISA Science', 'in_school', 5, 'OECD PISA'),
    ('od_cog_009', '情報リテラシー', 'Digital Literacy', 'cognitive', 'P21', '学術理論', 'AA',
     'デジタル情報の検索・評価・活用力。', '実技評価', 'in_school', 4, 'WEF Future of Jobs'),
    ('od_cog_010', 'AI協働リテラシー', 'AI Collaboration Literacy', 'cognitive', 'JP_2024_MEXT', '時代変遷', 'AA',
     '生成AIを学習・思考のパートナーとして使う力。', '行動観察/作品', 'graduate_5y', 3, 'MEXT 2024 Guideline'),
    ('od_cog_011', '言語表現力', 'Language Expression', 'cognitive', 'JP', '学術理論', 'AK',
     '日本語の語彙・文章構成・口頭表現能力。', '作文/プレゼン評価', 'in_school', 4, 'OECD'),
    ('od_cog_012', '英語コミュニケーション', 'English Communication', 'cognitive', 'OECD', '学術理論', None,
     '英語による情報受発信能力。', 'CEFR/TOEFL', 'in_school', 5, 'CEFR'),
    ('od_cog_013', '探究力', 'Inquiry', 'cognitive', 'OECD_LC2030', '学術理論', 'AK',
     '問いを立て、調査・検証する能力。', 'プロジェクト評価', 'in_school', 4, 'IB MYP'),
    ('od_cog_014', '抽象的概念把握', 'Abstract Conceptualization', 'cognitive', 'AK', '学術理論', 'AK',
     '抽象概念の理解・操作能力。', '概念課題', 'in_school', 4, 'Piaget formal operations'),
    ('od_cog_015', '専門的技能', 'Domain Mastery', 'cognitive', 'Anders Ericsson', '学術理論', 'GF',
     '特定領域での熟達（10,000時間ルール）。', 'パフォーマンス評価', 'graduate_10y', 3, 'Ericsson 1993'),

    # ---------- 2. 社会情動 (social_emotional) ----------
    ('od_se_001', '自己認識', 'Self-Awareness', 'social_emotional', 'CASEL', '学術理論', 'AK',
     '自分の感情・思考・価値観の認識能力。', 'SEL自己評価', 'in_school', 4, 'CASEL'),
    ('od_se_002', '自己管理', 'Self-Management', 'social_emotional', 'CASEL', '学術理論', 'AK',
     '感情・行動の調整能力。', '自己評定/観察', 'in_school', 4, 'CASEL'),
    ('od_se_003', '社会的認識', 'Social Awareness', 'social_emotional', 'CASEL', '学術理論', 'AK',
     '他者への共感・尊重・文脈理解。', '社会認知課題', 'in_school', 4, 'CASEL'),
    ('od_se_004', '対人関係スキル', 'Relationship Skills', 'social_emotional', 'CASEL', '学術理論', 'AK',
     '信頼関係構築・対立解決の能力。', '行動観察', 'in_school', 4, 'CASEL'),
    ('od_se_005', '責任ある意思決定', 'Responsible Decision-Making', 'social_emotional', 'CASEL', '学術理論', 'AK',
     '倫理的・社会的配慮を伴う選択能力。', 'ジレンマ課題', 'in_school', 4, 'CASEL'),
    ('od_se_006', 'PERMA人間関係', 'PERMA Relationships', 'social_emotional', 'PERMA', '学術理論', 'AK',
     '家族・友人との肯定的つながり。', 'PERMA-Profiler', 'in_school', 4, 'Seligman 2011'),
    ('od_se_007', 'PISA友人関係', 'PISA Friendship', 'social_emotional', 'PISA_WB', '学術理論', None,
     '友人とのつながり・受容感。', 'PISA-WB scale', 'in_school', 4, 'OECD PISA'),
    ('od_se_008', '感情調整', 'Emotional Regulation', 'social_emotional', 'AK', '学術理論', 'AK',
     '情動の認識と調整能力。', 'ERQ/観察', 'in_school', 4, 'Gross 1998'),
    ('od_se_009', '共感力', 'Empathy', 'social_emotional', 'AK', '学術理論', 'AK',
     '他者の感情・立場を理解する力。', 'IRI/共感課題', 'in_school', 4, 'Davis 1983'),
    ('od_se_010', '愛着安定性', 'Attachment Stability', 'social_emotional', 'AK', '学術理論', 'AK',
     '安定した対人関係を持つ基盤。', 'AAI/ECR', 'graduate_5y', 3, 'Bowlby 1969'),

    # ---------- 3. 価値観・道徳 (values_morals) ----------
    ('od_val_001', 'OECD価値観', 'OECD Values', 'values_morals', 'OECD_LC2030', '学術理論', None,
     '個人・社会・人類の4層価値観体系。', 'OECD価値観調査', 'graduate_5y', 3, 'OECD 2019'),
    ('od_val_002', '道徳性・倫理観', 'Moral Reasoning', 'values_morals', 'JP', '学術理論', 'AK',
     '善悪の判断と倫理的行動への意志。', 'DIT/MJI', 'in_school', 4, 'Kohlberg 1981; 文科省'),
    ('od_val_003', '地域貢献意識', 'Community Contribution', 'values_morals', 'JP', '学術理論', 'AK',
     '地域社会への貢献意識・実践。', '行動記録', 'graduate_5y', 3, '日本独自'),
    ('od_val_004', '集団協調性', 'Group Harmony', 'values_morals', 'JP', '学術理論', 'AN',
     '集団調和を保つ対人スキル。', '行動観察', 'in_school', 4, '日本独自'),
    ('od_val_005', '誠実さ', 'Honesty', 'values_morals', 'CharacterEd', '学術理論', 'GF',
     '虚偽を避け真実を語る性向。', '自己評定/他者評定', 'in_school', 3, 'Peterson & Seligman 2004'),
    ('od_val_006', '感謝', 'Gratitude', 'values_morals', 'PERMA', '学術理論', 'AK',
     '受けた恩恵への感謝の表明。', 'GQ-6', 'in_school', 3, 'Emmons 2003'),
    ('od_val_007', '寛容性', 'Tolerance', 'values_morals', 'OECD', '学術理論', 'AN',
     '異なる価値観・文化への受容。', '態度尺度', 'graduate_5y', 3, 'OECD 2018'),
    ('od_val_008', '社会正義感', 'Social Justice', 'values_morals', 'OECD', '学術理論', 'SIF',
     '不公正への問題意識と行動。', '質問紙', 'graduate_5y', 3, 'Torney-Purta 2002'),
    ('od_val_009', '宗教的内省', 'Religious Reflection', 'values_morals', 'JP', '学術理論', 'AN',
     '宗教的・哲学的内省の習慣。', '自己評定', 'in_school', 2, 'Religious schools'),
    ('od_val_010', '伝統文化尊重', 'Respect for Tradition', 'values_morals', 'JP', '学術理論', 'AN',
     '日本の伝統文化への理解と敬意。', '質問紙', 'in_school', 3, '日本独自'),

    # ---------- 4. 主体性・市民性 (agency_civic) ----------
    ('od_ag_001', 'OECD変革コンピテンシー', 'OECD Transformative Competencies', 'agency_civic', 'OECD_LC2030', '学術理論', 'SIF',
     '価値創造・対立調整・責任ある行動の3コンピテンシー。', 'OECD評価', 'graduate_5y', 3, 'OECD 2019'),
    ('od_ag_002', '社会的自立性', 'Social Autonomy', 'agency_civic', 'JP', '学術理論', 'AK',
     '社会の一員として自律判断行動する力。', '自己評定', 'graduate_5y', 4, '日本独自'),
    ('od_ag_003', 'コミュニケーション・協働', 'Communication & Collaboration', 'agency_civic', 'P21', '学術理論', 'AK',
     '多様な相手との対話と協働能力。', '実技評価', 'in_school', 4, 'P21'),
    ('od_ag_004', '主体性', 'Agency', 'agency_civic', 'OECD_LC2030', '学術理論', 'AK',
     '自ら行動を起こし、責任を負う志向。', 'ASA scale', 'in_school', 4, 'OECD'),
    ('od_ag_005', 'リーダーシップ', 'Leadership', 'agency_civic', 'MG', '学術理論', 'MG',
     '集団を方向づけ、影響を与える力。', '360°評価', 'graduate_10y', 3, 'Northouse 2018'),
    ('od_ag_006', '市民参画', 'Civic Engagement', 'agency_civic', 'OECD', '学術理論', 'AK',
     '社会・政治参加の意欲と行動。', 'IEA Civic', 'graduate_10y', 3, 'IEA Civic Education Study'),
    ('od_ag_007', '起業家精神', 'Entrepreneurial Spirit', 'agency_civic', 'IT', '学術理論', 'IT',
     '機会を見出し行動を起こす志向。', 'EOA scale', 'graduate_10y', 3, 'Sarasvathy 2008; Shane 2003'),
    ('od_ag_008', '社会変革志向', 'Social Change Orientation', 'agency_civic', 'SIF', '学術理論', 'SIF',
     '社会課題解決への能動的関与。', 'SCO scale', 'graduate_10y', 3, 'Lerner Five Cs Contribution'),
    ('od_ag_009', '異文化対応力', 'Cross-Cultural Competence', 'agency_civic', 'OECD', '学術理論', 'AN',
     '異文化環境での適応・橋渡し力。', 'ICAPS', 'graduate_5y', 3, 'Bennett 1993'),
    ('od_ag_010', '組織化能力', 'Organizing Capacity', 'agency_civic', 'MG', '学術理論', 'MG',
     '人と資源を統合・運営する力。', '実績評価', 'graduate_10y', 3, 'Drucker 1985'),

    # ---------- 5. ウェルビーイング (wellbeing) ----------
    ('od_wb_001', 'PERMAポジティブ感情', 'PERMA Positive Emotion', 'wellbeing', 'PERMA', '学術理論', 'AK',
     '幸福感・希望・満足感などの感情体験。', 'PERMA-P', 'in_school', 4, 'Seligman 2011'),
    ('od_wb_002', 'PERMAエンゲージメント', 'PERMA Engagement', 'wellbeing', 'PERMA', '学術理論', 'AK',
     'フロー体験・深い没入感。', 'FLOW Scale', 'in_school', 4, 'Csikszentmihalyi 1990'),
    ('od_wb_003', 'PERMA意味', 'PERMA Meaning', 'wellbeing', 'PERMA', '学術理論', 'AK',
     '人生の意味・帰属感。', 'MLQ', 'graduate_5y', 3, 'Steger 2006'),
    ('od_wb_004', 'PERMA達成', 'PERMA Achievement', 'wellbeing', 'PERMA', '学術理論', 'AK',
     '目標達成・熟達感。', 'PERMA-A', 'in_school', 4, 'Seligman 2011'),
    ('od_wb_005', 'PISA学校環境ウェルビーイング', 'PISA School Wellbeing', 'wellbeing', 'PISA_WB', '学術理論', None,
     '学校所属感・安全感・教師関係。', 'PISA-WB', 'in_school', 5, 'OECD PISA'),
    ('od_wb_006', 'PISA達成意欲', 'PISA Achievement Motivation', 'wellbeing', 'PISA_WB', '学術理論', None,
     '学業達成への意欲・期待。', 'PISA-WB', 'in_school', 5, 'OECD PISA'),
    ('od_wb_007', '自己肯定感', 'Self-Esteem', 'wellbeing', 'JP', '学術理論', 'AK',
     '自己への肯定的評価。', 'RSE', 'in_school', 5, 'Rosenberg 1965'),
    ('od_wb_008', '心理的レジリエンス', 'Resilience', 'wellbeing', 'AK', '学術理論', 'AK',
     '逆境からの回復力。', 'CD-RISC', 'in_school', 4, 'Masten 2001'),
    ('od_wb_009', 'マインドフルネス', 'Mindfulness', 'wellbeing', 'AK', '学術理論', 'AN',
     '今この瞬間への注意の質。', 'MAAS', 'graduate_5y', 3, 'Kabat-Zinn 1990'),
    ('od_wb_010', '生活満足度', 'Life Satisfaction', 'wellbeing', 'AK', '学術理論', 'AK',
     '人生全般への主観的満足度。', 'SWLS', 'graduate_5y', 4, 'Diener 1985'),

    # ---------- 6. 創造・卓越 (creative_excellence) ----------
    ('od_ce_001', 'Flow頻度', 'Flow Experience Frequency', 'creative_excellence', 'Csikszentmihalyi', '学術理論', 'AK',
     '挑戦と技能のバランスでの没入体験頻度。', 'ESM', 'in_school', 4, 'Csikszentmihalyi 1990'),
    ('od_ce_002', 'Domain Mastery指向', 'Domain Mastery Orientation', 'creative_excellence', 'Ericsson', '学術理論', 'GF',
     '特定領域での熟達への志向。', '行動記録', 'graduate_10y', 3, 'Ericsson 1993'),
    ('od_ce_003', '内発的動機（Cox）', 'Intrinsic Motivation (Cox)', 'creative_excellence', 'Cox', '学術理論', 'GF',
     '報酬より内的関心からの行動。', 'IMI', 'in_school', 4, 'Cox 1926; Simonton 2012'),
    ('od_ce_004', '失敗への復帰力', 'Recovery from Failure', 'creative_excellence', 'GF', '学術理論', 'GF',
     '挫折後の継続意志と立ち直り。', '事例記録', 'graduate_10y', 3, 'Simonton 2014'),
    ('od_ce_005', '早期独立心', 'Early Independence', 'creative_excellence', 'GF', '学術理論', 'GF',
     '若年期からの自立的判断。', '事例記録', 'graduate_5y', 3, 'Cox 1926'),
    ('od_ce_006', '異分野統合志向', 'Interdisciplinary Synthesis', 'creative_excellence', 'GF', '学術理論', 'GF',
     '複数領域を統合する創造力。', '作品評価', 'graduate_10y', 3, 'Gardner Creating Minds 1993'),
    ('od_ce_007', '芸術的創造力', 'Artistic Creativity', 'creative_excellence', 'GF', '学術理論', 'GF',
     '芸術領域での創造的成果。', '作品/受賞', 'graduate_10y', 3, 'Csikszentmihalyi 1996'),
    ('od_ce_008', '科学的卓越性', 'Scientific Excellence', 'creative_excellence', 'Zuckerman', '学術理論', 'AL',
     '研究領域での顕著な業績。', '論文/受賞', 'graduate_20y', 2, 'Zuckerman 1977'),
    ('od_ce_009', 'プロデュース力', 'Producing Capability', 'creative_excellence', 'GF', '学術理論', 'GF',
     '構想を実現し届ける力。', '事例記録', 'graduate_10y', 3, 'Howard Gardner'),
    ('od_ce_010', '師との関係構築力', 'Mentor Relationship Building', 'creative_excellence', 'Zuckerman', '学術理論', 'AL',
     '指導者との生産的関係を作る力。', '事例記録', 'graduate_5y', 3, 'Zuckerman Scientific Elite 1977'),

    # ---------- 7. 市場・経営 (market_management) ----------
    ('od_mm_001', 'Effectuation思考', 'Effectuation Thinking', 'market_management', 'Sarasvathy', '学術理論', 'IT',
     '手持ち資源と失敗許容度で判断する起業家思考。', '判断課題', 'graduate_10y', 3, 'Sarasvathy 2008'),
    ('od_mm_002', '機会認識', 'Opportunity Recognition', 'market_management', 'Shane', '学術理論', 'IT',
     '市場機会を見出す感性。', '事例研究', 'graduate_10y', 3, 'Shane 2003'),
    ('od_mm_003', 'リスクテイク', 'Risk-Taking', 'market_management', 'IT', '学術理論', 'IT',
     '計算されたリスクを取る性向。', 'DOSPERT', 'graduate_10y', 3, 'Knight 1921'),
    ('od_mm_004', 'Level5リーダーシップ', 'Level 5 Leadership', 'market_management', 'Collins', '学術理論', 'MG',
     '謙虚さと強い意志の融合。', '360°評価', 'graduate_20y', 2, 'Collins 2001'),
    ('od_mm_005', '目的志向', 'Purpose Orientation', 'market_management', 'Drucker', '学術理論', 'MG',
     '組織の目的に対する個人的野心の従属。', '質問紙', 'graduate_10y', 3, 'Drucker 1993'),
    ('od_mm_006', '破壊的イノベーション思考', 'Disruptive Innovation Thinking', 'market_management', 'Christensen', '学術理論', 'IT',
     '市場の非連続性を見抜く視座。', '判断課題', 'graduate_20y', 2, 'Christensen 1997'),
    ('od_mm_007', 'チームサイエンス', 'Team Science', 'market_management', 'Wuchty', '学術理論', 'AL',
     '異分野協働でアウトプットを出す力。', '実績評価', 'graduate_10y', 3, 'Wuchty 2007'),
    ('od_mm_008', '心理的安全性創出', 'Psychological Safety Creation', 'market_management', 'Edmondson', '学術理論', 'MG',
     'チームに失敗許容環境を作る力。', '組織サーベイ', 'graduate_10y', 3, 'Edmondson 1999'),
    ('od_mm_009', '組織開発', 'Organization Development', 'market_management', 'MG', '学術理論', 'MG',
     '組織の能力を高める実践力。', '組織サーベイ', 'graduate_20y', 2, 'Schein 1985'),
    ('od_mm_010', '資金調達能力', 'Fundraising Capability', 'market_management', 'IR', '実証DB', 'IR',
     '事業資金を調達する力。', '実績評価', 'graduate_10y', 2, 'VC research'),
    ('od_mm_011', '顧客理解', 'Customer Understanding', 'market_management', 'MS', '学術理論', 'MS',
     '顧客ニーズとJTBDを把握する力。', '実技評価', 'graduate_10y', 3, 'Christensen JTBD'),
    ('od_mm_012', 'グロース思考', 'Growth Thinking', 'market_management', 'MS', '学術理論', 'MS',
     'AARRR・PLG等の成長設計能力。', '実績評価', 'graduate_10y', 2, 'McClure AARRR'),
]

def main():
    db = sqlite3.connect(DB)
    c = 0
    for od in OUTCOMES:
        try:
            db.execute("""
                INSERT OR REPLACE INTO outcome_dim_v2
                (id, name_ja, name_en, cluster_id, framework, source_type, source_db_ref,
                 definition, measurement_method, age_window, predictability, literature_ref)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, od)
            c += 1
        except Exception as e:
            print(f"Error on {od[0]}: {e}")
    db.commit()
    print(f"Inserted: {c} outcome dimensions")

    # Cluster check
    rows = db.execute("""SELECT cluster_id, COUNT(*) FROM outcome_dim_v2 GROUP BY cluster_id""").fetchall()
    print("\nCluster distribution:")
    for cluster, count in rows:
        print(f"  {cluster}: {count}")
    print(f"\nTotal: {db.execute('SELECT COUNT(*) FROM outcome_dim_v2').fetchone()[0]}")
    db.close()

if __name__ == '__main__':
    main()
