#!/usr/bin/env python3
"""flagged_dup_similar 469件の再評価。
同テキストが複数学校に出現 → テンプレ判定で flagged のまま。
1校のみ → 学校固有の独立証言として approved に救済。
"""
import sqlite3
from collections import defaultdict

DB = '/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db'

db = sqlite3.connect(DB, timeout=300.0)
db.execute('PRAGMA busy_timeout=300000')

rows = db.execute("""
    SELECT id, school_id, quote_text FROM testimonials_v2
    WHERE ethics_review_status='flagged_dup_similar'
""").fetchall()

print(f'flagged_dup_similar: {len(rows)} 件を分析')

by_text = defaultdict(set)
for id_, sid, qt in rows:
    key = qt[:100] if qt else ''
    by_text[key].add(sid)

salvaged = 0
template_kept = 0
for id_, sid, qt in rows:
    key = qt[:100] if qt else ''
    schools = by_text[key]
    if len(schools) == 1:
        db.execute(
            "UPDATE testimonials_v2 SET ethics_review_status='approved' WHERE id=?",
            (id_,)
        )
        salvaged += 1
    else:
        template_kept += 1

db.commit()

print(f'Salvaged (単一校・独立証言): {salvaged}')
print(f'Kept as template (複数校跨ぎ): {template_kept}')

approved_total = db.execute(
    "SELECT COUNT(*) FROM testimonials_v2 WHERE ethics_review_status='approved'"
).fetchone()[0]
print(f'approved 件数: {approved_total:,}')
db.close()
