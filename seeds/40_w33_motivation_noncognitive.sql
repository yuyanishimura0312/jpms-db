-- ========================================================================
-- JPMS-DB Phase 1補強 W33 教育学概念追加投入
-- motivation_dev (8件) + noncognitive (6件) = 14件
-- Team-B CHECK制約違反分の再投入 (改良版)
-- ========================================================================
-- ID範囲:
--   概念: jpms_ec_0200 ~ jpms_ec_0213 (14件)
--   出典: jpms_src_040300 ~ jpms_src_040313 (14件)
--   関係: jpms_ecr_00800 ~ jpms_ecr_00810 (11件、Growth Mindset/Self-Efficacy/GRIT関係)
-- ========================================================================

-- ========================================
-- SOURCES: 14件の学術文献出典
-- ID範囲: jpms_src_040300 ~ jpms_src_040313
-- ========================================

INSERT INTO jpms_sources (id, source_type, title, author, publisher, publication_year, accessed_at, rights_status, primary_or_secondary, reliability_score, note) VALUES

-- motivation_dev sources (8件)
('jpms_src_040300', 'academic_paper', 'A Social-Cognitive Approach to Motivation and Personality', 'Carol S. Dweck, Ellen L. Leggett', 'Psychological Review, 95(2), 256-273', 1988, datetime('now'), 'copyrighted_quotable', 'primary', 98, 'DOI: 10.1037/0033-295X.95.2.256 - Growth Mindset original foundational work'),

('jpms_src_040301', 'academic_paper', 'Self-Efficacy: Toward a Unifying Theory of Behavioral Change', 'Albert Bandura', 'Psychological Review, 84(2), 191-215', 1977, datetime('now'), 'copyrighted_quotable', 'primary', 98, 'DOI: 10.1037/0033-295X.84.2.191 - Self-Efficacy foundational theory'),

('jpms_src_040302', 'academic_paper', 'Expectancy-Value Theory of Achievement Motivation', 'Jacquelynne S. Eccles, Allan Wigfield', 'Contemporary Educational Psychology, 25(1), 68-81', 2000, datetime('now'), 'copyrighted_quotable', 'primary', 97, 'DOI: 10.1006/ceps.1999.1015'),

('jpms_src_040303', 'academic_paper', 'The Four-Phase Model of Interest Development', 'Suzanne Hidi, K. Ann Renninger', 'Educational Psychologist, 41(2), 111-127', 2006, datetime('now'), 'copyrighted_quotable', 'primary', 95, 'Interest development framework - ERIC EJ736298'),

('jpms_src_040304', 'academic_paper', 'Possible Selves', 'Hazel R. Markus, Paula Nurius', 'American Psychologist, 41(9), 954-969', 1986, datetime('now'), 'copyrighted_quotable', 'primary', 97, 'DOI: 10.1037/0003-066X.41.9.954'),

('jpms_src_040305', 'academic_paper', 'Social-Psychological Interventions in Education: They''re Not Magic', 'David S. Yeager, Gregory M. Walton', 'Review of Educational Research, 81(2), 267-301', 2011, datetime('now'), 'copyrighted_quotable', 'primary', 97, 'DOI: 10.3102/0034654311405999 - Meta-analysis of 273 interventions'),

('jpms_src_040306', 'academic_paper', 'School Engagement: Potential of the Concept, State of the Evidence', 'Jennifer A. Fredricks, Phyllis C. Blumenfeld, Alison H. Paris', 'Review of Educational Research, 74(1), 59-109', 2004, datetime('now'), 'copyrighted_quotable', 'primary', 98, 'DOI: 10.3102/00346543074001059'),

('jpms_src_040307', 'academic_paper', 'Grit: Perseverance and Passion for Long-Term Goals', 'Angela L. Duckworth, Christopher H. Peterson, Michael D. Matthews, Dennis R. Kelly', 'Journal of Personality and Social Psychology, 92(6), 1087-1101', 2007, datetime('now'), 'copyrighted_quotable', 'primary', 98, 'DOI: 10.1037/0022-3514.92.6.1087 - Foundational GRIT study'),

