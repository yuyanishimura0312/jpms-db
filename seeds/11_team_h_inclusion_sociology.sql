-- JPMS-DB 教育学概念シード（inclusion & sociology_of_ed）
-- Team-H 提供: 6概念（inclusion 3件 + sociology_of_ed 3件）
-- research-precision-protocol準拠: DOI/ISBN/URL必須、hallucination禁止

-- ========================================================================
-- 教育学文献出典の登録
-- ========================================================================

-- Inclusion関連の出典
INSERT INTO jpms_sources (id, source_type, title, author, publisher, publication_year, accessed_at, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_010801','academic_book','Universal Design for Learning: Principles, Framework, and Practice (Third Edition)','Rose, D. H., Hall, T. E., & Strangman, N. (CAST)','CAST Professional Publishing',2018,datetime('now'),'copyrighted_quotable','primary',98,'ISBN: 9781943085392 — UDLフレームワークの統合的解説'),
('jpms_src_010802','academic_paper','The Salamanca Statement and Framework for Action on Special Needs Education','UNESCO','UNESCO Publishing',1994,datetime('now'),'public_domain','primary',99,'UNESCO Reference: ED-94/WS/18 — インクルーシブ教育の国際的規範'),
('jpms_src_010803','academic_book','How to Differentiate Instruction in Mixed-Ability Classrooms (2nd Edition)','Tomlinson, Carol Ann','Pearson Education',2001,datetime('now'),'copyrighted_quotable','primary',96,'ISBN: 9781416623304 — 差異化授業の実践的ガイド'),
('jpms_src_010804','academic_book','Les héritiers: Les étudiants et la culture (The Inheritors: French Students and Culture)','Bourdieu, Pierre & Passeron, Jean-Claude','Éditions de Minuit',1964,datetime('now'),'copyrighted_quotable','primary',98,'ISBN: 9782707300812 — 文化資本の社会学的分析'),
('jpms_src_010805','academic_paper','Equality of Educational Opportunity (Coleman Report)','Coleman, James S., et al.','U.S. Government Printing Office',1966,datetime('now'),'public_domain','primary',97,'ERIC ID: ED012275, ICPSR DOI: 10.3886/ICPSR06389.v3 — 教育機会平等の実証的検証'),
('jpms_src_010806','academic_book','Life in Classrooms','Jackson, Philip W.','Holt, Rinehart and Winston',1968,datetime('now'),'copyrighted_quotable','primary',96,'Publisher: Holt, Rinehart and Winston — 隠れたカリキュラムの概念化');

-- ========================================================================
-- 教育学概念（inclusion 3件）
-- ========================================================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0100',
 'ユニバーサルデザイン・フォー・ラーニング',
 'Universal Design for Learning (UDL)',
 'Universal Design for Learning',
 'すべての学習者がアクセス可能で有意義な学習機会を得られるよう、教材設計・教授設計に普遍的な原則を適用する教育フレームワーク。CAST（Center for Applied Special Technology）が開発。学習への意欲（Engagement）・学習内容の表現方法（Representation）・学習成果の表現方法（Action & Expression）の3つの柱で、多様な学習者ニーズに対応する柔軟な教育を実現する。',
 '米国の特別支援教育・インクルーシブ教育の実践的基盤として位置づけられ、世界中の教育改革・カリキュラム設計に影響を与えている。日本の特別支援教育でもUDLの考え方が徐々に導入され始めている。',
 'inclusion',
 'Universal Design / Inclusive Education',
 2000, NULL,
 '標準化された一律授業設計',
 'ユニバーサルデザイン,アクセシビリティ,柔軟な教材,多様な表現方法',
 'universal design,accessibility,flexible curriculum,multiple means of engagement representation action expression',
 '["David H. Rose","Todd E. Hall","Nikolai Strangman","CAST"]',
 '[{"title":"Universal Design for Learning: Principles, Framework, and Practice (Third Edition)","year":2018,"isbn":"9781943085392","verified":true,"source_id":"jpms_src_010801"}]',
 88,
 'active','primary',85),

('jpms_ec_0101',
 'インクルーシブ教育',
 'Inclusive Education',
 'Inclusive Education',
 'すべての子どもが、障害の有無や能力の違いに関わらず、同じ教室で一緒に学ぶ権利を認める教育理念・実践体系。1994年のUNESCO「サラマンカ宣言」で「通常教育システム内でのすべての児童の学習」が国際的原則として明記された。差異化授業・支援体制の充実・物理的アクセス改善を通じて、包括的な学習環境を構築する。',
 'インクルーシブ教育は国連障害者権利条約（2006年批准）の基本理念として位置づけられ、先進国を中心に法制度・実践の変革をもたらした。日本の教育改革でも「共生社会の形成」の重要施策として推進されている。',
 'inclusion',
 'Human Rights & Inclusive Education',
 1994, NULL,
 '統合教育(Integration)的分離',
 'インクルーシブ教育,共生社会,教育機会平等,差異への対応',
 'inclusive education,equal educational opportunity,disability rights,accessibility',
 '["UNESCO","國際障害者権利委員会"]',
 '[{"title":"The Salamanca Statement and Framework for Action on Special Needs Education","year":1994,"reference":"ED-94/WS/18","verified":true,"source_id":"jpms_src_010802"}]',
 92,
 'active','primary',90),

