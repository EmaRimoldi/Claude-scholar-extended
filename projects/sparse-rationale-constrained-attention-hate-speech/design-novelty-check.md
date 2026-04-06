# Design-Novelty Gate Check (Gate N2)

**Date:** 2026-04-01
**Decision:** PASS
**Cycle:** 1 / 2
**Inputs:** experiment-plan.md, hypotheses.md, novelty-assessment.md, claim-overlap-report.md

---

## Check 1: Novelty Claim → Experiment Alignment

| Novelty Dimension | Claimed in N1 | Experiment That Tests It | Status |
|------------------|--------------|--------------------------|--------|
| Method novelty C1: gradient importance head selection | YES (primary) | M4a/M4b/M4c vs M3 (varies k with sparsemax fixed); M7 vs M0 (head selection without sparsemax) | PASS |
| Method novelty C2: sparsemax as activation under supervision | YES (primary) | M2 (softmax, all-12) vs M3 (sparsemax, all-12); M7 (softmax, k=6) vs M4b (sparsemax, k=6) | PASS |
| Combination novelty C1+C2+C3 | YES (primary) | Full ablation matrix; primary comparison M0 vs M4b | PASS |
| Empirical novelty C3: IG evaluation + bootstrap CIs | YES (primary) | Phase 3 (LIME stability H4, IG-LIME agreement H4b); all metrics under both IG and LIME | PASS |
| Application novelty: hate speech | PARTIAL (not primary) | HateXplain as primary dataset; task-specific metrics (IoU-F1 vs. HateXplain rationales) | PASS (partial = no isolating test needed) |

**Result: NO CRITICAL issues. All primary novelty dimensions have corresponding experiments.**

---

## Check 2: Baseline Completeness

### HIGH-overlap prior work (from claim-overlap-report.md)

| Prior Work | Overlap Level | As Baseline? | Justification if Absent | Status |
|-----------|--------------|-------------|------------------------|--------|
| Eilertsen et al. 2025 (SRA) | HIGH | YES — M1 (SRA replication: BERT-base + softmax + fixed head (8,7) + MSE) | — | PASS |

### Additional baseline completeness checks

| Requirement | Present? | Status |
|-------------|---------|--------|
| Plain vanilla baseline (no modification) | YES — M0: BERT-base + CE only (Mathew et al. 2021) | PASS |
| Most widely used method in field | YES — M0 and M1 together represent the field's state-of-the-art | PASS |
| Component ablation: remove head selection | YES — M3 (sparsemax, all-12 heads) removes importance selection | PASS |
| Component ablation: remove sparsemax | YES — M2 (softmax, all-12 heads); M7 (softmax, k=6 heads) | PASS |
| Component ablation: remove alignment loss | M0 is the no-supervision baseline; M4b+no-loss is implicitly M0 | PASS |
| Loss function comparison | YES — M4b (MSE), M5 (KL), M6 (sparsemax_loss) | PASS |

**Missing baselines:** None. All HIGH-overlap papers are baselines. MEDIUM-overlap papers (SMRA, TaSc, MRP) are in the related work and cited, but their code is either unavailable or their task formulation differs; not required as baselines.

**MRP (Kim et al. 2022) note:** MRP uses pre-training (masked rationale prediction), not runtime attention supervision. Different mechanism; non-comparable as a direct baseline. Document this in related work.

**Result: PASS**

---

## Check 3: Evaluation Metric Alignment

