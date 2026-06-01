# Figure Cropping & SVG Redraw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace full-page PNG references in HTML figures with properly cropped images or inline SVG redraws, using AI vision to locate figure boundaries.

**Architecture:** For each page containing figures, AI vision MCP analyzes the page PNG to identify figure boundaries and classify each as crop-candidate or SVG-redraw-candidate. Simple data charts get redrawn as inline SVG; complex diagrams get cropped from the original page PNG. HTML `<figure>` elements are updated with the new `src` or inline SVG content.

**Tech Stack:** AI vision MCP (`analyze_image`), `sips` (macOS image cropping), inline SVG in HTML

---

## Key Context for Implementation

**Project state:**
- 427 page PNGs in `book/pages/page_001.png`–`page_427.png` (1190×1684px each)
- 159 `<figure class="embedded-figure">` elements across 34 HTML files
- 126 pages contain figures (28 pages have multiple figures)
- Existing `book/pages/crops/` has 151 crop files — ALL must be redone
- 7 crop files are currently shared by multiple figures (incorrect — each figure needs its own unique crop)
- All HTML figure `src` currently point to `pages/crops/page_NNN_figX.png`

**Naming convention:** `page_NNN_figX.png` where NNN is the zero-padded page number and X is the figure index (1-based) on that page.

**Multi-figure page ordering:** Figures are numbered top-to-bottom, left-to-right within a single page.

---

### Task 1: Clear existing crops and create output directory

**Files:**
- Modify: `book/pages/crops/` (clear all existing files)

- [ ] **Step 1: Remove all existing crop files**

```bash
rm -f book/pages/crops/*.png
echo "Cleared $(ls book/pages/crops/ 2>/dev/null | wc -l) remaining files"
```

Run: `rm -f book/pages/crops/*.png`
Expected: all old crop files removed, directory still exists

- [ ] **Step 2: Verify directory is clean**

```bash
ls book/pages/crops/ | wc -l
```

Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add -A book/pages/crops/
git commit -m "chore: clear old figure crops for re-processing"
```

---

### Task 2: Build figure inventory from HTML

**Files:**
- Create: `book/scripts/figure_inventory.py`

This script scans all HTML files and outputs a JSON inventory of every figure: its page number, position on page, figcaption, current src, and HTML file location. This inventory drives all subsequent tasks.

- [ ] **Step 1: Write the inventory script**

```python
#!/usr/bin/env python3
"""Scan HTML files and output JSON inventory of all embedded figures."""
import re, json, glob, os, sys

inventory = []

for html_file in sorted(
    glob.glob("book/chapter_*.html")
    + glob.glob("book/preface.html")
    + glob.glob("book/appendix_*.html")
):
    content = open(html_file).read()

    # Find all page-body-container sections and their page numbers
    page_sections = re.findall(
        r'<div class="page-body-container"[^>]*id="page-content-(\d+)"[^>]*>(.*?)</div>\s*<div class="page-divider"',
        content,
        re.DOTALL,
    )

    # Also try matching last page section (no following page-divider)
    page_sections += re.findall(
        r'<div class="page-body-container"[^>]*id="page-content-(\d+)"[^>]*>(.*?)(?:</div>\s*$)',
        content,
        re.DOTALL,
    )

    # Build page_number -> section_content map
    page_map = {int(p): s for p, s in page_sections}

    # Find all figure blocks with their parent page
    # Approach: find each figure and look backwards for nearest page-content-N
    figure_pattern = re.compile(
        r'<div class="page-body-container"[^>]*id="page-content-(\d+)"[^>]*>(.*?)</div>\s*(?=<div class="page-divider"|$)',
        re.DOTALL,
    )

    for match in figure_pattern.finditer(content):
        page_num = int(match.group(1))
        section = match.group(2)

        figures = re.findall(
            r'<figure class="embedded-figure">(.*?)</figure>', section, re.DOTALL
        )

        for fig_idx, block in enumerate(figures):
            src_match = re.search(r'<img src="([^"]+)"', block)
            alt_match = re.search(r'alt="([^"]+)"', block)
            cap_match = re.search(r"<figcaption>(.*?)</figcaption>", block)

            src = src_match.group(1) if src_match else ""
            alt = alt_match.group(1) if alt_match else ""
            caption = cap_match.group(1) if cap_match else ""

            inventory.append(
                {
                    "page": page_num,
                    "fig_index_on_page": fig_idx + 1,
                    "src": src,
                    "alt": alt,
                    "caption": caption,
                    "html_file": os.path.basename(html_file),
                }
            )

