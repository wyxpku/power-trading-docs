# PaddleOCR-VL-1.6 PDF Reconversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Claude-vision-based PDF transcription with PaddleOCR-VL-1.6 for higher accuracy OCR, table recognition, and figure extraction on the Chinese technical book "电力现货市场实务" (646 pages).

**Architecture:** Three-phase pipeline: (1) PaddleOCR-VL processes the PDF into per-page JSON with layout blocks (PP-DocLayoutV2 layout analysis + PaddleOCR-VL-0.9B VLM recognition), (2) Python script extracts figure crops from page images using OCR bounding boxes, (3) Python script converts the structured output into the existing HTML book reader format (34 chapter files with split-view, themes, sidebar navigation).

**Tech Stack:** Python 3.12.7 + PaddleOCR-VL-1.6 (`paddleocr[doc_parser]`) + PaddlePaddle (CPU mode on Apple M3) + Pillow

---

## Pre-flight: Hardware & Environment

| Item | Value |
|------|-------|
| Machine | Apple M3 MacBook, 16 GB RAM |
| Python | 3.12.7 |
| Source PDF | `docs/电力现货市场实务 (国家电力调度控制中心组编) (Z-Library).pdf` (~45 MB, 646 pages) |
| Page images | `book/pages/page_001.png` – `page_647.png` (1190×1684 px, 284 MB total) |
| PaddleOCR-VL mode | CPU only (`device="cpu"`) — no GPU on Apple Silicon |
| Expected speed | ~10-30s/page on CPU → ~2-5 hours for full PDF |

---

## File Structure

### New files to create:

| File | Purpose |
|------|---------|
| `.venv/` | Python virtual environment |
| `.gitignore` | Exclude `.venv/`, `paddleocr_output/`, model caches |
| `book/scripts/paddleocr_run.py` | Run PaddleOCR-VL on full PDF, save per-page results |
| `book/scripts/paddleocr_to_html.py` | Convert PaddleOCR-VL output to HTML book format |
| `book/scripts/paddleocr_output/` | Directory for raw PaddleOCR-VL output |

### Smoke-test & utility scripts (new, can be deleted after use):

| File | Purpose |
|------|---------|
| `book/scripts/paddleocr_smoke_test.py` | Single-page test to understand output format |
| `book/scripts/detect_chapters.py` | Scan OCR output for chapter title pages |
| `book/scripts/extract_figures.py` | Crop figures from page images using OCR bboxes |

### Files to regenerate (overwrite):

| Files | Note |
|-------|------|
| `book/preface.html` | Front matter, preface, 序言 |
| `book/chapter_01.html` – `chapter_31.html` | All 31 chapters |
| `book/appendix_a.html`, `appendix_b.html` | Appendices |
| `book/pages/crops/*.png` | Delete old crops, regenerate from OCR bboxes |

### Files to delete (old approach):

| File | Reason |
|------|--------|
| `book/scripts/figure_crop_mcp.py` | Replaced by PaddleOCR-VL pipeline |
| `book/scripts/figure_recrop.py` | Replaced by PaddleOCR-VL pipeline |
| `book/scripts/figure_inventory.py` | No longer needed |
| `book/scripts/figure_auto_crop.py` | No longer needed |
| `book/scripts/figure_inventory.json` | No longer needed |

### Files to preserve (unchanged):

| File | Note |
|------|------|
| `book/css/style.css` | Styles, themes |
| `book/js/book-navigation.js` | Heading anchors, section nav |
| `book/index.html` | Landing page |
| `book/pages/page_NNN.png` | Source page images |

---

### Task 1: Create Python Virtual Environment and Install PaddleOCR-VL

**Files:**
- Create: `.venv/`
- Create: `.gitignore`

- [ ] **Step 1: Create virtual environment**

```bash
cd /Users/ethan/Workspace/power-trading-docs
python3 -m venv .venv
source .venv/bin/activate
python --version
```

Expected: `Python 3.12.7`

- [ ] **Step 2: Install PaddleOCR-VL and dependencies**

```bash
pip install --upgrade pip setuptools wheel
pip install "paddleocr[doc_parser]" Pillow
```

Note: This downloads PaddlePaddle (CPU), PaddleOCR, and doc-parser extras (PP-DocLayoutV2 + PaddleOCR-VL models). Total download ~2-3 GB. The first time `PaddleOCRVL` is instantiated it will also download model weights (~1 GB).