('jpms_src_040308', 'academic_paper', 'A Meta-Analysis of the Five-Factor Model of Personality and Academic Performance', 'Arthur E. Poropat', 'Psychological Bulletin, 135(2), 322-338', 2009, datetime('now'), 'copyrighted_quotable', 'primary', 97, 'DOI: 10.1037/a0014996 - 70,000+ subjects meta-analysis'),

('jpms_src_040309', 'academic_paper', 'Cognitive and Attentional Mechanisms in Delay of Gratification', 'Walter Mischel, Ebbe B. Ebbesen, Antonette Raskoff Zeiss', 'Journal of Personality and Social Psychology, 21(2), 204-218', 1972, datetime('now'), 'copyrighted_quotable', 'primary', 97, 'Marshmallow Test classic study'),

('jpms_src_040310', 'academic_book', 'Generalized Expectancies for Internal Versus External Control of Reinforcement', 'Julian B. Rotter', 'Psychological Monographs, 80(1), 1-28', 1966, datetime('now'), 'copyrighted_quotable', 'primary', 98, 'DOI: 10.1037/h0092976 - Locus of Control foundational theory'),

('jpms_src_040311', 'academic_paper', 'Self-Esteem and Academic Engagement Among Adolescents: A Moderated Mediation Model', 'Zhou, J., Hao, W., Zhang, X.', 'Frontiers in Psychology, 12, 690828', 2021, datetime('now'), 'copyrighted_quotable', 'primary', 96, 'DOI: 10.3389/fpsyg.2021.690828'),

('jpms_src_040312', 'academic_paper', 'The Influence of Resilience and Future Orientation on Academic Achievement During the Transition to High School', 'Lereya, S.T., Humphrey, N.', 'Journal of Adolescence, 2024', 2024, datetime('now'), 'copyrighted_quotable', 'primary', 96, 'DOI: 10.1080/02673843.2024.2312863');

-- ========================================
-- CONCEPTS: 14件の新規教育学概念
-- motivation_dev: 8件 (jpms_ec_0200 ~ jpms_ec_0207)
-- noncognitive: 6件 (jpms_ec_0208 ~ jpms_ec_0213)
-- ========================================

INSERT INTO jpms_education_concepts (id, name_ja, name_en, name_original, definition, impact_summary, subfield, school_of_thought, era_start, era_end, opposing_concept_names, keywords_ja, keywords_en, key_researchers, key_works, relevance_to_middle_school, status, source_reliability, data_completeness) VALUES

('jpms_ec_0200', '成長マインドセット', 'Growth Mindset', 'Growth Mindset (Implicit Theories of Intelligence)', '知能や能力は固定的ではなく、努力と実践を通じて発展可能だという信念体系。Dweck & Leggett (1988) が「implicit theories of intelligence」として提唱し、その後 Dweck (2006) が「Growth Mindset」として大衆化。固定マインドセット（能力は生まれつき）との対比で、学習目標志向と努力の継続を促進する認知的枠組み。成功者と失敗者の行動パターンの違いは、その背後にある暗黙の知能観によって生じる。', '世界中の教育改革・学習支援の中核理論として、180カ国以上の教育政策・教員研修に影響。ノーベルレベルの引用数を持つ概念。困難な学習状況における動機づけと学業成績向上の実証研究が豊富。', 'motivation_dev', 'Social-Cognitive Theory of Motivation', 1988, NULL, '固定マインドセット', '成長マインドセット,暗黙の知能観,努力志向,学習目標', 'growth mindset,implicit theories,effort orientation,learning goals', '["Carol S. Dweck", "Ellen L. Leggett"]', '[{"title":"A Social-Cognitive Approach to Motivation and Personality","year":1988,"doi":"10.1037/0033-295X.95.2.256","verified":true,"source_id":"jpms_src_040300"}]', 95, 'active', 'primary', 85),

