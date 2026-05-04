-- JPMS-DB 教育学概念シード 拡張セット07 （Team-D: キャリア発展・ウェルビーイング 13件）
-- research-precision-protocol準拠: DOI/ISBN 必須、hallucination禁止、不明なら除外
-- ID範囲: jpms_ec_0054-0066（概念13件）、jpms_src_010400-010412（出典13件）、jpms_ecr_00400-00410（関係11件）

-- ============================================================
-- 出典レイヤ: career_dev (5件) & wellbeing (8件) の学術文献
-- ============================================================

INSERT INTO jpms_sources (id, source_type, title, author, publisher, publication_year, accessed_at, rights_status, primary_or_secondary, reliability_score, note) VALUES

-- Career Development 出典群
('jpms_src_010400','academic_paper','A life-span, life-space approach to career development','Donald E. Super','Journal of Vocational Behavior',1980,datetime('now'),'copyrighted_quotable','primary',98,'DOI: 10.1016/0001-8791(80)90056-1'),

('jpms_src_010401','academic_paper','The Theory and Practice of Career Construction','Mark L. Savickas','Career Development and Counseling: Putting Theory and Research to Work',2005,datetime('now'),'copyrighted_quotable','primary',96,'DOI: 10.4135/9781412952675.n34'),

('jpms_src_010402','academic_paper','Career Adapt-Abilities Scale: Construction, reliability, and measurement equivalence across 13 countries','Mark L. Savickas, Erika J. Porfeli','Journal of Vocational Behavior',2012,datetime('now'),'copyrighted_quotable','primary',97,'DOI: 10.1016/j.jvb.2012.01.011'),

('jpms_src_010403','academic_book','Making Vocational Choices: A Theory of Vocational Personalities and Work Environments (3rd ed.)','John L. Holland','Psychological Assessment Resources',1997,datetime('now'),'copyrighted_quotable','primary',95,'ISBN: 9780911907049'),

('jpms_src_010404','academic_paper','The Happenstance Learning Theory','John D. Krumboltz','Journal of Career Assessment',2009,datetime('now'),'copyrighted_quotable','primary',95,'DOI: 10.1177/1069072708328861'),

-- Wellbeing 出典群
('jpms_src_010405','academic_book','Flourish: A Visionary New Understanding of Happiness and Well-being','Martin E. P. Seligman','Simon & Schuster',2011,datetime('now'),'copyrighted_quotable','primary',97,'ISBN: 9781439190760'),

('jpms_src_010406','academic_paper','The mental health continuum: From languishing to flourishing in life','Corey L. M. Keyes','Journal of Health and Social Behavior',2002,datetime('now'),'copyrighted_quotable','primary',96,'DOI: 10.2307/3090197'),

('jpms_src_010407','academic_paper','Subjective Well-Being','Ed Diener','Psychological Bulletin',1984,datetime('now'),'copyrighted_quotable','primary',98,'PMID: 6399758; Vol. 95(3):542-575'),

('jpms_src_010408','academic_paper','On Happiness and Human Potentials: A Review of Research on Hedonic and Eudaimonic Well-Being','Richard M. Ryan, Edward L. Deci','Annual Review of Psychology',2001,datetime('now'),'copyrighted_quotable','primary',97,'DOI: 10.1146/annurev.psych.52.1.141'),

('jpms_src_010409','academic_paper','Happiness is everything, or is it? Explorations on the meaning of psychological well-being','Carol D. Ryff','Journal of Personality and Social Psychology',1989,datetime('now'),'copyrighted_quotable','primary',96,'DOI: 10.1037/0022-3514.57.6.1069'),

('jpms_src_010410','academic_book','Childrens views on their lives and well-being in 16 countries','Gwyther Rees, Shoshana Andresen, Jonathan Bradshaw (eds.)','International Society on Child Indicators (ISCI)',2016,datetime('now'),'public_domain','primary',94,'https://isciweb.org'),

