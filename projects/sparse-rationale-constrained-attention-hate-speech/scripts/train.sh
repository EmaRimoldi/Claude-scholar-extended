#!/bin/bash
# SLURM job array script for sparse-hate-explain experiments.
# Submit: sbatch scripts/train.sh --condition M4b --n_seeds 10
# Or: sbatch --array=0-9 scripts/train.sh --condition M4b
#
# Usage:
#   sbatch --array=0-4 scripts/train.sh --condition M0
#   sbatch --array=0-9 scripts/train.sh --condition M4b   (primary: 10 seeds)
#   sbatch --array=0-4 scripts/train.sh --condition M1

#SBATCH --job-name=sparse-hate
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=04:00:00
#SBATCH --partition=ou_bcs_low

set -euo pipefail

# Parse arguments
CONDITION="M4b"
while [[ $# -gt 0 ]]; do
    case $1 in
        --condition) CONDITION="$2"; shift 2;;
        *) echo "Unknown argument: $1"; exit 1;;
    esac
done

# Map condition to experiment config name
declare -A CONDITION_TO_CONFIG
CONDITION_TO_CONFIG["M0"]="m0_baseline_softmax"
CONDITION_TO_CONFIG["M1"]="m1_sra_replication"
CONDITION_TO_CONFIG["M2"]="m2_full_softmax_mse"
CONDITION_TO_CONFIG["M3"]="m3_full_sparsemax_mse"
CONDITION_TO_CONFIG["M4a"]="m4a_sel_sparsemax_mse_k3"
CONDITION_TO_CONFIG["M4b"]="m4b_sel_sparsemax_mse_k6"
CONDITION_TO_CONFIG["M4c"]="m4c_sel_sparsemax_mse_k9"
CONDITION_TO_CONFIG["M5"]="m5_sel_sparsemax_kl"
CONDITION_TO_CONFIG["M6"]="m6_sel_sparsemax_loss"
CONDITION_TO_CONFIG["M7"]="m7_sel_softmax_mse"

CONFIG_NAME="${CONDITION_TO_CONFIG[$CONDITION]}"
SEED=$((42 + SLURM_ARRAY_TASK_ID))

echo "Running condition=${CONDITION}, config=${CONFIG_NAME}, seed=${SEED}"
echo "SLURM_JOB_ID=${SLURM_JOB_ID}, SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"

export LD_LIBRARY_PATH=/orcd/software/core/001/spack/pkg/gcc/12.2.0/yt6vabm/lib64:${LD_LIBRARY_PATH:-}

# Thread limits
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# Activate environment
source .venv/bin/activate

# Create log directory
mkdir -p logs outputs

# Run experiment
python run_experiment.py \
    "+experiment=${CONFIG_NAME}" \
    "seed=${SEED}" \
    "hydra.run.dir=outputs/${CONDITION}/seed${SEED}"