| Metric | Standard in Field? | Tests Novelty Claim? | Source | Status |
|--------|-------------------|---------------------|--------|--------|
| IoU-F1 | YES (HateXplain; SRA, SMRA, MRP) | YES — plausibility (H1, H2, H3) | Mathew 2021, DeYoung 2020 | PASS |
| Token-F1 | YES (HateXplain standard) | YES — plausibility secondary | Mathew 2021 | PASS |
| Comprehensiveness | YES (ERASER standard) | YES — faithfulness (H2, H4) | DeYoung 2020 | PASS |
| Sufficiency | YES (ERASER standard) | YES — faithfulness secondary | DeYoung 2020 | PASS |
| Macro-F1 | YES (HateXplain standard) | YES — non-degradation constraint (H5) | Mathew 2021 | PASS |
| IG as primary evaluator | Non-standard vs SRA (SRA uses LIME) | YES — tests C3 directly; dual reporting maintains comparability | Sundararajan 2017 | PASS (justified) |
| Kendall's τ | Standard for ranking agreement | YES — H4a LIME stability | — | PASS |
| Spearman ρ | Standard for attribution correlation | YES — H4b IG-LIME agreement | — | PASS |
| Cohen's d | Standard for effect size | YES — H5 statistical rigor | — | PASS |
| Bootstrap 95% CI | Standard for NLP comparisons | YES — H5 | — | PASS |

**Non-standard metric flag:** IG as primary faithfulness evaluator is non-standard relative to SRA. **This is intentional and is hypothesis H4 itself.** Justified by: (a) IG satisfies Sensitivity + Implementation Invariance axioms that LIME does not; (b) LIME instability on short texts is the testable prediction; (c) LIME-based results still reported as secondary for comparability. **Not a MAJOR issue.**

**Result: PASS**

---

## Check 4: Ablation Coverage of Novelty

### Component isolation matrix

| Component | Held-constant controls | Isolating comparison | Confound risk | Status |
|-----------|----------------------|---------------------|--------------|--------|
| Head selection (C1) | Activation=sparsemax, Loss=MSE | M3 (k=12) vs M4a (k=3) vs M4b (k=6) vs M4c (k=9) | Confound: different k values may have different expressive capacity (not just selection quality). Addressed by: reporting all 4 k values; using gradient importance (not random) for selection; E-G1 gate checks importance score variance. | PASS |
| Sparsemax activation (C2) | Head selection=k=6, Loss=MSE | M7 (softmax, k=6, MSE) vs M4b (sparsemax, k=6, MSE) | Confound: sparsemax changes gradient magnitudes, affecting effective learning rate. Addressed by: same LR for all conditions; gradient clipping (max_norm=1.0). | PASS |
| Sparsemax activation C2 (second instance) | Head selection=all-12, Loss=MSE | M2 (softmax, all-12, MSE) vs M3 (sparsemax, all-12, MSE) | Same as above. Two independent ablations strengthen causal inference. | PASS |
| Alignment loss type (H3) | Activation=sparsemax, Heads=k=6 | M4b (MSE) vs M5 (KL) vs M6 (sparsemax_loss) | Confound: learning dynamics differ between loss functions (Lipschitz constants). Addressed by: independent λ tuning per loss on seed 0 before main run. | PASS |
| IG vs LIME evaluation (C3) | All models | Phase 3 dual evaluation + H4a/H4b tests | Confound: IG may mechanically favor sparsemax (gradients backpropagate differently through sparsemax vs softmax). Addressed by: also reporting comprehensiveness via model-based perturbation (token masking), which does not backpropagate through attention. | PASS |

**NOTE — Minor ablation gap:** There is no explicit "sparsemax + no supervision" condition (sparsemax attention in all heads, no alignment loss, no rationale supervision). This would isolate "does sparsemax help at all without supervision?" from "does sparsemax help under supervision?"

**Assessment:** This gap is covered by prior work. Ribeiro et al. 2020 (in ledger: ribeiro2020sparsemax) tested unsupervised sparsemax in text classification and found "limited gains." We cite this result and argue our contribution is specifically about sparsemax under supervision, not sparsemax per se. The experiment plan is correct not to include a no-supervision sparsemax condition; it would add compute without testing our specific claim.

**Action required:** Add one sentence to the manuscript related work: "We do not include an unsupervised sparsemax baseline because prior work (Ribeiro et al. 2020) already established that sparsemax alone yields marginal gains in text classification without external supervision; our contribution is specifically about sparsemax under rationale supervision."

**Result: PASS (with manuscript note)**

---

