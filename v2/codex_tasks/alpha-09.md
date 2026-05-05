# Codex Task: alpha-09 — Team Alpha (HP一次取得)

## 担当
中四国・九州前半 (23 schools)

## ファイル参照
- 学校リスト: `codex_tasks/alpha-09_schools.jsonl`
- 取得スクリプト: `scripts/fetch_school_hp.py`
- 共通仕様: `specs/phase_e_plan.md`

## 実行コマンド

```bash
# 1校ずつ取得（5秒/req遅延）
while IFS= read -r line; do
  sid=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['id'])")
  python3 ~/projects/research/jpms-db/v2/scripts/fetch_school_hp.py --school-id "$sid"
done < ~/projects/research/jpms-db/v2/codex_tasks/alpha-09_schools.jsonl
```

## 倫理規律（絶対遵守）
- robots.txt 厳守（urllib.robotparser で確認済）
- 同一ドメインへ 5秒/req 遅延
- User-Agent: `JPMS-DB-Research/2.0 (+research-contact@miratuku.org)`
- 取得失敗は再試行1回のみ
- スクリーンショット保管: `raw_html_cache/<school_id>/`

## 出力
- `school_homepage_assets` テーブル
- `school_philosophy_v2` テーブル（抽出された理念）
- `testimonials_v2` テーブル（抽出された関係者声）
- HTML キャッシュ: `raw_html_cache/<school_id>/<page_slug>.html`

## 進捗報告
完了時に以下を `codex_progress/alpha-09.json` に書き出してください:

```json
{
  "task_id": "alpha-09",
  "team": "alpha",
  "region": "中四国・九州前半",
  "total_schools": 23,
  "completed": <int>,
  "philosophies_added": <int>,
  "testimonials_added": <int>,
  "status": "completed",
  "ts": "<ISO8601>"
}
```

## 期待時間
23 校 × 約60秒/校 = 約23 分
