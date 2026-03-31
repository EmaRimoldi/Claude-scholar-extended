#!/bin/bash
# submit_grid.sh — SLURM batch submission for all v3 experiment conditions.
#
# Conditions submitted:
#   Baselines  B0: vanilla (softmax, no supervision)
#              B1: softmax-all (softmax, all heads, MSE)
#              B2: sra_replication  (sparsemax, all heads, KL)
#              B3: smra_replication (sparsemax, all heads, KL)
#              B4: entmax_full      (entmax α=1.5, all heads, KL)
#              B5: random_head_sparsemax (sparsemax, random 24 heads, MSE)
#   Ablation   M1–M8: 2×2×2 (supervision × transform × loss)
#   K-sweep    K1–K6: sel-sparsemax-mse at K∈{6,12,24,36,48,72}
#
# Total: 20 conditions × 10 seeds = 200 SLURM jobs
#
# Prerequisites:
#   - B0 trained + head importance scored before B5 or M5-8/K1-6 are submitted.
#   - Run in two phases:  Phase 1 (B0, B1, B2, B3, B4, M1-M4) then head
#     importance, then Phase 2 (B5, M5-M8, K1-K6).
#
# Usage:
#   bash scripts/submit_grid.sh [--phase 1|2|all] [--dry-run]
#
# SLURM defaults (override via environment):
#   PARTITION   gpu (default)
#   TIME        12:00:00
#   MEM         32G
#   CPUS        4
#   GPUS        1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# --- tuneable SLURM defaults ---
PARTITION="${PARTITION:-gpu}"
TIME="${TIME:-12:00:00}"
MEM="${MEM:-32G}"
CPUS="${CPUS:-4}"
GPUS="${GPUS:-1}"
SEEDS=(42 123 456 789 1234 2345 3456 4567 5678 6789)   # 10 seeds

# --- parse flags ---
PHASE="all"
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --phase) PHASE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

LOG_DIR="${PROJECT_ROOT}/logs/slurm"
mkdir -p "$LOG_DIR"

# -----------------------------------------------------------------------
# Helper: submit one SLURM job
# submit_job <job_name> <experiment_config> <seed> [extra_overrides...]
# -----------------------------------------------------------------------
submit_job() {
    local job_name="$1"
    local experiment="$2"
    local seed="$3"
    shift 3
    local extra_args=("$@")

    local output_dir="${PROJECT_ROOT}/results/${experiment}/seed_${seed}"

    local sbatch_cmd=(
        sbatch
        --job-name="${job_name}_s${seed}"
        --partition="${PARTITION}"
        --time="${TIME}"
        --mem="${MEM}"
        --cpus-per-task="${CPUS}"
        --gres="gpu:${GPUS}"
        --output="${LOG_DIR}/${job_name}_s${seed}_%j.out"
        --error="${LOG_DIR}/${job_name}_s${seed}_%j.err"
        --wrap="
            set -euo pipefail
            cd '${PROJECT_ROOT}'
            if [ -f ../.venv/bin/activate ]; then
                source ../.venv/bin/activate
            elif [ -f .venv/bin/activate ]; then
                source .venv/bin/activate
            fi
            python3 -m src.main \
                +experiment='${experiment}' \
                seed=${seed} \
                data.cache_dir='${PROJECT_ROOT}/data/cache' \
                output_dir='${output_dir}' \
                ${extra_args[*]+"${extra_args[*]}"}
        "
    )

    if $DRY_RUN; then
        echo "[DRY-RUN] ${sbatch_cmd[*]}"
    else
        "${sbatch_cmd[@]}"
        echo "Submitted: ${job_name} seed=${seed}"
    fi
}