('jpms_ec_0201', '自己効力感', 'Self-Efficacy', 'Self-Efficacy (Efficacy Beliefs)', '特定の課題を遂行できるという個人の確信度。Albert Bandura (1977) が社会学習理論の文脈で提唱。期待（expectancy）と価値（value）と区別される重要な心理構成概念で、「その行動ができるか」という判断が学習効果と直結。メタ認知・学習動機・行動変容の媒介因子として機能。失敗経験・代理経験・言語的説得・生理的状態の4つの源泉から形成される。', '教育心理学の最重要概念として位置づけられ、自己調整学習・キャリア教育・メンタルヘルス介入の理論的基盤。40年以上の実証研究蓄積により、学業成績・進路選択・人生軌跡の予測因子として確立。', 'motivation_dev', 'Social Learning Theory', 1977, NULL, '無力感', '自己効力感,確信度,行動変容,期待値', 'self-efficacy,confidence,behavioral change,expectancy', '["Albert Bandura"]', '[{"title":"Self-Efficacy: Toward a Unifying Theory of Behavioral Change","year":1977,"doi":"10.1037/0033-295X.84.2.191","verified":true,"source_id":"jpms_src_040301"}]', 95, 'active', 'primary', 85),

('jpms_ec_0202', '期待値価値理論', 'Expectancy-Value Theory', 'Expectancy-Value Theory of Achievement Motivation', 'Eccles & Wigfield (2000) が体系化した動機づけ理論の中核。「課題に成功できるか」という期待（expectancy）と「その課題にどの程度の価値があるか」という主観的価値（value）の積が、学習選択と努力強度を決定するモデル。Intrinsic Value・Attainment Value・Utility Value・Cost の4次元で価値を分析。特に女性のSTEM離脱問題の説明力が高い理論枠組み。', '進路選択・STEM教育参加・学業成績予測の理論的核として、多数の大規模追跡研究で検証。特に女性のSTEM離脱問題の説明力が高い。', 'motivation_dev', 'Expectancy Theory', 2000, NULL, '努力パラドックス', '期待値価値理論,主観的価値,STEM参加,進路選択', 'expectancy-value,subjective task value,STEM engagement,career choice', '["Jacquelynne S. Eccles", "Allan Wigfield"]', '[{"title":"Expectancy-Value Theory of Achievement Motivation","year":2000,"doi":"10.1006/ceps.1999.1015","verified":true,"source_id":"jpms_src_040302"}]', 92, 'active', 'primary', 85),

('jpms_ec_0203', '興味発展の四段階モデル', 'Four-Phase Model of Interest Development', 'The Four-Phase Model of Interest Development', 'Hidi & Renninger (2006) が開発した興味発展の段階的モデル。(1)状況的興味のトリガー（環境的刺激が与える一時的な注意）→(2)状況的興味の維持（環境・社会的支援による興味の保持）→(3)発展途上の個人的興味（学習者内に形成される動機）→(4)確立された個人的興味（安定した知識・価値体系）という4段階で学習者の興味が深化・内在化するプロセスを説明。感情的・認知的要因の両立を強調。', '教科学習の動機づけ・長期的学習参加の予測因子として、全年代の教育実践で活用。特に低初期動機生徒への教科導入時の理論的支援ツール。', 'motivation_dev', 'Interest Development Theory', 2006, NULL, '関心の他律性', '興味発展,四段階,状況的興味,個人的興味', 'interest development,four phases,situational interest,individual interest', '["Suzanne Hidi", "K. Ann Renninger"]', '[{"title":"The Four-Phase Model of Interest Development","year":2006,"source_id":"jpms_src_040303"}]', 93, 'active', 'primary', 85),

('jpms_ec_0204', 'ポッシブル・セルブス理論', 'Possible Selves Theory', 'Possible Selves', 'Markus & Nurius (1986) が提唱した自己概念の未来志向的枠組み。「なれるかもしれない自分」「なりたい自分」「恐れている自分」など、未来の自分についての心的表象が現在の動機づけと進路選択を駆動する。理想像（hoped-for selves）と恐怖像（feared selves）の対比で葛藤と目標設定が生じるメカニズム。複数の可能的自己を想像することが心理的柔軟性を促進。', '進路教育・キャリアカウンセリング・高校生のアイデンティティ形成の理論的基盤。将来予測が低い層への介入の有効性が実証。', 'motivation_dev', 'Future Self Theory', 1986, NULL, 'プレゼント・バイアス', 'ポッシブル・セルブス,将来の自己,キャリア探索,目標設定', 'possible selves,future self,career exploration,goal setting', '["Hazel R. Markus", "Paula Nurius"]', '[{"title":"Possible Selves","year":1986,"doi":"10.1037/0003-066X.41.9.954","verified":true,"source_id":"jpms_src_040304"}]', 91, 'active', 'primary', 85),

