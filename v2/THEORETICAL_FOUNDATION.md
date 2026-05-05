# JPMS-DB v2 理論基盤統合ドキュメント

**作成**: 2026-05-05
**Phase**: B-3
**統合元**: Phase B-1a/b/c/d/e + B-2 の調査結果

## 1. 全体構造

JPMS-DB v2 の5層モデルは以下の理論的基盤に依拠する。

```
Layer 1（学校実態） ← NCES/PISA/TIMSS/UNESCO の構造を参照
Layer 2（個人特性） ← Big Five / SDT / Dweck / Marcia / Lerner Five Cs
Layer 3（成果次元） ← OECD LC2030 / CASEL / PERMA / P21 / 偉人研究 / 経営学 / 起業家研究
Layer 4（適合モデル） ← Eccles Stage-Environment Fit / Holland P-E Fit / Edwards 多次元
Layer 5（時代変遷） ← CLA zeitgeist / MT / FK / FS / AA / AD
```

## 2. Layer 2: 個人特性の理論基盤

### 2.1 Big Five Personality（McCrae & Costa）

中学生段階で測定可能な5因子（O/C/E/A/N）。BFI-Jで信頼性 α=0.74-0.83。BFI-2で完全測定。

### 2.2 Self-Determination Theory（Deci & Ryan）

3基本欲求: 自律性・有能感・関係性。AMS-J、BPNS-Jで測定。中学生段階の動機づけタイプを4類型化（内発・自律・統合・統制・無動機）。

### 2.3 Growth Mindset（Dweck 2006）

「能力は努力で伸びる」信念。MSCIで測定（α=0.80）。学業成果と直接関連（β=0.20-0.30）。

### 2.4 GRIT（Duckworth 2007）

長期目標への情熱と忍耐。Grit-S（8項目、α=0.84）。中学生での妥当性は12歳以降確認済み。

### 2.5 Self-Regulated Learning（Zimmerman 2002）

計画-モニタ-評価のメタ認知サイクル。SRL-Q（α=0.77）。

### 2.6 Marcia Identity Status（1966）

4ステータス（達成/モラトリアム/早期達成/拡散）。中学2-3年での適用可能性が確認されている（EIPQ）。

### 2.7 Lerner Five Cs (PYD)

Competence/Confidence/Connection/Character/Caring。11-19歳で測定不変性確認。中学段階（13-15）で妥当性高い。

### 2.8 推奨される測定構成

中学生段階のJPMS-DB v2では以下を採用:

| 次元 | 測定ツール | α | 重要度 |
|---|---|---|---|
| Big Five 5因子 | BFI-J | 0.74-0.83 | 必須 |
| Growth Mindset | MSCI | 0.80 | 必須 |
| GRIT | Grit-S | 0.84 | 必須 |
| 内発的動機 | AMS-J | 0.86 | 必須 |
| 自律・有能・関係 | BPNS-J | 0.78-0.81 | 高 |
| Identity（探索/確約） | EIPQ | 0.80-0.82 | 高 |
| Five Cs | PYD-Five-Cs | 0.78-0.85 | 中 |
| 自己効力感 | GSES-J | 0.83 | 必須 |

## 3. Layer 3: 成果次元の理論基盤

### 3.1 7大クラスタの根拠

| クラスタ | 主要フレームワーク | 代表理論 |
|---|---|---|
| 認知・学術 | OECD LC2030 / P21 / PISA | Stanovich Critical Thinking, Torrance Creativity |
| 社会情動 | CASEL / PERMA / PISA-WB | CASEL 5要素, Gross Emotion Regulation |
| 価値観・道徳 | OECD / 日本独自 | Kohlberg Moral Reasoning, 文科省道徳教育 |
| 主体性・市民性 | OECD LC2030 / P21 | OECD 変革コンピテンシー, Lerner Contribution |
| ウェルビーイング | PERMA / PISA-WB / Ryff | Seligman, Diener SWLS, Masten Resilience |
| **創造・卓越** | Cox/Simonton/Csikszentmihalyi/Ericsson | Flow, Domain Mastery, Howard Gardner |
| **市場・経営** | Collins/Drucker/Christensen/Sarasvathy/Zuckerman | Level 5, Effectuation, Disruption, Team Science |

### 3.2 偉人・天才・経営者・起業家・研究者の人格特性（既存知見）

#### Cox 1926（300人天才の幼少期）
- 内在的動機（報酬より内的関心）
- 忍耐力と失敗復帰力
- 早期独立心
- 学際的知識の統合能力

#### Simonton 2012/2014
- IQは文化的成就の4-5%のみ説明
- 動機づけ・性格・発展要因がより重要
- 創造的成就は age-curve に従う

#### Lerner Five Cs（PYD）
- Competence/Confidence/Connection/Character/Caring
- Sixth C: Contribution（社会貢献）

#### Collins Good to Great（2001）
- Level 5 Leadership = 謙虚さ + 強い意志
- 「個人的野心 < 組織の目的」が長期成功の鍵

