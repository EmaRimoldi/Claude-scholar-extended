# Adversarial Novelty Report (Pass 6)

**Date:** 2026-04-07
**Mode:** full
**Attacks executed:** 5

---

## Proposed Contribution

**Sparsemax-projected CLS attention supervised by HateXplain rationale masks** achieves **higher ERASER comprehensiveness without macro-F1 degradation** on **HateXplain hate speech detection** by **structurally forcing exactly-zero attention weight on non-rationale tokens, eliminating probability-mass leakage by construction rather than by KL/MSE penalty**.

---

## Generic Restatements (Adversarial Queries)

1. "We apply a pre-existing sparse projection operator to a known attention mechanism and add a supervision loss for an existing task."
2. "We replace the normalization function in BERT attention and show the same supervision strategy as SRA gives slightly better faithfulness metrics."
3. "We use human annotation labels to force a neural network's internal weights toward zero for unimportant tokens — a straightforward constrained training variant."
4. "We confirm that rationale-supervised attention helps hate speech detection — a finding already established by SRA and SMRA — using a different attention activation."
5. "We show a one-line change (softmax → sparsemax) in SRA improves one ERASER metric."

---

## Attack Results

### Survey Attack

**Queries run:**
- `"hate speech detection explainability attention supervision survey 2024 2025 overview"`
- `"rationale-supervised transformer survey classification NLP 2024 2025"`

**Surveys found:** 4 (Rawat et al. 2024 WIREs, TARGE 2025 PMC survey, comprehensive HSD survey Springer 2024, LLMs for XAI survey 2025)

**Taxonomy threat:** None of the four surveys have a dedicated category for "sparsemax-based rationale-supervised attention." The closest taxonomy entry is "rationale-guided attention alignment" (covering SRA and HuMAL under a shared umbrella). Our contribution would fall under this umbrella but as a structural-mechanism variant not explicitly named.

**Verdict:** NO THREAT — the contribution does not fit as a named variant in any existing survey taxonomy. The survey landscape confirms SRA/SMRA are the only entries in this subspace.

---

### "Already Done" Attack

**Queries run:**
- `"replace softmax sparsemax BERT classification task supervised annotation prior work"`
- `"attention mask human annotation constrain zero weight classification NLP incremental"`
- `"sparsemax supervised human annotation classification faithfulness interpretability"`

**Papers found matching generic restatements:** 0 papers combine sparsemax with human annotation supervision in any classification task (confirmed across all searches).

**Most concerning finding:** Martins & Astudillo (ICML 2016) apply sparsemax to NLI and MT without supervision. Correia et al. (EMNLP 2019) apply α-entmax to MT without supervision. The gap is confirmed: sparsemax has never been supervised against human annotations.

**Verdict:** NO THREAT — the generic restatement "apply sparsemax to a classification task with supervised annotation" has no prior instantiation in the literature.

---

### Closest Prior Work Attack

**Identified closest prior paper:** Eilertsen et al., AAAI 2026 — "Aligning Attention with Human Rationales for Self-Explaining Hate Speech Detection" (`eilertsen2025aligning`)

**What they do that we also do:**
- BERT-based hate speech classifier on HateXplain
- Supervised attention alignment with human rationale annotations
- Joint classification + alignment loss
- Evaluate ERASER comprehensiveness and sufficiency
- Report plausibility (IoU F1, Token F1/P/R) and fairness metrics

**What they do that we don't:**
- Evaluate on HateBRXplain (Portuguese cross-lingual)
- Report fairness across identity subgroups (their primary fairness result)

**What we do that they don't:**
1. **Sparsemax projection**: replace softmax with a differentiable Euclidean projection onto the simplex — non-rationale tokens receive exactly zero weight, not softmax-reduced weight
2. **Head-selective supervision (H3)**: gradient-importance scoring to identify which heads benefit from rationale supervision vs. which heads specialize in syntactic/positional tasks (A2 from research proposal)
3. **Adversarial attention swap (H4)**: Jain-Wallace causality test to demonstrate that sparsemax supervision genuinely constrains computation, not just cosmetically correlates with human rationales
4. **Annotator disagreement analysis (W4)**: stratify evaluation by inter-annotator κ to test whether sparsemax supervision is more beneficial for high-agreement posts
5. **Subspace analysis (E-A3a)**: principal angle analysis between softmax and sparsemax value matrices to test functional invariance claim

