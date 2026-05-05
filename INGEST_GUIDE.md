# JPMS-DB Phase 3 取り込み運用ガイド

関係者発言（testimonials）を Markdown 素材ファイルから自動で `jpms.db` に投入するためのガイドです。Phase 3 の自動化対象は **`reports/material_*.md` → `jpms_testimonials` + `jpms_sources`** の経路です。

---

## 1. 全体像

```
reports/material_w*.md   ──parse──>  Statement[]  ──resolve──>  jpms_schools.id
                                                  ──upsert──>   jpms_sources
                                                  ──insert──>   jpms_testimonials
```

- パース: `### #N` ブロック（または `### テーマX`）から「立場 / sentiment / テーマ / 発言 / 出典」を抽出
- school_id 逆引き: `jpms_schools.name_ja` に対するファジーマッチ（接尾辞除去・包含一致）
- 重複検知: 既存 `(school_id, excerpt[:60])` で同一発言を再投入しない
- sources は URL またはタイトルで一意化

スクリプト本体:

| ファイル | 役割 |
|---|---|
| `scripts/ingest_testimonials.py` | パース・投入のメインパイプライン |
| `scripts/quality_check.py` | 件数・ネガ有無・立場多様性のチェック |

---

## 2. Markdown 素材ファイルの推奨フォーマット

新規に取り込み用ファイルを書くときは、次のテンプレートに従ってください。
パーサは多少の表記ゆれ（H1/H2見出し、`**立場**` の有無、引用 `>` ブロック等）を吸収しますが、**この骨格に従えば確実に取り込めます**。

```markdown
# 学校名（中学校までフルネーム）

## 元データ量サマリー
（任意の自由記述。パース対象外）

## 発言一覧

### #1
- 立場: 中3在校生（内部進学組）
- sentiment: positive
- テーマ: 自由な校風と人間関係
- 発言: > 引用テキストをここに。複数行も可。
- 出典: みんなの中学校情報（保護者口コミ） https://example.com/...

### #2
- 立場: 2020年卒業の社会人
- sentiment: negative
- テーマ: 内部進学制度の課題
- 発言: > 別の引用テキスト
- 出典: プレジデント社『記事タイトル』 https://...
```

### 複数校を1ファイルに含める場合

`## 開成中学校` / `## 海城中学校` のように **学校ごとに H2 見出し**で区切ると、それぞれの学校に正しく振り分けられます。

```markdown
# 関係者発言レポート（開成・海城）

## 開成中学校

### #1
- 立場: ...
- sentiment: ...
（中略）

## 海城中学校

### #1
- 立場: ...
（以下同様）
```

### キー名の表記ゆれ

| 想定キー | 受理する表記例 |
|---|---|
| 立場 | `- 立場:` / `- **立場**:` / `**立場**:` |
| sentiment | `sentiment:` / `Sentiment:` / `**sentiment**:` |
| テーマ | `- テーマ:` |
| 発言 | `- 発言:` / 引用ブロック `> ...` のみでも可 |
| 出典 | `- 出典:` / `**出典**:` |

---

## 3. 値マッピングのルール

### 立場 → speaker_category

「立場」フィールドの文字列に対し、以下のキーワードが含まれていれば自動分類します（先勝ち）。

| キーワード | speaker_category |
|---|---|
| 校長 / 理事長 / 学園長 / 学長 / 教頭 / 副校長 | `principal` |
| 教員 / 教諭 / 教師 / 先生 | `teacher` |
| 元在校生 / 卒業 / OB / OG | `student_former` |
| 在校生 / 在籍 / 中1 / 中2 / 中3 / 高1 / 高2 / 高3 / 生徒 | `student_current` |
| 元保護者 | `parent_former` |
| 保護者 / お母さん / お父さん / ママ / 親 | `parent_current` |
| 評論家 / 教育評論家 / 研究者 / ジャーナリスト / 記者 | `external_evaluator` |
| 塾講師 / 予備校 / 塾 / 議員 | `third_party` |

ヒットしない場合は `third_party`。複数キーワードに該当する場合は **上の表で先にあるルールが優先** されます（校長＞教員＞卒業生＞在校生＞保護者）。

### sentiment

`positive` / `neutral` / `negative` / `mixed` の4値。`neutral/positive` のような複合表記は最初を採用、不明値は `neutral` に丸めます。

### medium / source_type 推定

「出典」フィールドの文字列から `medium` (testimonials)、`source_type` (sources) を推定します。例: `youtube` → `youtube` / `sns_youtube`、`新聞|日経|プレジデント|東洋経済` → `newspaper`、`note|ameblo|ブログ` → `blog` / `blog`、`学校HP|公式サイト|学校説明会` → `school_website`。該当なしは `other`。

### rights_level

すべて `quoted_with_attribution` で固定（短文引用＋出典明記の運用ポリシーに整合）。

---

## 4. 実行手順

### 4.1 ドライラン（推奨：まず必ず実行）

