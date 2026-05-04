#!/usr/bin/env python3
"""残りのSQLを一括正規化（religious_affiliation/gender_type/integrated_type のCHECK違反対応、ID重複ずらし）"""
import re
from pathlib import Path

ALLOWED_REL = {'catholic','protestant','anglican','buddhist','shinto','non_religious','other','unknown'}
ALLOWED_GENDER = {'coed','boys','girls'}
ALLOWED_INTEG = {'full','attached','linked','none'}

REL_MAP = {
    'christian': 'protestant',
    'mission': 'catholic',
    'christianity': 'protestant',
    'mixed': 'unknown',
    'religious': 'unknown',
    'secular': 'non_religious',
    'none': 'non_religious',
}
GENDER_MAP = {
    'coeducational': 'coed',
    'mixed': 'coed',
    'male': 'boys',
    'female': 'girls',
}
INTEG_MAP = {
    'junior_senior_combined': 'attached',
    'junior_only': 'none',
    'middle_only': 'none',
    'separate': 'none',
}


def fix_quoted(s, allowed, mapping, default):
    """単一引用符で囲まれた値またはNULLを正規化"""
    if s == 'NULL' or s == '':
        return s
    m = re.match(r"^'(.+)'$", s)
    if not m:
        return s
    val = m.group(1).lower()
    if val in allowed:
        return f"'{val}'"
    if val in mapping:
        return f"'{mapping[val]}'"
    return f"'{default}'"


def fix_sql(text, id_offset=0):
    """SQL中のCHECK違反を修正"""
    # religious_affiliation
    text = re.sub(
        r"'(christian|mission|christianity|mixed|religious|secular|none|coeducational)'",
        lambda m: {
            'christian': "'protestant'",
            'mission': "'catholic'",
            'christianity': "'protestant'",
            'mixed': "'unknown'",
            'religious': "'unknown'",
            'secular': "'non_religious'",
            'none': "'non_religious'",
            'coeducational': "'coed'",
        }.get(m.group(1).lower(), m.group(0)),
        text,
    )
    # integrated_type
    text = text.replace("'junior_senior_combined'", "'attached'")
    text = text.replace("'junior_only'", "'none'")
    return text


def offset_school_ids(text, offset):
    """jpms_s_NNNN を offset 分ずらす"""
    def shift(m):
        n = int(m.group(1))
        return f"jpms_s_{n + offset:04d}"
    return re.sub(r"jpms_s_(\d{4})", shift, text)


def offset_source_ids(text, offset):
    def shift(m):
        n = int(m.group(1))
        return f"jpms_src_{n + offset:06d}"
    return re.sub(r"jpms_src_(\d{6})", shift, text)


root = Path("/Users/nishimura+/projects/research/jpms-db/seeds")

# W23 残りの行を全て修正
src = root / "22_kanto_w23_kanagawa_fixed.sql"
text = src.read_text(encoding="utf-8")
fixed = fix_sql(text)
(root / "22_kanto_w23_kanagawa_v2.sql").write_text(fixed, encoding="utf-8")
print("W23 v2 written")

# W22 ID重複を 200 ずらし、religious_affiliation修正
src = root / "21_kanto_w22_tokyo_west.sql"
text = src.read_text(encoding="utf-8")
fixed = fix_sql(text)
fixed = offset_school_ids(fixed, 200)  # jpms_s_0061-0120 → jpms_s_0261-0320
fixed = offset_source_ids(fixed, 1000)  # jpms_src_030101-030160 → jpms_src_031101-031160
(root / "21_kanto_w22_tokyo_west_v2.sql").write_text(fixed, encoding="utf-8")
print("W22 v2 written (offset +200/+1000)")

# W21patch — 先頭の不正テキストを除去（コメントは保持）
src = root / "21_kanto_w21_tokyo_central_patch.sql"
text = src.read_text(encoding="utf-8")
# 先頭から「-- JPMS-DB Phase 2」までスキップ
m = re.search(r"-- JPMS-DB Phase 2", text)
if m:
    text = text[m.start():]
fixed = fix_sql(text)
(root / "21_kanto_w21_tokyo_central_patch_v2.sql").write_text(fixed, encoding="utf-8")
print("W21patch v2 written")
