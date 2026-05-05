# JPMS-DB v2 品質管理プロセス（中央オーケストレーター: opus）

**監督**: Claude Opus 4.7 (1M context) — 中央オーケストレーター兼 QM
**期間**: Phase E 進行中
**チーム規模**: 30-40 名（opus エージェント + Codex協力）

## 役割分担

### 中央オーケストレーター（私 = opus）
- 全フェーズの設計・進行管理
- 各チームへのタスク配布
- 品質ゲート（QM-1〜4）統括
- 統合判断（trade-off の処理）
- 依頼者への進捗報告
- VETO 権の行使（sentinel エージェントと連動）

### チーム A — HP取得（4-8 並列、Codex 協力）
- 役割: 全 528 校の HP 一次取得
- 倫理規律: robots.txt 厳守、5秒/req 遅延、UA 明示
- 出力: school_homepage_assets, raw_html_cache/

### チーム B — 関係者声抽出（opus 5名、HPから抽出）
- B-1 校長メッセージ抽出（opus）
- B-2 教員紹介・教科だより抽出（opus）
- B-3 在校生インタビュー抽出（opus）
- B-4 卒業生メッセージ抽出（opus）
- B-5 保護者声・PTA抽出（opus）
- 出力: testimonials_v2 への JSONL → 一括 INSERT

### チーム C — 卒業生活躍連動（opus 8名、ミラツク36DB連動）
- C-1 GF DB → alumni_career
- C-2 IC DB → 上場企業役員
- C-3 IR DB → VC creators
- C-4 UPR DB → 大学研究者
- C-5 EX DB → 有識者
- C-6 AL DB → 学術ランドスケープ
- C-7 SGRD DB → 産学R&D
- C-8 統合・重複解消

### チーム D — 公的統計詳細取り込み（opus 4名）
- D-1 学校基本調査（年度別・公私別、e-Stat API）
- D-2 学校保健統計（5年分時系列）
- D-3 PISA/TIMSS 詳細データ
- D-4 都道府県別私立教育統計

### チーム E — 家庭関係データ（opus 4名）
- E-1 学校HP「保護者の方へ」抽出
- E-2 PTA活動内容
- E-3 Hoover-Dempsey & Sandler 3層分類
- E-4 Epstein 6 Types 自動分類

### チーム QM — 品質管理（opus 4名）
- QM-1 doc-verify: 4カテゴリ検証（スナップショット不整合・ハルシネーション・カバレッジ・チーム間整合）
- QM-2 sentinel: VETO 権行使、最終ゲート
- QM-3 legal-advisor: 引用倫理・著作権監修
- QM-4 compliance-monitor: 個人情報・規制遵守

## 品質ゲート

各チームの出力は以下のゲートを通過してから DB に統合:

```
[Team B/C/D/E 出力 JSONL]
    ↓
[QM-1 doc-verify: ハルシネーション・カバレッジ検証]
    ↓
[QM-3 legal-advisor: 引用倫理・著作権]
    ↓
[QM-4 compliance-monitor: 個人情報・規制]
    ↓
[opus 統合: trade-off 判断]
    ↓
[QM-2 sentinel: 最終 VETO チェック]
    ↓
[SQLite 一括 INSERT]
    ↓
[ダッシュボード更新 → デプロイ]
```

## 並列実行戦略

### 同時並列上限
- opus エージェント: 同時 5 並列まで
- Codex 並列ワーカー: 同時 30 並列まで（HP取得など機械的タスク）
- 計 35-40 並列

### スケジュール
1. **第1ラウンド** (今): Team B 5名 + Team C 4名 = opus 9 並列 → 既存raw_html_cache から抽出
2. **第2ラウンド**: Team D 4名 + Team E 4名 + Team QM 4名 = opus 12 並列
3. **第3ラウンド**: 統合 + Team B/C/D/E 残り

### opus チーム起動方法
- 並列上限が 5 のため、優先度高チームから順次起動
- 各チームの出力を JSONL（独立ファイル）にして競合回避
- 統合は中央オーケストレーター（opus 私）が一括実行

## ロギング

- `v2/codex_progress/<task_id>.json` — 各チームの完了状態
- `v2/codex_output/<task_id>.jsonl` — 各チームのデータ出力
- `v2/quality_gate.log` — 品質ゲート結果

## 完了基準

| 指標 | 目標 |
|---|---|
| HP取得校 | 420校（80%） |
| 関係者声 | 7,000件 |
| 卒業生活躍紐付け | 5,000件 |
| 公的統計指標 | 50+件 |
| 家庭関係データ | 528校全件 |
| QM 通過率 | 95%+ |

## 倫理規律（全員絶対遵守）

1. robots.txt 厳守
2. 5秒/req 遅延
3. User-Agent 明示
4. 引用は短文＋出典明示
5. 未成年は完全匿名化
6. 削除依頼 SOP 48時間以内
