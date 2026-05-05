# Codex Task: delta-04 — Team Delta (公的統計取り込み)

## 担当
TIMSS/PISA日本データ

## 出典
https://www.nier.go.jp/timss/

## 実行手順
1. 公開URLから CSV/PDF/Excel をダウンロード
2. パース・正規化
3. `school_official_stats` テーブルに投入

## スキーマ
```sql
INSERT INTO school_official_stats
(school_id, stat_year, stat_source, stat_name, stat_value, stat_unit, source_url)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

## 倫理
- 公開データのみ
- 個人特定可能な情報は除外
- 引用は出典明示