#### Sarasvathy Effectuation（2008）
- Predictive vs. Effectual logic
- 起業家は「予測」ではなく「手持ちリソース＋失敗許容度」で判断
- Bird-in-Hand / Affordable Loss / Crazy Quilt / Lemonade / Pilot in the Plane

#### Zuckerman Scientific Elite（1977）
- Mentor relationship quality が研究者形成の中核
- ノーベル賞受賞者の95%がノーベル賞受賞者をメンターに持つ
- 異分野協働環境（Wuchty 2007 Team Science）

#### Csikszentmihalyi Flow（1990, 1996）
- Challenge-Skill Balance での没入
- 才能開発の必要条件
- 環境設計（フィードバック頻度・自律性）が重要

### 3.3 時代適応指標

各成果次元には era_relevance（meiji〜2050s の8時代×1-10）を付与。
例: AI協働リテラシー（od_cog_010）は reiwa=9, 2030s=10。
変革コンピテンシー（od_ag_001）は heisei=8, reiwa=9, 2030s=10。

## 4. Layer 4: 適合モデルの理論基盤

### 4.1 Lewin の出発点（1936）

B = f(P, E)。全ての適合理論の基礎。

### 4.2 Eccles Stage-Environment Fit（1989, 1993）— 中核理論

中学校移行期での6つの不適合:
1. 教師関係の質低下
2. 自律性の制限
3. 自己意識の上昇 × 社会競争導入
4. 能力評価の公共化
5. カリキュラム難度の急上昇
6. 異学年関係の複雑化

**実証**: 入学初期3ヶ月の段階-環境適合度低が後続3年間の学業・社会的統合をβ≥0.35で説明。

### 4.3 Holland P-E Fit（1959, 1997）

RIASEC 6タイプ。学校選択への拡張で「学校の学習風土・教育方針・生徒文化」と個人の「興味・価値観・能力」のマッチングを評価。

### 4.4 Edwards 多次元 P-E Fit（1991, 2008）

- Demands-Abilities Fit
- Supplies-Values Fit
- 過剰適合 vs 過小適合の非対称的効果

### 4.5 ASA Model（Schneider 1987）

Attraction-Selection-Attrition による組織選別の自己強化サイクル。
日本の私立中学受験では Attraction（学校に魅力を感じる）と Selection（受験で選別される）の両方が働き、入学後の Attrition（離脱）は限定的だが、適合度が低い場合は内向的離脱（不登校・無気力）として現れる。

### 4.6 Hoover-Dempsey & Sandler（1995, 2005）+ Epstein 6 Types

家庭関与の3層: 役割構成・効力感・資源。
Hill & Tyson 2009メタ分析: 中学段階の親関与全体効果d=0.42、学習スキル指導d=0.61。
Epstein 6 Types: Parenting / Communicating / Volunteering / Learning at Home / Decision Making / Collaborating with Community。

日本固有: 「教育ママ」現象は1年目成績向上だが3年で自律性発達阻害＋自己肯定感低下。Authoritative > Authoritarian。

### 4.7 数理モデル化アプローチ

| アプローチ | 特徴 | 必要N | 推奨度 |
|---|---|---|---|
| 直接適合測定 | 単一項目「適合していると思うか」 | 100+ | 第1段階 |
| 差分スコア | D = |P - E| | 200+ | 第1段階 |
| 多項式回帰 + 応答曲面分析 | P, E, P², E², P×E の二次モデル | 200+ | 第2段階 |
| 多次元適合 | Edwards 多次元 + SEM | 300+ | 第3段階 |

## 5. Layer 5: 時代変遷モデルの理論基盤

### 5.1 CLA（Causal Layered Analysis）— Inayatullah 1998

4層: Litany / Systemic causes / Worldview / Myth-Metaphor。
JPMS-DB v2 では1900-2026の127年×4層 = 508レコードを参照。

### 5.2 Three Horizons（Sharpe & Hodgson）

H1（現状）/ H2（移行期）/ H3（未来）の同時並存。
学校文化を H1（伝統的）/ H2（移行的）/ H3（未来志向）に分類可能。

### 5.3 18メガトレンド（ミラツク MT DB）

5メガドメイン × Three Horizons × 5認識論的フレーム。

### 5.4 OECD Future of Skills 2030

39%の中核スキルが2030までに変化。
- Cognitive: 批判思考・創造的思考・分析思考
- Self: レジリエンス・柔軟性・敏捷性
- Social: コラボ・リーダーシップ・社会的影響
- Tools: テクノロジースキル・AIリテラシー

### 5.5 WEF Future of Jobs 2025

Top skills 2025-2030:
1. Analytical thinking
2. Creative thinking
3. Resilience, flexibility, agility
4. Motivation and self-awareness
5. Curiosity and lifelong learning
6. Technological literacy
7. Dependability and attention to detail
8. Empathy and active listening

### 5.6 第4期教育振興基本計画（2023-2027、文科省）

