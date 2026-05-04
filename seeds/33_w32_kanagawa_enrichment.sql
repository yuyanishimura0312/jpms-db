-- ========================================================================
-- JPMS-DB Phase 2 W32: Kanagawa Key Schools Enrichment
-- Enhancement of founding philosophy and education principles
-- Plus curriculum characteristics for 10 major schools
-- ========================================================================

-- ============================================================
-- UPDATE jpms_schools: Founding Philosophy & Education Principles
-- ============================================================

-- jpms_s_0136: 栄光学園中学校
UPDATE jpms_schools 
SET founding_philosophy = 'イエズス会の標語「AD MAIOREM DEI GLORIAM（より大いなる神の栄光のために）」に基づき、カトリック信仰に根ざした人格教育を重視。心身の成長を重視しながら、世界に通用するリーダーシップを持つ人材の育成を目指す。',
    education_principle = '「他者のために、他者とともに（Men for others, with others）」という理念の下、自己の成長と社会への貢献を両立させる人格を培う。知識の獲得だけでなく、道徳性と実践力を兼ね備えた世界市民の養成を教育の本質とする。'
WHERE id = 'jpms_s_0136';

-- jpms_s_0121: 聖光学院中学校
UPDATE jpms_schools 
SET founding_philosophy = 'キリスト教（カトリック）の教えを根幹とし、「紳士たれ（Be Gentlemen）」という人格教育の理想を掲げる。Christian Brothers の伝統を受け継ぎ、品性の向上と信仰的な人格形成を教育の核心とする。',
    education_principle = '聖フランシスコ・ザビエルの遺志を受け継ぎ、学問と品性の調和を目指す。生徒一人ひとりが自らの潜在能力を開発し、社会への責任感を持った自立した人間へ成長することを教育目標とする。'
WHERE id = 'jpms_s_0121';

-- jpms_s_0122: 浅野中学校
UPDATE jpms_schools 
SET founding_philosophy = '創立者浅野總一郎が欧米視察で感銘を受けた企業人育成の精神を教育に生かし、教養主義に陥らない幅広い知識と実践的指導力の習得を目的とした革新的な教育機関として創立。校訓「愛と和」と「九転十起」を精神的支柱とする。',
    education_principle = '「自主独立の精神、義務と責任の自覚、高い品位と豊かな情操を具えた、心身ともに健康で、創造的な能力を持つ、逞しい人間の育成」を教育目標とする。文武両道を実践し、バランスの取れた人格形成を重視する。'
WHERE id = 'jpms_s_0122';

-- jpms_s_0123: フェリス女学院中学校
UPDATE jpms_schools 
SET founding_philosophy = '1870年、アメリカ人女性宣教師メアリー・E・キダーによる「For Others」の教えを根本とし、キリスト教に基づく女子教育の先駆けとして創立。豊かな知性と教養を備えた自由で自立した女性の育成を使命とする。',
    education_principle = 'キリスト教教育の価値観の下、知的成長と人格形成を重視し、六年間の一貫教育を通じて、社会に貢献できる自主性のある女性の育成を目指す。他者への思慮深さと責任感を備えた世界市民の育成に注力する。'
WHERE id = 'jpms_s_0123';

-- jpms_s_0124: 横浜共立学園中学校
UPDATE jpms_schools 
SET founding_philosophy = '1871年、アメリカ人女性宣教師によって創立され、「主を畏れることは知恵のはじめ」および隣人愛の聖書的価値観を根幹とするプロテスタント女子教育。一人ひとりが神に愛されていることを知り、隣人愛に基づいた人格形成を重視。',
    education_principle = '自分を愛するように隣人を愛し、敬うことのできる心を育てながら、一人の人間として自立するために必要な知識・技術を磨く。世界の平和のために考えて行動できる女性の育成を、六年間の一貫教育で実現する。'
WHERE id = 'jpms_s_0124';

-- jpms_s_0125: 横浜雙葉中学校
UPDATE jpms_schools 
SET founding_philosophy = 'カトリック信仰に基づき、校訓「徳においては純真に義務においては堅実に」を教育の根本とする。17世紀フランスの修道会の伝統を受け継ぎ、社会への奉仕と自己犠牲の精神を建学の理念とする。',
    education_principle = '包括的な能力の開発を学校活動と学習を通じて実現し、カトリック教育の伝統の下で人格の完成を目指す。小規模だからこそ実現できる個別対応の教育と、修道会の精神に基づいた思いやりのある人間形成を重視。'
WHERE id = 'jpms_s_0125';

