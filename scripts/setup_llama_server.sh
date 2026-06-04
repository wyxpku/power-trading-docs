#!/bin/bash
set -e

echo "=== Step 1: Install llama.cpp ==="
if command -v llama-server &>/dev/null; then
    echo "llama-server already installed: $(which llama-server)"
else
    echo "Installing llama.cpp via brew..."
    brew install llama.cpp
    echo "Done."
fi

echo ""
echo "=== Step 2: Download GGUF model ==="
MODEL_DIR="$HOME/models/PaddleOCR-VL-1.6-GGUF"
mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_DIR/PaddleOCR-VL-1.6-GGUF.gguf" ]; then
    echo "Model already exists at $MODEL_DIR"
else
    echo "Installing huggingface-cli..."
    pip install huggingface_hub
    echo "Downloading PaddleOCR-VL-1.6 GGUF model (may take several minutes)..."
    hf download PaddlePaddle/PaddleOCR-VL-1.6-GGUF --local-dir "$MODEL_DIR"
    echo "Download complete."
fi

echo ""
echo "=== Model files ==="
ls -lh "$MODEL_DIR/"*.gguf

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To START the llama-server (run in a separate terminal):"
echo "  llama-server \\"
echo "    -m $MODEL_DIR/PaddleOCR-VL-1.6-GGUF.gguf \\"
echo "    --mmproj $MODEL_DIR/PaddleOCR-VL-1.6-GGUF-mmproj.gguf \\"
echo "    --port 8080 --host 0.0.0.0 --temp 0"
echo ""
echo "Then run the conversion with:"
echo "  .venv/bin/python book/scripts/paddleocr_run.py"
