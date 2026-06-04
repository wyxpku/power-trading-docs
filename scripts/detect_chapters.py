#!/usr/bin/env python3
"""Detect chapter boundaries from PaddleOCR-VL output.

Scans all page JSON results for doc_title and header blocks matching
known chapter patterns. Outputs chapter_mapping.json with page ranges.

Adapted to actual PaddleOCR-VL-1.6 output format:
  - Chapter title pages have 'doc_title' blocks
  - Running headers repeat '第N章 ...' on every page
  - Bbox format: [x1, y1, x2, y2]
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"

# Known chapter structure (from book/index.html TOC)
CHAPTERS = [
    {"id": "ch01", "pattern": r"第\s*1\s*章", "html": "chapter_01.html",
     "title": "第1章 电力市场概述", "group": "第一篇 理论篇"},
    {"id": "ch02", "pattern": r"第\s*2\s*章", "html": "chapter_02.html",
     "title": "第2章 电力现货市场组织", "group": "第一篇 理论篇"},
    {"id": "ch03", "pattern": r"第\s*3\s*章", "html": "chapter_03.html",
     "title": "第3章 电力现货市场价格机制", "group": "第一篇 理论篇"},
    {"id": "ch04", "pattern": r"第\s*4\s*章", "html": "chapter_04.html",
     "title": "第4章 电力现货市场阻塞管理", "group": "第一篇 理论篇"},
    {"id": "ch05", "pattern": r"第\s*5\s*章", "html": "chapter_05.html",
     "title": "第5章 电力市场信息披露与风险管控", "group": "第一篇 理论篇"},
    {"id": "ch06", "pattern": r"第\s*6\s*章", "html": "chapter_06.html",
     "title": "第6章 电力现货市场绩效评价", "group": "第一篇 理论篇"},
    {"id": "ch07", "pattern": r"第\s*7\s*章", "html": "chapter_07.html",
     "title": "第7章 美国 PJM 电力市场", "group": "第二篇 国外实践篇"},
    {"id": "ch08", "pattern": r"第\s*8\s*章", "html": "chapter_08.html",
     "title": "第8章 美国 ERCOT 电力市场", "group": "第二篇 国外实践篇"},
    {"id": "ch09", "pattern": r"第\s*9\s*章", "html": "chapter_09.html",
     "title": "第9章 英国 电力市场", "group": "第二篇 国外实践篇"},
    {"id": "ch10", "pattern": r"第\s*10\s*章", "html": "chapter_10.html",
     "title": "第10章 欧洲统一电力市场", "group": "第二篇 国外实践篇"},
    {"id": "ch11", "pattern": r"第\s*11\s*章", "html": "chapter_11.html",
     "title": "第11章 澳大利亚电力市场", "group": "第二篇 国外实践篇"},
    {"id": "ch12", "pattern": r"第\s*12\s*章", "html": "chapter_12.html",
     "title": "第12章 巴西电力市场", "group": "第二篇 国外实践篇"},
    {"id": "ch13", "pattern": r"第\s*13\s*章", "html": "chapter_13.html",
     "title": "第13章 我国电力现货市场的演进", "group": "第三篇 国内实践篇"},
    {"id": "ch14", "pattern": r"第\s*14\s*章", "html": "chapter_14.html",
     "title": "第14章 省间电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch15", "pattern": r"第\s*15\s*章", "html": "chapter_15.html",
     "title": "第15章 浙江电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch16", "pattern": r"第\s*16\s*章", "html": "chapter_16.html",
     "title": "第16章 山西电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch17", "pattern": r"第\s*17\s*章", "html": "chapter_17.html",
     "title": "第17章 山东电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch18", "pattern": r"第\s*18\s*章", "html": "chapter_18.html",
     "title": "第18章 福建电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch19", "pattern": r"第\s*19\s*章", "html": "chapter_19.html",
     "title": "第19章 四川电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch20", "pattern": r"第\s*20\s*章", "html": "chapter_20.html",
     "title": "第20章 甘肃电力现货市场", "group": "第三篇 国内实践篇"},
    {"id": "ch21", "pattern": r"第\s*21\s*章", "html": "chapter_21.html",
     "title": "第21章 电力现货市场技术支持系统总体概况", "group": "第四篇 技术支持系统篇"},
    {"id": "ch22", "pattern": r"第\s*22\s*章", "html": "chapter_22.html",
     "title": "第22章 现货及辅助服务市场申报发布", "group": "第四篇 技术支持系统篇"},
    {"id": "ch23", "pattern": r"第\s*23\s*章", "html": "chapter_23.html",
     "title": "第23章 电力现货市场出清", "group": "第四篇 技术支持系统篇"},
    {"id": "ch24", "pattern": r"第\s*24\s*章", "html": "chapter_24.html",
     "title": "第24章 辅助服务市场出清", "group": "第四篇 技术支持系统篇"},
    {"id": "ch25", "pattern": r"第\s*25\s*章", "html": "chapter_25.html",
     "title": "第25章 安全校核", "group": "第四篇 技术支持系统篇"},
    {"id": "ch26", "pattern": r"第\s*26\s*章", "html": "chapter_26.html",
     "title": "第26章 市场分析", "group": "第四篇 技术支持系统篇"},
    {"id": "ch27", "pattern": r"第\s*27\s*章", "html": "chapter_27.html",
     "title": "第27章 电力市场结算", "group": "第四篇 技术支持系统篇"},
    {"id": "ch28", "pattern": r"第\s*28\s*章", "html": "chapter_28.html",
     "title": "第28章 模拟仿真", "group": "第四篇 技术支持系统篇"},
    {"id": "ch29", "pattern": r"第\s*29\s*章", "html": "chapter_29.html",
     "title": "第29章 系统运维管理", "group": "第四篇 技术支持系统篇"},
    {"id": "ch30", "pattern": r"第\s*30\s*章", "html": "chapter_30.html",
     "title": "第30章 安全防护", "group": "第四篇 技术支持系统篇"},
    {"id": "ch31", "pattern": r"第\s*31\s*章", "html": "chapter_31.html",
     "title": "第31章 \"双碳\"目标和新型电力系统下的电力市场展望", "group": "第五篇 展望篇"},
    {"id": "appa", "pattern": r"附录\s*A", "html": "appendix_a.html",
     "title": "附录A 电力现货市场规则框架示例", "group": "附录"},
    {"id": "appb", "pattern": r"附录\s*B", "html": "appendix_b.html",
     "title": "附录B 电力现货市场导则范本", "group": "附录"},
]


def load_page_json(page_idx: int) -> Optional[Dict[str, Any]]:
    page_dir = OUTPUT_DIR / f"page_{page_idx:04d}"
    json_files = list(page_dir.glob("*.json"))
    if not json_files:
        return None
    with open(json_files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def find_chapter_in_blocks(blocks: List[Dict]) -> Optional[Dict]:
    """Check if a page's blocks indicate a chapter start.

    Strategy: Scan header blocks for "第N章" patterns. The FIRST page
    where a new chapter number appears is the chapter start page.
    Also check for doc_title blocks with matching chapter name content.
    """
    for block in blocks:
        label = block.get("block_label", "")
        content = str(block.get("block_content", "")).strip()
        if label == "header" and content:
            for ch in CHAPTERS:
                if re.search(ch["pattern"], content):
                    return {**ch, "matched_title": content}
    return None


def main():
    # Count pages
    page_dirs = [d for d in OUTPUT_DIR.glob("page_*")
                 if d.is_dir() and d.name not in ("restructured", "smoke_test")]
    total_pages = len(page_dirs)
    print(f"Scanning {total_pages} page directories for chapter titles...")

    # Scan for chapter start pages — track first occurrence of each chapter
    chapter_starts: Dict[int, Dict] = {}
    seen_chapters: set = set()
    for page_dir in sorted(page_dirs):
        try:
            page_idx = int(page_dir.name.split("_")[1])
        except (ValueError, IndexError):
            continue

        data = load_page_json(page_idx)
        if data is None:
            continue

        blocks = data.get("parsing_res_list", [])
        ch = find_chapter_in_blocks(blocks)
        if ch and ch["id"] not in seen_chapters:
            seen_chapters.add(ch["id"])
            chapter_starts[page_idx] = ch
            pdf_page = page_idx + 1
            print(f"  Page idx {page_idx:3d} (PDF {pdf_page:3d}): "
                  f"{ch['id']:5s} → {ch['matched_title'][:40]}")

    # Build page ranges
    sorted_starts = sorted(chapter_starts.keys())
    mapping = []
    for i, start_idx in enumerate(sorted_starts):
        end_idx = sorted_starts[i + 1] - 1 if i + 1 < len(sorted_starts) else total_pages - 1
        ch = chapter_starts[start_idx]
        mapping.append({
            "start_page_idx": start_idx,
            "end_page_idx": end_idx,
            "start_pdf_page": start_idx + 1,
            "end_pdf_page": end_idx + 1,
            "chapter_id": ch["id"],
            "title": ch["title"],
            "html_file": ch["html"],
            "group": ch["group"],
            "matched_title": ch.get("matched_title", ""),
        })

    # Prepend preface: all pages before first chapter
    if mapping:
        first_ch_start = mapping[0]["start_page_idx"]
        # Find first page with real content (skip cover/blank pages)
        preface_start = 0
        for page_dir in sorted(page_dirs):
            try:
                page_idx = int(page_dir.name.split("_")[1])
            except (ValueError, IndexError):
                continue
            if page_idx >= first_ch_start:
                break
            data = load_page_json(page_idx)
            if data and data.get("parsing_res_list"):
                blocks = data["parsing_res_list"]
                text_blocks = [b for b in blocks
                               if b.get("block_label") in ("text", "doc_title", "paragraph_title")
                               and len(str(b.get("block_content", ""))) > 10]
                if len(text_blocks) >= 2:
                    preface_start = page_idx
                    break

        if preface_start < first_ch_start:
            mapping.insert(0, {
                "start_page_idx": preface_start,
                "end_page_idx": first_ch_start - 1,
                "start_pdf_page": preface_start + 1,
                "end_pdf_page": first_ch_start,
                "chapter_id": "preface",
                "title": "前言与序言",
                "html_file": "preface.html",
                "group": "序篇",
                "matched_title": "前言",
            })

    # Save
    mapping_path = OUTPUT_DIR / "chapter_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\nChapter mapping ({len(mapping)} entries):")
    for m in mapping:
        pages = m["end_page_idx"] - m["start_page_idx"] + 1
        print(f"  {m['html_file']:20s}  PDF {m['start_pdf_page']:3d}-{m['end_pdf_page']:3d}  "
              f"({pages:2d} pages)  {m['title']}")
    print(f"\nSaved to {mapping_path}")


if __name__ == "__main__":
    main()
