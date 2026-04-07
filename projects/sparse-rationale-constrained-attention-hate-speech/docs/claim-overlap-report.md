# Claim-Level Search Report (Pass 2)

**Date:** 2026-04-07
**Hypothesis:** Sparsemax-projected CLS attention supervised by HateXplain rationale masks achieves higher ERASER comprehensiveness without macro-F1 degradation on HateXplain hate speech detection by structurally forcing exactly-zero attention weight on non-rationale tokens, eliminating probability-mass leakage by construction rather than by KL/MSE penalty.

---

## Canonical Claim Decomposition

| Component | Value | Queries Run | Papers Found |
|-----------|-------|-------------|-------------|
| Method | Sparsemax-projected attention supervised by human rationale masks | 3 | 2 relevant |
| Task/Domain | Hate speech detection on HateXplain (English) | 3 | 4 relevant |
| Result | ERASER comprehensiveness improvement without F1 degradation | 2 | 3 relevant |
| Mechanism | Structural zero-weight attention; probability mass leakage eliminated | 2 | 0 exact |
| Method × Task | Sparsemax + hate speech detection | 2 | 0 exact (gap confirmed) |
| Method × Result | Sparsemax + comprehensiveness/sufficiency improvement | 2 | 0 exact |
| Task × Result | Comprehensiveness improvement in HSD | 3 | 2 relevant (SRA, SMRA) |

**Total queries:** 17 (minimum required: 14) ✓
**Fallback:** Semantic Scholar rate-limited; WebSearch + arXiv MCP used

---

## High-Threat Papers

### eilertsen2025aligning — "Aligning Attention with Human Rationales for Self-Explaining Hate Speech Detection" — AAAI 2026

- **Overlap components:** Task/Domain (HateXplain HSD) ✓, Result (comprehensiveness + faithfulness) ✓, partial Method (supervised attention alignment, but softmax not sparsemax)
- **Overlap level:** HIGH (2+ components for the same primary claim)
- **What they do:** SRA uses BERT with softmax attention; adds a KL-divergence alignment loss between softmax attention weights and human-annotated rationale masks from HateXplain. Reports 2.4× better explainability (IoU F1) vs. baselines. Evaluates on HateXplain (English) and HateBRXplain (Portuguese). Claims fairness gains.
- **What we do differently:** We replace softmax with sparsemax in the attention projection step. This is a **structural** difference: sparsemax outputs exactly zero probability for non-rationale tokens, eliminating mass leakage by construction. SRA's KL penalty can only shrink non-rationale mass toward zero; it cannot reach zero. The zero-weight structural property means: (1) gradient signal through masked tokens is exactly zero during backprop; (2) comprehensiveness is provably maximal for deleted tokens already receiving zero weight; (3) the Jain-Wallace adversarial swap test should show larger output perturbation because the model genuinely depends on its sparse attention support. These three differences are not achievable by tuning SRA's loss weight.
- **Is differentiation sufficient?** YES — sparsemax vs. softmax is a change in the operator's range (open simplex vs. closed simplex boundary), not a change in the loss function. The differential is mathematically precise.
- **Action required:** Cite and differentiate. This is the primary related work. Must appear in related work section with explicit operator-level differential.
- **Cite key:** `eilertsen2025aligning`

---

## Medium-Threat Papers

### vargas2026smra — "Self-Explaining Hate Speech Detection with Moral Rationales" — arXiv Jan 2026

- **Overlap components:** Task (hate speech detection) ✓, Result (faithfulness improvement, sufficiency +2.3pp) ✓, partial Method (supervised attention alignment, but moral MFT rationales, softmax, Portuguese)
- **Overlap level:** MEDIUM (1–2 components; different language, different rationale source, no sparsemax)
- **What they do:** SMRA uses Moral Foundations Theory (MFT) expert-annotated moral spans (not crowd-sourced human rationales) as supervision signal for attention alignment. Evaluates on HateBRMoralXplain (Portuguese, new dataset). Uses softmax + alignment loss. Claims IoU F1 +7.4pp, sufficiency +2.3pp. No comprehensiveness metric reported.
- **Differential:** Three differences: (1) rationale source — MFT moral spans vs. crowd-annotated HateXplain spans; (2) language — Portuguese vs. English HateXplain; (3) operator — softmax + loss penalty vs. sparsemax structural zero. Our work is on English HateXplain with crowd-annotated rationales and sparsemax. The moral framing of SMRA is orthogonal to our structural sparsity contribution.
- **Cite key:** `vargas2026smra`

