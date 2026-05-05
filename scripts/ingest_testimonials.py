#!/usr/bin/env python3
"""
JPMS-DB Phase 3: Testimonials Ingest Pipeline
==============================================

Markdown 形式の素材ファイル (reports/material_*.md など) から関係者発言を抽出し、
jpms_testimonials / jpms_sources テーブルへ自動投入する。

使い方:
    # ドライラン（DBに書き込まずに抽出件数とエラーのみ表示）
    python3 ingest_testimonials.py --dry-run reports/material_w101_salesio_kaijo.md

    # 全 material_*.md をドライラン
    python3 ingest_testimonials.py --dry-run --all

    # 実投入
    python3 ingest_testimonials.py reports/material_w101_salesio_kaijo.md

    # 全ファイル投入
    python3 ingest_testimonials.py --all

設計ポイント:
- ### #N または ### テーマ◯ の両形式に対応する複数パーサ
- 学校名は「## 学校名」「# 学校名」「ファイル冒頭#見出し」など複数候補から検出
- school_id は jpms_schools.name_ja に対するファジーマッチで逆引き
- 既存 testimonials の (school_id, excerpt[:80]) で重複検知
- jpms_sources はタイトル/URL の組合せで一意化

Author: Claude Code (Phase 3)
Date: 2026-05-04
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# 定数 / 設定
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "jpms.db"
REPORTS_DIR = ROOT / "reports"

# 立場テキスト → speaker_category マッピング（部分一致、優先度の高い順）
SPEAKER_RULES: list[tuple[str, str]] = [
    # 校長・教員系（最初にチェック）
    ("校長", "principal"),
    ("理事長", "principal"),
    ("学園長", "principal"),
    ("学長", "principal"),
    ("教頭", "principal"),
    ("副校長", "principal"),
    ("教員", "teacher"),
    ("教諭", "teacher"),
    ("教師", "teacher"),
    ("先生", "teacher"),
    ("学校", "principal"),  # 「学校公開発言」「学校HP」など
    # 卒業生
    ("元在校生", "student_former"),
    ("卒業", "student_former"),
    ("ob", "student_former"),
    ("og", "student_former"),
    ("OB", "student_former"),
    ("OG", "student_former"),
    ("元生徒", "student_former"),
    # 在校生
    ("在校生", "student_current"),
    ("在籍", "student_current"),
    ("中1", "student_current"),
    ("中2", "student_current"),
    ("中3", "student_current"),
    ("高1", "student_current"),
    ("高2", "student_current"),
    ("高3", "student_current"),
    ("生徒", "student_current"),
    # 保護者
    ("元保護者", "parent_former"),
    ("保護者", "parent_current"),
    ("お母さん", "parent_current"),
    ("お父さん", "parent_current"),
    ("ママ", "parent_current"),
    ("親", "parent_current"),
    # 第三者
    ("塾講師", "third_party"),
    ("予備校", "third_party"),
    ("塾", "third_party"),
    ("評論家", "external_evaluator"),
    ("教育評論家", "external_evaluator"),
    ("研究者", "external_evaluator"),
    ("ジャーナリスト", "external_evaluator"),
    ("記者", "external_evaluator"),
    ("議員", "third_party"),
]

# medium 推定: 出典文字列 → medium
MEDIUM_RULES: list[tuple[str, str]] = [
    ("youtube", "youtube"),
    ("YouTube", "youtube"),
    ("instagram", "instagram"),
    ("Instagram", "instagram"),
    ("twitter", "x"),
    ("Twitter", "x"),
    ("X(", "x"),
    ("X（", "x"),
    ("note", "note"),
    ("ameblo", "blog"),
    ("はてなブログ", "blog"),
    ("ブログ", "blog"),
    ("5ch", "5ch"),
    ("インターエデュ", "blog"),
    ("みんなの中学", "blog"),
    ("みんなの学校", "blog"),
    ("学校HP", "school_website"),
    ("学校公式", "school_website"),
    ("公式サイト", "school_website"),
    ("学校説明会", "school_event"),
    ("説明会", "school_event"),
    ("インタビュー", "interview"),
    ("取材", "newspaper"),
    ("新聞", "newspaper"),
    ("日本経済新聞", "newspaper"),
    ("日経", "newspaper"),
    ("文春", "newspaper"),
    ("president", "newspaper"),
    ("プレジデント", "newspaper"),
    ("東洋経済", "newspaper"),
    ("ダイヤモンド", "newspaper"),
    ("ＡＥＲＡ", "newspaper"),
    ("AERA", "newspaper"),
    ("書籍", "book"),
    ("本（", "book"),
]

# source_type 推定: 出典文字列 → source_type
SOURCE_TYPE_RULES: list[tuple[str, str]] = [
    ("youtube", "sns_youtube"),
    ("YouTube", "sns_youtube"),
    ("instagram", "sns_instagram"),
    ("Instagram", "sns_instagram"),
    ("twitter", "sns_x"),
    ("X(", "sns_x"),
    ("note", "blog"),
    ("ameblo", "blog"),
    ("ブログ", "blog"),
    ("5ch", "5ch"),
    ("インターエデュ", "blog"),
    ("みんなの中学", "blog"),
    ("学校HP", "school_website"),
    ("学校公式", "school_website"),
    ("公式サイト", "school_website"),
    ("学校説明会", "school_website"),
    ("説明会", "school_website"),
    ("新聞", "newspaper"),
    ("日経", "newspaper"),
    ("文春", "newspaper"),
    ("プレジデント", "newspaper"),
    ("東洋経済", "newspaper"),
    ("ダイヤモンド", "newspaper"),
    ("AERA", "newspaper"),
    ("書籍", "school_book"),
]

VALID_SENTIMENTS = {"positive", "neutral", "negative", "mixed"}


# ---------------------------------------------------------------------------
# データクラス
# ---------------------------------------------------------------------------

@dataclass
class Statement:
    """素材ファイルから抽出された一件の発言レコード"""
    school_name_raw: str
    block_index: int
    standpoint: str            # 立場
    sentiment: str             # positive / neutral / negative / mixed
    theme: str
    excerpt: str
    source_text: str           # 出典の生テキスト
    source_url: Optional[str] = None
    source_file: Optional[str] = None  # どの material_*.md から来たか

    @property
    def speaker_category(self) -> str:
        return _resolve_speaker_category(self.standpoint)

    @property
    def medium(self) -> str:
        return _resolve_medium(self.source_text)

    @property
    def source_type(self) -> str:
        return _resolve_source_type(self.source_text)


@dataclass
class IngestStats:
    files_processed: int = 0
    files_no_school: int = 0
    schools_matched: dict[str, str] = field(default_factory=dict)  # raw -> id
    schools_unmatched: list[str] = field(default_factory=list)
    extracted: int = 0
    inserted: int = 0
    skipped_duplicate: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 正規化ヘルパ
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    """ファジーマッチ用の正規化（NFKC + 全角空白除去 + lower）"""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("　", "").replace(" ", "").strip().lower()
    return s


def _resolve_speaker_category(standpoint: str) -> str:
    s = standpoint or ""
    for kw, cat in SPEAKER_RULES:
        if kw.lower() in s.lower():
            return cat
    return "third_party"  # 不明なときの安全弁


def _resolve_medium(source_text: str) -> str:
    s = source_text or ""
    for kw, med in MEDIUM_RULES:
        if kw.lower() in s.lower():
            return med
    return "other"


def _resolve_source_type(source_text: str) -> str:
    s = source_text or ""
    for kw, st in SOURCE_TYPE_RULES:
        if kw.lower() in s.lower():
            return st
    return "other"


URL_RE = re.compile(r"https?://[\w\-./:%?#=&+@~,]+", re.IGNORECASE)


def _extract_url(text: str) -> Optional[str]:
    m = URL_RE.search(text or "")
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Markdown パーサ
# ---------------------------------------------------------------------------

# 学校見出し検出パターン（複数）
SCHOOL_HEADING_PATTERNS = [
    re.compile(r"^#\s+(.+?)$", re.MULTILINE),     # # 慶應義塾中等部
    re.compile(r"^##\s+(.+?)$", re.MULTILINE),    # ## 開成中学校
]

# 発言ブロック開始パターン
BLOCK_PATTERNS = [
    # ### #1 / ### #1 | ヘッダ / ### #1 校長: タイトル
    re.compile(r"^###\s*#\s*(\d+)\b.*$", re.MULTILINE),
    # ### テーマA: ... / ### テーマB ...
    re.compile(r"^###\s*テーマ([A-Z甲乙丙丁戊己庚辛壬癸０-９0-9]+).*$", re.MULTILINE),
]

# キー: 値 抽出 (- **立場**: xxx / - 立場: xxx / **立場**: xxx の3パターン)
KEY_VALUE_RE = re.compile(
    r"^\s*[-*]?\s*\*{0,2}(立場|sentiment|Sentiment|テーマ|発言|出典|引用|URL)\*{0,2}\s*[:：]\s*(.*)$",
    re.MULTILINE,
)

# > 引用ブロック
QUOTE_RE = re.compile(r"^>\s?(.*)$", re.MULTILINE)


def find_school_blocks(text: str) -> list[tuple[str, int, int]]:
    """
    学校名見出し（# / ##）でテキストを区切り、
    [(school_name, start_pos, end_pos), ...] を返す。

    優先順位:
      1) 「## 学校名」が複数あればそれで分割
      2) 無ければ「# 学校名」で分割
      3) どちらも単一ならファイル全体を1ブロック
    """
    # まず ## レベルで「○○中学校」を含む見出しを探す
    candidates_h2 = [
        (m.group(1).strip(), m.start())
        for m in re.finditer(r"^##\s+(.+?)$", text, re.MULTILINE)
        if "中学" in m.group(1) or "中等" in m.group(1) or "学院" in m.group(1) or "学園" in m.group(1)
    ]
    candidates_h1 = [
        (m.group(1).strip(), m.start())
        for m in re.finditer(r"^#\s+(.+?)$", text, re.MULTILINE)
        if "中学" in m.group(1) or "中等" in m.group(1) or "学院" in m.group(1) or "学園" in m.group(1)
    ]

    # 「## サレジオ学院中学校」のような単独見出しが複数あるパターン優先
    if len(candidates_h2) >= 2:
        chosen = candidates_h2
    elif len(candidates_h1) >= 2:
        chosen = candidates_h1
    elif candidates_h1:
        # H1 が一つだけ → ファイル全体をその学校とする
        chosen = candidates_h1
    elif candidates_h2:
        chosen = candidates_h2
    else:
        return []

    # 末尾位置も含めて区間化
    blocks: list[tuple[str, int, int]] = []
    for i, (name, pos) in enumerate(chosen):
        end = chosen[i + 1][1] if i + 1 < len(chosen) else len(text)
        blocks.append((name, pos, end))
    return blocks


def parse_statement_block(
    block_text: str, block_index: int, school_name: str, source_file: str
) -> Optional[Statement]:
    """1つの ### #N ブロックから Statement を抽出"""
    fields = {}
    # キーバリュー抽出
    for m in KEY_VALUE_RE.finditer(block_text):
        key = m.group(1)
        val = m.group(2).strip().strip("*").strip()
        # キー正規化
        if key in ("Sentiment",):
            key = "sentiment"
        if key == "引用":
            key = "発言"
        # 既出のキーは上書きしない（最初を採用）
        if key not in fields:
            fields[key] = val

    # 「発言」が空なら、その後ろの > 引用ブロックを連結して使う
    if "発言" not in fields or not fields.get("発言"):
        quotes = QUOTE_RE.findall(block_text)
        if quotes:
            fields["発言"] = " ".join(q.strip() for q in quotes if q.strip())

    # 「発言:」の値が空かつ次行に > の引用がある場合のサポート
    if fields.get("発言") in ("", None):
        # 「発言: 」直後の連続した > 行を拾う
        m = re.search(r"発言\*{0,2}\s*[:：]\s*\n((?:>.*\n?)+)", block_text)
        if m:
            quote_block = m.group(1)
            qs = [q.strip("> ").strip() for q in quote_block.splitlines() if q.strip()]
            fields["発言"] = " ".join(qs)

    # 必須項目チェック
    excerpt = (fields.get("発言") or "").strip().strip('"「」"')
    if not excerpt:
        return None
    standpoint = (fields.get("立場") or "").strip()
    sentiment = (fields.get("sentiment") or "").strip().lower()
    # "neutral/positive" のような複合値は最初を採用
    sentiment = re.split(r"[,/、・]", sentiment)[0].strip()
    if sentiment not in VALID_SENTIMENTS:
        sentiment = "neutral"
    theme = (fields.get("テーマ") or "").strip()
    source_text = (fields.get("出典") or "").strip()

    if not standpoint and not source_text:
        # 立場も出典も無いのはノイズ
        return None

    return Statement(
        school_name_raw=school_name,
        block_index=block_index,
        standpoint=standpoint,
        sentiment=sentiment,
        theme=theme,
        excerpt=excerpt,
        source_text=source_text,
        source_url=_extract_url(source_text + " " + (fields.get("URL") or "")),
        source_file=source_file,
    )