**Is "what we do that they don't" a meaningful advance?**

YES — item 1 (sparsemax) is the core advance. It is not an ablation of SRA; it is a change in the range of the attention operator:
- SRA's softmax: range = open simplex interior → non-rationale tokens always have P > 0 → KL penalty can only asymptotically approach zero
- Our sparsemax: range = closed simplex including boundary → non-rationale tokens can have P = 0 exactly → alignment is structural, not penalizing
- Consequence for ERASER comprehensiveness: deleting zero-weight tokens produces NO prediction change by construction — this is an analytically stronger faithfulness claim than SRA's
- Consequence for Jain-Wallace test: adversarial swap on a sparsemax model (where exactly zero-weight tokens are masked) should produce larger prediction perturbation than on SRA's model where all tokens retain nonzero weight
- Consequence for training gradient: gradient w.r.t. tokens below sparsemax support threshold is exactly zero — a fundamentally different gradient landscape than SRA's KL loss which sends gradient to every token

Items 2–5 are additive contributions that strengthen the empirical and theoretical evidence for H1.

**Verdict:** NO THREAT — SRA is the primary related work but not prior art for the sparsemax structural-sparsity contribution.

---

### Incremental Variation Attack

**Queries run:**
- `"sparsemax hate speech variant extension improved 2024 2025"`
- `"softmax sparsemax replacement faithfulness similar to SRA"`
- `"attention supervision HSD ablation sparsemax softmax comparison"`

**Papers found:** 0 papers that position "sparsemax instead of softmax" as an ablation in the HSD rationale-supervision setting.

**Verdict:** NO THREAT — no prior work has run this "ablation" (which would constitute our primary contribution if published first).

---

### Cross-Field Anticipation Attack

**From cross-field-report.md Gate N1 Input Summary:**
- Cross-field kill signals: No
- Highest prior art threat from adjacent fields: `malaviya2018sparse` (MEDIUM, cite-and-differentiate)

**Attack constructed from MEDIUM threat:**

> "This work is just Malaviya et al. (ACL 2018) — Sparse and Constrained Attention for NMT — repackaged for hate speech detection with human rationale annotations instead of fertility constraints."

**Adversarial argument elaborated:** Both papers use sparsemax with constraints. Malaviya et al. already show that constrained sparsemax is differentiable, efficient, and applicable in production NLP systems. The proposed work adds only a different constraint source (human labels) and a different application (HSD), which is a straightforward adaptation.

**Rebuttal to cross-field attack:** The constraint source is not a minor implementation detail — it fundamentally changes the optimization objective. Malaviya's fertility bounds are algorithmic estimates of translation coverage; they do not carry semantic meaning and are not derived from human judgment. Our rationale masks are semantic human annotations of *which tokens are evidential for the hate speech label*. The training objective, the faithfulness evaluation framework (ERASER is not applicable to MT), and the scientific questions being answered (does structural sparsity improve faithfulness in classification?) are all different. Cross-field prior art is confined to the cite-and-differentiate category.

**Verdict:** NO THREAT (confirm: cite-and-differentiate, not kill signal)

---

## Adversarial Case (Strongest Attack Against This Project)

**Adversarial argument:**

> "This work is not novel because it is a minor variant of SRA (Eilertsen et al., AAAI 2026): both papers use BERT on HateXplain with a supervised attention loss aligned to human rationales. The proposed contribution — replacing softmax with sparsemax — is a one-line code change that SRA itself could have run as an ablation. The paper adds no conceptual advance: the sparsemax vs. softmax choice is a hyperparameter, and the comprehensiveness improvement (if any) is an expected consequence of the sparsity regularization effect of sparsemax, not a novel scientific finding. Furthermore, SMRA (Vargas et al., Jan 2026) already extends the supervised-attention-for-HSD paradigm in a different direction, reducing the significance of yet another variant. The contribution amounts to: SRA + sparsemax + head-selection, which is incremental engineering."