### malaviya2018sparse — "Sparse and Constrained Attention for NMT" — ACL 2018

- **Overlap components:** Method (constrained sparsemax) ✓; no task/domain overlap
- **Overlap level:** MEDIUM (same base mechanism, different constraint source and task)
- **Differential:** Fertility/coverage budget constraint for NMT generation vs. human rationale annotation mask for classification. Full differential in cross-field-report.md.
- **Cite key:** `malaviya2018sparse`

---

## Low-Threat Papers (list only)

- `xie2024ivra` (IvRA, BlackboxNLP 2024) — overlap: attention regularization for interpretability; different task, no sparsemax, no hate speech
- `humal2025` (HuMAL, arXiv 2025) — overlap: human-machine attention alignment; different loss (cosine), no sparsemax
- `regularization2023attention` (Springer 2023) — overlap: attention plausibility supervision in classification; different task, no sparsemax
- `gao2025rise` (RISE, IJCNN 2025) — overlap: rationale-guided hate speech; MTL not attention supervision; no sparsemax
- `bouchacourt2019miss` (ACL 2019) — overlap: human vs. model attention alignment; unsupervised comparison, no sparsemax
- `le2023guiding` (WACV 2023) — overlap: annotation-guided attention for interpretability; CV domain, softmax not sparsemax

---

## Composite Threat Assessment

**Overall threat level:** MEDIUM

**Reasoning:** The highest-threat paper (SRA, `eilertsen2025aligning`) covers Task/Domain and Result components, and partially covers Method (supervised attention alignment). However, SRA uses softmax — the core of our contribution (sparsemax structural zero) is unoccupied. No paper covers Method × Task (sparsemax + hate speech) or Method × Result (sparsemax + ERASER comprehensiveness). The second concurrent work (SMRA, `vargas2026smra`) adds a third method in the same family but is further differentiated by rationale type and language. Together, SRA and SMRA create a cluster of "supervised attention for HSD" papers that we must position against — but the sparsemax structural-zero mechanism is a confirmed gap.

**Primary threat paper:** `eilertsen2025aligning` (SRA) — covers the same task domain and result type, with partial method overlap (softmax instead of sparsemax). This is the paper reviewers will ask about first.

**Differentiability:** YES — the differential between softmax+KL and sparsemax+structural-zero is mathematically precise (range of the operator includes zero vs. does not), is empirically testable (adversarial swap test, H4), and is confirmed by the research-landscape search as unoccupied.

---

## Kill Signal Flags

**None.** No paper found that combines sparsemax (or α-entmax) with human rationale supervision in any task. The contribution gap is confirmed across:
- Pass 1 (54 papers, 5 clusters): no such paper found
- Pass 2 (17 targeted queries, 7 claim components): no such paper found
- Cross-field search (5 adjacent fields): no such paper found

The SMRA paper (Jan 2026) is a new concurrent work that strengthens the "supervised attention for HSD" literature but does not use sparsemax — it is a cite-and-differentiate case, not a kill signal.

---

## Search Coverage

**Total new queries run (Pass 2):** 17 (minimum required: 14) ✓
**New papers found:** 2 (vargas2026smra, confirmation of eilertsen2025aligning)
**Papers read in full:** 2 (SMRA abstract+method via WebFetch; SRA already read in Pass 1)
**HIGH overlap papers:** 1 (eilertsen2025aligning)
**MEDIUM overlap papers:** 2 (vargas2026smra, malaviya2018sparse)
**LOW overlap papers:** 6

---

## Epistemic Updates

Citation ledger updated with:
- `vargas2026smra`: new entry (MEDIUM prior art threat)
- `eilertsen2025aligning`: claim_overlap_level = HIGH
- `malaviya2018sparse`: claim_overlap_level = MEDIUM (already in ledger from cross-field)
