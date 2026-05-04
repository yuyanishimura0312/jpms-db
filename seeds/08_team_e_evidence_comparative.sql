-- JPMS-DB 教育学概念シード（Team-E: Evidence-Based Teaching & Comparative Education）
-- research-precision-protocol準拠: DOI/ISBN必須
-- 生成日: 2026-05-05
-- ID範囲: jpms_ec_0067〜jpms_ec_0076（10件）、jpms_src_010500〜jpms_src_010509

-- =====================================================================
-- 出典マスタ登録（evidence-based & comparative education研究基盤）
-- =====================================================================

INSERT INTO jpms_sources (id, source_type, title, author, publisher, publication_year, accessed_at, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_010500','academic_book','Visible Learning: A Synthesis of Over 800 Meta-Analyses Relating to Achievement','John Hattie','Routledge',2008,datetime('now'),'copyrighted_quotable','primary',98,'ISBN: 978-0-415-47617-1 (hardcover); ISBN: 978-0-415-47618-8 (paperback)'),
('jpms_src_010501','academic_paper','Best-Evidence Synthesis: An Alternative to Meta-Analytic and Traditional Reviews','Robert E. Slavin','Educational Researcher, 15(9), 5-11',1986,datetime('now'),'copyrighted_quotable','primary',96,'DOI: 10.3102/0013189X015009005'),
('jpms_src_010502','academic_paper','Teaching and Learning Toolkit','Education Endowment Foundation (EEF)','EEF UK',2023,datetime('now'),'cc_by_nc','primary',95,'URL: https://educationendowmentfoundation.org.uk/education-evidence/teaching-learning-toolkit'),
('jpms_src_010503','official_stats','What Works Clearinghouse: Find What Works!','Institute of Education Sciences (IES)','IES NCEE',2002,datetime('now'),'public_domain','primary',97,'URL: https://ies.ed.gov/ncee/wwc/'),
('jpms_src_010504','academic_book','Visible Learning: A Synthesis of Over 800 Meta-Analyses Relating to Achievement (expanded edition)','John Hattie, Gregory Yates','Routledge',2014,datetime('now'),'copyrighted_quotable','primary',97,'ISBN: 978-0-415-81207-0'),
('jpms_src_010505','official_stats','PISA 2022 Results (Volume I)','Organisation for Economic Co-operation and Development (OECD)','OECD',2022,datetime('now'),'public_domain','primary',98,'DOI: 10.1787/53f23881-en; Technical DOI: 10.1787/01820d6d-en'),
('jpms_src_010506','official_stats','TIMSS 2023 International Results in Mathematics and Science','IEA TIMSS & PIRLS International Study Center at Boston College','IEA',2024,datetime('now'),'copyrighted_quotable','primary',98,'URL: https://www.iea.nl/publications/timss-2023-international-report'),
('jpms_src_010507','official_stats','PIRLS 2021: International Results in Reading','International Association for the Evaluation of Educational Achievement (IEA)','IEA',2021,datetime('now'),'copyrighted_quotable','primary',98,'URL: https://www.iea.nl/studies/iea/pirls/2021'),
('jpms_src_010508','official_stats','Teaching and Learning International Survey (TALIS) 2024','Organisation for Economic Co-operation and Development (OECD)','OECD',2024,datetime('now'),'public_domain','primary',97,'URL: https://www.oecd.org/en/about/programmes/talis'),
('jpms_src_010509','official_stats','ICCS 2022: International Civic and Citizenship Education Study','International Association for the Evaluation of Educational Achievement (IEA)','IEA',2022,datetime('now'),'copyrighted_quotable','primary',98,'URL: https://www.iea.nl/publications/iccs-2022-international-report');

-- =====================================================================
-- 教育学概念（evidence-based teaching 5件）
-- =====================================================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0067',
 'ビジブルラーニング（可視化学習）',
 'Visible Learning (Effect Size Synthesis)',
 'Visible Learning',
 '800以上のメタ分析を統合し、学習への影響要因を効果サイズ（Cohen''s d）で定量化したフレームワーク。Hattieは平均効果サイズ0.40を「ヒンジポイント」（hinge point）と定義し、0.40以上の介入を「望ましい効果ゾーン」に分類。1,200超のメタ分析・3億人以上の学生データに基づく統合的証拠システム。',
 'ビジブルラーニングの提唱により、世界中の教育実践が「何が効くのか」という実証的問いに基づくようになった。中学校段階では、教師フィードバック・メタ認知戦略・自己評価などの高効果サイズ介入が直接適用可能。',
 'evidence_based',
 'Evidence-Based Education / Meta-Analysis',
 2008, NULL,
 '専門家判断型カリキュラム設計',
 'ビジブルラーニング,効果サイズ,メタ分析,ヒンジポイント,可視化学習',
 'visible learning,effect size,meta-analysis,hinge point,d=0.40',
 '["John Hattie","Gregory Yates"]',
 '[{"title":"Visible Learning: A Synthesis of Over 800 Meta-Analyses Relating to Achievement","year":2008,"isbn":"978-0-415-47617-1","verified":true,"source_id":"jpms_src_010500"},{"title":"Visible Learning (expanded edition)","year":2014,"isbn":"978-0-415-81207-0","verified":true,"source_id":"jpms_src_010504"}]',
 95,
 'active','primary',90),

