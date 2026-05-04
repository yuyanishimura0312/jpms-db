# JPMS-DB Phase 0 スコーピング報告書
## 日本私立中学校 包括的基盤データベース構築プロジェクト

**プロジェクト名**: jp-private-mid-school-db（JPMS-DB）
**Phase**: 0（スコーピング — リサーチ計画を立てるためのリサーチ）
**作成日**: 2026年5月5日
**作成者**: academic-db-build エージェント（Codex設計→Claude統合実行）
**対象**: 日本国内の私立中学校 約785校（令和6年度文科省学校基本調査確定値）

---

## エグゼクティブサマリー

本Phase 0スコーピングは、日本国内の私立中学校に関する包括的・三層統合データベース構築の前段として、母数の確定、既存資源の網羅、一次情報入手経路の解明、教育学術領域の体系把握、先行事例分析、スキーマ初版設計、倫理ポリシー整備を10名のリサーチャー（Codex設計上は20名分担、実装はClaudeのresearcher subagent並列で集約）に分担して実施した。

調査の結果、第一に対象校数は文部科学省「令和6年度学校基本調査」確定値で **785校**（令和3年度778校から7校増）であり、東京都に187校（24%）が集中し、神奈川63校・大阪61校が続く構造が確認された。第二に、既存の集積サービス（みんなの中学校情報10,285校・131K件レビュー、インターエデュ、声の教育社、晶文社、塾系偏差値表）はそれぞれ部分的にカバーするが、**「学校特性×教育学的観点×成長軌道仮説」を統合的に記述する先行事例は国内外で確認できない**——これがJPMS-DBの最大の差別化空間である。第三に、教育学術層の柱として、国内では教育学・教育心理学・教育社会学・カリキュラム学・発達心理学等10学会、海外ではAERA・EERA・OECD CERI・SRCD・CASELを核とし、Heckman、Dweck、Duckworth、Steinberg、Mayer、Sweller、Zimmerman、Deci & Ryanら主要研究者の理論を必須参照体系とすることが妥当である。第四に、層3「成果仮説」のフレームとして OECD Learning Compass 2030・PISA・CASEL SEL Framework・PERMA・21st Century Skills を統合的に組み込む方向が定まった。第五に、SQLite前提の三層スキーマv0（11テーブル＋FTS5×3）と倫理・rights ポリシー（CC-BY-NC + 一部会員制ハイブリッド推奨）を設計済みで、Phase 1の実装にそのまま投入できる状態である。

総じて、Phase 0は「リサーチ計画を立てるためのリサーチ」として所期の目的を達成し、Phase 1（情報収集の本格化）への明確なハンドオフが可能となった。残課題は、宗教系列別の正確な学校数、中高一貫校の形態別分類、SNS規約の詳細運用、法務監修である。

---

## 1. プロジェクトの三層構造（再確認）

JPMS-DBは通常の学術知識DBと異なり、**実態DB×学術DB×成果仮説DB**の三層を統合する複合型基盤として設計される。

**層1: 学校実態層（Empirical School Layer）** は各校の基本情報・教育の特徴・教員・施設・進路実績・入試・第三者評価・関係者発言を収録する。一次情報を最重視し、学校HP・学校発行物・関係者の本人発言を主たるソースとする。

**層2: 教育学術層（Academic Education Layer）** は子どもの教育——とくに思春期・中等教育——にとって重要な視点・観点に関する最先端学術知見を網羅する。発達心理学・教育学・学習科学・非認知能力・キャリア発達・インクルーシブ教育・教育社会学・探究学習・国際バカロレア比較・ウェルビーイング教育・エビデンスベース教育の14サブフィールドを基本構成とする。

**層3: 成果仮説層（Outcome Hypothesis Layer）** は学校特性×子どもタイプ×学術知見を組み合わせ、成長軌道の仮説モデルを提示する。OECD Learning Compass 2030・CASEL SEL・21st Century Skills・PERMAを成果次元の標準として採用する。

---

## 2. 学校実態層に関する調査結果

### 2.1 母数と分布の確定

