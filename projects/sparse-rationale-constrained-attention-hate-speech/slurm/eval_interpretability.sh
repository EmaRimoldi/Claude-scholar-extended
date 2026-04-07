#!/bin/bash
#SBATCH --job-name=sprattn_eval
#SBATCH --partition=mit_normal_gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=logs/slurm_eval_%j.out
#SBATCH --error=logs/slurm_eval_%j.err

# Interpretability evaluation: ERASER + faithfulness + plausibility
# Runs all 5 conditions × 5 seeds on the test set.

set -e
echo "=== ALETHEIA interpretability eval ==="
echo "Host: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)"
echo "Started: $(date)"

REPO_ROOT="/home/erimoldi/projects/Claude-scholar-extended"
PROJECT_DIR="$REPO_ROOT/projects/sparse-rationale-constrained-attention-hate-speech"
PYTHON="$REPO_ROOT/.venv/bin/python"

cd "$PROJECT_DIR"

export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

echo ""
echo "[1/1] Running interpretability evaluation..."
$PYTHON scripts/eval_interpretability.py \
    --device cuda \
    --conditions C1 C2 C3 C4 C5

echo ""
echo "Finished: $(date)"
echo "Results written to results/tables/"
ls -la results/tables/*.csv results/tables/*.json 2>/dev/null