# -----------------------------------------------------------------------
# Phase 1: Baselines that do NOT require head importance first
# -----------------------------------------------------------------------
phase1() {
    echo "=== Phase 1: B0 vanilla, B1 softmax-all, B2 SRA replication,"
    echo "              B3 SMRA replication, B4 entmax, M1-M4 (full-head ablation) ==="

    for seed in "${SEEDS[@]}"; do
        submit_job "b0_vanilla"          "vanilla"            "$seed"
        submit_job "b1_softmax_all"      "softmax_all"        "$seed"
        submit_job "b2_sra_rep"          "sra_replication"    "$seed"
        submit_job "b3_smra_rep"         "smra_replication"   "$seed"
        submit_job "b4_entmax_full"      "entmax_full"        "$seed"
        submit_job "m1_full_softmax_mse" "m1_full_softmax_mse" "$seed"
        submit_job "m2_full_softmax_kl"  "m2_full_softmax_kl"  "$seed"
        submit_job "m3_full_spmax_mse"   "m3_full_sparsemax_mse" "$seed"
        submit_job "m4_full_spmax_kl"    "m4_full_sparsemax_kl"  "$seed"
    done

    echo ""
    echo "Phase 1 submitted (${#SEEDS[@]} seeds × 9 conditions = $((${#SEEDS[@]} * 9)) jobs)."
    echo "Next:"
    echo "  1. Wait for B0 to finish (or best-seed checkpoint)."
    echo "  2. python scripts/run_head_importance.py --model-path results/vanilla/seed_42/best_model.pt"
    echo "  3. bash scripts/submit_grid.sh --phase 2"
}

# -----------------------------------------------------------------------
# Phase 2: Conditions that depend on head importance ranking
# -----------------------------------------------------------------------
phase2() {
    local importance_dir="${PROJECT_ROOT}/results/head_importance"
    if [ ! -f "${importance_dir}/top_24_heads.json" ]; then
        echo "ERROR: Head importance file not found: ${importance_dir}/top_24_heads.json"
        echo "Run: python scripts/run_head_importance.py --model-path results/vanilla/seed_42/best_model.pt"
        exit 1
    fi

    echo "=== Phase 2: B5 random-head, M5-M8 selective ablation, K1-K6 sweep ==="

    # B5: random head — each seed gets a different random selection
    for seed in "${SEEDS[@]}"; do
        # Generate random head list for this seed before submitting
        if $DRY_RUN; then
            echo "[DRY-RUN] python scripts/select_random_heads.py --seed ${seed} --k 24 --output-dir ${importance_dir}"
        else
            python3 "${SCRIPT_DIR}/select_random_heads.py" \
                --seed "$seed" --k 24 \
                --output-dir "$importance_dir"
        fi
        submit_job "b5_rand_spmax" "random_head_sparsemax" "$seed" \
            "model.head_importance_path=${importance_dir}/random_heads_seed${seed}.json"
    done

    # M5–M8: selective ablation (requires importance ranking for top-24 selection)
    for seed in "${SEEDS[@]}"; do
        submit_job "m5_sel_softmax_mse" "m5_sel_softmax_mse" "$seed"
        submit_job "m6_sel_softmax_kl"  "m6_sel_softmax_kl"  "$seed"
        submit_job "m7_sel_spmax_mse"   "m7_sel_sparsemax_mse" "$seed"
        submit_job "m8_sel_spmax_kl"    "m8_sel_sparsemax_kl"  "$seed"
    done

    # K-sweep: K ∈ {6, 12, 24, 36, 48, 72}
    for seed in "${SEEDS[@]}"; do
        submit_job "k1_k6"  "k1_sel_sparsemax_mse_k6"  "$seed"
        submit_job "k2_k12" "k2_sel_sparsemax_mse_k12" "$seed"
        submit_job "k3_k24" "k3_sel_sparsemax_mse_k24" "$seed"
        submit_job "k4_k36" "k4_sel_sparsemax_mse_k36" "$seed"
        submit_job "k5_k48" "k5_sel_sparsemax_mse_k48" "$seed"
        submit_job "k6_k72" "k6_sel_sparsemax_mse_k72" "$seed"
    done

    local p2_conditions=11   # B5 + M5-M8 + K1-K6
    echo ""
    echo "Phase 2 submitted (${#SEEDS[@]} seeds × ${p2_conditions} conditions = $((${#SEEDS[@]} * p2_conditions)) jobs)."
    echo "After all jobs finish:"
    echo "  python scripts/collect_results.py"
    echo "  python scripts/compute_bootstrap_ci.py"
    echo "  python scripts/value_subspace_analysis.py --results-dir results/ --output-dir results/value_subspace/"
}

# -----------------------------------------------------------------------
# Main dispatch
# -----------------------------------------------------------------------
case "$PHASE" in
    1)   phase1 ;;
    2)   phase2 ;;
    all) phase1; echo ""; phase2 ;;
    *)   echo "Unknown phase: $PHASE (use 1, 2, or all)"; exit 1 ;;
esac