('jpms_src_010411','academic_paper','Positive education: Positive psychology and classroom interventions','Martin E. P. Seligman, Randal M. Ernst, Jane Gillham, Karen Reivich, Margaret Linkins','Oxford Review of Education',2009,datetime('now'),'copyrighted_quotable','primary',97,'DOI: 10.1080/03054980902934563'),

('jpms_src_010412','academic_paper','Mental illness and/or mental health? Investigating axioms of the complete state model of health','Corey L. M. Keyes','Journal of Consulting and Clinical Psychology',2005,datetime('now'),'copyrighted_quotable','primary',96,'DOI: 10.1037/0022-006X.73.3.539');

-- ============================================================
-- 教育学概念レイヤ: career_dev (5件)
-- ============================================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0054', 'スーパーのライフスパン・ライフスペース理論', 'Super Life-Span Life-Space Theory', 'Life-Span, Life-Space Approach to Career Development', 'Donald E. Superが提唱。キャリアを「人生を通じて演じられる役割の組み合わせと続き」と定義。成長→探索→確立→維持→衰退の5段階と複数の人生役割の相互作用を強調。キャリア成熟度で年齢ではなく決定対応能力を測定。', 'ライフキャリア・キャリアカウンセリングの理論的基盤。世界中のキャリア教育政策に影響。', 'career_dev', 'Life-Span Career Development Theory', 1980, NULL, '単線的職業選択観', 'ライフスパン,ライフスペース,キャリア成熟度,人生役割', 'life-span,life-space,career maturity,life roles', '["Donald E. Super"]', '[{"title":"A life-span, life-space approach to career development","year":1980,"doi":"10.1016/0001-8791(80)90056-1","verified":false,"source_id":"jpms_src_010400"}]', 88, 'pending_verification', 'primary', 75),

('jpms_ec_0055', 'キャリア構成理論', 'Career Construction Theory', 'Career Construction Theory', 'Mark L. Savickasが提唱。キャリアは個人のアイデンティティと人生経験の物語として再解釈。自己概念の発展、キャリアの意味づけ、適応能力の育成を中心。人生肖像法などの実践的介入方法を提供。', 'キャリアカウンセリングの現代的アプローチ。成人教育・生涯学習・SEL分野に影響。', 'career_dev', 'Narrative Career Counseling', 2005, NULL, 'マッチング理論', 'キャリア構成,自己物語,アイデンティティ', 'career construction,self-narrative,identity', '["Mark L. Savickas"]', '[{"title":"The Theory and Practice of Career Construction","year":2005,"doi":"10.4135/9781412952675.n34","verified":false,"source_id":"jpms_src_010401"}]', 90, 'pending_verification', 'primary', 75),

('jpms_ec_0056', 'キャリア適応性', 'Career Adaptability', 'Career Adapt-Abilities', 'Mark L. Savickas & Erika J. Porfeliが提唱。急速に変化する労働市場での個人の対応能力を、Concern・Control・Curiosity・Confidenceの4次元で測定。13カ国による国際的実証研究で信頼性と測定等価性を確認。', 'VUCAな時代の人材育成戦略のコア指標。企業研修・教育プログラムに広く導入。', 'career_dev', 'Career Development Theory', 2012, NULL, '固定的職業適性観', 'キャリア適応性,CAAS,4次元構造', 'career adaptability,CAAS,four-factor structure', '["Mark L. Savickas","Erika J. Porfeli"]', '[{"title":"Career Adapt-Abilities Scale: Construction, reliability, and measurement equivalence across 13 countries","year":2012,"doi":"10.1016/j.jvb.2012.01.011","verified":false,"source_id":"jpms_src_010402"}]', 92, 'pending_verification', 'primary', 75),

('jpms_ec_0057', 'ホランドのRIASEC理論', 'Holland RIASEC Theory', 'Theory of Vocational Personalities and Work Environments', 'John L. Hollandが提唱。職業人は6つの人格タイプ（現実的・研究的・芸術的・社会的・企業的・慣例的）を持つ。人格と環境のマッチング程度が職業満足度を予測。六角形モデルで各タイプの距離関係を図式化。', '職業心理学の古典的理論。半世紀以上世界的に採用。キャリア適性診断の標準的枠組み。', 'career_dev', 'Vocational Psychology', 1959, 1997, '人生経験主義的進路選択観', 'RIASEC,職業人格,環境適合,六角形モデル', 'RIASEC,vocational personality,person-environment fit', '["John L. Holland"]', '[{"title":"Making Vocational Choices: A Theory of Vocational Personalities and Work Environments (3rd ed.)","year":1997,"isbn":"9780911907049","verified":false,"source_id":"jpms_src_010403"}]', 85, 'pending_verification', 'primary', 78),