def split_blocks(school_text: str) -> list[tuple[int, str]]:
    """
    1校分のテキストから、### #N または ### テーマX ブロックに分割し、
    [(index, block_text), ...] を返す。
    """
    # まず ### #N を試す
    starts: list[tuple[int, int]] = []  # (idx, start_pos)
    for m in re.finditer(r"^###\s*#\s*(\d+)\b.*$", school_text, re.MULTILINE):
        try:
            idx = int(m.group(1))
        except ValueError:
            continue
        starts.append((idx, m.start()))

    if not starts:
        # テーマ形式
        for i, m in enumerate(
            re.finditer(r"^###\s*(?:テーマ|【)[^\n]*$", school_text, re.MULTILINE), start=1
        ):
            starts.append((i, m.start()))

    if not starts:
        return []

    # 区間化
    starts.sort(key=lambda t: t[1])
    blocks: list[tuple[int, str]] = []
    for i, (idx, pos) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(school_text)
        blocks.append((idx, school_text[pos:end]))
    return blocks


def parse_material_file(path: Path) -> list[Statement]:
    """1つの material_*.md から Statement のリストを返す"""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []

    school_blocks = find_school_blocks(text)
    if not school_blocks:
        return []

    out: list[Statement] = []
    for school_name, start, end in school_blocks:
        section = text[start:end]
        for idx, block_text in split_blocks(section):
            stmt = parse_statement_block(block_text, idx, school_name, path.name)
            if stmt:
                out.append(stmt)
    return out


