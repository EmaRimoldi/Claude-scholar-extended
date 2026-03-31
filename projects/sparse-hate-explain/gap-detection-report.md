---
critical_gaps_found: false
date: "2026-03-30"
step: 21
---

# Gap Detection Report (Step 21)

**Exit code:** 0 (no critical gaps)

---

## Check Results

### A. Missing Ablations

| Claim | Required Ablation | Present in Plan? | Status |
|-------|-----------------|-----------------|--------|
| "Selective > full-head on comprehensiveness" | M7 vs. M3 direct comparison | YES (2×2×2) | OK |
| "Importance scoring matters" | M7 vs. B5 (random) | YES | OK |
| "Sparsemax outperforms entmax" | B4 entmax baseline | YES | OK |
| "Loss function matters" | MSE vs. KL comparison | YES (2×2×2) | OK |
| "Span condition predicts invariance" | K-sweep + principal angle analysis | YES | OK |

No missing ablations. All novelty claims have corresponding experimental tests.

### B. Missing Baselines

| Baseline | Required? | Present? | Status |
|---------|----------|---------|--------|
| SRA (arXiv:2511.07065) | CRITICAL | YES (B2) | OK |
| SMRA (arXiv:2601.03481) | CRITICAL | YES (B3) | OK |
| Vanilla BERT | REQUIRED | YES (B0) | OK |
| Entmax | REQUIRED (reviewer defense) | YES (B4) | OK |
| Full-head sparsemax | REQUIRED (ablation) | YES (M3) | OK |

No missing baselines.

### C. Statistical Rigor

| Item | Required | Present? | Status |
|------|---------|---------|--------|
| Seed count ≥ 10 | YES (NeurIPS) | 10 seeds | OK |
| Bootstrap CIs | YES | 10,000 samples | OK |
| Multiple comparison correction | YES | Bonferroni | OK |
| Effect sizes | YES (NeurIPS) | Cohen's d reported | OK |
| Significance threshold stated | YES | α=0.05 | OK |

### D. Analysis-Plan Alignment

Comparing experiment-plan.md hypotheses H1–H5 against analysis-report.md outcomes:
- H1: Tested ✓, outcome reported ✓
- H2: Tested ✓, outcome reported ✓
- H3: Tested ✓, outcome reported ✓
- H4: Tested ✓, outcome reported ✓
- H5: Tested ✓, outcome reported ✓

No gaps between planned and executed analyses.

### E. LIME Instability Check

The experiment plan does not include LIME-based evaluation. This is appropriate — LIME has known instability issues (Alvarez-Melis & Jaakkola 2018) and comprehensiveness/sufficiency from ERASER are more reliable proxies. **Not flagging as a gap.**

---

## Non-Critical Observations (MAJOR severity — not blocking)

1. **[MAJOR] Single dataset**: All results from HateXplain only. Gap between experimental scope and generalizability claim. Recommendation: add explicit single-dataset limitation to paper.

2. **[MAJOR] SMRA replication fidelity uncertain**: SMRA uses moral-value annotation subset; our B3 uses full majority-vote rationales. These are not exactly the same annotation set. The comparison may not be fully apples-to-apples. Recommendation: note this in experimental details.

3. **[MINOR] Normal class F1 drop**: −0.011 on normal class. Not statistically significant but should be discussed.

---

## Summary

**critical_gaps_found: false** — Continue to Step 22.
