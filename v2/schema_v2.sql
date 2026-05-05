-- JPMS-DB v2.0 Schema
-- Author: JPMS-DB v2 team
-- Version: 2.0-draft
-- Created: 2026-05-05
--
-- 5層モデル: Layer1=学校実態 / Layer2=個人特性 / Layer3=成果次元 / Layer4=適合 / Layer5=時代変遷
-- 既存 jpms.db のテーブルは保持し、v2 系テーブルを並走配置

-- ============================================================
-- Layer 1: 学校実態（拡張）
-- ============================================================

-- 既存 jpms_schools を拡張する v2 マスタ
CREATE TABLE IF NOT EXISTS schools_v2 (
  id TEXT PRIMARY KEY,
  legacy_id TEXT,                          -- 旧 jpms_s_xxxx
  name_ja TEXT NOT NULL,
  name_kana TEXT,
  establishment_year INTEGER,
  school_corporation TEXT,
  religious_affiliation TEXT,              -- catholic/protestant/anglican/buddhist/non_religious/unknown/other
  gender_type TEXT,                        -- boys/girls/coed
  integrated_type TEXT,                    -- attached/full/linked/none
  location_pref TEXT,
  location_city TEXT,
  homepage_url TEXT,
  homepage_archived_at TEXT,               -- ISO 8601
  data_completeness_v2 INTEGER DEFAULT 0,  -- 0-100
  primary_outcome_cluster TEXT,            -- 主軸成果クラスタ
  secondary_outcome_cluster TEXT,
  archetype_label TEXT,                    -- カトリック・女子・付属 等
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 建学理念・教育方針の詳細テキスト（多バージョン対応）
CREATE TABLE IF NOT EXISTS school_philosophy_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  philosophy_type TEXT NOT NULL,           -- founding_philosophy/education_principle/principal_message/mission/vision
  text_full TEXT NOT NULL,
  text_summary TEXT,
  word_count INTEGER,
  source_url TEXT,
  source_id TEXT,                          -- jpms_sources.id への参照
  rights_level TEXT NOT NULL,
  retrieved_at TEXT,
  language TEXT DEFAULT 'ja',
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);
CREATE INDEX idx_philosophy_school ON school_philosophy_v2(school_id);

-- カリキュラム
CREATE TABLE IF NOT EXISTS school_curriculum_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  category TEXT,                           -- regular/elective/special_program/extracurricular
  subject_or_program TEXT,
  description TEXT,
  hours_per_week REAL,
  grade_levels TEXT,                       -- 1,2,3 or 1-3
  is_signature INTEGER DEFAULT 0,          -- 看板プログラム
  source_url TEXT,
  source_id TEXT,
  rights_level TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- 進学実績（年度別、外部公表値のみ）
CREATE TABLE IF NOT EXISTS school_progress_record_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  destination_type TEXT,                   -- internal_high/external_high/national_univ/private_univ/intl_univ
  destination_name TEXT,                   -- e.g. 東京大学
  count INTEGER,
  share_pct REAL,
  source_url TEXT,
  source_id TEXT,
  rights_level TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- 入試
CREATE TABLE IF NOT EXISTS school_admission_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  year INTEGER,
  exam_type TEXT,
  exam_count INTEGER,                       -- 試験回数
  applicants INTEGER,
  admitted INTEGER,
  competition_ratio REAL,
  scoring_summary TEXT,                     -- JSON
  source_url TEXT,
  rights_level TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- 施設
CREATE TABLE IF NOT EXISTS school_facility_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  facility_type TEXT,                       -- library/lab/gym/dorm/etc
  description TEXT,
  capacity INTEGER,
  notable INTEGER DEFAULT 0,
  source_url TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- 行事・カレンダー
CREATE TABLE IF NOT EXISTS school_calendar_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  event_type TEXT,                          -- festival/excursion/study_trip/sports_day/etc
  event_name TEXT,
  duration_days REAL,
  destination TEXT,
  description TEXT,
  source_url TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- HPアセット