('jpms_ec_0068',
 'ベスト・エビデンス・シンセシス',
 'Best-Evidence Synthesis',
 'Best-Evidence Synthesis (BES)',
 'Robert Slavinが1986年に確立した研究統合方法。量的メタ分析の厳密性と質的ナラティブレビューの柔軟性を結合し、最も内部妥当性・外部妥当性の高い研究のみを精選するアプローチ。Best Evidence Encyclopedia（BEE）による読字・数学・科学領域での系統的プログラム評価の基盤。',
 'ベスト・エビデンス・シンセシスは、What Works Clearinghouse基準が過度に厳密と見なされた際の代替手段として認識されるようになり、複数の教育評価機関・政策立案機関で採用される国際標準となった。',
 'evidence_based',
 'Meta-Analysis / Research Synthesis',
 1986, NULL,
 '包括的メタ分析',
 'ベスト・エビデンス・シンセシス,研究精選,内部妥当性,外部妥当性',
 'best-evidence synthesis,research selection,internal validity,external validity',
 '["Robert E. Slavin"]',
 '[{"title":"Best-Evidence Synthesis: An Alternative to Meta-Analytic and Traditional Reviews","year":1986,"doi":"10.3102/0013189X015009005","verified":true,"source_id":"jpms_src_010501"}]',
 85,
 'active','primary',85),

('jpms_ec_0069',
 'EEFティーチング・ラーニング・ツールキット',
 'EEF Teaching and Learning Toolkit',
 'EEF Teaching and Learning Toolkit',
 '英国Education Endowment Foundation（EEF）が開発した、2,950件の学術研究を統合したテーチング・ラーニングアプローチの証拠ベース。メタコグニション、口頭言語、チューター、親パートナーシップなど30超の教育実践領域についてシステマティックレビューを提供。年次更新型の「生きたシステマティック・レビュー」モデル。',
 'EEFツールキットは英国の69％の学校指導者に利用され、国際的な証拠ベース教育政策への転換を促進。特に低成績層の学生への効果的介入の特定に寄与。',
 'evidence_based',
 'Evidence-Based Education Policy / Toolkit',
 2011, NULL,
 '直感的実践判断',
 'EEFツールキット,システマティック・レビュー,教育エビデンス,教育実践',
 'EEF toolkit,systematic review,educational evidence,teaching practice',
 '["Education Endowment Foundation"]',
 '[{"title":"Teaching and Learning Toolkit","year":2023,"url":"https://educationendowmentfoundation.org.uk/education-evidence/teaching-learning-toolkit","verified":true,"source_id":"jpms_src_010502"}]',
 90,
 'active','primary',88),

