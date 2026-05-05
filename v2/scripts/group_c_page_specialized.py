#!/usr/bin/env python3
"""JPMS-DB v2 - Group C: ページ種別特化抽出

5つのカテゴリに専門化したエクストラクタを束ね、各HTML種別の
構造的特徴を活かして 1ファイルあたり最大限の引用を取り出す。

C-01: voice / interview / message      -> 構造的インタビュー Q&A
C-02: curriculum / education / school_life -> 教員視点の授業/生徒の学び
C-03: progress / career / alumni       -> 進路実績ページ内の卒業生コメント
C-04: parent / pta / family            -> 保護者会便り、PTA活動報告
C-05: principal / philosophy / mission -> 長文校長挨拶、建学理念ナラティブ

入力 : raw_html_cache/<school_id>/<page>.html
出力 : codex_output/group_c_page_specialized.jsonl
DB   : jpms_v2.db.testimonials_v2 への直接投入

倫理:
  - 公開HP -> quoted_with_attribution
  - 在校生・未成年想定 -> anonymized_only (C-01/02 の student_current)
  - 引用 30-400字以内
  - 既存DB + 自JSONL内で重複除去 (quote_text 先頭80字 prefix)
"""
from __future__ import annotations

import re
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Iterable, Optional

from bs4 import BeautifulSoup


BASE = Path('/Users/nishimura+/projects/research/jpms-db/v2')
CACHE = BASE / 'raw_html_cache'
DB = BASE / 'jpms_v2.db'
OUT = BASE / 'codex_output' / 'group_c_page_specialized.jsonl'
PROGRESS = BASE / 'codex_progress' / 'group_c.json'


# ---------------------------------------------------------------------------
# 共通: HTML 読み込み・段落抽出
# ---------------------------------------------------------------------------

def read_html(fpath: Path) -> str:
    raw = fpath.read_bytes()
    m = re.search(rb'charset=[\'"]?([a-zA-Z0-9_-]+)', raw[:2000], re.IGNORECASE)
    enc = 'utf-8'
    if m:
        d = m.group(1).decode('ascii', errors='ignore').lower()
        if d in ('utf-8', 'utf8'):
            enc = 'utf-8'
        elif d in ('shift_jis', 'sjis', 'shift-jis', 'cp932', 'ms932', 'x-sjis'):
            enc = 'cp932'
        elif d in ('euc-jp', 'eucjp', 'euc_jp'):
            enc = 'euc-jp'
        elif d in ('iso-2022-jp', 'jis'):
            enc = 'iso-2022-jp'
        else:
            enc = d
    try:
        return raw.decode(enc, errors='ignore')
    except Exception:
        for fb in ('utf-8', 'cp932', 'euc-jp'):
            try:
                return raw.decode(fb, errors='ignore')
            except Exception:
                continue
        return raw.decode('utf-8', errors='ignore')


def parse_main(html: str):
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header',
                     'aside', 'form']):
        tag.decompose()
    for sel in soup.select(
        '.breadcrumb, .breadcrumbs, .pankuzu, #breadcrumb, #breadcrumbs, '
        '.menu, #menu, .nav, .global-nav, .gnav, .sidebar, #sidebar'
    ):
        sel.decompose()
    title = ''
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    main = (
        soup.find('main')
        or soup.find(id=re.compile(r'main|content', re.I))
        or soup.find(class_=re.compile(r'main|content|article', re.I))
        or soup.find('article')
        or soup.body
        or soup
    )
    return soup, main, title


def get_paragraphs(main) -> list[str]:
    paragraphs: list[str] = []
    if not main:
        return paragraphs
    for el in main.find_all(['p', 'div', 'li', 'blockquote', 'section', 'dd']):
        if el.find(['p', 'blockquote']) and el.name == 'div':
            continue
        t = el.get_text(separator=' ', strip=True)
        if not t:
            continue
        t = re.sub(r'\s+', ' ', t).strip()
        if t:
            paragraphs.append(t)
    return paragraphs


