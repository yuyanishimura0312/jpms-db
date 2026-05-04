# JPMS-DB 必須情報チェックリスト

**作成日**: 2026年5月5日
**目的**: Phase 1で確定すべき必須項目を、各層・各収集ワーカーに引き継げる形で整理する
**準拠**: research-precision-protocol（外部ソース照合・検証なし投入禁止・空欄推測禁止）

---

## 層1: 学校実態の必須項目（35項目／全785校で取得目標）

各校について以下の35項目は最低限取得する。データ不在の場合は空欄ではなく `unknown` または `not_disclosed` で明示する。

### 基本属性（10項目）

1. 正式名称（name_ja）
2. ふりがな（name_kana）
3. 設立年（establishment_year）
4. 学校法人名（school_corporation）
5. 宗教・思想系列（religious_affiliation の8分類）
6. 建学の精神（founding_philosophy、150文字以上）
7. 教育方針（education_principle、150文字以上）
8. 男女共学・別学（gender_type）
9. 中高一貫の形態（integrated_type の4分類）
10. 系列大学（affiliated_university、ない場合 `none`）

### 所在・規模（5項目）

11. 所在都道府県（location_pref）
12. 市区町村（location_city）
13. 住所（address）
14. 最寄駅（nearest_station）
15. 在籍生徒数総数（student_count_total）

### 教育特性（10項目）

16. 探究学習（inquiry_learning, 0/1）
17. STEAM（steam, 0/1）
18. PBL（pbl, 0/1）
19. IBプログラム（ib_program: none/PYP/MYP/DP/CP）
20. 国際教育トラック（international_track, 0/1）
21. ICT強化レベル（ict_strength, 0-3）
22. 芸術強化レベル（art_strength, 0-3）
23. 体育強化レベル（sports_strength, 0-3）
24. 宗教教育（religious_education, 0/1）
25. 第二外国語（second_language、ない場合 `none`）

### 進路・入試（5項目）

26. 直近年度の東大京大合格者数
27. 直近年度の早慶合格者数
28. 直近年度の海外大学進学者数
29. 直近年度の入試倍率
30. SAPIX/四谷大塚/日能研の偏差値（複数併記）

### Web・SNS（5項目）

31. 公式HP URL（website_url）
32. 公式X（sns_x、ない場合 `none`）
33. 公式Instagram（sns_instagram、ない場合 `none`）
34. 公式YouTubeチャンネル（sns_youtube、ない場合 `none`）
35. 主要パンフ・要覧の入手経路（PDF URL or 入手手段）

---

## 層1関連: 関係者発言の必須カテゴリ（各校5件以上）

各校あたり以下の5カテゴリから最低1件ずつ、計5件以上の関係者発言を収集する。

### 必須カテゴリ

1. **校長メッセージ**: 学校HP・パンフ等の公式発言（speaker_category = 'principal', medium = 'school_website' or 'school_brochure'）
2. **教員コラム**: 学校HP・SNS・教育系メディア等の教員発言（speaker_category = 'teacher'）
3. **在校生の声**: 学校HP・パンフ掲載分（speaker_category = 'student_current'、原則匿名化）
4. **卒業生インタビュー**: 学校HP・代表的卒業生紹介（speaker_category = 'student_former'）
5. **保護者の声**: 学校HP・公開ブログ・新聞等（speaker_category = 'parent_current' or 'parent_former'、原則匿名化）

### 各発言で必須のメタデータ

- excerpt（引用テキスト、原則300文字以内）
- summary（要約、100文字以内）
- theme（主テーマ）
- sentiment（positive/neutral/negative/mixed）
- rights_level（public/quoted_with_attribution/anonymized_only/permission_required/withhold）
- source_id（必須、出典なし投入は不可）
- spoken_year（発言時期）

### Phase 1での目標件数

