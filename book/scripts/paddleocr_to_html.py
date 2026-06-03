#!/usr/bin/env python3
"""Convert PaddleOCR-VL output to the HTML book reader format.

Reads:
  - book/scripts/paddleocr_output/chapter_mapping.json
  - book/scripts/paddleocr_output/page_XXXX/*.json (per-page OCR results)

Writes:
  - book/preface.html
  - book/chapter_01.html through chapter_31.html
  - book/appendix_a.html, appendix_b.html

The generated HTML matches the existing book reader layout:
  - Sidebar with TOC navigation (active link per chapter)
  - Split view: text panel (OCR content) + scan panel (page images)
  - Theme selector (light/cream/dark)
  - IntersectionObserver for scroll-synced page image updates
  - book-navigation.js for heading anchors and section nav

Adapted to actual PaddleOCR-VL-1.6 output format:
  - block_label "doc_title" for chapter titles
  - block_label "paragraph_title" for section headings
  - block_label "text" for paragraphs
  - block_label "image" for figures
  - block_label "figure_title" for figure captions
  - block_label "table" for tables (content is HTML <table>)
  - block_label "header"/"header_image"/"number" are skipped (running headers/footers)
"""
import html as html_mod
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"
BOOK_DIR = REPO_ROOT / "book"
MAPPING_PATH = OUTPUT_DIR / "chapter_mapping.json"

# Page numbering: PDF page 19 = book page 2 → book_page = pdf_page - 17
BOOK_PAGE_OFFSET = 17
FIRST_CHAPTER_PDF_PAGE = 19


# ─── Sidebar Template ────────────────────────────────────────────────────────

TOC_GROUPS = [
    ("序篇", [("前言与序言", "preface.html")]),
    ("第一篇 理论篇", [
        ("第1章 电力市场概述", "chapter_01.html"),
        ("第2章 电力现货市场组织", "chapter_02.html"),
        ("第3章 电力现货市场价格机制", "chapter_03.html"),
        ("第4章 电力现货市场阻塞管理", "chapter_04.html"),
        ("第5章 电力市场信息披露与风险管控", "chapter_05.html"),
        ("第6章 电力现货市场绩效评价", "chapter_06.html"),
    ]),
    ("第二篇 国外实践篇", [
        ("第7章 美国 PJM 电力市场", "chapter_07.html"),
        ("第8章 美国 ERCOT 电力市场", "chapter_08.html"),
        ("第9章 英国 电力市场", "chapter_09.html"),
        ("第10章 欧洲统一电力市场", "chapter_10.html"),
        ("第11章 澳大利亚电力市场", "chapter_11.html"),
        ("第12章 巴西电力市场", "chapter_12.html"),
    ]),
    ("第三篇 国内实践篇", [
        ("第13章 我国电力现货市场的演进", "chapter_13.html"),
        ("第14章 省间电力现货市场", "chapter_14.html"),
        ("第15章 浙江电力现货市场", "chapter_15.html"),
        ("第16章 山西电力现货市场", "chapter_16.html"),
        ("第17章 山东电力现货市场", "chapter_17.html"),
        ("第18章 福建电力现货市场", "chapter_18.html"),
        ("第19章 四川电力现货市场", "chapter_19.html"),
        ("第20章 甘肃电力现货市场", "chapter_20.html"),
    ]),
    ("第四篇 技术支持系统篇", [
        ("第21章 电力现货市场技术支持系统总体概况", "chapter_21.html"),
        ("第22章 现货及辅助服务市场申报发布", "chapter_22.html"),
        ("第23章 电力现货市场出清", "chapter_23.html"),
        ("第24章 辅助服务市场出清", "chapter_24.html"),
        ("第25章 安全校核", "chapter_25.html"),
        ("第26章 市场分析", "chapter_26.html"),
        ("第27章 电力市场结算", "chapter_27.html"),
        ("第28章 模拟仿真", "chapter_28.html"),
        ("第29章 系统运维管理", "chapter_29.html"),
        ("第30章 安全防护", "chapter_30.html"),
    ]),
    ("第五篇 展望篇", [
        ("第31章 \"双碳\"目标和新型电力系统下的电力市场展望", "chapter_31.html"),
    ]),
    ("附录", [
        ("附录A 电力现货市场规则框架示例", "appendix_a.html"),
        ("附录B 电力现货市场导则范本", "appendix_b.html"),
    ]),
]


def build_sidebar(active_href: str) -> str:
    """Generate sidebar HTML with active chapter highlighted."""
    groups = []
    for group_title, entries in TOC_GROUPS:
        items = []
        for title, href in entries:
            active = ' class="toc-link active"' if href == active_href else ' class="toc-link "'
            items.append(f'        <li class="toc-item"><a{active} href="{href}">{title}</a></li>')
        items_str = "\n".join(items)
        groups.append(
            f'    <div class="toc-group">\n'
            f'      <div class="toc-group-title">{group_title}</div>\n'
            f'      <ul class="toc-list">\n'
            f'{items_str}\n'
            f'      </ul>\n'
            f'    </div>'
        )
    return (
        '<aside id="sidebar">\n'
        '  <div class="sidebar-header">\n'
        '    <h2>电力现货市场实务</h2>\n'
        '    <p>国家电力调度控制中心 组编</p>\n'
        '  </div>\n'
        f'  <nav class="toc-nav">\n'
        + "\n".join(groups) + "\n"
        + '  </nav>\n'
        '</aside>'
    )


