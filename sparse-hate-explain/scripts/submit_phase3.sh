#!/bin/bash
# Submit Phase 3 (sparsemax experiments) and Phase 4 (lambda ablation) to SLURM
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLUSTER_SCRIPT="${PROJECT_ROOT}/../scripts/run_on_cluster.sh"

SEEDS=(42 123 456)
HEAD_IMPORTANCE="${PROJECT_ROOT}/results/head_importance/head_importance.json"

if [ ! -f "$HEAD_IMPORTANCE" ]; then
    echo "ERROR: Head importance results not found at ${HEAD_IMPORTANCE}"
    echo "Run head importance analysis first: bash scripts/run_head_importance.sh"
    exit 1
fi

echo "=== Phase 3: Sparsemax Experiments ==="
for seed in "${SEEDS[@]}"; do
    echo "Submitting sparsemax_all seed=${seed}"
    "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh sparsemax_all ${seed}"

    for K in 12 24 36; do
        echo "Submitting sparsemax_topk K=${K} seed=${seed}"
        "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh sparsemax_topk ${seed} model.top_k=${K}"
    done

    echo "Submitting softmax_top24 seed=${seed}"
    "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh sparsemax_topk ${seed} model.attention_transform=softmax model.top_k=24"

    echo "Submitting sparsemax_top24_strong seed=${seed}"
    "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh sparsemax_topk ${seed} model.top_k=24 model.lambda_attn=2.0"
done

echo ""
echo "=== Phase 4: Lambda Ablation ==="
for seed in "${SEEDS[@]}"; do
    for LAMBDA in 0.1 0.5 1.0 2.0; do
        echo "Submitting sparsemax_topk K=24 lambda=${LAMBDA} seed=${seed}"
        "$CLUSTER_SCRIPT" gpu-single "cd ${PROJECT_ROOT} && bash scripts/run_experiment.sh sparsemax_topk ${seed} model.top_k=24 model.lambda_attn=${LAMBDA}"
    done
done

echo ""
echo "=== All phases submitted ==="