# ---------------------------------------------------------------------------
# 学校名 → school_id 逆引き
# ---------------------------------------------------------------------------

class SchoolResolver:
    def __init__(self, conn: sqlite3.Connection):
        rows = conn.execute(
            "SELECT id, name_ja, name_short FROM jpms_schools"
        ).fetchall()
        self.by_norm: dict[str, str] = {}
        self.entries: list[tuple[str, str]] = []  # (norm_name, id)
        for sid, name_ja, name_short in rows:
            for n in (name_ja, name_short):
                if not n:
                    continue
                k = _norm(n)
                self.by_norm.setdefault(k, sid)
                self.entries.append((k, sid))

    def resolve(self, raw: str) -> Optional[str]:
        """学校名から school_id を解決。完全一致 → 包含一致 → 短縮形一致 の順"""
        if not raw:
            return None
        # 「JPMS-DB拡張レポート：駒場東邦中学校 関係者発言スナップショット」のような
        # 飾り言葉を取り除き、最も学校名らしい部分を抽出する
        # 「：」「:」「-」で分割し、各候補を試す
        candidates = [raw]
        for sep in ("：", ":", " ", "・", "—", "-", "#"):
            for c in raw.split(sep):
                c = c.strip()
                if c and ("中学" in c or "中等" in c or "学院" in c or "学園" in c):
                    candidates.append(c)
        # 飾り語を除去
        cleaned = re.sub(r"(関係者発言|多面的評価|サマリー|スナップショット|詳細レポート|レポート|JPMS-?DB|拡張)", "", raw)
        cleaned = cleaned.strip(" :：・—-#")
        if cleaned:
            candidates.append(cleaned)

        for cand in candidates:
            sid = self._resolve_one(cand)
            if sid:
                return sid
        return None

    def _resolve_one(self, raw: str) -> Optional[str]:
        if not raw:
            return None
        k = _norm(raw)
        # 不要な接尾辞を除去
        k_stripped = re.sub(r"中等部$|中学校$|中学$|高等学校$|高校$|学園$|学校$", "", k)
        # 完全一致
        if k in self.by_norm:
            return self.by_norm[k]
        if k_stripped in self.by_norm:
            return self.by_norm[k_stripped]
        # 包含一致（学校名 が raw に含まれる、または raw が name に含まれる）
        # 長いものから優先
        cands = []
        for nk, sid in self.entries:
            if not nk:
                continue
            if nk == k or nk == k_stripped:
                return sid
            if nk in k or k in nk:
                cands.append((len(nk), nk, sid))
            elif k_stripped and (nk in k_stripped or k_stripped in nk):
                cands.append((len(nk), nk, sid))
        if cands:
            # 一番長くマッチしたもの
            cands.sort(reverse=True)
            return cands[0][2]
        return None


