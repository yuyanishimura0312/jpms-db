#!/usr/bin/env python3
"""12校レポートHTML統合ビルダー"""
from pathlib import Path
import re

ROOT = Path("/Users/nishimura+/projects/research/jpms-db")
REPORTS = ROOT / "reports"

# 表示順（聖光が第一志望のため概要直後に配置）
# 確定検討10校（聖光・栄光・浅野＝神奈川男子御三家を先に、その後カトリック→東京有名校→灘）
# 候補2校（東京農大第一・渋渋）は結語の前に
ARTICLE_ORDER = [
    ("overview", "概要編"),
    ("seiko", "聖光学院（第一志望）"),
    ("eiko", "栄光学園"),
    ("asano", "浅野"),
    ("salesio", "サレジオ学院"),
    ("kaijo", "海城"),
    ("keio", "慶應義塾中等部"),
    ("azabu", "麻布"),
    ("komaba", "駒場東邦"),
    ("kaisei", "開成"),
    ("nada", "灘"),
    ("nodai", "東京農大第一（候補）"),
    ("shibushibu", "渋谷教育学園渋谷（候補）"),
    ("conclusion", "結語"),
]

def read_section(key):
    p = REPORTS / f"article_{key}.html"
    if not p.exists():
        return f"<!-- missing: {key} -->"
    text = p.read_text(encoding="utf-8")
    # <section>～</section>を抽出（greedy版で sub-section 含む全体取得）
    m = re.search(r"<section[^>]*>.*</section>", text, re.DOTALL)
    if m:
        return m.group(0)
    # sectionタグがない場合は本文丸ごと
    return text

# 各記事を読み込み
sections_html = []
toc_items = []
for key, label in ARTICLE_ORDER:
    section = read_section(key)
    sections_html.append(section)
    # idを抽出
    m = re.search(r'<section[^>]*id="([^"]+)"', section)
    sec_id = m.group(1) if m else key
    toc_items.append((sec_id, label))

content = "\n\n".join(sections_html)
toc_html = "\n".join([
    f'<li><a href="#{sid}">{label}</a></li>'
    for sid, label in toc_items
])

# ベースHTML
html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>サンプル12校レポート（拡張版） | JPMS-DB</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700;900&family=Noto+Serif+JP:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root{{
    --akashiro-red:#CC1400;
    --akashiro-red-light:#E63D2C;
    --bg:#FFFFFF;
    --ink:#0E0E0E;
    --ink-soft:#3A3A3A;
    --line:#E5E5E5;
    --bg-soft:#FAFAFA;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{
    font-family:'Noto Serif JP',serif;
    background:var(--bg);
    color:var(--ink);
    line-height:1.95;
    font-size:15.5px;
    font-weight:400;
  }}
  header{{
    border-bottom:3px solid var(--akashiro-red);
    padding:36px 56px 24px;
    background:var(--bg);
  }}
  .brand{{display:flex;align-items:baseline;gap:18px;font-family:'Noto Sans JP',sans-serif}}
  .brand h1{{
    font-family:'Noto Serif JP',serif;
    font-size:24px;font-weight:700;letter-spacing:0.05em;
    color:var(--akashiro-red);
  }}
  .brand .sub{{font-size:13px;color:var(--ink-soft);font-weight:400}}
  nav{{margin-top:14px;font-family:'Noto Sans JP',sans-serif;font-size:13px}}
  nav a{{color:var(--ink-soft);text-decoration:none;margin-right:24px}}
  nav a:hover{{color:var(--akashiro-red)}}
  main{{max-width:880px;margin:0 auto;padding:48px 56px 100px}}

  .doc-meta{{
    font-family:'Noto Sans JP',sans-serif;
    font-size:12px;color:var(--ink-soft);
    border-bottom:1px solid var(--line);
    padding-bottom:16px;margin-bottom:48px;
    letter-spacing:0.05em;
  }}
  h1.title{{
    font-size:38px;font-weight:700;line-height:1.45;
    margin-bottom:16px;letter-spacing:0.02em;
  }}
  .subtitle{{
    font-size:18px;color:var(--akashiro-red);font-weight:400;
    margin-bottom:32px;font-family:'Noto Sans JP',sans-serif;
  }}
  .lead{{
    font-size:16px;line-height:2.05;
    margin-bottom:48px;color:var(--ink);
  }}

  .school-section{{
    margin:64px 0 80px;padding-bottom:32px;
    border-bottom:1px dashed var(--line);
  }}
  .school-section.eiko-major{{
    background:#FFFAF6;
    padding:32px 28px;
    border:2px solid var(--akashiro-red);
    border-radius:2px;
    margin:80px 0;
  }}
  h2{{
    font-size:26px;font-weight:700;margin:0 0 28px;
    padding:14px 0 14px 22px;
    border-left:6px solid var(--akashiro-red);
    line-height:1.5;
  }}
  h2 .num{{
    color:var(--akashiro-red);font-size:13px;
    display:block;letter-spacing:0.15em;
    font-family:'Noto Sans JP',sans-serif;font-weight:500;
    margin-bottom:6px;
  }}
  h3{{
    font-size:17px;font-weight:700;margin:36px 0 14px;
    color:var(--akashiro-red-light);
    font-family:'Noto Sans JP',sans-serif;letter-spacing:0.03em;
  }}
  p{{margin-bottom:18px;text-align:justify}}

  .meta-table{{
    width:100%;border-collapse:collapse;
    font-family:'Noto Sans JP',sans-serif;font-size:13px;
    margin:16px 0 32px;
  }}
  .meta-table th,.meta-table td{{
    padding:9px 14px;text-align:left;
    border-bottom:1px solid var(--line);
    vertical-align:top;
  }}
  .meta-table th{{
    background:var(--bg-soft);color:var(--akashiro-red);
    font-weight:500;width:130px;font-size:12px;
    letter-spacing:0.05em;
  }}
  blockquote{{
    border-left:3px solid var(--akashiro-red);
    padding:14px 22px;margin:20px 0;
    background:var(--bg-soft);
    font-size:14.5px;color:var(--ink);
    font-style:normal;
  }}
  blockquote .who{{
    display:block;font-style:normal;font-size:11px;
    color:var(--akashiro-red);margin-top:10px;
    letter-spacing:0.05em;font-family:'Noto Sans JP',sans-serif;
  }}

  .compare-table{{
    width:100%;border-collapse:collapse;font-size:12.5px;
    font-family:'Noto Sans JP',sans-serif;
    margin:24px 0;
  }}
  .compare-table th{{
    background:var(--akashiro-red);color:#fff;
    padding:10px 8px;text-align:left;font-weight:500;
    font-size:11px;letter-spacing:0.05em;
  }}
  .compare-table td{{
    padding:8px;border-bottom:1px solid var(--line);
    vertical-align:top;
  }}
  .compare-table tr:nth-child(even){{background:var(--bg-soft)}}

  .academic-link{{
    display:inline-block;background:#FFF4F0;
    border:1px solid var(--akashiro-red);
    padding:2px 8px;font-size:11px;color:var(--akashiro-red);
    margin-right:6px;font-family:'Noto Sans JP',sans-serif;
    border-radius:2px;letter-spacing:0.02em;
  }}
  .summary-box{{
    margin:48px 0;padding:32px;
    border:2px solid var(--akashiro-red);
    background:var(--bg-soft);
  }}
  .summary-box h3{{
    color:var(--akashiro-red);margin-top:0;font-size:18px;
  }}
  footer{{
    border-top:1px solid var(--line);
    padding:32px 56px;text-align:center;
    color:var(--ink-soft);font-size:12px;
    font-family:'Noto Sans JP',sans-serif;
  }}
  .toc{{
    background:var(--bg-soft);
    padding:28px 36px;margin-bottom:48px;
    font-family:'Noto Sans JP',sans-serif;font-size:13.5px;
    border-left:4px solid var(--akashiro-red);
  }}
  .toc h3{{margin-top:0;color:var(--akashiro-red)}}
  .toc ol{{padding-left:22px;line-height:2;column-count:2;column-gap:32px}}
  .toc a{{color:var(--ink);text-decoration:none}}
  .toc a:hover{{color:var(--akashiro-red)}}

  .top-link{{
    position:fixed;bottom:24px;right:24px;
    background:var(--akashiro-red);color:#fff;
    padding:10px 16px;font-size:12px;
    text-decoration:none;
    font-family:'Noto Sans JP',sans-serif;
    box-shadow:0 2px 8px rgba(0,0,0,0.15);
  }}

  @media(max-width:680px){{
    main{{padding:32px 20px 80px}}
    h1.title{{font-size:28px}}
    h2{{font-size:21px}}
    .toc ol{{column-count:1}}
    .toc{{padding:18px}}
  }}
