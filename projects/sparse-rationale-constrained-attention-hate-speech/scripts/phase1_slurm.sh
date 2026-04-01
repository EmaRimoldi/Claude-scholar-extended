#!/bin/bash
#SBATCH --job-name=sparse-phase1
#SBATCH --output=logs/phase1_%j.out
#SBATCH --error=logs/phase1_%j.err
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=03:00:00
#SBATCH --partition=ou_bcs_low

export LD_LIBRARY_PATH=/orcd/software/core/001/spack/pkg/gcc/12.2.0/yt6vabm/lib64:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=4

source .venv/bin/activate
mkdir -p logs outputs/phase1

echo "=== Pre-flight validation ===" && \
python scripts/validate_phase1.py || { echo "[ABORT] validate_phase1.py failed — job cancelled."; exit 1; }
echo "=== Validation passed. Starting Phase 1 ==="

python scripts/phase1_head_importance.py --device cuda --max_batches 200