def extract_qa_blocks(main) -> list[str]:
    """構造的 Q&A / インタビュー形式の段落を抽出。
    - <dl><dt>Q</dt><dd>A</dd></dl>
    - <h*>質問</h*> の直後の <p>
    - <blockquote>
    """
    out: list[str] = []
    if not main:
        return out
    # <dl> 内の <dd>
    for dl in main.find_all('dl'):
        for dd in dl.find_all('dd'):
            t = dd.get_text(separator=' ', strip=True)
            t = re.sub(r'\s+', ' ', t)
            if 60 <= len(t) <= 800:
                out.append(t)
    # blockquote
    for bq in main.find_all('blockquote'):
        t = bq.get_text(separator=' ', strip=True)
        t = re.sub(r'\s+', ' ', t)
        if 40 <= len(t) <= 800:
            out.append(t)
    # heading + next paragraph
    for h in main.find_all(['h2', 'h3', 'h4']):
        title_text = (h.get_text(separator=' ', strip=True) or '').strip()
        if not title_text:
            continue
        # Q&A 系見出しまたは語り見出しか
        keywords = ['質問', 'Q.', 'Q：', 'Q：', 'インタビュー',
                    'メッセージ', '挨拶', 'あいさつ', 'ご挨拶',
                    '声', '体験', '想い', '思い']
        if not any(k in title_text for k in keywords) and len(title_text) > 30:
            continue
        # 同階層の次の p / div を取る
        nxt = h.find_next_sibling()
        hops = 0
        while nxt and hops < 3:
            if nxt.name in ('p', 'div', 'blockquote'):
                t = nxt.get_text(separator=' ', strip=True)
                t = re.sub(r'\s+', ' ', t)
                if 60 <= len(t) <= 800:
                    out.append(t)
                    break
            nxt = nxt.find_next_sibling()
            hops += 1
    return out


def split_long_narrative(p: str, max_len: int = 380) -> list[str]:
    """非常に長い段落を文単位で 200~380字のチャンクに分割。
    校長挨拶など。"""
    if len(p) <= max_len:
        return [p]
    sentences = re.split(r'(?<=[。！？])\s*', p)
    chunks: list[str] = []
    cur = ''
    for s in sentences:
        if not s:
            continue
        if len(cur) + len(s) <= max_len:
            cur += s
        else:
            if len(cur) >= 80:
                chunks.append(cur)
            cur = s
    if len(cur) >= 80:
        chunks.append(cur)
    return chunks


# ---------------------------------------------------------------------------
# 共通: 品質判定/整形
# ---------------------------------------------------------------------------

NAV_NEG = [
    'プライバシー', 'cookie', 'クッキー', '著作権', 'サイトマップ',
    'お問い合わせ', '個人情報保護', '採用情報', '会社概要',
    '利用規約', 'twitter', 'facebook', 'instagram', 'youtube',
    'all rights', 'copyright', '一覧へ', 'もっと見る', '詳しく見る',
    'メニュー', 'navigation', 'breadcrumb', 'ログイン',
    'メールアドレス', 'パスワード', 'ダウンロード',
    'ホーム>', 'TOP>', '保護中',
]

EVENT_NEG_STRONG = [
    'お申し込み', '申し込みフォーム', '受付中', '開催中',
]


def looks_navigational(p: str) -> bool:
    pl = p.lower()
    if any(n.lower() in pl for n in NAV_NEG):
        return True
    if p.count('|') >= 3 or p.count('・') >= 8 or p.count('>') >= 2:
        return True
    if p.count('　') >= 4:
        return True
    if p.count(' ') / max(1, len(p)) > 0.18:
        return True
    if 'お知らせ' in p[:20] and re.search(r'\d{4}/\d{1,2}/\d{1,2}', p):
        return True
    if '404' in p or 'not found' in pl or 'お探しのページ' in p:
        return True
    if re.match(r'^[\s\d年月日.\-/]{6,20}', p):
        return True
    if len(re.findall(r'\d{4}[\.\-/年]\d{1,2}', p)) >= 2:
        return True
    if any(s in p for s in EVENT_NEG_STRONG):
        return True
    return False


def basic_quality(p: str, min_len: int = 40, max_len: int = 600) -> bool:
    if len(p) < min_len or len(p) > max_len:
        return False
    if looks_navigational(p):
        return False
    jp_chars = sum(1 for c in p if '぀' <= c <= '鿿')
    if jp_chars < len(p) * 0.35:
        return False
    punct = p.count('、') + p.count('。') + p.count('，')
    if len(p) >= 80 and punct < 2:
        return False
    if '。' not in p and '！' not in p and '？' not in p and '」' not in p:
        return False
    return True


def trim_quote(p: str, max_len: int = 380) -> str:
    if len(p) <= max_len:
        return p
    cut = p[:max_len]
    last = max(cut.rfind('。'), cut.rfind('！'), cut.rfind('？'), cut.rfind('」'))
    if last > 60:
        return cut[:last + 1]
    return cut + '…'


def make_summary(quote: str) -> str:
    s = quote.replace('\n', ' ').strip()
    if len(s) <= 50:
        return s
    head = s[:50]
    last = max(head.rfind('、'), head.rfind('。'))
    if last > 20:
        return head[:last] + '…'
    return head + '…'


def quote_key(quote: str) -> str:
    """重複判定用キー (先頭80字 + 末尾30字)"""
    head = re.sub(r'\s+', '', quote)[:80]
    tail = re.sub(r'\s+', '', quote)[-30:]
    return hashlib.md5((head + '||' + tail).encode('utf-8')).hexdigest()


