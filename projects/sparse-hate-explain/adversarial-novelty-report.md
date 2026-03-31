# Adversarial Novelty Report (Step 6 — Pass 6)

**Date:** 2026-03-30
**Step:** 6 / 38
**Mission:** Actively attempt to kill the novelty claim. Every argument that a hostile reviewer would make.
**Model:** opus (extended thinking)

---

## Target Claim

> "Selective-head sparsemax supervision of BERT's CLS attention — supervising only the semantically important heads identified by gradient importance scoring — produces more faithful and plausible explanations than full-head softmax supervision, without degrading classification F1, and this functional invariance can be explained by a value-subspace span condition."

---

## Attack 1: The SRA Attack (CRITICAL)

**Attack:** "This paper is a minor extension of SRA (arXiv:2511.07065). SRA already supervises BERT attention using sparsemax on human rationales. The selective-head component is a straightforward engineering variation, not a research contribution."

**Evidence for attack:**
- SRA published Nov 2025; supervises BERT [CLS] attention with sparsemax; trains on human rationale annotations
- SRA evaluates faithfulness metrics (comprehensiveness, sufficiency) — same metrics as proposed work
- The only addition is "which heads" — but head selection via gradient importance is already Michel et al. (2019) and Voita et al. (2019)

**Differential defense:**
1. SRA supervises all heads uniformly; we show that selective supervision achieves higher comprehensiveness (quantitative improvement)
2. The *theoretical* explanation (span condition) is absent from SRA
3. SRA does not test on hate speech; SMRA does, but neither performs the head importance analysis
4. The 2×2×2 ablation cleanly disentangles factors that SRA conflates

**Verdict:** This attack has substantial merit. The defense is defensible but not airtight. **If the authors do not include a direct experimental comparison with SRA, this attack is fatal.**

**Required response:** Include SRA as a direct baseline. Show quantitative improvement specifically from the selective-head mechanism over SRA's full-head supervision.

---

## Attack 2: The SMRA Double-Threat (CRITICAL)

**Attack:** "SMRA (arXiv:2601.03481) already does sparsemax attention supervision on HateXplain specifically. The proposed work duplicates SMRA's core experimental setup on the same dataset with the same model."

**Evidence for attack:**
- SMRA: sparsemax supervision + HateXplain + BERT + comprehensiveness/sufficiency metrics
- This is the exact experimental setup of the proposed work
- SMRA published Jan 2026, 2 months before submission

**Differential defense:**
1. SMRA focuses on *moral value* rationales (a specific annotation dimension of HateXplain); proposed work uses the standard hate/offensive/normal rationales
2. SMRA does not do head selection or importance analysis
3. SMRA does not provide a theoretical explanation

**Verdict:** This is a serious problem. If the paper does not cite SMRA and show clear differentiation, it will likely be desk-rejected from NeurIPS. **This paper must be in the related work with an honest comparison table.**

---

## Attack 3: Head Selection Novelty (MAJOR)

**Attack:** "Head selection by gradient importance is not novel. Michel et al. (2019) introduced gradient-based head importance scoring for pruning. Voita et al. (2019) analyzed specialized heads. The proposed work is applying a known head selection technique (Michel 2019) to a known attention supervision task (SRA 2025)."

**Evidence for attack:**
- Michel et al. (2019) compute head importance by gradient magnitude w.r.t. a head's output; proposed work uses same approach
- Voita et al. (2019) show specialized heads; motivates selective supervision
- The *combination* of these is new, but combining A (known) + B (known) = C that is obviously implied

**Differential defense:**
1. No prior work applies importance-based selection to *supervision* (vs. pruning): Michel et al. prune heads, we supervise selected heads — different objective
2. The empirical claim is that *importance-guided selection for supervision* outperforms random selection or full supervision — this specific hypothesis has not been tested
3. The theoretical analysis (span condition) formalizes why this works, which is genuinely new

**Verdict:** This attack is moderately strong but can be defended. The key is: "we use importance for supervision selection, not pruning, and show this produces gains" is testable and testably different.

---

## Attack 4: Span Condition is Post-Hoc (MAJOR)

**Attack:** "The value-subspace span condition is a post-hoc theoretical rationalization. Jain & Wallace (2019) already showed that attention can be arbitrarily changed without affecting predictions in many settings. The span condition restates this known observation in different notation."