# ─── Block → HTML Conversion ─────────────────────────────────────────────────

def detect_heading_level(text: str) -> Optional[str]:
    """Infer heading level from Chinese technical book patterns."""
    text = text.strip()
    if not text:
        return None
    # Chapter / part / appendix titles → h1
    if re.match(r'^第\d+章\s', text):
        return 'h1'
    if re.match(r'^第[一二三四五六七八九十]+篇\s', text):
        return 'h1'
    if re.match(r'^附录[A-Z]\s', text):
        return 'h1'
    if text in ('前言', '序', '序言', '前言与序言', '目　录', '目录'):
        return 'h1'
    # Section headings based on numbering patterns
    if re.match(r'^\d+\.\d+\.\d+\.\d+', text):
        return 'h4'
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 'h3'
    if re.match(r'^\d+\.\d+\s', text):
        return 'h2'
    return None


def block_to_html(block: Dict[str, Any], pdf_page: int) -> Optional[str]:
    """Convert a single PaddleOCR-VL block to an HTML string."""
    label = block.get("block_label", "")
    content = str(block.get("block_content", "")).strip()

    # Skip running headers, footers, page numbers, header images
    if label in ("header", "header_image", "footer", "footer_image", "number"):
        return None

    # Empty content (skip unless it's an image with a crop)
    if not content and label != "image":
        return None

    # ── doc_title blocks (chapter titles) ────────────────────────────
    if label == "doc_title":
        level = detect_heading_level(content) or "h1"
        return f'\t<{level}>{html_mod.escape(content)}</{level}>'

    # ── paragraph_title blocks (section headings) ────────────────────
    if label == "paragraph_title":
        level = detect_heading_level(content) or "h2"
        return f'\t<{level}>{html_mod.escape(content)}</{level}>'

    # ── Text blocks ──────────────────────────────────────────────────
    if label == "text":
        # Split on double newlines for paragraph breaks
        paragraphs = re.split(r'\n\s*\n', content)
        parts = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para = re.sub(r'\n', ' ', para)
            parts.append(f'\t<p>{html_mod.escape(para)}</p>')
        return '\n'.join(parts)

    # ── Table blocks ─────────────────────────────────────────────────
    if label == "table":
        if content.startswith('<'):
            # Already HTML — use as-is
            return f'\t<div class="table-container">{content}</div>'
        # Fallback: preformatted text
        return f'\t<pre>{html_mod.escape(content)}</pre>'

    # ── Figure/Image blocks ──────────────────────────────────────────
    if label == "image":
        crop_path = block.get("crop_path", "")
        fig_idx = block.get("figure_index", 0)
        if not crop_path:
            crop_name = f"page_{pdf_page:03d}_fig{fig_idx}.png"
            crop_path = f"pages/crops/{crop_name}"

        caption = f"图 page {pdf_page} fig {fig_idx}"
        escaped_caption = html_mod.escape(caption)
        return (
            f'\t<figure class="embedded-figure">\n'
            f'\t  <img src="{crop_path}" alt="{escaped_caption}">\n'
            f'\t  <figcaption>{escaped_caption}</figcaption>\n'
            f'\t</figure>'
        )

    # ── Figure caption (standalone) ──────────────────────────────────
    if label == "figure_title":
        return f'\t<p><em>{html_mod.escape(content)}</em></p>'

    # ── Unknown block → text fallback ────────────────────────────────
    if content:
        return f'\t<p>{html_mod.escape(content)}</p>'
    return None


# ─── Page HTML Generation ────────────────────────────────────────────────────

def page_divider_html(pdf_page: int) -> str:
    if pdf_page >= FIRST_CHAPTER_PDF_PAGE:
        book_page = pdf_page - BOOK_PAGE_OFFSET
        badge = f"PDF 第 {pdf_page} 页 / 书第 {book_page} 页"
    else:
        badge = f"PDF 第 {pdf_page} 页"
    return (
        f'<div class="page-divider" id="page-div-{pdf_page}" data-page="{pdf_page}">\n'
        f'  <span class="page-number-badge">{badge}</span>\n'
        f'</div>'
    )


def page_content_html(page_idx: int, blocks: List[Dict]) -> str:
    """Generate HTML for all blocks on one page."""
    pdf_page = page_idx + 1  # 0-indexed → 1-indexed
    parts = [page_divider_html(pdf_page)]
    parts.append(f'<div class="page-body-container" id="page-content-{pdf_page}">')

    for block in blocks:
        block_html = block_to_html(block, pdf_page)
        if block_html:
            parts.append(block_html)

    parts.append('\t</div>')
    return '\n'.join(parts)


