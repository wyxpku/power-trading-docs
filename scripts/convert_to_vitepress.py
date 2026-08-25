#!/usr/bin/env python3
"""Convert PaddleOCR-VL output to VitePress Markdown files.

Reads:
  - book/scripts/paddleocr_output/chapter_mapping.json
  - book/scripts/paddleocr_output/page_XXXX/*.json

Writes:
  - book-vitepress/preface.md
  - book-vitepress/chXX.md (31 chapters)
  - book-vitepress/appendix-a.md, appendix-b.md
"""
import html as html_mod
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"
VITEPRESS_DIR = REPO_ROOT / "book-vitepress"
MAPPING_PATH = OUTPUT_DIR / "chapter_mapping.json"

BOOK_PAGE_OFFSET = 17
FIRST_CHAPTER_PDF_PAGE = 19


def load_page_json(page_idx: int) -> Optional[Dict]:
    page_dir = OUTPUT_DIR / f"page_{page_idx:04d}"
    json_files = list(page_dir.glob("*.json"))
    if not json_files:
        return None
    with open(json_files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def detect_heading_level(text: str) -> str:
    text = text.strip()
    if not text:
        return "##"
    if re.match(r'^第\d+章\s', text):
        return '#'
    if re.match(r'^第[一二三四五六七八九十]+篇\s', text):
        return '#'
    if re.match(r'^附录[A-Z]\s', text):
        return '#'
    if text in ('前言', '序', '序言', '前言与序言'):
        return '#'
    if re.match(r'^\d+\.\d+\.\d+\.\d+', text):
        return '####'
    if re.match(r'^\d+\.\d+\.\d+', text):
        return '###'
    if re.match(r'^\d+\.\d+\s', text):
        return '##'
    return '##'


def block_to_markdown(block: Dict[str, Any], pdf_page: int) -> Optional[str]:
    """Convert a single OCR block to Markdown."""
    label = block.get("block_label", "")
    content = str(block.get("block_content", "")).strip()

    # Skip running headers, footers, page numbers
    if label in ("header", "header_image", "footer", "footer_image", "number"):
        return None

    # Skip empty blocks (unless image with crop)
    if not content and label != "image":
        return None

    # doc_title / paragraph_title → Markdown heading
    if label in ("doc_title", "paragraph_title"):
        level = detect_heading_level(content)
        return f'{level} {content}'

    # Text → paragraph
    if label == "text":
        paragraphs = re.split(r'\n\s*\n', content)
        parts = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para = re.sub(r'\n', ' ', para)
            parts.append(para)
        return '\n\n'.join(parts)

    # Table → raw HTML (VitePress supports inline HTML in Markdown)
    if label == "table":
        if content.startswith('<'):
            return f'<div class="table-container">\n\n{content}\n\n</div>'
        return f'```\n{content}\n```'

    # Image → Markdown image with crop path
    if label == "image":
        crop_path = block.get("crop_path", "")
        fig_idx = block.get("figure_index", 0)
        if not crop_path:
            crop_path = f"pages/crops/page_{pdf_page:03d}_fig{fig_idx}.png"
        caption = f"图 page {pdf_page} fig {fig_idx}"
        return f'![{caption}](/{crop_path})'

    # Figure title → italic caption
    if label == "figure_title":
        return f'*{content}*'

    # Fallback
    if content:
        return content
    return None


def page_divider_markdown(pdf_page: int) -> str:
    if pdf_page >= FIRST_CHAPTER_PDF_PAGE:
        book_page = pdf_page - BOOK_PAGE_OFFSET
        badge = f"PDF 第 {pdf_page} 页 / 书第 {book_page} 页"
    else:
        badge = f"PDF 第 {pdf_page} 页"
    return (
        f'<PageDivider pdf-page="{pdf_page}" />'
        f'\n\n<!-- PAGE {badge} -->'
    )


def convert_chapter(chapter: Dict) -> str:
    """Convert a chapter's pages to Markdown string."""
    start_idx = chapter["start_page_idx"]
    end_idx = chapter["end_page_idx"]
    title = chapter["title"]

    parts: List[str] = []

    for page_idx in range(start_idx, end_idx + 1):
        data = load_page_json(page_idx)
        if data is None:
            continue
        blocks = data.get("parsing_res_list", [])
        pdf_page = page_idx + 1

        # Page divider
        parts.append(page_divider_markdown(pdf_page))

        # Block content
        for block in blocks:
            md = block_to_markdown(block, pdf_page)
            if md:
                parts.append(md)

    return '\n\n'.join(parts)


def get_chapter_file_info(chapter: Dict) -> tuple:
    """Return (output_path, frontmatter_title) for a chapter."""
    html_file = chapter["html_file"]
    title = chapter["title"]

    if html_file == "preface.html":
        return (VITEPRESS_DIR / "preface.md", title)
    elif html_file.startswith("chapter_"):
        num = html_file.replace("chapter_", "").replace(".html", "")
        return (VITEPRESS_DIR / f"ch{num}.md", title)
    elif html_file == "appendix_a.html":
        return (VITEPRESS_DIR / "appendix-a.md", title)
    elif html_file == "appendix_b.html":
        return (VITEPRESS_DIR / "appendix-b.md", title)
    else:
        return (VITEPRESS_DIR / html_file.replace(".html", ".md"), title)


def main():
    if not MAPPING_PATH.exists():
        print(f"ERROR: {MAPPING_PATH} not found. Run detect_chapters.py first.")
        return

    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    print(f"Converting {len(mapping)} chapters to VitePress Markdown...")

    for chapter in mapping:
        output_path, title = get_chapter_file_info(chapter)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = convert_chapter(chapter)

        # Write with frontmatter
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"---\ntitle: {title}\n---\n\n")
            f.write(content)
            f.write("\n")

        pages = chapter["end_page_idx"] - chapter["start_page_idx"] + 1
        rel_path = str(output_path.relative_to(VITEPRESS_DIR))
        print(f"  {rel_path:30s}  {pages:2d} pages  {len(content):>7,} chars")

    print(f"\nDone! {len(mapping)} Markdown files in {VITEPRESS_DIR}")


if __name__ == "__main__":
    main()