# ---------------------------------------------------------------------------
# DB 投入
# ---------------------------------------------------------------------------

def next_id(conn: sqlite3.Connection, table: str, prefix: str, width: int) -> str:
    cur = conn.execute(
        f"SELECT id FROM {table} WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",),
    )
    row = cur.fetchone()
    if not row:
        n = 1
    else:
        last_id: str = row[0]
        try:
            n = int(last_id[len(prefix):]) + 1
        except ValueError:
            n = 1
    return f"{prefix}{str(n).zfill(width)}"


def find_or_create_source(
    conn: sqlite3.Connection, stmt: Statement, dry_run: bool
) -> str:
    """jpms_sources を URL/タイトルで一意化して挿入。返り値は source_id"""
    title = stmt.source_text or "(no title)"
    url = stmt.source_url

    cur = conn.cursor()
    if url:
        row = cur.execute(
            "SELECT id FROM jpms_sources WHERE url = ? LIMIT 1", (url,)
        ).fetchone()
        if row:
            return row[0]
    row = cur.execute(
        "SELECT id FROM jpms_sources WHERE title = ? AND (url IS NULL OR url = '') LIMIT 1",
        (title,),
    ).fetchone()
    if row:
        return row[0]

    sid = next_id(conn, "jpms_sources", "jpms_src_", 6)
    now = datetime.now().isoformat(timespec="seconds")
    if not dry_run:
        cur.execute(
            """
            INSERT INTO jpms_sources
            (id, source_type, title, url, accessed_at, rights_status, primary_or_secondary, reliability_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                sid,
                stmt.source_type,
                title[:500],
                url,
                now,
                "copyrighted_quotable",
                "secondary",
                3,
            ),
        )
    return sid


def is_duplicate(
    conn: sqlite3.Connection, school_id: str, excerpt: str
) -> bool:
    """同一 school_id × excerpt(先頭60字) は重複扱い"""
    head = excerpt[:60]
    row = conn.execute(
        """
        SELECT id FROM jpms_testimonials
        WHERE school_id = ? AND substr(excerpt, 1, 60) = ?
        LIMIT 1
        """,
        (school_id, head),
    ).fetchone()
    return row is not None


def insert_testimonial(
    conn: sqlite3.Connection,
    school_id: str,
    source_id: str,
    stmt: Statement,
    dry_run: bool,
) -> str:
    tid = next_id(conn, "jpms_testimonials", "jpms_t_", 6)
    if not dry_run:
        conn.execute(
            """
            INSERT INTO jpms_testimonials
            (id, school_id, speaker_category, speaker_name, speaker_anonymized,
             medium, excerpt, theme, sentiment, rights_level, source_id, fetched_at, created_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                tid,
                school_id,
                stmt.speaker_category,
                None,
                stmt.medium,
                stmt.excerpt,
                stmt.theme[:200] if stmt.theme else None,
                stmt.sentiment,
                "quoted_with_attribution",
                source_id,
            ),
        )
    return tid