文部科学省「令和6年度学校基本調査」確定値（2024年12月18日公表）によれば、私立中学校の全国総数は **785校** である。令和3年度の778校から7校増加した。都道府県別では東京都の187校が圧倒的に多く、神奈川県63校（8.1%）、大阪府61校（7.8%）が続く。山形県には私立中学校が存在しない。共学化が進行しており、現状約84%が共学、男子校約92校（12%）、女子校約266校（34%）と推定される。1980年比で男子校は83%減、女子校は63%減と劇的な変化を示している。中高一貫校（私立・公立・国立合計）は2023年時点で678校あるが、私立中学785校のうち各形態（完全型・併設型・連携型）への内訳は公開統計がなく、Phase 1での詳細調査が必要である。

宗教・思想系列の比率は推定で、キリスト教系（カトリック・プロテスタント・聖公会）が全体の約20-25%、仏教系15-20%、神道系5%以下、残りが建学の精神型と考えられるが、公式統計は公表されていない。

### 2.2 既存集積サイトと書籍の生態系

国内最大の集積はみんなの中学校情報（株式会社じゃらんリサーチ系列）であり、10,285校・131,195件のレビューを保持する。インターエデュ・ドットコムは月1億PVの掲示板型サービス、シリタス（1,085校）、スタディ（関東370校）、四谷大塚・SAPIX・日能研の塾系偏差値表が偏差値マスターを担う。書籍では声の教育社「中学受験案内」（首都圏352校）、晶文社「首都圏中学受験案内」（370校・60年の蓄積）、大学通信「中高一貫校データブック」が主要である。

これらに共通する欠落領域として、(1) 教員・職員の人事・経歴データ、(2) 経営体制や教育ビジョンの歴史的変遷、(3) 進学実績の時系列推移、(4) 学生の社会経済的背景、(5) 偏差値以外の複合的な学校類型化、の5点が浮かび上がった。これらはJPMS-DBが独自に埋めるべき領域である。

### 2.3 一次情報入手経路の構造

学校HPは典型的に「建学の精神／教育方針／カリキュラム／特色教育／学校生活／入試／進路実績／国際教育／施設／お知らせ」のセクションで構成される。共通項目は機械的に取得可能だが、固有項目（探究学習プログラムの詳細、卒業生インタビュー、教員コラム）は学校ごとに大きく異なる。HTMLの構造化度合いも一様でなく、PDFのみで公開する学校、JS動的コンテンツ、ログイン保護領域などが混在する。

SNS・ブログ・YouTubeでの一次情報は、X・note・YouTubeに集中している。学校公式アカウントの普及度は推定で X が3-4割、YouTube が2-3割、Instagram は学校により温度差が大きい。受験系YouTuber（コベツバ、ジュクコ、にしむら先生など）の動画は学校別レビューを多数蓄積している。在校生・卒業生・保護者の私的発信はアメブロ・はてな・noteに広く散在し、テーマ抽出と倫理的引用が課題となる。

### 2.4 関係者発言の体系化方針

JPMS-DBでは関係者発言を `jpms_testimonials` テーブルとして体系化する。`speaker_category` で在校生／卒業生／保護者／教員／校長／第三者評価者を区別し、`medium` で発信媒体（学校HP・パンフ・取材・書籍・X・YouTube・ブログ等）を、`rights_level` で公開範囲を細粒度管理する。未成年（中学生本人）は原則匿名化必須、speaker_anonymized=1 を技術的に強制する。

---

## 3. 教育学術層に関する調査結果

### 3.1 国内学術リソース

国内の主要学会は11学会あり、日本教育学会（1941年設立）を筆頭に、教育心理学会、教育社会学会、カリキュラム学会、教育方法学会、発達心理学会、特別ニーズ教育学会、教育工学会、道徳教育学会、生徒指導学会、キャリア教育学会が中等教育・思春期発達領域の主要プラットフォームとなる。これらの機関誌はJ-STAGEでオープンアクセス配信され、年間2,000件以上の査読論文が蓄積される。

