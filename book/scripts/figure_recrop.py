#!/usr/bin/env python3
"""Re-crop figures with improved AI vision prompts and validation.

All 159 existing crops are broken -- they're full-width horizontal strips
that truncate figures. This script provides utilities for re-cropping with
tight bounding boxes and validation.

Usage:
    python3 book/scripts/figure_recrop.py              # summary & usage hints
    python3 book/scripts/figure_recrop.py --check       # audit all existing crops
    python3 book/scripts/figure_recrop.py --page 20     # per-page figure info
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BOOK_DIR = REPO_ROOT / "book"
PAGES_DIR = BOOK_DIR / "pages"
CROP_DIR = PAGES_DIR / "crops"
INVENTORY_PATH = BOOK_DIR / "scripts" / "figure_inventory.json"

# Page image dimensions
PAGE_WIDTH = 1190
PAGE_HEIGHT = 1684

# Validation thresholds
FULL_WIDTH_THRESHOLD = 1170  # crops >= this width are "broken" (full-width strips)
MIN_AREA = 10000  # minimum bounding box area in pixels^2
CROP_PADDING = 8  # pixels of padding around tight bounding box


def load_inventory() -> List[Dict[str, Any]]:
    """Load figure_inventory.json and return list of figure entries."""
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def group_by_page(entries: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Group figure entries by their page number.

    Returns dict mapping page number -> list of figure entries for that page.
    """
    pages: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        pages[entry["page"]].append(entry)
    return pages


def build_vision_prompt(page_num: int, captions: List[str]) -> str:
    """Build an AI vision prompt requesting TIGHT bounding boxes.

    The prompt emphasizes that bounding boxes must NOT span the full page
    width, must be tight around figure content including captions, and must
    exclude headers/footers/page numbers.
    """
    caption_list = "\n".join(f"  - {c}" for c in captions)
    return f"""Analyze this page image ({PAGE_WIDTH}x{PAGE_HEIGHT} pixels) from a Chinese technical book.

CRITICAL RULES for bounding boxes:
1. Bounding boxes MUST be TIGHT around the actual figure content — do NOT span the full {PAGE_WIDTH}px page width. Figures have margins and do not touch the page edges.
2. Include the figure caption (图X-X ...) as part of the bounding box area.
3. EXCLUDE page numbers, page headers, and page footers from bounding boxes.
4. EXCLUDE body text paragraphs — only capture standalone figures/diagrams/photos.
5. The typical figure is centered with generous margins, so width should rarely exceed 900px.
6. Order figures top-to-bottom, left-to-right.

Return ONLY a JSON array. Each object must have:
  - "index": 1-based figure index on this page
  - "x": left edge in pixels (should be > 50, NOT near 0)
  - "y": top edge in pixels
  - "width": width in pixels (should be < {PAGE_WIDTH}, typically 400-900)
  - "height": height in pixels
  - "caption": the figure caption text found on the page
  - "confidence": "high", "medium", or "low"

Expected figures on this page (use as clues to locate them):
{caption_list}

IMPORTANT: A bounding box with x near 0 and width near {PAGE_WIDTH} is WRONG.
Figures are centered on the page with significant left/right margins."""


def parse_vision_response(text: str) -> List[Dict[str, Any]]:
    """Parse AI vision response, handling markdown code blocks and extracting JSON.

    Handles responses that may be wrapped in ```json ... ``` blocks,
    or contain other text around the JSON array.
    """
    text = text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Try to find a JSON array in the text
    match = re.search(r"\[\s*\{.*?\}\s*\]", text, flags=re.S)
    if match:
        candidate = match.group(0)
    else:
        candidate = text

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse vision response as JSON: {e}\nText: {candidate[:500]}")

    # Normalize single dict to list
    if isinstance(data, dict):
        data = [data]

    # Validate and normalize each entry
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "x" not in item or "y" not in item:
            continue
        results.append({
            "index": int(item.get("index", 1)),
            "x": int(item["x"]),
            "y": int(item["y"]),
            "width": int(item.get("width", 0)),
            "height": int(item.get("height", 0)),
            "caption": str(item.get("caption", "")),
            "confidence": str(item.get("confidence", "medium")),
        })
    return results


