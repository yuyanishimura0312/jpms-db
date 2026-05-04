-- JPMS-DB サンプル10校シード
-- 多様性: 地域（東京6・千葉1・関西3）/ 性別（男子3・女子3・共学4）
--        宗教（カトリック1・プロテスタント1・仏教1・神道0・無宗教7）
--        系列（伝統校7・新興系3）

-- 学校HP出典の登録
INSERT INTO jpms_sources (id, source_type, title, author, url, accessed_at, publication_year, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_020001','school_website','開成中学校 公式サイト','学校法人開成学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020002','school_website','麻布中学校 公式サイト','学校法人麻布学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020003','school_website','桜蔭中学校 公式サイト','学校法人桜蔭学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020004','school_website','雙葉中学校 公式サイト','学校法人雙葉学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020005','school_website','渋谷教育学園幕張中学校 公式サイト','学校法人渋谷教育学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020006','school_website','灘中学校 公式サイト','学校法人灘育英会',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020007','school_website','洛南高等学校附属中学校 公式サイト','学校法人真言宗洛南学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020008','school_website','広尾学園中学校 公式サイト','学校法人広尾学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020009','school_website','神戸女学院中学部 公式サイト','学校法人神戸女学院',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定'),
('jpms_src_020010','school_website','渋谷教育学園渋谷中学校 公式サイト','学校法人渋谷教育学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'Phase 1で実URL取得予定');

-- サンプル10校の基本情報（公開情報の範囲）
INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, founding_philosophy, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0001','開成中学校','かいせいちゅうがっこう',1871,'学校法人開成学園','non_religious','「ペンは剣よりも強し」を校章に掲げ、自由闊達な気風と質実剛健の校風のもと、社会のリーダーを育成する。','boys','attached','東京都','荒川区','jpms_src_020001',30,'active'),
('jpms_s_0002','麻布中学校','あざぶちゅうがっこう',1895,'学校法人麻布学園','non_religious','自主自立・自由闊達の校風のもと、生徒の個性と自由な発想を尊重する教育を行う。','boys','attached','東京都','港区','jpms_src_020002',30,'active'),
('jpms_s_0003','桜蔭中学校','おういんちゅうがっこう',1924,'学校法人桜蔭学園','non_religious','「礼と学」を校訓に、女性の社会的自立と知的向上を目指す。','girls','attached','東京都','文京区','jpms_src_020003',30,'active'),
('jpms_s_0004','雙葉中学校','ふたばちゅうがっこう',1872,'学校法人雙葉学園','catholic','カトリックの愛の精神を基盤に「徳においては純真に、義務においては堅実に」をモットーとする。','girls','attached','東京都','千代田区','jpms_src_020004',30,'active'),
('jpms_s_0005','渋谷教育学園幕張中学校','しぶやきょういくがくえんまくはりちゅうがっこう',1986,'学校法人渋谷教育学園','non_religious','「自調自考」を建学の精神に、グローバル時代を生き抜く力と国際感覚を育成する。','coed','attached','千葉県','千葉市','jpms_src_020005',30,'active'),
('jpms_s_0006','灘中学校','なだちゅうがっこう',1928,'学校法人灘育英会','non_religious','「精力善用・自他共栄」を校訓に、自由な学風のもと学問への純粋な探究心を育てる。','boys','attached','兵庫県','神戸市','jpms_src_020006',30,'active'),
('jpms_s_0007','洛南高等学校附属中学校','らくなんこうとうがっこうふぞくちゅうがっこう',1962,'学校法人真言宗洛南学園','buddhist','弘法大師空海の教えを建学の精神とし、「規律・自学・友愛」を三大目標として人格教育を行う。','coed','attached','京都府','京都市','jpms_src_020007',30,'active'),
('jpms_s_0008','広尾学園中学校','ひろおがくえんちゅうがっこう',1918,'学校法人広尾学園','non_religious','医進・サイエンスコース、インターナショナルコースを擁し、グローバルかつアカデミックな教育を行う。','coed','attached','東京都','港区','jpms_src_020008',30,'active'),
('jpms_s_0009','神戸女学院中学部','こうべじょがくいんちゅうがくぶ',1875,'学校法人神戸女学院','protestant','プロテスタントのキリスト教精神に基づき、「Love God and Serve His People」を建学の精神とする。','girls','attached','兵庫県','西宮市','jpms_src_020009',30,'active'),
('jpms_s_0010','渋谷教育学園渋谷中学校','しぶやきょういくがくえんしぶやちゅうがっこう',1924,'学校法人渋谷教育学園','non_religious','「自調自考」を建学の精神に、自分で調べ自分で考える力と国際感覚を育成する。','coed','attached','東京都','渋谷区','jpms_src_020010',30,'active');

-- カリキュラム特性（暫定値、Phase 1で学校HPから精緻化）
INSERT INTO jpms_school_curriculum (school_id, inquiry_learning, steam, pbl, ib_program, international_track, ict_strength, art_strength, sports_strength, religious_education, source_id) VALUES
('jpms_s_0001',1,1,0,'none',0,2,1,2,0,'jpms_src_020001'),
('jpms_s_0002',1,0,1,'none',0,1,2,2,0,'jpms_src_020002'),
('jpms_s_0003',1,1,0,'none',0,2,2,1,0,'jpms_src_020003'),
('jpms_s_0004',1,0,1,'none',1,2,2,1,1,'jpms_src_020004'),
('jpms_s_0005',1,1,1,'DP',1,3,1,1,0,'jpms_src_020005'),
('jpms_s_0006',1,1,0,'none',0,2,1,2,0,'jpms_src_020006'),
('jpms_s_0007',1,0,0,'none',0,2,1,2,1,'jpms_src_020007'),
('jpms_s_0008',1,1,1,'DP',1,3,1,1,0,'jpms_src_020008'),
('jpms_s_0009',1,0,1,'none',1,2,3,1,1,'jpms_src_020009'),
('jpms_s_0010',1,1,1,'DP',1,3,1,1,0,'jpms_src_020010');