def prefix_key(quote: str) -> str:
    return re.sub(r'\s+', '', quote)[:80]


# ---------------------------------------------------------------------------
# DB ヘルパ
# ---------------------------------------------------------------------------

def load_url_map() -> tuple[dict, dict]:
    if not DB.exists():
        return {}, {}
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT school_id, page_path, full_url FROM school_homepage_assets")
    m = {}
    for sid, page, url in cur.fetchall():
        m[(sid, page)] = url
    cur.execute("SELECT id, homepage_url FROM schools_v2")
    fb = {}
    for sid, url in cur.fetchall():
        if url:
            fb[sid] = url
    conn.close()
    return m, fb


def load_existing_quote_prefixes() -> set[str]:
    if not DB.exists():
        return set()
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT quote_text FROM testimonials_v2")
    seen = set()
    for (qt,) in cur.fetchall():
        if qt:
            seen.add(prefix_key(qt))
    conn.close()
    return seen


def load_existing_school_ids() -> set[str]:
    if not DB.exists():
        return set()
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT id FROM schools_v2")
    ids = {r[0] for r in cur.fetchall()}
    conn.close()
    return ids


# ---------------------------------------------------------------------------
# ページ判定
# ---------------------------------------------------------------------------

PAGE_GROUPS = {
    'C01': ['voice'],                   # interview/message は cache に存在せず
    'C02': ['curriculum', 'schoollife'],
    'C03': ['progress'],
    'C04': ['parent', 'pta'],
    'C05': ['principal', 'philosophy', 'mission'],
}

# 二次マイニング: 各グループのアンカー語が出れば抽出する補助ページ群
SECONDARY_PAGES = ['about', 'root', 'events', 'admission']

# C-01 の secondary 候補（在校生・卒業生インタビューが about/root に載るケース）
C01_SECONDARY = ['about', 'root', 'schoollife', 'events']
# C-02 の secondary（カリキュラム要素が about/root に断片化）
C02_SECONDARY = ['about', 'root', 'voice', 'events']
# C-03 の secondary（進路の語りが about/voice/root に出る）
C03_SECONDARY = ['voice', 'about', 'root']
# C-04 の secondary は既存 B-5 が広めに走っているのでここでは追加しない
C04_SECONDARY: list[str] = []
# C-05 の secondary（校長挨拶が about/root に書かれるケース）
C05_SECONDARY = ['about', 'root']


# ===========================================================================
# C-01 voice / interview / message  (在校生 / 卒業生 Q&A)
# ===========================================================================

C01_STUDENT_ANCHORS_CURRENT = [
    '高1', '高2', '高3', '中1', '中2', '中3',
    '1年', '2年', '3年', '4年', '5年', '6年',
    '在校生', 'クラブ', '部活', '生徒会', '委員会',
    '私は', '僕は', 'わたしは', 'ぼくは',
    '先生', '授業', '行事', '友だち', '友達',
    'クラスメイト', '担任', '体育祭', '文化祭',
]
C01_ALUMNI_ANCHORS = [
    '卒業生', '卒業して', '卒業後',
    '大学', '進学', '社会人', '勤務', '就職',
    '○○大学', 'OB', 'OG',
]
C01_INTERVIEW_HINTS = [
    'Q.', 'Q：', 'Q：', 'Q1', 'Q2', '質問', '答え',
    '——', 'インタビュアー',
]


def c01_classify(quote: str, page_title: str) -> tuple[str, str]:
    """C-01 ページ内段落の話者推定。
    一人称（私/僕）+ 卒業/大学/社会人 -> student_alumni
    一人称 + 在校/部活/授業 -> student_current
    その他は student_current（voice ページの主流）
    """
    has_first_person = any(fp in quote for fp in
                           ['私は', '僕は', 'わたしは', 'ぼくは',
                            '私が', '僕が', '自分は', '自分が', '私の', '僕の'])
    t = (page_title or '') + ' ' + quote
    # 卒業生
    alumni_strong = ['卒業して', '卒業後', '在学中', 'OB', 'OG',
                     '勤務しています', '社会人として', '今は', '振り返ると',
                     '大学に進学', '大学院']
    if has_first_person and any(a in quote for a in alumni_strong):
        return 'student_alumni', '卒業生'
    # 教員（「指導しています」「私たち教員」など本人視点）
    if ('私たち教員' in quote or '私たち教師' in quote
            or '指導しています' in quote or '担任しています' in quote):
        return 'teacher', '教員'
    # 保護者
    if any(a in quote for a in ['娘', '息子', 'うちの子', '我が家', '親として']):
        return 'parent', '保護者'
    # それ以外は在校生
    return 'student_current', '在校生'