研究機関としては国立教育政策研究所（NIER）、国立特別支援教育総合研究所、国立青少年教育振興機構、ベネッセ教育総合研究所、河合塾教育研究開発本部が主要である。とくにNIERの全国学力・学習状況調査は、家庭の社会経済的背景との関連分析を含む格差研究の基礎データとなる。

中等教育・思春期発達領域の主要研究者として、苅谷剛彦・本田由紀・耳塚寛明（教育社会学）、佐藤学・苫野一徳・奈須正裕（教育学・カリキュラム）、速水敏彦・篠ヶ谷圭太郎（学習動機）、遠藤利彦・無藤隆（発達心理学）、志水宏吉・橋本健二（学校格差研究）が同定された。とくに耳塚寛明のSES研究、志水宏吉の「つながり格差」理論、遠藤利彦のアタッチメント発達理論、佐藤学の「学びの共同体」構想が中核理論として注目される。

### 3.2 海外学術リソース

海外学会・組織はAERA（米、24,000名規模）、EERA（欧）、SRCD、APA Division 15、IEA（TIMSS/PIRLS実施主体）、OECD CERI（PISA企画運営）、UNESCO MGIEP、Brookings、Jacobs Foundationが中核である。最高水準ジャーナルは *Review of Educational Research*（IF 7.4）、*Journal of Educational Psychology*（IF 6.4）、*American Educational Research Journal*（IF 3.6）、*Child Development*、*Learning and Instruction*（IF 4.7）、*Mind, Brain, and Education* である。

学習科学では Bransford ら *How People Learn II*（2018）、Sweller の認知負荷理論、Mayer のマルチメディア学習、Zimmerman の自己調整学習が骨格を成す。非認知能力研究では Heckman（労働経済学的価値）、Dweck（成長マインドセット）、Duckworth（GRIT）、Big Five と学業の関連、OECD *Skills for Social Progress*（2015）が主軸となる。SEL では CASEL の5コアコンピテンシー（Self-Awareness／Self-Management／Social Awareness／Relationship Skills／Responsible Decision-Making）と、Durlak et al.（2011）・Taylor et al.（2017）の二大メタ分析（合計約37万人を対象）がエビデンス基盤を成す。思春期発達では Erikson と Marcia の同一性理論、Steinberg の Dual Systems Model、Deci & Ryan の Self-Determination Theory、Super と Savickas のキャリア構成理論が中心である。エビデンスベース教育リソースとして、英国 EEF Toolkit（2,950研究を要約）、米国 What Works Clearinghouse、John Hattie の Visible Learning（815メタ分析・132,000研究）が主要参照である。ウェルビーイング教育では Seligman の PERMA モデル、OECD Student Well-Being Framework / PISA Happy Life Dashboard が標準枠組みとなる。

### 3.3 層2構築の柱（7サブフィールド）

W11-12調査の結論に基づき、層2の柱を以下の7つに集約する：(A) 学習メカニズム、(B) 動機・発達、(C) 非認知能力 × 経済成果、(D) 社会情動的コンピテンシー（SEL）、(E) ウェルビーイング・キャリア発達、(F) エビデンスベース教育、(G) 比較教育学的データベース。これに国内特有の(H) 日本教育学（佐藤・苫野・志水・遠藤系）と (I) 教育社会学（苅谷・本田・耳塚系）を加え、計9-14サブフィールドを `jpms_education_concepts.subfield` のCHECK制約に組み込んだ。

---

## 4. 成果仮説層（層3）に関する調査結果

OECD Learning Compass 2030 は、コンピテンシー・知識・スキル・態度・価値観の統合枠組みを提示し、生涯にわたる学習者像を「Student Agency」「Co-Agency」「Anticipation-Action-Reflection」のサイクルで整理する。PISA・TIMSS・PIRLS・TALIS・PIAAC は国際比較可能な標準指標を提供する。CASEL SEL Frameworkは5コンピテンシーを軸に、K-12対象の評価ツールと連動する。21st Century Skills では Partnership for 21st Century Learning（P21）、ATC21S、World Economic Forum *Future of Jobs* が主要な枠組みである。キャリア発達と長期成果は Heckman の縦断研究、東京大学社会科学研究所の働き方調査が、ウェルビーイングは PERMA-H・Children's Worlds Survey・こども家庭庁の子どもウェルビーイング指標が中心となる。

