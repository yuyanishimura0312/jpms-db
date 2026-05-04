# JPMS-DB: 日本私立中学校 包括的基盤データベース

**プロジェクト名**: jp-private-mid-school-db（JPMS-DB）
**現在のフェーズ**: Phase 0完了 → Phase 1着手準備
**対象**: 日本国内の私立中学校 全785校（令和6年度学校基本調査確定値）

## 概要

日本の私立中学校について、学校実態・教育学術知見・成長軌道仮説の三層を統合する包括的データベースを構築するプロジェクト。一次情報重視、教育学的知見との接続、成長軌道の仮説提示を三本柱とする。

## 主要ファイル

- `scoping_report.md` — Phase 0統合報告書（約32KB）
- `phase1_research_plan.md` — Phase 1リサーチ計画書
- `schema_v0.sql` — DB初版スキーマ（15テーブル + FTS5×3）
- `essential_checklist.md` — 必須情報チェックリスト
- `workers_brief/` — Phase 0ワーカー指示書
- `workers_output/` — Phase 0全10ワーカー出力（約76,000字）
- `deliverables/` — Phase 0統合成果物（scoping_report・schema の重複コピー）
- `jpms.db` — 前ワーカー試作DB（225KB、Phase 1で統合検討）

## Phase 0で確定した主要事項

- 私立中学校 全国785校（東京187校・神奈川63校・大阪61校等）
- 既存集積サービス（みんなの中学校情報10,285校等）と書籍系の構造とカバー範囲
- 学校HP・SNS・ブログ・YouTubeの一次情報入手経路
- 国内主要11学会、海外AERA/EERA/OECD/CASEL等の体系
- 教育学概念14サブフィールド・必須文献45件
- OECD/CASEL/PERMA/PISA/P21/日本独自指標を統合した成果次元
- 国際先行DB（GreatSchools/Niche/SchoolDigger/GOV.UK/Good Schools Guide等）と差別化10項目
- スキーマv0（15メインテーブル+FTS5×3）
- 倫理ポリシー（CC-BY-NC + 一部会員制ハイブリッド推奨）

## Phase 1の主要タスク

1. スキーマv0実環境適用とサンプル10校投入
2. 必須情報チェックリスト確定
3. 学校HP収集パイプライン設計と試作
4. 教育学概念100件のシード投入（Semantic Scholar Paper ID/DOI付記必須）
5. 成果次元20-30個の確定
6. 倫理パイロット運用（10校）
7. 法務監修取得
8. 私学団体・関係機関への通知

詳細は `phase1_research_plan.md` を参照。

## 既知の課題（Phase 1で対応）

- 既存 jpms.db に前ワーカーが別スキーマで部分実装したテーブルが存在。Phase 1冒頭でスキーマv0と統合可否を判断する。
- 宗教系列別の正確な学校数、中高一貫校形態別分類、e-Stat令和6年度詳細データのダウンロードと検証は Phase 1初期で実施。
- 主要私学団体への正式通知、削除依頼受付フォーム整備、CC-BY-NC + 会員制公開モデルの最終確定は Phase 1完了条件。

## 関連DB

本DBはミラツク既存の学術DB群と接続予定：
- mg（経営学概念DB）
- it（イノベーション理論DB）
- academic（5分野学術知識DB）

## ライセンス

CC-BY-NC（Phase 1で最終確定予定）
