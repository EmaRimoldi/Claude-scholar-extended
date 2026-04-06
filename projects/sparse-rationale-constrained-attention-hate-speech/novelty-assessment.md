# Novelty Assessment — Gate N1

**Date:** 2026-04-01
**Gate:** N1 (post-hypothesis, pre-experiment-design)
**Decision:** PROCEED
**Kill decision script:** `.epistemic/kill-decision.json` — PROCEED (no criteria triggered)

---

## Contribution Statement

**Canonical form:**
> Sparsemax attention activation in gradient-importance-selected BERT CLS heads (Method) → improved faithfulness (comprehensiveness) and plausibility (IoU-F1/Token-F1) (Result) → HateXplain hate speech detection (Task) → by structurally aligning sparse attention distributions with binary rationale annotation targets (Mechanism)

**Three independent technical claims:**
- **C1**: Gradient-importance scoring selects BERT heads before applying rationale alignment supervision — no prior work tests this selection mechanism in this context
- **C2**: Sparsemax replaces softmax as the attention activation in supervised heads — never applied in a rationale-supervised setting in any NLP task
- **C3**: IG-based faithfulness evaluation with 5-seed bootstrap CIs — methodologically superior to LIME + ≤3 seeds used by all prior work on HateXplain

---

## Novelty Dimension Analysis

| Dimension | Applicable | Status | Primary? | Evidence source |
|-----------|-----------|--------|----------|----------------|
| Method novelty | Y | CLEAR | YES | claim-overlap-report.md (Mechanism: 0 overlap papers); adversarial-novelty-report.md (null search C1+C2) |
| Application novelty | Y | PARTIAL | NO | claim-overlap-report.md (Task: SRA/SMRA already on HateXplain) |
| Combination novelty | Y | CLEAR | YES | adversarial-novelty-report.md (Closest Prior Work: SRA covers 1/3 components; no paper covers C1+C2+C3) |
| Empirical novelty | Y | CLEAR | YES | claim-overlap-report.md (Method×Result: null); adversarial-novelty-report.md C3 |
| Theoretical novelty | N | N/A | NO | No formal propositions with proofs in hypotheses.md |
| Scale novelty | N | N/A | NO | Single dataset, English only |
| Negative result novelty | CONDITIONAL | POTENTIAL | NO | H2/H3/H4/H5 falsification would yield novel null results; not yet applicable at N1 |

**Primary novelty dimensions: Method (C1+C2) + Combination (C1+C2+C3) + Empirical (C3)**

---

## Prior Art Differentials

### Eilertsen et al. (2025) — SRA — AAAI 2025 [HIGH overlap]

- **What they do:** Apply MSE alignment loss between BERT layer 8 head 7 CLS attention and majority-vote token-level rationale mask, using softmax attention, n≤3 seeds, LIME-based faithfulness evaluation on HateXplain (English + Portuguese). Report 2.4× IoU-F1 improvement over unguided BERT.
- **What we do differently:** (a) Select supervised heads by gradient importance I(h,l) = E_x[|∂L_CE/∂A^{CLS,h,l}|] instead of fixed selection; (b) replace softmax with sparsemax as the CLS attention activation in supervised heads; (c) ablate alignment losses (MSE, KL, sparsemax_loss); (d) evaluate faithfulness with IG (not LIME), 5 seeds, bootstrap CIs (B=1000); (e) stratify results by annotator agreement (H6).
- **Why the difference matters:** The three technical differences target three unjustified design assumptions in SRA (A1: fixed head, A2: softmax, A3: MSE). The sparsemax structural alignment argument is non-trivial: exact-zero attention weights naturally match the binary rationale target, while softmax creates a persistent density mismatch regardless of the alignment loss. Head selection matters because supervising the wrong heads may harm their specialized functions (Michel et al. 2019 ~80% prunable). The IG evaluation matters because LIME instability on ~20-token posts is a validity concern that affects the entire prior literature.
- **Differential statement written and defensible:** YES

### Vargas et al. (2026) — SMRA — arXiv:2601.03481 [MEDIUM overlap]

