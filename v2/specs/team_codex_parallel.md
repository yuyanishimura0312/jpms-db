# JPMS-DB v2 Phase E チーム編成（Codex 30-40並列）

## 編成方針

Phase E は5つの独立サブフェーズ + 多数のサブタスクに分解できる。Codex の30-40並列を以下のチーム構造で展開する。

## 5チーム × 6-8名 = 30-40並列

### Team Alpha: HP一次取得（10名・E-1）
**役割**: 528校のHP取得を並列分担
- 担当: 各ワーカー50校（重複ドメイン回避のため都道府県別分配）
- ツール: `scripts/fetch_school_hp.py --school-id <id>`
- 倫理: robots.txt厳守、5秒/req遅延、User-Agent明示
- 出力: `school_homepage_assets`, `school_philosophy_v2` (extracted)

| ワーカー | 担当 | 校数 |
|---|---|---|
| Alpha-1 | 東京 1-50 | 50 |
| Alpha-2 | 東京 51-136 | 86 |
| Alpha-3 | 神奈川 全 | 63 |
| Alpha-4 | 埼玉 全 | 33 |
| Alpha-5 | 千葉 全 | 26 |
| Alpha-6 | 大阪・兵庫 | 39 |
| Alpha-7 | 愛知・静岡 | 29 |
| Alpha-8 | 関西残り | 35 |
| Alpha-9 | 中四国・九州 | 80 |
| Alpha-10 | 北海道・東北・北陸 | 87 |

### Team Beta: 関係者声収集（8名・E-3）
**役割**: 公式HP・公開資料から5主体の発言を抽出
- 担当: 各ワーカー65校
- 手法: HPテキスト → GTAコード化 → testimonials_v2 に投入
- 倫理: rights_level 厳格管理、未成年完全匿名化

| ワーカー | 担当主体 | 内容 |
|---|---|---|
| Beta-1 | 校長 | 校長メッセージ抽出 |
| Beta-2 | 教員 | 教員紹介・教科だより |
| Beta-3 | 在校生 | 在校生インタビュー |
| Beta-4 | 卒業生 | OBOG便り・進路実績 |
| Beta-5 | 保護者 | PTA・保護者会 |
| Beta-6 | 全校 | 学校説明会動画文字起こし |
| Beta-7 | 全校 | 学校パンフ画像→OCR→テキスト |
| Beta-8 | 全校 | rights_level審査・倫理レビュー |

### Team Gamma: 卒業生活躍データ連動（8名・E-4）
**役割**: ミラツク36DBから卒業生活躍経路を抽出して school_id に紐付け
- 各ワーカーが特定DBを担当

| ワーカー | 担当DB | 方法 |
|---|---|---|
| Gamma-1 | IC（上場企業役員 7,658件） | 役員プロファイル→学歴抽出→中学逆引き |
| Gamma-2 | IR（VC 4,180組織） | 創業者プロファイル→中学識別 |
| Gamma-3 | UPR（大学PR 14,016件） | 研究者→出身校 |
| Gamma-4 | EX（有識者 3,995人） | 審議会委員→学歴 |
| Gamma-5 | AL（学術 233K journals） | 論文著者→学歴 |
| Gamma-6 | GF（歴史人物 9,178人） | 偉人プロファイル→中学 |
| Gamma-7 | SGRD（産学R&D 11,997件） | R&D責任者→学歴 |
| Gamma-8 | データ統合・重複解消 | 同一人物の複数DBレコード統合 |

### Team Delta: 公的統計取り込み（6名・E-2）
**役割**: 政府・自治体の教育統計データを構造化

| ワーカー | 担当 | 出典 |
|---|---|---|
| Delta-1 | 学校基本調査 | 文科省 e-Stat |
| Delta-2 | 学校保健統計 | 文科省 e-Stat |
| Delta-3 | 全国学力・学習状況調査 | 国立教育政策研究所 |
| Delta-4 | TIMSS/PISA 日本データ | NIER |
| Delta-5 | 都道府県別私立教育統計 | 各都道府県教育委員会 |
| Delta-6 | 学校法人財務 | 文科省学校法人会計基準 |

### Team Epsilon: 家庭関係・追加データ（6名・E-5）
**役割**: 家庭関与・PTA・保護者プログラムの構造化

| ワーカー | 担当 |
|---|---|
| Epsilon-1 | 「保護者の方へ」セクション抽出（HoverDS 3層） |
| Epsilon-2 | PTA活動内容 |
| Epsilon-3 | 保護者会便り |
| Epsilon-4 | 学校説明会の保護者向け部分 |
| Epsilon-5 | Epstein 6 Types 自動分類 |
| Epsilon-6 | 家庭タイプ × 学校特性 適合表生成 |

## 並列実行プロトコル

### 1. タスク配布
- 各ワーカーに `~/projects/research/jpms-db/v2/specs/codex_task_<team>_<id>.md` を生成
- ワーカーは指定範囲のみを処理（重複防止）

### 2. データ書き込みの排他制御
- SQLite はライターロック競合の可能性があるため、各ワーカーは独立 JSONL に出力
- 統合フェーズで JSONL → SQLite 一括 INSERT

### 3. 進捗集計
- 各ワーカーが `progress/<team>_<id>.json` を書き出し
- 監督エージェント（Claude Code）が30秒ごとに集計

### 4. 倫理ゲート
- 各ワーカーは取得前に robots.txt を確認
- 取得失敗時は再試行1回のみ
- 法務監修（legal-advisor）が rights_level を最終確認

## Codex タスク仕様書（テンプレート）

各 Codex ワーカーへ以下を渡す:

```markdown
## Task: <Team>-<ID>

### 担当範囲
<具体的な学校ID範囲、DB名、データタイプ>

### 入力
- DB: ~/projects/research/jpms-db/v2/jpms_v2.db
- スクリプト: ~/projects/research/jpms-db/v2/scripts/<script_name>.py
- 仕様: ~/projects/research/jpms-db/v2/specs/phase_e_plan.md

### 期待出力
- JSONL: ~/projects/research/jpms-db/v2/codex_output/<team>_<id>.jsonl
- 進捗: ~/projects/research/jpms-db/v2/progress/<team>_<id>.json

### 倫理規律（絶対遵守）
- robots.txt 厳守
- 5秒/req 遅延
- User-Agent 明示
- 個人情報は完全匿名化

### 完了条件
- 担当全件処理完了 OR スクリプト終了
- 進捗JSONに status:"completed" を記録
```

## 統合スケジュール

```
Day 1 (今日): Team Alpha + Beta 起動 → Day 1終了時 100校HP取得目標
Day 2: Team Alpha 続行 + Team Gamma 起動 → 累計300校HP, IC/IR連動開始
Day 3: Team Alpha 完了（528校）+ Gamma 完了 + Delta 開始
Day 4: Beta 完了 + Delta 完了 + Epsilon 開始
Day 5: Epsilon 完了、データ統合・品質検証
```

## 監督・統合（Claude Code 中央）

Claude Code はメインプロセスとして以下を担当:
1. タスク配布（codex_task_*.md 生成）
2. 進捗監視（progress/*.json 集計）
3. JSONL → SQLite 統合（毎日）
4. 倫理レビュー監督
5. 依頼者向け日次レポート

実装ファイル: `scripts/team_orchestrator.py`