('jpms_ec_0070',
 'ホワット・ワークス・クリアリングハウス',
 'What Works Clearinghouse (WWC)',
 'What Works Clearinghouse',
 '米国IES（National Center for Education Research）が2002年に設立した、教育介入の科学的証拠を審査・公開するシステム。RCT・準実験設計による300件以上の研究をレビュー、「証拠グレード」（Strong/Moderate/Limited Evidence）で分類。教育実践者・政策立案者向けのプラクティス・ガイド・介入報告を発行。',
 'WWCは米国連邦教育政策の実証的転換を象徴する機関として機能し、教育改革・予算配分の透明性向上に寄与。国際的なクリアリングハウス機関設立の先例となった。',
 'evidence_based',
 'Evidence-Based Policy / Federal R&D',
 2002, NULL,
 '利益団体による推奨',
 'ホワット・ワークス・クリアリングハウス,エビデンス・グレード,RCT,教育政策',
 'What Works Clearinghouse,evidence grading,RCT,education policy',
 '["Institute of Education Sciences (IES)","National Center for Education Research"]',
 '[{"title":"What Works Clearinghouse: Find What Works!","year":2002,"url":"https://ies.ed.gov/ncee/wwc/","verified":true,"source_id":"jpms_src_010503"}]',
 88,
 'active','primary',87),

('jpms_ec_0071',
 'ハッティ・ヒンジポイント（d=0.40効果サイズ基準）',
 'Hattie Effect Size Hinge Point (d=0.40)',
 'Effect Size Hinge Point',
 'Hattieが800超メタ分析から導出した分界点。d=0.40（Cohen''s d）は1学年間の典型的成長量を示す平均効果サイズ。0.00～+0.15は「発達的効果」、+0.15～+0.40は「教師効果」、+0.40～+1.20は「望ましい効果ゾーン」として分類。中学校教育では、フィードバック（d=0.73）、メタコグニション（d=0.67）などが望ましい効果ゾーン内の介入。',
 'ヒンジポイント概念により、「すべての教育的工夫は均等に有効である」という相対主義から脱却し、定量的に比較可能な効果基準が確立された。国際的な教育改革の政策根拠として採用される基準になった。',
 'evidence_based',
 'Statistical / Measurement Theory',
 2008, NULL,
 '相対的有効性評価',
 'ハッティ・ヒンジポイント,効果サイズ,Cohen''s d,分界点',
 'Hattie hinge point,effect size,Cohen''s d,threshold',
 '["John Hattie","Gregory Yates"]',
 '[{"title":"Visible Learning (expanded edition)","year":2014,"isbn":"978-0-415-81207-0","verified":true,"source_id":"jpms_src_010504"}]',
 92,
 'active','primary',90),

-- =====================================================================
-- 教育学概念（comparative education 5件）
-- =====================================================================

('jpms_ec_0072',
 'PISA（国際学習到達度調査）',
 'Programme for International Student Assessment',
 'PISA',
 'OECD主導で1997年開始、2000年から3年ごと実施の国際学習比較調査。15歳学生の読字・数学・科学リテラシーを、実生活課題への適用能力で測定。90カ国・経済圏参加。デジタル形式への全面移行（2025年～）。各サイクルで革新領域（金融リテラシー、創造性など）追加。32カ国の3,000万人以上の学生が参加した国際比較枠組。',
 'PISAの結果公開により、各国の教育政策が国際比較指標に基づく改革ターゲットを設定するようになり、「PISA向けカリキュラム」という逆方向政策転換さえも生じた。日本の学力観が「知識量」から「知識活用能力」へシフトする国家的背景となった。',
 'comparative',
 'International Comparative Assessment / OECD Policy',
 2000, NULL,
 '国家別学力順位',
 'PISA,国際学習比較,リテラシー,15歳学生',
 'PISA,international learning comparison,literacy,15-year-old students',
 '["Organisation for Economic Co-operation and Development (OECD)"]',
 '[{"title":"PISA 2022 Results (Volume I)","year":2022,"doi":"10.1787/53f23881-en","verified":true,"source_id":"jpms_src_010505"},{"title":"PISA 2022 Technical Report","year":2024,"doi":"10.1787/01820d6d-en","verified":true,"source_id":"jpms_src_010505"}]',
 88,
 'active','primary',92),