CREATE TABLE IF NOT EXISTS school_homepage_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  page_path TEXT,                           -- /about/principal etc
  full_url TEXT,
  fetched_at TEXT,
  archive_path TEXT,                        -- raw_html_cache/<school_id>/...
  screenshot_path TEXT,
  status_code INTEGER,
  content_length INTEGER,
  rights_level TEXT DEFAULT 'archive_only',
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- 関係者の声（5主体）
CREATE TABLE IF NOT EXISTS testimonials_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  speaker_role TEXT NOT NULL,               -- principal/teacher/student_current/student_alumni/parent
  speaker_attribute TEXT,                   -- 学年/教科/卒業年/職業/性別/匿名度合
  quote_text TEXT NOT NULL,
  quote_summary TEXT,
  context TEXT,                             -- 入学式祝辞/学校HP/取材/SNS等
  source_type TEXT,                         -- school_website/pamphlet/magazine/blog/sns/interview
  source_url TEXT,
  source_id TEXT,
  rights_level TEXT NOT NULL,               -- quoted_with_attribution/anonymized_only/archive_only
  retrieved_at TEXT,
  retrieval_notes TEXT,
  ethics_review_status TEXT DEFAULT 'pending', -- pending/approved/rejected
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);
CREATE INDEX idx_testimonials_school ON testimonials_v2(school_id);
CREATE INDEX idx_testimonials_role ON testimonials_v2(speaker_role);

-- 公的統計
CREATE TABLE IF NOT EXISTS school_official_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  stat_year INTEGER,
  stat_source TEXT,                         -- mext_basic/mext_health/private_council等
  stat_name TEXT,
  stat_value REAL,
  stat_unit TEXT,
  source_url TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- ============================================================
-- Layer 2: 個人特性（新設）
-- ============================================================

CREATE TABLE IF NOT EXISTS person_trait_dim (
  id TEXT PRIMARY KEY,
  name_ja TEXT NOT NULL,
  name_en TEXT,
  theory_origin TEXT,                       -- BigFive/GrowthMindset/SDT/SRL/GRIT/Marcia等
  big_five_axis TEXT,                       -- O/C/E/A/N
  growth_dimension TEXT,
  age_floor INTEGER DEFAULT 10,             -- 測定可能最低年齢
  measurement_tool TEXT,                    -- BFI-J/MSCI-J/etc
  reliability_score REAL,
  literature_ref TEXT,
  description TEXT
);

CREATE TABLE IF NOT EXISTS person_archetype (
  id TEXT PRIMARY KEY,
  name_ja TEXT NOT NULL,
  name_en TEXT,
  trait_pattern TEXT,                       -- JSON: 各次元のスコア閾値
  description TEXT,
  origin_theory TEXT,                       -- 神話/MY DB由来 / Big Five / etc.
  prevalence_estimate REAL                  -- 母集団中の推定割合
);

-- ============================================================
-- Layer 3: 成果次元（拡張・多角化）
-- ============================================================

CREATE TABLE IF NOT EXISTS outcome_cluster_v2 (
  id TEXT PRIMARY KEY,                      -- cognitive/social_emotional/values_morals/agency_civic/wellbeing/creative_excellence/market_management
  name_ja TEXT NOT NULL,
  name_en TEXT,
  description TEXT,
  display_order INTEGER
);

CREATE TABLE IF NOT EXISTS outcome_dim_v2 (
  id TEXT PRIMARY KEY,
  name_ja TEXT NOT NULL,
  name_en TEXT,
  cluster_id TEXT NOT NULL,
  framework TEXT,                           -- OECD/CASEL/PERMA/P21/PISA_WB/JP/Cox/Simonton/Lerner/Collins/Christensen等
  source_type TEXT,                         -- 学術理論/実証DB/時代変遷
  source_db_ref TEXT,                       -- ミラツクDB ID（GF/MG/IT等）
  definition TEXT,
  measurement_method TEXT,
  age_window TEXT,                          -- in_school/graduate_5y/graduate_10y/graduate_20y
  predictability INTEGER,                   -- 1-5
  literature_ref TEXT,
  FOREIGN KEY (cluster_id) REFERENCES outcome_cluster_v2(id)
);
CREATE INDEX idx_outcome_cluster ON outcome_dim_v2(cluster_id);

CREATE TABLE IF NOT EXISTS outcome_era_relevance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  outcome_dim_id TEXT NOT NULL,
  era TEXT NOT NULL,                        -- meiji/taisho/showa/heisei/reiwa/2030s/2050s
  relevance INTEGER,                        -- 1-10
  reasoning TEXT,
  source_ref TEXT,                          -- FS/MT/CLA/AA/AD等のID
  FOREIGN KEY (outcome_dim_id) REFERENCES outcome_dim_v2(id)
);