# ---------------------------------------------------------------------------
# 上位ロジック
# ---------------------------------------------------------------------------

def ingest_files(paths: Iterable[Path], dry_run: bool, verbose: bool = False) -> IngestStats:
    stats = IngestStats()
    conn = sqlite3.connect(DB_PATH)
    try:
        resolver = SchoolResolver(conn)
        for p in paths:
            stats.files_processed += 1
            try:
                statements = parse_material_file(p)
            except Exception as e:
                stats.errors.append(f"{p.name}: parse error: {e}")
                continue
            if not statements:
                stats.files_no_school += 1
                if verbose:
                    print(f"  [SKIP] {p.name}: 学校ブロックも発言ブロックも検出されず")
                continue

            # 学校ごとにグループ化
            from collections import defaultdict
            by_school: dict[str, list[Statement]] = defaultdict(list)
            for s in statements:
                by_school[s.school_name_raw].append(s)

            for school_raw, group in by_school.items():
                sid = resolver.resolve(school_raw)
                if not sid:
                    stats.schools_unmatched.append(f"{p.name}: {school_raw}")
                    if verbose:
                        print(f"  [UNMATCHED] {p.name}: '{school_raw}' → school_id 解決失敗")
                    continue
                stats.schools_matched[school_raw] = sid
                if verbose:
                    print(f"  [MATCH] {school_raw} → {sid}  ({len(group)}件)")
                for stmt in group:
                    stats.extracted += 1
                    if is_duplicate(conn, sid, stmt.excerpt):
                        stats.skipped_duplicate += 1
                        continue
                    try:
                        src_id = find_or_create_source(conn, stmt, dry_run)
                        insert_testimonial(conn, sid, src_id, stmt, dry_run)
                        stats.inserted += 1
                    except sqlite3.Error as e:
                        stats.errors.append(
                            f"{p.name} #{stmt.block_index}: SQL error: {e} "
                            f"(speaker={stmt.speaker_category}, medium={stmt.medium})"
                        )
        if not dry_run:
            conn.commit()
    finally:
        conn.close()
    return stats