('jpms_ec_0058', 'クランボルツの偶然学習理論', 'Krumboltz Happenstance Learning Theory', 'The Happenstance Learning Theory', 'John D. Krumboltzが提唱。キャリアパスは計画通りには進まず、偶然の出来事の活用が重要。キャリア決定を「単一の正解」から「複数選択肢の継続的探索」へシフト。柔軟性・レジリエンス・適応的学習を強調。', '不確実性の時代のキャリア教育パラダイム。起業家教育・探究的キャリア学習の理論的支柱。', 'career_dev', 'Career Counseling Theory', 2009, NULL, '計画的キャリア決定論', '偶然学習,キャリア探索,試行的学習', 'happenstance learning,career exploration,trial learning', '["John D. Krumboltz"]', '[{"title":"The Happenstance Learning Theory","year":2009,"doi":"10.1177/1069072708328861","verified":false,"source_id":"jpms_src_010404"}]', 89, 'pending_verification', 'primary', 75);

-- ============================================================
-- 教育学概念レイヤ: wellbeing (8件)
-- ============================================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0059', 'PERMA モデル', 'PERMA Model', 'Positive Emotion, Engagement, Relationships, Meaning, Accomplishment', 'Martin E. P. Seligmanが『Flourish』で提唱。Positive Emotion・Engagement・Relationships・Meaning・Accomplishmentの5要素がウェルビーイングの本質。各要素が独立して測定・追求される。従来の快楽モデルから人生充実度を含む統合的定義。', 'ポジティブ教育・学校ウェルビーイング施策の世界的標準。組織心理学・学校経営改革の枠組みを提供。', 'wellbeing', 'Positive Psychology', 2011, NULL, '病理モデル中心の心理学', 'PERMA,5要素フレームワーク,ウェルビーイング', 'PERMA,five-factor framework,well-being', '["Martin E. P. Seligman"]', '[{"title":"Flourish: A Visionary New Understanding of Happiness and Well-being","year":2011,"isbn":"9781439190760","verified":false,"source_id":"jpms_src_010405"}]', 92, 'pending_verification', 'primary', 75),

('jpms_ec_0060', 'PERMA-H 拡張モデル', 'PERMA-H Extended Model', 'PERMA plus Health', 'Seligmanの PERMA モデルにHealth（身体的健康）を第6要素として追加。物理的活力・睡眠の質・運動習慣・栄養摂取が精神的ウェルビーイングと同等に重要。脳神経科学的エビデンスに基づき心身一体的ウェルビーイング観を提唱。', '学校における包括的ウェルビーイング施策の理論的根拠。体育・食育・健康教育とメンタルヘルスの統合的アプローチを支持。', 'wellbeing', 'Positive Psychology', 2011, NULL, 'メンタルヘルス単一主義', 'PERMA-H,身体健康,心身統合', 'PERMA-H,physical health,mind-body integration', '["Martin E. P. Seligman"]', '[{"title":"Flourish: A Visionary New Understanding of Happiness and Well-being","year":2011,"isbn":"9781439190760","verified":false,"source_id":"jpms_src_010405"}]', 90, 'pending_verification', 'primary', 70),