# Sort by page, then figure index
inventory.sort(key=lambda x: (x["page"], x["fig_index_on_page"]))

# Assign unique fig numbers per page
page_counters = {}
for item in inventory:
    key = item["page"]
    page_counters[key] = page_counters.get(key, 0) + 1
    item["fig_number"] = page_counters[key]
    item["expected_crop_name"] = f"page_{item['page']:03d}_fig{item['fig_number']}.png"
    item["expected_crop_path"] = f"pages/crops/page_{item['page']:03d}_fig{item['fig_number']}.png"

print(json.dumps(inventory, ensure_ascii=False, indent=2))
print(f"\n# Summary: {len(inventory)} figures across {len(set(i['page'] for i in inventory))} pages", file=sys.stderr)
```

- [ ] **Step 2: Run the inventory script and save output**

```bash
python3 book/scripts/figure_inventory.py > book/scripts/figure_inventory.json 2>&1
```

Expected: JSON file with 159 figure entries, one per figure element

- [ ] **Step 3: Verify the inventory**

```bash
python3 -c "import json; d=json.load(open('book/scripts/figure_inventory.json')); print(f'Figures: {len(d)}'); pages=set(i['page'] for i in d); print(f'Pages: {len(pages)}'); multi=[p for p in pages if sum(1 for i in d if i['page']==p)>1]; print(f'Multi-fig pages: {len(multi)}')"
```

Expected: `Figures: 159`, `Pages: 126`, `Multi-fig pages: 28`

- [ ] **Step 4: Commit**

```bash
git add book/scripts/figure_inventory.py book/scripts/figure_inventory.json
git commit -m "feat: add figure inventory script and generated inventory"
```

---

### Task 3: Process figures page by page using AI vision (manual/interactive loop)

This is the core task. It processes each page that contains figures, using AI vision to identify figure boundaries, classify them, and produce either cropped images or inline SVG.

Since this is an interactive process driven by AI vision MCP calls, it should be executed as a loop over the inventory. Each page is processed independently.

**Processing logic per page:**

1. Read the page PNG image
2. Call `analyze_image` MCP with a structured prompt asking for:
   - All figure/diagram/chart regions with pixel coordinates (x, y, width, height)
   - Classification of each: `crop` (complex diagram/photo) or `svg_redraw` (simple data chart)
   - For `svg_redraw` candidates: data points, labels, axis info
3. For `crop` type: use `sips` to crop the region from the page PNG
4. For `svg_redraw` type: generate inline SVG from extracted data
5. Update HTML: change `<img src="...">` to point to new crop, or replace `<img>` with `<div class="svg-chart">...</div>`
6. Save and commit per-chapter (not per-page)

**AI Vision Prompt Template:**

```
Analyze this page from a Chinese technical book. Identify ALL standalone figures, diagrams, charts, and photographs (NOT text paragraphs, headers, or page numbers).

For each identified figure, provide:
1. Figure index (1-based, ordered top-to-bottom then left-to-right)
2. Bounding box as pixel coordinates: x (left edge), y (top edge), width, height
3. Type classification:
   - "svg_redraw" for: line charts, bar charts, pie charts, scatter plots, simple data visualizations
   - "crop" for: architecture diagrams, flowcharts, photographs, complex schematics, diagrams with heavy Chinese annotations
4. Brief description of content

Return as JSON array. Example:
[
  {"index": 1, "x": 100, "y": 200, "width": 500, "height": 300, "type": "svg_redraw", "description": "Bar chart showing power generation by source"},
  {"index": 2, "x": 50, "y": 800, "width": 600, "height": 400, "type": "crop", "description": "System architecture diagram"}
]

