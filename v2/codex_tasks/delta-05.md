# Codex Task: delta-05 — Team Delta (公的統計取り込み)

## 担当
都道府県別私立教育統計

## 出典
各都道府県教育委員会

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