サンプル10校 × 各校5件 = 50件以上を Phase 1で投入する。Phase 2で全785校に展開し、最終的に各校10-15件、合計約8,000-12,000件を目指す。

---

## 層2: 教育学概念の必須150件（Phase 1シードは100件）

サブフィールド別の必須件数は次の通り。各概念は **key_works に Semantic Scholar Paper IDまたはDOI付記必須**（research-precision-protocol準拠）。

### サブフィールド別シード目標

| サブフィールド | Phase 1シード | Phase 2拡張後目標 |
|--------------|--------------|------------------|
| learning_science | 10件 | 60件 |
| motivation_dev | 10件 | 60件 |
| noncognitive | 8件 | 50件 |
| sel | 10件 | 60件 |
| adolescent_dev | 10件 | 60件 |
| career_dev | 5件 | 30件 |
| wellbeing | 8件 | 50件 |
| evidence_based | 5件 | 30件 |
| comparative | 5件 | 30件 |
| japanese_pedagogy | 10件 | 70件 |
| curriculum | 8件 | 50件 |
| assessment | 5件 | 30件 |
| inclusion | 4件 | 30件 |
| sociology_of_ed | 2件 | 20件 |
| **合計** | **100件** | **630件** |

### 必須投入対象（Phase 0優先度A・Bリストから抽出）

**learning_science**:
1. How People Learn (Bransford 2000 + 2018) — National Academies
2. Cognitive Load Theory (Sweller 2011)
3. Multimedia Learning (Mayer 2009)
4. Self-Regulated Learning (Zimmerman & Schunk 2011)

**motivation_dev**:
5. Self-Determination Theory (Deci & Ryan 2020)
6. Growth Mindset (Dweck & Leggett 1988)
7. Self-Efficacy (Bandura 1977)

**noncognitive**:
8. Heckman Skills Formation (Heckman & Mosso 2014)
9. GRIT (Duckworth et al. 2007)
10. OECD Skills for Social Progress (2015)
11. Big Five and Academic Achievement (2021)

**sel**:
12. CASEL 5 Competencies Framework (CASEL 2023)
13. Durlak SEL Meta-Analysis (Durlak et al. 2011)
14. Taylor SEL Long-term Follow-up (Taylor et al. 2017)
15. PATHS Program (Greenberg et al.)

**adolescent_dev**:
16. Erikson Identity vs. Role Confusion (1968)
17. Marcia Identity Statuses (1966)
18. Steinberg Dual Systems Model (2008)
19. Adolescent Brain Development (Casey et al.)

**career_dev**:
20. Super Life-Span Life-Space (1980)
21. Career Construction Theory (Savickas 2005)

**wellbeing**:
22. PERMA Model (Seligman 2011)
23. PISA Happy Life Dashboard (OECD 2024)
24. Children's Worlds Survey

**evidence_based**:
25. Visible Learning (Hattie 2008)
26. EEF Toolkit (2024)
27. WWC Practice Guides (IES)

**comparative**:
28. PISA Programme (OECD ongoing)
29. TIMSS/PIRLS (IEA ongoing)

**japanese_pedagogy**:
30. 学びの共同体（佐藤学）
31. 苅谷剛彦の階層と教育研究
32. 耳塚寛明のSES研究
33. 志水宏吉のつながり格差論
34. 苫野一徳の教育の本質論
35. 奈須正裕のカリキュラムマネジメント

**curriculum**:
36. 探究学習の理論的基盤（OECD 2030）
37. PBL（Project-Based Learning）
38. STEAM教育
39. IB Middle Years Programme

**assessment**:
40. Assessment for Learning (Black & Wiliam 1998)
41. Performance Assessment

**inclusion**:
42. Universal Design for Learning (CAST)
43. Inclusive Education (UNESCO)

**sociology_of_ed**:
44. Bourdieu Cultural Capital (1986)
45. Coleman Report (1966)

これらの45概念をPhase 1のシード必須対象とし、残り55件はサブフィールドの均等性を見ながらPhase 1内で追加投入する。