- **What they do:** Extend SRA with Moral Foundations Theory rationale supervision (6 dimensions); introduce HateBRMoralXplain; same softmax BERT, focus on Portuguese.
- **What we do differently:** Same mechanistic advances as vs. SRA (sparsemax, head selection, IG evaluation). SMRA's key contribution (moral rationale taxonomy) is orthogonal to ours — we do not claim this.
- **Differential statement:** Our method vs. SMRA is identical to our method vs. SRA on the mechanism dimension. SMRA does not test sparsemax, head selection, or IG evaluation.

### Ribeiro, Felisberto & Neto (2020) — arXiv [MEDIUM overlap]

- **What they do:** Apply sparsemax to hierarchical attention networks for document sentiment classification; no rationale supervision; report limited unsupervised gains.
- **What we do differently:** We apply sparsemax under explicit human rationale annotation supervision. The key difference is unsupervised (no external target) vs. supervised (binary rationale mask). Ribeiro et al. find limited gains; our hypothesis is that the alignment loss combined with sparsemax drives gains not achievable by either alone.
- **Differential statement:** Unsupervised sparse attention ≠ rationale-constrained sparse attention.

### Chrysostomou & Aletras (2021) — TaSc — ACL 2021 [MEDIUM overlap]

- **What they do:** Learn task-specific scaling factors that modulate existing attention weights post-hoc; improve faithfulness without human rationale supervision; evaluated across 5 datasets and 5 encoders.
- **What we do differently:** TaSc improves faithfulness via learned scaling without any external annotation signal. Our work uses human token-level rationale annotations from HateXplain annotators as the training signal, and additionally replaces the attention activation function itself. These are different mechanisms: implicit learned scaling vs. explicit sparse activation + human annotation alignment.
- **Differential statement:** Implicit self-supervised scaling ≠ explicit human-supervised sparse alignment.

### Kim, Lee & Sohn (2022) — MRP — arXiv [MEDIUM overlap]

- **What they do:** Masked Rationale Prediction pre-training for hate speech on HateXplain; improves explainability and robustness.
- **What we do differently:** MRP is a pre-training task (predict masked rationale tokens), not direct attention supervision. No attention activation modification, no head selection, no alignment loss.
- **Differential statement:** Pre-training on rationale prediction ≠ runtime attention supervision with sparse activation.

### Ross et al. (2017) — "Right for the Right Reasons" — IJCAI [MEDIUM — cross-field]

- **What they do:** Constrain input gradients (∂L/∂x) to match human annotation masks via L2 penalty; general method for any differentiable model; applied to image/tabular classification.
- **What we do differently:** We constrain attention distributions (A^{CLS,h,l}) not input gradients; we use sparsemax activation replacement (not L2 penalty); we select which heads to constrain (Ross et al. have no multi-head component selection). The target space is fundamentally different: attention weight space vs. input gradient space.
- **Differential statement:** Constraining input gradients ≠ replacing attention activation with sparse operator + head importance selection.

---

## Significance Assessment

| Dimension | Rating | Justification |
|-----------|--------|--------------|
| Problem significance | HIGH | Hate speech detection is high-impact (platform policy, EU AI Act); explainability and fairness are regulatory requirements; Poletto et al. (2021) and Lyu et al. (2022) surveys identify rationale supervision as open problem |
| Improvement magnitude | MODERATE (expected) | Sparsemax structural alignment predicts improvement in comprehensiveness over SRA; H5 tests whether prior SRA gains are even credible at n=3; actual magnitude TBD by experiments |
| Generalizability | MODERATE | Method applies to any BERT-based classifier with token-level rationale annotations; HateXplain is English-only; sparsemax head selection applicable to other tasks with human annotations |
| Insight value | HIGH | H4 (LIME instability) teaches something methodologically important for the field — all prior LIME-based HateXplain evaluations would need reinterpretation if confirmed; H5 (SRA fragility) challenges prior reported results; structural alignment argument is a principled theoretical insight |

---

