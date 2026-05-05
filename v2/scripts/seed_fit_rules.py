#!/usr/bin/env python3
"""Seed person_school_fit_rule table for JPMS-DB v2 Layer 4.

Layer 4: 個人特性 × 学校特性 適合ルール構築

各ルールは person_archetype (10) × school_culture_dim (10) の主要組合せをカバーし、
以下の理論基盤に依拠する:

- Eccles & Midgley (1989, 1993) Stage-Environment Fit
- Holland (1959, 1997) P-E Fit (RIASEC)
- Edwards (1991, 2008) Multi-dimensional P-E Fit (Demands-Abilities, Supplies-Values)
- Schneider (1987) ASA Model
- Hoover-Dempsey & Sandler (1995, 2005) + Epstein (1995) Six Types
- Deci & Ryan SDT, Dweck Growth Mindset, Marcia Identity, Lerner PYD Five Cs

設計方針:
1. 10アーキタイプの主要マッチを高確信度（confidence 4-5）で投入
2. ミスマッチの「アンチ・パターン」も負の適合として投入（confidence 3-4）
3. SDT/Identity/Growth といった次元横断ルールも投入
4. 全ルール合計 25 件を投入
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

JPMS_DB = Path("/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db")


# ----------------------------------------------------------------------
# 25 fit rules
# Each rule: rule_name, person_pattern, school_pattern, formula,
#            outcomes, evidence_from, confidence, rationale
# ----------------------------------------------------------------------
RULES: list[tuple[
    str,             # rule_name
    dict,            # person_trait_pattern
    dict,            # school_culture_pattern
    str,             # fit_score_formula
    dict,            # expected_outcomes
    str,             # evidence_from
    int,             # confidence (1-5)
    str,             # rationale
]] = [
    # ===== 1. Explorer 系 =====
    (
        "探究者型 × 自律性高校",
        {"archetype": "arch_explorer", "trait_o": ">75", "trait_c": ">60"},
        {"cult_autonomy": ">65", "cult_creativity": ">60"},
        "0.5*(P_o + P_c)/2 + 0.5*(S_autonomy + S_creativity)/2 - bias_overstructure",
        {"cognitive": "high", "creative_excellence": "high", "wellbeing": "medium-high"},
        "Holland P-E Fit (Investigative) + Eccles Stage-Environment Fit",
        5,
        "内的探求志向の生徒（高O・C）は、規律より自律を優先する学校で発達ニーズが満たされ、認知・創造卓越が伸びる。逆に過度な構造下では好奇心が減衰する（Eccles）。",
    ),
    (
        "探究者型 × メンター密度高",
        {"archetype": "arch_explorer", "trait_intrinsic_mot": ">70"},
        {"cult_mentor": ">70", "cult_autonomy": ">55"},
        "0.4*P_intrinsic_mot + 0.4*S_mentor + 0.2*S_autonomy",
        {"cognitive": "high", "research_orientation": "high"},
        "Zuckerman Scientific Elite (Mentor relationship) + SDT Autonomy",
        5,
        "Zuckermanはノーベル賞受賞者の95%が受賞者をメンターに持つことを示した。内発的動機の高い探究者は濃密メンター環境でこそ研究志向が育つ。",
    ),

    # ===== 2. Creator 系 =====
    (
        "創造者型 × 創造性奨励校",
        {"archetype": "arch_creator", "trait_o": ">80"},
        {"cult_creativity": ">70", "cult_autonomy": ">60"},
        "0.6*S_creativity + 0.3*S_autonomy + 0.1*P_o - bias_competition",
        {"creative_excellence": "high", "wellbeing": "high"},
        "Csikszentmihalyi Flow + Holland Artistic + Edwards Supplies-Values",
        5,
        "高O・高Nの創造者は、創造性を奨励し自律を保障する環境でフロー状態に入りやすい。競争圧の強い環境では内的創造プロセスが阻害される。",
    ),
    (
        "創造者型 × 高競争校（負の適合）",
        {"archetype": "arch_creator", "trait_n": ">55"},
        {"cult_competition": ">75", "cult_intensity": ">75"},
        "-(0.4*S_competition + 0.4*S_intensity) + 0.2*S_creativity",
        {"wellbeing": "low", "creative_excellence": "medium-low", "burnout_risk": "high"},
        "Eccles Stage-Environment Fit (mismatch) + Edwards 過剰適合理論",
        4,
        "高Nの創造者は競争・高強度環境で不安が増幅し、創造性が萎縮する。Eccles理論の不適合パターン。",
    ),

    # ===== 3. Leader 系 =====
    (
        "リーダー型 × 構造度・競争性高校",
        {"archetype": "arch_leader", "trait_e": ">70", "trait_c": ">65"},
        {"cult_structure": ">65", "cult_competition": ">60"},
        "0.4*(P_e + P_c)/2 + 0.4*(S_structure + S_competition)/2 + 0.2*S_intensity",
        {"leadership": "high", "agency_citizenship": "high", "achievement": "high"},
        "Holland Enterprising + Collins Level 5 Leadership 萌芽",
        4,
        "外向・誠実性の高いリーダー型は、明確な構造と健全な競争のある環境で達成志向と統率力を伸ばす（Holland Enterprising × Eccles適合）。",
    ),
    (
        "リーダー型 × 共同体性高校",
        {"archetype": "arch_leader", "trait_a": "<60"},
        {"cult_community": ">70"},
        "0.5*P_e + 0.3*S_community + 0.2*S_mentor",
        {"leadership": "high", "agency_citizenship": "high", "social_emotional": "medium"},
        "Lerner PYD Connection + Collins (組織目的志向)",
        4,
        "共同体性の強い学校では、リーダー型生徒が「個人野心 < 組織目的」を学習し、成熟したリーダーシップ（Level 5の萌芽）が育つ。",
    ),

    # ===== 4. Caregiver 系 =====
    (
        "養育者型 × 共同体性・関係性高校",
        {"archetype": "arch_caregiver", "trait_a": ">75", "trait_pyd_caring": ">70"},
        {"cult_community": ">70", "cult_mentor": ">60"},
        "0.4*P_a + 0.3*P_pyd_caring + 0.3*(S_community + S_mentor)/2",
        {"social_emotional": "high", "values_morality": "high", "wellbeing": "high"},
        "Lerner PYD (Caring/Connection) + Hoover-Dempsey 関係性層",
        5,
        "高A・高Caringの養育者は、共同体性とメンター密度の高い学校でケア志向と道徳発達が伸びる。CASEL関係性スキルとも整合。",
    ),
    (
        "養育者型 × 高競争校（負の適合）",
        {"archetype": "arch_caregiver"},
        {"cult_competition": ">75", "cult_community": "<40"},
        "-(0.5*S_competition - 0.5*S_community) + 0.3*P_a",
        {"wellbeing": "medium-low", "social_emotional": "medium-low"},
        "Eccles Stage-Environment Fit + Edwards Supplies-Values mismatch",
        3,
        "養育者型は競争圧が強く共同体性の薄い環境では「自分が役に立てない」感覚を抱きやすく、関係性欲求（SDT）が満たされず無気力化のリスク。",
    ),

    # ===== 5. Warrior 系 =====
    (
        "挑戦者型 × 高強度・構造度校",
        {"archetype": "arch_warrior", "trait_grit": ">70", "trait_n": "<40"},
        {"cult_intensity": ">70", "cult_structure": ">60"},
        "0.5*(P_grit + (100-P_n))/2 + 0.5*(S_intensity + S_structure)/2",
        {"achievement": "high", "agency_citizenship": "high", "resilience": "high"},
        "Duckworth GRIT + Eccles Demand-Abilities Fit",
        5,
        "GRITの高い挑戦者は、明確な構造下で高強度の挑戦が連続する環境でこそ忍耐と達成志向が伸びる（Demands-Abilities Fitの理想形）。",
    ),
    (
        "挑戦者型 × 国際性高校",
        {"archetype": "arch_warrior", "trait_o": ">60"},
        {"cult_internationality": ">70", "cult_intensity": ">60"},
        "0.4*P_grit + 0.3*S_internationality + 0.3*S_intensity",
        {"global_competence": "high", "leadership": "medium-high", "agency_citizenship": "high"},
        "OECD LC2030 Global Competence + Sarasvathy Effectuation",
        4,
        "挑戦者型は国際性の高い環境で「未知への対応力」を磨き、Sarasvathyのアフォーダブルロス志向（起業家性）に結びつく。",
    ),

    # ===== 6. Mediator 系 =====
    (
        "調停者型 × 多様性・国際性高校",
        {"archetype": "arch_mediator", "trait_a": ">75", "trait_o": ">65"},
        {"cult_diversity": ">70", "cult_internationality": ">60"},
        "0.4*(P_a + P_o)/2 + 0.4*(S_diversity + S_internationality)/2 + 0.2*S_community",
        {"social_emotional": "high", "global_competence": "high", "values_morality": "high"},
        "Holland Social + OECD Global Competence + Lerner PYD Connection",
        5,
        "調停者型は異質性の高い環境で価値統合・対立調整能力が伸びる。多様性と国際性は調停者のSupplies-Valuesに合致（Edwards）。",
    ),

    # ===== 7. Craftsman 系 =====
    (
        "職人型 × 構造度・メンター高校",
        {"archetype": "arch_craftsman", "trait_c": ">80"},
        {"cult_structure": ">70", "cult_mentor": ">65"},
        "0.5*P_c + 0.3*S_structure + 0.2*S_mentor",
        {"achievement": "high", "creative_excellence": "medium-high", "values_morality": "high"},
        "Ericsson Deliberate Practice + Zuckerman Mentor Quality",
        5,
        "高Cの職人型は、明確な手順構造と熟練メンターのいる環境で意図的練習（Deliberate Practice）が効果的に進み、専門技能が高水準に達する。",
    ),
    (
        "職人型 × 自律性過剰校（負の適合）",
        {"archetype": "arch_craftsman"},
        {"cult_autonomy": ">80", "cult_structure": "<40"},
        "-(0.4*(S_autonomy - 70) - 0.4*(60-S_structure)) + 0.2*S_mentor",
        {"achievement": "medium-low", "wellbeing": "medium"},
        "Edwards 過剰適合（過剰自律）+ Eccles 構造ニーズ",
        3,
        "職人型は明確な構造と段階的フィードバックを必要とする。過度な自律放任の環境では到達基準が不明確になり練習効率が落ちる。",
    ),

    # ===== 8. Introvert Thinker 系 =====
    (
        "内省思索者型 × 静謐・自律高校",
        {"archetype": "arch_introvert_thinker", "trait_e": "<40", "trait_o": ">70"},
        {"cult_autonomy": ">65", "cult_competition": "<45", "cult_creativity": ">55"},
        "0.4*((100-P_e) + P_o)/2 + 0.4*S_autonomy - 0.2*S_competition",
        {"cognitive": "high", "creative_excellence": "medium-high", "wellbeing": "high"},
        "Holland Investigative + Cain Quiet (内向性の強み) + SDT Autonomy",
        5,
        "内向的思索者は競争圧が低く自律的探究を許す環境で深い思考が可能。高競争・高刺激環境では認知資源が消耗する（Eccles不適合）。",
    ),
    (
        "内省思索者型 × 競争性高校（負の適合）",
        {"archetype": "arch_introvert_thinker"},
        {"cult_competition": ">75", "cult_community": ">75"},
        "-(0.4*S_competition + 0.3*S_community) + 0.3*S_autonomy",
        {"wellbeing": "low", "social_emotional": "low", "burnout_risk": "high"},
        "Eccles Stage-Environment Fit (Person × Competition mismatch)",
        4,
        "内向思索者は競争性と共同体強度の双方が高い環境で「常時可視化」の負荷を受け、不適応・無気力化しやすい（Stage-Environment Fitの典型不適合）。",
    ),

    # ===== 9. Social Creator 系 =====
    (
        "社交創造者型 × 多様性・創造性校",
        {"archetype": "arch_social_creator", "trait_e": ">70", "trait_o": ">75"},
        {"cult_diversity": ">65", "cult_creativity": ">65", "cult_community": ">55"},
        "0.4*(P_e + P_o)/2 + 0.4*(S_diversity + S_creativity)/2 + 0.2*S_community",
        {"creative_excellence": "high", "social_emotional": "high", "leadership": "medium-high"},
        "Wuchty Team Science + Holland Social-Artistic + Csikszentmihalyi Group Flow",
        5,
        "社交創造者は多様性と創造性の交点で「Team Creativity」を発揮する。プロデューサー型キャリアの萌芽を育てる理想環境。",
    ),

    # ===== 10. Steady 系 =====
    (
        "堅実型 × 構造度高・規律高校",
        {"archetype": "arch_steady", "trait_c": ">70", "trait_n": "<45"},
        {"cult_structure": ">70", "cult_intensity": "55-75"},
        "0.5*(P_c + (100-P_n))/2 + 0.4*S_structure + 0.1*S_intensity",
        {"achievement": "high", "wellbeing": "high", "values_morality": "high"},
        "Edwards Demands-Abilities Fit + Eccles Stage-Environment Fit",
        4,
        "堅実型は予測可能な構造と中程度〜高強度の環境で安定した成果を出す。専門職・公務員キャリアへの基礎適性が形成される。",
    ),

    # ===== 11. SDT 系（次元横断） =====
    (
        "SDT 3欲求充足 × 関係性重視校",
        {"trait_autonomy": ">65", "trait_competence": ">65", "trait_relatedness": ">65"},
        {"cult_mentor": ">60", "cult_community": ">55", "cult_autonomy": ">55"},
        "0.33*(P_autonomy + P_competence + P_relatedness)/3 + 0.33*(S_mentor + S_community + S_autonomy)/3",
        {"wellbeing": "high", "intrinsic_motivation": "high", "social_emotional": "high"},
        "Deci & Ryan Self-Determination Theory (BPNS)",
        5,
        "SDT3基本欲求（自律・有能・関係）が充足されている生徒は、3欲求を支える環境でWB・内発動機が高水準に達する（Ryan-Deci 2000）。",
    ),

    # ===== 12. Growth Mindset 系 =====
    (
        "Growth Mindset高 × 創造性・自律高校",
        {"trait_growth_mindset": ">70"},
        {"cult_creativity": ">60", "cult_autonomy": ">55", "cult_competition": "<70"},
        "0.5*P_growth + 0.3*S_creativity + 0.2*S_autonomy - 0.1*max(0, S_competition-70)",
        {"cognitive": "high", "achievement": "high", "resilience": "high"},
        "Dweck Growth Mindset + Eccles Stage-Environment Fit",
        5,
        "Growth Mindsetは挑戦と失敗復帰を許容する自律的環境で強化される。過度な比較競争環境ではFixed Mindsetへ退行するリスク（Dweck 2006）。",
    ),

    # ===== 13. Identity 系 =====
    (
        "アイデンティティ探索期 × 多様性高校",
        {"trait_identity_explore": ">65", "trait_identity_commit": "<55"},
        {"cult_diversity": ">65", "cult_internationality": ">55", "cult_creativity": ">55"},
        "0.4*P_identity_explore + 0.3*S_diversity + 0.3*S_internationality",
        {"identity_achievement": "high", "global_competence": "high", "wellbeing": "medium-high"},
        "Marcia Identity Status + Erikson Moratorium",
        4,
        "Marciaのモラトリアム期生徒は多様性の高い環境で複数のアイデンティティを試行でき、最終的にAchieved Statusへ到達する確率が高まる。",
    ),
    (
        "アイデンティティ確約型 × 構造度高校",
        {"trait_identity_commit": ">70", "trait_identity_explore": "<50"},
        {"cult_structure": ">65", "cult_mentor": ">55"},
        "0.5*P_identity_commit + 0.3*S_structure + 0.2*S_mentor",
        {"achievement": "high", "values_morality": "high", "agency_citizenship": "medium-high"},
        "Marcia Foreclosure→Achievement経路 + Hoover-Dempsey",
        3,
        "確約先行型（Foreclosure）の生徒は構造とメンターのある環境で内省機会を得て、Achieved Statusへ移行する。構造のない環境では確約が硬直化する。",
    ),

    # ===== 14. PYD 系 =====
    (
        "PYD 5C高 × 共同体・メンター校",
        {"trait_pyd_competence": ">65", "trait_pyd_confidence": ">65", "trait_pyd_connection": ">65", "trait_pyd_character": ">60", "trait_pyd_caring": ">60"},
        {"cult_community": ">65", "cult_mentor": ">60"},
        "0.5*(avg of 5Cs) + 0.5*(S_community + S_mentor)/2",
        {"agency_citizenship": "high", "social_emotional": "high", "values_morality": "high", "contribution": "high"},
        "Lerner Five Cs (PYD) + Sixth C (Contribution)",
        5,
        "PYD Five Csが揃った生徒は、共同体性とメンター密度の高い環境で『Contribution（社会貢献）』第6Cが発現する（Lerner 2005）。",
    ),

    # ===== 15. Spirituality 系 =====
    (
        "誠実・思いやり高 × 精神性高校",
        {"trait_c": ">65", "trait_pyd_caring": ">65", "trait_pyd_character": ">65"},
        {"cult_spirituality": ">65", "cult_community": ">55"},
        "0.4*(P_c + P_pyd_caring + P_pyd_character)/3 + 0.4*S_spirituality + 0.2*S_community",
        {"values_morality": "high", "wellbeing": "high", "social_emotional": "high"},
        "Kohlberg Moral Development + 日本宗教系学校研究",
        4,
        "誠実性とCharacterの高い生徒は精神性重視校で道徳的推論（Kohlberg後慣習段階）と内的価値統合が促進される。",
    ),

    # ===== 16. 自己調整学習 系 =====
    (
        "自己調整学習 × 自律性・メンター校",
        {"trait_self_regulation": ">65", "trait_growth_mindset": ">60"},
        {"cult_autonomy": ">60", "cult_mentor": ">55", "cult_structure": "50-75"},
        "0.4*P_self_regulation + 0.3*S_autonomy + 0.2*S_mentor + 0.1*(70-abs(S_structure-62))",
        {"achievement": "high", "cognitive": "high", "lifelong_learning": "high"},
        "Zimmerman SRL + SDT Autonomy + Hattie Visible Learning",
        5,
        "SRLサイクル（計画-モニタ-評価）は自律的環境で機能し、メンターのフィードバックで深化する。中程度の構造が足場（scaffolding）となる。",
    ),

    # ===== 17. 神経症傾向高 × 環境 =====
    (
        "高神経症傾向 × 高強度・高競争校（負の適合）",
        {"trait_n": ">65"},
        {"cult_intensity": ">75", "cult_competition": ">75"},
        "-(0.5*P_n*(S_intensity + S_competition)/200) + 0.3*S_mentor",
        {"wellbeing": "low", "burnout_risk": "high", "achievement": "medium-low"},
        "Eccles Stage-Environment Fit (vulnerability × demand mismatch)",
        4,
        "高Nの生徒は高強度・高競争環境で慢性ストレス・燃え尽きのリスクが顕著に高い。メンター密度が高い場合は緩衝されるが、欠如すると不適応化する。",
    ),
    (
        "高神経症傾向 × メンター・共同体校",
        {"trait_n": ">60"},
        {"cult_mentor": ">70", "cult_community": ">65", "cult_competition": "<55"},
        "0.4*(S_mentor + S_community)/2 - 0.2*S_competition + 0.2*P_pyd_connection",
        {"wellbeing": "high", "social_emotional": "high", "resilience": "medium-high"},
        "Masten Ordinary Magic (Resilience) + SDT Relatedness",
        4,
        "高Nの生徒も、メンター密度と共同体性の高い環境では関係性欲求が満たされ、レジリエンスが育つ（Masten 2019）。",
    ),

    # ===== 18. GRIT × Effectuation 起業家系 =====
    (
        "GRIT・自律性高 × 創造性・国際性校（起業家適性）",
        {"trait_grit": ">70", "trait_autonomy": ">65", "trait_o": ">65"},
        {"cult_creativity": ">60", "cult_internationality": ">55", "cult_autonomy": ">60"},
        "0.4*(P_grit + P_autonomy)/2 + 0.4*(S_creativity + S_internationality + S_autonomy)/3",
        {"entrepreneurship": "high", "agency_citizenship": "high", "creative_excellence": "medium-high"},
        "Sarasvathy Effectuation + Duckworth GRIT + OECD Transformative Competencies",
        4,
        "高GRIT・高自律・高Oの生徒は、創造性と国際性のある自律環境でEffectuation（手持ち資源・許容損失思考）を育み、起業家適性が顕在化する。",
    ),
]


def main() -> None:
    if not JPMS_DB.exists():
        raise SystemExit(f"DB not found: {JPMS_DB}")

    conn = sqlite3.connect(JPMS_DB)
    try:
        cur = conn.cursor()

        # Show pre-state
        before = cur.execute("SELECT COUNT(*) FROM person_school_fit_rule").fetchone()[0]
        print(f"[pre]  person_school_fit_rule rows: {before}")

        # Optional: clear table to make script idempotent. We use INSERT OR REPLACE
        # behavior by deleting prior seeded rows by rule_name.
        rule_names = [r[0] for r in RULES]
        placeholders = ",".join("?" * len(rule_names))
        cur.execute(
            f"DELETE FROM person_school_fit_rule WHERE rule_name IN ({placeholders})",
            rule_names,
        )

        # Insert
        sql = """
            INSERT INTO person_school_fit_rule
              (rule_name, person_trait_pattern, school_culture_pattern,
               fit_score_formula, expected_outcomes,
               evidence_from, confidence, rationale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        for (rule_name, p_pat, s_pat, formula, outcomes,
             evidence, confidence, rationale) in RULES:
            cur.execute(
                sql,
                (
                    rule_name,
                    json.dumps(p_pat, ensure_ascii=False),
                    json.dumps(s_pat, ensure_ascii=False),
                    formula,
                    json.dumps(outcomes, ensure_ascii=False),
                    evidence,
                    confidence,
                    rationale,
                ),
            )

        conn.commit()

        after = cur.execute("SELECT COUNT(*) FROM person_school_fit_rule").fetchone()[0]
        print(f"[post] person_school_fit_rule rows: {after}")
        print(f"[diff] inserted: {after - before + len(rule_names) - len(rule_names)} (target {len(RULES)})")
        print(f"[ok]   {len(RULES)} rules upserted")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
