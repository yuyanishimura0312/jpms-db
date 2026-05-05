#!/usr/bin/env python3
"""Team orchestrator: divide schools into parallel batches for Codex worker dispatch.

各バッチを Codex ワーカーに渡せる形（task_*.md, school list）に変換。
バッチごとに独立した DB writes を許容するため、JSONL output を採用。
最終的に Claude Code が JSONL → SQLite 統合。
"""
import sqlite3
import json
import argparse
from pathlib import Path
from collections import defaultdict

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')
TASKS_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_tasks')
PROGRESS_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_progress')
OUTPUT_DIR = Path('/Users/nishimura+/projects/research/jpms-db/v2/codex_output')

TEAM_ALPHA_BATCHES = [
    ('alpha-01', '東京 part1', "location_pref='東京都' ORDER BY id LIMIT 50"),
    ('alpha-02', '東京 part2', "location_pref='東京都' ORDER BY id LIMIT 50 OFFSET 50"),
    ('alpha-03', '東京 part3', "location_pref='東京都' ORDER BY id LIMIT 50 OFFSET 100"),
    ('alpha-04', '神奈川', "location_pref='神奈川県' ORDER BY id"),
    ('alpha-05', '埼玉・千葉', "location_pref IN ('埼玉県','千葉県') ORDER BY id"),
    ('alpha-06', '大阪・兵庫・京都', "location_pref IN ('大阪府','兵庫県','京都府') ORDER BY id"),
    ('alpha-07', '愛知・静岡・岐阜', "location_pref IN ('愛知県','静岡県','岐阜県') ORDER BY id"),
    ('alpha-08', '関西残り', "location_pref IN ('奈良県','和歌山県','滋賀県','三重県') ORDER BY id"),
    ('alpha-09', '中四国・九州前半', "location_pref IN ('広島県','岡山県','山口県','香川県','徳島県','愛媛県','高知県') ORDER BY id"),
    ('alpha-10', '九州・沖縄', "location_pref IN ('福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県') ORDER BY id"),
    ('alpha-11', '北海道・東北', "location_pref IN ('北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県') ORDER BY id"),
    ('alpha-12', '北陸・甲信越', "location_pref IN ('新潟県','富山県','石川県','福井県','長野県','山梨県','茨城県','栃木県','群馬県') ORDER BY id"),
]


def make_alpha_tasks(db):
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Team Alpha (HP取得) タスク生成 ===\n")
    total_schools = 0
    for task_id, region, where in TEAM_ALPHA_BATCHES:
        rows = db.execute(f"""SELECT id, name_ja, homepage_url FROM schools_v2 WHERE {where}""").fetchall()
        total_schools += len(rows)
        if not rows:
            print(f"  {task_id}: 0 schools (skip)")
            continue

        # Save school list as JSONL
        list_file = TASKS_DIR / f"{task_id}_schools.jsonl"
        with list_file.open('w') as f:
            for r in rows:
                f.write(json.dumps({'id':r[0], 'name':r[1], 'url':r[2]}, ensure_ascii=False) + '\n')

        # Save task spec markdown
        task_md = TASKS_DIR / f"{task_id}.md"
        task_md.write_text(f"""# Codex Task: {task_id} — Team Alpha (HP一次取得)

## 担当
{region} ({len(rows)} schools)

## ファイル参照
- 学校リスト: `codex_tasks/{task_id}_schools.jsonl`
- 取得スクリプト: `scripts/fetch_school_hp.py`
- 共通仕様: `specs/phase_e_plan.md`

## 実行コマンド

```bash
# 1校ずつ取得（5秒/req遅延）
while IFS= read -r line; do
  sid=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['id'])")
  python3 ~/projects/research/jpms-db/v2/scripts/fetch_school_hp.py --school-id "$sid"
done < ~/projects/research/jpms-db/v2/codex_tasks/{task_id}_schools.jsonl
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
完了時に以下を `codex_progress/{task_id}.json` に書き出してください:

```json
{{
  "task_id": "{task_id}",
  "team": "alpha",
  "region": "{region}",
  "total_schools": {len(rows)},
  "completed": <int>,
  "philosophies_added": <int>,
  "testimonials_added": <int>,
  "status": "completed",
  "ts": "<ISO8601>"
}}
```

## 期待時間
{len(rows)} 校 × 約60秒/校 = 約{len(rows)*60//60} 分
""")
        print(f"  {task_id}: {len(rows)} schools — {region}")

    print(f"\n合計: {total_schools} 校（重複除く実数）")
    return total_schools


