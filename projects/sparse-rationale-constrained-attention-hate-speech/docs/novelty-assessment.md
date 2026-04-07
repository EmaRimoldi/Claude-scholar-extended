# Novelty Assessment — Gate N1

**Date:** 2026-04-07
**Gate:** N1 (Post-hypothesis, Pre-experiment design)
**Decision:** PROCEED

---

## Contribution Statement

**Sparsemax-projected CLS attention supervised by HateXplain rationale masks** achieves **higher ERASER comprehensiveness without macro-F1 degradation** on **HateXplain hate speech detection** by **structurally forcing exactly-zero attention weight on non-rationale tokens, eliminating probability-mass leakage by construction rather than by KL/MSE penalty** (`eilertsen2025aligning` alternative).

---

## Novelty Dimension Analysis

| Dimension | Applicable? | Status | Evidence Source |
|-----------|------------|--------|----------------|
| Method novelty | YES | **CLEAR** | Sparsemax never combined with human rationale supervision in any task — confirmed by 6 search passes, 17 claim queries, 5 adjacent fields |
| Application novelty | YES | **PARTIAL** | Hate speech detection on HateXplain is shared with SRA (`eilertsen2025aligning`); differentiation via mechanism |
| Combination novelty | YES | **CLEAR** | Sparsemax × human rationale supervision × HSD — no paper combines these three |
| Empirical novelty | YES | **PARTIAL** | Comprehensiveness improvement on HateXplain is novel; sufficiency improvement claimed by SMRA but via different route |
| Theoretical novelty | YES | **PARTIAL** | Structural zero vs. soft penalty distinction is theoretically grounded; requires formal proposition |
| Scale novelty | NO | — | — |
| Negative result novelty | Contingent | — | If H1 sufficiency fails to improve, negative result characterization may apply |

**Primary novelty dimensions: Method + Combination** (CLEAR)
**Supporting novelty dimensions: Empirical + Theoretical** (PARTIAL, strengthened by H4)

---

## Per-Dimension Prior Art Assessment

### Method Novelty — CLEAR

No prior work applies sparsemax (or α-entmax) with human annotation supervision as the constraint source in any task. The foundational sparsemax literature (`martins2016sparsemax`, `correia2019adaptively`) is unsupervised. The constrained sparsemax for NMT (`malaviya2018sparse`) uses algorithmic fertility bounds, not human annotations.

**Confidence:** HIGH (17 claim-level queries, 5 adjacent fields, 54 landscape papers — all confirm 0 papers)

### Application Novelty — PARTIAL

HateXplain hate speech detection is the primary evaluation domain of SRA (`eilertsen2025aligning`) and SMRA (`vargas2026smra`). The application domain is shared. However, the cross-field report confirms that no adjacent field has produced equivalent work (cite-and-differentiate for Malaviya 2018 and Le 2023).

**Differential to SRA:** We use a different attention operator (sparsemax vs. softmax) that changes the structural properties of the model. This is a methodological contribution that extends the application novelty beyond "a different paper on HateXplain."

### Combination Novelty — CLEAR

The specific combination of (sparsemax) × (human rationale annotation constraint) × (HSD) is confirmed absent across all 6 search passes. This is the primary novelty claim.

### Empirical Novelty — PARTIAL

Claiming comprehensiveness improvement on HateXplain is directionally novel (SRA claims 2.4× IoU F1 improvement, not comprehensiveness specifically). The specific claim "structural sparsity improves ERASER comprehensiveness" has no prior empirical demonstration. SMRA claims sufficiency improvement (+2.3pp) via moral rationale alignment — our contribution to comprehensiveness via sparsemax is empirically distinct.

However, the magnitude of the expected improvement (Δ ≥ +0.04 AOPC, H1 prediction) is based on a 3-seed mini-project. This needs 5-seed replication.

### Theoretical Novelty — PARTIAL

The theoretical claim that structural zero attention guarantees provably maximal comprehensiveness for the masked tokens requires formal proof. The argument is clear (zero-weight token → cannot affect CLS representation → comprehensiveness contribution = 0 by construction), but it should be stated as a formal proposition with proof sketch (not just an empirical claim). Without this, the theoretical novelty is "stated" not "proven."

**Action required (Theoretical Claim Heuristic triggered):** H4 (adversarial swap test) directly engages the Jain-Wallace debate. The theoretical contribution must be explicitly differentiated from Jain & Wallace (2019): we are not claiming that attention IS explanation (JW debate), but that supervised sparsemax attention CANNOT fail to exclude zero-weight tokens from computation (a structural property, not a post-hoc correlation). This requires a formal proposition.

---

## Differential Articulation

### vs. eilertsen2025aligning (SRA) — HIGH overlap

> SRA (`eilertsen2025aligning`) proposes supervised softmax attention for HSD via KL-divergence loss. Our work uses sparsemax, which changes the range of the attention operator from the open simplex interior to the closed simplex (including zero-probability boundary). This structural change: (1) guarantees exact zero weight on non-rationale tokens (vs. reduced-but-nonzero); (2) produces analytically maximal comprehensiveness for zero-weight tokens by construction; (3) predicts a larger Jain-Wallace adversarial swap perturbation because the sparse support is a hard computational dependency. The specific technical advance is: operator range change → structural faithfulness guarantee → verifiable via H4 adversarial swap. This is not a tuning of SRA's loss weight.

### vs. vargas2026smra (SMRA) — MEDIUM overlap