「持続可能な社会の創り手」+「ウェルビーイングの向上」。
JPMS-DB v2 の Layer 5 reiwa の era_required_traits の主要参照源。

### 5.7 AGI時代の人材論（AA + AD DBより）

7段階AGIクリティカルパス（AD DB）に基づく能力要件:
- Stage 1-2: AI協働リテラシー、批判思考
- Stage 3-4: 学際統合、変革コンピテンシー
- Stage 5-7: 人間性再定義、社会変革志向

## 6. 4. 統合フレームワーク

### 6.1 中核モデル

```
個人特性（Layer 2）
   × 学校文化（Layer 4 culture）
   = 適合度 (P-E Fit)
       ↓
   学校文化（Layer 4 culture）
   × 成果次元（Layer 3）
   = 学校が育てる成果プロファイル
       ↓
   時代要請（Layer 5 era）
   × 成果次元（Layer 3）
   = 時代適応度
       ↓
   適合度 × 学校成果プロファイル × 時代適応度
   = 予測スコア（Layer 4 fit_prediction_log）
```

### 6.2 SEM の構造例

```
Endogenous: 卒業時アウトカム（Layer 3 in_school）
↑
Mediating: 学校適合度（Layer 4）
↑
Exogenous (Person): Big Five-J + Growth Mindset + GRIT + SDT + Identity
Exogenous (Environment): 学校文化10次元（Layer 4 culture_score）
Moderator: 家庭関与（Hoover-Dempsey, Epstein）
Time-varying: era_relevance（Layer 5）
```

期待適合度: CFI > 0.95, RMSEA < 0.06, SRMR < 0.08

### 6.3 LCA の構造例

```
Observed indicators: 528校×10学校文化次元 + 進路・規模・宗教・性別
潜在クラス: K=5-7（NYC研究の6クラス枠組み参照）
```

期待モデル選択基準: BIC最小、entropy > 0.80。

## 7. 理論的限界と注意

1. **Holland理論**: 職業選択には有効だが、学校（複数職業環境混在）への直接応用には課題。
2. **Eccles理論**: 「発達ニーズ」の文化差・個人差への対応が未解決。
3. **多項式回帰**: 多重共線性により係数不安定、LASSO/Ridge等の正則化が必要。
4. **PYD Five Cs**: 西洋文化中心の構成で、日本独自次元（集団協調・地域貢献）の追加が必要。

## 8. JPMS-DB v2 のオリジナリティ

既存ベンチマーク（PISA/TIMSS/Coleman/Terman/NCES）に対する優位性:

1. **日本私立中学校特化** — 528校の悉皆構造的データ
2. **5層統合** — 学校×個人×成果×適合×時代の同時モデリング
3. **36DB接続** — 偉人/経営/起業/研究/人類学/神話/未来の統合
4. **時代変遷モデル化** — 過去理解と未来予測の同時実装
5. **予防的適合スコア** — 入学前段階での個別適合予測

## 9. 主要参考文献（30件抜粋）

- McCrae, R. R., & Costa, P. T. (1992). Discriminant validity of NEO-PIR.
- Dweck, C. S. (2006). Mindset: The New Psychology of Success.
- Duckworth, A. (2007). Grit.
- Deci, E. L., & Ryan, R. M. (2000). The "What" and "Why" of Goal Pursuits.
- Marcia, J. E. (1966). Development and validation of ego-identity status.
- Lerner, R. M., et al. (2005). Positive youth development.
- Cox, C. M. (1926). The early mental traits of three hundred geniuses.
- Simonton, D. K. (2014). The Wiley handbook of genius.
- Csikszentmihalyi, M. (1996). Creativity: Flow and the psychology of discovery.
- Collins, J. (2001). Good to great.
- Sarasvathy, S. (2008). Effectuation.
- Christensen, C. (1997). The innovator's dilemma.
- Zuckerman, H. (1977). Scientific Elite.
- Wuchty, S. (2007). The increasing dominance of teams in production of knowledge.
- Eccles, J. S., & Midgley, C. (1989). Stage-environment fit.
- Holland, J. L. (1959, 1997). RIASEC.
- Tinto, V. (1993). Leaving College.
- Edwards, J. R. (2008). Person-environment fit.
- Schneider, B. (1987). The people make the place.
- Hoover-Dempsey, K. V., & Sandler, H. M. (2005). Final report.
- Epstein, J. L. (1995). Six types of parental involvement.
- Steinberg, L. (2008). A social neuroscience perspective on adolescent risk-taking.
- Masten, A. S. (2019). Ordinary magic.
- Inayatullah, S. (1998). Causal Layered Analysis.
- OECD (2019). OECD Learning Compass 2030.
- WEF (2025). Future of Jobs Report.
- 文科省 (2023). 第4期教育振興基本計画.
- 松岡亮二 (2019). 教育格差.
- 耳塚寛明 (2018). 教育格差への処方箋.
- 濱本真一 (2015). 教育機会不平等構造の中の中学校.
