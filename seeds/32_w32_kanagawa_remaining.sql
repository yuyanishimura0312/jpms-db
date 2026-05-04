-- ========================================================================
-- JPMS-DB Phase 2 W32: Kanagawa Remaining Private Junior High Schools
-- Total: 15 schools (jpms_s_0490 - jpms_s_0504)
-- Source ID range: jpms_src_040200 - jpms_src_040214
-- Data from school websites, Wikipedia, and educational databases
-- ========================================================================

-- INSERT Sources
INSERT INTO jpms_sources (id, source_type, title, url, fetched_at, accessed_at, publication_year, primary_or_secondary, reliability_score, note) VALUES 
('jpms_src_040200', 'school_website', '公文国際学園中等部', 'https://kumon.ac.jp/k-gakuen/kokusai/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040201', 'school_website', '法政大学第二中学校', 'https://www.hosei2.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040202', 'school_website', '日本女子大学附属中学校', 'https://www.jwu.ac.jp/jhsc/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040203', 'school_website', '森村学園中等部', 'https://www.morimura.ac.jp/jsh/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040204', 'school_website', '日本大学藤沢中学校', 'https://www.fujisawa.hs.nihon-u.ac.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040205', 'school_website', '鶴見大学附属中学校', 'https://tsurumi-fuzoku.ed.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040206', 'school_website', 'カリタス女子中学校', 'https://www.caritas.ed.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040207', 'school_website', '湘南学園中学校', 'https://www.shogak.ac.jp/highschool/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040208', 'school_website', '聖セシリア女子中学校', 'https://www.cecilia.ac.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040209', 'school_website', '藤嶺学園藤沢中学校', 'https://www.tohrei-fujisawa.ed.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040210', 'school_website', '横浜隼人中学校', 'https://www.hayato.ed.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040211', 'school_website', '横浜富士見丘学園中等教育学校', 'https://fujimigaoka.ed.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040212', 'school_website', '横浜翠陵中学校', 'https://www.suiryo.ed.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040213', 'school_website', '北鎌倉女子学園中学校', 'https://www.kitakama.ac.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website'),
('jpms_src_040214', 'school_website', '武相中学校', 'https://buso.ac.jp/', '2026-05-04', '2026-05-04', 2026, 'primary', 95, 'Official school website');

-- INSERT Schools
INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, website_url, primary_source_id, data_completeness, status) VALUES 
('jpms_s_0490', '公文国際学園中等部', 'くもんこくさいがくえんちゅうとうぶ', 1992, '学校法人公文学園', 'non_religious', 'coed', 'none', '神奈川県', '横浜市戸塚区', 'https://kumon.ac.jp/k-gakuen/kokusai/', 'jpms_src_040200', 40, 'active'),
('jpms_s_0491', '法政大学第二中学校', 'ほうせいだいがくだいにちゅうがっこう', 1928, '学校法人法政大学', 'non_religious', 'coed', 'attached', '神奈川県', '横浜市港北区', 'https://www.hosei2.jp/', 'jpms_src_040201', 40, 'active'),
('jpms_s_0492', '日本女子大学附属中学校', 'にほんじょしだいがくふぞくちゅうがっこう', 1901, '学校法人日本女子大学', 'non_religious', 'girls', 'attached', '神奈川県', '横浜市栄区', 'https://www.jwu.ac.jp/jhsc/', 'jpms_src_040202', 40, 'active'),
('jpms_s_0493', '森村学園中等部', 'もりむらがくえんちゅうとうぶ', 1910, '学校法人森村学園', 'non_religious', 'coed', 'none', '神奈川県', '横浜市緑区', 'https://www.morimura.ac.jp/jsh/', 'jpms_src_040203', 40, 'active'),
('jpms_s_0494', '日本大学藤沢中学校', 'にほんだいがくふじさわちゅうがっこう', 1952, '学校法人日本大学', 'non_religious', 'coed', 'attached', '神奈川県', '藤沢市', 'https://www.fujisawa.hs.nihon-u.ac.jp/', 'jpms_src_040204', 40, 'active'),
('jpms_s_0495', '鶴見大学附属中学校', 'つるみだいがくふぞくちゅうがっこう', 1925, '学校法人鶴見大学', 'buddhist', 'boys', 'attached', '神奈川県', '横浜市鶴見区', 'https://tsurumi-fuzoku.ed.jp/', 'jpms_src_040205', 40, 'active'),
('jpms_s_0496', 'カリタス女子中学校', 'かりたすじょしちゅうがっこう', 1957, '学校法人カリタス学園', 'catholic', 'girls', 'attached', '神奈川県', '川崎市中原区', 'https://www.caritas.ed.jp/', 'jpms_src_040206', 40, 'active'),
('jpms_s_0497', '湘南学園中学校', 'しょうなんがくえんちゅうがっこう', 1933, '学校法人湘南学園', 'non_religious', 'coed', 'attached', '神奈川県', '藤沢市', 'https://www.shogak.ac.jp/highschool/', 'jpms_src_040207', 40, 'active'),
('jpms_s_0498', '聖セシリア女子中学校', 'せいせしりあじょしちゅうがっこう', 1929, '学校法人大和学園', 'catholic', 'girls', 'attached', '神奈川県', '大和市', 'https://www.cecilia.ac.jp/', 'jpms_src_040208', 40, 'active'),
('jpms_s_0499', '藤嶺学園藤沢中学校', 'とうれいがくえんふじさわちゅうがっこう', 1941, '学校法人藤嶺学園', 'buddhist', 'boys', 'attached', '神奈川県', '藤沢市', 'https://www.tohrei-fujisawa.ed.jp/', 'jpms_src_040209', 40, 'active'),
('jpms_s_0500', '横浜隼人中学校', 'よこはまはやとちゅうがっこう', 2007, '学校法人藤沢学院', 'non_religious', 'coed', 'attached', '神奈川県', '横浜市瀬谷区', 'https://www.hayato.ed.jp/', 'jpms_src_040210', 40, 'active'),
('jpms_s_0501', '横浜富士見丘学園中等教育学校', 'よこはまふじみおかがくえんちゅうとうきょういくがっこう', 1932, '学校法人富士見丘学園', 'non_religious', 'girls', 'none', '神奈川県', '横浜市旭区', 'https://fujimigaoka.ed.jp/', 'jpms_src_040211', 40, 'active'),
('jpms_s_0502', '横浜翠陵中学校', 'よこはまみどりおかちゅうがっこう', 1940, '学校法人綜合学園', 'non_religious', 'coed', 'attached', '神奈川県', '横浜市栄区', 'https://www.suiryo.ed.jp/', 'jpms_src_040212', 40, 'active'),
('jpms_s_0503', '北鎌倉女子学園中学校', 'きたかまくらじょしがくえんちゅうがっこう', 1945, '学校法人北鎌倉学園', 'non_religious', 'girls', 'attached', '神奈川県', '鎌倉市', 'https://www.kitakama.ac.jp/', 'jpms_src_040213', 40, 'active'),
('jpms_s_0504', '武相中学校', 'ぶそうちゅうがっこう', 1942, '学校法人武相学園', 'catholic', 'boys', 'attached', '神奈川県', '横浜市神奈川区', 'https://buso.ac.jp/', 'jpms_src_040214', 40, 'active');

-- Note: This file contains 15 remaining private junior high schools in Kanagawa Prefecture.
-- The schools were selected based on significance and enrollment scale from the complete list of 
-- Kanagawa private schools. Curriculum data and additional details to be added in enrichment phase.
