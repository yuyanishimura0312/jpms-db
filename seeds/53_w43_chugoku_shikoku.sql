-- JPMS-DB Phase 2.5 W43: 中国・四国地方の私立中学校
-- 対象地域: 広島県、岡山県、山口県、島根県、鳥取県、愛媛県、香川県、徳島県、高知県
-- ID範囲: jpms_s_0820 〜 jpms_s_0844（25校）
-- ソースID範囲: jpms_src_053000 〜 jpms_src_053024

-- ===== SOURCES: 学校HP出典 (25件) =====

INSERT INTO jpms_sources (id, source_type, title, author, url, accessed_at, publication_year, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_053000','school_website','ノートルダム清心 中・高等学校','学校法人ノートルダム清心学園','https://www.hiro-seishin.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'広島市西区 1952年開設'),
('jpms_src_053001','school_website','広島学院中学校・高等学校','学校法人上智学院',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'広島市西区 1956年創立'),
('jpms_src_053002','school_website','広島城北中学校・高等学校','学校法人広島城北学園','https://hiroshimajohoku.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'広島市東区 1961年開校'),
('jpms_src_053003','school_website','AICJ中学・高等学校','学校法人AICJ鴎州学園','https://aicj.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'広島市安佐南区 2006年開校'),
('jpms_src_053004','school_website','広島なぎさ中学校・高等学校','学校法人鶴学園','https://www.nagisa.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'広島市佐伯区 1965年開校'),
('jpms_src_053005','school_website','岡山白陵中学校・高等学校','学校法人三木学園','https://www.okahaku.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'赤磐市 1976年開校'),
('jpms_src_053006','school_website','就実中学校・高等学校','学校法人就実学園','https://www.shujitsu-h.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'岡山市北区 1904年創立'),
('jpms_src_053007','school_website','清心中学校・清心女子高等学校','学校法人ノートルダム清心学園','https://www.nd-seishin.ac.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'倉敷市 1886年創立'),
('jpms_src_053008','school_website','岡山中学校・岡山高等学校','学校法人関西学園','https://www.okayama-h.ed.jp',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'岡山市北区 1982年開校'),
('jpms_src_053009','school_website','岡山理科大学附属中学校',NULL,'https://www.richuhp.info/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'岡山市北区'),
('jpms_src_053010','school_website','岡山学芸館清秀中学校','学校法人森教育学園','https://www.gakugeikan.ed.jp/seishu/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'岡山市北区 2010年開校'),
('jpms_src_053011','school_website','サビエル高等学校',NULL,'https://xavier.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'山陽小野田市 1962年開校'),
('jpms_src_053012','school_website','慶進中学校・高等学校',NULL,NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',90,'宇部市 2004年設置'),
('jpms_src_053013','school_website','開星中学校・高等学校','学校法人大多和学園','https://shimane-kaisei.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'松江市 1994年開校'),
('jpms_src_053014','school_website','青翔開智中学校・高等学校','学校法人鶏鳴学園','https://seishokaichi.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'鳥取市 2014年開校'),
('jpms_src_053015','school_website','愛光中学校・高等学校','学校法人愛光学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'松山市 1953年開校'),
('jpms_src_053016','school_website','済美平成中等教育学校','学校法人済美学園','https://www.saibi-heisei.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'松山市 2002年開校'),
('jpms_src_053017','school_website','新田青雲中等教育学校','学校法人新田学園','https://www.nitta-seiun.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'松山市 2003年開校'),
('jpms_src_053018','school_website','大手前高松中学・高等学校','学校法人倉田学園','https://www.otemae.net/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'高松市 1973年開校'),
('jpms_src_053019','school_website','徳島文理中学校・高等学校',NULL,'https://www.bunri.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'徳島市'),
('jpms_src_053020','school_website','生光学園中学校・高等学校',NULL,'https://www.seikogakuen.ac.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'徳島市'),
('jpms_src_053021','school_website','土佐塾中学校・高等学校',NULL,'https://www.tosajuku.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'高知市 1987年開校'),
('jpms_src_053022','school_website','土佐中学校・高等学校',NULL,'https://www.tosa.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'高知市 1922年開校'),
('jpms_src_053023','school_website','高知学芸中学校・高等学校',NULL,NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'高知市 1957年開校'),
('jpms_src_053024','school_website','明徳義塾中学校・高等学校','学校法人明徳義塾','https://www.meitoku-gijuku.ed.jp/',datetime('now'),NULL,'copyrighted_permission_required','primary',95,'須崎市 1973年創立');

-- ===== SCHOOLS: 基本情報 (25校) =====

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0820','ノートルダム清心中学校・高等学校','placeholder',1952,NULL,'non_religious','coed','full','広島県','広島市西区','jpms_src_053000',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0821','広島学院中学校・高等学校','placeholder',1956,NULL,'non_religious','coed','full','広島県','広島市西区','jpms_src_053001',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0822','広島城北中学校・高等学校','placeholder',1961,NULL,'non_religious','coed','full','広島県','広島市東区','jpms_src_053002',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0823','AICJ中学校・高等学校','placeholder',2006,NULL,'non_religious','coed','full','広島県','広島市安佐南区','jpms_src_053003',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0824','広島なぎさ中学校・高等学校','placeholder',1965,NULL,'non_religious','coed','full','広島県','広島市佐伯区','jpms_src_053004',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0825','岡山白陵中学校・高等学校','placeholder',1976,NULL,'non_religious','coed','full','岡山県','赤磐市','jpms_src_053005',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0826','就実中学校・高等学校','placeholder',1904,NULL,'non_religious','coed','full','岡山県','岡山市北区','jpms_src_053006',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0827','清心中学校・清心女子高等学校','placeholder',1886,NULL,'non_religious','coed','full','岡山県','倉敷市','jpms_src_053007',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0828','岡山中学校・岡山高等学校','placeholder',1982,NULL,'non_religious','coed','full','岡山県','岡山市北区','jpms_src_053008',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0829','岡山理科大学附属中学校','placeholder',NULL,NULL,'non_religious','coed','full','岡山県','岡山市北区','jpms_src_053009',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0830','岡山学芸館清秀中学校','placeholder',2010,NULL,'non_religious','coed','full','岡山県','岡山市北区','jpms_src_053010',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0831','サビエル高等学校','placeholder',1962,NULL,'non_religious','coed','full','山口県','山陽小野田市','jpms_src_053011',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0832','慶進中学校・高等学校','placeholder',2004,NULL,'non_religious','coed','full','山口県','宇部市','jpms_src_053012',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0833','開星中学校・高等学校','placeholder',1994,NULL,'non_religious','coed','full','島根県','松江市','jpms_src_053013',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0834','青翔開智中学校・高等学校','placeholder',2014,NULL,'non_religious','coed','full','鳥取県','鳥取市','jpms_src_053014',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0835','愛光中学校・高等学校','placeholder',1953,NULL,'non_religious','coed','full','愛媛県','松山市','jpms_src_053015',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0836','済美平成中等教育学校','placeholder',2002,NULL,'non_religious','coed','full','愛媛県','松山市','jpms_src_053016',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0837','新田青雲中等教育学校','placeholder',2003,NULL,'non_religious','coed','full','愛媛県','松山市','jpms_src_053017',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0838','大手前高松中学・高等学校','placeholder',1973,NULL,'non_religious','coed','full','香川県','高松市','jpms_src_053018',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0839','徳島文理中学校・高等学校','placeholder',NULL,NULL,'non_religious','coed','full','徳島県','徳島市','jpms_src_053019',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0840','生光学園中学校・高等学校','placeholder',NULL,NULL,'non_religious','coed','full','徳島県','徳島市','jpms_src_053020',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0841','土佐塾中学校・高等学校','placeholder',1987,NULL,'non_religious','coed','full','高知県','高知市','jpms_src_053021',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0842','土佐中学校・高等学校','placeholder',1922,NULL,'non_religious','coed','full','高知県','高知市','jpms_src_053022',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0843','高知学芸中学校・高等学校','placeholder',1957,NULL,'non_religious','coed','full','高知県','高知市','jpms_src_053023',25,'active');

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0844','明徳義塾中学校・高等学校','placeholder',1973,NULL,'non_religious','coed','full','高知県','須崎市','jpms_src_053024',25,'active');

