#!/bin/bash
# Download HateXplain dataset and BERT model weights (run on login node)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CACHE_DIR="${PROJECT_ROOT}/data/cache"

mkdir -p "$CACHE_DIR"

# Activate venv
if [ -f "$PROJECT_ROOT/../.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/../.venv/bin/activate"
elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

echo "=== Downloading HateXplain dataset ==="
python3 -c "
from datasets import load_dataset
ds = load_dataset('hatexplain', cache_dir='${CACHE_DIR}')
print(f'Train: {len(ds[\"train\"])}, Val: {len(ds[\"validation\"])}, Test: {len(ds[\"test\"])}')
print('Dataset downloaded successfully.')
"

echo "=== Downloading bert-base-uncased model ==="
python3 -c "
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', cache_dir='${CACHE_DIR}')
model = AutoModel.from_pretrained('bert-base-uncased', cache_dir='${CACHE_DIR}')
print('Model downloaded successfully.')
"

echo "=== All downloads complete ==="
