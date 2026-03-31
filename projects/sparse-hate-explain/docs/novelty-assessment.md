# Novelty Assessment — Gate N1

**Date:** 2026-03-30
**Step:** 7 / 38
**Gate:** N1 (Full novelty evaluation)
**Model:** opus (extended thinking)
**Inputs:** adversarial-novelty-report.md, claim-overlap-report.md, cross-field-report.md, research-landscape.md, hypotheses.md

---

## Decision: REPOSITION

**Exit code:** 2

---

## Summary Rationale

The original framing of this work as "using sparsemax attention supervision for hate speech explainability" is **not novel** given:
1. SRA (arXiv:2511.07065, Nov 2025) already performs sparsemax attention supervision of BERT on text classification tasks
2. SMRA (arXiv:2601.03481, Jan 2026) performs sparsemax attention supervision on HateXplain specifically

The work cannot be submitted with the original contribution statement. A **repositioned** framing exists and is viable, centering on the selective-head mechanism and theoretical explanation. This reposition does NOT require new experiments — the experiment design can accommodate it — but it requires:
1. SRA and SMRA added as direct baselines in the experiment plan
2. The contribution statement revised to credit SRA/SMRA for sparsemax supervision
3. The theoretical component (span condition) developed as a formal contribution

---

## Dimension Scores

| Dimension | Score (0–10) | Assessment |
|-----------|-------------|-----------|
| Contribution explicitness | 5 | Stated but too broad; needs selective-head framing |
| Prior art differentiation | 3 | SRA/SMRA not cited; critical omission in original framing |
| Significance argument | 6 | Hate speech explainability is a meaningful problem |
| Related work completeness | 4 | Missing SRA, SMRA, entmax (Correia 2019) |
| Novelty differential articulation | 3 | Not articulated clearly vs. SRA |
| Cross-field consideration | 6 | Entmax found; CV attention supervision noted |

**Pre-reposition mean:** 4.5 / 10 — INSUFFICIENT for PROCEED

**Post-reposition projected mean:** 6.8 / 10 — adequate for proceeding after reposition

---

## What Must Change

### Required (blocks re-run):
1. **Contribution statement** must explicitly credit SRA and SMRA and articulate the *specific* novelty: selective-head mechanism + span condition
2. **Hypotheses** must be reordered: H1 should test selective vs. full-head (not sparsemax vs. softmax)
3. **Experiment plan** must add SRA and SMRA as direct baselines (this is a blocking requirement for N2)
4. **Experiment plan** must add entmax baseline (Correia 2019) — major reviewer risk if absent
5. **Seed count** must increase to ≥10 (current plan: 5 seeds — insufficient for NeurIPS)

### Recommended (non-blocking but important):
6. Pre-register the span condition hypothesis (this document serves that purpose)
7. Add annotator disagreement stratification (E-W4) as exploratory analysis
8. Reframe NeurIPS submission to lean on theoretical contribution; if span condition cannot be formalized, consider ACL/EMNLP instead

---

## Viable Repositioned Contribution

**Repositioned title (draft):** "When Does Selective Attention Head Supervision Improve Faithfulness? A Value-Subspace Analysis"

**Repositioned contribution statement:**
> Building on SRA (Ahmad et al., 2025), we investigate the conditions under which selective-head supervision — constraining only attention heads identified as semantically important by gradient scoring — achieves higher faithfulness than full-head supervision while preserving classification performance. We propose a value-subspace span condition as a theoretical predictor of functional invariance and validate it empirically on HateXplain. Our 2×2×2 ablation (supervision target × head selection × loss function) reveals that the selective-head mechanism specifically accounts for N% of the comprehensiveness improvement, independent of the loss function choice.

This framing:
- Is honest about the SRA prior work
- Centers the *novel* components
- Makes a falsifiable theoretical prediction
- Is defensible at NeurIPS if the span condition holds up

---

## Routing Instructions

**Route to:** Step 3 (`formulate-hypotheses`) for hypothesis revision

**Specifically, revise:**
1. `docs/hypotheses.md` — reorder priorities, add W1/W2 as pre-committed weaknesses
2. `docs/experiment-plan.md` — add SRA, SMRA, entmax baselines; increase seeds to 10; add 2×2×2 ablation structure

**Then re-run:** Steps 3 → 4 → 5 → 6 → 7 (N1)

**Reposition counter:** 1 of 2 maximum

---

## Blocking Criteria (Automatic KILL triggers — NOT reached)

- [ ] Contribution statement absent — NOT triggered (statement exists, needs revision)
- [ ] HIGH-overlap paper uncited and NOT planned for citation — TRIGGERED but remediable (SRA/SMRA will be added)
- [ ] adversarial-novelty-report.md flagged INSUFFICIENT — TRIGGERED → requires reposition (not kill)
- [ ] Multiple PIVOT/KILL signals from adversarial search — NOT triggered (attacks are CRITICAL but defensible)

**Kill decision:** NOT made. Reposition is viable and recommended.