-- jpms_s_0146: 湘南白百合学園中学校
UPDATE jpms_schools 
SET founding_philosophy = 'キリストの愛の教えに基づく全人教育を通して、社会に貢献できる子女を育成する。カトリック精神に根ざし、三つの校訓「従順（真の自由を生きるよろこび）」「勤勉（能力をみがき役立てるよろこび）」「愛徳（互いに大切にし合うよろこび）」を日常実践。',
    education_principle = '聖書に示される価値観を指針として、中高一貫の女子教育を実施。将来社会貢献できる愛ある人への成長を目指し、勉学に励み自らを磨く。学園での6年間を通じて、信仰と学問を統合した総合的な人格発展を実現。'
WHERE id = 'jpms_s_0146';

-- jpms_s_0141: 洗足学園中学校
UPDATE jpms_schools 
SET founding_philosophy = '新約聖書のキリストの教え「たがいに足を洗え」に由来し、謙虚にして慈愛に満ちた心をもち、社会に奉仕貢献できる人材を育成することを基本理念とする。キリスト教の感謝と献身、犠牲と奉仕の精神を学園教育の中心に位置づけ。',
    education_principle = '中等教育の最大の使命は人格育成であり、正しい価値観に基づいた判断基準を有し、高邁な意志を抱く人物の育成を目指す。自立・挑戦・奉仕・幸福な自己実現という4つの人物像を育てることで、社会で役立つ理想を実現していく能力を涵養する。'
WHERE id = 'jpms_s_0141';

-- jpms_s_0132: サレジオ学院中学校
UPDATE jpms_schools 
SET founding_philosophy = 'カトリックのサレジオ会の教育母体として、創立者ヨハネ・ボスコの「信」「愛」「理」を根本理念とする。「25歳の男づくり」を掲げ、高校卒業時ではなく社会人としての基礎を形成する長期的視点での人格育成を志向。',
    education_principle = '「教育共同体の実現」「ともに居ること（アシステンツァ）」の精神の下、生徒一人ひとりに教師の目が行き届く家庭的な雰囲気を大切にする。変革できる人間の形成と、家庭・学校の共同体としての協力体制を通じ、社会に貢献できる男性人材を育成。'
WHERE id = 'jpms_s_0132';

-- jpms_s_0130: 神奈川大学附属中学校
UPDATE jpms_schools 
SET founding_philosophy = '「教育は人を造るにあり」という創立理念の下、「質実剛健」「積極進取」「中正堅実」の三つの原則を建学の精神とする。大学附属校として、継続的な学びと実践を通じ、社会に貢献できる人材育成を目標。',
    education_principle = '学問と実践のバランスを重視し、知識習得だけでなく、経験を通じた人格の成長を促進する。グローバルな視野と日本文化の理解を兼ね備え、自立的かつ創造的に行動できる人間の育成を六年間の一貫教育で実現。'
WHERE id = 'jpms_s_0130';

-- ============================================================
-- INSERT jpms_school_curriculum: Curriculum Characteristics
-- ============================================================

INSERT INTO jpms_school_curriculum (school_id, inquiry_learning, steam, pbl, international_track, ict_strength, art_strength, sports_strength, source_id) VALUES 
('jpms_s_0136', 2, 2, 1, 3, 2, 2, 3, 'jpms_src_030206'),  -- 栄光学園
('jpms_s_0121', 2, 2, 1, 3, 2, 2, 3, 'jpms_src_030207'),  -- 聖光学院
('jpms_s_0122', 2, 1, 2, 2, 2, 2, 3, 'jpms_src_030203'),  -- 浅野
('jpms_s_0123', 2, 1, 1, 3, 2, 3, 2, 'jpms_src_030208'),  -- フェリス女学院
('jpms_s_0124', 2, 1, 1, 3, 2, 3, 2, 'jpms_src_030209'),  -- 横浜共立学園
('jpms_s_0125', 2, 1, 1, 2, 2, 2, 2, 'jpms_src_030202'),  -- 横浜雙葉
('jpms_s_0146', 2, 1, 1, 2, 2, 3, 2, 'jpms_src_030202'),  -- 湘南白百合学園
('jpms_s_0141', 2, 1, 1, 2, 2, 3, 3, 'jpms_src_030210'),  -- 洗足学園
('jpms_s_0132', 2, 2, 2, 2, 2, 2, 3, 'jpms_src_030202'),  -- サレジオ学院
('jpms_s_0130', 2, 2, 2, 2, 3, 2, 2, 'jpms_src_030202');  -- 神奈川大学附属

-- Scale: 0=none/minimal, 1=basic, 2=moderate, 3=strong/advanced
-- inquiry_learning: 主体的学習, steam: STEAM教育, pbl: プロジェクト型学習, 
-- international_track: 国際コース/プログラム, ict_strength: ICT活用, 
-- art_strength: 美術・音楽教育, sports_strength: 運動部活動