**Evidence for attack:**
- Jain & Wallace (2019): adversarial swap shows predictions invariant to attention perturbations
- Wiegreffe & Pinter (2019): counter-argument, but only under specific conditions
- The span condition essentially says "if you supervise heads whose value vectors span the same subspace as unsupervised heads, the decision boundary is unaffected" — this is closely related to the Jain & Wallace result

**Differential defense:**
1. The span condition provides a *sufficient condition* for invariance, not just an empirical observation
2. It is formalizable as a proposition with a proof sketch
3. It makes a testable prediction: principal angles between value subspaces should correlate with F1 degradation

**Verdict:** This attack has merit. The defense requires the span condition to be stated as a formal proposition with a proof, not just informal reasoning. Without formalization, this theoretical contribution is weak.

---

## Attack 5: Generalizability (MAJOR)

**Attack:** "The paper uses a single dataset (HateXplain) with a specific annotation paradigm. The results may not generalize. This limits the contribution to a narrow experimental setting."

**Evidence for attack:**
- Only HateXplain tested
- HateXplain has well-known annotation quality issues (Davani et al. 2024)
- Results on comprehensiveness in the mini-project: 3-run average, statistically significant but small effect sizes

**Differential defense:**
1. HateXplain is the standard benchmark for this sub-problem
2. Out-of-domain generalization is explicitly listed as a limitation
3. The theoretical contribution (span condition) is dataset-agnostic

**Verdict:** This is a limitation, not a fatal flaw. Will reduce acceptance probability at NeurIPS (which expects broader evaluation). More acceptable at ACL/EMNLP.

---

## Attack 6: Venue Mismatch (MODERATE)

**Attack:** "This paper belongs at ACL or EMNLP, not NeurIPS. NeurIPS reviewers expect broader methodological contributions, stronger theoretical analysis, and evaluation beyond a single NLP dataset."

**Evidence for attack:**
- NeurIPS 2026 ML track: expects either (a) broad methodological contribution applicable across ML domains, or (b) strong theoretical results
- The span condition is NeurIPS-relevant only if formalized
- HateXplain-only evaluation is narrow for NeurIPS
- ACL would be more appropriate for hate speech + NLP explanation methodology

**Differential defense:**
1. The theoretical contribution (span condition) could make this NeurIPS-appropriate
2. The broader interpretation: "sparse constrained optimization of model internals" could be framed as an ML contribution
3. If submitted to NeurIPS ML track, must lean harder on the theoretical angle

**Verdict:** NeurIPS is achievable but requires the theoretical contribution to be central and well-developed. If the span condition is weak, this is an ACL/EMNLP paper.

---

## Adversarial Summary

| Attack | Severity | Defensible | Required Fix |
|--------|---------|-----------|-------------|
| 1. SRA overlap | CRITICAL | Conditionally | Add SRA as direct baseline |
| 2. SMRA overlap (same dataset) | CRITICAL | Conditionally | Cite SMRA, show clear differentiation |
| 3. Head selection not novel | MAJOR | Yes | Frame as supervision-selection (not pruning) |
| 4. Span condition post-hoc | MAJOR | With formalization | Formalize as proposition with proof |
| 5. Single dataset | MAJOR | Yes (with limitations) | Acknowledge; do not overclaim |
| 6. Venue mismatch | MODERATE | Conditionally | Strengthen theoretical angle for NeurIPS |

**Overall adversarial verdict:** REPOSITION. The core method (sparsemax + supervision) is not novel standalone. A defensible contribution exists at the intersection of (selective-head mechanism) + (ablation disentanglement) + (theoretical formalization), but only if the paper is honest about what SRA and SMRA already did.

**INSUFFICIENT** — original hypothesis framing must be revised before proceeding to design.

---

## Recommended Repositioned Contribution Frame

> "We study when and why selective attention head supervision outperforms full-head supervision. Our main contribution is the identification of a value-subspace span condition that predicts functional invariance under attention constraint, which explains the surprising result that supervising fewer heads can improve faithfulness without sacrificing F1. We demonstrate this on hate speech detection where we show the 2×2×2 design of supervision target × head selection × loss function reveals qualitatively different regimes."

This frame:
- Does not claim sparsemax supervision is new (gives full credit to SRA)
- Does not claim head selection is new (gives credit to Michel, Voita)
- Claims: (1) the *combination* in the specific context of rationale supervision, (2) the theoretical explanation, and (3) the 2×2×2 ablation
