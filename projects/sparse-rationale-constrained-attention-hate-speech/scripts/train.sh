#!/bin/bash
# Sequential multi-condition training job.
# All seeds for each condition run sequentially within a single GPU job.
# Group 2 conditions per submission to balance GPU time across jobs.
#
# Usage:
#   sbatch scripts/train.sh --conditions M0 M1          # Wave 1, GPU-A (~9h)
#   sbatch scripts/train.sh --conditions M3 M4b         # Wave 1, GPU-B (~9h)
#   sbatch scripts/train.sh --conditions M2 M4a         # Wave 2, GPU-C (~9h)
#   sbatch scripts/train.sh --conditions M4c M5         # Wave 2, GPU-D (~9h)
#   sbatch scripts/train.sh --conditions M6 M7          # Wave 2, GPU-E (~9h)
#
# Optional: --n_seeds N (default: 3), --start_seed S (default: 42)

#SBATCH --job-name=sparse-hate
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=5:50:00
#SBATCH --partition=mit_normal_gpu

set -euo pipefail

# --- Argument parsing ---
CONDITIONS=()
N_SEEDS=3
START_SEED=42

while [[ $# -gt 0 ]]; do
    case $1 in
        --conditions)
            shift
            while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                CONDITIONS+=("$1")
                shift
            done
            ;;
        --n_seeds)   N_SEEDS="$2";   shift 2;;
        --start_seed) START_SEED="$2"; shift 2;;
        *) echo "Unknown argument: $1"; exit 1;;
    esac
done

if [[ ${#CONDITIONS[@]} -eq 0 ]]; then
    echo "Error: --conditions requires at least one condition (e.g. --conditions M0 M1)"
    exit 1
fi

# --- Condition → config mapping ---
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

# --- Environment setup ---
export LD_LIBRARY_PATH=/orcd/software/core/001/spack/pkg/gcc/12.2.0/yt6vabm/lib64:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

source .venv/bin/activate
mkdir -p logs outputs

echo "=== Pre-flight validation ===" && \
python scripts/validate_train.py || { echo "[ABORT] validate_train.py failed — job cancelled."; exit 1; }
echo "=== Validation passed. Starting training ==="

echo "=== Job started: $(date) ==="
echo "Conditions: ${CONDITIONS[*]}"
echo "Seeds per condition: ${N_SEEDS} (starting from seed ${START_SEED})"
echo "SLURM_JOB_ID=${SLURM_JOB_ID}"
echo ""

# --- Sequential loop: condition → seed ---
for CONDITION in "${CONDITIONS[@]}"; do
    CONFIG_NAME="${CONDITION_TO_CONFIG[$CONDITION]}"
    echo "--- Condition ${CONDITION} (config=${CONFIG_NAME}) ---"

    for ((i=0; i<N_SEEDS; i++)); do
        SEED=$((START_SEED + i))
        echo "[$(date +%H:%M:%S)] ${CONDITION} seed=${SEED}"

        python run_experiment.py \
            "experiment=${CONFIG_NAME}" \
            "seed=${SEED}" \
            "hydra.run.dir=outputs/${CONDITION}/seed${SEED}"

        echo "[$(date +%H:%M:%S)] ${CONDITION} seed=${SEED} done"
    done

    echo "--- Condition ${CONDITION} complete ---"
    echo ""
done

echo "=== Job finished: $(date) ==="