def make_gamma_tasks(db):
    """Team Gamma: alumni career linking from miratuku 36 DBs."""
    print("\n=== Team Gamma (卒業生活躍データ連動) タスク生成 ===\n")

    GAMMA_BATCHES = [
        ('gamma-01', 'IC 上場企業役員DB', '~/projects/research/miratuku-news-v2/data/ic.db', '役員プロファイルから学歴抽出→中学逆引き'),
        ('gamma-02', 'IR VC投資DB', '~/projects/research/investment-signal-radar/data/', '創業者プロファイル→中学識別'),
        ('gamma-03', 'UPR 大学PR', '~/projects/research/miratuku-news-v2/data/upr.db', '研究者→出身校'),
        ('gamma-04', 'EX 有識者DB', '~/projects/research/miratuku-news-v2/data/ex.db', '審議会委員→学歴'),
        ('gamma-05', 'AL 学術ランドスケープ', '~/projects/research/academic-landscape-db/data/', '論文著者→学歴'),
        ('gamma-06', 'GF 歴史人物DB', '~/projects/research/great-figures-db/data/', '偉人プロファイル→中学'),
        ('gamma-07', 'SGRD 産学R&D', '~/projects/research/miratuku-news-v2/data/sgrd.db', 'R&D責任者→学歴'),
        ('gamma-08', '統合・重複解消', None, '同一人物の複数DBレコード統合'),
    ]

    for task_id, db_name, db_path, method in GAMMA_BATCHES:
        task_md = TASKS_DIR / f"{task_id}.md"
        task_md.write_text(f"""# Codex Task: {task_id} — Team Gamma (卒業生活躍データ連動)

## 担当
{db_name} ({method})

## 入力データ
{db_path or '前段(gamma-01〜07)の出力 JSONL'}

## 実行手順

1. {db_name} を読み込み、人物レコードを取得
2. 各人物の学歴情報を抽出（中学校卒業時の学校名）
3. JPMS-DB v2 の schools_v2 テーブルと照合
4. マッチした場合、alumni_career テーブルに INSERT

## 出力
- DB: `~/projects/research/jpms-db/v2/jpms_v2.db` の `alumni_career` テーブル
- ログ: `codex_output/{task_id}.jsonl`

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
""")
        print(f"  {task_id}: {db_name}")


def make_delta_tasks():
    """Team Delta: official statistics."""
    print("\n=== Team Delta (公的統計取り込み) タスク生成 ===\n")

    DELTA_TASKS = [
        ('delta-01', '学校基本調査', 'https://www.e-stat.go.jp/stat-search/files?tstat=000001011528'),
        ('delta-02', '学校保健統計調査', 'https://www.e-stat.go.jp/stat-search/files?tstat=000001011648'),
        ('delta-03', '全国学力・学習状況調査', 'https://www.nier.go.jp/24chousakekkahoukoku/'),
        ('delta-04', 'TIMSS/PISA日本データ', 'https://www.nier.go.jp/timss/'),
        ('delta-05', '都道府県別私立教育統計', '各都道府県教育委員会'),
        ('delta-06', '学校法人会計データ', '文科省学校法人会計基準'),
    ]

    for task_id, name, source in DELTA_TASKS:
        task_md = TASKS_DIR / f"{task_id}.md"
        task_md.write_text(f"""# Codex Task: {task_id} — Team Delta (公的統計取り込み)

## 担当
{name}

## 出典
{source}

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
""")
        print(f"  {task_id}: {name}")


def collect_progress():
    """Aggregate progress from codex_progress/ directory."""
    if not PROGRESS_DIR.exists():
        return {}
    progress = {}
    for f in PROGRESS_DIR.glob('*.json'):
        try:
            d = json.loads(f.read_text())
            progress[d.get('task_id', f.stem)] = d
        except:
            pass
    return progress


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true', help='Build all task specs')
    parser.add_argument('--status', action='store_true', help='Show current progress')
    args = parser.parse_args()

    db = sqlite3.connect(DB)

    if args.build:
        total = make_alpha_tasks(db)
        make_gamma_tasks(db)
        make_delta_tasks()
        print(f"\n=== タスク生成完了 ===")
        print(f"出力先: {TASKS_DIR}")
        print(f"30タスク生成（Alpha 12 + Gamma 8 + Delta 6 + ほか）")

    if args.status:
        print("=== 進捗集計 ===\n")
        progress = collect_progress()
        if not progress:
            print("(進捗ファイルなし)")
        for task_id, d in sorted(progress.items()):
            print(f"  {task_id}: {d.get('status','unknown')} — completed={d.get('completed',0)}/{d.get('total_schools','?')}")

    db.close()


if __name__ == '__main__':
    main()
