-- JPMS-DB Phase 2 W21: 追加校パッチ (台東・墨田・北区・板橋 + 文京区残) 
-- 2026-05-05
-- ID範囲: schools jpms_s_0051-0060, sources jpms_src_030044-030050

-- ===== ADDITIONAL SOURCES =====

INSERT INTO jpms_sources (id, source_type, title, author, url, accessed_at, publication_year, rights_status, primary_or_secondary, reliability_score, note) VALUES
-- 文京区 (6校分)
('jpms_src_030044','school_website','東邦音楽大学附属東邦中学校 公式サイト','学校法人東邦学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,''),
('jpms_src_030045','school_website','東洋大学京北中学校 公式サイト','学校法人東洋大学',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,''),
('jpms_src_030046','school_website','獨協中学校 公式サイト','学校法人獨協学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'1883年創立'),
('jpms_src_030047','school_website','日本大学豊山中学校 公式サイト','学校法人日本大学豊山学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'1903年認可、仏教系'),
('jpms_src_030048','school_website','広尾学園小石川中学校 公式サイト','学校法人広尾学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,''),
('jpms_src_030049','school_website','文京学院大学女子中学校 公式サイト','学校法人文京学院',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,''),
-- 台東・墨田・北・板橋区
('jpms_src_030050','school_website','上野学園中学校 公式サイト','学校法人上野学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'台東区');

-- ===== ADDITIONAL SCHOOLS (10校: jpms_s_0051-0060) =====

INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, founding_philosophy, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
-- 文京区 (6校追加分)
('jpms_s_0051','東邦音楽大学附属東邦中学校','とうほうおんがくだいがくふぞくとうほうちゅうがっこう',1956,'学校法人東邦学園','non_religious',NULL,'coed','attached','東京都','文京区','jpms_src_030044',20,'active'),
('jpms_s_0052','東洋大学京北中学校','とうようだいがくきょうほくちゅうがっこう',1903,'学校法人東洋大学','non_religious',NULL,'boys','attached','東京都','文京区','jpms_src_030045',25,'active'),
('jpms_s_0053','獨協中学校','どっきょうちゅうがっこう',1883,'学校法人獨協学園','non_religious','「心構えは正しく、身体は健康、知性に照らされた善意志と豊かな情操」を持つ気品ある人間の育成。','boys','attached','東京都','文京区','jpms_src_030046',45,'active'),
('jpms_s_0054','日本大学豊山中学校','にほんだいがくとよやまちゅうがっこう',1903,'学校法人日本大学豊山学園','buddhist','「自主創造」の精神と「強く 正しく 大らかに」の校訓のもと、人格教育を行う。','boys','attached','東京都','文京区','jpms_src_030047',40,'active'),
('jpms_s_0055','広尾学園小石川中学校','ひろおがくえんこいしかわちゅうがっこう',2016,'学校法人広尾学園','non_religious',NULL,'coed','non_religious','東京都','文京区','jpms_src_030048',20,'active'),
('jpms_s_0056','文京学院大学女子中学校','ぶんきょうがくいんだいがくじょしちゅうがっこう',1924,'学校法人文京学院','non_religious',NULL,'girls','attached','東京都','文京区','jpms_src_030049',20,'active'),
-- 台東区 (1校)
('jpms_s_0057','上野学園中学校','うえのがくえんちゅうがっこう',1904,'学校法人上野学園','non_religious',NULL,'coed','attached','東京都','台東区','jpms_src_030050',20,'active'),
-- 墨田区は追加分なし（既知: 日本大学第一・安田学園）
-- 北区・板橋区は66校超過のため後次フェーズに延期
-- リサーチレポート参照

INSERT INTO jpms_school_curriculum (school_id, inquiry_learning, steam, pbl, ib_program, international_track, ict_strength, art_strength, sports_strength, religious_education, source_id) VALUES
('jpms_s_0051',1,1,0,'non_religious',0,2,3,1,0,'jpms_src_030044'),
('jpms_s_0052',1,1,0,'non_religious',0,1,1,2,0,'jpms_src_030045'),
('jpms_s_0053',1,1,0,'non_religious',0,2,1,2,0,'jpms_src_030046'),
('jpms_s_0054',1,0,0,'non_religious',0,1,1,2,1,'jpms_src_030047'),
('jpms_s_0055',1,1,0,'non_religious',0,2,1,1,0,'jpms_src_030048'),
('jpms_s_0056',1,0,0,'non_religious',0,1,2,1,0,'jpms_src_030049'),
('jpms_s_0057',1,1,0,'non_religious',0,1,3,1,0,'jpms_src_030050');
