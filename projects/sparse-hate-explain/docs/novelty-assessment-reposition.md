# Novelty Assessment — Gate N1 (Cycle 2, Post-Reposition)

**Date:** 2026-03-30
**Step:** 7 / 38 (re-run, reposition cycle 2)
**Gate:** N1
**Reposition cycle:** 2 of 2 maximum
**Inputs:** adversarial-novelty-report.md, claim-overlap-report.md, cross-field-report.md + UPDATED hypotheses.md + UPDATED experiment-plan.md

---

## Decision: PROCEED (with conditions)

**Exit code:** 0

---

## Summary Rationale

After reposition, the contribution has been adequately reframed. The updated hypotheses.md explicitly:
- Credits SRA for sparsemax supervision
- Credits SMRA for HateXplain application
- Centers the novel components: (1) selective-head mechanism for supervision (vs. uniform full-head), (2) value-subspace span condition, (3) 2×2×2 ablation design, (4) annotator disagreement stratification

The updated experiment-plan.md adds SRA and SMRA as direct baselines, entmax as an ablation, and increases to 10 seeds.

---

## Dimension Scores (Post-Reposition)

| Dimension | Score (0–10) | Assessment |
|-----------|-------------|-----------|
| Contribution explicitness | 7 | Clear selective-head + span condition framing |
| Prior art differentiation | 7 | SRA/SMRA credited; differential articulated |
| Significance argument | 7 | Hate speech + faithfulness + theoretical account |
| Related work completeness | 7 | SRA, SMRA, entmax, Michel, Voita, Correia all covered |
| Novelty differential articulation | 7 | "Selective vs. full-head supervision" clearly stated |
| Cross-field consideration | 6 | CV analogy and entmax noted |

**Post-reposition mean:** 6.8 / 10 — PROCEED

---

## Remaining Conditions (tracked for N3 re-evaluation)

1. The value-subspace span condition must be stated as a formal proposition — if post-results analysis shows the span condition is just a restatement of Jain & Wallace, the theoretical contribution collapses
2. Experiment plan now correctly specifies SRA/SMRA baselines and ≥10 seeds — N2 gate should verify this
3. If NeurIPS reviewers reject the theoretical framing, venue should be reconsidered (ACL/EMNLP fallback)

---

## Gate Status

- [x] PROCEED with conditions
- [x] Reposition recorded (cycle 2)
- [x] Routing instructions followed: hypotheses revised, experiment plan updated
- [x] N2 gate will verify experiment design incorporates repositioning
