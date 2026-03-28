#!/bin/bash
# Submit all experiment phases to SLURM
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLUSTER_SCRIPT="${PROJECT_ROOT}/../scripts/run_on_cluster.sh"

SEEDS=(42 123 456)

echo "=== Phase 1: Baselines ==="
for seed in "${SEEDS[@]}"; do
    echo "Submitting vanilla seed=${seed}"
    "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh vanilla ${seed}"
    echo "Submitting softmax_all seed=${seed}"
    "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh softmax_all ${seed}"
    echo "Submitting softmax_all_strong seed=${seed} (lambda=2.0)"
    "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh softmax_all ${seed} model.lambda_attn=2.0"
done

echo ""
echo "=== Phase 1 submitted. Wait for completion, then run head importance, then Phase 3. ==="
echo "After Phase 1: bash scripts/run_head_importance.sh"
echo "After head importance: bash scripts/submit_phase3.sh"
