# Codex Task: gamma-06 — Team Gamma (卒業生活躍データ連動)

## 担当
GF 歴史人物DB (偉人プロファイル→中学)

## 入力データ
~/projects/research/great-figures-db/data/

## 実行手順

1. GF 歴史人物DB を読み込み、人物レコードを取得
2. 各人物の学歴情報を抽出（中学校卒業時の学校名）
3. JPMS-DB v2 の schools_v2 テーブルと照合
4. マッチした場合、alumni_career テーブルに INSERT

## 出力
- DB: `~/projects/research/jpms-db/v2/jpms_v2.db` の `alumni_career` テーブル
- ログ: `codex_output/gamma-06.jsonl`

## スキーマ
```sql
INSERT INTO alumni_career
(school_id, alumni_anonymous_id, career_field, career_archetype_id,
 achievement_level, source_db_ref, source_record_id, source_url,
 evidence_count, privacy_status)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

## 倫理
- 個人特定可能な情報は alumni_anonymous_id にハッシュ化
- privacy_status='public_record' のみを公開対象
- 未成年情報は完全除外

## 期待出力
- 各DBから推定 500-2,000 人の卒業生 → school_id への紐付け
