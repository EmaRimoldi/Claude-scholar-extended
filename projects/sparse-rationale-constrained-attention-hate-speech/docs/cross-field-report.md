# Cross-Field Search Report

**Date:** 2026-04-07
**Hypothesis summary:** Sparsemax attention constrained to human rationale annotations in BERT achieves structurally faithful hate speech detection by producing exactly-zero attention on non-rationale tokens — structural sparsity rather than softmax diffusion.
**Passes run:** Pass 4 (Cross-Field)

---

## Abstract Problem Statement

The core computation in this paper is: **a supervised projection of a weighted aggregation operator (attention) onto a sparse support set (human rationale tokens), such that items outside the support receive exactly zero weight, while items inside the support receive allocation proportional to their learned relevance scores.**

In domain-agnostic terms:
> Given a parameterized soft-assignment operator over a discrete set of items (tokens), and a binary annotation mask identifying a privileged subset (rationale), learn to assign all probability mass to the privileged subset while maintaining downstream prediction quality. The privileged subset is small (~25% of items) and defined by human judgment. The goal is both structural faithfulness (zero weight outside mask) and classification accuracy.

This abstraction strips all NLP-specific vocabulary. The key elements are:
1. A parameterized distribution over discrete items
2. An externally-provided sparse support set
3. An operator that projects the distribution onto the support
4. A downstream prediction task whose performance must not degrade
5. A faithfulness requirement: items outside support must receive exactly zero weight

---

## Adjacent Fields Searched

### Field 1: Neural Machine Translation / Constrained Sparse Attention

**Why searched:** The sparsemax operator was originally developed in the MT community (DeepSPIN / IST Lisbon). Constrained variants of sparsemax may already exist for MT coverage problems — structurally the same projection technique applied to a different task.

**Vocabulary used:** sparsemax, constrained attention, fertility constraints, coverage mechanism, aligned attention, structured sparsity, attention bounds

**Queries executed:**
- `"sparse and constrained attention" neural machine translation ACL 2018 sparsemax`
- `sparsemax entmax text classification constrained rationale alignment faithfulness 2024 2025`
- `annotation-guided sparse attention transformer text classification faithfulness human rationale 2024 2025`

**Sources searched:** ACL Anthology, arXiv cs.CL, Semantic Scholar

**Papers scanned:** 8 total, 3 relevant

**Key findings:**

| Paper | Year | Venue | Relation to proposed contribution | Threat level |
|-------|------|-------|----------------------------------|--------------|
| Malaviya, Ferreira & Martins — "Sparse and Constrained Attention for NMT" | 2018 | ACL | Proposes **constrained sparsemax** with upper-bound fertility constraints; differentiable and sparse | MEDIUM |
| Martins & Astudillo — "From Softmax to Sparsemax" | 2016 | ICML | Foundation; unsupervised sparsemax | LOW (already in Pass 1) |
| Correia et al. — "Adaptively Sparse Transformers" | 2019 | EMNLP | α-entmax, learnable sparsity; unsupervised | LOW (already in Pass 1) |

**Prior art threat level for this field:** MEDIUM (Malaviya 2018)

**Differential statements:**

> **Malaviya et al. 2018:** Solves the *coverage problem* in neural machine translation using constrained sparsemax with fertility upper bounds — each source word receives at most a fixed amount of total attention across decoding steps. The constraint is algorithmic (coverage budget), not annotation-driven. Our proposed work addresses *faithful hate speech classification* using sparsemax constrained by **human rationale annotations** as the support set. The specific technical difference is: (1) our constraint is a support mask from human judgment, not a coverage counter; (2) we operate in an encoder-only classification setting, not a sequence-to-sequence setting; (3) our optimization jointly trains classification and rationale alignment, not coverage alone; (4) we evaluate faithfulness via ERASER comprehensiveness/sufficiency metrics, which are not relevant to NMT. This is not a transfer of their work because the constraint mechanism, the optimization objective, the task domain, and the evaluation criteria are all fundamentally different.

---

### Field 2: Computer Vision — Supervised Spatial Attention in VQA

**Why searched:** Computer vision uses annotation-supervised attention (grounding, saliency, region-of-interest) to guide visual attention toward human-annotated regions. If soft attention supervision with annotation masks already exists in CV, and the contribution of our paper is the "human annotation → attention constraint" idea, this is prior art for the idea even if the domain and mechanism differ.

**Vocabulary used:** attention priors, grounded attention, ROI supervision, visual grounding, annotation-constrained attention, saliency supervision, weakly supervised grounding

**Queries executed:**
- `supervised spatial attention human annotation ROI constrained vision transformer 2023 2024 2025`
- `supervised attention grounding visual question answering annotation constrained attention zero weight 2023 2024`
- `"attention priors" supervised annotation vision transformer faithfulness VQA grounding WACV 2023`

**Sources searched:** arXiv cs.CV, CVPR/ICCV/WACV proceedings, CVF Open Access

**Papers scanned:** 12 total, 4 relevant

**Key findings:**