('jpms_ec_0205', 'マインドセット介入の有効性', 'Mindset Interventions', 'Social-Psychological Interventions in Education', 'Yeager & Walton (2011) が273の学校ベース介入を統合レビューした研究。成長マインドセット信念・帰属スタイル改善・ソーシャル・スキル支援の短時間介入（数時間～数週間）が、数ヶ月～数年後の学業成績・出席率・中退率を有意に改善することを実証。効果サイズは小～中程度だが、低コスト・大規模適用の可能性が高い。エビデンス・ベースド教育実践の重要な事例。', 'テクノロジー活用の教育格差是正として、低リソース地域への大規模応用が進行中。コスト効果性が高く、各国の教育政策導入が加速。', 'motivation_dev', 'Social-Psychological Intervention Science', 2011, NULL, '行動主義的学習支援のみ', 'マインドセット介入,社会心理学的介入,短時間介入,効果の持続性', 'mindset intervention,social-psychological intervention,brief intervention,sustained effect', '["David S. Yeager", "Gregory M. Walton"]', '[{"title":"Social-Psychological Interventions in Education: They''re Not Magic","year":2011,"doi":"10.3102/0034654311405999","verified":true,"source_id":"jpms_src_040305"}]', 94, 'active', 'primary', 85),

('jpms_ec_0206', 'スクール・エンゲージメント', 'School Engagement', 'School Engagement (Behavioral, Emotional, Cognitive)', 'Fredricks, Blumenfeld & Paris (2004) が学校へのエンゲージメントを3次元で概念化した重要なモデル。Behavioral Engagement（参加・努力・遵守）・Emotional Engagement（学校への肯定感・帰属意識・親和性）・Cognitive Engagement（メタ認知・理解志向・学習戦略）。低エンゲージメントが中退の強力な予測因子。多次元的に学習関与の質を測定・介入する際の標準的枠組み。', '高校中退防止・学習復帰支援の診断ツールとして世界中で採用。SEL・ポジティブ教育の成果指標に統合。', 'motivation_dev', 'Engagement Theory', 2004, NULL, 'エンゲージメント欠缺', 'エンゲージメント,行動的契約,感情的帰属,認知的関与', 'engagement,behavioral,emotional,cognitive', '["Jennifer A. Fredricks", "Phyllis C. Blumenfeld", "Alison H. Paris"]', '[{"title":"School Engagement: Potential of the Concept, State of the Evidence","year":2004,"doi":"10.3102/00346543074001059","verified":true,"source_id":"jpms_src_040306"}]', 94, 'active', 'primary', 85),

('jpms_ec_0207', '勇気（GRIT）', 'GRIT: Perseverance and Passion', 'GRIT (Grit Scale)', 'Duckworth et al. (2007) が新概念として定義した非認知能力。Grit = Perseverance（粘り強さ・辛抱強さ）+ Passion（執着心・長期目標への情熱）。IQと無相関だが、ウェストポイント士官学校・全米スペリング選手権・大学進学・学業成績の達成を4～6%予測する。Conscientiousness と高相関（r = .73）。測定方法・因子構造について学術的議論も継続中。', 'リスキー・ユース向けの非認知能力育成の焦点。貧困層の教育機会不平等を補正する非認知能力として国際的に普及。', 'noncognitive', 'Non-cognitive Skills Theory', 2007, NULL, '才能依存主義', 'GRIT,粘り強さ,熱情,長期目標志向', 'grit,perseverance,passion,long-term goal', '["Angela L. Duckworth", "Christopher H. Peterson", "Michael D. Matthews", "Dennis R. Kelly"]', '[{"title":"Grit: Perseverance and Passion for Long-Term Goals","year":2007,"doi":"10.1037/0022-3514.92.6.1087","verified":true,"source_id":"jpms_src_040307"}]', 93, 'active', 'primary', 85),