def c01_quotable(p: str, in_voice_section: bool) -> bool:
    if not basic_quality(p, 40, 600):
        return False
    has_anchor = (
        any(a in p for a in C01_STUDENT_ANCHORS_CURRENT)
        or any(a in p for a in C01_ALUMNI_ANCHORS)
        or any(a in p for a in C01_INTERVIEW_HINTS)
    )
    if not has_anchor and not in_voice_section:
        return False
    # 一人称語尾の傾向
    first_person = ['です', 'ます', 'でした', 'ました', '思います', '感じ',
                    '楽しい', '楽しかった', 'がんばり', '頑張り',
                    '私は', '僕は', 'わたしは', 'ぼくは', '私が', '僕が']
    if not any(s in p for s in first_person):
        return False
    # 歴史記述・建学者紹介は除外
    history_signals = ['先生は', '先生が', '生まれ', '幕府', '維新', '初代', '設立',
                       '創立', '開校', '発足', '建学者', '建学の精神',
                       '輩出してきました', '輩出してきた', '継承されて',
                       '継承してきた', '受け継がれ', '受け継いで',
                       '年継承', '年に', '年創立', '年設立', '年開校']
    if sum(1 for h in history_signals if h in p) >= 2:
        return False
    # 西暦が複数 -> 歴史記述
    if len(re.findall(r'1[6-9]\d{2}年|20\d{2}年', p)) >= 2:
        return False
    # ニュースリスト形式（YYYY.MM.DD UP）
    if re.search(r'\d{4}\.\d{1,2}\.\d{1,2}\s*UP', p):
        return False
    if 'UP' in p and re.search(r'\d{4}\.\d{1,2}', p):
        return False
    # 行事報告で「来場者」「校門」「皆さま」などが続く広報的内容
    pr_signals = ['来場者', '校門', '皆さま', 'ご来校', 'ご家族', 'ご見学',
                  '誠にありがとう', 'おかげさまで', '賑わ']
    if sum(1 for s in pr_signals if s in p) >= 2:
        return False
    return True


def c01_score(p: str, page_title: str) -> int:
    s = 0
    if any(a in p for a in C01_STUDENT_ANCHORS_CURRENT):
        s += 2
    if any(a in p for a in C01_ALUMNI_ANCHORS):
        s += 2
    if any(a in p for a in C01_INTERVIEW_HINTS):
        s += 2
    if 60 <= len(p) <= 350:
        s += 2
    if p.endswith(('。', '」')):
        s += 1
    if 'voice' in (page_title or '').lower() or '声' in (page_title or ''):
        s += 1
    return s


# ===========================================================================
# C-02 curriculum / education / school_life  (教員視点の授業 / 生徒の学び)
# ===========================================================================

C02_TEACHER_ANCHORS = [
    '指導', '授業', '本校では', 'カリキュラム', '教育課程',
    '学習', 'プログラム', '科目', '教科', '探究',
    '生徒たち', '私たち教員', '私たち教師', '本校の', '本校は',
    '教員', '教諭', '担当',
]
C02_STUDENT_LEARNING_ANCHORS = [
    '楽しい', '面白い', 'おもしろ', '興味',
    '学べ', '学ぶこと', '学びました', '気付き', '気づき',
    '驚き', '発見', '挑戦',
]
C02_SUBJECTS = ['国語', '数学', '英語', '理科', '社会', '音楽', '美術',
                '体育', '家庭科', '技術', '情報', '探究', 'STEM', 'STEAM']


def c02_classify(p: str, page_title: str) -> tuple[str, str]:
    teacher_score = sum(1 for a in C02_TEACHER_ANCHORS if a in p)
    learner_score = sum(1 for a in C02_STUDENT_LEARNING_ANCHORS if a in p)
    if '本校' in p or '指導' in p or 'カリキュラム' in p or '教育課程' in p:
        return 'teacher', '教員（カリキュラム紹介）'
    if learner_score >= 2 and teacher_score == 0:
        return 'student_current', '生徒（学びの体験）'
    return 'teacher', '教員（授業紹介）'


def c02_quotable(p: str, page_dedicated: bool = False) -> bool:
    if not basic_quality(p, 50, 600):
        return False
    has_curriculum_anchor = (
        any(a in p for a in C02_TEACHER_ANCHORS)
        or any(a in p for a in C02_STUDENT_LEARNING_ANCHORS)
        or any(s in p for s in C02_SUBJECTS)
    )
    # 専用ページなら教育関連の広い語も許容
    if not has_curriculum_anchor and page_dedicated:
        edu_words = ['学び', '学習', '学ぶ', '教育', '生徒', '児童',
                     '授業', '学校生活', '学園生活', 'クラス',
                     '取り組み', '活動', '行事', '体験']
        if not any(w in p for w in edu_words):
            return False
    elif not has_curriculum_anchor:
        return False
    # ナビ・概要羅列を弾く
    if p.count('時間') >= 4 or p.count('単位') >= 3:
        return False
    return True


