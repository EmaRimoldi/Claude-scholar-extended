# Claim-Level Search Report (Pass 2)

**Date:** 2026-04-01
**Step:** claim-search (Step 4)
**Hypothesis:** H1–H3 (primary mechanistic contributions)

## Canonical Claim

> "We show that **sparsemax attention in gradient-importance-selected BERT heads with rationale alignment loss** achieves **improved faithfulness (comprehensiveness) and plausibility (IoU-F1)** on **HateXplain hate speech detection** by **inducing sparse attention distributions that structurally match the binary rationale annotation target**."

---

## Canonical Claim Decomposition

| Component | Value | Queries Run | Papers Found (new) |
|-----------|-------|-------------|---------------------|
| Method | Sparsemax as BERT CLS attention activation under alignment supervision | 3 queries | ribeiro2020sparsemax (already in ledger) |
| Task/Domain | HateXplain hate speech detection | 3 queries | 0 new (SRA/SMRA/MRP known) |
| Result | Improved comprehensiveness + IoU-F1 over softmax baselines | 2 queries | chrysostomou2021tasc (new) |
| Mechanism | Gradient-importance head selection before applying alignment loss | 2 queries | 0 new (no paper does this) |
| Method × Task | Sparsemax BERT for hate speech detection | 2 queries | 0 (null result confirmed) |
| Method × Result | Sparsemax attention improves comprehensiveness in NLP | 2 queries | 0 (null result confirmed) |
| Task × Result | Rationale supervision improves plausibility on HateXplain | 2 queries | 0 new (SRA/SMRA known) |

**Total queries run:** 16 (≥ 14 required ✓)
**New papers found this pass:** 1 (chrysostomou2021tasc; ribeiro2020sparsemax was already in ledger)
**Papers read in full for overlap assessment:** 3 (chrysostomou2021tasc, ribeiro2020sparsemax abstract, SRA confirmed)

---

## High-Threat Papers

### Eilertsen et al. (2025) — "Aligning Attention with Human Rationales for Self-Explaining Hate Speech Detection" — AAAI 2025

- **Overlap components:** Task/Domain, Result, Task × Result (3 components)
- **Overlap level:** HIGH (concurrent work — already identified in Pass 1)
- **What they do:** Supervised Rational Attention (SRA). Applies MSE alignment loss between CLS attention at BERT layer 8, head 7 (fixed) and majority-vote binary rationale mask from HateXplain, using softmax attention. Joint training: CE loss + MSE alignment loss. Evaluated on HateXplain (English) and HateBRXplain (Portuguese) with LIME-based faithfulness.
- **What we do differently:**
  > "SRA constrains a single pre-selected attention head (layer 8, head 7) using MSE loss under softmax attention, reporting IoU-F1 and faithfulness metrics evaluated via LIME with 3 seeds. Our work (a) selects supervised heads via gradient importance scoring I(h,l) = E_x[|∂L_CE/∂A^{CLS,h,l}|], replacing fixed selection with mechanistically justified selection; (b) replaces the softmax activation function of supervised heads with sparsemax, whose sparse output naturally aligns with the binary structure of the rationale target; (c) evaluates faithfulness via Integrated Gradients (theoretically superior to LIME on short texts) with 5 seeds and bootstrap CIs; (d) ablates alignment loss functions (MSE, KL, sparsemax_loss). The combination of (a)+(b) is entirely unexplored by SRA."
- **Is differentiation sufficient?** YES — three independent technical dimensions clearly separate our contribution from SRA.
- **Action required:** Cite and differentiate in related work section; use as primary baseline.
- **Kill signal?** NO

---

## Medium-Threat Papers

### Vargas et al. (2026) — "Self-Explaining Hate Speech Detection with Moral Rationales" — arXiv

- **Overlap components:** Task/Domain, Task × Result
- **Overlap level:** MEDIUM
- **What they do:** SMRA extends SRA with Moral Foundations Theory-based rationale supervision (6 moral dimensions). Introduces HateBRMoralXplain. Same softmax-only BERT architecture. Focuses on Portuguese, not English HateXplain.
- **Differential:** Same mechanistic limitations as SRA (softmax, no head selection). SMRA differentiates on the type of rationale (moral-dimension-specific vs generic span rationales), not on attention mechanism design. Our focus is English HateXplain with sparsemax + importance selection; SMRA's key contribution (moral rationale taxonomy) is orthogonal to ours.
- **Action required:** Cite as concurrent extension of SRA; use their HateBRMoralXplain numbers for comparison only if including cross-lingual evaluation.

### Ribeiro, Felisberto & Neto (2020) — "Pruning and Sparsemax Methods for Hierarchical Attention Networks" — arXiv

- **Overlap components:** Method (sparsemax as attention activation in text classification)
- **Overlap level:** MEDIUM
- **What they do:** Replace softmax with sparsemax in hierarchical attention networks for document classification (IMDB sentiment). Report limited gains (no significant improvement over baseline). No rationale supervision, no hate speech, no head selection, no alignment loss, no binary mask target.
- **Differential:**
  > "Ribeiro et al. apply sparsemax to document-level hierarchical attention (word → sentence) for sentiment classification, without any external supervision signal. Our work applies sparsemax specifically to BERT CLS token attention heads selected by gradient importance, under explicit MSE/KL/sparsemax_loss alignment with token-level human rationale annotations. The mechanisms are fundamentally different: unsupervised sparse attention vs. rationale-constrained sparse attention. Ribeiro et al. find limited gains because sparsemax alone does not improve performance; our hypothesis is precisely that sparsemax under rationale supervision produces faithfulness gains not achievable by softmax under the same supervision."
