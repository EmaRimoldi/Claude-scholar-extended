# Citation Traversal Report (Pass 3)

**Date:** 2026-04-01
**Step:** citation-traversal (Step 5)
**Seed papers used:** 12
**Second-order papers examined:** ~80 (30 SRA refs + 20 TaSc refs + 20 HateXplain forward cites + ~10 sparsemax forward cites scanned)
**New papers found:** 4

---

## Seed Papers

| # | Cite Key | Title | Selection Reason |
|---|----------|-------|-----------------|
| 1 | eilertsen2025sra | SRA: Aligning Attention with Human Rationales | HIGH overlap concurrent work |
| 2 | chrysostomou2021tasc | TaSc: Improving Faithfulness of Attention Explanations | MEDIUM overlap Pass 2 find |
| 3 | martins2016sparsemax | From Softmax to Sparsemax | Foundational method paper |
| 4 | mathew2021hatexplain | HateXplain benchmark | Primary dataset paper |
| 5 | kim2022mrp | MRP: Masked Rationale Prediction | MEDIUM overlap, hate speech baseline |
| 6 | michel2019sixteen | Are Sixteen Heads Really Better than One? | Head selection formula |
| 7 | clark2019bert | What Does BERT Look at? | Head specialization foundation |
| 8 | voita2019heads | Analyzing Multi-Head Self-Attention | Head importance foundation |
| 9 | deyoung2020eraser | ERASER benchmark | Faithfulness metrics |
| 10 | jain2019attention | Attention is not Explanation | Attention faithfulness debate |
| 11 | sundararajan2017ig | Integrated Gradients | Attribution method |
| 12 | correia2019adaptive | Adaptively Sparse Transformers | Sparsemax family extension |

---

## Citation Graph Statistics

| Seed Paper | Forward Citations Retrieved | Backward References Retrieved | High-Score 2nd-Order |
|-----------|---------------------------|------------------------------|---------------------|
| eilertsen2025sra | 0 (too new; <5 citing papers) | 30 refs retrieved | 4 relevant finds |
| chrysostomou2021tasc | — | 20 refs retrieved | 4 relevant (mainly background) |
| martins2016sparsemax | 30 forward cites scanned | — | 1 relevant (Treviso&Martins) |
| mathew2021hatexplain | 20 forward cites scanned | — | 0 new relevant |
| Others | — | — | — |

---

## New Relevant Papers Found

### Treviso & Martins (2020) — "The Explanation Game: Towards Prediction Explainability through Sparse Communication"
- **Found via:** TaSc references (chrysostomou2021tasc), also present in martins2016sparsemax citation neighborhood
- **arXiv:** BlackboxNLP 2020 (ACL Workshop)
- **Citation overlap score:** 2 seed connections (sparsemax + TaSc)
- **Overlap with proposed contribution:** Uses α-entmax (sparsemax family) to produce sparse token-level explanations via structured latent variable communication. The model produces a sparse "message" (selection of tokens) that constitutes the explanation.
- **Overlap level:** MEDIUM — Method component (sparse attention/activation for explanations in NLP). No rationale supervision, no hate speech, no head selection.
- **Differential:**
  > "Treviso & Martins use α-entmax to produce sparse communication as a post-hoc explanation mechanism — the model selects tokens via a latent sparse distribution trained without external supervision. Our work uses sparsemax as the attention activation under explicit MSE/KL/sparsemax_loss supervision from human-annotated token-level rationale masks, applied to gradient-importance-selected BERT heads. The key difference: unsupervised sparse selection (no human annotation target) vs. supervised sparse alignment (binary rationale mask as training signal)."
- **Added to:** citation_ledger.json as `treviso2020sparsecommunication`

---

### Jain et al. (2020) — "Learning to Faithfully Rationalize by Construction" (FRESH)
- **Found via:** Backward reference of eilertsen2025sra; also in TaSc references
- **arXiv:** 2005.00115 | ACL 2020
- **Citation overlap score:** 2 seed connections (SRA + TaSc)
- **Overlap with proposed contribution:** FRESH (Full-text Rationale Extractor with Sparse-Highlighting) trains an extractor to select input tokens and a predictor trained only on those tokens. Faithful by construction: the predictor literally cannot see non-selected tokens.
- **Overlap level:** LOW-MEDIUM — Task×Result (faithful rationalization for NLP, but: extractive pipeline not attention supervision; no sparsemax activation; no hate speech; no head selection).
- **Differential:**
  > "FRESH achieves faithfulness by construction via a binary token selection pipeline (extractor + predictor); the predictor never sees non-selected tokens. Our work achieves faithfulness via attention alignment: the model sees all tokens but attention weights are constrained to concentrate on rationale-annotated spans via sparsemax activation and alignment loss. These are fundamentally different approaches to faithfulness: FRESH enforces it structurally (masking input), our approach enforces it via optimization (alignment loss + sparse activation)."