-- 偉人プロファイル（GF DB由来）
CREATE TABLE IF NOT EXISTS great_figure_traits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  figure_id TEXT NOT NULL,                  -- GF DB の人物ID参照
  figure_name TEXT,
  trait_dim_id TEXT,                        -- person_trait_dim.id
  trait_description TEXT,                   -- 自由記述
  trait_value REAL,                         -- 0-100 推定値
  development_period TEXT,                  -- childhood/adolescence/early_adult
  evidence_type TEXT,                       -- biography/letters/anecdote/etc
  source_id TEXT,
  confidence INTEGER,                        -- 1-5
  FOREIGN KEY (trait_dim_id) REFERENCES person_trait_dim(id)
);

-- 卒業後活躍経路アーキタイプ
CREATE TABLE IF NOT EXISTS career_archetype (
  id TEXT PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  domain TEXT,                              -- it/bio/social/finance/academia/arts/etc
  description TEXT,
  predicting_traits TEXT,                   -- JSON: 中学生時に観察可能な特性
  development_path TEXT,                    -- JSON: 中→高→大→社のtypical軌道
  source_db TEXT,                           -- IR/IC/UPR/EX/AL/GF
  case_count INTEGER DEFAULT 0,
  notable_examples TEXT                     -- JSON
);

-- 卒業生活躍データ
CREATE TABLE IF NOT EXISTS alumni_career (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  alumni_anonymous_id TEXT,                 -- 個人特定可能な情報は別管理
  career_field TEXT,
  career_archetype_id TEXT,
  achievement_level INTEGER,                -- 1-5
  source_db_ref TEXT,                       -- IR/IC/UPR/EX/AL/GF
  source_record_id TEXT,
  source_url TEXT,
  evidence_count INTEGER,
  privacy_status TEXT DEFAULT 'public_record',
  FOREIGN KEY (school_id) REFERENCES schools_v2(id),
  FOREIGN KEY (career_archetype_id) REFERENCES career_archetype(id)
);
CREATE INDEX idx_alumni_school ON alumni_career(school_id);

-- ============================================================
-- Layer 4: 適合・予測モデル（新設）
-- ============================================================

CREATE TABLE IF NOT EXISTS school_culture_dim (
  id TEXT PRIMARY KEY,
  name_ja TEXT,
  name_en TEXT,
  axis_negative TEXT,                       -- 例: 規律
  axis_positive TEXT,                       -- 例: 自律
  description TEXT,
  measurement_proxy TEXT                    -- データから算出する代理変数の定義
);

-- 525校 × N次元のスコア
CREATE TABLE IF NOT EXISTS school_culture_score (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  culture_dim_id TEXT NOT NULL,
  score REAL,                               -- 0-100
  evidence_count INTEGER,
  evidence_summary TEXT,
  computed_at TEXT,
  method TEXT,                              -- heuristic/keyword_count/lca/etc
  FOREIGN KEY (school_id) REFERENCES schools_v2(id),
  FOREIGN KEY (culture_dim_id) REFERENCES school_culture_dim(id)
);
CREATE INDEX idx_score_school ON school_culture_score(school_id);

-- LCA抽出された学校類型
CREATE TABLE IF NOT EXISTS school_typology_lca (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  typology_class TEXT,                      -- versatile/structured/responsive/etc.
  posterior_prob REAL,
  computed_at TEXT,
  model_version TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id)
);

-- 適合ルール
CREATE TABLE IF NOT EXISTS person_school_fit_rule (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_name TEXT,
  person_trait_pattern TEXT NOT NULL,       -- JSON
  school_culture_pattern TEXT NOT NULL,     -- JSON
  fit_score_formula TEXT,                   -- 数理表現
  expected_outcomes TEXT,                   -- JSON
  evidence_from TEXT,                       -- 文献またはミラツクDB ID
  confidence INTEGER,                       -- 1-5
  rationale TEXT
);

-- 予測ログ
CREATE TABLE IF NOT EXISTS fit_prediction_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  input_person_profile TEXT,                -- JSON
  predicted_top_schools TEXT,               -- JSON ranked
  model_version TEXT,
  computed_at TEXT
);

-- ============================================================
-- Layer 5: 時代変遷モデル（新設）
-- ============================================================

