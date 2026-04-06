#!/bin/bash
# Automatic Wave 2 submission after Wave 1 completion.
# Call this script once Wave 1 jobs (11480518, 11480519) have completed.
#
# Usage:
#   ./scripts/submit_wave2_auto.sh
#
# Or to monitor Wave 1 and auto-submit Wave 2:
#   watch -n 60 'squeue -j 11480518,11480519; echo "---"; \
#     if ! squeue -j 11480518,11480519 | grep -q .; then \
#       echo "Wave 1 complete. Submitting Wave 2..."; \
#       ./scripts/submit_wave2_auto.sh; \
#     fi'

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cd "$PROJECT_DIR"

log "=== Wave 2 Automatic Submission ==="

# Check that Wave 1 outputs exist
log "Verifying Wave 1 outputs..."
for condition in M0 M1 M3 M4b; do
    for seed in 42 43 44; do
        output_dir="outputs/${condition}/seed${seed}"
        if [[ ! -d "$output_dir" ]]; then
            log "ERROR: Missing Wave 1 output: $output_dir"
            log "Wave 1 may not have completed yet. Check with: squeue -j 11480518,11480519"
            exit 1
        fi
    done
done
log "✓ All Wave 1 outputs verified"

# Run pre-flight validation before submitting Wave 2
log "Running pre-flight validation..."
if ! $PYTHON scripts/validate_train.py; then
    log "ERROR: Pre-flight validation failed"
    exit 1
fi
log "✓ Validation passed"

# Submit Wave 2 jobs
log "Submitting Wave 2 jobs..."
mkdir -p logs

log "  Submitting: M2 + M4a"
WAVE2_JOB1=$(sbatch scripts/train.sh --conditions M2 M4a | awk '{print $NF}')
log "  → Job ID: $WAVE2_JOB1"

sleep 2

log "  Submitting: M4c + M5"
WAVE2_JOB2=$(sbatch scripts/train.sh --conditions M4c M5 | awk '{print $NF}')
log "  → Job ID: $WAVE2_JOB2"

sleep 2

log "  Submitting: M6 + M7"
WAVE2_JOB3=$(sbatch scripts/train.sh --conditions M6 M7 | awk '{print $NF}')
log "  → Job ID: $WAVE2_JOB3"

log "=== Wave 2 Submission Complete ==="
log "Job IDs: $WAVE2_JOB1, $WAVE2_JOB2, $WAVE2_JOB3"
log ""
log "Monitor Wave 2 with:"
log "  squeue -j $WAVE2_JOB1,$WAVE2_JOB2,$WAVE2_JOB3"
log ""
log "Once all Wave 2 jobs complete, run:"
log "  ./scripts/run_remaining_pipeline.sh"

exit 0
