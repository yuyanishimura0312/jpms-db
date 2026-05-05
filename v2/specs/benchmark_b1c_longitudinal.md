# Benchmark B-1c: 教育縦断研究のデータ構造とJPMS-DB v2への応用ガイド

**フェーズ**: B-1c
**実施**: 2026-05-05
**担当**: researcher エージェント

## 1. 国際的教育縦断研究の比較分析

### Terman Longitudinal Study（1921年開始、IQ135超1,528人）

スタンフォード大学のLewis Termanが開始。サンプルは平均11歳のIQ135以上の児童1,528名（男856・女672）。データ収集は5-10年間隔で1928年、1936年、1940年、1945年、1950年、1955年、後継研究者により1960年、1972年、1977年、1982年、1986年と70年追跡。親・教師・本人・配偶者からの質問票、面接、テスト器材を多層的に組み合わせ、健康・身体情動発達・学歴・職業歴・婚姻関係・死亡率を網羅。1936年までに98%の追跡継続。

**JPMS応用**: 中学入学時の学力測定→大学進学→職業成果の連携データ構造として転用可能。

### Project STAR（テネシー州、1985-1989、7,000人）

79校から7,000人以上、小規模クラス（13-17人）/通常/補助者付きにランダム配置。Stanford Achievement Test、Tennessee Basic Skills Firstと動機づけ・自己概念スコアを学年末ごとに測定。小規模クラスが特に低所得・少数民族児に大きな初期効果、学年が進むにつれ平準化。

**JPMS応用**: 学校環境要因と学習成果の因果関係検証モデル。学校規模別の学習効果比較。

### ECLS-K（米国Early Childhood Longitudinal Study）

NCES主導、幼稚園級〜5年生。3段階サンプリング（PSU→学校→児童）、アジア系・太平洋島嶼民族を過サンプリング。直接認知評価（読み書き・数学・科学・執行機能）、身体測定、社会情動発達、保護者・教師・学校管理者質問票の複層データ。

**JPMS応用**: 多次元的発達指標の並行測定、認知・非認知スキルの相互作用検証。

### British Cohort Study（1958/1970/2000）

NCDS（1958）、BCS70（1970、17,000名以上）、MCS（2000）の3コホート。BCS70は5・10・16・26・30・42歳での測定。健康・身体発達・教育・社会経済を網羅。コホート間で90%の共通項目で世代効果と時代効果を分離。

**JPMS応用**: 複数コホートの並行比較構造で世代効果と時代効果分離。

### Beginning School Study（Baltimore、Entwisle & Alexander）

1982年開始、790人の1年生を28歳まで追跡。20校公立学校から無作為抽出、SES別層化。年1回測定、成人後は数年間隔。標準化テスト、学生・保護者インタビュー、教師質問票、学校記録。「夏期学習ギャップ」の発見で社会経済的不利の累積メカニズムを実証。

**JPMS応用**: 社会経済背景と学習軌跡の精密追跡モデル。

## 2. 分析手法の比較

- **HLM/Multilevel**: 学生→クラス→学校の入れ子構造。Project STARで採用。
- **成長曲線モデル**: 個人発達軌跡の多項式・非線形関数化。ECLS-Kで認知発達差検証。
- **SEM**: 複数の潜在因子と観測変数の統合分析。
- **イベント履歴分析**: 脱学・進学・職業転職等の時間的予測要因。BSSで中1成績→高卒脱学リスク予測。
- **脱落バイアス対策**: Multiple Imputation、WGEE。

## 3. ドロップアウト管理の実務

- Project STAR: 各時点5-10%脱落
- ECLS-K: 5年で15-20%
- BSS: 28年で約31%

対策: 複数連絡先事前収集、年2-4回の多様な接触、報酬提供、オンライン回答、関係者インタビューへの転換。低SES層・少数民族・両親単身世帯はリテンション戦略必須。

## 4. JPMS-DB v2 への応用：日本特化縦断研究プラットフォーム設計

### 測定時点

中学入学(13歳)、中学卒業(16)、高校卒業(18)、大学卒業(22)、25歳、30歳の6時点。在学中3時点は密集、成人期は3-5年間隔。

### サンプルサイズ

初期3,000名（全国私立中学の層別抽出）、目標脱落率30%で各時点2,000名以上を確保。

### 測定変数構造

- 個人特性: WAIS-IV/学力診断、Big Five、Self-Efficacy、Growth Mindset、SDQ、抑うつスクリーニング
- 家族経済: 世帯年収、親学歴、文化資本、母就業
- 学校特性: 学校規模、教員/生徒比、進学実績、活動充実度
- 学習投入: 宿題時間、塾、読書、ICT
- 成果: 各科目学力、大学進学先、初職、キャリア満足度、年収

### スキーマ設計（縦断パネル構造）

```
Person → TimePoint → PersonTimePanel
  ↓
CognitiveAssessment / SocioemotionalAssessment / FamilyBackground /
SchoolCharacteristics / StudyInput / Outcomes
```

### 分析パイプライン

```
Level 1: Achievement_ij = π0i + π1i(Time_ij) + εij
Level 2: π0i = β00 + β01(SES_i) + β02(SchoolSize_i) + u0i
         π1i = β10 + β11(SchoolQuality_i) + u1i
```

### 実装上の注意

- 脱落対策: 5層連絡先（本人携帯/自宅/メール/親族2名）を初期インテーク
- 測定等価性: IRT均等化で各波等価難易度
- データセキュリティ: 識別情報と測定データ分離、暗号化、毎年倫理審査更新
- 資金: 初期1,000万円＋年600万円、20年計1.2億円

## 5. 結論

5研究の焦点は明確に異なる: Termanは高能力児の生涯成果、STARは学校環境因果、ECLS-Kは多次元発達相互作用、BCSは世代比較、BSSはSES累積メカニズム。JPMS-DB v2では中学入学から30歳までの24年追跡で、学校選択の長期成果・SES再生産・非認知スキル発達を同時検証可能。HLMを核とした多層構造分析で個人→クラス→学校→地域の効果分離を実現する。

## 6. 主要参考文献

- Terman Life-Cycle Study: https://atlaslongitudinaldatasets.ac.uk/datasets/terman-life-cycle-study-of-children-with-high-ability
- Project STAR: https://econweb.ucsd.edu/~gelliott/ProjectStar_ch6.html
- ECLS-K: https://nces.ed.gov/ecls/
- BCS70: https://academic.oup.com/ije/article/52/3/e179/6645761
- BSS: https://journals.sagepub.com/doi/10.1177/003804070708000202
- HLM: https://files.eric.ed.gov/fulltext/ED545279.pdf
- Attrition: https://www.sciencedirect.com/science/article/pii/S1326020023046654
