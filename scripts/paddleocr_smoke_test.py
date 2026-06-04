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
