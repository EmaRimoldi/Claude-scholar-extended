# Compute Plan — Sparse Rationale-Constrained Attention for Hate Speech Detection

**Date:** 2026-04-07
**Pipeline Step:** 17 (`/plan-compute`)

---

## Resource Summary

| Resource | Value |
|----------|-------|
| GPU type | A100 80GB (preferred) or V100 32GB |
| GPUs per job | 1 (per compute-budget.md) |
| Seeds per condition | 5 (per compute-budget.md) |
| Total training jobs | 25 (5 conditions × 5 seeds) |
| Additional jobs | 2 (W5a HateBRXplain × 3 seeds × 3 conditions ≈ 9 jobs, optional) |
| Total GPU-hours (primary) | ~110 |
| Estimated wall time | 2–2.5h per job |

---

## Job Matrix (Primary Experiments)

| Job Array | Condition | Config | Seeds | SLURM Array |
|-----------|-----------|--------|-------|------------|
| `slurm/train_c1.sh` | C1 (BERT-base FT) | `model=bert_softmax_baseline` | 42-46 | `--array=0-4` |
| `slurm/train_c2.sh` | C2 (SRA softmax+KL) | `model=bert_softmax_sra` | 42-46 | `--array=0-4` |
| `slurm/train_c3.sh` | C3 (sparsemax, no sup) | `model=bert_sparsemax, model.alpha=0.0` | 42-46 | `--array=0-4` |
| `slurm/train_c4.sh` | C4 (sparsemax+MSE all-12) | `model=bert_sparsemax` | 42-46 | `--array=0-4` |
| `slurm/train_c5.sh` | C5 (sparsemax+MSE top-6) | `model=bert_sparsemax_top6` | 42-46 | `--array=0-4` |

Seeds encoded as: `SEED = 42 + SLURM_ARRAY_TASK_ID`

---

## SLURM Template (Primary Conditions)

```bash
#!/bin/bash
#SBATCH --job-name=sprattn_${CONDITION}
#SBATCH --output=logs/slurm_%x_%A_%a.out
#SBATCH --error=logs/slurm_%x_%A_%a.err
#SBATCH --array=0-4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --partition=gpu

# Environment
source ~/.bashrc
cd $PROJECT_DIR
SEED=$((42 + SLURM_ARRAY_TASK_ID))
VENV=/home/erimoldi/projects/Claude-scholar-extended/.venv/bin/python

# Pre-flight (1-seed CPU sanity check on first task only)
if [ "$SLURM_ARRAY_TASK_ID" -eq 0 ]; then
    $VENV scripts/preflight_validate.py || exit 1
fi

# Download data (once, first task only)
if [ "$SLURM_ARRAY_TASK_ID" -eq 0 ]; then
    $VENV scripts/download_data.py --output-dir data/hatexplain
fi

# Training
$VENV train.py \
    model=${MODEL_CONFIG} \
    seed=$SEED \
    condition=${CONDITION} \
    training.output_dir=checkpoints/${CONDITION}/seed_${SEED}
```

---

## Condition-Specific SLURM Scripts

### C1: BERT baseline
```bash
# slurm/train_c1.sh
#SBATCH --job-name=sprattn_C1
CONDITION=C1 MODEL_CONFIG=bert_softmax_baseline sbatch slurm/train_template.sh
```

### C2: SRA replication
```bash
# slurm/train_c2.sh
#SBATCH --job-name=sprattn_C2
CONDITION=C2 MODEL_CONFIG=bert_softmax_sra sbatch slurm/train_template.sh
```

### C3: Sparsemax no supervision
```bash
# slurm/train_c3.sh
#SBATCH --job-name=sprattn_C3
# Override alpha=0 at command line
CONDITION=C3 MODEL_CONFIG=bert_sparsemax sbatch slurm/train_template.sh
# Add: model.alpha=0.0 model.supervised_heads=null to train.py args
```