```bash
cd ~/projects/research/jpms-db

# 単一ファイルで試す
python3 scripts/ingest_testimonials.py --dry-run --verbose reports/material_w110_azabu.md

# reports/ 配下の material_*.md を一括ドライラン
python3 scripts/ingest_testimonials.py --dry-run --all --verbose
```

ドライランでは DB に書き込みません。出力で次を確認します。

- `[MATCH] 学校名 → school_id (N件)` … 各ファイルから抽出された件数
- `[UNMATCHED]` … 該当する school_id が `jpms_schools` に無い学校
- `[SKIP]` … 学校見出しまたは `### #N` ブロックが検出できなかったファイル
- `エラー: ...` … スキーマ違反など

### 4.2 本番投入

```bash
# 単一ファイル
python3 scripts/ingest_testimonials.py reports/material_w110_azabu.md

# 一括投入
python3 scripts/ingest_testimonials.py --all
```

トランザクションは1コネクション1コミットなので、途中エラーが出た場合は `git stash` 等で `jpms.db` を元に戻して再実行してください（DB はリポジトリ管理対象）。

### 4.3 DB 現状サマリー

```bash
python3 scripts/ingest_testimonials.py --summary
```

525校中いくつが testimonial 5件以上か、0件はどこか、未対応都道府県（DBに学校未登録）はどこかを表示します。

### 4.4 品質チェック

```bash
# 全体の達成度ダッシュボード
python3 scripts/quality_check.py --dashboard

# 1件以上ある学校の詳細
python3 scripts/quality_check.py

# 特定校
python3 scripts/quality_check.py --school jpms_s_0002
```

各校で以下3条件をチェックします。

- **件数**: 5件以上か
- **ネガティブ発言**: `sentiment='negative'` を1件以上含むか
- **立場多様性**: 在校生／卒業生／保護者のうち2種以上を含むか

---

## 5. 未マッチ学校の扱い

ドライランで `[UNMATCHED]` と表示された場合の対処:

1. `jpms_schools` テーブルに該当校が登録されているか確認
   ```bash
   sqlite3 jpms.db "SELECT id, name_ja FROM jpms_schools WHERE name_ja LIKE '%栄光%';"
   ```
2. 未登録ならまず `seeds/*.sql` 経由で学校マスタを追加
3. 登録済みだが名称が一致しない場合は、素材ファイルの H2 見出しを正式名に揃えるか、`name_short` を `jpms_schools` に追加する

---

## 6. 既知の制約と将来課題

### 6.1 取り込めない素材ファイルパターン

- `### #N` ブロックも `### テーマX` ブロックも持たないファイル（要約のみ・空ファイル）
- 例: `material_w101_salesio_kaijo.md`（要約のみ）、`material_w112_seiko.md`（要約のみ）
- 対応方針: 要約のみのファイルは Phase 3 では対象外。必要なら個別に発言ブロック化したリビジョン版を再生成してください。

### 6.2 学校未登録県

`三重県` `山形県` `秋田県` は `jpms_schools` 自体に登録ゼロ。Phase 4 で当該県の学校マスタ整備が必要。

### 6.3 重複判定の精度

現状 `excerpt[:60]` の前方一致のみで判定。発言文の言い換え（例: 同じ趣旨を別の引用元で言い直したもの）は重複扱いされず別行として残ります。発言の概念単位での重複統合は Phase 4 以降で検討。

### 6.4 speaker_name

匿名引用が多いため `speaker_name` は常に `NULL`、`speaker_anonymized=1` で固定しています。実名引用が必要なケースは別パイプラインで対応してください。

---

## 7. 推奨運用フロー（毎週）

1. 新しい素材ファイルを `reports/material_<wave>_<school>.md` として配置
2. `python3 scripts/ingest_testimonials.py --dry-run --all --verbose` で検証
3. `[UNMATCHED]` がある場合は学校マスタを先に整備
4. `python3 scripts/ingest_testimonials.py --all` で投入
5. `python3 scripts/quality_check.py --dashboard` で全体カバレッジを確認
6. `git add jpms.db && git commit -m "feat: ingest testimonials wave NN"`
7. 重要な仕様変更（マッピングルール追加など）はこの `INGEST_GUIDE.md` も更新

---

## 8. トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| 全件 `[SKIP]` になる | ファイルに `### #N` も `## 学校名` も無い | テンプレートに沿って書き直す |
| `[UNMATCHED]` | 学校が `jpms_schools` 未登録 | 学校マスタ追加 |
| `SQL error: CHECK constraint failed: speaker_category` | speaker キーワードがどれにも該当せず `third_party` 以外を返している | `SPEAKER_RULES` に追加 |
| `medium` が `other` ばかり | 出典文字列にキーワードが無い | `MEDIUM_RULES` に追加 |
| 重複だが投入したい | excerpt 先頭60字が完全一致 | 一時的に `is_duplicate` を無効化、または元データを微修正 |

---

最終更新: 2026-05-04（Phase 3 初版）
