-- ========================================================================
-- JPMS-DB（日本私立中学校包括基盤データベース）スキーマ v0
-- ========================================================================
-- 作成日: 2026-05-05
-- 対象DB: SQLite 3.x with FTS5 / JSON1 extensions
-- 構造: 三層（学校実態×教育学術×成長軌道仮説）+ 共通レイヤ
-- ========================================================================

-- ============================================================
-- 共通レイヤ: 出典マスタ・取得ジョブ
-- ============================================================

CREATE TABLE jpms_sources (
    id TEXT PRIMARY KEY,
    source_type TEXT CHECK(
        source_type IN ('school_website','school_brochure','school_book','interview_field','newspaper','academic_paper','academic_book','official_stats','sns_x','sns_instagram','sns_youtube','blog','5ch','other')
    ) NOT NULL,
    title TEXT,
    author TEXT,
    publisher TEXT,
    url TEXT,
    fetched_at TEXT,
    accessed_at TEXT,
    publication_year INTEGER,
    rights_status TEXT CHECK(
        rights_status IN ('public_domain','cc_by','cc_by_nc','copyrighted_quotable','copyrighted_permission_required','private_use_only','unknown')
    ),
    primary_or_secondary TEXT CHECK(primary_or_secondary IN ('primary','secondary')),
    reliability_score INTEGER,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE jpms_fetch_jobs (
    id TEXT PRIMARY KEY,
    target_url TEXT,
    target_school_id TEXT,
    job_type TEXT,
    status TEXT CHECK(status IN ('queued','running','completed','failed','skipped')),
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    result_source_ids TEXT
);

-- ============================================================
-- 層1: 学校実態層
-- ============================================================

CREATE TABLE jpms_schools (
    id TEXT PRIMARY KEY,
    name_ja TEXT NOT NULL,
    name_kana TEXT,
    name_short TEXT,
    name_en TEXT,
    establishment_year INTEGER,
    founder TEXT,
    school_corporation TEXT,
    religious_affiliation TEXT CHECK(
        religious_affiliation IN ('catholic','protestant','anglican','buddhist','shinto','non_religious','other','unknown')
    ),
    religious_subgroup TEXT,
    founding_philosophy TEXT,
    education_principle TEXT,
    gender_type TEXT CHECK(gender_type IN ('coed','boys','girls')) NOT NULL,
    integrated_type TEXT CHECK(integrated_type IN ('full','attached','linked','none')),
    affiliated_university TEXT,
    location_pref TEXT NOT NULL,
    location_city TEXT,
    address TEXT,
    nearest_station TEXT,
    student_count_total INTEGER,
    teacher_count INTEGER,
    website_url TEXT,
    sns_x TEXT,
    sns_instagram TEXT,
    sns_youtube TEXT,
    sns_facebook TEXT,
    primary_source_id TEXT REFERENCES jpms_sources(id),
    data_completeness INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE jpms_school_curriculum (
    school_id TEXT PRIMARY KEY REFERENCES jpms_schools(id),
    inquiry_learning INTEGER DEFAULT 0,
    steam INTEGER DEFAULT 0,
    pbl INTEGER DEFAULT 0,
    ib_program TEXT,
    international_track INTEGER DEFAULT 0,
    ict_strength INTEGER DEFAULT 0,
    art_strength INTEGER DEFAULT 0,
    sports_strength INTEGER DEFAULT 0,
    religious_education INTEGER DEFAULT 0,
    second_language TEXT,
    special_programs TEXT,
    source_id TEXT REFERENCES jpms_sources(id),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE jpms_school_stats (
    id TEXT PRIMARY KEY,
    school_id TEXT NOT NULL REFERENCES jpms_schools(id),
    fiscal_year INTEGER NOT NULL,
    students_g1 INTEGER,
    students_g2 INTEGER,
    students_g3 INTEGER,
    male_ratio REAL,
    deviation_value REAL,
    deviation_source TEXT,
    competition_ratio REAL,
    source_id TEXT REFERENCES jpms_sources(id),
    UNIQUE(school_id, fiscal_year, deviation_source)
);

CREATE TABLE jpms_school_outcomes (
    id TEXT PRIMARY KEY,
    school_id TEXT NOT NULL REFERENCES jpms_schools(id),
    fiscal_year INTEGER NOT NULL,
    outcome_type TEXT CHECK(
        outcome_type IN ('todai_kyodai','soukei','gmarch','kankan_doritsu','medical','overseas','attached_uni','other')
    ),
    count INTEGER,
    note TEXT,
    source_id TEXT REFERENCES jpms_sources(id)
);

CREATE TABLE jpms_school_admissions (
    id TEXT PRIMARY KEY,
    school_id TEXT NOT NULL REFERENCES jpms_schools(id),
    fiscal_year INTEGER NOT NULL,
    admission_round TEXT,
    subjects TEXT,
    capacity INTEGER,
    applicants INTEGER,
    successful INTEGER,
    competition_ratio REAL,
    exam_features TEXT,
    source_id TEXT REFERENCES jpms_sources(id)
);

CREATE TABLE jpms_school_facilities (
    school_id TEXT PRIMARY KEY REFERENCES jpms_schools(id),
    has_dormitory INTEGER DEFAULT 0,
    dormitory_capacity INTEGER,
    notable_facilities TEXT,
    transport_options TEXT,
    campus_size_m2 INTEGER,
    source_id TEXT REFERENCES jpms_sources(id)
);

CREATE TABLE jpms_school_evaluations (
    id TEXT PRIMARY KEY,
    school_id TEXT NOT NULL REFERENCES jpms_schools(id),
    evaluator TEXT,
    eval_year INTEGER,
    eval_summary TEXT,
    source_id TEXT REFERENCES jpms_sources(id)
);

-- ============================================================
-- 層1関連: 関係者発言テーブル（一次情報の核心）
-- ============================================================

CREATE TABLE jpms_testimonials (
    id TEXT PRIMARY KEY,
    school_id TEXT REFERENCES jpms_schools(id),
    speaker_category TEXT CHECK(
        speaker_category IN ('student_current','student_former','parent_current','parent_former','teacher','principal','external_evaluator','third_party')
    ) NOT NULL,
    speaker_name TEXT,
    speaker_anonymized INTEGER DEFAULT 1,
    spoken_year INTEGER,
    medium TEXT CHECK(
        medium IN ('school_website','school_brochure','school_event','interview','book','newspaper','x','instagram','youtube','blog','note','5ch','other')
    ) NOT NULL,
    excerpt TEXT NOT NULL,
    summary TEXT,
    theme TEXT,
    sentiment TEXT CHECK(sentiment IN ('positive','neutral','negative','mixed')),
    rights_level TEXT CHECK(
        rights_level IN ('public','quoted_with_attribution','anonymized_only','permission_required','withhold')
    ) NOT NULL,
    source_id TEXT NOT NULL REFERENCES jpms_sources(id),
    fetched_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE jpms_testimonial_concept_links (
    id TEXT PRIMARY KEY,
    testimonial_id TEXT NOT NULL REFERENCES jpms_testimonials(id),
    concept_id TEXT NOT NULL,
    link_type TEXT,
    confidence REAL
);

-- ============================================================
-- 層2: 教育学術層
-- ============================================================

CREATE TABLE jpms_education_concepts (
    id TEXT PRIMARY KEY,
    name_ja TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_original TEXT,
    definition TEXT NOT NULL,
    impact_summary TEXT,
    subfield TEXT NOT NULL CHECK(
        subfield IN ('learning_science','motivation_dev','noncognitive','sel','adolescent_dev','career_dev','wellbeing','evidence_based','comparative','japanese_pedagogy','curriculum','assessment','inclusion','sociology_of_ed')
    ),
    school_of_thought TEXT NOT NULL,
    era_start INTEGER NOT NULL,
    era_end INTEGER,
    opposing_concept_names TEXT,
    keywords_ja TEXT NOT NULL,
    keywords_en TEXT NOT NULL,
    key_researchers TEXT NOT NULL,
    key_works TEXT NOT NULL,
    relevance_to_middle_school INTEGER,
    status TEXT DEFAULT 'active',
    source_reliability TEXT DEFAULT 'secondary',
    data_completeness INTEGER DEFAULT 80,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE jpms_education_concept_relations (
    id TEXT PRIMARY KEY,
    source_concept_id TEXT NOT NULL REFERENCES jpms_education_concepts(id),
    target_concept_id TEXT NOT NULL REFERENCES jpms_education_concepts(id),
    relation_type TEXT NOT NULL CHECK(
        relation_type IN ('derived_from','extends','critiques','empirically_tests','synthesizes','competes_with','applies_to_practice','complements','related_to','influenced')
    ),
    relation_description TEXT,
    strength INTEGER DEFAULT 5,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 層3: 成果仮説層
-- ============================================================

CREATE TABLE jpms_outcome_dimensions (
    id TEXT PRIMARY KEY,
    name_ja TEXT NOT NULL,
    name_en TEXT NOT NULL,
    definition TEXT NOT NULL,
    framework TEXT NOT NULL,
    measurement_approach TEXT,
    measurability TEXT CHECK(measurability IN ('quantitative','qualitative','mixed','conceptual')),
    relevance_age TEXT,
    source_id TEXT REFERENCES jpms_sources(id)
);

CREATE TABLE jpms_growth_hypotheses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    target_school_id TEXT REFERENCES jpms_schools(id),
    target_school_type TEXT,
    target_child_profile TEXT,
    hypothesized_trajectory TEXT NOT NULL,
    short_term_outcomes TEXT,
    mid_term_outcomes TEXT,
    long_term_outcomes TEXT,
    referenced_concepts TEXT,
    referenced_outcome_dimensions TEXT,
    confidence REAL DEFAULT 0.5,
    rationale TEXT,
    counter_arguments TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE jpms_school_concept_links (
    id TEXT PRIMARY KEY,
    school_id TEXT NOT NULL REFERENCES jpms_schools(id),
    concept_id TEXT NOT NULL REFERENCES jpms_education_concepts(id),
    relation_type TEXT,
    evidence_summary TEXT,
    source_id TEXT REFERENCES jpms_sources(id),
    confidence REAL DEFAULT 0.5
);

CREATE TABLE jpms_school_outcome_weights (
    id TEXT PRIMARY KEY,
    school_id TEXT NOT NULL REFERENCES jpms_schools(id),
    outcome_dimension_id TEXT NOT NULL REFERENCES jpms_outcome_dimensions(id),
    weight REAL,
    rationale TEXT,
    source_id TEXT REFERENCES jpms_sources(id)
);

-- ============================================================
-- インデックス
-- ============================================================

CREATE INDEX idx_schools_pref ON jpms_schools(location_pref);
CREATE INDEX idx_schools_gender ON jpms_schools(gender_type);
CREATE INDEX idx_schools_religious ON jpms_schools(religious_affiliation);
CREATE INDEX idx_stats_year ON jpms_school_stats(fiscal_year);
CREATE INDEX idx_outcomes_school_year ON jpms_school_outcomes(school_id, fiscal_year);
CREATE INDEX idx_admissions_school_year ON jpms_school_admissions(school_id, fiscal_year);
CREATE INDEX idx_test_school ON jpms_testimonials(school_id);
CREATE INDEX idx_test_speaker ON jpms_testimonials(speaker_category);
CREATE INDEX idx_test_medium ON jpms_testimonials(medium);
CREATE INDEX idx_concepts_subfield ON jpms_education_concepts(subfield);
CREATE INDEX idx_concepts_era ON jpms_education_concepts(era_start);
CREATE INDEX idx_rel_src ON jpms_education_concept_relations(source_concept_id);
CREATE INDEX idx_rel_tgt ON jpms_education_concept_relations(target_concept_id);
CREATE INDEX idx_gh_school ON jpms_growth_hypotheses(target_school_id);
CREATE INDEX idx_scl_school ON jpms_school_concept_links(school_id);
CREATE INDEX idx_scl_concept ON jpms_school_concept_links(concept_id);
CREATE INDEX idx_sources_type ON jpms_sources(source_type);

-- ============================================================
-- 全文検索（FTS5）
-- ============================================================

CREATE VIRTUAL TABLE jpms_testimonials_fts USING fts5(
    excerpt, summary, theme,
    content='jpms_testimonials', content_rowid='rowid'
);

CREATE VIRTUAL TABLE jpms_concepts_fts USING fts5(
    name_ja, name_en, definition, keywords_ja, keywords_en,
    content='jpms_education_concepts', content_rowid='rowid'
);

CREATE VIRTUAL TABLE jpms_schools_fts USING fts5(
    name_ja, name_kana, founding_philosophy, education_principle,
    content='jpms_schools', content_rowid='rowid'
);

-- 初期投入用ID範囲予約（参考メモ）
-- 学校:    jpms_s_0001 - jpms_s_0785
-- 概念:    jpms_ec_0001 - jpms_ec_0800
-- 関係:    jpms_ecr_00001 - jpms_ecr_03500
-- 発言:    jpms_t_000001 - jpms_t_060000
-- 仮説:    jpms_gh_0001 - jpms_gh_2300
-- 出典:    jpms_src_000001 - jpms_src_080000
