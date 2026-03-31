# Claim Overlap Report (Step 4 — Pass 2 Claim-Level Search)

**Date:** 2026-03-30
**Step:** 4 / 38
**Hypothesis:** Selective-head sparsemax supervision improves faithfulness and plausibility of hate speech explanations without degrading F1
**Databases searched:** Semantic Scholar, arXiv (cs.CL, cs.LG), ACL Anthology

---

## Claim Decomposition

The hypothesis was decomposed into the following atomic searchable claims:

| Claim ID | Claim | Search Terms |
|---------|-------|-------------|
| C-ATT | Sparsemax can replace softmax in BERT attention for supervised training | "sparsemax attention BERT", "sparse attention supervision", "rational attention" |
| C-SEL | Attention head selection by gradient importance improves supervision quality | "head importance scoring", "head selection BERT", "attention head pruning" |
| C-FAITH | Supervising attention with human rationales improves faithfulness metrics | "attention supervision rationale", "faithfulness explainability supervision" |
| C-HATE | Hate speech detection benefits from explicit supervision of attention | "hate speech BERT attention", "explainable hate speech" |
| C-SPAN | Value-subspace span condition explains functional invariance under supervision | "attention value subspace", "functional invariance attention" |

---

## Per-Claim Search Results

### C-ATT: Sparsemax BERT Attention Supervision

**HIGH OVERLAP PAPERS:**

**[1] SRA — Supervised Rational Attention (arXiv:2511.07065, Nov 2025)**
- Overlap level: **HIGH**
- Method: Supervises BERT [CLS]-token attention across all heads using human rationale annotations; uses sparsemax to produce sparse supervision targets; trains on text classification tasks
- Dataset: IMDb, SST-2, MultiRC — NOT HateXplain
- Key difference from proposed work: (1) Full-head supervision (all heads), not selective; (2) no head importance scoring; (3) no theoretical analysis; (4) does not test on hate speech
- Status: **Must be cited and compared against as a direct baseline**
- Note: This paper was NOT cited by the original mini-project (predates it but only published on arXiv Nov 2025)

**[2] Bastings & Filippova (2020)** — "The elephant in the interpretability room: Why use attention as explanation when we have saliency methods?" ACL Findings.
- Overlap level: MEDIUM — argues against attention as explanation; background for framing

**[3] Attention supervision in NLI (Stacey et al., 2022)**
- Overlap level: LOW-MEDIUM — supervises attention in NLI with human rationales but uses softmax, not sparsemax

---

### C-SEL: Head Selection by Gradient Importance

**MODERATE OVERLAP PAPERS:**

**[4] Michel et al. (2019)** — Are Sixteen Heads Really Better Than One? NeurIPS.
- Overlap level: MODERATE — uses gradient importance to identify and prune heads; directly used for the head selection motivation
- Status: Must be cited; our contribution builds on their importance metric

**[5] Voita et al. (2019)** — Analyzing Multi-Head Self-Attention. ACL.
- Overlap level: MODERATE — identifies functionally specialized heads; motivates selective supervision

**[6] Shim et al. (2023)** — Efficient Head Pruning via Gradient-Based Importance Scores. arXiv.
- Overlap level: LOW — efficiency-focused, different objective

No paper found that *uses* head importance selection specifically for rationale supervision quality. **This is a genuine gap.**

---

### C-FAITH: Rationale Supervision → Faithfulness

**HIGH OVERLAP:**

**[7] SMRA — Supervised Moral Rationale Attention (arXiv:2601.03481, Jan 2026)**
- Overlap level: **HIGH**
- Method: Supervises BERT attention with moral-value rationale annotations on HateXplain; uses sparsemax supervision targets; measures comprehensiveness and sufficiency
- Dataset: **HateXplain** — same dataset as proposed work
- Key difference: (1) Focuses on moral value dimensions of rationales, not generic hate speech rationales; (2) full-head supervision, not selective; (3) no head importance analysis
- Status: **CRITICAL — must be cited and compared against; same task, same dataset, very similar method**
- Note: Published Jan 2026 — will be found in Pass 5 recency sweeps if not now

**[8] Jain et al. (2020)** — Learning to Faithfully Rationalize by Construction. ACL. FRESH framework.
- Overlap level: MODERATE — different approach (extractive rationales) but measures same metrics

---

### C-HATE: Explainable Hate Speech with Attention

**LOW-MODERATE OVERLAP:**

**[9] Kapil et al. (2020)** — A Deep Neural Network Based Multi-task Learning Approach to Hate Speech Detection.
- Overlap level: LOW — uses attention for multi-task learning, not supervision

**[10] Roy & Goldwasser (2020)** — Weakly Supervised Learning of Nuanced Frames for Analyzing Hate Speech. EMNLP.
- Overlap level: LOW-MODERATE — nuanced framing analysis for hate speech

No paper found that combines selective-head supervision + sparsemax specifically for hate speech explainability. **Gap confirmed for the specific combination.**

---

### C-SPAN: Value-Subspace Analysis

**No overlap papers found.** The value-subspace span condition appears to be a genuinely novel theoretical contribution. No prior paper formalizes this condition in the context of attention supervision. Related works:
- Brunner et al. (2020) — On Identifiability in Transformers. *Value matrix analysis in transformers; theoretical background.*
- Dong et al. (2021) — Attention is not all you need: Pure attention loses rank doubly exponentially. *Rank collapse analysis — tangentially related.*

---

## High-Threat Summary

| Paper | Threat Level | Overlap With | Status |
|-------|-------------|-------------|--------|
| SRA (arXiv:2511.07065) | **HIGH** | C-ATT (sparsemax attention supervision) | Must cite + compare |
| SMRA (arXiv:2601.03481) | **HIGH** | C-FAITH (rationale supervision on HateXplain) | Must cite + compare |
| Michel et al. (2019) | MODERATE | C-SEL (head importance scoring) | Must cite + build on |
| Voita et al. (2019) | MODERATE | C-SEL (head specialization) | Must cite |

---

## Novelty Delta Assessment (Pre-N1)

After claim-level search, the contribution can be decomposed as:

| Component | Prior Art | Novelty Level |
|-----------|----------|--------------|
| Sparsemax in BERT attention | Martins 2016, SRA 2025 | NOT novel alone |
| Rationale supervision of BERT attention | SRA 2025, SMRA 2026 | NOT novel alone |
| Selective-head supervision via importance scoring | Michel 2019 + SRA = **combination** | PARTIALLY novel |
| Hate speech + sparsemax attention supervision | SMRA 2026 | NOT novel alone |
| Value-subspace span condition | Nothing found | NOVEL |
| 2×2×2 ablation disentangling factors | Nothing directly | MODERATELY novel |
| Annotator disagreement stratification | Davani 2024 + nothing specific | NOVEL angle |

**Pre-N1 assessment: REPOSITION required.** The method as originally framed is not novel. A repositioned contribution centering on: (1) selective-head mechanism, (2) ablation disentanglement, and (3) theoretical span condition — is defensible.

---

## Gate Status

- [x] All 5 atomic claims searched
- [x] SRA (arXiv:2511.07065) identified — HIGH overlap
- [x] SMRA (arXiv:2601.03481) identified — HIGH overlap
- [x] Novelty delta computed per component
- [x] All high-overlap papers added to citation_ledger.json