# ---------------------------------------------------------------------------
# DB 現状サマリー
# ---------------------------------------------------------------------------

def print_db_summary() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        total_schools = conn.execute("SELECT COUNT(*) FROM jpms_schools").fetchone()[0]
        total_test = conn.execute("SELECT COUNT(*) FROM jpms_testimonials").fetchone()[0]
        with_test = conn.execute(
            "SELECT COUNT(DISTINCT school_id) FROM jpms_testimonials"
        ).fetchone()[0]
        ge5 = conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT school_id FROM jpms_testimonials
                GROUP BY school_id HAVING COUNT(*) >= 5
            )
            """
        ).fetchone()[0]
        zero = total_schools - with_test

        # 都道府県別カバレッジ
        rows = conn.execute(
            """
            SELECT s.location_pref,
                   COUNT(DISTINCT s.id)                                         AS school_count,
                   COUNT(DISTINCT CASE WHEN t.id IS NOT NULL THEN s.id END)     AS with_testimonials
            FROM jpms_schools s
            LEFT JOIN jpms_testimonials t ON t.school_id = s.id
            GROUP BY s.location_pref
            ORDER BY s.location_pref
            """
        ).fetchall()

        all_prefs = {
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
        }
        in_db_prefs = {r[0] for r in rows}
        missing_pref = sorted(all_prefs - in_db_prefs)

        no_test_pref = [r[0] for r in rows if r[2] == 0]

        print("=" * 64)
        print("JPMS-DB 現状サマリー")
        print("=" * 64)
        print(f"全学校数: {total_schools}")
        print(f"全 testimonial 件数: {total_test}")
        print(f"testimonial が 1件以上ある学校: {with_test} 校")
        print(f"  うち 5件以上: {ge5} 校")
        print(f"  0件: {zero} 校")
        print()
        print("都道府県別 testimonial カバレッジ:")
        for pref, sc, wt in rows:
            mark = "  " if wt > 0 else "× "
            print(f"  {mark}{pref:<6}  学校数={sc:>3}  testimonial有={wt:>3}")
        print()
        if no_test_pref:
            print(f"testimonial 0件の都道府県 ({len(no_test_pref)}): {', '.join(no_test_pref)}")
        if missing_pref:
            print(f"DBに学校が未登録の都道府県 ({len(missing_pref)}): {', '.join(missing_pref)}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="JPMS testimonials ingest")
    parser.add_argument("files", nargs="*", help="material_*.md ファイルへのパス")
    parser.add_argument("--all", action="store_true", help="reports/ 配下の material_*.md を全処理")
    parser.add_argument("--dry-run", action="store_true", help="DB に書き込まず抽出のみ")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログ")
    parser.add_argument("--summary", action="store_true", help="DB 現状サマリーを出力して終了")
    args = parser.parse_args()

    if args.summary:
        print_db_summary()
        return 0

    if args.all:
        files = sorted(REPORTS_DIR.glob("material_*.md"))
    else:
        files = [Path(p) for p in args.files]

    if not files:
        parser.print_help()
        return 1

    print(f"対象ファイル数: {len(files)}  (dry-run={args.dry_run})")
    stats = ingest_files(files, dry_run=args.dry_run, verbose=args.verbose)

    print()
    print("=" * 64)
    print("Ingest 結果")
    print("=" * 64)
    print(f"処理ファイル数         : {stats.files_processed}")
    print(f"  内 学校抽出失敗      : {stats.files_no_school}")
    print(f"抽出された発言件数     : {stats.extracted}")
    print(f"  → 投入成功          : {stats.inserted}")
    print(f"  → 重複スキップ      : {stats.skipped_duplicate}")
    print(f"学校マッチ成功         : {len(stats.schools_matched)}  unique 学校")
    print(f"学校マッチ失敗         : {len(stats.schools_unmatched)} 件")
    if stats.schools_unmatched:
        print("  未マッチ学校:")
        for u in stats.schools_unmatched[:30]:
            print(f"    - {u}")
    if stats.errors:
        print(f"エラー: {len(stats.errors)} 件")
        for e in stats.errors[:20]:
            print(f"  - {e}")
    if args.dry_run:
        print("\n*** DRY-RUN モード: DB への書き込みは行われていません ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