CREATE TABLE IF NOT EXISTS era_definition (
  id TEXT PRIMARY KEY,                      -- meiji/taisho/showa_pre/showa_post/heisei/reiwa/2030s/2050s
  name_ja TEXT,
  name_en TEXT,
  start_year INTEGER,
  end_year INTEGER,
  description TEXT
);

CREATE TABLE IF NOT EXISTS era_zeitgeist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  era_id TEXT NOT NULL,
  zeitgeist_summary TEXT,
  source_db TEXT,                           -- CLA/MT/FK
  source_record_id TEXT,
  FOREIGN KEY (era_id) REFERENCES era_definition(id)
);

CREATE TABLE IF NOT EXISTS era_required_traits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  era_id TEXT NOT NULL,
  outcome_dim_id TEXT,
  trait_dim_id TEXT,
  weight REAL,                              -- 0-1
  reasoning TEXT,
  source_ref TEXT,                          -- FK/MT/FS/CLA/AA/AD等のID
  FOREIGN KEY (era_id) REFERENCES era_definition(id),
  FOREIGN KEY (outcome_dim_id) REFERENCES outcome_dim_v2(id),
  FOREIGN KEY (trait_dim_id) REFERENCES person_trait_dim(id)
);

CREATE TABLE IF NOT EXISTS era_school_alignment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_id TEXT NOT NULL,
  era_id TEXT NOT NULL,
  alignment_score REAL,                     -- 0-100
  alignment_type TEXT,                      -- classical/transitional/contemporary/future_oriented
  reasoning TEXT,
  computed_at TEXT,
  FOREIGN KEY (school_id) REFERENCES schools_v2(id),
  FOREIGN KEY (era_id) REFERENCES era_definition(id)
);

-- ============================================================
-- 共通: ソース・倫理管理
-- ============================================================

CREATE TABLE IF NOT EXISTS sources_v2 (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,                -- school_website/academic_paper/government_stat/book/interview
  url TEXT,
  title TEXT,
  author TEXT,
  publisher TEXT,
  publication_date TEXT,
  retrieved_at TEXT,
  primary_or_secondary TEXT,
  reliability_score INTEGER,                -- 1-5
  rights_status TEXT,                       -- public_domain/cc-by/cc-by-nc/copyright_cleared/permission_granted/research_use_only
  notes TEXT
);

CREATE TABLE IF NOT EXISTS ethics_review_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reviewed_table TEXT,
  reviewed_record_id INTEGER,
  reviewer TEXT,                            -- legal-advisor/compliance-monitor/manual
  decision TEXT,                            -- approved/rejected/needs_anonymization
  reasoning TEXT,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS deletion_request_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  requester_contact TEXT,
  target_table TEXT,
  target_record_id INTEGER,
  reason TEXT,
  status TEXT,                              -- received/processing/completed/rejected
  received_at TEXT,
  completed_at TEXT
);

-- ============================================================
-- ビュー: ミラツク36DB との接続点
-- ============================================================

-- これらは別DBへのattachまたは外部APIで実装。スキーマ上は参照記録のみ。
CREATE TABLE IF NOT EXISTS external_db_reference (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_db_code TEXT NOT NULL,           -- AK/GF/MG/IT/AN/MY/SIF/FS/FK/MT/CLA/AA/AD/EX/AL/UPR/IR/IC/SGRD/MS
  external_record_id TEXT,
  external_record_type TEXT,
  internal_table TEXT,                      -- どの v2 テーブルが参照しているか
  internal_record_id INTEGER,
  reference_purpose TEXT,
  fetched_at TEXT
);
CREATE INDEX idx_external_ref_db ON external_db_reference(external_db_code);

-- ============================================================
-- メタ: スキーマバージョン管理
-- ============================================================

CREATE TABLE IF NOT EXISTS schema_metadata (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT
);

INSERT OR REPLACE INTO schema_metadata (key, value, updated_at) VALUES
  ('schema_version', '2.0-draft', CURRENT_TIMESTAMP),
  ('total_layers', '5', CURRENT_TIMESTAMP),
  ('initial_total_schools', '525', CURRENT_TIMESTAMP),
  ('target_outcome_dims', '100+', CURRENT_TIMESTAMP),
  ('target_testimonials', '7800', CURRENT_TIMESTAMP),
  ('target_alumni_records', '5000+', CURRENT_TIMESTAMP);