# ─── Full Page Template ──────────────────────────────────────────────────────

INLINE_JS = r"""
    function setTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.innerText === (theme === 'light' ? '明亮' : theme === 'cream' ? '护眼' : '深色')) {
          btn.classList.add('active');
        }
      });
      localStorage.setItem('reader-theme', theme);
    }

    function setViewMode(mode) {
      const body = document.body;
      const btnText = document.getElementById('btn-text-only');
      const btnSplit = document.getElementById('btn-split');
      if (mode === 'text') {
        body.classList.remove('split-view');
        btnText.classList.add('active');
        btnSplit.classList.remove('active');
      } else {
        body.classList.add('split-view');
        btnText.classList.remove('active');
        btnSplit.classList.add('active');
      }
      localStorage.setItem('reader-view', mode);
    }

    const textPanel = document.getElementById('text-panel');
    const scanImg = document.getElementById('original-scan-img');
    const pageDividers = document.querySelectorAll('.page-divider');
    const observerOptions = {
      root: textPanel,
      rootMargin: '-50px 0px -50% 0px',
      threshold: 0
    };
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const page = entry.target.getAttribute('data-page');
          const pageStr = String(page).padStart(3, '0');
          scanImg.src = 'pages/page_' + pageStr + '.png';
        }
      });
    }, observerOptions);
    pageDividers.forEach(div => observer.observe(div));

    window.addEventListener('DOMContentLoaded', () => {
      const savedTheme = localStorage.getItem('reader-theme') || 'light';
      setTheme(savedTheme);
      const savedView = localStorage.getItem('reader-view') || 'split';
      setViewMode(savedView);
    });
"""


def full_page_html(title: str, active_href: str, content_html: str,
                   first_pdf_page: int) -> str:
    """Wrap content in the full HTML page template."""
    sidebar = build_sidebar(active_href)
    escaped_title = html_mod.escape(title)
    return f'''<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escaped_title} - 《电力现货市场实务》</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body class="split-view">
  <div id="app-container">
    {sidebar}

    <main id="content-wrapper">
      <header id="topbar">
        <div class="controls-left">
          <h1>{escaped_title}</h1>
        </div>
        <div class="controls-right">
          <div class="theme-selector">
            <button class="theme-btn active" onclick="setTheme('light')">明亮</button>
            <button class="theme-btn" onclick="setTheme('cream')">护眼</button>
            <button class="theme-btn" onclick="setTheme('dark')">深色</button>
          </div>
          <div class="view-selector">
            <button class="view-btn" id="btn-text-only" onclick="setViewMode('text')">纯文本</button>
            <button class="view-btn active" id="btn-split" onclick="setViewMode('split')">对照扫描件</button>
          </div>
        </div>
      </header>

      <div id="reader-container">
        <div class="panel" id="text-panel">
          <article class="reading-content">
{content_html}
          </article>
        </div>

        <div class="panel" id="original-panel">
          <img id="original-scan-img" src="pages/page_{first_pdf_page:03d}.png" alt="扫描件">
        </div>
      </div>
    </main>
  </div>

  <script>
{INLINE_JS}
  </script>
<script src="js/book-navigation.js"></script>
</body>
</html>'''


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def load_page_json(page_idx: int) -> Optional[Dict]:
    page_dir = OUTPUT_DIR / f"page_{page_idx:04d}"
    json_files = list(page_dir.glob("*.json"))
    if not json_files:
        return None
    with open(json_files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if not MAPPING_PATH.exists():
        print(f"ERROR: {MAPPING_PATH} not found. Run detect_chapters.py first.")
        return

    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    print(f"Generating {len(mapping)} HTML files...")

    for chapter in mapping:
        html_file = chapter["html_file"]
        title = chapter["title"]
        start_idx = chapter["start_page_idx"]
        end_idx = chapter["end_page_idx"]

        # Collect HTML for all pages in this chapter
        page_htmls: List[str] = []
        for page_idx in range(start_idx, end_idx + 1):
            data = load_page_json(page_idx)
            if data is None:
                continue
            blocks = data.get("parsing_res_list", [])
            page_html = page_content_html(page_idx, blocks)
            page_htmls.append(page_html)

        if not page_htmls:
            print(f"  SKIP {html_file}: no page data")
            continue

        content_html = '\n'.join(page_htmls)
        first_pdf_page = start_idx + 1

        full_html = full_page_html(title, html_file, content_html, first_pdf_page)

        output_path = BOOK_DIR / html_file
        output_path.write_text(full_html, encoding="utf-8")

        pages = end_idx - start_idx + 1
        print(f"  {html_file:20s}  {pages:2d} pages  {len(full_html):>8,} chars")

    print(f"\nDone! {len(mapping)} HTML files in {BOOK_DIR}")


if __name__ == "__main__":
    main()
