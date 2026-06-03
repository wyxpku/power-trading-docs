#!/usr/bin/env python3
"""Run PaddleOCR-VL on the full PDF and save per-page results.

Supports two modes:
  1. llama-server backend (fast, ~16s/page on Apple Silicon):
     - Start llama-server first (see setup_llama_server.sh)
     - Uses --vl_rec_backend llama-cpp-server + --vl_rec_server_url
  2. Pure CPU mode (slow, ~99s/page):
     - Fallback when no server is running

Results are saved incrementally — if interrupted, already-saved pages
are skipped on re-run.
"""
import json
import sys
import time
from pathlib import Path
from paddleocr import PaddleOCRVL

# Force unbuffered output so print() shows in nohup logs immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PDF_PATH = REPO_ROOT / "docs" / "电力现货市场实务 (国家电力调度控制中心组编) (Z-Library).pdf"
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"

# llama-server config
LLAMA_SERVER_URL = "http://127.0.0.1:8080/v1"
LLAMA_BACKEND = "llama-cpp-server"


def check_llama_server():
    """Check if llama-server is running and reachable."""
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"{LLAMA_SERVER_URL.rsplit('/v1', 1)[0]}/health", timeout=3)
        return resp.status == 200
    except Exception:
        return False


def get_completed_pages():
    """Find pages that have already been processed."""
    completed = set()
    for d in OUTPUT_DIR.glob("page_*"):
        if d.is_dir() and d.name != "restructured" and d.name != "smoke_test" and list(d.glob("*.json")):
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

    # Determine backend
    use_llama = check_llama_server()
    if use_llama:
        print(f"llama-server detected at {LLAMA_SERVER_URL}")
        print("Initializing PaddleOCR-VL with llama-server backend...")
        pipeline = PaddleOCRVL(
            device="cpu",
            vl_rec_backend=LLAMA_BACKEND,
            vl_rec_server_url=LLAMA_SERVER_URL,
        )
    else:
        print("No llama-server detected, falling back to pure CPU mode.")
        print("WARNING: Pure CPU mode is ~99s/page (~17h total).")
        print("For acceleration, run setup_llama_server.sh first.")
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

        if (i + 1) % 20 == 0 or i < 3:
            elapsed = time.time() - start_time
            rate = elapsed / (i + 1)
            remaining = rate * (646 - i - 1)
            print(f"  {i+1}/646 pages ({elapsed:.0f}s elapsed, ~{remaining/60:.0f}min remaining, {rate:.1f}s/page)")

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
