#!/usr/bin/env python3
"""
Team C-5: UPR (University Press Release / R&D activity) -> JPMS-DB v2 linkage

Goal: Connect ミラツク university-startups DB (5,087 startups, 大学発R&D成果) to
      JPMS schools_v2 (551 private junior high schools).

Data reality:
- The originally-cited "UPR 14,016 university press releases" DB was not located.
- Closest substitute: ~/projects/apps/miratuku-news-v2/data/university-startups.db
  (5,087 university-spinout companies with founder_researchers + prefecture).
- These are aggregate R&D outcomes per university, not individual alumni records.
- JPMS schools_v2 contains junior high schools only; founder_researchers contain
  university affiliations, not 中学校. Direct alumni linkage is structurally impossible.

Strategy: Aggregate to prefecture level, attach to school_official_stats as
"prefecture_university_startup_index" so each JPMS school inherits the local
academic-entrepreneurial activity intensity of its location_pref.

Output:
- team_c5_upr.jsonl  (one row per JPMS school, with linked aggregate stat)
- codex_progress/team_c5.json  (run summary)
"""
import sqlite3
import json
import hashlib
import datetime
import os

JPMS_DB = "/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db"
UPR_DB = "/Users/nishimura+/projects/apps/miratuku-news-v2/data/university-startups.db"
OUT_JSONL = "/Users/nishimura+/projects/research/jpms-db/v2/codex_output/team_c5_upr.jsonl"
PROGRESS = "/Users/nishimura+/projects/research/jpms-db/v2/codex_progress/team_c5.json"

os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
os.makedirs(os.path.dirname(PROGRESS), exist_ok=True)


def anon_id(seed: str) -> str:
    return "anon_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def main():
    # 1. Aggregate UPR data by prefecture
    upr = sqlite3.connect(UPR_DB)
    upr.row_factory = sqlite3.Row
    cur = upr.execute(
        """
        SELECT prefecture,
               COUNT(*) AS startup_count,
               COUNT(DISTINCT university) AS univ_count,
               SUM(CASE WHEN status='ipo' THEN 1 ELSE 0 END) AS ipo_count,
               SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active_count
        FROM university_startups
        WHERE prefecture IS NOT NULL AND prefecture != ''
        GROUP BY prefecture
        """
    )
    pref_stats = {r["prefecture"]: dict(r) for r in cur}

    # Also collect named founder researchers (public record) per prefecture
    cur2 = upr.execute(
        """
        SELECT prefecture, university, founder_researchers, name_ja, id, source_urls
        FROM university_startups
        WHERE founder_researchers IS NOT NULL
          AND founder_researchers != '[]'
          AND founder_researchers != ''
        """
    )
    pref_founders = {}
    founder_records = []
    for r in cur2:
        try:
            researchers = json.loads(r["founder_researchers"])
        except Exception:
            researchers = []
        if not researchers:
            continue
        pref = r["prefecture"] or "不明"
        pref_founders.setdefault(pref, set()).update(researchers)
        for name in researchers:
            founder_records.append({
                "anon_id": anon_id(f"upr|{name}|{r['university']}"),
                "founder_name_public": name,
                "university": r["university"],
                "startup": r["name_ja"],
                "prefecture": pref,
                "upr_record_id": r["id"],
                "source": "university-startups DB (ミラツク 36DB UPR代替)",
            })
    upr.close()

    # 2. Walk JPMS schools and emit one record per school with linked aggregate
    jpms = sqlite3.connect(JPMS_DB)
    jpms.row_factory = sqlite3.Row
    schools = list(jpms.execute(
        "SELECT id, name_ja, location_pref FROM schools_v2"
    ))
    jpms.close()

    out = []
    matched_schools = 0
    for s in schools:
        pref = s["location_pref"] or ""
        pstat = pref_stats.get(pref)
        if not pstat:
            continue
        founders = sorted(list(pref_founders.get(pref, set())))[:5]
        record = {
            "school_id": s["id"],
            "school_name": s["name_ja"],
            "prefecture": pref,
            "source_db": "UPR",
            "source_db_path": UPR_DB,
            "stat_name": "prefecture_university_startup_index",
            "stat_value": pstat["startup_count"],
            "stat_unit": "startups",
            "stat_breakdown": {
                "univ_count": pstat["univ_count"],
                "ipo_count": pstat["ipo_count"],
                "active_count": pstat["active_count"],
            },
            "linkage_type": "prefecture_aggregate",
            "evidence_text": (
                f"{pref}所在の大学発スタートアップ {pstat['startup_count']} 社"
                f"（IPO {pstat['ipo_count']} 社、active {pstat['active_count']} 社、"
                f"関与大学 {pstat['univ_count']} 校）。同県のJPMS私立中学はその学術-起業活動圏に立地。"
            ),
            "sample_founder_researchers_public": founders,
            "privacy_status": "public_record",
            "confidence": 3,
            "match_method": "prefecture_aggregate",
        }
        out.append(record)
        matched_schools += 1

    # Append founder-level records (public_record, anon_id) at the tail for traceability
    for fr in founder_records:
        out.append({
            "school_id": None,
            "anon_id": fr["anon_id"],
            "source_db": "UPR",
            "founder_name_public": fr["founder_name_public"],
            "university": fr["university"],
            "startup": fr["startup"],
            "prefecture": fr["prefecture"],
            "upr_record_id": fr["upr_record_id"],
            "linkage_type": "person_no_school_link",
            "privacy_status": "public_record",
            "confidence": 1,
            "match_method": "no_school_match",
            "note": "founder researchers do not record 中学校; preserved as evidence with anon_id",
        })

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    progress = {
        "team": "C-5",
        "task": "UPR (university-startups) -> JPMS-DB v2 prefecture-level linkage",
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": {
            "upr_db": UPR_DB,
            "upr_db_actual_role": "ミラツク36DB UPR枠の代替: 大学発スタートアップ 5,087件",
            "upr_original_target_not_found": "14,016件の大学プレスリリースDBは見つからず",
            "jpms_db": JPMS_DB,
        },
        "stats": {
            "schools_total": len(schools),
            "schools_with_prefecture_match": matched_schools,
            "prefectures_covered": len(pref_stats),
            "founder_records_with_public_name": len(founder_records),
            "total_jsonl_rows": len(out),
        },
        "output": {
            "jsonl": OUT_JSONL,
            "min_required_candidates": 50,
            "met_minimum": matched_schools >= 50,
        },
        "notes": [
            "原タスク 14,016件 university press release DB は ~/projects 配下に発見できず。",
            "代替として university-startups.db (5,087件) を選択。これは大学のR&D成果の事業化記録で、UPRの本旨（大学発の研究成果アウトプット）に最も近い。",
            "JPMS schools_v2 は中学校レベル、university-startups の founder_researchers には中学情報なし。直接の alumni linkage は不可能。",
            "代替として都道府県レベルで集計し、school_official_stats への投入用に prefecture_university_startup_index を提供。",
            "founder_researchers は public_record として anon_id 付きで保持（追跡可能性のため）。",
        ],
    }
    with open(PROGRESS, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"[C-5] schools matched: {matched_schools}/{len(schools)}")
    print(f"[C-5] founder-level public records: {len(founder_records)}")
    print(f"[C-5] output: {OUT_JSONL}")
    print(f"[C-5] progress: {PROGRESS}")


if __name__ == "__main__":
    main()