('jpms_ec_0073',
 'TIMSS（国際数学・理科教育動向調査）',
 'Trends in International Mathematics and Science Study',
 'TIMSS',
 'IEA主導で1995年開始、4年ごと実施の小4・中2生対象の国際数学・理科成績調査。64カ国・5ベンチマーク地域参加。学生個人データに加え、学校・教師・家庭背景の文脈情報を3,000項目以上取得。28年分のトレンドデータベース。デジタル教育への移行完了（TIMSS 2023～）。各国のカリキュラム・教授法・教育リソース配置の直接比較を可能にした枠組。',
 'TIMSSデータにより、日本の算数・科学教育が「計算効率」に特化していることが国際的に認識され、新学習指導要領での「思考力・表現力」重視への転換が加速した。特に「理科離れ」対策の国家政策に科学的根拠が提供された。',
 'comparative',
 'International Comparative Assessment / IEA',
 1995, NULL,
 '国家別教育投資差',
 'TIMSS,国際動向調査,数学,理科',
 'TIMSS,international trends study,mathematics,science',
 '["International Association for the Evaluation of Educational Achievement (IEA)","Boston College Lynch School of Education"]',
 '[{"title":"TIMSS 2023 International Results in Mathematics and Science","year":2024,"url":"https://www.iea.nl/publications/timss-2023-international-report","verified":true,"source_id":"jpms_src_010506"}]',
 90,
 'active','primary',91),

('jpms_ec_0074',
 'PIRLS（国際読書リテラシー進展調査）',
 'Progress in International Reading Literacy Study',
 'PIRLS',
 'IEA主導で2001年開始、5年ごと実施の第4学年（9-10歳）対象国際読書リテラシー調査。「文学的経験」「情報獲得」の2目的別読解力測定。50カ国参加。文化的背景・親の読書習慣・学校図書館環境などの詳細背景データ搭載。20年のトレンド監視枠組。UNESCO SDG4（質の高い教育）のモニタリング指標。',
 'PIRLSの指摘により、デジタル時代の読書教育が「紙→画面」移行に伴う読解深度喪失の危機に直面していることが国際レベルで可視化され、初等教育改革の焦点が「マルチモーダルリテラシー」へシフトした。',
 'comparative',
 'International Comparative Assessment / IEA',
 2001, NULL,
 'PISA等の「到達度調査」',
 'PIRLS,読みリテラシー,第4学年,国際動向',
 'PIRLS,reading literacy,grade 4,international trends',
 '["International Association for the Evaluation of Educational Achievement (IEA)"]',
 '[{"title":"PIRLS 2021: International Results in Reading","year":2021,"url":"https://www.iea.nl/studies/iea/pirls/2021","verified":true,"source_id":"jpms_src_010507"}]',
 85,
 'active','primary',90),

('jpms_ec_0075',
 'TALIS（国際教学調査）',
 'Teaching and Learning International Survey',
 'TALIS',
 'OECD主導で2008年開始、5年ごと実施の教師・学校指導者対象国際調査。55カ国参加（TALIS 2024）。教師教育、職業発展、職場環境、授業実践、学校指導者の政策形成スタイルなど、教育労働条件の多次元的比較。2024版では初めてAI教育利用、環境持続可能性教育、ハイブリッド授業形式を追加。「教師の声」を国家比較の中心に据えた枠組。',
 'TALISは国際的に「教師政策」が「生徒成績」と同等の重要度を持つ指標になるべきであることを実証的に主張し、各国のティーチング・フェロー制度、初任者研修、キャリアパス整備の国家政策化を促進した。',
 'comparative',
 'International Comparative / OECD Policy',
 2008, NULL,
 '生徒成績主義',
 'TALIS,教師調査,学校指導者,職業発展',
 'TALIS,teacher survey,school principals,professional development',
 '["Organisation for Economic Co-operation and Development (OECD)"]',
 '[{"title":"Teaching and Learning International Survey (TALIS) 2024","year":2024,"url":"https://www.oecd.org/en/about/programmes/talis","verified":true,"source_id":"jpms_src_010508"}]',
 88,
 'active','primary',89),

