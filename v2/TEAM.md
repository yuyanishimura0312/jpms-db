# JPMS-DB v2 チーム編成

**作成**: 2026-05-05

## 1. 役割マトリクス

| 階層 | エージェント | モデル | 主担当フェーズ | 役割 |
|---|---|---|---|---|
| 統括 | process-orchestrator | opus | A〜H | 全体進行、Phase間ハンドオフ |
| 設計 | architect | opus | A,D | 5層アーキ精緻化 |
| 仕様 | spec-writer | opus | A〜G | 各フェーズ仕様確定 |
| 品質ゲート | sentinel | opus | 各Phase終了時 | VETO権、独立検証 |
| リサーチ | researcher | haiku | B-1, E | 並列リサーチ |
| 学術検索 | academic-search | sonnet | B-1, B-3 | 学術文献調査 |
| 深掘り | deep-research | opus | B-1 | ベンチマーク詳細 |
| 知識統合 | knowledge-synthesizer | opus | B-2 | 36DB横断統合 |
| 学術DB | academic-oracle | opus | B-3, C | 7学術DB+5補助DB+教科書統合 |
| 概念翻訳 | concept-bridge | opus | B-3 | 学際概念翻訳 |
| 開発 | engineer | sonnet | A,D,E,F,G | 実装全般 |
| DB | db-specialist | sonnet | A,C,D,E | スキーマ・チューニング |
| 解析 | data-analyst | sonnet | E,F | ETL・GTA |
| 統計 | statistical-analyst | opus | F | MLM/IRT/SEM/LCA/GCM |
| デザイン | design | sonnet | G | UI/UX |
| UX統括 | ux-lead | opus | G | ユーザビリティ |
| CI | ci-check | sonnet | G | ミラツクCI準拠 |
| QA | qa-lead | opus | G,H | 機能検証 |
| 文書検証 | doc-verify | opus | G,H | 4カテゴリ検証 |
| 法務 | legal-advisor | sonnet | E,H | 引用倫理・著作権 |
| コンプラ | compliance-monitor | sonnet | E,H | 個人情報保護 |
| Codex | codex-team research | - | B-1, E | 大量並列リサーチ・パース |
| デプロイ | deploy-manager | sonnet | H | 公開・記録 |
| 観測 | monitor-observer | haiku | H 以降 | 公開後ログ・改善 |

## 2. フェーズ別投入チーム

### Phase A（W0、計画基盤）
- リード: process-orchestrator
- 補助: architect / spec-writer / db-specialist
- 検証: sentinel

### Phase B（W1-2、ベンチマーク・理論）
- 並列1（B-1a 国際DB）: researcher + academic-search
- 並列2（B-1b 学校適合理論）: researcher + academic-search
- 並列3（B-1c 縦断研究）: deep-research
- 並列4（B-1d 日本国内）: researcher
- 並列5（B-1e 中学校特化）: researcher + academic-search
- 並列6-13（B-2 既存DB）: knowledge-synthesizer + academic-oracle 各DB
- 統合（B-3）: knowledge-synthesizer + concept-bridge
- 検証: doc-verify + sentinel

### Phase C（W2-3、成果次元DB）
- リード: db-specialist + academic-oracle
- 並列: GF/MG/IT/EX/AL/IR/UPR の各DBから抽出（researcher並列）
- 統合: data-analyst
- 検証: doc-verify

### Phase D（W3-4、個人特性・適合）
- リード: architect + statistical-analyst
- 補助: db-specialist + researcher
- 検証: sentinel

### Phase E（W4-8、一次情報収集）★最重要・最長
- リード: engineer
- 並列5チーム（各110校担当）: engineer + codex-team research
- GTA: data-analyst
- 倫理監修: legal-advisor + compliance-monitor
- 監督: db-specialist
- 検証: qa-lead

### Phase F（W8-9、数理モデル）
- リード: statistical-analyst
- 補助: data-analyst + engineer
- 検証: sentinel + doc-verify

### Phase G（W9-10、ダッシュボード・サンプル）
- リード: design + ux-lead
- 補助: engineer + ci-check
- レポート: article-team（4エージェント企画/ライター/編集/マネージャ）
- 検証: qa-lead + doc-verify

### Phase H（W10、検証・公開）
- リード: deploy-manager
- 補助: doc-verify + legal-advisor + compliance-monitor
- 観測: monitor-observer
- 検証: sentinel（最終ゲート）

## 3. 並列実行パターン

```
Phase B（最大13並列）:
  B-1a, B-1b, B-1c, B-1d, B-1e (5並列)
  B-2 GF, B-2 AK, B-2 MG, B-2 IT,
  B-2 SIF, B-2 FK, B-2 EX, B-2 CLA (8並列)

Phase E（5並列・各110校）:
  E-Worker-1: 関東圏 110校
  E-Worker-2: 関東圏 110校
  E-Worker-3: 関西・中部 110校
  E-Worker-4: 中国・四国・九州 100校
  E-Worker-5: 北海道・東北・北陸 95校
```

## 4. ハンドオフ規律

各フェーズ終了時に以下を必ず作成:

```markdown
## Handoff Briefing
- From: [Phase X owner] → To: [Phase X+1 owner]
- Subject: [何を引き渡すか]
- Intent: 次フェーズの目的
- Rationale: 引き継ぎ判断の根拠
- Completed work: 完了した内容
- Completion criteria: 次フェーズが満たすべき条件
- Open issues: 残っている懸念
- Rejected alternatives: 検討して却下した方法
```

ファイル: `~/projects/research/jpms-db/v2/specs/handoff_phase_*.md`

## 5. Codex連携の運用

Codex は以下の重い処理を分担:
- E-1: 525校HP取得（Playwright並列、5秒/req遅延）
- E-3: 関係者声の機械抽出（GTAコード化前処理）
- F: 数理モデルのコード生成補助
- B-1: 学術文献の大量並列検索

Codex への依頼パターン:
1. Claude Code（メイン）が specs/codex_request_*.md を作成
2. Codex が処理して raw output を返却
3. Claude Code が品質チェック→DB投入

## 6. 監督・進捗

- 日次更新: `PROGRESS.md`（process-orchestrator）
- フェーズ完了時: 依頼者向け `WEEKLY_BRIEFING.md`
- メモリ更新: project_jpms_db.md（フェーズ完了ごと）
