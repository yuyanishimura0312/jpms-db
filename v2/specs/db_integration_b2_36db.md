# DB統合 B-2: ミラツク36DB から JPMS-DB v2 への統合戦略

**フェーズ**: B-2
**実施**: 2026-05-05
**担当**: knowledge-synthesizer エージェント

## 統合の基本思想

JPMS-DB v2 は「日本人の幼少期〜成人期の人格形成・能力発達・社会的役割」を多層的に記述するDB。既存ミラツク36DBはそれぞれ異なる切り口（学術・歴史・経営・神話・未来）から「人間とは」「能力とは」「社会要請とは」を語っており、JPMS の Person Layer / Capability Layer / Era Layer / Society Layer に注ぎ込むことで、単独DBでは到達できない多層解像度を獲得する。

## 各DBの接続戦略（15DB詳細）

### 1. AK（学術知識DB）— 教育心理学レイヤーの理論基盤
- 接続先: Capability Layer / Theory Reference Table
- 抽出: 心理学665理論のうち発達・教育・パーソナリティ系180-220理論
- 例: ピアジェ認知発達、エリクソン心理社会8段階、ヴィゴツキーZPD、Bowlby/Ainsworth愛着、Deci/Ryan SDT、Dweck Growth Mindset、Big Five、Gardner多重知能
- 接続: `jpms_capability.theory_id → ak_psychology_theories.id` のFK＋中間テーブル `capability_theory_bridge`

### 2. GF（歴史偉人DB）— 幼少期人格形成の最重要参照源
- 接続先: Person Profile Layer / Childhood Trajectory Reference
- 抽出: 9,178人物のうち日本人・東アジア人優先 1,500-2,000人。**397幼少期プロファイル＋10意思決定アーキタイプ**が JPMS の核心と直結
- 接続: `jpms_person.archetype_id → gf_decision_archetypes.id`
- 価値: 「渋沢栄一型」「南方熊楠型」「津田梅子型」など具体的アーキタイプ。10アーキタイプ（Visionary/Pragmatist/Synthesizer等）は人格分類軸そのもの

### 3. MG（経営学概念DB）— 経営者人格像
- 接続: Career Trajectory Layer / Executive Capability Profile
- 抽出: 3,458概念中リーダーシップ・組織行動・経営者特性論400-500概念。Level 5 Leadership、Servant、Authentic等
- FK: `jpms_capability_executive.mg_concept_id`

### 4. IT（イノベーション理論DB）— 起業家・創造者像
- 抽出: 9,998件中Entrepreneurship、Effectuation、Disruptive、Creator Personality 600-800件
- 35,939関係から起業家育成系譜抽出

### 5. AN（人類学概念DB）— 学校文化分類の理論基盤
- 抽出: 500概念のうち文化伝達、通過儀礼、学校エスノグラフィー、ハビトゥス、文化資本、隠れたカリキュラム 60-80概念
- 価値: 「進学校型/自由型/伝統型」を人類学的概念（高文脈/低文脈、儀礼密度）で記述

### 6. MY（神話ナラティブDB）— アーキタイプ的人格像
- 抽出: 10,615物語からHero's Journey、Jungian Archetypes（12類型）、日本神話人格類型 300-500アーキタイプ
- 価値: GF（実在）と MY（象徴）を二重化、柳田・河合的視点

### 7. SIF（SI構造変革DB）— 社会変革者像
- 抽出: 1,096事象のうち日本社会変革150-200事象。232関係から系譜
- 価値: NPO・社会起業家のキャリア論の根拠

### 8. FS（未来学知識DB）— フォーサイト能力発達
- 抽出: 448研究者・99手法・507概念から Futures Literacy、Anticipatory Awareness、Three Horizons 100-150単位

### 9. FK（フォーサイト基盤）— 機関別能力要請の言及
- 抽出: 309機関45K件から「2030/2040求められる能力」関連 2,000-3,000言及。WEF、OECD、UNESCO、文科省
- 価値: 「日本社会が必要とする人物像」を世界309機関でクロス検証

### 10. MT（18メガトレンド）— 社会要請の多層タクソノミー
- 抽出: 18メガトレンド全件＋下位カテゴリ
- FK: `jpms_capability.megatrend_id`

### 11. CLA（因果階層分析）— 時代精神変遷
- 抽出: 1900-2026 zeitgeist。4層（Litany/System/Worldview/Myth）×120年=480レコード以上
- **Integrated CLA を使用**

### 12. AA（LLM親和領域DB）— AI時代の能力要件
- 抽出: 551言及・97ドメインから「AI代替/非代替/協働」3類型

### 13. AD（AI発展DB）— AGI時代の人材論
- 抽出: 2,236論文からAGI時代人材論。**7段階AGIクリティカルパス**

### 14. EX（有識者DB）— 専門家キャリアパス
- 抽出: 3,995人の学歴・職歴・転機・著作

### 15. AL（学術ランドスケープ）— 研究者キャリア
- 抽出: 233K journals から日本人研究者出版履歴・分野遷移

## 統合優先順位 TOP10

| 順位 | DB | 理由 | 工数 |
|---|---|---|---|
| 1 | **GF** 歴史偉人 | 397幼少期＋10アーキタイプは JPMS の核心 | 中 |
| 2 | **AK** 学術知識 | 心理学665理論＝JPMS理論的背骨 | 中 |
| 3 | **FK** フォーサイト基盤 | 309機関45K件で社会要請を世界横断根拠化 | 大 |
| 4 | **MT** 18メガトレンド | 軽量＋効果大 | 小 |
| 5 | **CLA** 因果階層分析 | 時代精神120年4層記述 | 中 |
| 6 | **MY** 神話 | アーキタイプ理論で物語深度 | 中 |
| 7 | **MG** 経営学概念 | リーダーシップ理論で成人キャリア像根拠 | 中 |
| 8 | **AA** LLM親和 | AI時代要件のエビデンス | 小 |
| 9 | **IT** イノベーション | 起業家系譜分析 | 中 |
| 10 | **AN** 人類学概念 | 学校文化質的解像度 | 小 |

次点: SIF / FS / AD / EX / AL（Phase 2）

## 統合実装の3原則

1. **FKは強制せず参照型で結ぶ** — JPMS-DB v2 が独立して機能、外部DBは "enrichment layer"
2. **最初の接続はGF×AK×FKの3点セット** — 「人物像×理論的根拠×社会要請」の最小完結ループ
3. **Integrated Dashboard登録前提** — db-registry.json で 32番目DB として登録

## 関連パス

- `~/projects/research/` — 各DB実体
- `~/.claude/projects/-Users-nishimura-/memory/MEMORY.md` — 36DBインデックス
- `~/projects/apps/miratuku-news-v2/` — Integrated Dashboard