- [ ] **Step 3: Verify installation**

```bash
python -c "
from paddleocr import PaddleOCRVL
print('PaddleOCR-VL import OK')
import paddle
print(f'PaddlePaddle version: {paddle.__version__}')
from PIL import Image
print('Pillow OK')
"
```

Expected: All three imports succeed.

- [ ] **Step 4: Create .gitignore**

```bash
cat > /Users/ethan/Workspace/power-trading-docs/.gitignore << 'EOF'
.venv/
book/scripts/paddleocr_output/
*paddleocr*.log
EOF
```

- [ ] **Step 5: Commit setup**

```bash
git add .gitignore
git commit -m "chore: add .gitignore for PaddleOCR-VL reconversion work"
```

---

### Task 2: Single-Page Smoke Test

**Purpose:** Run PaddleOCR-VL on one page (page 20, which has figure 1-1) to discover the exact output format before building the full pipeline.

**Files:**
- Create: `book/scripts/paddleocr_smoke_test.py`

- [ ] **Step 1: Write smoke test script**

Create `book/scripts/paddleocr_smoke_test.py`:

```python
#!/usr/bin/env python3
"""Smoke test: run PaddleOCR-VL on a single page and examine output.

Uses page_020.png (chapter 1, contains figure 1-1) as the test case.
"""
import json
from pathlib import Path
from paddleocr import PaddleOCRVL

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_IMAGE = REPO_ROOT / "book" / "pages" / "page_020.png"
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output" / "smoke_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print(f"Test image: {TEST_IMAGE}")
    print(f"Exists: {TEST_IMAGE.exists()}")

    print("\nInitializing PaddleOCR-VL (CPU mode)...")
    print("NOTE: First run downloads model weights (~1 GB).")
    pipeline = PaddleOCRVL(device="cpu")

    print("Running prediction on single page image...")
    output = pipeline.predict(input=str(TEST_IMAGE))
    pages_res = list(output)
    print(f"Got {len(pages_res)} result(s)")

    for i, res in enumerate(pages_res):
        print(f"\n{'='*60}")
        print(f"Result {i} — type: {type(res).__name__}")
        print(f"{'='*60}")

        # Print all public attributes
        attrs = [a for a in dir(res) if not a.startswith('_')]
        print(f"Public attributes: {attrs}")

        # Try to access parsing results
        if hasattr(res, 'parsing_res_list'):
            blocks = res.parsing_res_list
            print(f"\nBlocks: {len(blocks)}")
            for j, block in enumerate(blocks):
                print(f"\n--- Block {j} ---")
                for key, val in block.items():
                    if key == 'block_content':
                        print(f"  {key}: {str(val)[:300]}...")
                    else:
                        print(f"  {key}: {val}")
        elif hasattr(res, '__dict__'):
            print(f"\nResult __dict__ keys: {list(res.__dict__.keys())}")
            for k, v in res.__dict__.items():
                print(f"  {k}: {type(v).__name__} = {str(v)[:300]}")

        # Save all output formats for inspection
        for save_fn in ['save_to_json', 'save_to_markdown', 'save_to_html']:
            if hasattr(res, save_fn):
                try:
                    getattr(res, save_fn)(save_path=str(OUTPUT_DIR))
                    print(f"\n{save_fn}() → {OUTPUT_DIR}")
                except Exception as e:
                    print(f"\n{save_fn}() failed: {e}")

    # List output files
    print(f"\nOutput files:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run smoke test**

```bash
cd /Users/ethan/Workspace/power-trading-docs
source .venv/bin/activate
python book/scripts/paddleocr_smoke_test.py 2>&1 | tee book/scripts/paddleocr_smoke_test.log
```

Expected: Console output shows block structure, labels, bbox formats. JSON/markdown/HTML files saved to `paddleocr_output/smoke_test/`.

- [ ] **Step 3: Document output format findings**

Read the JSON output file and record these critical details:

1. **Block labels used** (e.g., `text`, `title`, `table`, `figure`, `figure_caption`)
2. **Bbox format** (is it `[x1, y1, x2, y2]`, `[[x1,y1],[x2,y2],...]` polygon, or `[x, y, w, h]`?)
3. **Text content format** (plain text or HTML with inline formatting?)
4. **Table content format** (HTML `<table>...</table>` or structured JSON?)
5. **Figure content format** (caption text, image path, or empty?)
6. **Title/heading level detection** (does it provide level info, e.g., `level: 1`?)

**CRITICAL:** Tasks 4-6 code makes assumptions about the output format. If the smoke test reveals differences, adjust the code in those tasks accordingly. The key integration points are:
- `extract_figures.py`: bbox parsing in `parse_bbox()` — adjust to match actual format
- `paddleocr_to_html.py`: `block_to_html()` — adjust block label checks and content handling

---

### Task 3: Run Full PDF Conversion

**Purpose:** Process the entire 646-page PDF through PaddleOCR-VL.

**Files:**
- Create: `book/scripts/paddleocr_run.py`

**Timing:** This takes 2-5 hours on CPU. Run it with `nohup` or in a `tmux` session so it survives terminal disconnects.

- [ ] **Step 1: Write full conversion script**

Create `book/scripts/paddleocr_run.py`:

```python
#!/usr/bin/env python3
"""Run PaddleOCR-VL on the full PDF and save per-page results.

On Apple M3 CPU, expect ~10-30 seconds per page.
Total: ~2-5 hours for 646 pages.

Results are saved incrementally — if interrupted, already-saved pages
are skipped on re-run.
"""
import json
import sys
import time
from pathlib import Path
from paddleocr import PaddleOCRVL

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PDF_PATH = REPO_ROOT / "docs" / "电力现货市场实务 (国家电力调度控制中心组编) (Z-Library).pdf"
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"