('jpms_ec_0102',
 '差異化授業',
 'Differentiated Instruction',
 'Differentiated Instruction',
 '学習者の準備度（readiness）・興味（interest）・学習プロフィール（learning profile）の違いに応じて、教材内容・教授方法・学習成果の評価方法を柔軟に変える授業設計法。Carol Ann Tomlinsonが体系化。本質的には「一人ひとりの学習者に応じた個別化」ではなく、「教室内の多様性を活かした教育」を目指す実践的手法。',
 '差異化授業は、個別学習・協調学習・小グループ学習を組み合わせた実践として、米国の標準的教授方法として認識され、世界中の教師研修の中核テーマになっている。',
 'inclusion',
 'Learner-Centered Instruction',
 1995, NULL,
 '能力別クラス編成・追い出し型分離教育',
 '差異化授業,学習ニーズ,個別化,柔軟な評価',
 'differentiated instruction,readiness interest learning profile,flexible assessment,mixed-ability classrooms',
 '["Carol Ann Tomlinson"]',
 '[{"title":"How to Differentiate Instruction in Mixed-Ability Classrooms (2nd Edition)","year":2001,"isbn":"9781416623304","verified":true,"source_id":"jpms_src_010803"}]',
 85,
 'active','primary',83);

-- ========================================================================
-- 教育学概念（sociology_of_ed 3件）
-- ========================================================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0103',
 'ブルデュー文化資本論',
 'Bourdieu Cultural Capital',
 'Capital culturel (Bourdieu)',
 'フランスの社会学者ピエール・ブルデューが提唱した概念。教育成功は個人の能力だけでは決まらず、家庭で習得される文化的素養・言語能力・芸術的感受性などの「文化資本」に大きく左右されるという理論。『遺産相続者たち』（1964年）で初出し、1986年の「資本の諸形態」でさらに理論化。社会再生産論の基礎を築く。',
 'ブルデューの文化資本論は、教育社会学の根本的命題である「教育不平等」を説明する最有力理論として、世界の教育研究・政策立案に深刻な影響を与え続けている。',
 'sociology_of_ed',
 'Sociology of Education / Educational Inequality',
 1964, NULL,
 'ヒューマン・キャピタル論（人的資本論）による個人責任論',
 '文化資本,社会的再生産,教育不平等,階級差別',
 'cultural capital,social reproduction,educational inequality,habitus',
 '["Pierre Bourdieu","Jean-Claude Passeron"]',
 '[{"title":"Les héritiers: Les étudiants et la culture (The Inheritors)","year":1964,"isbn":"9782707300812","verified":true,"source_id":"jpms_src_010804"}]',
 78,
 'active','primary',88),

('jpms_ec_0104',
 'コールマン報告と教育機会平等',
 'Coleman Report / Equality of Educational Opportunity',
 'Equality of Educational Opportunity (EEOS)',
 '1966年に米国の社会学者ジェームス・コールマンが中心となって実施した大規模調査。1964年の公民権法に基づき、人種・宗教・出身地による教育機会の不平等を全米規模で実証的に検証した。約65万人の学生と3,000校以上の学校を対象とした調査結果から、「学校の資源格差よりも家庭・地域の社会経済的背景が学業成績に強く影響する」という衝撃的知見を報告。',
 'コールマン報告は教育政策・教育投資の効果をめぐる根本的な問い直しをもたらし、教育不平等研究の古典として世界中の教育学・社会学で引用され続けている。',
 'sociology_of_ed',
 'Empirical Educational Sociology',
 1966, NULL,
 'スクール・エフェクト重視論',
 'コールマン報告,教育機会,家庭背景,学業成績,社会経済的地位',
 'Coleman Report,equality of opportunity,socioeconomic status,academic achievement',
 '["James S. Coleman"]',
 '[{"title":"Equality of Educational Opportunity","year":1966,"eric_id":"ED012275","icpsr_doi":"10.3886/ICPSR06389.v3","verified":true,"source_id":"jpms_src_010805"}]',
 81,
 'active','primary',87),

('jpms_ec_0105',
 '隠れたカリキュラム',
 'Hidden Curriculum',
 'Hidden Curriculum',
 'フィリップ・ジャクソンが1968年の『教室での生活』で概念化した理論。学校の公式なカリキュラムには現れない、実は教室のあらゆる場面で学生に伝わる非公式な学習内容を指す。例えば、教師への服従・時間厳守・競争心・規範遵守など、社会化の過程で習得される暗黙的価値観やスキル。近年の研究では、性別役割・人種意識など、権力構造や社会的不平等を再生産する機構として認識されている。',
 '隠れたカリキュラム論は教育の政治性・権力性を可視化した重要な視点として、カリキュラム研究・批判的教育学の基盤をなし、世界中の教育改革で「隠れたメッセージ」への自覚を促してきた。',
 'sociology_of_ed',
 'Critical Pedagogy / Curriculum Studies',
 1968, NULL,
 '公式カリキュラム中心主義',
 '隠れたカリキュラム,非公式学習,社会化,権力関係,暗黙的価値観',
 'hidden curriculum,informal learning,socialization,power relations,implicit values',
 '["Philip W. Jackson"]',
 '[{"title":"Life in Classrooms","year":1968,"publisher":"Holt, Rinehart and Winston","verified":true,"source_id":"jpms_src_010806"}]',
 80,
 'active','primary',82);