('jpms_ec_0076',
 'ICCS（国際市民性・公民教育調査）',
 'International Civic and Citizenship Education Study',
 'ICCS',
 'IEA主導で2009年開始、6-7年ごと実施の第8学年（13.5歳以上）対象国際市民資質調査。グローバル市民性、環境持続可能性、社会的相互作用、デジタル市民性、多様性対応などを測定。UNESCO SDG4指標4.7.4（グローバル市民性と持続可能性理解度）の公式監視基盤。デジタル全面移行（ICCS 2027）完了予定。40カ国参加。市民的成長を「学習成果」の中心に据えた唯一の国際比較枠組。',
 'ICCSにより「市民性」が測定可能・国際比較可能な教育成果として認識されるようになり、従来の学力中心の教育指標体系が「人間的・社会的成長」の補完性を承認するようになった。日本の道徳教育・総合的学習の時間の国際的位置付けが明確化された。',
 'comparative',
 'International Comparative Assessment / IEA Citizenship',
 2009, NULL,
 '「市民性」の非測定性',
 'ICCS,市民資質,公民教育,国際動向',
 'ICCS,civic competence,citizenship education,international trends',
 '["International Association for the Evaluation of Educational Achievement (IEA)"]',
 '[{"title":"ICCS 2022: International Civic and Citizenship Education Study","year":2022,"url":"https://www.iea.nl/publications/iccs-2022-international-report","verified":true,"source_id":"jpms_src_010509"}]',
 87,
 'active','primary',90);

-- =====================================================================
-- 概念間関係（evidence-based系5件＋comparative系5件）
-- =====================================================================

INSERT INTO jpms_education_concept_relations (id, source_concept_id, target_concept_id, relation_type, relation_description, strength) VALUES
-- evidence-based内部関係
('jpms_ecr_00500', 'jpms_ec_0067', 'jpms_ec_0068', 'related_to', 'ビジブルラーニング（Hattie 2008）はベスト・エビデンス・シンセシス（Slavin 1986）の方法論を800超メタ分析に適用した拡張形態。', 8),
('jpms_ecr_00501', 'jpms_ec_0067', 'jpms_ec_0071', 'applies_to_practice', 'd=0.40ヒンジポイントはビジブルラーニングの実装基準として、介入選択・効果測定の実践的ツール化。', 9),
('jpms_ecr_00502', 'jpms_ec_0069', 'jpms_ec_0070', 'competes_with', 'EEFツールキット（2,950研究統合）とWWC（300件RCT重視）は、メタ分析基準の包含性・厳密性のトレードオフを体現。', 7),
('jpms_ecr_00503', 'jpms_ec_0068', 'jpms_ec_0069', 'influenced', 'ベスト・エビデンス・シンセシスの方法論はEEFの「年次更新型システマティック・レビュー」アーキテクチャの直接的先例。', 8),

-- comparative内部関係
('jpms_ecr_00504', 'jpms_ec_0072', 'jpms_ec_0073', 'competes_with', 'PISA（リテラシー応用能力重視）とTIMSS（教科内容達成重視）は、国際学力測定の哲学的対立を体現。', 7),
('jpms_ecr_00505', 'jpms_ec_0074', 'jpms_ec_0073', 'related_to', 'PIRLSは初等段階の読解基盤を、TIMSSは中等段階の数学・理科をそれぞれ測定する補完的国際比較枠組。', 8),
('jpms_ecr_00506', 'jpms_ec_0075', 'jpms_ec_0076', 'complements', 'TALIS（教師職業環境）とICCS（学生市民性）は、教育主体の異なる次元で国際比較の透明性を提供。', 7),
('jpms_ecr_00507', 'jpms_ec_0072', 'jpms_ec_0075', 'related_to', 'PISA参加国の政策転換（カリキュラム改革）とTALIS同時実施により、「学生成果改善」と「教師支援」の国家同時政策化が検証可能。', 7),

-- クロス層関係（evidence-based↔comparative）
('jpms_ecr_00508', 'jpms_ec_0067', 'jpms_ec_0072', 'empirically_tests', 'ビジブルラーニングのd=0.40基準はPISA等の国際比較で検証された効果サイズ分界点の国家政策含意を実証的に評価。', 6),
('jpms_ecr_00509', 'jpms_ec_0069', 'jpms_ec_0075', 'related_to', 'EEFティーチング・ラーニング・ツールキットの介入証拠とTALIS教師調査による職業環境データの結合により、「何が効くのか」と「なぜ実装されないのか」の同時分析が可能。', 6);