## Kill Criteria Check

| Criterion | Triggered | Notes |
|-----------|-----------|-------|
| Full anticipation | NO | SRA covers 3/7 claim components; no paper covers all 4 primary components (Method + Task + Result + Mechanism simultaneously) |
| Marginal differentiation | NO | Three independent technical advances (C1 head selection, C2 sparsemax, C3 IG+bootstrap) — not hyperparameter differences |
| Failed reposition count ≥ 2 | NO | First evaluation at N1; reposition_count = 0 |
| Significance collapse | NO | Problem significance HIGH; downstream applications clear (explainability + fairness in hate speech systems) |
| Concurrent scoop | NO | Recency sweep (Step 8) pending; adversarial search Pass 6 found no covering paper across 16+ queries |

**Kill script output:** `PROCEED` — no criteria triggered (see `.epistemic/kill-decision.json`)

---

## Search Coverage Summary

| Pass | Steps | Papers reviewed | New papers found | Threat level |
|------|-------|----------------|-----------------|--------------|
| Pass 1 (research-landscape) | 1 | ~58 papers, 6 clusters | 6 gaps identified | MEDIUM |
| Pass 4 (cross-field) | 2 | 48 papers across 5 fields | Ross et al. 2017, Shu 2025, HuMAL, SPLADE, CBM | MEDIUM (CV-EGL only) |
| Pass 2 (claim-search) | 4 | 16 queries, ~30 papers | TaSc (chrysostomou2021tasc) | MEDIUM |
| Pass 3 (citation-traversal) | 5 | ~80 second-order papers | Treviso2020, FRESH, Sen2020, Strout2019 | MEDIUM (unchanged) |
| Pass 6 (adversarial) | 6 | 5 attacks, 16 queries | 0 new covering papers | STRONG rebuttal |

**Total papers reviewed:** ~230 (unique)
**Kill signals across all passes:** 0
**Composite threat level:** MEDIUM (SRA as concurrent work; all MEDIUM papers differentiable)

---

## Attention-Faithfulness Differentiation Note (N1 Heuristic)

The hypotheses use the terms "attention faithfulness" and "faithfulness evaluation" (H2, H4, H5). These relate to ERASER-style comprehensiveness/sufficiency metrics and LIME stability — not to the Jain & Wallace (2019) attention-swap argument.

Our work does NOT claim "attention is inherently faithful" — it claims "supervised sparsemax attention is more faithful than supervised softmax attention under identical training conditions." This is a different claim. The attention-is-not-explanation debate (Jain & Wallace 2019, Wiegreffe & Pinter 2019) is about unsupervised attention distributions; our hypothesis concerns supervised distributions with an explicit alignment loss. Both papers are in our references and will be cited in the related work section to position the contribution correctly.

For the adversarial review (Step 35): the reviewer should verify that the manuscript clearly differentiates our supervised setting from the unsupervised setting in which the attention-faithfulness debate applies.

---

## Gate Decision

```
NOVELTY ASSESSMENT
==================
Gate: N1
Primary contribution: Method (C1+C2) + Combination + Empirical (C3)
Novelty level: CLEAR
Closest prior work: Eilertsen et al. (2025) SRA, AAAI 2025 — differentiable on 3 independent technical axes
Differential: (a) importance-guided head selection vs. fixed; (b) sparsemax vs. softmax activation; (c) IG+bootstrap vs. LIME+n≤3
Significance: HIGH (problem) / MODERATE (expected improvement magnitude) / MODERATE (generalizability) / HIGH (insight)
Problem significance: HIGH
Improvement magnitude: MODERATE (expected; to be confirmed by experiments)
Generalizability: MODERATE
Insight value: HIGH
Kill signals triggered: 0
Recommendation: PROCEED
Confidence: HIGH
Evidence: 5 search passes, ~230 papers reviewed, 16 adversarial queries, 0 kill signals, kill_decision.py PROCEED
```

**PROCEED to Step 8 (/recency-sweep sweep_id=1) then Step 9 (/design-experiments)**
