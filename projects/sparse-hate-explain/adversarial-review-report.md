# Adversarial Review Report (Step 35 — Pre-Submission)

**Date:** 2026-03-30
**Step:** 35 / 38
**Inputs:** manuscript/ (post-cycle-2 revision), paper-quality-report.md (PASS)
**Three reviewers:** R1 (Methods Expert), R2 (Hate Speech / NLP Application Expert), R3 (ML Theory Skeptic)

---

## Reviewer R1: Methods Expert

### R1.1 — CRITICAL: Incremental extension of SRA/SMRA

> "This paper is a minor extension of SRA (Ahmad et al., 2025) and SMRA (arXiv:2601.03481). SRA already performs sparsemax attention supervision on text classification; SMRA performs this exact task on HateXplain. The proposed selective-head mechanism adds a small variation that does not rise to the level of a full research contribution. The 2.0% comprehensiveness improvement over M3 (full-head sparsemax) is modest and may not generalize beyond the single dataset tested."

**Severity:** CRITICAL
**Route_to:** `/position` — related work framing must center the comparison explicitly; the paper must argue that 2.0% comprehensiveness improvement is meaningful by the standards of the field

**Assessment (evaluator):** This attack is correctly identified. It is the most likely killer argument. The paper's revised abstract and comparison table (I1 fix) address this partially but may not satisfy a hostile reviewer. The response must make the case that the *mechanistic disentanglement* (2×2×2 ablation showing head selection factor accounts for most of the gain) and the *theoretical account* are contributions beyond SRA, not just a +2% result.

---

### R1.2 — MAJOR: Head selection is not novel

> "Gradient-based head importance scoring for selection was introduced by Michel et al. (2019) for pruning. Applying the same technique for supervision selection is a straightforward engineering transfer, not a new method."

**Severity:** MAJOR
**Route_to:** `/produce-manuscript` — method section needs a paragraph explicitly addressing this: "We use Michel et al.'s (2019) importance metric for a different purpose — supervision selection rather than pruning — and our key claim is the empirical demonstration and theoretical analysis of why this matters."

**Assessment (evaluator):** Correctly identified. The paper should acknowledge this transfer explicitly and focus on the *novel application context* and the *theoretical result* as the distinguishing contribution.

---

### R1.3 — MINOR: K-sweep underspecified

> "The K-sweep analysis uses only 6 values and does not include K=1 (single head). It would be informative to see whether a single highly-important head achieves near-equivalent performance."

**Severity:** MINOR
**Assessment:** Legitimate but easily addressed in a revision or rebuttal.

---

## Reviewer R2: NLP Application Expert

### R2.1 — MAJOR: Single dataset generalizability

> "All experiments are conducted on a single dataset (HateXplain). It is unclear whether the selective-head supervision advantage holds for other hate speech datasets (e.g., OffComEval, OLID) or other explanation-requiring tasks. The theoretical span condition should in principle generalize, but no evidence is provided."

**Severity:** MAJOR
**Route_to:** `/produce-manuscript` — limitations section must be explicit; optionally add a brief result on one additional dataset

**Assessment (evaluator):** Correctly identified. This is weakness W3 (pre-committed). The paper handles it in limitations but reviewers may ask for at least one additional dataset. This is the strongest empirical weakness.

---

### R2.2 — MODERATE: Venue mismatch — this is an ACL/EMNLP paper

> "The primary contribution is a specific improvement in hate speech explanation quality on HateXplain. While the theoretical component is interesting, NeurIPS reviewers will be skeptical of a paper whose main evaluation is on a single NLP task with a single dataset. This paper would be better received at ACL or EMNLP, where hate speech detection is a recognized community topic."

**Severity:** MODERATE (does not block per adversarial review protocol, but should be noted in cover letter)
**Assessment (evaluator):** Correctly identified. This is weakness W6 (venue mismatch). The theoretical contribution (span condition) is the only element that makes NeurIPS viable. If reviewers downgrade this to "observation," the venue case collapses.

---

### R2.3 — MINOR: Annotation aggregation choice not justified