('jpms_ec_0061', '主観的ウェルビーイング', 'Subjective Well-Being', 'Subjective Well-Being (SWB)', 'Ed Dienerが1984年の総説で体系化。幸福度・人生満足度・肯定的感情の客観的測定を通じ個人が主観的に評価した「人生の充実度」を定量化。心理学的要因が客観的生活条件より幸福に強く影響することを実証。', 'ウェルビーイング研究の基盤理論として四十年間世界的に活用。各国の幸福度調査・GNH政策に影響。', 'wellbeing', 'Positive Psychology / Happiness Research', 1984, NULL, '客観的生活条件決定説', '主観的幸福度,人生満足度,感情的幸福', 'subjective happiness,life satisfaction,affective well-being', '["Ed Diener"]', '[{"title":"Subjective Well-Being","year":1984,"pmid":"6399758","verified":false,"source_id":"jpms_src_010407"}]', 88, 'pending_verification', 'primary', 78),

('jpms_ec_0062', 'フローリッシング（心理的充実）', 'Flourishing', 'Flourishing as Complete Mental Health', 'Corey L. M. Keyesが提唱。メンタルヘルスは「精神疾患の有無」ではなく「言語化困難→中程度健康→フローリッシング」という連続体。フローリッシングは情動的・心理的・社会的ウェルビーイングの組み合わせ。米国では約17%の成人がフローリッシング状態。', 'メンタルヘルスの一元化と予防的観点を導く。学校心理学・キャリア開発の枠組みに影響。', 'wellbeing', 'Mental Health Continuum Model', 2002, 2005, '二者択一的精神疾患分類', 'フローリッシング,メンタルヘルス連続体,多次元評価', 'flourishing,mental health continuum,complete mental health', '["Corey L. M. Keyes"]', '[{"title":"The mental health continuum: From languishing to flourishing in life","year":2002,"doi":"10.2307/3090197","verified":false,"source_id":"jpms_src_010406"},{"title":"Mental illness and/or mental health? Investigating axioms of the complete state model of health","year":2005,"doi":"10.1037/0022-006X.73.3.539","verified":false,"source_id":"jpms_src_010412"}]', 90, 'pending_verification', 'primary', 76),

('jpms_ec_0063', '快楽的幸福 vs 人生充実的幸福', 'Hedonic vs Eudaimonic Well-Being', 'Two Paths to Well-Being', 'Richard M. Ryan & Edward L. Deciが2001年の総説で統合的に解説。Hedonic（快楽的）パスは快感・喜びを求め、Eudaimonic（人生充実的）パスは自己実現・内発的動機を追求。自己決定理論の基盤として外発的報酬より内発的動機付けが持続的幸福につながることを実証。', 'ポジティブサイコロジー・教育心理学・キャリア開発の理論的統合。学校における喜びと達成のバランスに影響。', 'wellbeing', 'Self-Determination Theory / Positive Psychology', 2001, NULL, '単一幸福観', '快楽的幸福,人生充実,自己決定理論', 'hedonic happiness,eudaimonic flourishing,self-determination theory', '["Richard M. Ryan","Edward L. Deci"]', '[{"title":"On Happiness and Human Potentials: A Review of Research on Hedonic and Eudaimonic Well-Being","year":2001,"doi":"10.1146/annurev.psych.52.1.141","verified":false,"source_id":"jpms_src_010408"}]', 91, 'pending_verification', 'primary', 76),

('jpms_ec_0064', '心理的ウェルビーイング', 'Psychological Well-Being', 'Psychological Well-Being (PWB)', 'Carol D. Ryffが1989年に提唱。個人の完全な心理的機能の6次元モデル：自己受容・他者との関係・自律性・環境制御・人生の目的・個人的成長。従来の快楽モデルから離れポテンシャルの実現と人生への意図的関与を強調。', 'ウェルビーイング研究の古典的フレームワーク。35年間世界的に採用。教育評価・臨床心理学の基準。', 'wellbeing', 'Developmental Psychology / Positive Psychology', 1989, NULL, '快楽主義的幸福観', '心理的ウェルビーイング,6次元,自己実現', 'psychological well-being,six dimensions,self-realization', '["Carol D. Ryff"]', '[{"title":"Happiness is everything, or is it? Explorations on the meaning of psychological well-being","year":1989,"doi":"10.1037/0022-3514.57.6.1069","verified":false,"source_id":"jpms_src_010409"}]', 92, 'pending_verification', 'primary', 76),

