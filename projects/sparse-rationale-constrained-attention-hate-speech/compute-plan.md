# Compute Plan (Step 17 — revised for experimental phase)

**Date:** 2026-04-01 (revised 2026-04-01)
**Seeds per condition:** 3 (experimental phase; upgrade to 5 before camera-ready)
**Estimated total GPU-hours:** ~51h
**Hardware assumption:** A100 40GB (~1.5 GPU-hours/condition-seed for BERT-base)
**Calendar time:** ~9h with 5 parallel jobs (Wave 1 + Wave 2 overlap where cluster allows)

---

## Design Principles

- **Sequential seeds within a single job:** all seeds for a condition run in one GPU job, no per-seed job arrays.
- **Grouped conditions per job:** 2 conditions per job to keep each GPU busy for ~9h.
- **Load balancing:** all training jobs are ~9h (3 seeds × 1.5h × 2 conditions).
- **Total training jobs:** 5 (down from 30 array tasks in the original design).
- **Wave gating:** Wave 2 waits for Gate G2 (M4b val IoU-F1 > M1 − 0.02).

---

## Phase 0 — Data Analysis (no GPU, ~5 min)

```bash
make phase0
# Writes: outputs/phase0/rationale_sparsity.json, annotator_agreement.json
# Gate G0: median coverage < 0.50
```

---

## Phase 1 — Head Importance Scoring (1 GPU job, ~2h)

```bash
sbatch scripts/phase1_slurm.sh
# Writes: outputs/phase1/importance_scores.pt, phase1_summary.json
# Gate G1: variance > 0.01
# Update importance_scores_path in M4a/M4b/M4c/M5/M6/M7 configs afterward
```

---

## Phase 2 Wave 1 — Primary conditions (2 GPU jobs, ~9h each)

Submit after Phase 1 Gate G1 passes.

| Job | Conditions (sequential) | Seeds each | Estimated wall time |
|-----|------------------------|-----------|---------------------|
| W1-A | M0 → M1 | 3 | ~9h |
| W1-B | M3 → M4b | 3 | ~9h |

```bash
sbatch scripts/train.sh --conditions M0 M1    # Job W1-A
sbatch scripts/train.sh --conditions M3 M4b   # Job W1-B
```

Wave 1 total: ~18 GPU-hours.

**Gate G2:** after both jobs complete, check M4b val IoU-F1 > M1 − 0.02 before submitting Wave 2.

---

## Phase 2 Wave 2 — Ablation conditions (3 GPU jobs, ~9h each)

Submit only after Gate G2 passes.

| Job | Conditions (sequential) | Seeds each | Estimated wall time |
|-----|------------------------|-----------|---------------------|
| W2-A | M2 → M4a | 3 | ~9h |
| W2-B | M4c → M5 | 3 | ~9h |
| W2-C | M6 → M7 | 3 | ~9h |

```bash
sbatch scripts/train.sh --conditions M2 M4a   # Job W2-A
sbatch scripts/train.sh --conditions M4c M5   # Job W2-B
sbatch scripts/train.sh --conditions M6 M7    # Job W2-C
```

Wave 2 total: ~27 GPU-hours.

---

## Phase 3 — Attribution Analysis (1 GPU job, ~4h)

```bash
python scripts/phase3_attributions.py --model_dir outputs/M4b/best_model
# IG: ~2.5h for 2000 test examples × 3 seeds
# LIME: ~1.5h for 50 examples × 10 runs × 1000 samples (seed0 only)
# Gate G3: IG convergence delta < 0.01
```

---

## Phase 4 — Statistics (CPU only, ~2h)

```bash
python scripts/phase4_statistics.py
# Bootstrap B=1000, Cohen's d, power analysis, H4a/H4b tests
```

---

## Job Summary

| Job ID | Script | Conditions | Wall time | GPU-hours |
|--------|--------|-----------|-----------|-----------|
| phase1 | phase1_slurm.sh | head importance | 3h | 2 |
| W1-A | train.sh | M0, M1 | 10h | 9 |
| W1-B | train.sh | M3, M4b | 10h | 9 |
| W2-A | train.sh | M2, M4a | 10h | 9 |
| W2-B | train.sh | M4c, M5 | 10h | 9 |
| W2-C | train.sh | M6, M7 | 10h | 9 |
| phase3 | (inline) | attributions | 5h | 4 |
| **Total** | | | | **~51h** |

**7 GPU jobs** total (vs 30+ array tasks in the original design).

---

## Resource Requirements per Job

```
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=10:00:00
#SBATCH --partition=ou_bcs_low
```

---

## Output Directory Structure

```
outputs/
├── M0/seed42/, seed43/, seed44/
├── M1/seed42/, seed43/, seed44/
├── M2/seed42/, seed43/, seed44/
├── M3/seed42/, seed43/, seed44/
├── M4a/seed42/, seed43/, seed44/
├── M4b/seed42/, seed43/, seed44/
├── M4c/seed42/, seed43/, seed44/
├── M5/seed42/, seed43/, seed44/
├── M6/seed42/, seed43/, seed44/
├── M7/seed42/, seed43/, seed44/
├── phase0/
├── phase1/
└── phase3/
```

---

## Upgrade Path (before camera-ready)

When moving from experimental to publication-quality runs:
- Change `--n_seeds 5` for ablation conditions (M2, M4a, M4c, M5, M6, M7)
- Change `--n_seeds 5` for Wave 1 (adds 2 more seeds per condition; regroup jobs accordingly)
- Re-run `python scripts/compute_budget_check.py --seeds 5 --conditions 10 --gpus-per-job 1`

---

## Validation Script

```bash
python scripts/compute_budget_check.py --seeds 3 --conditions 10 --gpus-per-job 1
```
