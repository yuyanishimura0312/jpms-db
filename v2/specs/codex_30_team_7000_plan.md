# Codex 30-40名チーム 7,000件達成計画

**中央オーケストレーター**: Claude Opus 4.7（品質管理＋統合判断）
**実行**: Codex 30-40 並列ワーカー
**目標**: testimonials_v2 3,238 → 7,000件（残り3,762件）

## 1. 並列分担マップ（30名構成）

### Group A: 学校ID範囲ベースHP深掘り（10ワーカー）
各ワーカー = 約53校担当（528 ÷ 10）。raw_html_cache 内の HTML を再走査＋追加サブページ取得。

| Worker | 範囲 | 担当 |
|---|---|---|
| A-01 | jpms_s_0001-0050 | 関東圏伝統校TOP50 |
| A-02 | jpms_s_0051-0100 | 関東圏 |
| A-03 | jpms_s_0101-0150 | 関東圏・神奈川 |
| A-04 | jpms_s_0151-0200 | 関東圏・千葉 |
| A-05 | jpms_s_0201-0270 | 埼玉・茨城 |
| A-06 | jpms_s_0271-0350 | 関西圏 |
| A-07 | jpms_s_0351-0420 | 中部・東海 |
| A-08 | jpms_s_0421-0500 | 中国・四国 |
| A-09 | jpms_s_0501-0700 | 九州・沖縄 |
| A-10 | jpms_s_0701-0900 | 北海道・東北・北陸 |

各ワーカーは:
1. 担当範囲の schools_v2 で URL あり HP未取得を fetch
2. 取得済 HTML から追加抽出（V4ロジック準拠）
3. JSONL → `codex_output/team_a_<worker_id>.jsonl`

### Group B: 主体特化抽出（5ワーカー）
全528校全 HTML キャッシュ × 役割特化深掘り。

| Worker | 主体 | 想定収量 |
|---|---|---|
| B-01 | principal | +400件 |
| B-02 | teacher | +400件 |
| B-03 | student_current | +600件 |
| B-04 | student_alumni | +400件 |
| B-05 | parent | +400件 |

### Group C: ページ種別特化（5ワーカー）
HTMLファイル種別ごとに専門化抽出。

| Worker | ページ | 想定 |
|---|---|---|
| C-01 | voice / interview / message | +500件 |
| C-02 | curriculum / education / school_life | +300件 |
| C-03 | progress / career / alumni | +300件 |
| C-04 | parent / pta / family | +300件 |
| C-05 | principal / philosophy / mission | +300件 |

### Group D: 関連DB横断＋公的ソース（5ワーカー）

| Worker | ソース | 想定 |
|---|---|---|
| D-01 | PE DB（PESTLE 196,714） 教育関連記事 | +200件 |
| D-02 | CI DB（Cultural Intelligence） | +100件 |
| D-03 | UPR DB（大学PR）の中高大連携言及 | +100件 |
| D-04 | 文科省学校教育研究所の論文 | +200件 |
| D-05 | 学校発信の公開ニュースリリース | +200件 |

### Group E: 品質改善＋検証（5ワーカー）

| Worker | 担当 |
|---|---|
| E-01 | 重複検出・除去 |
| E-02 | 引用倫理ゲート（rights_level検証） |
| E-03 | 未成年情報マスキング検査 |
| E-04 | speaker_role 再分類精緻化 |
| E-05 | 出典URL 検証＋ broken link 検出 |

## 2. opus オーケストレーター（私）の役割

### 品質管理（QM）
- 各ワーカーの JSONL を統合スクリプトで投入前にゲートチェック
- 引用長 30-400字、source_url 必須、role 妥当性
- 重複（school_id × text[:80] hash）除去

### 統合判断
- ワーカー間の役割競合解消
- 新規挿入と既存更新の判断
- ロールバック判断

### 進捗監視
- 30秒ごとに codex_progress/<worker_id>.json 集計
- ボトルネックワーカーの特定と再投入

## 3. 実行プロトコル

### Step 1: 並列起動
```bash
# Codex 30 ワーカー同時起動（実装は 5 グループ × 6 並列）
for i in {1..30}; do
  task_spec="codex_tasks/team_${i}.md"
  echo "$task_spec"
done
```

### Step 2: バッチ統合
```bash
# 各ワーカー完了時に即時統合
python3 scripts/integrate_codex_30_outputs.py
```

### Step 3: 品質ゲート
```bash
# 投入後の品質検証
python3 scripts/qm1_gate_audit.py
```

### Step 4: 重複除去
```bash
python3 scripts/global_dedup.py
```

### Step 5: デプロイ
```bash
python3 scripts/export_v2_data.py
git add ... && git commit && git push
```

## 4. 倫理規律（30名全員遵守）

1. robots.txt 厳守
2. 5秒/req 遅延（HP fetch 時）
3. User-Agent: `JPMS-DB-Research/2.0 (+research-contact@miratuku.org)`
4. 未成年: 完全匿名化、speaker_attribute は generic
5. 引用: 30-400字、出典URL必須
6. rights_level: quoted_with_attribution / anonymized_only / archive_only
7. 個人特定可能情報: 学年・部活・期数・実名等を generic 化

## 5. 期待スループット

| Group | 想定収量 | 完了想定 |
|---|---|---|
| A 学校ID 10並列 | +1,500件 | 30-60分 |
| B 主体特化 5並列 | +2,200件 | 20-40分 |
| C ページ種別 5並列 | +1,700件 | 20-40分 |
| D 関連DB 5並列 | +800件 | 10-30分 |
| E 品質改善 5並列 | 重複除去 +0件 | 10分 |

合計純増: **+6,200件**（重複除去後 +3,762件以上）
最終目標: testimonials_v2 = 7,000件

## 6. opus オーケストレーター実装

中央オーケストレーター（私）は以下を順次実行:

1. **Codex 30 並列指示書生成**: `codex_tasks/team_<i>.md` × 30本
2. **opus エージェント 5 並列起動**: 各 Group のリーダー役を opus が監督
3. **統合スクリプト事前準備**: integrate_codex_30_outputs.py
4. **品質ゲート実行**: qm1_gate_audit.py
5. **デプロイ**: GitHub Pages へ自動更新

実装即時開始。
