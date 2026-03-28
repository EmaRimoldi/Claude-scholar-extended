#!/bin/bash
# Run a single experiment condition with a given seed
# Usage: ./scripts/run_experiment.sh <experiment_config> <seed> [extra_overrides...]
# Example: ./scripts/run_experiment.sh sparsemax_topk 42 model.supervised_heads=top12
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <experiment_config> <seed> [extra_overrides...]"
    echo "Configs: vanilla, softmax_all, sparsemax_all, sparsemax_topk"
    exit 1
fi

EXPERIMENT="$1"
SEED="$2"
shift 2

cd "$PROJECT_ROOT"

# Activate venv
if [ -f "../.venv/bin/activate" ]; then
    source "../.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

CACHE_DIR="${PROJECT_ROOT}/data/cache"
OUTPUT_DIR="${PROJECT_ROOT}/results/${EXPERIMENT}_seed${SEED}"
mkdir -p "$OUTPUT_DIR"

echo "=== Running experiment: ${EXPERIMENT} seed=${SEED} ==="
echo "Output: ${OUTPUT_DIR}"

python3 -m src.main \
    +experiment="${EXPERIMENT}" \
    seed="${SEED}" \
    data.cache_dir="${CACHE_DIR}" \
    output_dir="${OUTPUT_DIR}" \
    "$@"

echo "=== Experiment complete: ${EXPERIMENT} seed=${SEED} ==="