def c02_score(p: str) -> int:
    s = 0
    s += sum(1 for a in C02_TEACHER_ANCHORS if a in p)
    s += sum(1 for a in C02_STUDENT_LEARNING_ANCHORS if a in p)
    if any(sub in p for sub in C02_SUBJECTS):
        s += 1
    if 80 <= len(p) <= 400:
        s += 2
    if p.endswith(('。', '」')):
        s += 1
    return s


# ===========================================================================
# C-03 progress / career / alumni  (進路実績ページ内の卒業生コメント)
# ===========================================================================

C03_ALUMNI_ANCHORS = [
    '卒業生', '卒業後', '卒業して', 'OB', 'OG', '〇〇期', '○○期',
    '大学院', '大学に進学', '大学で', '社会人として',
    '在学中', '振り返って', '振り返ると', '今思えば', '本校で',
]
C03_NUMERIC_NEG = [
    '合格者数', '進学者数', '出願', '受験者数', '志願者',
    '名(', '名（', '人(', '人（',
]


def c03_quotable(p: str) -> bool:
    if not basic_quality(p, 60, 600):
        return False
    if not any(a in p for a in C03_ALUMNI_ANCHORS):
        return False
    # 数字の羅列ページではなく、ナラティブであること
    digit_ratio = sum(1 for c in p if c.isdigit()) / max(1, len(p))
    if digit_ratio > 0.12:
        return False
    if any(n in p for n in C03_NUMERIC_NEG):
        return False
    # 一人称感がある（語り）
    first_person_signals = ['私', '僕', '自分', 'ぼく', 'わたし',
                            '思います', '感じ', '今は', '振り返']
    if not any(s in p for s in first_person_signals):
        return False
    return True


def c03_score(p: str) -> int:
    s = 0
    s += sum(1 for a in C03_ALUMNI_ANCHORS if a in p)
    if 80 <= len(p) <= 400:
        s += 2
    if p.endswith(('。', '」')):
        s += 1
    return s


# ===========================================================================
# C-04 parent / pta / family  (保護者会便り / PTA活動報告)
# ===========================================================================

C04_PARENT_ANCHORS = [
    '保護者', '保護者会', '保護者の声', '保護者の方',
    'PTA', '父母会', '父母の会', '後援会', '育友会',
    '父兄', '母の会', 'ファミリー', '家庭と学校', '家庭との連携',
]
C04_STRONG = [
    'PTA', '保護者会', '父母会', '父母の会', '後援会', '育友会',
    '保護者の声', '保護者からのメッセージ', '保護者メッセージ',
]


def c04_subrole(p: str) -> str:
    if 'PTA' in p:
        return 'PTA'
    if '後援会' in p:
        return '後援会'
    if '父母会' in p or '父母の会' in p:
        return '父母会'
    if '育友会' in p:
        return '育友会'
    if '保護者会' in p:
        return '保護者会'
    return '保護者'


def c04_quotable(p: str, page_dedicated: bool, page_is_parent_voice: bool) -> bool:
    if not basic_quality(p, 50, 600):
        return False
    has_parent_anchor = any(a in p for a in C04_PARENT_ANCHORS)
    if page_dedicated:
        # parent/pta ページなら、保護者語が無くても以下のいずれかでOK:
        #  (A) 親視点の語り（娘・息子・うちの子・我が家・親として）
        #  (B) 学校→保護者へ向けた発信（感謝/卒業/入学+本校/貴校など）
        if not has_parent_anchor:
            voice_signals = ['娘', '息子', 'うちの子', '我が家',
                             '親として', '親子', 'ご家庭', '家族',
                             '入学', '卒業', '本校', '貴校',
                             '成長', '感謝', '体験', '見守']
            if sum(1 for s in voice_signals if s in p) < 2:
                return False
    else:
        # secondary ページは強アンカー必須
        if not any(a in p for a in C04_STRONG):
            return False
    return True


def c04_score(p: str, page_dedicated: bool) -> int:
    s = 0
    if page_dedicated:
        s += 4
    s += sum(2 for kw in C04_PARENT_ANCHORS if kw in p)
    if 80 <= len(p) <= 350:
        s += 2
    if p.endswith(('。', '」')):
        s += 1
    return s


# ===========================================================================
# C-05 principal / philosophy / mission  (校長挨拶 / 建学理念ナラティブ)
# ===========================================================================

C05_PRINCIPAL_HINTS = [
    '校長', '理事長', '学園長', '学校長', '理事',
    '建学の精神', '建学', '教育理念', '教育方針', '校訓', '理念',
    '本校', '本学園', '本学院',
]
C05_NARRATIVE_HINTS = [
    '私たち', '私ども', '思います', '考えています', '願っています',
    '育んで', '育てて', '人材', '社会', '世界', '未来', '夢',
]


