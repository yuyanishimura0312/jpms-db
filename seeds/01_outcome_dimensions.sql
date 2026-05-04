-- JPMS-DB 成果次元シード（25項目）
-- frameworkごとに OECD_LC2030 / CASEL / PERMA / PISA_WB / P21 / japanese_independent

INSERT INTO jpms_sources (id, source_type, title, author, url, accessed_at, publication_year, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_000001','academic_paper','OECD Learning Compass 2030 Concept Note','OECD','https://www.oecd.org/education/2030-project/teaching-and-learning/learning/learning-compass-2030/',datetime('now'),2019,'cc_by','primary',95,'OECD Future of Education and Skills 2030'),
('jpms_src_000002','academic_paper','CASEL SEL Framework','CASEL','https://casel.org/casel-sel-framework-11-2020/',datetime('now'),2020,'copyrighted_quotable','primary',95,'5コアコンピテンシー枠組み'),
('jpms_src_000003','academic_book','Flourish: A Visionary New Understanding of Happiness and Well-Being','Martin E. P. Seligman','https://www.simonandschuster.com/books/Flourish/Martin-E-P-Seligman/9781439190760',datetime('now'),2011,'copyrighted_quotable','primary',92,'PERMAモデル原典'),
('jpms_src_000004','academic_paper','PISA Happy Life Dashboard','OECD','https://gpseducation.oecd.org/',datetime('now'),2024,'cc_by','primary',95,'9次元のwell-being指標'),
('jpms_src_000005','academic_paper','P21 Framework for 21st Century Learning','Partnership for 21st Century Learning','https://www.battelleforkids.org/networks/p21/frameworks-resources',datetime('now'),2019,'copyrighted_quotable','primary',88,'P21枠組み'),
('jpms_src_000006','academic_book','こども大綱・こどものWell-being指標','こども家庭庁','https://www.cfa.go.jp/',datetime('now'),2024,'public_domain','primary',95,'日本のこども関連指標');

-- ============================================
-- OECD Learning Compass 2030 (5次元)
-- ============================================
INSERT INTO jpms_outcome_dimensions (id, name_ja, name_en, definition, framework, measurement_approach, measurability, relevance_age, source_id) VALUES
('jpms_od_001','学際的知識','Knowledge (disciplinary, interdisciplinary, epistemic, procedural)','学術的・学際的・認識論的・手続的の4種を統合した知識体系。OECD Learning Compass 2030において、コンピテンシー発揮の基盤として位置づけられる。','OECD_LC2030','学力テスト・PISA・教科横断課題','quantitative','12-22','jpms_src_000001'),
('jpms_od_002','スキル（認知・メタ認知・社会情動・実用）','Skills (cognitive, metacognitive, social-emotional, practical)','認知スキル・メタ認知スキル・社会情動スキル・実用スキルの4分類で構成される。OECD Learning Compass 2030の中核要素。','OECD_LC2030','認知課題・自己評価・観察評価','mixed','12-22','jpms_src_000001'),
('jpms_od_003','学びへの態度','Attitudes','学習に対する開放性・粘り強さ・成長指向の態度。新しい知識への開放性と挑戦への意欲を含む。','OECD_LC2030','質問紙・行動観察','qualitative','12-22','jpms_src_000001'),
('jpms_od_004','価値観','Values (personal, social, societal, human)','個人的・社会的・社会全体的・人類的の4層で構成される価値観体系。倫理的判断の基盤を成す。','OECD_LC2030','質問紙・対話評価','conceptual','12-22','jpms_src_000001'),
('jpms_od_005','変革コンピテンシー','Transformative Competencies','価値創造・対立とジレンマの調整・責任ある行動の3コンピテンシー。21世紀の課題への対応力。','OECD_LC2030','プロジェクト評価・実践記録','mixed','15-22','jpms_src_000001');

-- ============================================
-- CASEL 5コアコンピテンシー
-- ============================================
INSERT INTO jpms_outcome_dimensions (id, name_ja, name_en, definition, framework, measurement_approach, measurability, relevance_age, source_id) VALUES
('jpms_od_006','自己認識','Self-Awareness','自分の感情・思考・価値観・強み・弱みを正確に認識する能力。情動調整と意思決定の基盤。','CASEL','SEL自己評価尺度・観察','mixed','12-18','jpms_src_000002'),
('jpms_od_007','自己管理','Self-Management','感情・思考・行動を効果的に調整し、目標達成のための自己制御を行う能力。ストレス管理・衝動抑制を含む。','CASEL','SEL自己評価・行動観察','mixed','12-18','jpms_src_000002'),
('jpms_od_008','社会的認識','Social Awareness','多様な背景を持つ他者への共感・理解・尊重。社会規範への認識と行動の文脈化。','CASEL','SEL自己評価・対人課題','mixed','12-18','jpms_src_000002'),
('jpms_od_009','対人関係スキル','Relationship Skills','信頼に基づく関係の構築・維持。コミュニケーション・協働・対立解決の能力。','CASEL','SEL自己評価・グループ課題','mixed','12-18','jpms_src_000002'),
('jpms_od_010','責任ある意思決定','Responsible Decision-Making','倫理的・社会的・状況的な配慮に基づく建設的な選択を行う能力。','CASEL','シナリオ判断課題','mixed','12-18','jpms_src_000002');

-- ============================================
-- PERMA (5次元)
-- ============================================
INSERT INTO jpms_outcome_dimensions (id, name_ja, name_en, definition, framework, measurement_approach, measurability, relevance_age, source_id) VALUES
('jpms_od_011','ポジティブ感情','Positive Emotion','幸福感・希望・満足感・感謝・愛情等のポジティブな感情体験。Seligmanのウェルビーイングの第一柱。','PERMA','PERMA Profiler・主観的幸福感尺度','qualitative','12-22','jpms_src_000003'),
('jpms_od_012','エンゲージメント','Engagement','活動への深い没入とフロー体験。集中と充実感の指標。','PERMA','フロー尺度・自己評価','qualitative','12-22','jpms_src_000003'),
('jpms_od_013','人間関係','Relationships','家族・友人・コミュニティとの肯定的なつながり。社会的支援の質と量。','PERMA','社会的ネットワーク評価','mixed','12-22','jpms_src_000003'),
('jpms_od_014','意味','Meaning','自分より大きな何かへの帰属感と人生の意味の感覚。','PERMA','MLQ・質的インタビュー','qualitative','15-22','jpms_src_000003'),
('jpms_od_015','達成','Accomplishment','目標達成感・自己実現・熟達の感覚。','PERMA','達成感尺度・自己評価','mixed','12-22','jpms_src_000003');

-- ============================================
-- PISA Happy Life Dashboard 主要次元
-- ============================================
INSERT INTO jpms_outcome_dimensions (id, name_ja, name_en, definition, framework, measurement_approach, measurability, relevance_age, source_id) VALUES
('jpms_od_016','学校環境ウェルビーイング','School Environment Well-being','学校での所属感・安全感・教師との関係。学習環境の心理的質。','PISA_WB','PISA質問紙','quantitative','12-15','jpms_src_000004'),
('jpms_od_017','友人関係','Peer Relationships','友人とのつながり・受容感・社会的支援。','PISA_WB','PISA質問紙・社会測定','quantitative','12-18','jpms_src_000004'),
('jpms_od_018','達成意欲・学業期待','Achievement and Aspirations','自分の将来への期待と学業達成への意欲。','PISA_WB','PISA質問紙','quantitative','15-18','jpms_src_000004');

-- ============================================
-- P21 / 21st Century Skills (3次元)
-- ============================================
INSERT INTO jpms_outcome_dimensions (id, name_ja, name_en, definition, framework, measurement_approach, measurability, relevance_age, source_id) VALUES
('jpms_od_019','批判的思考','Critical Thinking','情報の分析・評価・統合に基づく合理的判断能力。','P21','批判的思考テスト・パフォーマンス評価','mixed','12-22','jpms_src_000005'),
('jpms_od_020','コミュニケーション・協働','Communication and Collaboration','多様な相手との効果的な対話と協働の能力。','P21','グループ課題評価・観察','mixed','12-22','jpms_src_000005'),
('jpms_od_021','創造性・革新性','Creativity and Innovation','新しいアイデアの創出と革新的な解決策の構想能力。','P21','創造性課題・作品評価','qualitative','12-22','jpms_src_000005');

-- ============================================
-- 日本独自指標 (4次元)
-- ============================================
INSERT INTO jpms_outcome_dimensions (id, name_ja, name_en, definition, framework, measurement_approach, measurability, relevance_age, source_id) VALUES
('jpms_od_022','社会的自立性','Independence in Society','社会の一員として自律的に判断し行動する力。生活設計・キャリア構築の基盤。','japanese_independent','質問紙・進路追跡','mixed','15-22','jpms_src_000006'),
('jpms_od_023','地域貢献意識','Community Contribution','地域社会・コミュニティへの貢献意識と実践。','japanese_independent','行動記録・質問紙','mixed','12-22','jpms_src_000006'),
('jpms_od_024','道徳性・倫理観','Moral Judgment','善悪の判断と倫理的行動への意志。日本の道徳教育の中核目標。','japanese_independent','道徳判断課題・行動観察','mixed','12-18','jpms_src_000006'),
('jpms_od_025','集団協調性','Group Harmony Skills','集団の調和を保ちつつ個性を発揮する能力。日本社会で重視される対人スキル。','japanese_independent','集団活動評価','qualitative','12-22','jpms_src_000006');