---

## 層3: 成果次元の必須25個

OECD・CASEL・PERMA・PISA・P21・日本独自指標から重複を排除して25個を確定する。

### 必須成果次元（framework別）

**OECD_LC2030（5次元）**:
1. Knowledge — 学際的知識
2. Skills — Cognitive・Metacognitive・Social-emotional・Practical
3. Attitudes — 学びへの態度
4. Values — Personal・Social・Societal・Human values
5. Transformative competencies — 価値創造・対立調整・責任遂行

**CASEL（5次元）**:
6. Self-Awareness（自己認識）
7. Self-Management（自己管理）
8. Social Awareness（社会的認識）
9. Relationship Skills（対人関係スキル）
10. Responsible Decision-Making（責任ある意思決定）

**PERMA（5次元）**:
11. Positive Emotion
12. Engagement
13. Relationships
14. Meaning
15. Accomplishment

**PISA Happy Life（5次元から代表抽出）**:
16. School environment well-being
17. Peer relationships
18. Achievement & aspirations

**P21／21st Century Skills（3次元）**:
19. Critical thinking
20. Communication & collaboration
21. Creativity & innovation

**日本独自指標（4次元）**:
22. 社会的自立性（Independence in society）
23. 地域貢献意識（Community contribution）
24. 道徳性・倫理観（Moral judgment）
25. 集団協調性（Group harmony skills）

各次元には framework タグ・measurability・relevance_age・定義（地の文100-150文字）を付与する。

---

## 共通レイヤ: 出典の必須付与ルール

すべてのレコードは jpms_sources への参照を伴う。出典なしのレコード投入は技術的に拒否する設計とする。

### 出典の最低要件

- source_type（必須、13分類のいずれか）
- url または publication詳細（書籍はISBN等）
- accessed_at（取得日時）
- rights_status（必須、7分類のいずれか）
- primary_or_secondary（必須）

### 信頼度スコア（reliability_score, 0-100）の運用ルール

- 90-100: 公的統計・査読論文・学校公式（学校HP・パンフ）
- 70-89: 商用書籍（声の教育社等）・主要メディア・公的研究機関報告
- 50-69: 一般メディア記事・専門ブログ・解説サイト
- 30-49: ユーザー生成コンテンツ（口コミ等）・SNS発言
- 0-29: 出所不明・噂・5ch・要検証情報

層1（学校実態）のメイン情報は信頼度70以上のソースのみで構成する。層1関連のtestimonialsは信頼度に応じてrights_levelを連動させる。

---

## チェックリスト運用ルール

Phase 1の収集開始時には、各ワーカーへの指示書に該当する必須項目を埋め込む。Phase 1完了時には、SQLクエリで各必須項目の充填状況を検証する。

```sql
-- 層1必須35項目の充填率検証（例）
SELECT
  '11_pref' AS field,
  COUNT(*) FILTER (WHERE location_pref IS NULL OR location_pref = '') AS missing,
  COUNT(*) AS total
FROM jpms_schools;

-- 関係者発言の各校5件以上検証
SELECT s.id, s.name_ja, COUNT(t.id) AS test_count
FROM jpms_schools s
LEFT JOIN jpms_testimonials t ON t.school_id = s.id
GROUP BY s.id
HAVING test_count < 5;

-- 教育学概念のサブフィールド分布
SELECT subfield, COUNT(*) FROM jpms_education_concepts GROUP BY subfield;

-- 成果次元のframework別件数
SELECT framework, COUNT(*) FROM jpms_outcome_dimensions GROUP BY framework;
```

これらのクエリを Phase 1完了判定の品質ゲートとして機能させる。

---

**作成日**: 2026年5月5日
**作成者**: Claude（academic-db-builder）
**次フェーズ**: Phase 1各ワーカーへの指示書テンプレートに本チェックリストを統合
