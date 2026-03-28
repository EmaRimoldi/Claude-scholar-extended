#!/usr/bin/env bash
# Wrapper script to run the RAG literature synthesis experiment.
# Activates the venv and launches the main entry point.
#
# Usage:
#   ./scripts/run_experiment.sh              # full run
#   ./scripts/run_experiment.sh --dry-run    # structure check
#   ./scripts/run_experiment.sh --build-data # download data only
#   ./scripts/run_experiment.sh --no-bert    # skip BERTScore

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated venv: $(python --version)"
else
    echo "ERROR: No .venv found in $PROJECT_DIR"
    exit 1
fi

# Create log directory
LOG_DIR="${PROJECT_DIR}/../logs/pipeline-$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR"

echo "Running experiment from: $PROJECT_DIR"
echo "Log directory: $LOG_DIR"
echo "Arguments: $*"
echo "---"

python -m src.main --log-dir "$LOG_DIR" "$@"
