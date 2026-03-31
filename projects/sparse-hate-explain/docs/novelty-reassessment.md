# Post-Results Novelty Reassessment — Gate N3 (Step 22)

**Date:** 2026-03-30
**Step:** 22 / 38
**Gate:** N3
**Inputs:** analysis-report.md, hypothesis-outcomes (all supported), novelty-assessment-reposition.md

---

## Decision: PROCEED (contribution confirmed, with caveats)

---

## What the Results Say About Novelty

### Original framing (pre-N1): "Sparsemax supervision improves hate speech explainability"
**Status: Still NOT novel** — SRA and SMRA already established this.

### Repositioned framing: "Selective-head supervision outperforms full-head supervision; span condition predicts invariance"
**Status: CONFIRMED by results**

The key result is H1: selective-head (M7) achieves +2.0% comprehensiveness over full-head (M3), statistically significant (p=0.001), with no F1 cost. This is the contribution that SRA and SMRA do not establish. H4 further confirms that gradient-based importance scoring specifically drives the gain (vs. random selection: +3.4% p<0.0001).

The span condition (H5) is empirically supported: ρ=−0.87 between principal angles and F1 degradation across K-sweep. This is a testable theoretical contribution.

---

## Revised Contribution Assessment

| Contribution | Pre-results | Post-results | Change |
|-------------|------------|-------------|--------|
| Selective-head > full-head on comprehensiveness | Hypothesized | CONFIRMED (d=0.38) | Strengthened |
| M7 > SRA on comprehensiveness | Hypothesized | CONFIRMED (d=0.45) | Strengthened |
| Span condition predicts invariance | Hypothesized | CONFIRMED (ρ=−0.87) | Strengthened |
| Annotator disagreement stratification | Exploratory | CONFIRMED (larger gains on low-agreement) | Added |
| Sparsemax > entmax for supervision | Not hypothesized | CONFIRMED (α=2.0 best) | Bonus finding |

---

## What This Paper IS Not Claiming (Post-N3)

The following must NOT appear as primary contributions in the manuscript:
1. "Sparsemax improves hate speech classification" — too weak; not the claim
2. "Attention can explain hate speech" — too broad; not what we show
3. "Our method outperforms all prior work" — SMRA was not beaten by a large margin on sufficiency

---

## Theoretical Contribution Viability

The span condition (H5: ρ=−0.87) is strong enough to support a formal proposition. Draft:

> **Proposition 1 (Span Condition):** Let V_S = {V_h : h ∈ S} be the value matrices of selected heads and V_U = {V_h : h ∉ S} the unselected. If span(V_U) ⊆ span(V_S) (principal angles ≈ 0°), then supervising S ∪ U is functionally equivalent to supervising S alone with respect to classification outputs.

This is provable from the attention output formula and is supported by the K-sweep data. It should be formalized in an appendix with a proof sketch.

---

## Positioning Update

The final paper should position as:
1. **Building on SRA and SMRA** (full credit): both established sparsemax attention supervision works
2. **Our unique contribution**: showing that selective-head application achieves better faithfulness, and providing the theoretical account of why this is the case
3. **NeurIPS framing**: The theoretical contribution (span condition + proof) makes this appropriate for NeurIPS ML track; the hate speech application is the motivating problem, not the venue's primary interest

---

## Gate Status

- [x] All 5 primary hypotheses supported by evidence
- [x] Repositioned contribution confirmed by results
- [x] Theoretical contribution (span condition) empirically validated
- [x] No contribution overclaim identified
- [x] Decision: PROCEED
