#!/usr/bin/env python3
"""Scan all HTML files in book/ and output a JSON inventory of every embedded figure."""

import glob
import json
import os
import re
from html.parser import HTMLParser

BOOK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTML_GLOB = os.path.join(BOOK_DIR, "chapter_*.html")


class FigureCollector(HTMLParser):
    """Parse an HTML file and collect all embedded figures grouped by page."""

    def __init__(self):
        super().__init__()
        self.figures = []
        self._current_page = None
        self._in_figure = False
        self._in_caption = False
        self._current_fig = {}
        self._caption_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "div":
            div_id = attrs_dict.get("id", "")
            m = re.match(r"page-content-(\d+)", div_id)
            if m:
                self._current_page = int(m.group(1))

        if tag == "figure" and "embedded-figure" in attrs_dict.get("class", ""):
            self._in_figure = True
            self._current_fig = {
                "page": self._current_page,
                "src": "",
                "alt": "",
                "caption": "",
            }
            self._caption_text = ""
            return

        if self._in_figure:
            if tag == "img":
                self._current_fig["src"] = attrs_dict.get("src", "")
                self._current_fig["alt"] = attrs_dict.get("alt", "")
            if tag == "figcaption":
                self._in_caption = True
                self._caption_text = ""

    def handle_endtag(self, tag):
        if not self._in_figure:
            return
        if tag == "figcaption":
            self._in_caption = False
            self._current_fig["caption"] = self._caption_text.strip()
        if tag == "figure":
            self._in_figure = False
            self.figures.append(self._current_fig)
            self._current_fig = {}

    def handle_data(self, data):
        if self._in_caption:
            self._caption_text += data


def collect_figures_from_file(filepath):
    """Parse one HTML file and return its list of figure dicts."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    parser = FigureCollector()
    parser.feed(content)
    return parser.figures


def build_inventory():
    """Scan all HTML files and return the full figure inventory."""
    html_files = sorted(glob.glob(HTML_GLOB))
    # Also include preface and appendix files
    for pattern in ["preface.html", "appendix_*.html"]:
        html_files.extend(sorted(glob.glob(os.path.join(BOOK_DIR, pattern))))
    html_files.sort()

    all_figures = []

    for filepath in html_files:
        basename = os.path.basename(filepath)
        figures = collect_figures_from_file(filepath)

        # Group by page to assign fig_index_on_page
        page_counters = {}
        for fig in figures:
            page = fig["page"]
            if page not in page_counters:
                page_counters[page] = 0
            page_counters[page] += 1
            fig_index = page_counters[page]

            fig_number = fig_index  # 1-based, unique per page
            page_str = f"{page:03d}"
            expected_crop_name = f"page_{page_str}_fig{fig_number}.png"
            expected_crop_path = f"pages/crops/{expected_crop_name}"

            all_figures.append({
                "page": page,
                "fig_index_on_page": fig_index,
                "fig_number": fig_number,
                "src": fig["src"],
                "alt": fig["alt"],
                "caption": fig["caption"],
                "html_file": basename,
                "expected_crop_name": expected_crop_name,
                "expected_crop_path": expected_crop_path,
            })

    return all_figures


def print_summary(inventory):
    """Print summary statistics to stderr."""
    import sys

    total = len(inventory)
    pages_with_figs = set(f["page"] for f in inventory)
    num_pages = len(pages_with_figs)

    # Count multi-fig pages
    from collections import Counter
    page_counts = Counter(f["page"] for f in inventory)
    multi_fig_pages = sum(1 for c in page_counts.values() if c > 1)

    # Check src vs expected mismatches
    mismatches = sum(
        1 for f in inventory if f["src"] != f["expected_crop_path"]
    )

    print(f"Total figures: {total}", file=sys.stderr)
    print(f"Pages with figures: {num_pages}", file=sys.stderr)
    print(f"Multi-figure pages: {multi_fig_pages}", file=sys.stderr)
    print(f"Src/expected mismatches: {mismatches}", file=sys.stderr)

    # Distribution of figures per page
    dist = Counter(page_counts.values())
    print("\nFigures-per-page distribution:", file=sys.stderr)
    for count in sorted(dist.keys()):
        print(f"  {count} figure(s): {dist[count]} pages", file=sys.stderr)


def main():
    inventory = build_inventory()
    # JSON to stdout, summary to stderr
    print_summary(inventory)
    print(json.dumps(inventory, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