- **Action required:** Cite as background for sparsemax in attention (NLP application); distinguish unsupervised vs supervised use case.

### Chrysostomou & Aletras (2021) — "Improving the Faithfulness of Attention-based Explanations with Task-specific Information for Text Classification" — ACL 2021

- **Overlap components:** Result (improved attention-based faithfulness for text classification)
- **Overlap level:** MEDIUM
- **What they do:** Task-Scaling (TaSc) mechanisms that learn task-specific non-contextualised scaling factors to modulate existing attention weights. Tested across 5 text classification datasets and 5 BERT-family encoders. Improves faithfulness over post-hoc baselines (LIME, SHAP) without changing the model's prediction performance.
- **Differential:**
  > "TaSc improves faithfulness by learning a task-specific weight vector that scales existing attention weights post-hoc, without replacing the attention activation function or adding external supervision from human rationale annotations. Our work (a) directly supervises specific BERT attention heads with binary token-level human rationale masks; (b) replaces softmax with sparsemax in the supervised heads; (c) focuses on hate speech detection with HateXplain rationales — a very different application and supervision signal. TaSc does not use human rationale annotations at all; its 'task-specific' information comes from learned attention scaling, not from human-labeled spans. The specific technical claim — that sparsemax activation under rationale alignment supervision outperforms softmax activation under identical supervision — is not addressed by TaSc."
- **Action required:** Cite as related work on attention-based faithfulness improvement in text classification; use TaSc's results as evidence that standard attention modification can improve faithfulness; motivate why we go further with explicit rationale supervision.

### Kim, Lee & Sohn (2022) — "Why Is It Hate Speech? Masked Rationale Prediction" — arXiv

- **Overlap components:** Task/Domain, Task × Result
- **Overlap level:** MEDIUM (already in ledger from Pass 1)
- **What they do:** Masked Rationale Prediction (MRP) intermediate pre-training task: predict masked rationale tokens from unmasked context. Improves explainability and robustness on HateXplain.
- **Differential:** MRP is a pre-training task (not direct attention supervision); uses masked prediction (not alignment loss); does not modify the attention activation function; no head selection. Already identified in Pass 1 as Cluster 1.3.
- **Action required:** Use as comparison baseline in experiments; cite in related work.

---

## Low-Threat Papers (list only)

- Liu & Chen (2023) "Picking the Underused Heads" — head selection by importance for feature injection in dialogue coreference. Overlap on Mechanism (head importance ranking). Domain: dialogue (not hate speech), purpose: feature injection (not rationale supervision), no sparsemax, no external annotations.
- Carton, Rathore & Tan (2020) "Evaluating and Characterizing Human Rationales" — evaluation methodology for human rationales. No model modification. LOW overlap on Result evaluation methodology.
- Lyu et al. (2022) "Towards Faithful Model Explanation in NLP: A Survey" — survey paper, no specific method.

---

## Composite Threat Assessment

**Overall threat level: MEDIUM**

**Reasoning:** SRA (eilertsen2025sra) is the only paper covering 3 or more decomposition components, but it has been identified as concurrent work since Pass 1 and admits a clear, honest differential statement along three independent technical dimensions. No newly found paper in Pass 2 introduces a threat beyond what was already identified. The **Mechanism component** (gradient importance head selection applied before rationale alignment supervision) has **zero overlap papers** — confirming this is the strongest novelty wedge. The **Method × Task** and **Method × Result** cross-components both returned null results, indicating no paper has combined sparsemax attention with hate speech detection or with improved faithfulness.

**Primary threat paper:** eilertsen2025sra (SRA, AAAI 2025) — concurrent work, not a kill signal.

**Differentiability:** YES — a clear differential statement exists for every MEDIUM/HIGH threat paper. The differentiating combination (sparsemax activation + gradient importance head selection + rationale supervision) is unaddressed by any prior or concurrent work.

---

## Kill Signal Flags

**No kill signals identified.**

No paper found that covers all 4 primary decomposition components (Method + Task + Result + Mechanism) simultaneously. SRA covers 3 components but is differentiable on all three axes. The specific mechanism — **gradient importance scoring for selecting which BERT heads to supervise with sparsemax attention under rationale alignment** — has no prior art across all searches.

---

## Search Coverage

**Total queries run:** 16 (minimum required: 14 ✓)
**New papers found:** 1 (chrysostomou2021tasc)
**Papers read in full (abstract/methodology):** 3
**HIGH overlap papers:** 1 (eilertsen2025sra — known concurrent work)
**MEDIUM overlap papers:** 4 (vargas2026smra, ribeiro2020sparsemax, chrysostomou2021tasc, kim2022mrp)
**LOW overlap papers:** 3

---

## Epistemic Updates

- Citation ledger updated: 1 new entry added (chrysostomou2021tasc)
- Existing entries updated with claim_overlap_level: 5 entries (eilertsen2025sra=HIGH, vargas2026smra=MEDIUM, ribeiro2020sparsemax=MEDIUM, chrysostomou2021tasc=MEDIUM, kim2022mrp=MEDIUM)
- Null results for Mechanism component and Method×Task/Method×Result cross-components recorded as confirmatory evidence of novelty
