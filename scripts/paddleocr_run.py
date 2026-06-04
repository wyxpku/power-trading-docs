#!/usr/bin/env python3
"""Run PaddleOCR-VL on individual page images and save per-page results.

Processes page_NNN.png images one at a time for incremental saving and
progress tracking. Supports llama-server backend for acceleration.

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
PAGES_DIR = REPO_ROOT / "book" / "pages"
OUTPUT_DIR = REPO_ROOT / "book" / "scripts" / "paddleocr_output"
TOTAL_PAGES = 647  # page_001.png through page_647.png

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
        if d.is_dir() and d.name not in ("restructured", "smoke_test") and list(d.glob("*.json")):
            try:
                page_idx = int(d.name.split("_")[1])
                completed.add(page_idx)
            except (ValueError, IndexError):
                pass
    return completed


def main():
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

    start_time = time.time()
    processed = 0
    errors = 0

    for page_num in range(1, TOTAL_PAGES + 1):
        page_idx = page_num - 1  # 0-indexed
        page_image = PAGES_DIR / f"page_{page_num:03d}.png"

        if not page_image.exists():
            print(f"  SKIP page {page_num}: image not found")
            continue

        if page_idx in completed:
            processed += 1
            continue

        # Process single page image
        try:
            output = list(pipeline.predict(input=str(page_image)))
            if output:
                res = output[0]
                page_dir = OUTPUT_DIR / f"page_{page_idx:04d}"
                page_dir.mkdir(parents=True, exist_ok=True)
                try:
                    res.save_to_json(save_path=str(page_dir))
                except Exception as e:
                    print(f"  ERROR saving page {page_num} JSON: {e}", file=sys.stderr)
                    errors += 1
        except Exception as e:
            print(f"  ERROR processing page {page_num}: {e}", file=sys.stderr)
            errors += 1
            continue

        processed += 1
        elapsed = time.time() - start_time
        new_pages = processed - len(completed)

        if new_pages <= 3 or processed % 20 == 0:
            rate = elapsed / new_pages if new_pages > 0 else 0
            remaining_pages = TOTAL_PAGES - processed
            remaining = rate * remaining_pages
            print(f"  {processed}/{TOTAL_PAGES} pages ({elapsed:.0f}s elapsed, "
                  f"~{remaining/60:.0f}min remaining, {rate:.1f}s/page)")

    elapsed = time.time() - start_time
    new_pages = processed - len(completed)
    print(f"\nProcessed {new_pages} new pages in {elapsed:.0f}s "
          f"({elapsed/new_pages:.1f}s/page)" if new_pages > 0 else "")
    if errors:
        print(f"Errors: {errors}")

    print(f"\nDone! Results in {OUTPUT_DIR}")
    total_dirs = len([d for d in OUTPUT_DIR.glob("page_*")
                      if d.is_dir() and d.name not in ("restructured", "smoke_test")])
    print(f"Page dirs: {total_dirs}")


if __name__ == "__main__":
    main()
