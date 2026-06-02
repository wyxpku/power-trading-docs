#!/usr/bin/env python3
"""Automatically re-crop figures from page images using pixel analysis.

Strategy:
- For each page with figures, detect the content regions using pixel density analysis
- Figures are regions with visual content that differs from regular text
- Use generous padding to ensure nothing is cut off
- Match detected regions to expected figure count from inventory
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BOOK_DIR = REPO_ROOT / "book"
PAGES_DIR = BOOK_DIR / "pages"
CROP_DIR = PAGES_DIR / "crops"
INVENTORY_PATH = BOOK_DIR / "scripts" / "figure_inventory.json"

PAGE_WIDTH = 1190
PAGE_HEIGHT = 1684
# Content area margins (book has ~80-100px margins on each side)
CONTENT_LEFT = 80
CONTENT_RIGHT = 1110
# Minimum figure height to be considered valid
MIN_FIG_HEIGHT = 60
# Padding around detected figure
CROP_PAD = 15


def load_inventory():
    with open(INVENTORY_PATH) as f:
        return json.load(f)


def group_by_page(figures):
    groups = defaultdict(list)
    for fig in figures:
        groups[fig["page"]].append(fig)
    return dict(groups)


def analyze_page_regions(page_path, expected_figures=1):
    """Analyze a page image to find figure regions.

    Returns list of bounding boxes (x, y, width, height) for detected figures.
    Strategy: scan rows for density changes to find visual content blocks.
    """
    img = Image.open(page_path).convert('L')
    w, h = img.size

    # Calculate row density (number of dark pixels per row)
    row_density = []
    for row in range(h):
        dark = sum(1 for col in range(w) if img.getpixel((col, row)) < 200)
        row_density.append(dark)

    # Find "gap" rows (very low density = whitespace between content blocks)
    gap_threshold = 15  # rows with <15 dark pixels are gaps
    is_gap = [d < gap_threshold for d in row_density]

    # Find content blocks (contiguous non-gap regions)
    blocks = []
    in_block = False
    block_start = 0
    for i, gap in enumerate(is_gap):
        if not gap and not in_block:
            in_block = True
            block_start = i
        elif gap and in_block:
            in_block = False
            # Filter: skip very small blocks (likely just a header line)
            block_height = i - block_start
            if block_height >= 10:
                blocks.append((block_start, i))
    if in_block:
        block_height = h - block_start
        if block_height >= 10:
            blocks.append((block_start, h))

    if not blocks:
        return []

    # Identify which blocks are figures vs text:
    # Text blocks have moderate, consistent density (~100-400 dark pixels)
    # Figure blocks often have higher density or more variable density
    # But the simplest approach: for multi-figure pages, split by largest gaps

    if expected_figures == 1:
        # Single figure: find the largest non-text block
        # Heuristic: find blocks with density patterns different from typical text
        # For now, return the full content area and let the caller decide
        # Actually, try to find the block that contains graphical content

        # Look for blocks with horizontal lines (>300px of continuous dark pixels)
        # These are characteristic of diagrams, charts, tables
        for y_start, y_end in blocks:
            for row in range(y_start, y_end):
                max_line = 0
                line_len = 0
                for col in range(w):
                    if img.getpixel((col, row)) < 128:
                        line_len += 1
                        max_line = max(max_line, line_len)
                    else:
                        line_len = 0
                if max_line > 300:
                    # This block has graphical content
                    return [(CONTENT_LEFT, y_start, CONTENT_RIGHT - CONTENT_LEFT, y_end - y_start)]

        # No block with obvious graphical content — return the largest block
        # (might be a text-heavy figure or the figure is mixed with text)
        largest = max(blocks, key=lambda b: b[1] - b[0])
        return [(CONTENT_LEFT, largest[0], CONTENT_RIGHT - CONTENT_LEFT, largest[1] - largest[0])]

    else:
        # Multiple figures: find the top-N largest blocks or split by largest gaps
        # Sort blocks by size (largest first)
        sorted_blocks = sorted(blocks, key=lambda b: b[1] - b[0], reverse=True)

        # Take the top N blocks, but prefer ones with graphical content
        figure_blocks = []
        text_blocks = []

        for y_start, y_end in sorted_blocks:
            has_graphic = False
            for row in range(y_start, y_end):
                max_line = 0
                line_len = 0
                for col in range(w):
                    if img.getpixel((col, row)) < 128:
                        line_len += 1
                        max_line = max(max_line, line_len)
                    else:
                        line_len = 0
                if max_line > 200:
                    has_graphic = True
                    break
            if has_graphic:
                figure_blocks.append((y_start, y_end))
            else:
                text_blocks.append((y_start, y_end))

        # If we found enough graphic blocks, use those
        if len(figure_blocks) >= expected_figures:
            figure_blocks.sort()  # sort by y position
            return [(CONTENT_LEFT, y_s, CONTENT_RIGHT - CONTENT_LEFT, y_e - y_s)
                    for y_s, y_e in figure_blocks[:expected_figures]]

        # Otherwise, use the largest blocks
        result_blocks = sorted(sorted_blocks[:expected_figures], key=lambda b: b[0])
        return [(CONTENT_LEFT, y_s, CONTENT_RIGHT - CONTENT_LEFT, y_e - y_s)
                for y_s, y_e in result_blocks]


def crop_with_padding(page_path, box, dest_path, pad=CROP_PAD):
    """Crop a region from the page image with padding."""
    img = Image.open(page_path)
    x, y, w, h = box
    left = max(0, x - pad)
    top = max(0, y - pad)
    right = min(img.width, x + w + pad)
    bottom = min(img.height, y + h + pad)
    cropped = img.crop((left, top, right, bottom))
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dest_path)
    return cropped.size


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto-crop figures using pixel analysis")
    parser.add_argument("--page", type=int, help="Process a specific page")
    parser.add_argument("--all", action="store_true", help="Process all pages")
    parser.add_argument("--check", action="store_true", help="Check current crop status")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cropped without saving")
    args = parser.parse_args()

    inventory = load_inventory()
    by_page = group_by_page(inventory)

    if args.check:
        ok = 0
        broken = 0
        missing = 0
        for page_num in sorted(by_page.keys()):
            figs = by_page[page_num]
            for fig in figs:
                crop_path = CROP_DIR / fig["expected_crop_name"]
                if crop_path.exists():
                    img = Image.open(crop_path)
                    w, h = img.size
                    if w >= PAGE_WIDTH - 20:
                        broken += 1
                    else:
                        ok += 1
                else:
                    missing += 1
        print(f"Results: {ok} OK, {broken} broken (full-width), {missing} missing — {ok+broken+missing} total")
        return

    if args.page:
        page = args.page
        figs = by_page.get(page, [])
        if not figs:
            print(f"No figures found on page {page}")
            return
        page_path = PAGES_DIR / f"page_{page:03d}.png"
        if not page_path.exists():
            print(f"Page image not found: {page_path}")
            return

        boxes = analyze_page_regions(page_path, expected_figures=len(figs))
        print(f"Page {page}: {len(figs)} figure(s) expected, {len(boxes)} region(s) detected")
        for i, (fig, box) in enumerate(zip(figs, boxes)):
            x, y, w, h = box
            print(f"  fig {fig['fig_number']}: {fig['caption'][:50]}")
            print(f"    box: x={x} y={y} w={w} h={h}")
            if not args.dry_run:
                dest = CROP_DIR / fig["expected_crop_name"]
                size = crop_with_padding(page_path, box, dest)
                print(f"    cropped: {size[0]}x{size[1]} -> {dest.name}")
        return

    if args.all:
        success = 0
        failed = 0
        for page_num in sorted(by_page.keys()):
            figs = by_page[page_num]
            page_path = PAGES_DIR / f"page_{page_num:03d}.png"
            if not page_path.exists():
                print(f"SKIP page {page_num}: image not found")
                failed += len(figs)
                continue

            try:
                boxes = analyze_page_regions(page_path, expected_figures=len(figs))

                if len(boxes) < len(figs):
                    # Not enough regions detected — use a single generous crop for all
                    # Find the overall content extent
                    img = Image.open(page_path).convert('L')
                    # Find first and last content rows
                    first_row = 0
                    last_row = PAGE_HEIGHT - 1
                    for row in range(PAGE_HEIGHT):
                        if any(img.getpixel((col, row)) < 200 for col in range(0, PAGE_WIDTH, 4)):
                            first_row = row
                            break
                    for row in range(PAGE_HEIGHT - 1, -1, -1):
                        if any(img.getpixel((col, row)) < 200 for col in range(0, PAGE_WIDTH, 4)):
                            last_row = row
                            break

                    # Split evenly
                    total_height = last_row - first_row
                    per_fig = total_height // len(figs)
                    boxes = []
                    for i in range(len(figs)):
                        y_start = first_row + i * per_fig
                        y_end = first_row + (i + 1) * per_fig if i < len(figs) - 1 else last_row
                        boxes.append((CONTENT_LEFT, y_start, CONTENT_RIGHT - CONTENT_LEFT, y_end - y_start))

                for fig, box in zip(figs, boxes):
                    dest = CROP_DIR / fig["expected_crop_name"]
                    size = crop_with_padding(page_path, box, dest)
                    status = "OK" if size[0] < PAGE_WIDTH - 20 else "WARN"
                    if status == "OK":
                        success += 1
                    else:
                        failed += 1

                print(f"page {page_num}: {len(figs)} fig(s) -> {', '.join(f['expected_crop_name'] for f in figs)}")
            except Exception as e:
                print(f"ERROR page {page_num}: {e}")
                failed += len(figs)

        print(f"\nDone: {success} OK, {failed} failed out of {len(inventory)} total")
        return

    print("Use --all to process all pages, --page N for a specific page, or --check to audit")


if __name__ == "__main__":
    main()