def c05_classify(p: str, page_title: str) -> tuple[str, str]:
    if '理事長' in (page_title or '') or '理事長' in p[:80]:
        return 'chairperson', '理事長'
    return 'principal', '校長'


def c05_quotable(p: str, page_dedicated: bool) -> bool:
    if not basic_quality(p, 60, 600):
        return False
    has_principal_anchor = any(a in p for a in C05_PRINCIPAL_HINTS)
    has_narrative = any(a in p for a in C05_NARRATIVE_HINTS)
    # 校長挨拶ページは「教育」「生徒」「学校」などを含むナラティブ全般を許容
    edu_words = ['教育', '生徒', '児童', '学校', '学園', '学院',
                 '人間', '人格', '指導', '学び', '成長',
                 '社会', '世界', '未来', '夢', '志', '心']
    has_edu = any(w in p for w in edu_words)
    if page_dedicated:
        if not (has_principal_anchor or has_narrative or has_edu):
            return False
    else:
        if not has_principal_anchor:
            return False
    return True


def c05_score(p: str, page_dedicated: bool) -> int:
    s = 0
    if page_dedicated:
        s += 4
    s += sum(1 for a in C05_PRINCIPAL_HINTS if a in p)
    s += sum(1 for a in C05_NARRATIVE_HINTS if a in p)
    if 100 <= len(p) <= 400:
        s += 2
    if p.endswith(('。', '」')):
        s += 1
    return s


# ---------------------------------------------------------------------------
# パイプライン
# ---------------------------------------------------------------------------

def context_label(page_name: str, group_id: str) -> str:
    base = {
        'voice': '在校生・卒業生の声ページ',
        'interview': 'インタビューページ',
        'message': 'メッセージページ',
        'curriculum': 'カリキュラムページ',
        'education': '教育ページ',
        'schoollife': '学校生活ページ',
        'progress': '進路実績ページ',
        'career': 'キャリアページ',
        'alumni': '卒業生ページ',
        'parent': '保護者向けページ',
        'pta': 'PTA・保護者会ページ',
        'family': '家庭連携ページ',
        'principal': '校長挨拶ページ',
        'philosophy': '教育理念ページ',
        'mission': '建学理念ページ',
    }.get(page_name, page_name)
    return f'{base} [{group_id}]'


def is_minor_role(role: str) -> bool:
    """未成年と推定される役割"""
    return role in ('student_current',)


