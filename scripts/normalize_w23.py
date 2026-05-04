#!/usr/bin/env python3
"""W23（神奈川）SQLをjpms_schemaに正規化"""
import re
import sys
from pathlib import Path

src = Path("/Users/nishimura+/projects/research/jpms-db/seeds/22_kanto_w23_kanagawa.sql")
dst = Path("/Users/nishimura+/projects/research/jpms-db/seeds/22_kanto_w23_kanagawa_fixed.sql")

text = src.read_text(encoding="utf-8")

# 1. Source INSERTはそのまま
# 2. jpms_schools INSERTを修正:
#    - schema: (id, name_ja, name_kana, establishment_year, school_corporation,
#               religious_affiliation, gender_type, integrated_type,
#               location_pref, location_city, primary_source_id) — 11列
#    - 元: (school_id, name_ja, name_kana, establishment_year, school_corporation,
#           religious_affiliation, gender_type, integrated_type,
#           location_pref, location_city, location_address, website_url, phone_number, primary_source_id) — 14列

pattern = re.compile(
    r"INSERT INTO jpms_schools \(school_id, name_ja, name_kana, establishment_year, school_corporation, religious_affiliation, gender_type, integrated_type, location_pref, location_city, location_address, website_url, phone_number, primary_source_id\) VALUES \(([^;]+)\);",
    re.MULTILINE | re.DOTALL,
)

def split_sql_values(s):
    """SQLのVALUES内をカンマで分割（'内のカンマは無視）"""
    out, cur, in_quote = [], [], False
    i = 0
    while i < len(s):
        c = s[i]
        if c == "'":
            if in_quote and i + 1 < len(s) and s[i + 1] == "'":
                cur.append("''")
                i += 2
                continue
            in_quote = not in_quote
            cur.append(c)
        elif c == "," and not in_quote:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if cur:
        out.append("".join(cur).strip())
    return out

GENDER_MAP = {"'coeducational'": "'coed'", "'boys'": "'boys'", "'girls'": "'girls'"}
INTEG_MAP = {
    "'junior_senior_combined'": "'attached'",
    "'junior_only'": "'none'",
    "'attached'": "'attached'",
    "'full'": "'full'",
    "'linked'": "'linked'",
    "'none'": "'none'",
    "NULL": "NULL",
}

count_in = count_out = 0


def transform(m):
    global count_in, count_out
    count_in += 1
    vals = split_sql_values(m.group(1))
    if len(vals) != 14:
        return f"-- SKIPPED (cols={len(vals)}): {m.group(0)[:80]}\n"
    sid, nja, nkana, ey, corp, rel, gen, integ, pref, city, addr, url, phone, psrc = vals
    gen2 = GENDER_MAP.get(gen, "'coed'")
    integ2 = INTEG_MAP.get(integ, "'none'")
    rel2 = rel if rel != "NULL" else "'unknown'"
    count_out += 1
    return (
        f"INSERT INTO jpms_schools (id, name_ja, name_kana, establishment_year, "
        f"school_corporation, religious_affiliation, gender_type, integrated_type, "
        f"location_pref, location_city, website_url, primary_source_id, data_completeness, status) "
        f"VALUES ({sid}, {nja}, {nkana}, {ey}, {corp}, {rel2}, {gen2}, {integ2}, "
        f"{pref}, {city}, {url}, {psrc}, 25, 'active');"
    )


fixed = pattern.sub(transform, text)
dst.write_text(fixed, encoding="utf-8")
print(f"in={count_in} out={count_out} -> {dst}")
