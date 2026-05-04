-- JPMS-DB Phase 2 W22: 東京西部・多摩地区の私立中学校
-- 対象地域: 世田谷区・杉並区・中野区・目黒区・大田区・品川区・武蔵野市・三鷹市・調布市・小金井市・国立市・八王子市・町田市・立川市・府中市


-- SOURCE REGISTRATION
INSERT INTO jpms_sources (id, source_type, title, author, url, accessed_at, publication_year, rights_status, primary_or_secondary, reliability_score, note) VALUES
('jpms_src_030101','school_website','鷗友学園女子中学校','学校法人鷗友学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'プロテスタント 1935年'),
('jpms_src_030102','school_website','駒場東邦中学校','学校法人東邦大学',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'無宗教 1957年'),
('jpms_src_030103','school_website','成城学園中学校','学校法人成城学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'無宗教 1947年'),
('jpms_src_030104','school_website','世田谷学園中学校','学校法人世田谷学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'曹洞宗 1902年'),
('jpms_src_030105','school_website','玉川聖学院中等部','学校法人玉川聖学院',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'プロテスタント 1950年'),
('jpms_src_030106','school_website','品川女子学院中等部','学校法人品川女子学院',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'無宗教 1925年'),
('jpms_src_030107','school_website','攻玉社中学校','学校法人攻玉社',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'無宗教 1872年'),
('jpms_src_030108','school_website','香蘭女学校中等科','学校法人香蘭学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'プロテスタント（聖公会） 1888年'),
('jpms_src_030109','school_website','青稜中学校','学校法人青稜学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'無宗教 1938年'),
('jpms_src_030110','school_website','吉祥女子中学校','学校法人吉祥学園',NULL,datetime('now'),NULL,'copyrighted_permission_required','primary',95,'無宗教 1938年');

-- SCHOOL DATA
INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, founding_philosophy, gender_type, integrated_type, location_pref, location_city, primary_source_id, data_completeness, status) VALUES
('jpms_s_0061','鷗友学園女子中学校','おうゆうがくえんじょしちゅうがっこう',1935,'学校法人鷗友学園','protestant','慈愛・誠実・創造を校訓に自立した女性の育成','girls','attached','東京都','世田谷区','jpms_src_030101',30,'active'),
('jpms_s_0062','駒場東邦中学校','こまばとうほうちゅうがっこう',1957,'学校法人東邦大学','non_religious','人類の福祉を高める仕事で活躍できる人材育成','boys','attached','東京都','世田谷区','jpms_src_030102',30,'active'),
('jpms_s_0063','成城学園中学校','せいじょうがくえんちゅうがっこう',1947,'学校法人成城学園','non_religious','個性尊重と心情の教育を重視','coed','attached','東京都','世田谷区','jpms_src_030103',30,'active'),
('jpms_s_0064','世田谷学園中学校','せたがやがくえんちゅうがっこう',1902,'学校法人世田谷学園','buddhist','曹洞宗の禅の精神に基づいた人格教育','boys','attached','東京都','世田谷区','jpms_src_030104',30,'active'),
('jpms_s_0065','玉川聖学院中等部','たまがわせいがくいんちゅうとうぶ',1950,'学校法人玉川聖学院','protestant','プロテスタント系キリスト教精神に基づく教育','girls','attached','東京都','世田谷区','jpms_src_030105',30,'active'),
('jpms_s_0066','品川女子学院中等部','しながわじょしがくいんちゅうとうぶ',1925,'学校法人品川女子学院','non_religious','女性の社会的自立と知識の習得','girls','attached','東京都','品川区','jpms_src_030106',30,'active'),
('jpms_s_0067','攻玉社中学校','こうぎょくしゃちゅうがっこう',1872,'学校法人攻玉社','non_religious','蘭学の精神を継承し科学的思考力を育成','boys','attached','東京都','品川区','jpms_src_030107',30,'active'),
('jpms_s_0068','香蘭女学校中等科','こうらんじょがっこうちゅうとうか',1888,'学校法人香蘭学園','protestant','聖公会のプロテスタント精神に基づく愛と信仰の教育','girls','attached','東京都','品川区','jpms_src_030108',30,'active'),
('jpms_s_0069','青稜中学校','せいりょうちゅうがっこう',1938,'学校法人青稜学園','non_religious','自由と自律の精神を育成','coed','attached','東京都','品川区','jpms_src_030109',30,'active'),
('jpms_s_0070','吉祥女子中学校','きちじょうじょしちゅうがっこう',1938,'学校法人吉祥学園','non_religious','社会に貢献する自立した女性の育成','girls','attached','東京都','武蔵野市','jpms_src_030110',30,'active');
