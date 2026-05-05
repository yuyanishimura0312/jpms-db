# Codex 30-40 並列ワーカー 起動指示書

**作成**: 2026-05-05
**対象**: Codex 協力チーム（30-40名規模）
**プロジェクト**: JPMS-DB v2 Phase E（一次情報大規模収集）

## 概要

JPMS-DB v2 拡張プロジェクトの Phase E では、528校の一次情報（HP、関係者声、卒業生活躍、公的統計、家庭関係）を地道に集積する必要があります。Claude Code をメインオーケストレーター、Codex を30-40並列ワーカーとして展開し、5チーム × 6-12名の構成で取り組みます。

## チーム編成

| チーム | 内容 | 人数 | 担当 |
|---|---|---|---|
| Alpha | HP一次取得 | 12名 | 都道府県別バッチ（各40-65校） |
| Beta | 関係者声抽出 | 8名 | HP取得後の構造化（5主体別） |
| Gamma | 卒業生活躍連動 | 8名 | ミラツク36DBとの紐付け |
| Delta | 公的統計取り込み | 6名 | e-Stat / NIER / 教育委員会 |
| Epsilon | 家庭関係データ | 6名 | HoverDS + Epstein 6Types |

## 起動手順

### 1. リポジトリ取得
```bash
git clone https://github.com/yuyanishimura0312/jpms-db.git
cd jpms-db
git pull origin main
```

### 2. タスク仕様確認
```bash
ls v2/codex_tasks/
# alpha-01.md, alpha-02.md, ..., gamma-01.md, ..., delta-01.md, ...
```

### 3. ワーカー実行
各 Codex ワーカーは、自分の担当タスクIDの `<task_id>.md` を読み、指示通りに実行する。

**Alpha タスク例（HP取得）**:
```bash
# alpha-01 を担当する場合
cd ~/projects/research/jpms-db
cat v2/codex_tasks/alpha-01.md
# 指示通りに while ループでHPを取得
while IFS= read -r line; do
  sid=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['id'])")
  python3 v2/scripts/fetch_school_hp.py --school-id "$sid"
done < v2/codex_tasks/alpha-01_schools.jsonl
```

### 4. 進捗報告
完了時に `v2/codex_progress/<task_id>.json` を作成:
```json
{
  "task_id": "alpha-01",
  "team": "alpha",
  "total_schools": 50,
  "completed": 47,
  "philosophies_added": 32,
  "testimonials_added": 18,
  "status": "completed",
  "ts": "2026-05-05T12:00:00"
}
```

## 倫理規律（全ワーカー絶対遵守）

1. **robots.txt 厳守** — `urllib.robotparser` で取得前に確認
2. **遅延** — 同一ドメイン 5秒/req 以上
3. **User-Agent明示** — `JPMS-DB-Research/2.0 (+research-contact@miratuku.org)`
4. **個人情報** — 未成年は完全匿名化、削除依頼SOP稼働
5. **引用倫理** — 短文＋出典明示（rights_level=quoted_with_attribution）
6. **取得失敗** — 再試行1回のみ、404/timeout は記録のみで先へ

## 並列実行のための排他制御

SQLite はライターロック競合の可能性があります。各 Codex ワーカーは:

- **A方式**: 直接 DB に書き込み（fetch_school_hp.py 既定）— 同時実行は2-3まで推奨
- **B方式**: JSONL に書き出し → 統合フェーズで一括 INSERT — 30+並列に推奨

B方式を取る場合、`fetch_school_hp.py` を `--output-jsonl` オプション付きで実行し、Claude Code 側で集約。

## 分担マップ

| タスクID | チーム | 担当 | 件数 |
|---|---|---|---|
| alpha-01 | Alpha | 東京 part1 | 50 |
| alpha-02 | Alpha | 東京 part2 | 50 |
| alpha-03 | Alpha | 東京 part3 | 37 |
| alpha-04 | Alpha | 神奈川 | 65 |
| alpha-05 | Alpha | 埼玉・千葉 | 59 |
| alpha-06 | Alpha | 大阪・兵庫・京都 | 49 |
| alpha-07 | Alpha | 愛知・静岡・岐阜 | 37 |
| alpha-08 | Alpha | 関西残り | 14 |
| alpha-09 | Alpha | 中四国・九州前半 | 23 |
| alpha-10 | Alpha | 九州・沖縄 | 48 |
| alpha-11 | Alpha | 北海道・東北 | 21 |
| alpha-12 | Alpha | 北陸・甲信越 | 73 |
| gamma-01 | Gamma | IC（役員） | 7,658 |
| gamma-02 | Gamma | IR（VC） | 4,180 |
| gamma-03 | Gamma | UPR（大学PR） | 14,016 |
| gamma-04 | Gamma | EX（有識者） | 3,995 |
| gamma-05 | Gamma | AL（学術） | 233K |
| gamma-06 | Gamma | GF（偉人） | 9,178 |
| gamma-07 | Gamma | SGRD（産学R&D） | 11,997 |
| gamma-08 | Gamma | 統合・重複解消 | - |
| delta-01 | Delta | 学校基本調査 | 5年分 |
| delta-02 | Delta | 学校保健統計 | 5年分 |
| delta-03 | Delta | 全国学テ | 公開分 |
| delta-04 | Delta | TIMSS/PISA | 国際比較 |
| delta-05 | Delta | 都道府県統計 | 47都道府県 |
| delta-06 | Delta | 学校法人会計 | 公開法人 |

合計 30 並列タスク（Alpha 12 + Gamma 8 + Delta 6 + ほか4 = 30）

## 監督

Claude Code（メイン）は以下を担当:
1. タスク配布完了監視
2. 進捗集計（`team_orchestrator.py --status`）
3. JSONL → SQLite 統合（毎日終わりに）
4. 倫理レビュー監督
5. 依頼者向け日次レポート

## 完了基準

| 指標 | 目標 |
|---|---|
| HP取得校数 | 420校（80%）以上 |
| 関係者声 | 7,000件以上 |
| 卒業生活躍紐付け | 5,000件以上 |
| 公的統計年度 | 5年分 |
| データ品質 | NOT NULL率 80%以上、ソース付与率100% |