| Paper | Year | Venue | Relation to proposed contribution | Threat level |
|-------|------|-------|----------------------------------|--------------|
| Le et al. — "Guiding VQA with Attention Priors" | 2023 | WACV | Uses grounding annotations as attention priors; supervises spatial attention to match annotated regions; improves interpretability | LOW-MEDIUM |
| Urooj et al. — "Found a Reason for Me? Weakly-supervised Grounded VQA" | 2021 | CVPR | Weakly-supervised attention grounding in VQA | LOW |
| Zhang et al. — "Interpretable VQA by Visual Grounding from Attention Supervision Mining" | 2019 | IEEE CVPR | Supervises attention with ground truth annotations for interpretability | LOW |
| "A Visual Attention Regularization Approach" | 2022 | TOMM | Regularizes attention toward human-identified regions | LOW |

**Prior art threat level for this field:** LOW (Le 2023 is closest but uses soft attention, not sparsemax)

**Differential statements:**

> **Le et al. 2023 (Guiding VQA with Attention Priors):** Solves attention alignment in *visual question answering* using soft attention priors derived from grounding annotations (image regions). The supervision is soft — attention weights are nudged toward annotated regions using MSE or KL loss; no tokens/pixels receive exactly zero weight. Our proposed work addresses *hate speech text classification* using sparsemax to produce **structurally zero attention** on non-rationale tokens. The specific technical differences are: (1) sparsemax vs. soft attention prior (structural zero vs. reduced-but-nonzero weight); (2) text tokens vs. image pixels/patches; (3) hate speech detection domain; (4) faithfulness evaluation via ERASER comprehensiveness/sufficiency, which is impossible to compute when attention is never exactly zero. This is not a transfer of their work because the zero-weight structural property of sparsemax is the core novel mechanism, and it has no equivalent in soft attention grounding systems.

---

### Field 3: Signal Processing / Compressed Sensing

**Why searched:** Sparse support recovery literature studies how to recover a support set (which elements are nonzero) from linear measurements. "Oracle" methods know the support in advance. If there is a body of work on constrained reconstruction given known support, it might constitute prior art for the projection-onto-support mechanism.

**Vocabulary used:** support recovery, constrained sparse reconstruction, oracle support, partially known support, basis pursuit, orthogonal matching pursuit, gradient projection sparse reconstruction

**Queries executed:**
- `supervised sparse support recovery signal processing constrained projection oracle`
- `oracle LASSO supervised support recovery pre-specified support set classification machine learning`

**Sources searched:** arXiv eess.SP, IEEE Xplore, Semantic Scholar

**Papers scanned:** 10 total, 2 relevant

**Key findings:**

| Paper | Year | Venue | Relation to proposed contribution | Threat level |
|-------|------|-------|----------------------------------|--------------|
| Vaswani et al. — "Exact Recovery of Sparse Signals with Side Information" | 2022 | EURASIP | Uses partially known support as prior to assist reconstruction | NONE |
| "Support Exploration Algorithm for Sparse Support Recovery" | 2023 | arXiv | Algorithm for support recovery from measurements with oracle update | NONE |

**Prior art threat level for this field:** NONE

**Reasoning:** Compressed sensing studies support *recovery* from noisy measurements — the goal is to *infer* what the support is. Our work takes the support as *given* (human annotations) and projects a distribution *onto* that support. The direction of inference is reversed: CS infers support from data; we constrain attention to a provided support. The mathematical structure (L1 minimization / basis pursuit) also differs from sparsemax projection onto the probability simplex. No prior art found.

---

### Field 4: Information Retrieval — Learned Sparse Retrieval

**Why searched:** Learned sparse retrieval (SPLADE, LACONIC) produces sparse token-importance vectors for efficient inverted-index retrieval. If sparsity in these vectors is supervised by relevance annotations, there could be structural overlap with annotation-supervised sparsemax attention.

**Vocabulary used:** learned sparse retrieval, SPLADE, sparse lexical vectors, constrained attention retrieval, annotation-constrained sparse representations

**Queries executed:**
- `learned sparse retrieval constrained attention relevance annotation information retrieval 2023 2024`

**Sources searched:** ACM SIGIR proceedings, arXiv cs.IR

**Papers scanned:** 8 total, 0 relevant

**Key findings:**

| Paper | Year | Venue | Relation to proposed contribution | Threat level |
|-------|------|-------|----------------------------------|--------------|
| LACONIC (Llama3-based learned sparse retrieval) | 2025 | arXiv | Sparse token vectors for inverted-index efficiency | NONE |
| Unified Framework for LSR | 2023 | arXiv | Systematizes SPLADE/DeepImpact family | NONE |

**Prior art threat level for this field:** NONE

**Reasoning:** Learned sparse retrieval uses sparsity for *computational efficiency* (inverted index compatibility), not for *interpretability* or *faithfulness*. The sparsity is in representation space (vocabulary-level importance scores), not in attention weight distributions. No annotation supervision for exact-zero weights. No structural overlap.

---

### Field 5: Computational Neuroscience — Top-Down Attention Gating

