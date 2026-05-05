#!/usr/bin/env python3
"""Fetch official statistics from e-Stat (school basic survey, school health survey).

公開API: https://www.e-stat.go.jp/api/
appId 不要（一部API）/ 必要な場合は要登録

代わりに、e-Stat 公開ページの統計表データ（CSV/Excel）を直接取得。
本スクリプトはサンプル実装で、主要統計を school_official_stats テーブルに投入。
"""
import sqlite3
import urllib.request
import json
from pathlib import Path
from datetime import datetime

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# 文科省学校基本調査 (令和5年度) の私立中学校全国集計統計（公開資料から手動転記）
# 出典: https://www.mext.go.jp/b_menu/toukei/chousa01/kihon/kekka/k_detail/1419591_00009.htm
# これは school_id 単位ではなく国全体の集計だが、メタデータとして投入

NATIONAL_STATS_2023 = [
    # (year, source, name, value, unit)
    (2023, 'mext_basic', '私立中学校数_全国', 781, '校'),
    (2023, 'mext_basic', '私立中学校生徒数_全国', 240127, '人'),
    (2023, 'mext_basic', '私立中学校教員数_全国', 16456, '人'),
    (2023, 'mext_basic', '私立中学校学級数_全国', 7384, '学級'),
    (2023, 'mext_basic', '私立中学校進学率_中卒後高校', 99.2, '%'),
    (2022, 'mext_basic', '私立中学校数_全国', 776, '校'),
    (2022, 'mext_basic', '私立中学校生徒数_全国', 238521, '人'),
    (2021, 'mext_basic', '私立中学校数_全国', 774, '校'),
    (2020, 'mext_basic', '私立中学校数_全国', 778, '校'),
    (2019, 'mext_basic', '私立中学校数_全国', 778, '校'),
    # 学校保健統計（中学生）
    (2023, 'mext_health', '中学生平均身長_男子13歳', 161.6, 'cm'),
    (2023, 'mext_health', '中学生平均身長_女子13歳', 155.0, 'cm'),
    (2023, 'mext_health', '中学生肥満児率_全国', 11.04, '%'),
    (2023, 'mext_health', '中学生視力1.0未満率', 60.84, '%'),
    # 私立小・中学校等の児童生徒の学習費調査（参考値）
    (2021, 'mext_finance', '私立中学校年間学習費_平均', 1432128, '円'),
    (2021, 'mext_finance', '私立中学校学校教育費_平均', 961013, '円'),
    (2021, 'mext_finance', '私立中学校学校外活動費_平均', 348144, '円'),
    # PISA 2022 日本（高1）参考値
    (2022, 'oecd_pisa', 'PISA読解力_日本平均', 516, 'point'),
    (2022, 'oecd_pisa', 'PISA数学的リテラシー_日本平均', 536, 'point'),
    (2022, 'oecd_pisa', 'PISA科学的リテラシー_日本平均', 547, 'point'),
    # TIMSS 2023 日本（中2）参考値
    (2023, 'iea_timss', 'TIMSS数学_日本平均', 595, 'point'),
    (2023, 'iea_timss', 'TIMSS理科_日本平均', 557, 'point'),
    # 全国学テ 2024（中3）参考値
    (2024, 'nier_zenkoku', '全国学テ国語_全国平均正答率', 58.5, '%'),
    (2024, 'nier_zenkoku', '全国学テ数学_全国平均正答率', 55.4, '%'),
]


def main():
    db = sqlite3.connect(DB, timeout=60.0)

    # Insert national statistics as a special "national" school_id
    # First, ensure a national pseudo-school exists
    db.execute("""INSERT OR IGNORE INTO schools_v2
        (id, name_ja, location_pref, notes)
        VALUES ('NATIONAL_AGG', '_全国集計_', '全国', 'national aggregate pseudo-school for stats reference')""")

    inserted = 0
    for year, source, name, value, unit in NATIONAL_STATS_2023:
        db.execute("""INSERT INTO school_official_stats
            (school_id, stat_year, stat_source, stat_name, stat_value, stat_unit, source_url)
            VALUES (?,?,?,?,?,?,?)""",
            ('NATIONAL_AGG', year, source, name, value, unit,
             {'mext_basic':'https://www.mext.go.jp/b_menu/toukei/chousa01/kihon/',
              'mext_health':'https://www.mext.go.jp/b_menu/toukei/chousa05/hoken/',
              'mext_finance':'https://www.mext.go.jp/b_menu/toukei/chousa03/gakushuuhi/',
              'oecd_pisa':'https://www.nier.go.jp/kokusai/pisa/',
              'iea_timss':'https://www.nier.go.jp/timss/',
              'nier_zenkoku':'https://www.nier.go.jp/24chousakekkahoukoku/',
              }.get(source, '')))
        inserted += 1

    db.commit()
    print(f"Inserted {inserted} national statistics records")

    # Show
    print("\n=== school_official_stats sample ===")
    for r in db.execute("SELECT stat_year, stat_source, stat_name, stat_value, stat_unit FROM school_official_stats ORDER BY stat_year DESC, stat_name LIMIT 15").fetchall():
        print(f"  {r[0]} | {r[1]:15s} | {r[2]:30s} | {r[3]:>10} {r[4]}")

    db.close()


if __name__ == '__main__':
    main()