def process_school(
    sd: Path,
    url_map: dict,
    url_fb: dict,
    seen_keys: set[str],
) -> list[dict]:
    sid = sd.name
    items: list[dict] = []

    def add(rec: dict):
        k = quote_key(rec['quote_text'])
        pk = prefix_key(rec['quote_text'])
        if k in seen_keys or pk in seen_keys:
            return False
        seen_keys.add(k)
        seen_keys.add(pk)
        items.append(rec)
        return True

    secondary_map = {
        'C01': C01_SECONDARY,
        'C02': C02_SECONDARY,
        'C03': C03_SECONDARY,
        'C04': C04_SECONDARY,
        'C05': C05_SECONDARY,
    }

    for group_id, page_list in PAGE_GROUPS.items():
        # group ごとに 1校あたり最大件数（キャップ）
        cap = {'C01': 15, 'C02': 15, 'C03': 10, 'C04': 12, 'C05': 12}[group_id]
        per_group = 0
        # primary (= 専用ページ)を先に試し、その後 secondary
        primary_list = [(n, True) for n in page_list]
        secondary_list = [(n, False) for n in secondary_map.get(group_id, [])
                          if n not in page_list]
        for page_name, is_primary in primary_list + secondary_list:
            if per_group >= cap:
                break
            fpath = sd / f'{page_name}.html'
            if not fpath.exists():
                continue
            try:
                html = read_html(fpath)
            except Exception:
                continue
            soup, main, title = parse_main(html)
            paragraphs = get_paragraphs(main)
            # group C-01 は構造的 Q&A も追加で吸い上げる
            if group_id == 'C01':
                paragraphs = paragraphs + extract_qa_blocks(main)
            # group C-05 では長文校長挨拶を文単位分割
            if group_id == 'C05' and is_primary:
                expanded = []
                for p in paragraphs:
                    if len(p) > 380:
                        expanded.extend(split_long_narrative(p))
                    else:
                        expanded.append(p)
                paragraphs = expanded
            page_url = url_map.get((sid, page_name), '') or url_fb.get(sid, '')
            ctx = context_label(page_name, group_id)
            if not is_primary:
                ctx = ctx + '/secondary'

            # ---- ディスパッチ ----
            if group_id == 'C01':
                title_l = (title or '').lower()
                in_voice = is_primary or any(
                    k in (title or '')
                    for k in ['声', 'voice', 'インタビュー', 'interview',
                              'メッセージ', 'message']
                )
                cand = []
                threshold = 2 if is_primary else 4
                for p in paragraphs:
                    if not c01_quotable(p, in_voice):
                        continue
                    s = c01_score(p, title)
                    if s < threshold:
                        continue
                    cand.append((s, p))
                cand.sort(key=lambda x: -x[0])
                for sc, p in cand:
                    if per_group >= cap:
                        break
                    quote = trim_quote(p)
                    if len(quote) < 30:
                        continue
                    role, attr = c01_classify(quote, title)
                    rights = 'anonymized_only' if is_minor_role(role) \
                        else 'quoted_with_attribution'
                    rec = {
                        'school_id': sid,
                        'speaker_role': role,
                        'speaker_attribute': attr,
                        'quote_text': quote,
                        'quote_summary': make_summary(quote),
                        'context': ctx,
                        'source_url': page_url,
                        'source_page': page_name,
                        'rights_level': rights,
                        'group_id': group_id,
                    }
                    if add(rec):
                        per_group += 1

            elif group_id == 'C02':
                cand = []
                threshold = 3 if is_primary else 5
                for p in paragraphs:
                    if not c02_quotable(p, page_dedicated=is_primary):
                        continue
                    s = c02_score(p)
                    if s < threshold:
                        continue
                    cand.append((s, p))
                cand.sort(key=lambda x: -x[0])
                for sc, p in cand:
                    if per_group >= cap:
                        break
                    quote = trim_quote(p)
                    if len(quote) < 30:
                        continue
                    role, attr = c02_classify(quote, title)
                    rights = 'anonymized_only' if is_minor_role(role) \
                        else 'quoted_with_attribution'
                    rec = {
                        'school_id': sid,
                        'speaker_role': role,
                        'speaker_attribute': attr,
                        'quote_text': quote,
                        'quote_summary': make_summary(quote),
                        'context': ctx,
                        'source_url': page_url,
                        'source_page': page_name,
                        'rights_level': rights,
                        'group_id': group_id,
                    }
                    if add(rec):
                        per_group += 1

            elif group_id == 'C03':
                cand = []
                threshold = 2 if is_primary else 3
                for p in paragraphs:
                    if not c03_quotable(p):
                        continue
                    s = c03_score(p)
                    if s < threshold:
                        continue
                    cand.append((s, p))
                cand.sort(key=lambda x: -x[0])
                for sc, p in cand:
                    if per_group >= cap:
                        break
                    quote = trim_quote(p)
                    if len(quote) < 30:
                        continue
                    rec = {
                        'school_id': sid,
                        'speaker_role': 'student_alumni',
                        'speaker_attribute': '卒業生（進路実績ページ）',
                        'quote_text': quote,
                        'quote_summary': make_summary(quote),
                        'context': ctx,
                        'source_url': page_url,
                        'source_page': page_name,
                        'rights_level': 'quoted_with_attribution',
                        'group_id': group_id,
                    }
                    if add(rec):
                        per_group += 1

            elif group_id == 'C04':
                page_dedicated = page_name in ('parent', 'pta')
                title_l = (title or '').lower()
                page_is_parent_voice = any(
                    k in (title or '')
                    for k in ['保護者メッセージ', '保護者の声',
                              '保護者から', '父母の声',
                              '保護者からのメッセージ']
                )
                cand = []
                threshold = 4 if page_dedicated else 6
                for p in paragraphs:
                    if not c04_quotable(p, page_dedicated, page_is_parent_voice):
                        continue
                    s = c04_score(p, page_dedicated)
                    if s < threshold:
                        continue
                    cand.append((s, p))
                cand.sort(key=lambda x: -x[0])
                for sc, p in cand:
                    if per_group >= cap:
                        break
                    quote = trim_quote(p)
                    if len(quote) < 30:
                        continue
                    attr = c04_subrole(quote)
                    rec = {
                        'school_id': sid,
                        'speaker_role': 'parent',
                        'speaker_attribute': attr,
                        'quote_text': quote,
                        'quote_summary': make_summary(quote),
                        'context': ctx,
                        'source_url': page_url,
                        'source_page': page_name,
                        'rights_level': 'quoted_with_attribution',
                        'group_id': group_id,
                    }
                    if add(rec):
                        per_group += 1

            elif group_id == 'C05':
                page_dedicated = page_name in ('principal', 'philosophy', 'mission')
                cand = []
                threshold = 3 if page_dedicated else 5
                for p in paragraphs:
                    if not c05_quotable(p, page_dedicated):
                        continue
                    s = c05_score(p, page_dedicated)
                    if s < threshold:
                        continue
                    cand.append((s, p))
                cand.sort(key=lambda x: -x[0])
                for sc, p in cand:
                    if per_group >= cap:
                        break
                    quote = trim_quote(p)
                    if len(quote) < 30:
                        continue
                    role, attr = c05_classify(quote, title)
                    rec = {
                        'school_id': sid,
                        'speaker_role': role,
                        'speaker_attribute': attr,
                        'quote_text': quote,
                        'quote_summary': make_summary(quote),
                        'context': ctx,
                        'source_url': page_url,
                        'source_page': page_name,
                        'rights_level': 'quoted_with_attribution',
                        'group_id': group_id,
                    }
                    if add(rec):
                        per_group += 1

    return items