</style>
</head>
<body id="top">
<header>
  <div class="brand">
    <h1>JPMS-DB</h1>
    <span class="sub">日本私立中学校 包括的基盤データベース</span>
  </div>
  <nav>
    <a href="./">ダッシュボード</a>
    <a href="./sample-12-schools.html">サンプル12校レポート（拡張版）</a>
  </nav>
</header>

<main>
  <div class="doc-meta">REPORT — 2026年5月5日 | JPMS-DB拡張版 | SAPIX主催学校説明会対象12校 | 約9万字</div>

  <h1 class="title">最難関12校から読み解く<br>私立中学校という選択</h1>
  <p class="subtitle">SAPIX主催学校説明会2026・5月～6月 訪問予定校の関係者発言から見える教育設計</p>

  <p class="lead">
    本稿は、2026年5月から6月にかけてSAPIX主催で開催される学校説明会のうち、首都圏・関西の最難関校12校（サレジオ学院・海城・慶應義塾中等部・浅野・麻布・駒場東邦・開成・栄光学園・聖光学院・東京農業大学第一・渋谷教育学園渋谷・灘）について、JPMS-DBが収集した約280件の関係者発言を立場・感情分布まで明示した上で、保護者の判断材料として整理した拡張レポートです。各校をランキングで比較するのではなく、ポジティブな声とネガティブな声を等しく取り上げ、お子さんとご家庭の価値観に照らして「合うかどうか」を考える素材を提供します。
  </p>

  <div class="toc">
    <h3>目次</h3>
    <ol>
      {toc_html}
    </ol>
  </div>

  {content}

</main>

<a href="#top" class="top-link">↑ 先頭へ</a>

<footer>
  JPMS-DB v0.2 | 日本私立中学校 包括的基盤データベース | Sample 12 Schools Extended Report | 2026-05-05<br>
  約9万字 / 関係者発言280件超 / 出典はWeb公開情報のみ・口コミは傾向集約のみ・未成年情報は匿名化
</footer>
</body>
</html>
"""

out = REPORTS.parent / "docs" / "sample-12-schools.html"
out.write_text(html, encoding="utf-8")
print(f"Written: {out}")
print(f"Size: {len(html):,} chars")

# dashboards にもコピー
out2 = REPORTS.parent / "dashboards" / "sample-12-schools.html"
out2.write_text(html, encoding="utf-8")
print(f"Written: {out2}")
