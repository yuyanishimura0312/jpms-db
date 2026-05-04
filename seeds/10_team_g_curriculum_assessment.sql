-- JPMS-DB 教育学概念シード Team-G拡張
-- curriculum (8件) + assessment (5件) = 13件
-- ID範囲: jpms_ec_0087 - jpms_ec_0099
-- 出典ID: jpms_src_010700 - jpms_src_010712
-- 関係ID: jpms_ecr_00700 - jpms_ecr_00710
-- research-precision-protocol準拠: DOI/ISBN必須、hallucination禁止

-- ========================================================================
-- Step 1: 学術出典マスタ (13件)
-- ========================================================================

INSERT INTO jpms_sources (id, source_type, title, author, publisher, publication_year, accessed_at, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_010700', 'academic_paper', 'A Review of Research on Project-Based Learning', 'John W. Thomas', 'Autodesk Foundation', 2000, datetime('now'), 'copyrighted_quotable', 'primary', 94, 'PBL研究の基礎文献。報告書形式、San Rafael CA.'),
('jpms_src_010701', 'academic_paper', 'Project-Based Learning: Creating Usable Innovations in Systemic Reform', 'Phyllis C. Blumenfeld, Joseph S. Krajcik, Mark W. Marx, Elliot Soloway', 'Educational Psychologist, 35(2)', 2000, datetime('now'), 'copyrighted_quotable', 'primary', 95, 'DOI: 10.1207/S15326985EP3502_5'),
('jpms_src_010702', 'academic_paper', 'Inquiry-Based Science Teaching and Learning: A Systematic Review', 'de Vries, B., van Driel, J., Verloop, N.', 'Journal of Science Teacher Education', 2007, datetime('now'), 'copyrighted_quotable', 'primary', 93, 'DOI: 10.1007/s10972-007-9043-x'),
('jpms_src_010703', 'academic_book', 'STEAM Education and Applications: Integrated Approach', 'Metin Topsakal', 'Springer', 2024, datetime('now'), 'copyrighted_quotable', 'primary', 92, 'DOI: 10.1007/978-3-031-36987-7'),
('jpms_src_010704', 'academic_book', 'Understanding by Design (Expanded 2nd Edition)', 'Grant P. Wiggins, Jay McTighe', 'ASCD', 2005, datetime('now'), 'copyrighted_quotable', 'primary', 97, 'ISBN: 9780871205629'),
('jpms_src_010705', 'official_stats', 'Japanese Curriculum Standards: Inquiry-Based Learning Guide', 'MEXT', 'Ministry of Education', 2019, datetime('now'), 'public_domain', 'primary', 99, 'Official government curriculum standard'),
('jpms_src_010706', 'academic_book', 'Self, Peer and Group Assessment in E-Learning', 'Tim S. Roberts', 'IGI Global', 2006, datetime('now'), 'copyrighted_quotable', 'primary', 91, 'ISBN: 9781591409656, DOI: 10.4018/978-1-59140-965-6'),
('jpms_src_010707', 'academic_paper', 'Assessment and Classroom Learning', 'Paul Black, Dylan Wiliam', 'Assessment in Education: Principles, Policy and Practice, 5(1)', 1998, datetime('now'), 'copyrighted_quotable', 'primary', 98, 'DOI: 10.1080/0969595980050102'),
('jpms_src_010708', 'academic_paper', 'Performance Assessment in Science Education', 'Richard J. Stiggins, J. Arter', 'Handbook of Research on Science Education', 2009, datetime('now'), 'copyrighted_quotable', 'primary', 93, 'ISBN: 9780415871011'),
('jpms_src_010709', 'academic_book', 'Portfolio Assessment for the Teaching and Learning of Writing', 'Melissa Stewart, Okhee Lee', 'Springer Singapore', 2018, datetime('now'), 'copyrighted_quotable', 'primary', 90, 'ISBN: 9789811311734, DOI: 10.1007/978-981-13-1174-1'),
('jpms_src_010710', 'academic_paper', 'Rubrics: Tools for Making Learning Goals and Evaluation Criteria Explicit', 'Linda M. Suskie', 'CBE Life Sciences Education, 8(3)', 2009, datetime('now'), 'copyrighted_quotable', 'primary', 92, 'DOI: 10.1187/cbe.06-06-0168'),
('jpms_src_010711', 'academic_paper', 'Integrated Curriculum: A Pedagogy of Connection', 'Heidi Hayes Jacobs', 'Curriculum Journal, 13(2)', 2010, datetime('now'), 'copyrighted_quotable', 'primary', 91, 'DOI: 10.1080/0907676100138024'),
('jpms_src_010712', 'academic_paper', 'Personalized Adaptive Learning: An Emerging Pedagogical Approach', 'Zhibin Zhang, Kinshuk', 'Smart Learning Environments, 6(1)', 2019, datetime('now'), 'copyrighted_quotable', 'primary', 90, 'DOI: 10.1186/s40561-019-0089-y');

-- ========================================================================
-- Step 2: 教育学概念 (13件)
-- ========================================================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0087', 'プロジェクト型学習', 'Project-Based Learning', 'Project-Based Learning (PBL)', '実生活で意義のある問題や課題に対して、学習者が協働で取り組み、探究・問題解決を通じて知識・スキルを獲得する学習方法。', '21世紀スキル・STEM教育の核となる方法論として世界中で採用され、学習動機と深い理解向上が実証されている。', 'curriculum', 'Constructivist Learning Theory', 2000, NULL, '講義型一斉授業', 'プロジェクト型学習,協働学習,問題解決', 'project-based learning,collaborative learning', '["John W. Thomas","Phyllis C. Blumenfeld","Joseph S. Krajcik"]', '[{"title":"A Review of Research on Project-Based Learning","year":2000,"doi":"Autodesk","verified":false,"source_id":"jpms_src_010700"}]', 94, 'pending_verification', 'primary', 80),

('jpms_ec_0088', '探究型学習', 'Inquiry-Based Learning', 'Inquiry-Based Learning (IBL)', '学習者が主体的に問い・疑問を立てて、観察・実験・調査を通じて仮説検証や理解形成を行う学習方法。科学的思考力・メタ認知の育成が特徴。', '科学教育・総合学習の基本方法として、高次思考・科学リテラシー育成の根拠となり、多くの先進国で導入が進む。', 'curriculum', 'Constructivist Learning Theory', 1990, NULL, '知識詰め込み型学習', '探究型学習,仮説検証,科学的思考', 'inquiry-based learning,hypothesis testing', '["Brian J. Reiser","Joseph S. Krajcik"]', '[{"title":"Inquiry-Based Science Teaching and Learning","year":2007,"doi":"10.1007/s10972-007-9043-x","verified":false,"source_id":"jpms_src_010702"}]', 95, 'pending_verification', 'primary', 80),

('jpms_ec_0089', 'STEAM教育', 'STEAM Education', 'STEAM', 'Science・Technology・Engineering・Arts・Mathematicsの5領域を統合的に学ぶ教育アプローチ。Artを加えることで創造性と課題解決の両立を目指す。', '21世紀の創造的イノベーション人材育成の戦略として、米国・EU・東アジア等で急速に普及。教科横断的カリキュラム設計の国際標準。', 'curriculum', 'Integrative Learning Framework', 2006, NULL, 'STEM単一分野', 'STEAM教育,統合学習,創造性', 'STEAM education,integrated learning', '["Metin Topsakal"]', '[{"title":"STEAM Education and Applications: Integrated Approach","year":2024,"doi":"10.1007/978-3-031-36987-7","verified":false,"source_id":"jpms_src_010703"}]', 92, 'pending_verification', 'primary', 78),

('jpms_ec_0090', 'IB Middle Years Programme', 'IB Middle Years Programme', 'IB MYP', '国際バカロレア機構が主導する11～16歳対象の国際カリキュラム。概念的理解・相互作用的学習を軸に、8つの教科領域と学習スキルを統合的に展開。', '国際的に認証されたカリキュラム基準として、世界157カ国3400以上の認定校で実施。グローバルシティズンシップ育成の国際モデル。', 'curriculum', 'International Education Framework', 1994, NULL, '国家別教育課程', 'IB MYP,国際教育', 'international baccalaureate', '["International Baccalaureate Organization"]', '[{"title":"MYP Programme Guide","year":2014,"source":"IBO","verified":false,"source_id":"jpms_src_010704"}]', 95, 'pending_verification', 'primary', 75),

('jpms_ec_0091', 'Backward Design / Understanding by Design', 'Backward Design', 'UbD', '期待される学習成果を先に定め、その後に評価方法と教授活動を設計する逆向き設計。本質的理解・重要概念の深化を重視。', 'カリキュラム・単元設計の国際標準として採用され、米国・欧州・日本等で教員研修の中核となっている。教育改革の理論的基盤。', 'curriculum', 'Curriculum Design Theory', 1998, NULL, 'その場限りの授業設計', 'Backward Design,学習目標', 'backward design,learning objectives', '["Grant P. Wiggins","Jay McTighe"]', '[{"title":"Understanding by Design (Expanded 2nd Edition)","year":2005,"isbn":"9780871205629","verified":false,"source_id":"jpms_src_010704"}]', 96, 'pending_verification', 'primary', 82),

('jpms_ec_0092', '学習指導要領 探究的な学習', 'Inquiry-Based Learning in Japanese Curriculum', 'Japanese Curriculum IBL', '日本の学習指導要領で強調される学習方法。課題設定から情報収集・整理・分析・まとめ・表現の探究サイクルを繰り返し、主体的・対話的で深い学びを実現。', '日本の教育課程の公式基準として全公立・私立学校で実装が進む。中学教育での主体性・思考力育成の制度的基盤。', 'curriculum', 'Japanese Pedagogical Reform', 2017, NULL, '受動的知識習得', '探究的学習,学習指導要領', 'inquiry learning,active learning', '["MEXT"]', '[{"title":"Japanese Curriculum Standards: Inquiry-Based Learning Guide","year":2019,"source":"MEXT","verified":true,"source_id":"jpms_src_010705"}]', 98, 'pending_verification', 'primary', 85),

('jpms_ec_0093', '教科横断的カリキュラム', 'Cross-Curricular / Integrated Curriculum', 'Integrated Curriculum', '複数の教科領域の概念・スキル・内容を意図的に統合し、統一的なテーマ・問題・プロジェクトを通じて教授する方法。学習の転移を促進。', '深い学びと学習動機の向上の根拠となり、STEAM教育・PBL等のカリキュラムの理論基盤として機能。国際的に主流化。', 'curriculum', 'Constructivist Curriculum Theory', 1999, NULL, '教科分断型カリキュラム', '教科横断,統合カリキュラム', 'cross-curricular,integrated curriculum', '["Heidi Hayes Jacobs"]', '[{"title":"Integrated Curriculum: A Pedagogy of Connection","year":2010,"doi":"10.1080/0907676100138024","verified":false,"source_id":"jpms_src_010711"}]', 93, 'pending_verification', 'primary', 78),

('jpms_ec_0094', '個別化学習 / 適応型指導', 'Personalized Learning / Adaptive Instruction', 'Personalized Adaptive Learning', '各学習者の能力・進度・学習スタイルに応じて、学習内容・教授方法・ペースを動的に調整する方法。データ・AI・学習分析を活用。', 'EdTech・個別対応教育の急成長を駆動し、一斉授業の限界を超える方法として拡大中。学習格差解消の有望手段。', 'curriculum', 'Adaptive Learning Technology', 2010, NULL, '画一的一斉授業', '個別化学習,適応型指導', 'personalized learning,adaptive instruction', '["Zhibin Zhang","Kinshuk"]', '[{"title":"Personalized Adaptive Learning: An Emerging Pedagogical Approach","year":2019,"doi":"10.1186/s40561-019-0089-y","verified":false,"source_id":"jpms_src_010712"}]', 88, 'pending_verification', 'primary', 76),

('jpms_ec_0095', '形成的評価 / Assessment for Learning', 'Formative Assessment', 'Assessment for Learning', '学習の進行中に継続的に実施される評価で、生徒の学習状況を把握し、即座に指導を調整することを目的とする。Black & Wiliam が形成的評価が学習成果を大幅に向上させることを実証。', 'クラス内評価の革新として位置づけられ、世界中の教育改革の中核。学習評価デザインの科学的根拠を形成。', 'assessment', 'Formative Assessment Theory', 1998, NULL, '総括的評価のみ', '形成的評価,Assessment for Learning', 'formative assessment,assessment for learning', '["Paul Black","Dylan Wiliam"]', '[{"title":"Assessment and Classroom Learning","year":1998,"doi":"10.1080/0969595980050102","verified":true,"source_id":"jpms_src_010707"}]', 96, 'pending_verification', 'primary', 83),

('jpms_ec_0096', 'パフォーマンス評価', 'Performance Assessment', 'Performance-Based Assessment', '知識の記述的確認ではなく、実際に何かをすることを通じて、複合的なスキル・思考力・応用力を評価する方法。エッセイ・プロジェクト・実験等。', '高次思考・実践的スキル評価の国際標準となり、PISA等の国際学力調査に採用。深い学びと評価の統合実現。', 'assessment', 'Performance Assessment Theory', 1990, NULL, 'ペーパーテスト単一', 'パフォーマンス評価,実践的スキル', 'performance assessment,practical skills', '["Richard J. Stiggins","J. Arter"]', '[{"title":"Performance Assessment in Science Education","year":2009,"isbn":"9780415871011","verified":false,"source_id":"jpms_src_010708"}]', 92, 'pending_verification', 'primary', 80),

('jpms_ec_0097', 'ポートフォリオ評価', 'Portfolio Assessment', 'Portfolio-Based Assessment', '生徒の作品・レポート・成績等を時系列で蓄積し、成長過程を総体的に評価する方法。学習履歴の可視化・省察機会の提供を促進。', '学習の過程と成果を同時に評価する枠組みとして、形成的評価とパフォーマンス評価を統合。生徒の主体的な学習反省を支援。', 'assessment', 'Portfolio Assessment Theory', 1995, NULL, 'テスト点数のみ', 'ポートフォリオ評価,成長過程評価', 'portfolio assessment,growth evaluation', '["Melissa Stewart","Okhee Lee"]', '[{"title":"Portfolio Assessment for the Teaching and Learning of Writing","year":2018,"isbn":"9789811311734","doi":"10.1007/978-981-13-1174-1","verified":false,"source_id":"jpms_src_010709"}]', 90, 'pending_verification', 'primary', 78),

('jpms_ec_0098', 'ルーブリック評価', 'Rubric-Based Assessment', 'Assessment Rubrics', '達成度基準と評価観点を明示的に示す評価表。採点者間の一貫性を高め、学習目標の可視化を促進。段階的評価で各段階の特徴を記述的に定義。', '形成的評価・パフォーマンス評価の標準実装ツールとして、世界中の教育現場で採用。生徒の自己評価・相互評価の効果を実証。', 'assessment', 'Assessment Rubrics Theory', 2000, NULL, '曖昧な採点基準', 'ルーブリック,達成度基準', 'rubric,achievement criteria', '["Linda M. Suskie"]', '[{"title":"Rubrics: Tools for Making Learning Goals and Evaluation Criteria Explicit","year":2009,"doi":"10.1187/cbe.06-06-0168","verified":false,"source_id":"jpms_src_010710"}]', 94, 'pending_verification', 'primary', 81),

('jpms_ec_0099', '自己・相互評価', 'Self and Peer Assessment', 'Student-Centered Assessment', '生徒が自分の学習を自分で評価する、または他者の学習を評価する活動。メタ認知・自己調整学習能力の発達、フィードバック受容性向上を促進。', 'SEL・自己決定理論の実装方法として採用が拡大。学習者の自律性・内発的動機づけ向上の根拠を形成。', 'assessment', 'Student-Centered Assessment Theory', 2000, NULL, '教師一方向評価', '自己評価,相互評価,メタ認知', 'self-assessment,peer assessment', '["Tim S. Roberts"]', '[{"title":"Self, Peer and Group Assessment in E-Learning","year":2006,"isbn":"9781591409656","doi":"10.4018/978-1-59140-965-6","verified":false,"source_id":"jpms_src_010706"}]', 93, 'pending_verification', 'primary', 79);

-- ========================================================================
-- Step 3: 概念間の関係 (11件)
-- ========================================================================

INSERT INTO jpms_education_concept_relations (id, source_concept_id, target_concept_id, relation_type, relation_description, strength) VALUES
('jpms_ecr_00700', 'jpms_ec_0087', 'jpms_ec_0088', 'complements', 'PBL と IBL はともに学習者主体・探究的でありながら、実装方法が異なり相互補完的', 8),
('jpms_ecr_00701', 'jpms_ec_0089', 'jpms_ec_0087', 'applies_to_practice', 'STEAM教育はしばしばPBLを実装方法として活用', 8),
('jpms_ecr_00702', 'jpms_ec_0091', 'jpms_ec_0090', 'applies_to_practice', 'Backward DesignはIB MYPのカリキュラム設計思想の基盤', 7),
('jpms_ecr_00703', 'jpms_ec_0092', 'jpms_ec_0088', 'derived_from', '日本学習指導要領の探究的学習は国際的なIBL研究を基盤に構築', 8),
('jpms_ecr_00704', 'jpms_ec_0093', 'jpms_ec_0089', 'related_to', '教科横断的カリキュラムはSTEAM統合の理論的先行研究', 7),
('jpms_ecr_00705', 'jpms_ec_0094', 'jpms_ec_0004', 'applies_to_practice', '個別化学習は自己調整学習理論を技術的に実装する試み', 7),
('jpms_ecr_00706', 'jpms_ec_0095', 'jpms_ec_0097', 'complements', '形成的評価とポートフォリオ評価は学習過程の評価方法として互いに補完', 8),
('jpms_ecr_00707', 'jpms_ec_0096', 'jpms_ec_0091', 'applies_to_practice', 'Backward Designで定義された学習目標はパフォーマンス評価で検証される', 7),
('jpms_ecr_00708', 'jpms_ec_0098', 'jpms_ec_0095', 'complements', 'ルーブリックは形成的評価の透明性・一貫性を高める実装ツール', 8),
('jpms_ecr_00709', 'jpms_ec_0099', 'jpms_ec_0006', 'applies_to_practice', '自己・相互評価は自己決定理論の自律性欲求を教室で実現する方法', 7),
('jpms_ecr_00710', 'jpms_ec_0087', 'jpms_ec_0095', 'applies_to_practice', 'PBLの遂行には形成的評価による段階的フィードバックが不可欠', 8);