- **Added to:** citation_ledger.json as `jain2020fresh`

---

### Sen et al. (2020) — "Human Attention Maps for Text Classification: Do Humans and Neural Networks Focus on the Same Words?"
- **Found via:** TaSc references (chrysostomou2021tasc)
- **Venue:** ACL 2020
- **Citation overlap score:** 1 seed connection (TaSc)
- **Overlap with proposed contribution:** Compares human attention (eye-tracking + crowdsourced annotation) with neural attention distributions in text classification. Finds misalignment between human and neural focus.
- **Overlap level:** LOW — Result component (human-neural attention alignment, motivates rationale supervision). No sparsemax, no hate speech, no alignment loss, no head selection.
- **Added to:** citation_ledger.json as `sen2020humanattention`

---

### Strout, Zhang & Mooney (2019) — "Do Human Rationales Improve Machine Explanations?"
- **Found via:** Backward reference of eilertsen2025sra
- **Venue:** BlackboxNLP@ACL 2019
- **arXiv:** 1905.13714
- **Citation overlap score:** 1 seed connection (SRA)
- **Overlap with proposed contribution:** Studies whether supervising models with human rationales improves model-generated explanations. Key finding: human rationales improve model explanations in extractive rationale tasks.
- **Overlap level:** LOW — Result component (positive effect of rationale supervision on explanation quality). Different mechanism (extractive rationale selection, not attention alignment).
- **Added to:** citation_ledger.json as `strout2019humanrationales`

---

## Missed Threads

**Thread 1: Sparse Communication for Explanation (Treviso & Martins group)**
The sparsemax/entmax group at IT Lisbon (Martins, Treviso, Correia, Peters, Niculae) has a research thread on using sparse activation functions for interpretability and communication. This thread (Treviso2020, Correia2019, Peters2019, Martins2016) is in our ledger but the Treviso2020 BlackboxNLP paper was not in Pass 1. No paper in this thread combines sparsemax with external rationale supervision — our work is the first to do so.

**Thread 2: Attention Faithfulness Improvement Methods (Chrysostomou group)**
Papers improving attention faithfulness via architectural modification: TaSc (chrysostomou2021tasc), Mohankumar et al. 2020 (transparent attention models), Bastings et al. 2019 (differentiable binary variables). These are cite-and-differentiate papers: they improve faithfulness via different mechanisms (scaling, structured prediction) without human rationale supervision.

**Thread 3: FRESH-style Faithful Rationalization**
Extractive pipeline approaches to faithful rationalization (Jain2020/FRESH, Lei2016/Rationalizing Neural Predictions). Structurally different from attention alignment: these mask the input to enforce faithfulness rather than supervising attention distributions.

---

## Coverage Assessment

**Papers scanned at abstract level:** ~80
**Papers read in full (methodology):** 4 (Treviso2020, Jain2020/FRESH, Sen2020, Strout2019)
**New HIGH/MEDIUM overlap papers:** 1 (Treviso2020, MEDIUM)
**Kill signals found:** None

---

## Appendix to claim-overlap-report.md

**Additional MEDIUM-threat paper identified in Pass 3:**

### Treviso & Martins (2020) — "The Explanation Game: Sparse Communication"
- **Overlap components:** Method
- **Overlap level:** MEDIUM
- **Key differential:** Unsupervised sparse selection (no human annotation target) vs. our supervised sparse alignment (binary rationale mask from human annotations). No hate speech, no head selection, no alignment loss.
- **Action required:** Cite as background for sparsemax family in explanation; emphasize supervised vs. unsupervised distinction.

**Overall composite threat level (updated from Pass 2):** MEDIUM (unchanged)
**Kill signals:** None identified across all 3 search passes.