**Why searched:** Biological selective attention implements suppression of irrelevant inputs (zero or near-zero activation for non-attended stimuli). If neural network models inspired by biology implement hard gating with zero suppression, this could be prior art for the idea of exactly-zero weight on non-rationale tokens.

**Vocabulary used:** top-down attention gating, selective attention suppression, biologically plausible gating, alpha oscillation suppression, inhibitory gating

**Queries executed:**
- `top-down attention gating zero suppression biologically plausible selective neural networks`

**Sources searched:** arXiv q-bio.NC, PubMed, NeurIPS/ICLR computational neuroscience track

**Papers scanned:** 7 total, 2 loosely relevant

**Key findings:**

| Paper | Year | Venue | Relation to proposed contribution | Threat level |
|-------|------|-------|----------------------------------|--------------|
| "Brain-Inspired Gating Mechanism for Spiking Neural Networks" | 2025 | arXiv | Dynamic conductance gating; selectively suppresses inputs | NONE |
| "Enhancing Spiking Neural Networks with Hybrid Top-Down Attention" | 2022 | PMC | Top-down attention as multiplicative gating | NONE |

**Prior art threat level for this field:** NONE

**Reasoning:** Biological gating models use multiplicative suppression (multiply by value between 0 and 1, not constrained simplex projection). The gating is not supervised by human annotations — it emerges from learned task demands. The application domain (spiking neural networks, working memory) is entirely different. No structural overlap with supervised simplex projection for text classification.

---

## Overall Cross-Field Assessment

| Field | Papers scanned | Relevant | Highest threat paper | Threat level |
|-------|---------------|---------|---------------------|--------------|
| NLP/MT — Constrained Sparsemax | 8 | 3 | Malaviya et al. ACL 2018 | MEDIUM |
| Computer Vision — Supervised Attention | 12 | 4 | Le et al. WACV 2023 | LOW-MEDIUM |
| Signal Processing — Sparse Recovery | 10 | 0 | — | NONE |
| Information Retrieval — Learned Sparse | 8 | 0 | — | NONE |
| Computational Neuroscience — Gating | 7 | 0 | — | NONE |

**Fields with prior art concerns:** NLP/MT (Malaviya 2018), Computer Vision (Le 2023)

**Highest overall threat:** Malaviya et al. (ACL 2018) — "Sparse and Constrained Attention for NMT". Uses the same base mechanism (constrained sparsemax) but in a coverage-constrained NMT setting. This is a **cite-and-differentiate** case, not a blocking threat. The constraint mechanism, task, optimization objective, and evaluation are all different. A reviewer familiar with the DeepSPIN literature will cite this paper and ask for differentiation — it must appear in related work with an explicit differential.

**Recommendation:** `cite_and_differentiate`

No cross-field prior art constitutes full prior art for the proposed contribution. The closest work (Malaviya 2018) uses constrained sparsemax but for NMT coverage, not for faithful hate speech classification via human rationale alignment. The computer vision attention supervision literature (Le 2023) uses soft annotation-guided attention but not sparsemax. Neither is an overlap that blocks the novelty claim.

---

## Gate N1 Input Summary

This section is read directly by `/novelty-gate gate=N1`:

**Application novelty status:** CLEAR — no adjacent field found where the combination of (sparsemax projection) + (human rationale annotation constraint) + (classification faithfulness evaluation) has been implemented.

**Cross-field threats to cite:**
- Malaviya et al. ACL 2018 (`malaviya2018sparse`): constrained sparsemax for NMT; must be in related work with explicit differentiation
- Le et al. WACV 2023 (`le2023guiding`): attention priors from grounding annotations for VQA; mention as evidence that annotation-supervised attention is used across fields

**Cross-field kill signals:** No

**Differential statements written for all HIGH/MEDIUM threats:** Yes (Malaviya 2018 differential written above; Le 2023 differential written above)

---

## Adjacent Field Findings for research-landscape.md

### NLP/MT — Constrained Sparse Attention (ACL 2018)
- **Abstract problem overlap:** How to enforce structural constraints on attention distributions using sparsemax
- **Key papers:** Malaviya et al. ACL 2018 (`malaviya2018sparse`)
- **Novelty implication:** Our paper must cite this work in related work section; differentiate on: (a) source of constraint (human rationales vs. fertility budget), (b) task (classification vs. generation), (c) evaluation (ERASER faithfulness vs. BLEU coverage). The novelty claim is not blocked but needs explicit framing.

### Computer Vision — Annotation-Supervised Soft Attention
- **Abstract problem overlap:** Guiding model attention toward human-annotated regions for interpretability
- **Key papers:** Le et al. WACV 2023 (`le2023guiding`), Zhang et al. IEEE 2019 (`zhang2019interpretable`)
- **Novelty implication:** Shows annotation-supervised attention for interpretability is an active research pattern across modalities. Our contribution's novelty lies in the sparsemax mechanism (structural zero vs. soft suppression) and the faithfulness evaluation framework (ERASER), not in the general idea of annotation-guided attention.
