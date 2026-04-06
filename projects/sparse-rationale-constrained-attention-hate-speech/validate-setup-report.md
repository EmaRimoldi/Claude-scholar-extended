# Validate-Setup Report (Step 15)

**Date:** 2026-04-01
**Status:** PASS

---

## Checklist

### Source files (26 files)

| Module | File | Status |
|--------|------|--------|
| Sparsemax | src/model/sparsemax.py | PASS |
| BERT+Sparsemax | src/model/bert_sparse.py | PASS |
| Dataset | src/data/dataset.py | PASS |
| Preprocessing | src/data/preprocessing.py | PASS |
| Alignment Losses | src/losses/alignment.py | PASS |
| Head Importance | src/head_selection/importance.py | PASS |
| Plausibility Metrics | src/evaluation/plausibility.py | PASS |
| Faithfulness Metrics | src/evaluation/faithfulness.py | PASS |
| Attribution (IG+LIME) | src/evaluation/attribution.py | PASS |
| Statistics | src/evaluation/statistics.py | PASS |
| Rationale Sparsity | src/analysis/rationale_sparsity.py | PASS |
| Annotator Agreement | src/analysis/annotator_agreement.py | PASS |
| Trainer | src/trainer/train.py | PASS |
| Entry Point | run_experiment.py | PASS |
| Build Config | pyproject.toml | PASS |
| Makefile | Makefile | PASS |

### Configuration files (11 files)

| Condition | Config | Status |
|-----------|--------|--------|
| Base | configs/config.yaml | PASS |
| M0 | configs/experiment/m0_baseline_softmax.yaml | PASS |
| M1 | configs/experiment/m1_sra_replication.yaml | PASS |
| M2 | configs/experiment/m2_full_softmax_mse.yaml | PASS |
| M3 | configs/experiment/m3_full_sparsemax_mse.yaml | PASS |
| M4a | configs/experiment/m4a_sel_sparsemax_mse_k3.yaml | PASS |
| M4b | configs/experiment/m4b_sel_sparsemax_mse_k6.yaml | PASS |
| M4c | configs/experiment/m4c_sel_sparsemax_mse_k9.yaml | PASS |
| M5 | configs/experiment/m5_sel_sparsemax_kl.yaml | PASS |
| M6 | configs/experiment/m6_sel_sparsemax_loss.yaml | PASS |
| M7 | configs/experiment/m7_sel_softmax_mse.yaml | PASS |

### Test files

| File | Status |
|------|--------|
| tests/test_sparsemax.py | PASS |
| tests/test_plausibility.py | PASS |
| tests/test_statistics.py | PASS |

### SLURM compliance (compute-budget.md)

- GPU per job: `--gres=gpu:1` — PASS
- Array syntax: `--array=0-4` (5 seeds), `--array=0-9` (10 seeds) — PASS
- No N×M-GPU single jobs — PASS

### Syntax check

All 26 Python files pass `ast.parse()` — PASS

### Line count compliance (coding-style.md: max 400 lines)

| File | Lines |
|------|-------|
| src/model/bert_sparse.py | 345 |
| src/trainer/train.py | 257 |
| src/evaluation/attribution.py | 266 |
| All other files | < 200 |

All files within the 400-line limit — PASS

---

## Blockers

**NONE** — All checks pass.

## Pre-cluster action required

Before Phase 2 training:
1. `make install` (or `uv pip install -e .`) on cluster to build `.venv`
2. Run `make phase0` (no GPU needed, ~5 min) to verify Gate G0
3. Run `make phase1` (1 GPU, ~2h) to compute head importance scores for Gate G1
4. Update `importance_scores_path` in M4a/M4b/M4c/M5/M6/M7 configs with actual path

## Decision

```
VALIDATE-SETUP: PASS
```

**Route to:** Step 16 (`/download-data`) — cluster-side data download.
