#!/usr/bin/env python3
"""Use ZAI MCP image analysis to crop inline figures from page screenshots."""

import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image
from lxml import html
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BOOK_DIR = REPO_ROOT / "book"
PAGES_DIR = BOOK_DIR / "pages"
CROP_DIR = PAGES_DIR / "crops"


def build_inventory() -> Dict[int, List[Dict[str, Any]]]:
    inventory: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for html_path in sorted(BOOK_DIR.glob("*.html")):
        if html_path.name == "index.html":
            continue
        text = html_path.read_text(encoding="utf-8")
        doc = html.fromstring(text)

        for container in doc.xpath('//div[contains(@class, "page-body-container")]'):
            page_id = container.get("id", "")
            match = re.search(r"page-content-(\d+)", page_id)
            if not match:
                continue
            page_num = int(match.group(1))
            figures = container.xpath('./figure[contains(@class, "embedded-figure")]')
            for idx, figure in enumerate(figures, start=1):
                img = figure.xpath('./img[1]')
                if not img:
                    continue
                src = img[0].get("src", "")
                alt = img[0].get("alt", "")
                caption = "".join(figure.xpath('./figcaption//text()')).strip()
                inventory[page_num].append(
                    {
                        "page_num": page_num,
                        "html_path": html_path,
                        "figure_index": idx,
                        "caption": caption,
                        "alt": alt,
                        "src": src,
                        "figure_node": figure,
                    }
                )
    return inventory


def extract_json_array(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    candidate = text
    match = re.search(r"\[\s*\{.*\}\s*\]", text, flags=re.S)
    if match:
        candidate = match.group(0)

    data = json.loads(candidate)
    if isinstance(data, dict):
        return [data]
    return data


async def analyze_page(page_num: int, captions: List[str]) -> List[Dict[str, Any]]:
    image_path = PAGES_DIR / f"page_{page_num:03d}.png"
    if not image_path.exists():
        raise FileNotFoundError(f"Missing page image: {image_path}")

    params = StdioServerParameters(
        command="npx",
        args=["-y", "@z_ai/mcp-server@latest"],
        env={**os.environ, "Z_AI_API_KEY": os.environ.get("Z_AI_API_KEY", ""), "Z_AI_MODE": "ZHIPU"},
    )

    prompt = (
        "Analyze this page image of a Chinese technical book. "
        "Identify every standalone figure/diagram/photo that is an inline figure, not page text or headers. "
        "Return ONLY a JSON array of objects. "
        "Each object must contain: index, x, y, width, height, caption, description. "
        "Use the figure captions below as clues to match each figure. "
        "Order the array from top to bottom, left to right. "
        "Ignore page number, page header, footers, and all paragraph text.\n\n"
        f"Captions:\n- " + "\n- ".join(captions)
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("analyze_image", {"image_source": str(image_path), "prompt": prompt})
            content = result.content[0].text if getattr(result, "content", None) else ""
            data = extract_json_array(content)
            return [
                {
                    "index": int(item.get("index", 1)),
                    "x": int(item.get("x", 0)),
                    "y": int(item.get("y", 0)),
                    "width": int(item.get("width", 0)),
                    "height": int(item.get("height", 0)),
                    "caption": str(item.get("caption", ""))
                }
                for item in data
                if item.get("x") is not None and item.get("y") is not None
            ]


def crop_figure(image_path: Path, box: Dict[str, Any], dest_path: Path) -> None:
    with Image.open(image_path) as img:
        x = max(0, int(box["x"]) - 4)
        y = max(0, int(box["y"]) - 4)
        w = int(box["width"]) + 8
        h = int(box["height"]) + 8
        crop = img.crop((x, y, min(img.width, x + w), min(img.height, y + h)))
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(dest_path)


def update_html(inventory: Dict[int, List[Dict[str, Any]]], detections: Dict[int, List[Dict[str, Any]]]) -> int:
    replacements = 0
    html_docs: Dict[Path, Any] = {}

    for page_num, figures in inventory.items():
        boxes = detections.get(page_num, [])
        if not boxes:
            print(f"SKIP page {page_num}: no MCP detection result")
            continue

        for figure_info in figures:
            idx = figure_info["figure_index"] - 1
            if idx >= len(boxes):
                print(f"WARN page {page_num}: only {len(boxes)} boxes returned, figure {idx + 1} unsafely mapped")
                continue

            box = boxes[idx]
            dest_path = CROP_DIR / f"page_{page_num:03d}_fig{figure_info['figure_index']}.png"
            if not dest_path.exists():
                crop_figure(PAGES_DIR / f"page_{page_num:03d}.png", box, dest_path)
                print(f"CROP page {page_num} fig {figure_info['figure_index']} -> {dest_path}")

            if figure_info["html_path"] not in html_docs:
                html_docs[figure_info["html_path"]] = html.fromstring(figure_info["html_path"].read_text(encoding="utf-8"))

            doc = html_docs[figure_info["html_path"]]
            page_container = doc.xpath(f'//div[@id="page-content-{page_num}"]')[0]
            figure_nodes = page_container.xpath('./figure[contains(@class, "embedded-figure")]')
            target_figure = figure_nodes[figure_info["figure_index"] - 1]
            target_img = target_figure.find("./img")
            if target_img is not None:
                target_img.set("src", f"pages/crops/page_{page_num:03d}_fig{figure_info['figure_index']}.png")
                replacements += 1

    for html_path, doc in html_docs.items():
        html_path.write_text(html.tostring(doc, encoding="unicode", pretty_print=True), encoding="utf-8")

    return replacements


async def main() -> None:
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    detections: Dict[int, List[Dict[str, Any]]] = {}

    for page_num, figures in sorted(inventory.items()):
        captions = [item["caption"] or item["alt"] for item in figures if item["caption"] or item["alt"]]
        if not captions:
            print(f"SKIP page {page_num}: no captions found")
            continue
        try:
            detections[page_num] = await analyze_page(page_num, captions)
            print(f"ANALYZED page {page_num}: {len(detections[page_num])} figure(s)")
        except Exception as exc:
            print(f"ERROR page {page_num}: {exc}", file=sys.stderr)

    replacements = update_html(inventory, detections)
    print(f"Done. Updated {replacements} figure image references.")


if __name__ == "__main__":
    asyncio.run(main())