def get_completed_pages():
    """Find pages that have already been processed."""
    completed = set()
    for d in OUTPUT_DIR.glob("page_*"):
        if d.is_dir() and d.name != "restructured" and list(d.glob("*.json")):
            try:
                page_idx = int(d.name.split("_")[1])
                completed.add(page_idx)
            except (ValueError, IndexError):
                pass
    return completed


def main():
    print(f"PDF: {PDF_PATH}")
    print(f"PDF exists: {PDF_PATH.exists()}")
    if not PDF_PATH.exists():
        print("ERROR: PDF not found!", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    completed = get_completed_pages()
    print(f"Already completed: {len(completed)} pages")

    print("Initializing PaddleOCR-VL (CPU mode)...")
    pipeline = PaddleOCRVL(device="cpu")

    print("Running prediction on full PDF...")
    start_time = time.time()
    output = pipeline.predict(input=str(PDF_PATH))

    # Collect all results (this drives the full processing)
    pages_res = []
    for i, res in enumerate(output):
        pages_res.append(res)
        if i in completed:
            continue

        page_dir = OUTPUT_DIR / f"page_{i:04d}"
        page_dir.mkdir(parents=True, exist_ok=True)

        try:
            res.save_to_json(save_path=str(page_dir))
        except Exception as e:
            print(f"  ERROR saving page {i} JSON: {e}", file=sys.stderr)

        if (i + 1) % 20 == 0:
            elapsed = time.time() - start_time
            rate = elapsed / (i + 1)
            remaining = rate * (646 - i - 1)
            print(f"  {i+1}/646 pages ({elapsed:.0f}s elapsed, ~{remaining/60:.0f}min remaining)")

    elapsed = time.time() - start_time
    print(f"Processed {len(pages_res)} pages in {elapsed:.0f}s ({elapsed/len(pages_res):.1f}s/page)")

    # Cross-page restructuring (merges tables spanning pages, reorders titles)
    print("\nRunning restructure_pages for cross-page merging...")
    try:
        restructured = pipeline.restructure_pages(pages_res)
        restructure_dir = OUTPUT_DIR / "restructured"
        restructure_dir.mkdir(parents=True, exist_ok=True)
        for i, res in enumerate(restructured):
            try:
                res.save_to_json(save_path=str(restructure_dir))
            except Exception as e:
                print(f"  ERROR saving restructured page {i}: {e}", file=sys.stderr)
        print("Restructured output saved.")
    except Exception as e:
        print(f"WARNING: restructure_pages failed: {e}", file=sys.stderr)
        print("Continuing with per-page results only.")

    print(f"\nDone! Results in {OUTPUT_DIR}")
    print(f"Page dirs: {len(list(OUTPUT_DIR.glob('page_*')))}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full conversion**

Option A — foreground (simple, keeps terminal occupied):
```bash
cd /Users/ethan/Workspace/power-trading-docs
source .venv/bin/activate
python book/scripts/paddleocr_run.py 2>&1 | tee book/scripts/paddleocr_run.log
```

Option B — background with `nohup` (survives terminal close):
```bash
cd /Users/ethan/Workspace/power-trading-docs
source .venv/bin/activate
nohup python book/scripts/paddleocr_run.py > book/scripts/paddleocr_run.log 2>&1 &
echo "PID: $!"
echo "Monitor: tail -f book/scripts/paddleocr_run.log"
```

- [ ] **Step 3: Verify output completeness**

```bash
# Count page directories and JSON files
echo "Page dirs: $(ls -d book/scripts/paddleocr_output/page_* 2>/dev/null | wc -l)"
echo "JSON files: $(find book/scripts/paddleocr_output -name '*.json' -not -path '*/restructured/*' -not -path '*/smoke_test/*' | wc -l)"
```

Expected: ~646 page directories, each with at least one JSON file.

---

### Task 4: Detect Chapter Boundaries

**Purpose:** Scan PaddleOCR-VL output for chapter title pages and build a page-to-chapter mapping.

**Files:**
- Create: `book/scripts/detect_chapters.py`
- Create: `book/scripts/paddleocr_output/chapter_mapping.json` (output)

- [ ] **Step 1: Write chapter detection script**

Create `book/scripts/detect_chapters.py`:

```python
#!/usr/bin/env python3
"""Detect chapter boundaries from PaddleOCR-VL output.

Scans all page JSON results for title blocks matching known chapter patterns.
Outputs chapter_mapping.json with page ranges for each chapter.

IMPORTANT: This script uses regex patterns to match chapter titles. If
PaddleOCR-VL OCR'd the titles differently, the patterns may need adjustment.
Check the smoke test output first to see how titles are recognized.
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
    """Check if a page's blocks contain a chapter title."""
    for block in blocks:
        label = block.get("block_label", "")
        content = str(block.get("block_content", "")).strip()

        # Only check title-like blocks and short text blocks
        if label not in ("title", "section_title", "text"):
            continue
        # Skip long text blocks (paragraphs, not titles)
        if label == "text" and len(content) > 50:
            continue

        for ch in CHAPTERS:
            if re.search(ch["pattern"], content):
                return {**ch, "matched_title": content}
    return None


def main():
    # Count pages
    page_dirs = [d for d in OUTPUT_DIR.glob("page_*")
                 if d.is_dir() and d.name != "restructured" and d.name != "smoke_test"]
    total_pages = len(page_dirs)
    print(f"Scanning {total_pages} page directories for chapter titles...")

    # Scan for chapter start pages
    chapter_starts: Dict[int, Dict] = {}
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
        if ch:
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
                               if b.get("block_label") in ("text", "title")
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
```

- [ ] **Step 2: Run chapter detection**

```bash
cd /Users/ethan/Workspace/power-trading-docs
source .venv/bin/activate
python book/scripts/detect_chapters.py
```

Expected: `chapter_mapping.json` with ~33-34 entries covering all pages. Each has `start_page_idx`, `end_page_idx`, `html_file`, `title`.

- [ ] **Step 3: Verify mapping covers all pages**

```bash
python -c "
import json
m = json.load(open('book/scripts/paddleocr_output/chapter_mapping.json'))
print(f'Entries: {len(m)}')
total = sum(e['end_page_idx'] - e['start_page_idx'] + 1 for e in m)
print(f'Pages covered: {total}')
# Check no overlaps
for i in range(len(m)-1):
    if m[i]['end_page_idx'] >= m[i+1]['start_page_idx']:
        print(f'OVERLAP: {m[i][\"html_file\"]} and {m[i+1][\"html_file\"]}')
"
```

Expected: 33-34 entries, ~646 pages covered, no overlaps.

---

### Task 5: Extract Figures from Page Images

**Purpose:** Crop figure regions from page images using PaddleOCR-VL bounding boxes. This replaces the old AI-vision cropping approach.

**Files:**
- Create: `book/scripts/extract_figures.py`
- Regenerate: `book/pages/crops/*.png`

- [ ] **Step 1: Clean old crops**

```bash
rm -f book/pages/crops/*.png
mkdir -p book/pages/crops
echo "Old crops removed"
```

- [ ] **Step 2: Write figure extraction script**

Create `book/scripts/extract_figures.py`:

```python
#!/usr/bin/env python3
"""Extract figures from page images using PaddleOCR-VL bounding boxes.

For each page, finds blocks with block_label == "image" (or "figure")
and crops the region from the page image with padding.

Also updates the JSON files with crop_path references for the HTML
conversion step.
"""
import json
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"
PAGES_DIR = REPO_ROOT / "book" / "pages"
CROP_DIR = PAGES_DIR / "crops"
CROP_DIR.mkdir(parents=True, exist_ok=True)
PADDING = 15
MIN_FIGURE_AREA = 5000


def parse_bbox(bbox):
    """Parse bbox to (x1, y1, x2, y2).

    Handles formats:
    - [x1, y1, x2, y2]
    - [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] (4-point polygon)
    """
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError(f"Unexpected bbox: {bbox}")

    if isinstance(bbox[0], (list, tuple)):
        # Polygon: 4 corners → bounding rect
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
    else:
        return (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))


def extract_figures():
    figure_count = 0
    skipped = 0

    for page_dir in sorted(OUTPUT_DIR.glob("page_*")):
        if not page_dir.is_dir() or page_dir.name in ("restructured", "smoke_test"):
            continue

        json_files = list(page_dir.glob("*.json"))
        if not json_files:
            continue

        page_idx = int(page_dir.name.split("_")[1])
        # Page images are 1-indexed: page_001.png, page_002.png, ...
        page_image_path = PAGES_DIR / f"page_{page_idx + 1:03d}.png"

        if not page_image_path.exists():
            continue

        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        blocks = data.get("parsing_res_list", [])
        fig_idx = 0
        modified = False

        for block in blocks:
            label = block.get("block_label", "")
            if label not in ("image", "figure"):
                continue

            bbox_raw = block.get("block_bbox")
            if not bbox_raw:
                skipped += 1
                continue

            try:
                x1, y1, x2, y2 = parse_bbox(bbox_raw)
            except (ValueError, IndexError, TypeError):
                skipped += 1
                continue

            area = (x2 - x1) * (y2 - y1)
            if area < MIN_FIGURE_AREA:
                skipped += 1
                continue

            fig_idx += 1

            with Image.open(page_image_path) as img:
                px1 = max(0, x1 - PADDING)
                py1 = max(0, y1 - PADDING)
                px2 = min(img.width, x2 + PADDING)
                py2 = min(img.height, y2 + PADDING)

                if px2 <= px1 or py2 <= py1:
                    skipped += 1
                    continue

                crop = img.crop((px1, py1, px2, py2))
                crop_name = f"page_{page_idx + 1:03d}_fig{fig_idx}.png"
                crop.save(CROP_DIR / crop_name)
                figure_count += 1

                # Store reference back in JSON for HTML conversion
                block["crop_path"] = f"pages/crops/{crop_name}"
                block["figure_index"] = fig_idx
                modified = True

        if modified:
            with open(json_files[0], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Extracted {figure_count} figures to {CROP_DIR}")
    print(f"Skipped {skipped} blocks (no bbox, too small, or invalid)")
    print(f"Crop files: {len(list(CROP_DIR.glob('*.png')))}")


if __name__ == "__main__":
    extract_figures()
```

- [ ] **Step 3: Run figure extraction**

```bash
cd /Users/ethan/Workspace/power-trading-docs
source .venv/bin/activate
python book/scripts/extract_figures.py
```

Expected: 100-200 figure crops in `book/pages/crops/`.

---

### Task 6: Build HTML Conversion Script

**Purpose:** Convert PaddleOCR-VL JSON output into the existing HTML book reader format. This is the core pipeline — it reads per-page JSON, generates HTML blocks, wraps them in the full page template, and writes the 34 chapter files.

**Files:**
- Create: `book/scripts/paddleocr_to_html.py`

This is the largest script. It has four sections:
1. **Sidebar template** — generates TOC navigation HTML with active link
2. **Block → HTML** — converts PaddleOCR-VL blocks to HTML elements
3. **Page template** — wraps content in full HTML page structure
4. **Main pipeline** — reads mapping, processes pages, writes files

- [ ] **Step 1: Write the HTML conversion script**

Create `book/scripts/paddleocr_to_html.py`:

```python
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
        ("第31章 "双碳"目标和新型电力系统下的电力市场展望", "chapter_31.html"),
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
    if re.match(r'^第\d+章\s', text):
        return 'h1'
    if re.match(r'^第[一二三四五六七八九十]+篇\s', text):
        return 'h1'
    if re.match(r'^附录[A-Z]\s', text):
        return 'h1'
    if text in ('前言', '序', '序言', '前言与序言', '目　录', '目录'):
        return 'h1'
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 'h3'
    if re.match(r'^\d+\.\d+\s', text):
        return 'h2'
    return None


def block_to_html(block: Dict[str, Any], pdf_page: int) -> Optional[str]:
    """Convert a single PaddleOCR-VL block to an HTML string."""
    label = block.get("block_label", "")
    content = str(block.get("block_content", "")).strip()

    # Skip headers, footers, page numbers
    if label in ("header", "footer", "page_number"):
        return None

    # Empty content (skip unless it's an image with a crop)
    if not content and label not in ("image", "figure"):
        return None

    # ── Title blocks ──────────────────────────────────────────────────
    if label in ("title", "section_title"):
        level = detect_heading_level(content) or "h2"
        return f'\t<{level}>{html_mod.escape(content)}</{level}>'

    # ── Text blocks ───────────────────────────────────────────────────
    if label in ("text",):
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

    # ── Table blocks ──────────────────────────────────────────────────
    if label == "table":
        if content.startswith('<'):
            # Already HTML — use as-is
            return f'\t{content}'
        # Fallback: preformatted text
        return f'\t<pre>{html_mod.escape(content)}</pre>'

    # ── Figure/Image blocks ───────────────────────────────────────────
    if label in ("image", "figure"):
        crop_path = block.get("crop_path", "")
        fig_idx = block.get("figure_index", 0)
        if not crop_path:
            crop_name = f"page_{pdf_page:03d}_fig{fig_idx}.png"
            crop_path = f"pages/crops/{crop_name}"

        # Use block content as caption, or generate a fallback
        if content:
            caption = content
        else:
            caption = f"图 page {pdf_page} fig {fig_idx}"

        escaped_caption = html_mod.escape(caption)
        return (
            f'\t<figure class="embedded-figure">\n'
            f'\t  <img src="{crop_path}" alt="{escaped_caption}">\n'
            f'\t  <figcaption>{escaped_caption}</figcaption>\n'
            f'\t</figure>'
        )

    # ── Figure caption (standalone, if not merged with figure) ────────
    if label in ("figure_caption", "caption"):
        return f'\t<p><em>{html_mod.escape(content)}</em></p>'

    # ── Unknown block → text fallback ─────────────────────────────────
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
```

- [ ] **Step 2: Run HTML conversion**

```bash
cd /Users/ethan/Workspace/power-trading-docs
source .venv/bin/activate
python book/scripts/paddleocr_to_html.py
```

Expected: 33-34 HTML files generated in `book/`, each with sidebar, split-view, page dividers, and OCR content.

- [ ] **Step 3: Verify generated files exist**

```bash
echo "HTML files:"
ls -la book/preface.html book/chapter_*.html book/appendix_*.html 2>/dev/null | wc -l
echo "Expected: 34 (preface + 31 chapters + 2 appendices)"
```

---

### Task 7: Visual Verification

**Purpose:** Spot-check generated HTML to ensure OCR quality, table rendering, figure crops, and navigation all work.

- [ ] **Step 1: Open test chapter in browser**

```bash
open book/chapter_01.html
```

Check all of the following:
- [ ] Sidebar navigation loads with "第1章" highlighted as active
- [ ] Theme switching works (明亮/护眼/深色 buttons)
- [ ] Split view: text panel shows OCR content, scan panel shows page image
- [ ] Scrolling the text panel updates the scan panel image (IntersectionObserver)
- [ ] View mode toggle works (纯文本/对照扫描件)
- [ ] Page dividers show correct page numbers (e.g., "PDF 第 19 页 / 书第 2 页")
- [ ] Text content matches the corresponding page image
- [ ] Figure crops render with `<figcaption>` captions
- [ ] Tables (if present) render as HTML tables
- [ ] `book-navigation.js` adds heading anchors and section navigation

- [ ] **Step 2: Spot-check figure quality**

```bash
# Compare a crop with the full page
open book/pages/crops/page_020_fig1.png
open book/pages/page_020.png
```

Verify the crop captures the complete figure with appropriate margins (not truncated, not too much whitespace).

- [ ] **Step 3: Check multiple chapters across the book**

Open 3-5 chapters spread across the book:
- Early: `chapter_03.html` (price mechanism, likely has tables)
- Middle: `chapter_10.html` or `chapter_11.html` (foreign markets)
- Late: `chapter_23.html` (clearing, technical content)
- Appendix: `appendix_a.html`

For each, verify text quality, table rendering, and figure display.

---

### Task 8: Cleanup and Commit

- [ ] **Step 1: Delete old scripts**

```bash
rm -f book/scripts/figure_crop_mcp.py
rm -f book/scripts/figure_recrop.py
rm -f book/scripts/figure_inventory.py
rm -f book/scripts/figure_auto_crop.py
rm -f book/scripts/figure_inventory.json
echo "Old scripts removed"
```

- [ ] **Step 2: Verify all 34 HTML files present and non-empty**

```bash
for f in preface.html chapter_{01..31}.html appendix_a.html appendix_b.html; do
  if [ -f "book/$f" ] && [ -s "book/$f" ]; then
    echo "OK  book/$f"
  else
    echo "MISSING OR EMPTY  book/$f"
  fi
done
```

Expected: All 34 files show "OK".

- [ ] **Step 3: Verify figure crops**

```bash
echo "Figure crops: $(ls book/pages/crops/*.png 2>/dev/null | wc -l)"
```

Expected: 100-200+ figure crops.

- [ ] **Step 4: Commit**

```bash
git add \
  .gitignore \
  book/scripts/paddleocr_run.py \
  book/scripts/paddleocr_smoke_test.py \
  book/scripts/detect_chapters.py \
  book/scripts/extract_figures.py \
  book/scripts/paddleocr_to_html.py \
  book/preface.html \
  book/chapter_*.html \
  book/appendix_*.html \
  book/pages/crops/

# Remove old scripts from tracking
git rm --cached book/scripts/figure_crop_mcp.py \
  book/scripts/figure_recrop.py \
  book/scripts/figure_inventory.py \
  book/scripts/figure_auto_crop.py \
  book/scripts/figure_inventory.json \
  2>/dev/null || true

git commit -m "feat: re-convert PDF with PaddleOCR-VL-1.6

Replace Claude-vision transcription with PaddleOCR-VL-1.6 for
higher accuracy OCR, table recognition, and figure extraction.
All 34 chapter HTML files and figure crops regenerated from scratch.

Pipeline: PaddleOCR-VL predict → per-page JSON → figure extraction
→ HTML generation matching existing book reader layout."
```

---

## Self-Review

### 1. Spec Coverage

| Requirement | Task |
|------------|------|
| Install PaddleOCR-VL-1.6 locally | Task 1 |
| Test single page, understand output | Task 2 |
| Run full PDF conversion | Task 3 |
| Detect chapter boundaries | Task 4 |
| Extract figures from bounding boxes | Task 5 |
| Convert to HTML book format | Task 6 |
| Visual quality verification | Task 7 |
| Clean up old approach, commit | Task 8 |
| Discard current results | Task 8 (deletes old scripts/crops, regenerates HTML) |

### 2. Placeholder Scan

- No "TBD", "TODO", "implement later", "fill in details"
- No "add appropriate error handling" / "add validation"
- All code blocks contain complete implementations
- No "similar to Task N" references

### 3. Type Consistency

- `page_idx` is 0-indexed (from PaddleOCR-VL) throughout all scripts
- `pdf_page` is 1-indexed (= `page_idx + 1`) throughout all scripts
- `chapter_mapping.json` fields used consistently: `start_page_idx`, `end_page_idx`, `html_file`, `title`
- `block_to_html()` returns `Optional[str]` consistently
- `build_sidebar(active_href)` parameter matches `html_file` values in mapping