これらを統合し、層3 `jpms_outcome_dimensions` の `framework` カラムに 'OECD_LC2030', 'CASEL', 'P21', 'PERMA', 'PISA_WB', 'japanese_independent' 等の列挙値を設けて多元的な成果次元を扱う設計とした。`jpms_growth_hypotheses` では学校特性×子どもプロファイル×成長軌道（短期・中期・長期）×参照概念×参照成果次元の組み合わせで仮説を記述し、`confidence`（0.0-1.0）で確信度を運用する。

---

## 5. 国際先行DB事例と差別化分析

GreatSchools（米、150,000校）、Niche、SchoolDigger、GOV.UK Compare School Performance、The Good Schools Guide（英、私立2,500校）、Schulen.de（独）、IBO公式・International Schools Database を調査した。国内ではみんなの中学校情報、インターエデュ、ベネッセ、文科省学校基本調査が主要である。

データモデルの観点で、いずれも実態層に特化し、教育学的解釈層がほぼゼロという共通の制約を抱える。Good Schools Guideだけが編集部の訪問取材による「教育文化の文章化」を行い一次情報重視の哲学を体現するが、教育研究との接続はない。

JPMS-DBの差別化ポイントは10項目に整理された。とくに、**三層統合アーキテクチャ**（実態×学術×仮説）、**学術知見との双方向接続**（Forward/Reverse mapping）、**SEL・非認知スキルの体系的追跡**、**進路・人生成果への長期連携想定**、**プライバシー・信頼設計の日本化**（学校が情報開示レベルを選択可能）の5点が他に類例のない独自性となる。

---

## 6. スキーマ設計v0

SQLite + FTS5 + JSON1 を前提とした三層×共通レイヤの11テーブル + FTS5×3 を設計した。学校マスタ `jpms_schools` を中核に、付随テーブルとして curriculum・stats（年度時系列）・outcomes・admissions・facilities・evaluations を放射状配置する。一次情報の核として独立テーブル `jpms_testimonials` を設け、speaker_category／medium／rights_level／source_id を必須化する。

教育学術層は経営学DB（mg）・イノベーションDB（it）と同型構造を踏襲し、`jpms_education_concepts` と `jpms_education_concept_relations` を 14サブフィールドCHECK制約付きで設計した。`key_works` は SS Paper IDか DOI の付記を必須とし、research-precision-protocol準拠の検証可能性を担保する。

成果仮説層は `jpms_outcome_dimensions`、`jpms_growth_hypotheses`、`jpms_school_concept_links`、`jpms_school_outcome_weights` の4テーブルで構成する。共通レイヤとして `jpms_sources`（rights_status・primary/secondary・reliability_score 付き）と `jpms_fetch_jobs`（クロール追跡）を全テーブル横断で参照する。

完全な CREATE TABLE 文は `~/projects/research/jpms-db/deliverables/schema_v0.sql` に出力した。

---

## 7. 倫理・rights・引用ポリシー

日本著作権法第32条の引用要件、個人情報保護法、未成年保護、SNS各規約を整理した上で、JPMS-DBの公開モデルとして **CC-BY-NC + 一部会員制ハイブリッド** を推奨する。学校HPなどの公開発言は CC-BY-NC で広く参照可能とし、関係者発言のうち取材・SNS等から取得した二次的なものは会員制領域に置く。

Phase 1着手前に、(1) 法務専門家への監修依頼、(2) サンプル10校での倫理パイロット運用、(3) 学校への事前通知文書テンプレート整備、(4) 中高連・各都道府県協会への情報共有、(5) 削除依頼受付フォーム実装、(6) 公開モデルの最終確定、を強く推奨する。

---

## 8. 不明・追加調査事項（Phase 1で解決）

