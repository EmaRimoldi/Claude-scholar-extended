# Claim-Source Alignment Report (Step 33)

**Date:** 2026-03-30
**Step:** 33 / 38
**Inputs:** manuscript/main.tex, .epistemic/claim_graph.json, analysis-report.md

---

## Exit Code: 0 (no hard-block violations after revisions)

---

## Sub-Check 1: Abstract Claims ⊆ Conclusion Claims ⊆ Evidence

### Abstract claims (extracted):

| Abstract Claim | In Conclusion? | In Evidence? | Status |
|---------------|---------------|-------------|--------|
| "Selective-head sparsemax supervision achieves higher comprehensiveness than full-head" | YES | YES (H1: +2.0%, p=0.001) | OK |
| "Without degrading classification F1" | YES | YES (ΔF1 not significant) | OK |
| "Gradient importance scoring drives the gain" | YES | YES (H4: +3.4% vs. random) | OK |
| "Value-subspace span condition predicts invariance" | YES | YES (H5: ρ=−0.87) | OK |
| "Building on SRA and SMRA" | YES | YES (citations present) | OK |

No abstract claims without corresponding evidence.

---

## Sub-Check 2: No Overclaiming

### Potential overclaims identified and resolved:

| Original Draft | Issue | Revised Version | Status |
|---------------|-------|----------------|--------|
| "substantially outperforms all prior work" | Too strong; SMRA sufficiency gap is small | "achieves statistically significant improvement in comprehensiveness over all baselines" | FIXED |
| "explains why attention supervision works" | Too broad; span condition is a sufficient condition, not a complete explanation | "provides a sufficient condition (span condition) for functional invariance under attention constraint" | FIXED |
| "demonstrating the first theoretically-grounded approach to hate speech attention supervision" | SRA has no theory, but "first" is risky | "providing the first theoretical analysis of selective attention supervision via value-subspace span condition" | FIXED |

---

## Sub-Check 3: Causal Claims

| Causal Claim | Causal Evidence? | Appropriate Hedge? | Status |
|-------------|-----------------|-------------------|--------|
| "Selective head importance scoring *causes* comprehensiveness improvement" | H4 (random vs. importance selection): isolates the causal factor | Changed to "is responsible for" | OK |
| "Value subspace alignment *causes* F1 preservation" | H5: correlation only; K-sweep is correlational | Hedged to "strongly predicts" | OK |

---

## Sub-Check 4: Confidence Calibration

- Confidence tracker checked: all claims have entries
- High-confidence claims (≥0.80): H1, H2, H3, H4 outcomes — appropriately asserted
- Medium-confidence claims (0.50–0.79): H5 span condition, annotator stratification — appropriately hedged
- The theoretical Proposition 1 is stated as a "conditional proposition" with explicit assumptions

---

## Sub-Check 5: Limitations Honest Acknowledgment

| Limitation | In Manuscript? | Location | Adequate? |
|-----------|--------------|---------|----------|
| Single dataset (HateXplain) | YES | Section 5 (Limitations) | YES |
| SMRA replication annotation difference | YES | Section 4.3 | YES |
| Normal class F1 slight degradation | YES | Section 4.1 | YES |
| Span condition is sufficient not necessary | YES | Appendix A | YES |
| ρ=−0.87 does not prove causation | YES | Section 4.4 | YES |

---

## Hard Block Status

**No hard block violations.** Previous draft had one hard-block: "demonstrates X is not JUST attention-based" — this was reverted. Current manuscript has no claims stronger than evidence warrants.

---

## Gate Status

- [x] All abstract claims traced to evidence
- [x] No overclaiming remaining after revisions
- [x] Causal claims appropriately hedged
- [x] Limitations section complete and honest
- [x] Exit code 0: continue to Step 34
