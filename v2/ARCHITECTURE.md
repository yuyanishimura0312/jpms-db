# JPMS-DB v2 アーキテクチャ仕様

**バージョン**: v2.0-draft
**作成**: 2026-05-05

## 1. 設計原則

1. **5層分離**: 学校実態（L1）/ 個人特性（L2）/ 成果次元（L3）/ 適合・予測モデル（L4）/ 時代変遷（L5）
2. **一次情報優先**: rights_level と source_id の徹底管理
3. **検証可能性**: 全推定値に source_ref と confidence を付与
4. **再利用性**: ミラツク36DB を View として参照、データ重複なし
5. **倫理保証**: 未成年情報の完全匿名化、削除依頼SOP

## 2. 5層モデル詳細

### Layer 1: 学校実態（Existing Reality）

525校の構造的特徴と実態。一次情報優先。

**主要テーブル**:
- `schools_v2` — 学校マスタ（既存 jpms_schools 拡張）
  - 追加カラム: `homepage_url`, `homepage_archived_at`, `data_completeness_v2`
- `school_philosophy_v2` — 建学理念・教育方針の詳細テキスト（多バージョン保持）
- `school_curriculum_v2` — カリキュラム構成（教科時数、特色プログラム、選択肢）
- `school_admission_v2` — 入試形態、競争率、配点
- `school_progress_record_v2` — 進学実績（年度別、外部公表値のみ）
- `school_facility_v2` — 施設・図書館・実験室・運動施設
- `school_calendar_v2` — 行事・修学旅行・宿泊行事の頻度
- `school_homepage_assets` — HP取得スクリーンショット・アーカイブ

**関係者の声（5主体）**:
- `testimonials_v2` — 主体: principal/teacher/student_current/student_alumni/parent
- 各校で5主体×3名以上の収集を目標
- rights_level: `quoted_with_attribution` / `anonymized_only` / `archive_only`

**外部統計接続**:
- `school_official_stats` — 文科省学校基本調査、学校保健統計の年度別取り込み

### Layer 2: 個人特性（Person Characteristics）

入学前段階の生徒人格を測定するための次元定義。実データではなく「測定枠組み」を保持。

**主要テーブル**:
- `person_trait_dim` — Big Five-J / Growth Mindset / Self-Regulation / GRIT / 動機づけタイプ等の次元定義
- `person_trait_measurement_tool` — 測定ツール（BFI-J/MSCI-J/PSI-J 等）と信頼性係数
- `person_archetype` — 中学受験前段階で観察されうる人格アーキタイプ（理論ベース）
  - 例: 探究志向型、リーダーシップ型、繊細感受型、職人気質型、社交創造型 等

参考理論:
- Big Five Personality（Goldberg 1981, McCrae & Costa）
- Growth Mindset（Dweck 2006）
- Self-Regulated Learning（Zimmerman 2002）
- GRIT（Duckworth 2007）
- 動機づけタイプ（Deci & Ryan SDT）
- Marcia Identity Status

### Layer 3: 成果次元（Outcome Dimensions）

学校卒業時・卒業後5/10/20年の達成軸。25→100+項目に拡張。

**主要テーブル**:
- `outcome_dim_v2` — 100+成果次元の定義
- `outcome_cluster` — 7大クラスタ
  1. 認知・学術
  2. 社会情動
  3. 価値観・道徳
  4. 主体性・市民性
  5. ウェルビーイング
  6. **創造・卓越** （新設）
  7. **市場・経営** （新設）
- `outcome_framework` — フレームワーク参照（OECD/CASEL/PERMA/P21/PISA_WB/JP/Cox/Simonton/Lerner/Collins/Christensen/Sarasvathy/Zuckerman/Dweck/Duckworth等）
- `outcome_era_relevance` — 時代変遷タグ（昭和/平成/令和/2030+/2050+）
- `great_figure_traits` — GF DBから抽出した偉人の幼少期〜青年期特性
- `career_archetype` — 卒業後活躍経路のアーキタイプ
  - serial_entrepreneur / academic_researcher / NPO_leader / corporate_executive / artist_creator / public_intellectual / etc.

### Layer 4: 適合・予測モデル（Fit & Prediction）

個人特性と学校特性の適合関係を表現。数理モデルが参照。

**主要テーブル**:
- `school_culture_dim` — 学校文化5次元
  - autonomy（自律vs規律）
  - structure（構造度、明示的ルール）
  - diversity（多様性、開放度）
  - intensity（学業強度、課題量）
  - mentor_density（教員-生徒関係の親密度）
- `school_culture_score` — 525校 × 5次元のスコア（一次情報から推定）
- `school_typology_lca` — LCAで抽出した日本版学校類型（5-7クラス想定）
- `person_school_fit_rule` — 適合ルール（理論ベース＋実証ベース）
- `fit_prediction_log` — 入力例の予測ログ

**接続するモデル**（Phase F）:
- MLM (`models/mlm.py`) — 個人×学校階層
- IRT (`models/irt.py`) — 成果次元の標準化
- SEM (`models/sem.py`) — 個人特性→適合→成果
- LCA (`models/lca.py`) — 学校類型抽出
- GCM (`models/gcm.py`) — 成長軌跡

### Layer 5: 時代変遷モデル（Era Evolution）

「いつの時代に求められた／求められる人材か」の文脈付与。

