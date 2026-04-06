#!/bin/bash
# Run remaining pipeline steps after Wave 1 and Wave 2 training complete.
# This includes:
#   - Phase 3: Attribution analysis (IG, LIME)
#   - Phase 4: Statistical analysis (metrics, tests, power)
#   - Phase 5: Adversarial analysis (attention swap, agreement)
#   - Result collection and aggregation

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cd "$PROJECT_DIR"

log "=== Running Remaining Pipeline Phases ==="

# Validate training outputs exist
log "Checking Phase 2 training outputs..."
for condition in M0 M1 M3 M4b M2 M4a M4c M5 M6 M7; do
    for seed in 42 43 44; do
        if [[ ! -d "outputs/${condition}/seed${seed}" ]]; then
            log "ERROR: Missing outputs/${condition}/seed${seed}"
            exit 1
        fi
    done
done
log "✓ All Phase 2 outputs found"

# Phase 3: Attribution analysis
log "=== Phase 3: Attribution Analysis ==="
if $PYTHON scripts/phase3_attributions.py; then
    log "✓ Phase 3 complete"
else
    log "✗ Phase 3 failed"
    exit 1
fi

# Phase 4: Statistical analysis
log "=== Phase 4: Statistical Analysis ==="
if $PYTHON scripts/phase4_statistics.py; then
    log "✓ Phase 4 complete"
else
    log "✗ Phase 4 failed"
    exit 1
fi

# Phase 5: Adversarial analysis
log "=== Phase 5: Adversarial Analysis ==="
if $PYTHON scripts/phase5_adversarial.py; then
    log "✓ Phase 5 complete"
else
    log "✗ Phase 5 failed (non-fatal, may require manual implementation)"
fi

# Collect results
log "=== Collecting Results ==="
if $PYTHON scripts/collect_results.py; then
    log "✓ Results collected"
else
    log "✗ Result collection failed"
    exit 1
fi

log "=== Pipeline Phases 3-5 Complete ==="
log "Next steps:"
log "  1. Review results in results/ and outputs/phase*/"
log "  2. Run manuscript generation steps"
log "  3. Prepare figures and tables for paper"

exit 0
