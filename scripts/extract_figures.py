#!/usr/bin/env python3
"""Extract figures from page images using PaddleOCR-VL bounding boxes.

For each page, finds blocks with block_label == "image" and crops the
region from the page image with padding. Also updates the JSON files
with crop_path references for the HTML conversion step.

Adapted to actual PaddleOCR-VL-1.6 output format:
  - block_label "image" for figure regions
  - block_label "figure_title" for figure captions (separate block)
  - bbox format: [x1, y1, x2, y2]
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

        # Collect figure titles for caption matching
        fig_titles = {}
        for block in blocks:
            if block.get("block_label") == "figure_title":
                bbox_raw = block.get("block_bbox")
                content = str(block.get("block_content", "")).strip()
                if bbox_raw and content:
                    fig_titles[id(block)] = content

        for block in blocks:
            label = block.get("block_label", "")
            if label != "image":
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
