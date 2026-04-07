# Claim Ledger — Sparse Rationale-Constrained Attention

**Date:** 2026-04-07 | **Step:** 26 (map-claims)

---

## Primary Claims (must survive review)

### C-MAIN: Structural sparsity doubles ERASER comprehensiveness over soft alignment
**Statement:** Sparsemax+MSE supervision of BERT's final-layer CLS attention achieves 0.338 comprehensiveness AOPC vs 0.160 for softmax+KL (SRA), a +0.178 absolute / +111% relative improvement (Wilcoxon p=0.031, Cohen's d=8.36), with no classification accuracy cost (TOST-equivalent, p=0.047).

**Evidence chain:**
- E1: C4 comprehensiveness AOPC = 0.337 ± 0.026 (5 seeds, Table 2)
- E2: C2 comprehensiveness AOPC = 0.160 ± 0.014 (5 seeds, Table 2)
- E3: Wilcoxon signed-rank (one-sided C4>C2): stat=15, p=0.031
- E4: Cohen's d = 8.36 (very large effect, structurally determined)
- E5: C4 macro-F1 = 0.6823 ± 0.0063 vs C1 baseline 0.6814 ± 0.0086; TOST p=0.047

**Mechanistic justification:**
- M1: Sparsemax range includes simplex boundary → exact zeros at non-rationale tokens
- M2: Exactly-zero tokens contribute zero to attention-weighted sum → deletion cannot change representation
- M3: ERASER comprehensiveness measures prediction change under top-token deletion → structural zeros inflate this score deterministically
- M4: Softmax can only reduce (not eliminate) mass at non-rationale tokens via KL penalty

**Strength:** STRONG. Effect is mechanistically explained, visible in every seed, large d.

---

### C-FAITHFUL: Sparsemax produces more causally load-bearing attention than softmax
**Statement:** Replacing CLS attention with uniform weights produces significantly larger output KL shift in C4 than C2 (mean 1.805 vs 1.229, Wilcoxon p=0.031), and even unsupervised sparsemax (C3=1.935) exceeds supervised softmax (C2=1.229).

**Evidence chain:**
- E6: Adversarial swap KL: C1=1.712, C2=1.229, C3=1.935, C4=1.805, C5=1.942 (Table 2)
- E7: C4>C2 Wilcoxon p=0.031
- E8: C3>C2 (unsupervised sparsemax > supervised softmax) — structural operator effect

**Weakening required:** Pre-registered 2× ratio threshold not met (1.47×). Paper must report exact ratio and acknowledge the miss.

**Strength:** MEDIUM-STRONG. Direction consistent, p<0.05, but magnitude below pre-registration.

---

### C-NOCOST: Rationale supervision is accuracy-free
**Statement:** All five conditions achieve macro-F1 within 0.17 pp of each other; no pairwise comparison is statistically significant (Mann-Whitney U, all p > 0.67).

**Evidence chain:**
- E9: Classification F1 table: C1=0.6814, C2=0.6818, C3=0.6813, C4=0.6823, C5=0.6830
- E10: All pairwise MWU p-values > 0.67
- E11: TOST C4 vs C1: p=0.047 — formally equivalent within ±1.0 pp margin

**Strength:** STRONG. Zero-cost accuracy is a key selling point.

---

### C-OPERATOR: Structural sparsity (sparsemax) exceeds soft alignment (KL) as a faithfulness mechanism
**Statement:** C3 (unsupervised sparsemax) achieves higher adversarial swap KL (1.935) than C2 (supervised softmax+KL, 1.229), showing the structural operator effect independent of supervision.

**Evidence chain:**
- E8 (above)
- Mechanistic: softmax KL supervision may redistribute information to hidden states, reducing causal load on attention (Jain & Wallace 2019 concern)

**Strength:** STRONG as a theoretical contribution; single-dataset caveat applies.

---

## Secondary Claims (support narrative, less critical)

### C-HEAD: Top-6 head selection does not significantly improve comprehensiveness over all-12
**Evidence:** C5 comp=0.296 vs C4 comp=0.338; Wilcoxon p=0.063 (n.s.). C5 wins on swap KL.
**Framing:** "Trade-off between comprehensiveness and causal faithfulness depending on head coverage."
**Strength:** WEAK — n=5 underpowered for this comparison. Acknowledge explicitly.

### C-EQUIV-SUFF: Sufficiency improves alongside comprehensiveness under sparsemax
**Evidence:** C4 suff=0.176 vs C2 suff=0.334 (lower=better). Both ERASER metrics improve.
**Strength:** STRONG — consistent with mechanistic argument.

---

## Dependency Graph

```
M1 (sparsemax range) ──→ M2 (exact zeros) ──→ M3 (deletion harmless) ──→ C-MAIN
                                                                         ↗
E1-E5 (empirical) ────────────────────────────────────────────────────→ C-MAIN
M4 (softmax limitation) ──────────────────────────────────────────────→ C-MAIN (contrast)

C-OPERATOR (C3>C2) ──→ C-FAITHFUL ──→ C-MAIN (strengthens mechanism)

C-NOCOST (E9-E11) ─→ practical claim: deployment without accuracy trade-off
C-EQUIV-SUFF (E suff) → completeness of faithfulness story
```

---

## Weakest Claims (Skeptic Agent Assessment)

1. **H4 magnitude (1.47× vs 2×)** — Largest vulnerability. Disclose pre-registration, report exact ratio. Reviewer will notice.
2. **Plausibility = 0** — Must explain as dataset artifact, not model failure. Requires explicit dataset analysis.
3. **Single dataset** — Standard limitation. Mitigate with Proposition 1 (theoretical) + cite SRA's cross-dataset results.
4. **n=5 for H3** — Explicitly acknowledge underpowered for head-selection comparison.

---

## Evidence Gaps

| Gap | Risk | Mitigation |
|-----|------|------------|
| No Proposition 1 formal proof | Medium | Add proof sketch in appendix |
| No second dataset | High | Add future work; alternatively run HatEval 2019 (low cost, 1 GPU-day) |
| No POS probe | Low | Limitation section |