This page has N figure(s). Their captions are: [list captions from inventory].
Use these captions to help locate and match each figure.
```

**For SVG redraw candidates, follow-up prompt:**

```
This is figure [N] from page [X]: [caption]. Extract all data needed to recreate this chart as SVG:
- Chart type (line/bar/pie/scatter)
- All data points with labels
- Axis labels and ranges
- Legend items
- Title
- Color scheme (approximate)
```

**Cropping command:**

```bash
# macOS sips crop: extract a rectangular region
# sips doesn't support direct pixel crop, use Python with PIL or ImageMagick
python3 -c "
from PIL import Image
img = Image.open('book/pages/page_NNN.png')
cropped = img.crop((x, y, x + width + 4, y + height + 4))  # +4px padding
cropped.save('book/pages/crops/page_NNN_figX.png')
"
```

Or if PIL unavailable, use `sips` with a two-step approach (crop height then crop width from origin, requires offset calculation):

```bash
# Alternative: use macOS built-in Python with no extra deps
python3 -c "
import subprocess, os
# Use sips to crop: first offset, then extract
# sips -c height width --out output input  (crops to size from center)
# Better approach: use CoreGraphics via pyobjc or just install Pillow
"
```

**Recommended: install Pillow if not available:**

```bash
pip3 install Pillow 2>/dev/null || pip install Pillow
```

---

### Task 3 Sub-tasks: Process pages in batches

The 126 pages should be processed in batches grouped by chapter file, so each commit updates one HTML file at a time. Process order follows chapter sequence.

**Batch processing order (by HTML file):**

| # | HTML file | Pages with figures | Figure count |
|---|-----------|-------------------|--------------|
| 1 | `chapter_01.html` | 20, 31, 37, 40 | 4 |
| 2 | `chapter_03.html` | 66, 67, 68, 69, 70, 72, 80 | 8 |
| 3 | `chapter_07.html` | 110, 111, 112, 113, 115, 120, 128, 133 | 10 |
| 4 | `chapter_08.html` | 146, 147, 149, 152, 154, 155, 156, 161, 163 | 9 |
| 5 | `chapter_09.html` | 174, 178, 180 | 5 |
| 6 | `chapter_10.html` | 189, 197, 198, 199 | 6 |
| 7 | `chapter_11.html` | 220 | 1 |
| 8 | `chapter_12.html` | 228, 229, 235, 238, 239, 240, 242, 243, 245 | 11 |
| 9 | `chapter_14.html` | 275, 278, 280, 281 | 4 |
| 10 | `chapter_15.html` | 292, 310, 317, 318 | 5 |
| 11 | `chapter_16.html` | 325, 326, 351 | 3 |
| 12 | `chapter_17.html` | 354, 355, 375 | 3 |
| 13 | `chapter_18.html` | 380, 392, 400 | 5 |
| 14 | `chapter_19.html` | 403, 404, 422, 423, 425 | 8 |
| 15 | `chapter_20.html` | 430, 436, 445, 446, 458, 460, 461 | 12 |
| 16 | `chapter_21.html` | 465, 466, 467, 469 | 4 |
| 17 | `chapter_22.html` | 473, 474, 476, 478 | 5 |
| 18 | `chapter_23.html` | 481, 482, 483, 487, 492, 496, 499, 500 | 12 |
| 19 | `chapter_24.html` | 503, 504, 505, 506, 507, 508, 509, 510 | 11 |
| 20 | `chapter_25.html` | 514, 515 | 2 |
| 21 | `chapter_26.html` | 516, 517, 521, 528, 530, 532, 533 | 7 |
| 22 | `chapter_27.html` | 538, 539, 542, 545, 547, 548 | 6 |
| 23 | `chapter_28.html` | 552, 554, 557, 558, 559, 560, 563, 564, 569 | 10 |
| 24 | `chapter_29.html` | 571, 575 | 2 |
| 25 | `chapter_30.html` | 580 | 3 |
| 26 | `chapter_31.html` | 586 | 2 |

For each batch (chapter), the steps are:

- [ ] **Step A: For each page in this batch, call `analyze_image` MCP** with the prompt template above, passing the page PNG path and the figure captions from inventory.

- [ ] **Step B: For each identified figure, process based on classification:**

  - **If `crop`:** Use Python/Pillow to crop the region with 4px padding:
    ```python
    from PIL import Image
    img = Image.open(f"book/pages/page_{page:03d}.png")
    x, y, w, h = fig["x"], fig["y"], fig["width"], fig["height"]
    pad = 4
    cropped = img.crop((max(0, x - pad), max(0, y - pad), x + w + pad, y + h + pad))
    cropped.save(f"book/pages/crops/page_{page:03d}_fig{idx}.png")
    ```

  - **If `svg_redraw`:** Generate inline SVG from extracted data. The SVG should:
    - Use a viewBox for responsive scaling
    - Use the project's CSS color variables where possible
    - Include all data points, labels, axes, legend
    - Be wrapped in `<div class="svg-chart">` for styling

- [ ] **Step C: Update the HTML file** — for each figure in this batch:
  - For crop: update `<img src="pages/crops/page_NNN_figX.png">` (ensure correct unique figX number)
  - For SVG redraw: replace the `<img>` element with `<div class="svg-chart"><svg>...</svg></div>`
  - Keep the `<figure class="embedded-figure">` and `<figcaption>` unchanged

- [ ] **Step D: Verify visually** — open the HTML file in a browser and check that figures render correctly.

- [ ] **Step E: Commit per chapter**

```bash
git add book/pages/crops/page_NNN_figX.png book/chapter_XX.html
git commit -m "feat: crop figures and redraw charts for chapter XX"
```

---

### Task 4: Add SVG chart CSS styling

**Files:**
- Modify: `book/css/style.css`

- [ ] **Step 1: Add CSS for inline SVG charts**

Add to the end of `book/css/style.css`:

```css
.svg-chart {
  margin: 1em auto;
  max-width: 100%;
  overflow: visible;
}