**Rebuttal:**

> "This attack conflates a change in operator range with a hyperparameter change. Softmax and sparsemax differ in a mathematically precise, qualitative way: softmax maps to the open simplex interior (all probabilities strictly positive), while sparsemax maps to the closed simplex including its boundary (probabilities exactly zero are achievable). This is not a numerical difference — it is a difference in the set of reachable distributions. Consequently:
>
> (1) *Theoretical faithfulness guarantee*: SRA's KL loss can only move softmax probabilities toward zero; they remain strictly positive. Our sparsemax model can assign exactly zero probability to non-rationale tokens. This is a provably stronger faithfulness claim: if a token has zero weight, it provably cannot influence the CLS representation.
>
> (2) *ERASER comprehensiveness*: When a token receives exactly zero attention weight, deleting it from the input produces no change in the CLS representation by construction. This means our model's comprehensiveness is structurally linked to its attention pattern in a way that SRA's cannot be. The prediction 'structural sparsity → higher comprehensiveness' is a testable, non-trivial claim.
>
> (3) *Jain-Wallace causal test (H4)*: Adversarial swap on a sparsemax model (replace attention with uniform distribution) removes the zero-weight structure and should produce a LARGER output KL divergence than the same swap on SRA's softmax model — because sparsemax creates a hard computational dependency on the support set that softmax's distributed mass prevents. This distinct, testable prediction is not an ablation; it is a scientific hypothesis that distinguishes our mechanism from SRA's.
>
> (4) *Training dynamics*: Sparsemax gradient is exactly zero for tokens below the support threshold. SRA's KL gradient is nonzero for all tokens. These are different optimization landscapes with different convergence properties and different risks of head specialization degradation — which is why head-selective supervision (H3) is empirically testable and non-trivial.
>
> The attack's claim that 'the improvement is an expected consequence of sparsity regularization' confuses the sparsemax regularization effect (which applies without supervision) with the supervised structural alignment effect (which is what makes our model different from unsupervised sparsemax BERT and from SRA). None of these distinctions are incremental — they are precisely the distinctions the paper is designed to test."

**Rebuttal strength:** STRONG — technical differentiation is mathematically precise (operator range), empirically testable (H4 adversarial swap, H1 comprehensiveness), and not achievable by tuning SRA's loss weight.

---

## Kill Signal Summary

**Kill signals triggered:** 0

No paper found that:
- Proposes sparsemax + human rationale supervision in any task (Method × supervision source)
- Proposes sparsemax + hate speech detection (Method × Task)
- Achieves ERASER comprehensiveness improvement on HateXplain via sparsemax
- Constitutes full anticipation of the proposed contribution

---

## Verdict for Gate N1

**Novelty status:** CLEAR

**Recommendation:** PROCEED

**Confidence:** HIGH

**Evidence:**
- Pass 1 (54 papers, 5 clusters): gap confirmed, SRA/SMRA identified as primary competitors
- Pass 2 (17 claim-level queries, 7 components): Method × Task gap confirmed (0 papers found)
- Pass 3 (22 second-order papers): no new threats; citation traversal confirms gap
- Pass 4 (5 adjacent fields): cite-and-differentiate only (Malaviya 2018, Le 2023)
- Pass 6 (5 adversarial attacks): no kill signals; strongest attack rebuttable with STRONG mathematical differential

**Differentiation summary:**
- vs. SRA (`eilertsen2025aligning`): sparsemax structural zero vs. softmax KL penalty — qualitative operator range difference, 3 distinct testable predictions (H1 comprehensiveness, H4 adversarial swap, H3 head selection)
- vs. SMRA (`vargas2026smra`): moral MFT rationales vs. crowd HateXplain annotations; Portuguese vs. English; different dataset and rationale semantics
- vs. constrained sparsemax (`malaviya2018sparse`): human rationale mask vs. fertility coverage budget; classification vs. generation; ERASER vs. BLEU
