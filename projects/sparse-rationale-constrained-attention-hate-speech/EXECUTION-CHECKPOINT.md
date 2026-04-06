# Execution Checkpoint — Pipeline Steps 11–17 Complete

**Date:** 2026-04-01
**Pipeline status:** Steps 1–17 complete. Waiting for GPU cluster execution.
**Next pipeline step:** Step 18 (`/run-experiment`) — submit jobs, monitor, collect

---

## What Is Ready

All implementation is complete. The project is ready for cluster submission.

### Source code
```
src/
├── model/sparsemax.py          # Sparsemax activation + loss
├── model/bert_sparse.py        # BERT + sparsemax injection
├── data/dataset.py             # HateXplain loader
├── data/preprocessing.py       # WordPiece tokenization + rationale alignment
├── losses/alignment.py         # MSE / KL / sparsemax alignment losses
├── head_selection/importance.py # Gradient importance scoring (Michel et al. 2019)
├── evaluation/plausibility.py  # IoU-F1, Token-F1
├── evaluation/faithfulness.py  # Comprehensiveness, Sufficiency (ERASER)
├── evaluation/attribution.py   # IG (Captum) + LIME
├── evaluation/statistics.py    # Bootstrap CIs, Cohen's d, power
├── analysis/rationale_sparsity.py
├── analysis/annotator_agreement.py
└── trainer/train.py            # HF Trainer wrapper with alignment loss
```

### Configs (10 conditions)
```
configs/experiment/
├── m0_baseline_softmax.yaml    # M0: CE only
├── m1_sra_replication.yaml     # M1: SRA baseline
├── m2_full_softmax_mse.yaml    # M2: ablation
├── m3_full_sparsemax_mse.yaml  # M3: ablation
├── m4a_sel_sparsemax_mse_k3.yaml  # M4a
├── m4b_sel_sparsemax_mse_k6.yaml  # M4b: PRIMARY METHOD
├── m4c_sel_sparsemax_mse_k9.yaml  # M4c
├── m5_sel_sparsemax_kl.yaml    # M5: loss ablation
├── m6_sel_sparsemax_loss.yaml  # M6: loss ablation
└── m7_sel_softmax_mse.yaml     # M7: sparsemax ablation
```

---

## Cluster Execution Sequence

### 1. Install environment
```bash
cd projects/sparse-rationale-constrained-attention-hate-speech
uv venv && uv pip install -e .
```

### 2. Download data (internet-accessible node, ~10 min)
```bash
python scripts/download_data.py
```

### 3. Phase 0 — Data analysis, Gate G0 (~5 min, CPU)
```bash
make phase0
# Check: outputs/phase0/phase0_summary.json → gate_g0 == "PASS"
```

### 4. Phase 1 — Head importance, Gate G1 (~2h, 1 GPU)
```bash
make phase1
# Check: outputs/phase1/phase1_summary.json → gate_g1 == "PASS"
# Note top-6 heads for M4b; they are logged there
```

### 5. Phase 2 Wave 1 — Primary training (~40 GPU-hours)
```bash
sbatch --array=0-9 scripts/train.sh --condition M0
sbatch --array=0-4 scripts/train.sh --condition M1
sbatch --array=0-4 scripts/train.sh --condition M3
sbatch --array=0-9 scripts/train.sh --condition M4b
```

Wait for all Wave 1 jobs. Check Gate G2: M4b val IoU-F1 > M1 val IoU-F1 - 0.02.

### 6. Phase 2 Wave 2 — Ablation training (~35-45 GPU-hours)
```bash
sbatch --array=0-4 scripts/train.sh --condition M2
sbatch --array=0-4 scripts/train.sh --condition M4a
sbatch --array=0-4 scripts/train.sh --condition M4c
sbatch --array=0-4 scripts/train.sh --condition M5
sbatch --array=0-4 scripts/train.sh --condition M6
sbatch --array=0-4 scripts/train.sh --condition M7
```

### 7. After training: resume pipeline
```
/run-pipeline --resume
```
This will trigger Step 18 (collect-results), 19 (analyze-results), and forward.

---

## Gates to Check Before Resuming

| Gate | Criterion | Where to Check |
|------|-----------|----------------|
| G0 | median rationale coverage < 0.50 | outputs/phase0/phase0_summary.json |
| G1 | head importance variance > 0.01 | outputs/phase1/phase1_summary.json |
| G2 | M4b val IoU-F1 > M1 val IoU-F1 - 0.02 | trainer eval logs |