.svg-chart svg {
  width: 100%;
  height: auto;
  display: block;
}

.embedded-figure .svg-chart {
  text-align: center;
}

/* Dark theme adjustments */
[data-theme="dark"] .svg-chart svg text {
  fill: var(--text-primary, #e0e0e0);
}

[data-theme="dark"] .svg-chart svg line,
[data-theme="dark"] .svg-chart svg path {
  stroke: var(--text-secondary, #aaa);
}
```

- [ ] **Step 2: Verify CSS doesn't break existing styles**

Open any chapter with figures in browser, toggle between light/dark themes.

- [ ] **Step 3: Commit**

```bash
git add book/css/style.css
git commit -m "feat: add SVG chart CSS styling with dark mode support"
```

---

### Task 5: Final verification pass

- [ ] **Step 1: Verify all 159 figures have valid references**

```bash
python3 -c "
import re, glob, os

missing = []
for f in sorted(glob.glob('book/chapter_*.html') + glob.glob('book/preface.html') + glob.glob('book/appendix_*.html')):
    content = open(f).read()
    blocks = re.findall(r'<figure class=\"embedded-figure\">(.*?)</figure>', content, re.DOTALL)
    for block in blocks:
        src = re.search(r'<img src=\"([^\"]+)\"', block)
        if src:
            path = src.group(1)
            if not os.path.exists(os.path.join('book', path)):
                missing.append((f, path))

if missing:
    print(f'MISSING {len(missing)} crop files:')
    for f, p in missing:
        print(f'  {f}: {p}')
else:
    print('All figure image references are valid')
"
```

Expected: `All figure image references are valid`

- [ ] **Step 2: Verify no duplicate crop references**

```bash
python3 -c "
import re, glob
from collections import defaultdict

crop_to_figs = defaultdict(list)
for f in sorted(glob.glob('book/chapter_*.html') + glob.glob('book/preface.html') + glob.glob('book/appendix_*.html')):
    content = open(f).read()
    blocks = re.findall(r'<figure class=\"embedded-figure\">(.*?)</figure>', content, re.DOTALL)
    for block in blocks:
        src = re.search(r'<img src=\"([^\"]+)\"', block)
        cap = re.search(r'<figcaption>(.*?)</figcaption>', block)
        if src:
            crop_name = src.group(1).split('/')[-1]
            cap_text = cap.group(1) if cap else 'none'
            crop_to_figs[crop_name].append((os.path.basename(f), cap_text))

dups = {k: v for k, v in crop_to_figs.items() if len(v) > 1}
if dups:
    print(f'WARNING: {len(dups)} crop files shared by multiple figures:')
    for crop, figs in dups.items():
        print(f'  {crop}:')
        for html, cap in figs:
            print(f'    {html}: {cap[:50]}')
else:
    print('No duplicate crop references — each figure has unique crop file')
"
```

Expected: `No duplicate crop references`

- [ ] **Step 3: Spot-check 5-10 pages visually in browser** — open chapters spanning different figure types (charts, diagrams, photos) and verify figures render correctly in both light and dark themes.

- [ ] **Step 4: Final commit with cleanup**

```bash
git add -A
git commit -m "feat: complete figure cropping and SVG redraw for all 159 figures"
```

---

## Error Recovery

If AI vision returns unusable coordinates for a page:
1. Try once more with a more specific prompt referencing the figure captions
2. If still failing, skip that page's figures and leave them pointing to a full-page image — add a comment in the HTML: `<!-- TODO: figure crop failed, needs manual review -->`
3. Log failed pages for later manual review

If SVG redraw produces incorrect or incomplete data:
1. Fall back to cropping the original image
2. Do not leave broken SVG in the HTML