> SMRA (`vargas2026smra`) uses Moral Foundations Theory expert-annotated moral spans as supervision signal for attention alignment in Portuguese hate speech detection (HateBRMoralXplain). Our contribution uses crowd-sourced HateXplain rationale annotations (English) and sparsemax structural projection. The annotation semantics (moral MFT vs. hate-evidential spans), the operator (softmax vs. sparsemax), the language (Portuguese vs. English), and the dataset are all different.

### vs. malaviya2018sparse — MEDIUM overlap

> Constrained sparsemax for NMT (`malaviya2018sparse`) uses upper-bound fertility constraints for coverage in generation tasks. Our constraint is a binary support mask from human annotation, applied in classification, with ERASER faithfulness evaluation. See cross-field-report.md for full differential.

---

## Significance Assessment

**Problem significance:** HIGH
- Hate speech detection is a deployed content moderation task with millions of decisions/day
- Explainability is required for responsible AI deployment (EU AI Act, platform trust)
- The faithfulness of explanations is an unsolved problem (Jain-Wallace debate unresolved for softmax)
- Evidence: multiple papers in 2024-2026 explicitly target this problem (SRA, SMRA, RISE, HateCOT, TARGE)

**Improvement magnitude:** MODERATE (estimated pre-experiment)
- Hypothesis H1 predicts Δ ≥ +0.04 AOPC comprehensiveness, Cohen's d ≥ 0.5 (medium effect size)
- Mini-project signal: "statistically significant" comprehensiveness improvement over 3 seeds
- Pre-experiment: not yet confirmed with 5-seed design

**Generalizability:** MODERATE
- Primary claim is specific to HateXplain (single dataset)
- Extension to HateBRXplain (W5a) and Davidson 2017 (W5b) planned
- The structural-sparsity mechanism generalizes beyond HSD to any short-text classification with rationale annotations
- NeurIPS venue fit: see Venue Warning below

**Insight value:** HIGH
- The structural-zero argument resolves the faithfulness-via-attention debate for a specific case: if zero-weight, then provably excluded
- The adversarial swap test (H4) provides empirical evidence that sparsemax supervision is causally constraining, not just cosmetically correlated
- Head-selective supervision (H3) provides mechanistic insight into when and which heads benefit from rationale supervision

---

## Kill Criteria Evaluation

| Criterion | Status | Notes |
|-----------|--------|-------|
| full_anticipation | NOT TRIGGERED | No paper does sparsemax + HSD + rationale supervision |
| marginal_differentiation | NOT TRIGGERED | Differential is structurally precise (operator range), not marginal |
| failed_reposition_count | NOT APPLICABLE (count=0) | First N1 evaluation |
| significance_collapse | NOT TRIGGERED | Problem is demonstrably high-significance |
| concurrent_scoop | NOT TRIGGERED | SRA/SMRA confirmed; neither uses sparsemax |

**Kill signals: 0**

---

## Gate Decision

```
NOVELTY ASSESSMENT
==================
Gate: N1
Primary contribution: Method novelty (CLEAR) + Combination novelty (CLEAR)
Novelty level: CLEAR on primary dimensions; PARTIAL on empirical/theoretical
Closest prior work: eilertsen2025aligning (SRA, AAAI 2026)
Differential: Sparsemax structural zero vs. softmax KL penalty; operator range change; 3 testable predictions
Significance: HIGH problem, MODERATE improvement magnitude, MODERATE generalizability, HIGH insight
Problem significance: HIGH
Improvement magnitude: MODERATE (pre-experiment estimate; must be confirmed with 5 seeds)
Generalizability: MODERATE (single dataset primary; extensions planned)
Insight value: HIGH
Kill signals triggered: 0
Recommendation: PROCEED
Confidence: HIGH
Evidence: Pass 1 (54 papers), Pass 2 (17 queries, 7 components), Pass 3 (22 papers),
          Pass 4 (5 fields), Pass 6 (5 attacks, 0 kill signals), Cross-field (cite-and-differentiate)
```

---

## Venue Warning

[VENUE WARNING] Single-dataset empirical NLP contribution submitted to NeurIPS.
NeurIPS/ICML/ICLR reviewers typically expect either:
  (a) a theoretical contribution that generalizes across domains, or
  (b) evaluation on multiple datasets and/or modalities.

The current contribution may be better suited for ACL / EMNLP / NAACL, where
single-dataset NLP results are an accepted community norm.

**Recommendation to address venue fit (required before final manuscript):**
1. Formalize the structural-zero faithfulness claim as Proposition 1 with proof sketch (promotes theoretical novelty to primary)
2. Add HateBRXplain cross-lingual evaluation (W5a) as a second dataset
3. Report adversarial swap test (H4) as the primary mechanistic contribution — this differentiates from prior work on both theoretical and empirical dimensions

This is a WARNING, not a BLOCK. The venue decision belongs to the researcher. The experiment design step should incorporate these requirements.

---

## Routing Instructions for Experiment Design

Proceed to Step 8 (`/recency-sweep sweep_id=1`) then Step 9 (`/design-experiments`) with these requirements:

**Must-have experiments** (required for N1 justification):
- H1: sparsemax vs. SRA-softmax comprehensiveness comparison (5 seeds, ERASER metrics)
- H4: Jain-Wallace adversarial swap test (causality test)
- H2: HateXplain rationale sparsity analysis (confirms motivation)

**Should-have experiments** (required for NeurIPS venue fit):
- H3: head-selective supervision (ablation depth)
- H5: identity-term FPR (fairness narrative)
- W5a: HateBRXplain cross-lingual (second dataset for venue fit)

**Formal contribution required:**
- Proposition 1: structural zero claim (proof sketch: if sparsemax assigns zero weight, the token cannot affect the CLS representation — prove from attention mechanism definition)
