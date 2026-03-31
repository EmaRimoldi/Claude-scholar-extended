# Research Plan: Sparse Rationale-Constrained Attention for Hate Speech Detection

**Project:** Selective-head sparsemax supervision of BERT attention for explainable hate speech detection
**Target venue:** NeurIPS 2026
**Status:** Pre-execution (ready for pipeline Phase 1)

---

## Section 0: Background and Research Question

### Origin

This project extends a mini-project (EE-559, Group 49) that replaced softmax with sparsemax in BERT's CLS-token attention, supervised against human-annotated rationales from HateXplain. The original project found a statistically significant improvement in comprehensiveness but no consistent gains elsewhere, over only 3 training runs.

### Repositioned Research Question

Can **selective-head** sparsemax supervision — supervising only the gradient-important subset of BERT's 144 attention heads — outperform full-head supervision on faithfulness metrics while preserving classification F1? And can this invariance be predicted by a value-subspace span condition?

### Why This Is Not Just SRA/SMRA

- **SRA (arXiv:2511.07065):** Supervised BERT attention with sparsemax on general text classification. Full-head supervision. No head importance analysis. Not on HateXplain.
- **SMRA (arXiv:2601.03481):** Sparsemax supervision on HateXplain with moral-value rationale annotations. Full-head. No head importance or theoretical analysis.
- **This work:** Isolates the head selection factor via 2×2×2 ablation; provides the value-subspace span condition as a theoretical account; uses standard hate speech rationales (not moral-value subset); performs annotator disagreement stratification.

Both SRA and SMRA are direct baselines.

---

## Section 1: Core Contribution Claim

> Selective-head sparsemax supervision — constraining only the top-K heads identified by gradient importance scoring — achieves higher comprehensiveness than full-head supervision (SRA-style) with no significant F1 degradation. A value-subspace span condition predicts when supervision is functionally invariant, providing the first theoretical account of when attention supervision preserves model behavior.

**What is NOT new (must state clearly):**
- Sparsemax as attention normalization → Martins & Astudillo 2016
- Supervised attention with human rationales → SRA 2025
- Attention on HateXplain with sparsemax → SMRA 2026
- Head importance scoring → Michel et al. 2019

**What IS potentially new:**
1. Selective-head mechanism specifically for supervision (vs. uniform all-head)
2. Value-subspace span condition as theoretical predictor of invariance
3. 2×2×2 ablation disentangling target × head selection × loss function
4. Annotator disagreement stratification showing differential benefit on ambiguous rationales

---

## Section 2: Assumptions to Test

| ID | Assumption | Experiment | Critical? |
|----|-----------|-----------|---------|
| A1 | Gradient importance identifies semantically meaningful heads | H4: random vs. importance-based selection | YES |
| A2 | Sparsemax produces sparser supervision targets than softmax | 2×2×2 ablation, attention entropy metric | YES |
| A3 | ERASER comprehensiveness/sufficiency are valid faithfulness proxies here | Compare against adversarial swap (Jain 2019) as sanity check | YES |
| A4 | HateXplain rationales are consistent enough to supervise | E-W4: stratify by annotator agreement | MODERATE |
| A5 | Value-subspace principal angles correlate with F1 delta | H5: K-sweep + principal angle analysis | YES |
| A6 | Results generalize beyond HateXplain | Out-of-scope — documented limitation | NO |

---

## Section 3: Experiment Priority Matrix

### HIGH priority (must run before submission)

| Condition | Rationale |
|-----------|----------|
| B0 `vanilla-bert` | Minimum baseline — all comparisons relative to this |
| B2 `sra-replication` | SRA is the closest prior work — must directly compare |
| B3 `smra-replication` | SMRA is the same task+dataset — must directly compare |
| M7 `sel-sparsemax-mse` | Primary proposed method |
| M3 `full-sparsemax-mse` | Needed for H1 (selective vs. full-head factor) |
| B5 `random-head-sparsemax` | Needed for H4 (importance scoring factor) |

### MEDIUM priority (run if compute allows; needed for full ablation)

| Condition | Rationale |
|-----------|----------|
| B4 `entmax-full` | Reviewer defense: "why not entmax?" |
| M1–M8 (full 2×2×2) | Complete factor analysis |
| K1–K6 (K-sweep) | H5 value-subspace span condition requires multiple K values |

### LOW priority (exploratory)

| Condition | Rationale |
|-----------|----------|
| B1 `softmax-full` | Weaker version of B2 |
| Lambda sweep L1–L4 | Sensitivity analysis; reviewers may ask |

---

## Section 4: Minimum Viable Experiment Set

To submit the paper with defensible results, the following 6 conditions are the minimum:

1. B0 (vanilla BERT)
2. B2 (SRA replication — full-head sparsemax)
3. B3 (SMRA replication)
4. M7 (selective-head sparsemax MSE — primary)
5. M3 (full-head sparsemax MSE — for H1 factor isolation)
6. B5 (random-head sparsemax — for H4 importance scoring factor)

Each at 10 seeds = 60 runs × ~15 min = ~15 GPU-hours minimum viable.

---

## Section 5: Recommended Repo Structure

```
src/
  models/
    bert_sparse.py      # BERT + configurable attention supervision
    sparsemax.py        # Sparsemax activation (Martins & Astudillo 2016)
    entmax.py           # α-entmax activation (Correia et al. 2019)
    head_importance.py  # Gradient-based head importance scoring
  data/
    hatexplain.py       # Dataset loading + tokenization + rationale extraction
  training/
    trainer.py          # Training loop with mixed precision, early stopping
  evaluation/
    evaluate.py         # Orchestrator: runs all metrics
  metrics/
    classification.py   # Macro-F1, per-class F1
    faithfulness.py     # Comprehensiveness, sufficiency (ERASER)
    plausibility.py     # IoU-F1, AUPRC vs. human rationales
  utils/
    seed.py             # Reproducibility seeding
scripts/
  submit_grid.sh        # SLURM batch submission for experiment matrix
  value_subspace_analysis.py  # Principal angle computation for H5
  run_head_importance.py      # Head importance scoring on trained model
  collect_results.py          # Aggregate run outputs to CSV/tables
  compute_bootstrap_ci.py     # Bootstrap CI computation
configs/
  config.yaml           # Root Hydra config
  experiment/           # Per-condition configs
    vanilla.yaml
    sra_replication.yaml
    smra_replication.yaml
    sel_sparsemax_mse.yaml
    full_sparsemax_mse.yaml
    random_head_sparsemax.yaml
    entmax_full.yaml
    [m1-m8 2x2x2 configs]
    [k1-k6 k-sweep configs]
```

---

## Section 6: Key References

- Mathew et al. (2021). HateXplain. AAAI.
- Martins & Astudillo (2016). Sparsemax. ICML.
- Correia et al. (2019). Adaptively Sparse Transformers (entmax). EMNLP.
- Clark et al. (2019). What Does BERT Look At? ACL BlackboxNLP.
- Voita et al. (2019). Analyzing Multi-Head Self-Attention. ACL.
- Jain & Wallace (2019). Attention is not Explanation. NAACL.
- Wiegreffe & Pinter (2019). Attention is not not Explanation. EMNLP.
- Michel et al. (2019). Are Sixteen Heads Really Better Than One? NeurIPS.
- DeYoung et al. (2020). ERASER Benchmark. ACL.
- SRA: arXiv:2511.07065 (Nov 2025)
- SMRA: arXiv:2601.03481 (Jan 2026)
- Sundararajan et al. (2017). Integrated Gradients. ICML.
- Davani et al. (2024). Annotator Disagreement. ACL.
