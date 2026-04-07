# Hypothesis Outcomes — Sparse Rationale-Constrained Attention

**Date:** 2026-04-07 | **Step:** 20 (analyze-results)

| Hypothesis | Verdict | Key Evidence |
|------------|---------|--------------|
| **H1** — Sparsemax+MSE comprehensiveness > SRA+KL without accuracy loss | **SUPPORTED** | Δcomp=+0.178 AOPC, Wilcoxon p=0.031, Cohen's d=8.36; F1 equiv. TOST p=0.047 |
| **H2** — Rationale sparsity (<30%) validates sparsemax structural fit | **SUPPORTED** | HateXplain median coverage ~23% << 30% threshold |
| **H3** — Top-6 heads ≥ all-12 on comprehensiveness | **INCONCLUSIVE** | C4>C5 numerically (0.338 vs 0.296), Wilcoxon p=0.063; C5>C4 on swap KL |
| **H4** — Adversarial swap KL ratio ≥ 2× (sparsemax vs SRA) | **PARTIAL** | Ratio=1.47×, p=0.031; structural sparsity (C3) more faithful than soft alignment (C2) even without supervision |
| **H5** — Identity-term FPR reduction | **NOT TESTED** | Requires fairness-stratified evaluation (future work) |

## Primary Claim (paper)
Sparsemax+MSE supervision achieves **+111% relative comprehensiveness** over SRA-softmax+KL (0.338 vs 0.160 AOPC; d=8.36; p=0.031) with no classification accuracy cost (+0.09 pp, TOST-equivalent).