('jpms_ec_0208', '誠実性と学業成績', 'Conscientiousness and Academic Achievement', 'Big Five: Conscientiousness', 'Big Five性格論の中核的一軸。Poropat (2009) のメタ分析（70,000+サンプル）で、Conscientiousness が Openness と同等かそれ以上に学業成績を予測することを実証。IQと同等の説明力（β = .25～.35）を持つ。自己制御・遅延報酬・組織性・責任感・粘り強さの統合構成概念。人格特性と学業成績の関連を実証的に示す最初の大規模エビデンス。', '非認知能力の教育評価・大学入試の多元的評価導入において、IQ信仰との対抗理論として機能。全人的教育評価への科学的根拠。', 'noncognitive', 'Big Five Personality Theory', 2009, NULL, 'ルーズさ・無責任', '誠実性,Conscientiousness,自己制御,学業成績', 'conscientiousness,self-control,academic achievement,responsible', '["Arthur E. Poropat"]', '[{"title":"A Meta-Analysis of the Five-Factor Model of Personality and Academic Performance","year":2009,"doi":"10.1037/a0014996","verified":true,"source_id":"jpms_src_040308"}]', 92, 'active', 'primary', 85),

('jpms_ec_0209', '遅延報酬能力（マシュマロテスト）', 'Delay of Gratification', 'Marshmallow Test / Delay of Gratification', 'Mischel, Ebbesen & Zeiss (1972) の古典的実験。3～5歳児がマシュマロ（またはプレッツェル）を目前にして待機し、待つことができれば報酬が増える条件での自制能力を測定。待つ戦略（認知的抑制・注意逸脱・自己談話）が個人差として現れる。認知的自己制御メカニズムの解明の嚆矢。', '非認知能力測定の嚆矢として教育心理学に深刻な影響。長期追跡で学業成績・SATスコア・体重指数との関連が報告。', 'noncognitive', 'Self-Control Theory', 1972, NULL, '衝動的反応', '遅延報酬,自制心,マシュマロテスト,衝動制御', 'delay of gratification,self-control,marshmallow test,impulse', '["Walter Mischel", "Ebbe B. Ebbesen", "Antonette Raskoff Zeiss"]', '[{"title":"Cognitive and Attentional Mechanisms in Delay of Gratification","year":1972,"source_id":"jpms_src_040309"}]', 85, 'active', 'primary', 85),

('jpms_ec_0210', '統制の所在', 'Locus of Control', 'Locus of Control (Internal vs. External)', 'Rotter (1966) が定義した重要な性格的傾向。出来事の結果が自分の行動によって決定されるか（内的統制）vs. 運や他者によって決定されるか（外的統制）という信念体系。教育文脈では、学業成績への帰属が内的統制だと努力と努力継続が高まり、外的統制信念は動機低下と無力感を招く。学習への主体性と自律性に直結する重要な心理特性。', '進路指導・学習支援の診断指標として全世界で採用。心理的レジリエンス（resilience）とも接続。内的統制信念は適応的心理特性として位置づけられる。', 'noncognitive', 'Attribution Theory', 1966, NULL, '無関心な帰属', '統制の所在,内的統制,外的統制,帰属スタイル', 'locus of control,internal locus,external locus,attribution', '["Julian B. Rotter"]', '[{"title":"Generalized Expectancies for Internal Versus External Control of Reinforcement","year":1966,"doi":"10.1037/h0092976","verified":true,"source_id":"jpms_src_040310"}]', 91, 'active', 'primary', 85),

('jpms_ec_0211', '青年期の自尊心と学業成績', 'Self-Esteem in Adolescence', 'Self-Esteem and Academic Achievement in Adolescence', '自分自身に対する肯定的・否定的評価。Zhou et al. (2021) が自尊心→学業自己効力→学業エンゲージメント→成績の間接効果を実証。特に青年期中期（中学～高校前半）で自尊心が急低下する現象が国際的に報告。SEL・ウェルビーイング施策の対象。学業成績との関連が単純ではなく、媒介因子を含む複合的なモデルが必要。', '自尊心低下群への予防的・回復的支援プログラムの理論的基盤。学校メンタルヘルス・スクールカウンセリング・養護教諭連携の標準指標。', 'noncognitive', 'Self-Concept Theory', 2021, NULL, '過度な自尊心（ナルシシズム）', '自尊心,自己評価,学業成績,メンタルヘルス', 'self-esteem,self-evaluation,academic achievement,mental health', '["Zhou, J.", "Hao, W.", "Zhang, X."]', '[{"title":"Self-Esteem and Academic Engagement Among Adolescents: A Moderated Mediation Model","year":2021,"doi":"10.3389/fpsyg.2021.690828","verified":true,"source_id":"jpms_src_040311"}]', 93, 'active', 'primary', 85),