def validate_crop(box: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a bounding box. Returns (is_valid, reason).

    Rejects:
      - Full-width strips (width >= FULL_WIDTH_THRESHOLD)
      - Too small (area < MIN_AREA)
      - Invalid dimensions (zero or negative width/height)
      - Negative coordinates
      - Boxes extending beyond page bounds
    """
    x = box.get("x", 0)
    y = box.get("y", 0)
    w = box.get("width", 0)
    h = box.get("height", 0)

    if x < 0:
        return False, f"negative x={x}"
    if y < 0:
        return False, f"negative y={y}"
    if w <= 0:
        return False, f"non-positive width={w}"
    if h <= 0:
        return False, f"non-positive height={h}"

    area = w * h
    if area < MIN_AREA:
        return False, f"area too small ({area}px^2 < {MIN_AREA}px^2)"

    if w >= FULL_WIDTH_THRESHOLD:
        return False, f"full-width strip (width={w} >= {FULL_WIDTH_THRESHOLD})"

    if x + w > PAGE_WIDTH:
        return False, f"extends beyond page width (x={x} + w={w} = {x+w} > {PAGE_WIDTH})"
    if y + h > PAGE_HEIGHT:
        return False, f"extends beyond page height (y={y} + h={h} = {y+h} > {PAGE_HEIGHT})"

    return True, "OK"


def crop_image(page_path: Path, box: Dict[str, Any], dest_path: Path) -> None:
    """Crop a figure from a page image with padding, clamped to page bounds.

    Uses CROP_PADDING (8px) padding around the tight bounding box.
    Clamps coordinates so the crop stays within page dimensions.
    """
    with Image.open(page_path) as img:
        x = max(0, int(box["x"]) - CROP_PADDING)
        y = max(0, int(box["y"]) - CROP_PADDING)
        right = min(img.width, int(box["x"]) + int(box["width"]) + CROP_PADDING)
        bottom = min(img.height, int(box["y"]) + int(box["height"]) + CROP_PADDING)

        if right <= x or bottom <= y:
            raise ValueError(f"Invalid crop region: ({x},{y})-({right},{bottom})")

        cropped = img.crop((x, y, right, bottom))
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dest_path)


def check_existing_crop(crop_path: Path) -> Tuple[bool, str]:
    """Check if an existing crop file is broken (full-width strip).

    Returns (is_valid, reason).
    """
    if not crop_path.exists():
        return False, "missing"

    try:
        with Image.open(crop_path) as img:
            w, h = img.size
            if w >= FULL_WIDTH_THRESHOLD:
                return False, f"broken (full-width strip: {w}x{h})"
            if w * h < MIN_AREA:
                return False, f"too small ({w}x{h} = {w*h}px^2)"
            return True, f"OK ({w}x{h})"
    except Exception as e:
        return False, f"error reading: {e}"


def cmd_check(entries: List[Dict[str, Any]]) -> None:
    """Audit all existing crops, report OK vs broken count."""
    ok_count = 0
    broken_count = 0
    missing_count = 0

    for entry in entries:
        crop_path = CROP_DIR / entry["expected_crop_name"]
        is_valid, reason = check_existing_crop(crop_path)

        if reason == "missing":
            missing_count += 1
        elif is_valid:
            ok_count += 1
        else:
            broken_count += 1
            print(f"  BROKEN  {entry['expected_crop_name']}: {reason}")

    print(f"\nCrop audit complete:")
    print(f"  Total:   {len(entries)}")
    print(f"  OK:      {ok_count}")
    print(f"  Broken:  {broken_count}")
    print(f"  Missing: {missing_count}")

    if broken_count + missing_count > 0:
        print(f"\n  {broken_count + missing_count} crops need re-cropping.")


def cmd_page(page_num: int, entries: List[Dict[str, Any]],
             pages: Dict[int, List[Dict[str, Any]]]) -> None:
    """Show info about a specific page's figures and check existing crops."""
    page_image = PAGES_DIR / f"page_{page_num:03d}.png"
    print(f"Page {page_num}")
    print(f"  Page image: {page_image} ({'exists' if page_image.exists() else 'MISSING'})")

    if page_image.exists():
        with Image.open(page_image) as img:
            print(f"  Page dimensions: {img.size[0]}x{img.size[1]}")

    page_entries = pages.get(page_num, [])
    if not page_entries:
        print(f"  No figures on this page in inventory.")
        return

    print(f"  Figures on this page: {len(page_entries)}")
    for entry in page_entries:
        crop_path = CROP_DIR / entry["expected_crop_name"]
        is_valid, reason = check_existing_crop(crop_path)
        status = "OK" if is_valid else "BROKEN"
        print(f"    [{status}] {entry['expected_crop_name']}: {reason}")
        print(f"           Caption: {entry['caption']}")

    # Show the vision prompt for this page
    captions = [e["caption"] for e in page_entries]
    prompt = build_vision_prompt(page_num, captions)
    print(f"\n  --- Vision prompt for page {page_num} ---")
    print(prompt)
    print(f"  --- End prompt ---\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-crop figures with improved AI vision prompts and validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 book/scripts/figure_recrop.py              # summary & usage hints
  python3 book/scripts/figure_recrop.py --check       # audit all existing crops
  python3 book/scripts/figure_recrop.py --page 20     # info about page 20's figures
        """,
    )
    parser.add_argument("--page", type=int, metavar="N", help="Show info for page N")
    parser.add_argument("--check", action="store_true", help="Audit all existing crops")

    args = parser.parse_args()

    entries = load_inventory()
    pages = group_by_page(entries)

    if args.check:
        cmd_check(entries)
        return

    if args.page is not None:
        cmd_page(args.page, entries, pages)
        return

    # Default: print summary and usage hints
    print(f"Figure Re-Crop Tool")
    print(f"{'=' * 50}")
    print(f"Inventory: {len(entries)} figures across {len(pages)} pages")
    print(f"Crop directory: {CROP_DIR}")
    print(f"Existing crops: {len(list(CROP_DIR.glob('*.png')))} files")
    print(f"Page dimensions: {PAGE_WIDTH}x{PAGE_HEIGHT}")
    print(f"Full-width threshold: {FULL_WIDTH_THRESHOLD}px")
    print()
    print(f"Usage:")
    print(f"  --check     Audit all existing crops")
    print(f"  --page N    Show info about page N's figures")
    print()
    print(f"Pages with figures: {', '.join(str(p) for p in sorted(pages.keys()))}")


if __name__ == "__main__":
    main()
