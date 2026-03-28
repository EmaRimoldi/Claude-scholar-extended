#!/bin/bash
# Run head importance analysis on best vanilla model
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
if [ -f "../.venv/bin/activate" ]; then
    source "../.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

CACHE_DIR="${PROJECT_ROOT}/data/cache"

echo "=== Running head importance analysis ==="
python3 -m src.main \
    +experiment=vanilla \
    mode=head_importance \
    data.cache_dir="${CACHE_DIR}" \
    output_dir="${PROJECT_ROOT}/results/head_importance"

echo "=== Head importance complete ==="
echo "Results saved to: ${PROJECT_ROOT}/results/head_importance/"