### C4: Primary (sparsemax + MSE all-12 heads)
```bash
# slurm/train_c4.sh — PRIMARY EXPERIMENT
#SBATCH --job-name=sprattn_C4
CONDITION=C4 MODEL_CONFIG=bert_sparsemax sbatch slurm/train_template.sh
```

### C5: Head-selective (sparsemax + MSE top-6 heads)
```bash
# slurm/train_c5.sh
#SBATCH --job-name=sprattn_C5
CONDITION=C5 MODEL_CONFIG=bert_sparsemax_top6 sbatch slurm/train_template.sh
```

---

## Submission Order and Dependency

Submit in this order to control cluster load:
1. Submit C1 (fast, ~1.5h) to verify basic pipeline
2. Submit C2 (SRA replication) — validates SRA baseline matches published results
3. Submit C3 simultaneously with C2
4. Submit C4 after C1 and C2 complete successfully
5. Submit C5 after C4 checkpoint exists (C5 uses C4's importance ranking)

```bash
# Submit all at once (scheduler handles queuing)
sbatch slurm/train_c1.sh
sbatch slurm/train_c2.sh
sbatch slurm/train_c3.sh
sbatch slurm/train_c4.sh
# Submit C5 with dependency on C4 completing at least seed 42:
# sbatch --dependency=afterok:$C4_JOBID slurm/train_c5.sh
```

---

## Checkpoint and Output Structure

```
checkpoints/
├── C1/
│   ├── seed_42/best_model.pt
│   ├── seed_43/best_model.pt
│   └── ...
├── C2/
├── C3/
├── C4/   ← primary; used for H4 adversarial swap
└── C5/

results/
├── raw/
│   ├── C1_seed42.json
│   └── ...
└── aggregated/
    ├── metrics_table.csv
    └── eraser_results.json
```

---

## Evaluation Jobs (Post-Training)

After training jobs complete, run evaluation:

```bash
# ERASER metrics for all conditions
python scripts/evaluate_eraser.py --conditions C1 C2 C3 C4 C5 --seeds 42 43 44 45 46

# H4 adversarial swap (uses saved checkpoints, ~0.5h CPU or 30min GPU)
python scripts/evaluate_h4_swap.py --conditions C2 C4 --seeds all

# H5 identity-term FPR
python scripts/evaluate_fairness.py --conditions C1 C2 C4

# H2 data analysis (no GPU)
python scripts/analyze_rationale_density.py --data-dir data/hatexplain
```

---

## Alpha Sensitivity Sweep (Supplementary)

```bash
# 4 alpha values × 5 seeds × C4 condition = 20 additional jobs
#SBATCH --array=0-19
ALPHA_VALS=(0.1 0.3 0.5 1.0)
SEED_IDX=$((SLURM_ARRAY_TASK_ID % 5))
ALPHA_IDX=$((SLURM_ARRAY_TASK_ID / 5))
SEED=$((42 + SEED_IDX))
ALPHA=${ALPHA_VALS[$ALPHA_IDX]}
$VENV train.py model=bert_sparsemax model.alpha=$ALPHA seed=$SEED condition=C4_alpha${ALPHA}
```

---

## Estimated Costs (if using cloud GPU)

At ~$3/hr for A100:
- Primary 25 jobs × 2.5h = 62.5 GPU-hours × $3 = ~$188
- W5a extension (9 jobs × 2h) = 18 GPU-hours × $3 = ~$54
- Alpha sweep (20 jobs × 2.5h) = 50 GPU-hours × $3 = ~$150
- **Total estimate: ~$390 for full experiment suite**

---

## Risk: SRA Hyperparameter Mismatch

The SRA paper (eilertsen2025aligning) reports hyperparameters for BERT+KL alignment but may use a different alpha or training schedule. If C2 macro-F1 diverges from SRA's reported ~84% F1:
1. Check alpha (try 0.1, 0.3, 0.5)
2. Check if SRA uses layer-wise LR decay
3. Report discrepancy and use our best-replicated C2 as the baseline

The comparison C4 vs. C2 is internally valid as long as C2 is a legitimate softmax+KL baseline regardless of exact hyperparameter match with SRA.