> "The paper uses majority vote over 3 annotators to create the supervision signal. Given that Davani et al. (2024) show annotator disagreements encode morally-relevant information, why not use all-annotator supervision? The choice of majority vote may systematically discard valid rationale tokens."

**Severity:** MINOR
**Assessment:** Legitimate and should be addressed. The E-W4 stratification analysis actually provides indirect evidence on this, but the paper doesn't explicitly connect these.

---

## Reviewer R3: ML Theory Skeptic

### R3.1 — MAJOR: Span condition restates known attention-is-not-explanation results

> "The value-subspace span condition (Proposition 1) is essentially a formal restatement of the known result from Jain & Wallace (2019) that attention distributions can be exchanged without affecting model outputs. The condition says: if value matrices are aligned, supervised heads behave similarly to unsupervised — but this is just saying 'attention doesn't matter for the CLS output if the values are sufficiently similar.' The ρ=−0.87 correlation is empirical confirmation of something theoretically expected, not a new theoretical result."

**Severity:** MAJOR
**Route_to:** `/produce-manuscript` — Proposition 1 must be clearly distinguished from Jain & Wallace (2019). The key distinction: Jain & Wallace show *adversarial* attention swaps don't affect outputs; our span condition provides a *geometric sufficient condition* that predicts *when* supervised attention preserves F1, which is actionable (it guides head selection design). This distinction needs to be explicit.

**Assessment (evaluator):** This attack partially hits. The proposition IS closely related to Jain & Wallace, but the distinctions are real: (1) it's a sufficient condition with geometry, not just an empirical observation; (2) it's predictive (guides K selection); (3) ρ=−0.87 validates it quantitatively. The defense is workable but requires a clear technical paragraph.

---

### R3.2 — MINOR: No theoretical lower bound on K

> "The span condition tells us when large K (many supervised heads) doesn't hurt. But the paper doesn't provide a condition for the *minimum* K that achieves the performance ceiling. This limits the practical usefulness of the theoretical result."

**Severity:** MINOR
**Assessment:** Fair point for a future work statement.

---

## Adversarial Review Summary

| Attack | Reviewer | Severity | Correctly identified? | Addressed in current draft? |
|--------|---------|---------|----------------------|---------------------------|
| Incremental extension of SRA/SMRA | R1.1 | CRITICAL | YES | Partially (comparison table added) |
| Head selection not novel | R1.2 | MAJOR | YES | Partially (needs explicit paragraph) |
| Single dataset limits generalizability | R2.1 | MAJOR | YES | Addressed in limitations |
| Span condition restates Jain & Wallace | R3.1 | MAJOR | YES | Needs clearer technical distinction |
| Venue mismatch (NeurIPS vs. ACL) | R2.2 | MODERATE | YES | Not addressed in draft |
| Annotation aggregation not justified | R2.3 | MINOR | Partially | E-W4 analysis relevant but not connected |

**Ground truth attacks (5 required):**
1. ✅ "Incremental extension of SRA/SMRA" — R1.1 (CRITICAL)
2. ✅ "Head selection not novel" — R1.2 (MAJOR)
3. ✅ "Span condition restates known results" — R3.1 (MAJOR)
4. ✅ "Single dataset limits generalizability" — R2.1 (MAJOR)
5. ✅ "Venue mismatch" — R2.2 (MODERATE)

**All 5 expected weaknesses identified.** The adversarial review is well-calibrated.

---

## Loop 4 Decision

Critical finding R1.1 and Major findings R1.2, R3.1 require upstream fixes:
- R1.1 → Route to `/position` (contribution framing)
- R1.2 → Route to `/produce-manuscript` (method section paragraph)
- R3.1 → Route to `/produce-manuscript` (Proposition 1 paragraph)

**Counter increment:** adversarial_review_cycles = 1 (within limit of 2)

After targeted fixes (1 rewrite cycle):
- R1.1: Comparison table + explicit "building on" language sufficient
- R1.2: New paragraph in Method section added
- R3.1: New paragraph distinguishing from Jain & Wallace added
- R2.2: Note added to limitations about venue rationale

**Post-fix adversarial review cycle 2:** No new CRITICAL findings. MAJOR findings addressed. Continue to Step 36.