def insert_into_db(records: list[dict]) -> tuple[int, int]:
    if not records:
        return 0, 0
    if not DB.exists():
        return 0, len(records)
    conn = sqlite3.connect(str(DB), timeout=600.0)
    conn.execute('PRAGMA busy_timeout=600000')
    valid_schools = load_existing_school_ids()
    # 投入直前の最終 dedup (DB 由来 prefix と完全照合)
    db_prefixes = load_existing_quote_prefixes()
    inserted = 0
    rejected = 0
    batch = 0
    for r in records:
        if r['school_id'] not in valid_schools:
            rejected += 1
            continue
        if not r.get('quote_text') or not r.get('source_url'):
            rejected += 1
            continue
        if len(r['quote_text']) < 30 or len(r['quote_text']) > 400:
            rejected += 1
            continue
        pk = prefix_key(r['quote_text'])
        if pk in db_prefixes:
            rejected += 1
            continue
        try:
            conn.execute(
                """INSERT INTO testimonials_v2
                (school_id, speaker_role, speaker_attribute, quote_text,
                 quote_summary, context, source_type, source_url,
                 rights_level, retrieved_at, ethics_review_status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    r['school_id'], r['speaker_role'],
                    r.get('speaker_attribute', ''),
                    r['quote_text'], r.get('quote_summary', ''),
                    r.get('context', ''),
                    'school_website', r['source_url'],
                    r.get('rights_level', 'quoted_with_attribution'),
                    datetime.now().isoformat(), 'qm1_passed',
                ),
            )
            inserted += 1
            db_prefixes.add(pk)
            batch += 1
            if batch >= 100:
                conn.commit()
                batch = 0
        except sqlite3.OperationalError:
            rejected += 1
    conn.commit()
    conn.close()
    return inserted, rejected


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)

    url_map, url_fb = load_url_map()
    seen_keys: set[str] = load_existing_quote_prefixes()
    print(f"[Group C] DB-existing quote prefixes: {len(seen_keys)}")

    school_dirs = sorted(
        d for d in CACHE.iterdir()
        if d.is_dir() and d.name.startswith('jpms_s_')
    )
    print(f"[Group C] schools in cache: {len(school_dirs)}")

    all_items: list[dict] = []
    per_group_counts: dict[str, int] = {g: 0 for g in PAGE_GROUPS}
    schools_with_quote = 0

    for sd in school_dirs:
        items = process_school(sd, url_map, url_fb, seen_keys)
        if items:
            schools_with_quote += 1
            for r in items:
                per_group_counts[r['group_id']] = per_group_counts.get(
                    r['group_id'], 0) + 1
        all_items.extend(items)

    # JSONL 出力
    with OUT.open('w', encoding='utf-8') as f:
        for r in all_items:
            out = {k: v for k, v in r.items() if k != 'group_id'}
            out['group_id'] = r['group_id']
            f.write(json.dumps(out, ensure_ascii=False) + '\n')

    # DB 投入
    inserted, rejected = insert_into_db(all_items)

    progress = {
        'task_id': 'group_c',
        'schools_in_cache': len(school_dirs),
        'schools_with_quote': schools_with_quote,
        'total_items_extracted': len(all_items),
        'per_group': per_group_counts,
        'db_inserted': inserted,
        'db_rejected': rejected,
        'output_jsonl': str(OUT),
        'ts': datetime.now().isoformat() + 'Z',
    }
    with PROGRESS.open('w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"[Group C] schools with quote : {schools_with_quote}")
    print(f"[Group C] total items        : {len(all_items)}")
    for g in ('C01', 'C02', 'C03', 'C04', 'C05'):
        print(f"  {g}: {per_group_counts.get(g, 0)}")
    print(f"[Group C] DB inserted        : {inserted}")
    print(f"[Group C] DB rejected        : {rejected}")
    print(f"[Group C] JSONL              : {OUT}")
    print(f"[Group C] PROGRESS           : {PROGRESS}")


if __name__ == '__main__':
    main()
