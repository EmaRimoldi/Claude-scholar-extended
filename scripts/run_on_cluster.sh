#!/bin/bash
# Universal SLURM job launcher for Claude Scholar projects.
#
# Usage:
#   ./scripts/run_on_cluster.sh <profile> <command> [options]
#
# Profiles: cpu-light, cpu-heavy, gpu-single, gpu-multi, gpu-large
#
# Examples:
#   ./scripts/run_on_cluster.sh gpu-single "python -m src.main"
#   ./scripts/run_on_cluster.sh cpu-heavy "python src/data/benchmark_builder.py"
#   ./scripts/run_on_cluster.sh gpu-single "python -m src.main" --wait
#   ./scripts/run_on_cluster.sh gpu-single "python -m src.main" --test
#   ./scripts/run_on_cluster.sh gpu-multi "torchrun --nproc_per_node=4 src/main.py" --partition mit_preemptable

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <profile> <command> [--wait] [--test] [--partition X] [--gpus N] [--gpu-type T]"
    echo ""
    echo "Profiles: cpu-light, cpu-heavy, gpu-single, gpu-multi, gpu-large"
    exit 1
fi

PROFILE="$1"
COMMAND="$2"
shift 2

# Use Python from the venv if available, else system python3
PYTHON="python3"
if [ -f "$PROJECT_ROOT/rag-lit-synthesis/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/rag-lit-synthesis/.venv/bin/python"
fi

cd "$PROJECT_ROOT"
"$PYTHON" scripts/slurm/submit.py submit --profile "$PROFILE" --command "$COMMAND" "$@"