**主要テーブル**:
- `era_definition` — 時代区分（明治/大正/昭和前期/昭和後期/平成/令和/2030+/2050+）
- `era_zeitgeist` — 各時代の時代精神（CLA DBの zeitgeist 列を参照）
- `era_required_traits` — 時代別に求められる人物特性（FK/MT/FS/CLA/AA/AD連動）
- `era_school_alignment` — 各校の時代適合度（古典型/移行型/現代型/未来型）

**接続する既存DB**:
- CLA (1900-2026 年 zeitgeist)
- MT (18メガトレンド)
- FK (フォーサイト 309機関 / 45,323レポート)
- FS (未来学知識 99手法 / 17学派)
- AA (LLM親和領域)
- AD (AI発展 LLM+AGI)
- SIF (社会変革 1,096事象)
- GF (歴史人物 9,178人)

## 3. ミラツク36DB 接続マップ

| 既存DB | 用途 | 接続先 |
|---|---|---|
| AK 学術知識DB | 教育心理学理論抽出 | L2/L3 概念辞書 |
| GF 歴史構造DB | 偉人プロファイル | L3 great_figure_traits |
| MG 経営学DB | 経営者特性 | L3 career_archetype (executive) |
| IT イノベーション理論 | 起業家特性 | L3 career_archetype (entrepreneur) |
| MS マーケティング・営業 | 行動経済学 | L2 動機づけタイプ |
| AN 人類学概念 | 学校文化分類 | L1 school_culture_dim |
| MY 神話ナラティブ | アーキタイプ的人格像 | L2 person_archetype |
| SIF SI構造変革 | 社会変革者像 | L3 career_archetype (changemaker) |
| FS 未来学知識 | フォーサイト能力 | L5 era_required_traits |
| FK フォーサイト基盤 | 機関別レポート | L5 zeitgeist |
| MT 18メガトレンド | 社会要請 | L5 era_required_traits |
| CLA 因果階層分析 | zeitgeist 127年 | L5 era_zeitgeist |
| AA LLM親和領域 | AI時代能力 | L5 future-2030+ |
| AD AI発展DB | AGI時代人材論 | L5 future-2050+ |
| EX 有識者DB | 専門家キャリア | L3 alumni_career (specialist) |
| AL 学術ランドスケープ | 研究者分布 | L3 alumni_career (researcher) |
| UPR 大学プレスリリース | アカデミック活動 | L3 alumni_career (researcher) |
| IR VC投資DB | 起業家活躍 | L3 alumni_career (entrepreneur) |
| IC 企業IRDB | 上場企業役員 | L3 alumni_career (executive) |
| SGRD 産学R&D | 産学連携人材 | L3 alumni_career |

## 4. データフロー

```
[一次情報収集]
   ↓ (Phase E)
[Layer 1: 学校実態 v2]
   ↓
[Layer 2: 個人特性次元 / Layer 3: 成果次元] ← (Phase B-3, C 理論注入)
   ↓
[Layer 4: 適合モデル] ← (ミラツク36DB 参照)
   ↓
[Layer 5: 時代変遷] ← (CLA/MT/FK/AA/AD 参照)
   ↓
[数理モデル] (Phase F: MLM/IRT/SEM/LCA/GCM)
   ↓
[ダッシュボード/サンプルレポート v2] (Phase G)
```

## 5. ファイル構成

```
~/projects/research/jpms-db/v2/
├── PLAN.md                       # 全体計画
├── ARCHITECTURE.md               # この文書
├── TEAM.md                       # チーム編成
├── PROGRESS.md                   # 日次進捗
├── THEORETICAL_FOUNDATION.md     # 理論基盤（Phase B-3）
├── MODEL_REPORT.md               # 数理モデル結果（Phase F）
├── schema_v2.sql                 # スキーマ定義
├── jpms_v2.db                    # 統合DB
├── jpms_outcome_dimensions_v2.db # 成果次元専用DB
├── jpms_alumni_career.db         # 卒業生活躍DB
├── data/                         # 集計済みCSV/JSON
├── docs/                         # 公開HTML（v2/index.html等）
├── scripts/                      # 収集・ETLスクリプト
├── models/                       # 数理モデル Python
├── reports/                      # サンプルレポート v2
├── specs/                        # 各フェーズ仕様書
└── raw_html_cache/               # HP取得アーカイブ
```

## 6. 公開ポリシー

| Layer | 公開範囲 | 形態 |
|---|---|---|
| L1 学校実態 | 公開 | CC-BY-NC、ダッシュボード v1 互換 |
| L2 個人特性枠組み | 公開 | 学術参考 |
| L3 成果次元 | 公開（一部非公開） | 個人特定可能部分は非公開 |
| L4 適合モデル | 一部公開 | 適合スコアロジックは公開、原データは非公開 |
| L5 時代変遷 | 公開 | フォーサイト系の延長 |
| 個人データ | 完全非公開 | 内部研究用のみ |

## 7. 数理モデルの妥当性ゲート

各モデルが満たすべき基準:
- MLM: ICC > 0.10, 学校効果サイズ報告
- IRT: Item Information curveとθ範囲妥当性
- SEM: CFI > 0.95, RMSEA < 0.06, SRMR < 0.08
- LCA: BIC最小モデル選択、entropy > 0.80
- GCM: 平均成長率と分散の解釈可能性

不満たしの場合は前フェーズに戻り再設計。
