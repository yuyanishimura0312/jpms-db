# Codex Task: delta-01 — Team Delta (公的統計取り込み)

## 担当
学校基本調査

## 出典
https://www.e-stat.go.jp/stat-search/files?tstat=000001011528

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