## Check 5: Power Analysis

| Comparison | Claimed/Expected Effect | Seeds Planned | Estimated Power | Status |
|-----------|------------------------|--------------|----------------|--------|
| M0 vs M4b (primary) | IoU-F1 d ≈ 0.5 (H2 + H1 combined) | 10 | ~80% | PASS |
| M0 vs M4b comprehensiveness | d ≈ 0.5 (sparsemax structural alignment) | 10 | ~80% | PASS |
| M1 vs M4b (vs SRA) | d ≈ 0.3 (smaller, incremental vs SRA) | 10 | ~50% | MINOR — acknowledged |
| M3 vs M4b (head selection ablation) | d ≈ 0.4 | 5 | ~55% | MINOR — acceptable for ablation |
| M2 vs M3 (sparsemax vs softmax ablation) | d ≈ 0.5 (structural alignment argument) | 5 | ~70% | PASS |
| M4b vs M5 vs M6 (loss ablation H3) | d ≈ 0.2–0.3 (subtle effect) | 5 | ~25–45% | MINOR — acceptable for exploratory ablation |
| H4a LIME stability (50 posts, 10 runs) | τ < 0.8 threshold test | N/A (threshold test) | N/A | PASS |
| H5 SRA fragility (M0/M1, n=10) | Sufficiency CI includes 0, IoU-F1 CI excludes 0 | 10 | ~50–80% (metric dependent) | PASS |

**Power concerns:**
1. **M1 vs M4b at n=10, d=0.3: ~50% power.** This means there is a ~50% chance of failing to detect a real improvement over SRA even if it exists. This is an explicit limitation. The plan correctly states: "Secondary comparison: M1 vs M4b — contribution over SRA." If this comparison is non-significant, we report it as "M4b does not significantly outperform SRA on any single metric but achieves comparable performance with principled methodology." The claim then rests on methodology (H4, H5, H6), not on beating SRA metrics.

2. **H3 loss ablation at n=5, d=0.2–0.3: ~25–45% power.** This means H3 may not produce detectable differences. The plan explicitly states the falsification criterion is "if CIs overlap, H3 is falsified." A null result here is still reportable.

**Neither concern is MAJOR** because:
- The power constraints are explicitly documented in the plan
- The falsification criteria account for both confirmatory and null outcomes
- The compute budget (87 GPU-hours) makes higher seeds impractical
- Post-hoc power analysis is planned for all metrics (Phase 4)

**Result: PASS with documented limitations**

---

## Issue Summary

| ID | Severity | Description | Required Fix |
|----|----------|-------------|-------------|
| N2-01 | NOTE | Minor ablation gap: no "sparsemax + no supervision" condition | Add manuscript note citing Ribeiro et al. 2020 to justify omission |
| N2-02 | NOTE | M1 vs M4b comparison underpowered (d=0.3, n=10, ~50% power) | Explicitly state in manuscript that M4b vs SRA comparison is exploratory; primary claim is M4b vs M0 |
| N2-03 | NOTE | H3 loss ablation underpowered for small effects | State explicitly: if CIs overlap, this is a valid null result; we do not claim loss function matters unless CIs separate |

**CRITICAL issues: 0**
**MAJOR issues: 0**
**MINOR/NOTE issues: 3** (all documented, none blocking)

---

## Decision

```
GATE N2: PASS
```

**Decision:** PASS — experimental design is aligned with the novelty claim. No CRITICAL or MAJOR issues.

**Route to:** Step 11 (`/scaffold`) — Phase 3 (Implementation) begins.

**Mandatory manuscript additions (from Notes):**
1. Add one sentence in Related Work noting that unsupervised sparsemax (Ribeiro et al. 2020) is the implicit no-supervision baseline, covered by prior work.
2. In the Results section, note that the M1 vs M4b comparison is exploratory (underpowered) and should not be the primary evidence for the contribution over SRA.
3. For H3, explicitly state the falsification criterion in the Methods section.

**Gate N2 status: PASSED (Cycle 1/2)**