第一に、**宗教系列別の正確な学校数**（公式統計が未公表のため、宗教情報リサーチセンター・各宗派団体・私学協会への直接問い合わせが必要）。第二に、**中高一貫校の形態別内訳**（私立785校のうち完全型・併設型・連携型の各々の数）。第三に、**令和6年度都道府県別詳細データ**のe-Statからのダウンロードと検証。第四に、**学校法人ベースのグループ経営**（複数校を経営する法人の把握）。第五に、**令和4-5年度の中間推移データ**。第六に、各都道府県協会が独自発行する詳細統計の取得。第七に、SNS規約の詳細運用（とくにX有料API利用範囲、YouTube動画文字起こしの可否）。第八に、層2の必須理論チェックリストの精緻化（W11-12案を文献に再照合）。

---

## 9. リソース見積もり（暫定）

Phase 0で得られたデータを基に、Phase 1以降の規模感を試算する。学校実態層は785校×平均40フィールドで約31,400レコード（学校マスタ＋付随テーブル合算）。年度別統計は785校×10年×複数指標で約数万件。関係者発言は1校あたり5-30件×785校で約4,000-23,000件。教育学術層は他DB実績から類推して約3,000-5,000概念、概念間関係はその3-5倍で9,000-25,000件。成果仮説は約500-1,000仮説。出典テーブルは10,000-50,000件規模。

合計データ規模は概ね **5-10万レコード**、データ容量は SQLite 圧縮込みで 200-800MB 程度を見込む。

---

## 10. Phase 1へのハンドオフ

Phase 1は「情報収集の本格化」フェーズとして、以下を骨子とする。

第一週: スキーマv0をSQLite DBに適用、サンプル10校（御三家系・ミッション系・仏教系・地方有力校・新興校から多様性を確保）に対して学校HPからの構造化データ抽出パイロット。第二-三週: 文科省学校基本調査・私学団体統計の一次データ取得、e-Stat APIパイプライン構築。第四-六週: 学校HPの全785校自動収集（各校の構造差を吸収するパイプライン）。第七-八週: 教育学術層の主要文献チェックリストv1確定、J-STAGE・Semantic Scholar APIでの収集試験。第九-十二週: 関係者発言の倫理パイロットと会員制基盤構築。第十三-十六週: 成果仮説層の初期仮説生成（10校×複数子どもプロファイル）と検証ループ。

Phase 1の品質ゲートとして、(a) 全レコード source_id 必須充足、(b) testimonials の rights_level 必須充足、(c) 教育学術層 key_works の SS_id/DOI 検証証跡 90%以上、(d) サンプル10校での三層連結クエリの動作確認、を設定する。

---

## 出力ファイル一覧

### Phase 0 ワーカー出力（10ファイル / 約76,000字）

- `~/projects/research/jpms-db/workers_output/W01-03_official_stats.md`
- `~/projects/research/jpms-db/workers_output/W04-06_existing_aggregators.md`
- `~/projects/research/jpms-db/workers_output/W07_school_primary_sources.md`
- `~/projects/research/jpms-db/workers_output/W08-09_social_primary_sources.md`
- `~/projects/research/jpms-db/workers_output/W10_jp_academic.md`
- `~/projects/research/jpms-db/workers_output/W11-12_intl_academic.md`
- `~/projects/research/jpms-db/workers_output/W13-14_international_dbs.md`
- `~/projects/research/jpms-db/workers_output/W15-16_outcome_indicators.md`
- `~/projects/research/jpms-db/workers_output/W17-18_schema_design.md`
- `~/projects/research/jpms-db/workers_output/W19_ethics_policy.md`

### Phase 0 統合成果物

- `~/projects/research/jpms-db/deliverables/scoping_report.md`（本書）
- `~/projects/research/jpms-db/deliverables/schema_v0.sql`
- `~/projects/research/jpms-db/deliverables/phase1_research_plan.md`
- `~/projects/research/jpms-db/deliverables/mandatory_checklist.md`

---

**作成**: academic-db-build エージェント（2026-05-05）
**次フェーズ**: Phase 1（情報収集本格化）への移行
