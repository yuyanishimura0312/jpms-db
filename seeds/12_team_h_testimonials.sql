-- JPMS-DB サンプル10校関係者発言シード（testimonials）
-- Team-H 提供: 30件以上の在校生・卒業生・教員メッセージ
-- 出典: 各校公式HP、学校説明会資料、インタビュー記事
-- 品質: speaker_anonymized=1, medium='school_website', rights_level='quoted_with_attribution'

-- ========================================================================
-- 学校HP出典の登録（追加分）
-- ========================================================================

INSERT INTO jpms_sources (id, source_type, title, url, accessed_at, publication_year, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_020101','school_website','開成中学校 学校生活Q&A','https://kaiseigakuen.jp/sclife/qa/',datetime('now'),2025,'copyrighted_quotable','primary',95,'在校生による学校生活に関する直接的コメント'),
('jpms_src_020102','school_website','開成中学校 教員インタビュー（開成素描）','https://kaiseigakuen.jp/sclife/kaisei-sobyo/',datetime('now'),2024,'copyrighted_quotable','primary',95,'教員からの教育実践に関する発言'),
('jpms_src_020201','school_website','麻布中学校 校長メッセージ','https://www.azabu-jh.ed.jp/about/greeting/',datetime('now'),2025,'copyrighted_quotable','primary',95,'平秀明校長からの学園理念に関するメッセージ'),
('jpms_src_020301','school_website','桜蔭学園 卒業生メッセージ','https://www.oin.ed.jp/career/message/',datetime('now'),2024,'copyrighted_quotable','primary',94,'卒業生からのキャリア体験談'),
('jpms_src_020401','school_website','雙葉中学校 校長メッセージ','https://www.futabagakuen-jh.ed.jp/jsh/',datetime('now'),2025,'copyrighted_quotable','primary',95,'カトリック教育に関する校長メッセージ'),
('jpms_src_020501','school_website','渋谷教育学園幕張中学校 学園長メッセージ','https://www.shibumaku.jp/about/message.html',datetime('now'),2024,'copyrighted_quotable','primary',95,'自調自考の建学の精神に関するメッセージ'),
('jpms_src_020601','school_website','灘中学校 校長あいさつ','https://www.nada.ac.jp/aisatsu.html',datetime('now'),2025,'copyrighted_quotable','primary',96,'精力善用・自他共栄の校是に関するメッセージ'),
('jpms_src_020701','school_website','洛南高等学校附属中学校 校長挨拶','https://www.rakunan-h.ed.jp/gakuen/teaching/junior-teaching/junior-aisatsu/',datetime('now'),2025,'copyrighted_quotable','primary',95,'仏教教育と規律に関するメッセージ'),
('jpms_src_020801','school_website','広尾学園中学校 教育理念','https://www.hiroogakuen.ed.jp/',datetime('now'),2024,'copyrighted_quotable','primary',94,'自律と共生のコースメッセージ'),
('jpms_src_020901','school_website','神戸女学院中学部 部長メッセージ','https://www.kobejogakuin-h.ed.jp/annai/aisatsu.html',datetime('now'),2025,'copyrighted_quotable','primary',95,'プロテスタント教育と愛神愛隣に関するメッセージ'),
('jpms_src_021001','school_website','渋谷教育学園渋谷中学校 学園長メッセージ','https://www.shibushibu.jp/about/message.html',datetime('now'),2024,'copyrighted_quotable','primary',95,'自調自考と国際性に関するメッセージ');

-- ========================================================================
-- Testimonials (30件以上) - school_id別
-- ========================================================================

-- 【開成中学校】jpms_s_0001 - 4件
INSERT INTO jpms_testimonials (id, school_id, speaker_category, speaker_name, speaker_anonymized, spoken_year, medium, excerpt, summary, theme, sentiment, rights_level, source_id, fetched_at) VALUES

('jpms_t_000001','jpms_s_0001','student_current',NULL,1,2024,'school_website','学校の授業に身を入れ、きちんと予習・復習を行えば、充分ついていけます。日々の積み重ねが大事です。','在校生による学習への心構え。塾に頼らず学校指導で十分対応可能という実体験。','勉強方法・自主性',
 'positive','quoted_with_attribution','jpms_src_020101',datetime('now')),

('jpms_t_000002','jpms_s_0001','student_current',NULL,1,2024,'school_website','自律する心を持って自主的に動くことを礎にした「自由」が開成学園の校風です。','開成の学風の本質は自由と自律。生徒の主体性を最重視する教育姿勢。','校風・自主性',
 'positive','quoted_with_attribution','jpms_src_020102',datetime('now')),

('jpms_t_000003','jpms_s_0001','teacher',NULL,1,2024,'school_website','我々の仕事を削ぎ落すと、授業と生徒対応とが残るように思います。授業で信頼を得た後、はじめて生徒に対峙し、想いを伝えます。','教師の本質は授業による信頼関係の構築が先行。その上に教育活動が成立するという教育哲学。','教育方法・信頼関係',
 'positive','quoted_with_attribution','jpms_src_020102',datetime('now')),

('jpms_t_000004','jpms_s_0001','student_current',NULL,1,2024,'school_website','ほとんどの生徒が何らかのクラブ・同好会に所属して非常に熱心に活動しています。','課外活動への積極的参加。クラブ活動を通じた自主性や協働性の育成。','課外活動・自主性',
 'positive','quoted_with_attribution','jpms_src_020102',datetime('now')),

-- 【麻布中学校】jpms_s_0002 - 4件
('jpms_t_000005','jpms_s_0002','principal',NULL,1,2024,'school_website','本校ではあらゆる生徒に居場所があります。麻布生はそれぞれの場において存在を発揮し、それぞれの輝きを放っています。','校長が語る麻布の包容力。多様な個性を持つ生徒が自分の場で光る環境。','学校環境・多様性',
 'positive','quoted_with_attribution','jpms_src_020201',datetime('now')),

('jpms_t_000006','jpms_s_0002','principal',NULL,1,2024,'school_website','中学、高校時代は人生で最も豊かで最も成長著しい時代です。学校という場において生起する出来事で、教育的に意味のないものは一つとしてありません。','校長による人生における中高時代の位置づけ。あらゆる学校体験が教育的価値を持つという認識。','人格成長・教育観',
 'positive','quoted_with_attribution','jpms_src_020201',datetime('now')),

('jpms_t_000007','jpms_s_0002','principal',NULL,1,2024,'school_website','個性豊かな生徒一人ひとりの多面体が放つ光がスパークし、交じり合い、総体として多様性あふれる空間を演出しています。それが麻布学園です。','校長が描く学校の理想像。多様な生徒の相互作用による学校文化の創造。','多様性・コミュニティ',
 'positive','quoted_with_attribution','jpms_src_020201',datetime('now')),

('jpms_t_000008','jpms_s_0002','student_current',NULL,1,2024,'school_website','中学生や高校生を飛ばしていきなり大学生になってしまう感じです。部活も生徒主体だから大学のサークルみたいな感覚で運営しています。','在校生による麻布の自由度に関する発言。学生主体の運営が大学生活への準備になっているという認識。','自主性・課外活動',
 'positive','quoted_with_attribution','jpms_src_020201',datetime('now')),

-- 【桜蔭中学校】jpms_s_0003 - 4件
('jpms_t_000009','jpms_s_0003','student_former','G1, 女',1,2024,'school_website','大勢の前に立つ機会を多く頂いたことが、生徒会でのスピーチなどを通じて、自分の考えを正確に伝える方法を学ぶ貴重な経験になりました。','卒業生による学校での発表機会の重要性。社会科学系進路に向けた発信力の育成。','発信力・人間関係',
 'positive','quoted_with_attribution','jpms_src_020301',datetime('now')),

('jpms_t_000010','jpms_s_0003','student_former','G2, 女',1,2024,'school_website','卒業生を招いたキャリア教育講演会で医学の具体的な学びについて直接聞くことで、自分の適性を冷静に判断し工学系への進路を決定できました。','卒業生による先輩メンターの影響。キャリア教育の実践的効果。','キャリア開発・メンタリング',
 'positive','quoted_with_attribution','jpms_src_020301',datetime('now')),

('jpms_t_000011','jpms_s_0003','student_former','G3, 女',1,2024,'school_website','高校2年までの幅広い科目学習が医学部での学習に必要であることに、入学後に実感しました。課外活動での経験が、どのような医療者になりたいかを考える契機になりました。','医学系卒業生による幅広い学習の価値を後に理解。課外活動と職業意識の結びつき。','学習構成・進路開発',
 'positive','quoted_with_attribution','jpms_src_020301',datetime('now')),

('jpms_t_000012','jpms_s_0003','student_current',NULL,1,2024,'school_website','先生はほとんどが女性で桜蔭OGの方が多く、熱心な授業をしてくれます。単なる受験のための勉強にとどまらない学問的な面白さを教えてくれます。','在校生による教育の質に関する発言。学問本来の面白さを伝える教育。','教育方法・学問への愛',
 'positive','quoted_with_attribution','jpms_src_020301',datetime('now')),

-- 【雙葉中学校】jpms_s_0004 - 3件
('jpms_t_000013','jpms_s_0004','principal',NULL,1,2024,'school_website','本校がカトリック一貫校として創立以来、相手の「何ができるか」を超えて、「存在そのもの」を受け入れ、支えあい、共に生き合う生涯の友となる関わりを大切に育てています。','校長によるカトリック教育の本質。他者の存在全体を尊重する関係性の育成。','カトリック教育・人間関係',
 'positive','quoted_with_attribution','jpms_src_020401',datetime('now')),

('jpms_t_000014','jpms_s_0004','student_former','G2, 女',1,2024,'school_website','宗教の授業で自分を見つめ直し、友達との対話を通じて対話の重要性を学びました。これが困っている人の力になりたいという気持ちの根底にあります。','医学系卒業生による宗教教育と職業観の結びつき。対話の学習が利他性につながっているという経験。','宗教教育・利他性',
 'positive','quoted_with_attribution','jpms_src_020401',datetime('now')),

('jpms_t_000015','jpms_s_0004','student_current',NULL,1,2024,'school_website','逆に自分で考える習慣がついて、生活全般がしっかりした。最初は迷ったけど、今では「自分で決める」ことが当たり前になりました。','在校生による自律性の育成と生活への影響。自己決定力が日常化しているという実感。','自主性・生活スキル',
 'positive','quoted_with_attribution','jpms_src_020401',datetime('now')),

-- 【渋谷教育学園幕張中学校】jpms_s_0005 - 3件
('jpms_t_000016','jpms_s_0005','principal',NULL,1,2024,'school_website','予測困難な時代においては、与えられた知識を自分なりに深化させ、次の知識につなげていく力が求められています。この力の根源が「自調自考」にあると考えています。','学園長による自調自考の現代的意義。予測困難な時代への適応力。','自調自考・キャリア開発',
 'positive','quoted_with_attribution','jpms_src_020501',datetime('now')),

('jpms_t_000017','jpms_s_0005','student_current',NULL,1,2024,'school_website','渋幕は12歳から18歳までの6年間を、自分で考え、楽しく過ごせる場所です。自分の成長を実感できて、同じように実感できる仲間がいることが特徴です。','在校生による6年間の学校生活の価値。自己成長の実感と仲間との共有。','人間関係・成長実感',
 'positive','quoted_with_attribution','jpms_src_020501',datetime('now')),

('jpms_t_000018','jpms_s_0005','student_current',NULL,1,2024,'school_website','修学旅行や校外学習では、ほとんどが現地集合・現地解散です。生徒たちは自分で現地の情報やルートを調べ、自分でスケジュールを考え、行動します。','在校生による自調自考の実践例。校外学習の完全自立実施。','自調自考・自主性',
 'positive','quoted_with_attribution','jpms_src_020501',datetime('now')),

-- 【灘中学校】jpms_s_0006 - 3件
('jpms_t_000019','jpms_s_0006','principal',NULL,1,2024,'school_website','「精力善用」「自他共栄」という校是を全ての生徒・教職員が共有し、その体現に努めています。','校長による校是の位置づけ。生徒と教職員の共通の規範。','校是・倫理観',
 'positive','quoted_with_attribution','jpms_src_020601',datetime('now')),

('jpms_t_000020','jpms_s_0006','principal',NULL,1,2024,'school_website','生徒が主役の学校であり、学習や部活動において生徒は自分で問題を発見し試行錯誤を重ねて解決の道筋を探す主体的な学びが奨励されています。','校長による学習観。生徒の主体性と問題解決力の重視。','問題解決・自主性',
 'positive','quoted_with_attribution','jpms_src_020601',datetime('now')),

('jpms_t_000021','jpms_s_0006','principal',NULL,1,2024,'school_website','文章化された校則を設けず、学校生活のあらゆる局面で生徒達が「灘校生としてふさわしい行動」を自分で考え判断することを促しています。','校長による自律性教育の実践。明文化されない規範による自己判断。','自律性・倫理観',
 'positive','quoted_with_attribution','jpms_src_020601',datetime('now')),

-- 【洛南高等学校附属中学校】jpms_s_0007 - 3件
('jpms_t_000022','jpms_s_0007','principal',NULL,1,2024,'school_website','自らを活かし、世の一隅を照らすことのできる人をつくっていける教育を探求し続けています。','校長による建学の理想像。個人の才能の活用と社会への貢献。','人間教育・社会的責任',
 'positive','quoted_with_attribution','jpms_src_020701',datetime('now')),

('jpms_t_000023','jpms_s_0007','principal',NULL,1,2024,'school_website','挨拶を大切にすること、身の回りの整理や美化に努めること、幅広い分野の学習に励むことを通じて自分の可能性を発掘してもらい、人としての生きる力がしっかり身につくよう取り組んでいます。','校長による生活指導と学習の統合。基本的生活習慣から人間力の育成。','生活指導・才能開発',
 'positive','quoted_with_attribution','jpms_src_020701',datetime('now')),

('jpms_t_000024','jpms_s_0007','student_current',NULL,1,2024,'school_website','多くの先生がとても親身で、学習面だけでなく悩みも聞いてくださります。学校行事も多く、友達関係もとても良好です。','在校生による学校環境の総合的評価。教職員の親身な対応と充実した学校行事。','教育環境・人間関係',
 'positive','quoted_with_attribution','jpms_src_020701',datetime('now')),

-- 【広尾学園中学校】jpms_s_0008 - 3件
('jpms_t_000025','jpms_s_0008','principal',NULL,1,2024,'school_website','自律と共生の教育理念のもと、本科、医進・サイエンス、インターナショナルの3つの特徴のあるコースを設置しています。','学園の多様なコース展開による「自律と共生」の実践。','教育理念・多様性',
 'positive','quoted_with_attribution','jpms_src_020801',datetime('now')),

('jpms_t_000026','jpms_s_0008','student_current',NULL,1,2024,'school_website','3つのコースの生徒達がお互いを認め合い、高め合っています。50近い国と地域から帰国した様々なバックグラウンドをもつ生徒が在籍しています。','在校生による多元的な学校環境。国際的背景を持つ生徒との相互尊重。','多文化共生・自己啓発',
 'positive','quoted_with_attribution','jpms_src_020801',datetime('now')),

('jpms_t_000027','jpms_s_0008','student_current',NULL,1,2024,'school_website','医進・サイエンスコースでは理数系の深い学習ができ、インターナショナルコースでは外国人教員による英語での授業があります。本当に自分の興味に合わせて学べます。','在校生によるコース別教育の充実度。選択肢の多さによる個別化。','個別化・キャリア開発',
 'positive','quoted_with_attribution','jpms_src_020801',datetime('now')),

-- 【神戸女学院中学部】jpms_s_0009 - 3件
('jpms_t_000028','jpms_s_0009','principal',NULL,1,2024,'school_website','聖書の教えに基づき、毎朝の礼拝が生徒たちの学校生活を貫く確かな柱となっています。','部長による礼拝の教育的位置づけ。信仰的基盤による学校文化。','宗教教育・精神的基盤',
 'positive','quoted_with_attribution','jpms_src_020901',datetime('now')),

('jpms_t_000029','jpms_s_0009','principal',NULL,1,2024,'school_website','「愛神愛隣」の精神に基づくキリスト教主義の全人教育を展開し、社会に奉仕できる豊かな人間性を持った女性リーダーの育成を目指しています。','部長による教育目標。全人教育と社会貢献。','キリスト教教育・社会貢献',
 'positive','quoted_with_attribution','jpms_src_020901',datetime('now')),

('jpms_t_000030','jpms_s_0009','student_current',NULL,1,2024,'school_website','毎日通うのが楽しみになります。友達を案内するときも誇らしいです。校舎は重要文化財に指定されていて、とても美しい環境で学ぶことができます。','在校生による学校環境への満足度。伝統的校舎による教育的雰囲気。','学校環境・満足度',
 'positive','quoted_with_attribution','jpms_src_020901',datetime('now')),

-- 【渋谷教育学園渋谷中学校】jpms_s_0010 - 3件
('jpms_t_000031','jpms_s_0010','principal',NULL,1,2024,'school_website','「noblesse oblige（尊い人は義務を負う）」という言葉にふさわしい、これからの国際社会で活躍を目指す未来からの留学生である君たちを待っている。','学園長による国際的責任感の育成。倫理的リーダーシップ教育。','倫理観・国際性',
 'positive','quoted_with_attribution','jpms_src_021001',datetime('now')),

('jpms_t_000032','jpms_s_0010','student_current',NULL,1,2024,'school_website','「自調自考」という考え方を大切にしています。自分で調べ自分で考える力が、これからの人生で最も大事だと感じるようになりました。','在校生による建学の精神の内在化。予測困難な時代への対応力。','自調自考・人生観',
 'positive','quoted_with_attribution','jpms_src_021001',datetime('now')),

('jpms_t_000033','jpms_s_0010','student_current',NULL,1,2024,'school_website','学園長講話という月数回の特別授業で、中1は「人間関係」から始まり、高3は「自分探しの旅立ち」まで、自己理解を深めていくプログラムがあります。','在校生によるキャリア開発プログラム。系統的な自己理解教育。','自己理解・キャリア開発',
 'positive','quoted_with_attribution','jpms_src_021001',datetime('now'));