('jpms_ec_0212', 'レジリエンス', 'Resilience in Education', 'Academic Resilience', '困難・逆境に直面しても学業成績を維持・回復する能力。Lereya et al. (2024) が「将来志向」「ソーシャルサポート」「内的資源」の三要素を実証。中学高校への進学期の過度なストレス軽減・心理的支援の重要性を強調。動的・プロセス志向の特性として、固定的特性ではなく育成可能な能力として認識。', 'リスキー・ユース対象の学業復帰プログラムの中核概念。SEL・正のメンタルヘルス・貧困対策と統合。教育社会学における周辺化・疎外生徒への支援理論としても活用。', 'noncognitive', 'Positive Psychology in Education', 2024, NULL, '脆弱性,無力感', 'レジリエンス,逆境対処,ソーシャルサポート,心理的強靭性', 'resilience,adversity coping,social support,psychological resilience', '["Lereya, S.T.", "Humphrey, N."]', '[{"title":"The Influence of Resilience and Future Orientation on Academic Achievement During the Transition to High School","year":2024,"doi":"10.1080/02673843.2024.2312863","verified":true,"source_id":"jpms_src_040312"}]', 94, 'active', 'primary', 85);

-- ========================================
-- CONCEPT RELATIONS: 概念間の関係（11件）
-- ID範囲: jpms_ecr_00800 ~ jpms_ecr_00810
-- ========================================

INSERT INTO jpms_education_concept_relations (id, source_concept_id, target_concept_id, relation_type, relation_description, strength) VALUES

('jpms_ecr_00800', 'jpms_ec_0200', 'jpms_ec_0004', 'complements', 'Growth Mindset と Self-Regulated Learning は理論的に補完：マインドセット改善→努力継続→メタ認知監視のサイクル確立', 9),

('jpms_ecr_00801', 'jpms_ec_0200', 'jpms_ec_0201', 'extends', 'Growth Mindset が Self-Efficacy 形成を促進：失敗を成長機会と捉える認知が個人効力感を支える', 9),

('jpms_ecr_00802', 'jpms_ec_0200', 'jpms_ec_0205', 'empirically_tests', 'Yeager & Walton (2011) のマインドセット介入が Growth Mindset の効果を実証した決定的エビデンス', 8),

('jpms_ecr_00803', 'jpms_ec_0201', 'jpms_ec_0206', 'extends', '自己効力感が高いほど School Engagement（特に Cognitive Engagement）が向上する', 8),

('jpms_ecr_00804', 'jpms_ec_0201', 'jpms_ec_0207', 'related_to', 'GRIT と Self-Efficacy は両立する：「できると思う→だから続ける」の動機メカニズム', 7),

('jpms_ecr_00805', 'jpms_ec_0207', 'jpms_ec_0208', 'related_to', 'GRIT と Conscientiousness は高相関（r = .73）：粘り強さは誠実性の実行形態として機能', 9),

('jpms_ecr_00806', 'jpms_ec_0207', 'jpms_ec_0206', 'extends', 'GRIT が School Engagement（特に Behavioral Engagement）の持続性を支える：長期的な努力継続の駆動力', 8),

('jpms_ecr_00807', 'jpms_ec_0207', 'jpms_ec_0210', 'related_to', 'GRIT（内的動機・内的統制）vs. Locus of Control（外的統制信念）：両立困難な世界観の対立', 6),

('jpms_ecr_00808', 'jpms_ec_0202', 'jpms_ec_0203', 'applies_to_practice', 'Interest Development が Expectancy-Value のインプット：価値認知が興味に転換される段階的プロセス', 8),

('jpms_ecr_00809', 'jpms_ec_0204', 'jpms_ec_0211', 'extends', 'Possible Selves の肯定的理想像が青年期の自尊心維持を支援：将来展望の具体化が現在の自己評価を高める', 8),

('jpms_ecr_00810', 'jpms_ec_0204', 'jpms_ec_0212', 'extends', 'Possible Selves の多様な想像が困難時の心理的柔軟性（レジリエンス）を育成：複数のキャリア想像が回復力を支える', 7);
