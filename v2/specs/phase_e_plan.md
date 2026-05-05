# Phase E: 一次情報大規模収集 実行計画

**Phase**: E
**期間**: Week 4-8（最長フェーズ）
**目的**: 528校の一次情報を地道に集積し、5層モデルの実体化を進める

## 概要

| サブフェーズ | 対象 | 目標 | 担当 |
|---|---|---|---|
| E-1 | 学校HP一次取得 | 528校×主要10ページ | engineer + codex |
| E-2 | 公的統計取り込み | 文科省/e-Stat | data-analyst |
| E-3 | 関係者声拡張 | 5主体×3名×528校=7,920件 | researcher |
| E-4 | 卒業生活躍データ | IC/IR/UPR/EX連動 5,000件 | data-analyst |
| E-5 | 家庭関係データ | HoverDS+Epstein 6Types | researcher |

## E-1: HP取得パイプライン

### 倫理規律（絶対遵守）
1. **robots.txt 厳守** — `urllib.robotparser` で取得前に確認
2. **遅延設定** — 同一ドメインへ最低5秒/req
3. **User-Agent明示** — `JPMS-DB-Research/2.0 (research+contact@miratuku.org)`
4. **取得範囲** — 公開ページのみ、ログイン要のページは除外
5. **キャッシュ重視** — 304/200ヘッダで再取得を最小化
6. **取得項目10件まで/校** — 主要ページに限定

### 取得対象ページ（優先順）
1. about/philosophy（建学理念）
2. about/principal（校長メッセージ）
3. curriculum / education（カリキュラム）
4. school_life / events（行事）
5. progress / career（進路実績）
6. message / voice（在校生・卒業生メッセージ）
7. parent / pta（保護者向け）
8. admission（入試案内）
9. facility（施設）
10. news / blog（最新情報）

### 出力
- HTML キャッシュ: `v2/raw_html_cache/<school_id>/<page_slug>.html`
- スクリーンショット: `v2/raw_html_cache/<school_id>/<page_slug>.png`
- メタデータ: `school_homepage_assets` テーブル
- 抽出テキスト: `school_philosophy_v2`, `testimonials_v2`, etc.

### 実行戦略
1. 528校を「HP取得済（既存99校）」「URL有り未取得」「URL未確定」の3群に分類
2. 第1群: 99校 → 補完取得
3. 第2群: URL有り → 順次取得（推定 200-300校）
4. 第3群: URL未確定 → Web検索で補完
5. 取得失敗（404/timeout/robots禁止）はログに記録、再試行は1回のみ

## E-2: 公的統計取り込み

### 対象データ
- 文科省 学校基本調査（毎年、e-Stat）
- 文科省 学校保健統計調査
- 各都道府県教育委員会 私立中学校統計

### 実装
- `scripts/fetch_official_stats.py` — e-Stat API + CSV取得
- `school_official_stats` テーブルに投入

## E-3: 関係者声拡張

### 5主体
| 主体 | 取得元 | 目標/校 |
|---|---|---|
| 校長 | 校長メッセージページ | 1-2件 |
| 教員 | 教員紹介・教科だより | 2-3件 |
| 在校生 | 在校生インタビュー | 3-5件 |
| 卒業生 | 卒業生メッセージ・OBOG会便り | 3-5件 |
| 保護者 | 保護者会便り・PTA挨拶 | 1-2件 |

### 倫理
- 引用は短文＋出典明示（rights_level=quoted_with_attribution）
- 未成年は完全匿名化（rights_level=anonymized_only）
- 削除依頼SOPは48時間以内対応

## E-4: 卒業生活躍データ

### ミラツク36DB連動
| ミラツクDB | 抽出 | 連動方法 |
|---|---|---|
| IC（上場企業役員） | 学歴に私立中名 | 役員プロファイル → school_id 逆引き |
| IR（VC投資） | 創業者プロファイル | 起業家×中学 |
| UPR（大学プレスリリース） | 研究者キャリア | 学術業績×出身校 |
| EX（有識者DB 3,995人） | 審議会委員 | 専門家×中学 |
| AL（学術ランドスケープ） | 論文業績 | 研究者×出身校 |
| GF（歴史構造DB 9,178人） | 偉人プロファイル | 歴史的活躍×中学 |

### 実装
- `scripts/link_alumni_career.py` — 各DBから学歴抽出→ school_id マッチング
- `alumni_career` テーブルに投入

## E-5: 家庭関係データ

### Hoover-Dempsey & Sandler の3層
1. 役割構成（学校が期待する家庭像）
2. 効力感（PTA活動・保護者会の活発度）
3. 資源（家庭での学習支援）

### Epstein 6 Types
1. Parenting / 2. Communicating / 3. Volunteering / 4. Learning at Home / 5. Decision Making / 6. Collaborating with Community

### データ源
- 学校HP「保護者の方へ」セクション
- PTA活動内容
- 保護者会便り
- 学校説明会資料の保護者向け部分

## 実行スケジュール（10セッション運用前提）

| セッション | 主な作業 |
|---|---|
| Session 1 | E-1 パイプライン実装＋12校パイロット取得 |
| Session 2-3 | E-1 残り500校バックグラウンド取得 |
| Session 4 | E-2 公的統計取り込み |
| Session 5 | E-3 関係者声収集（HP由来） |
| Session 6 | E-4 卒業生活躍データ連動（IC/EX/UPR） |
| Session 7 | E-4 続き（IR/AL/GF） |
| Session 8 | E-5 家庭関係データ |
| Session 9 | データ品質検証＋ETL再実行 |
| Session 10 | Phase F 数理モデル本格実装へハンドオフ |

各セッション後に `PROGRESS.md` 更新＋GitHub commit/push。

## KPI（Phase E 完了時点）

| KPI | 目標 | 現状（Phase A-D 完了時） |
|---|---|---|
| HP取得校数 | 420校（80%） | 35校 |
| 建学理念テキスト | 528校全件 | 122校 |
| 関係者声 | 7,000件以上 | 93件 |
| 卒業生活躍紐付け | 5,000件以上 | 0件 |
| 公的統計年度 | 5年分 | 0件 |
| 家庭関係データ | 528校 | 0件 |

## リスク管理

1. **HP取得拒否** — robots.txt厳守＋取得失敗を記録するのみ、強行しない
2. **個人情報リスク** — 未成年情報は完全匿名化、削除依頼SOP稼働
3. **時間ボトルネック** — 並列ワーカー（最大5並列）でスループット確保
4. **データ偏り** — 関東偏重防止のため地方校を優先キューに