('jpms_ec_0065', 'チルドレンズ・ワールズ調査', 'Childrens Worlds Survey', 'International Survey of Child Subjective Well-Being (ISCWeB)', 'Gwyther Reesら主導の国際比較研究。2010年以降世界40カ国以上の児童20万人以上を対象に子ども自身の視点から生活満足度・人間関係・学校環境・安全感・健康感を測定。定期波で子ども主体のウェルビーイング国際統計を構築。', '子ども主体の教育評価パラダイム転換を導く。各国の教育政策・学校経営改革の指標基盤。', 'wellbeing', 'Child Psychology / Comparative Education', 2016, NULL, '大人主観的児童評価', 'チルドレンズ・ワールズ,子ども主体調査,主観的幸福感', 'Childrens Worlds,child-centered survey,subjective well-being', '["Gwyther Rees","Shoshana Andresen","Jonathan Bradshaw"]', '[{"title":"Childrens views on their lives and well-being in 16 countries","year":2016,"source_id":"jpms_src_010410"}]', 90, 'pending_verification', 'primary', 75),

('jpms_ec_0066', 'ポジティブ教育', 'Positive Education', 'Positive Education', 'Martin E. P. Seligmanら が2009年に提唱した学校教育プログラム。伝統的な学業成績に加え生徒の幸福感・レジリエンス・人間関係・自己肯定感を系統的に育成。Geelong Grammar School での全校導入で抑うつ症状低減・学習意欲向上を実証。', 'ウェルビーイングを中心とした教育改革の国際的標準。思春期のメンタルヘルス予防と学習成果の両立を実現。', 'wellbeing', 'Positive Psychology / School Education', 2009, NULL, '病理的メンタルヘルス介入', 'ポジティブ教育,レジリエンス,学校ウェルビーイング', 'positive education,resilience,school well-being', '["Martin E. P. Seligman","Randal M. Ernst","Jane Gillham","Karen Reivich","Margaret Linkins"]', '[{"title":"Positive education: Positive psychology and classroom interventions","year":2009,"doi":"10.1080/03054980902934563","verified":false,"source_id":"jpms_src_010411"}]', 95, 'pending_verification', 'primary', 76);

-- ============================================================
-- 概念間関係: career_dev と wellbeing の統合的関係
-- ============================================================

INSERT INTO jpms_education_concept_relations (id, source_concept_id, target_concept_id, relation_type, relation_description, strength) VALUES

('jpms_ecr_00400','jpms_ec_0054','jpms_ec_0055','derived_from','スーパー理論がキャリア構成理論の源泉',7),
('jpms_ecr_00401','jpms_ec_0055','jpms_ec_0056','extends','キャリア構成理論からキャリア適応性が派生',8),
('jpms_ecr_00402','jpms_ec_0057','jpms_ec_0056','related_to','RIASEC理論がキャリア適応性の個人差説明に関連',6),
('jpms_ecr_00403','jpms_ec_0058','jpms_ec_0055','complements','偶然学習理論がキャリア構成理論の柔軟性面を補完',7),
('jpms_ecr_00404','jpms_ec_0054','jpms_ec_0059','applies_to_practice','ライフスパン理論がPERMA評価に応用',6),
('jpms_ecr_00405','jpms_ec_0056','jpms_ec_0064','related_to','キャリア適応性と心理的ウェルビーイングの相互補完',7),
('jpms_ecr_00406','jpms_ec_0059','jpms_ec_0062','synthesizes','PERMAモデルがフローリッシング概念を統合',8),
('jpms_ecr_00407','jpms_ec_0063','jpms_ec_0064','related_to','快楽vs充実パスがRyff理論の背景を説明',7),
('jpms_ecr_00408','jpms_ec_0059','jpms_ec_0066','applies_to_practice','PERMAフレームワークがポジティブ教育の基盤',8),
('jpms_ecr_00409','jpms_ec_0065','jpms_ec_0061','empirically_tests','チルドレンズ調査が主観的ウェルビーイングを検証',8),
('jpms_ecr_00410','jpms_ec_0058','jpms_ec_0059','related_to','偶然学習がPERMAのEngagement達成に寄与',6);

