# Concurrent Work Report

**Last updated:** 2026-04-01 (Sweep 1)
**Project start date:** 2026-04-01
**Lookback window:** 2026-01-01 to 2026-04-01 (90 days)

---

## Sweep History

| Sweep | Date | Queries Run | Papers Screened | New Relevant | Max Severity | Action |
|-------|------|-------------|----------------|-------------|-------------|--------|
| Sweep 1 | 2026-04-01 | 7 | ~60 | 3 new (SMRA already known) | should_be_cited | Add to ledger; cite in related work |
| Sweep 2 | — | — | — | — | — | — |
| Sweep Final | — | — | — | — | — | — |

---

## Query Log (Sweep 1)

**Query category 1 — Key technical terms:**
1. `"sparsemax" attention rationale supervision hate speech` (arXiv cs.CL, 2026-01-01+) → 0 relevant
2. `ti:"sparsemax" OR ti:"rationale attention" OR ti:"attention supervision" classification explainability` (arXiv cs.CL, 2026-01-01+) → 2 should_be_cited
3. `"rationale supervised attention" OR "attention rationale alignment" hate speech explainability` (arXiv cs.CL, 2026-01-01+) → 0 relevant

**Query category 2 — Method + task combinations:**
4. `ti:"hate speech" explainability rationale attention faithfulness 2026` (arXiv cs.CL, 2026-01-01+) → 1 should_be_cited (SMRA already known, X-MuTeST new)
5. `"HateXplain" attention explainability BERT rationale supervision 2026` (arXiv cs.CL, 2026-01-01+) → 0 new

**Query category 3 — Closest prior work forward citations:**
6. `S2 citations of arXiv:2511.07065 (SRA)` → 2 papers: TabSieve (irrelevant) + SMRA (already in ledger)

**Query category 4 — Author monitoring:**
7. `au:Eilertsen attention rationale hate speech 2025 2026` (arXiv cs.CL, 2025-10-01+) → 0 new papers

**Total papers screened:** ~60 (across all queries; most returned generic recent cs.CL papers not matching topic)
**Null result confirmation:** 0 new papers covering sparsemax + rationale supervision; 0 new papers covering gradient head selection + supervision

---

## Active Concurrent Work (Requires Attention)

*No papers classified as `blocks_project` or `requires_repositioning` found in Sweep 1.*

---

## Should-Be-Cited Papers (New, not in ledger)

### Rehman et al. (2026) — "X-MuTeST: A Multilingual Benchmark for Explainable Hate Speech Detection" — arXiv:2601.03194

- **First found:** Sweep 1 (2026-04-01)
- **Published:** 2026-01-06
- **Severity:** `should_be_cited`
- **Overlap description:** Applies human token-level rationale annotations to improve explainability in hate speech detection; evaluates with IoU-F1, Token-F1, Comprehensiveness, Sufficiency; includes English HateXplain data (6,334 samples). Combines LLM explanations with X-MuTeST probability-difference scores to refine model attention.
- **Classification:** `subset` — overlaps on task and evaluation metrics; mechanism is fundamentally different (LLM-based probability difference vs. BERT attention supervision with alignment loss)
- **Technical differential:** X-MuTeST uses an LLM-consulted approach: the explanation is the union of LLM-generated explanations and token prediction probability differences (P(y|x) - P(y|x \ t)). No attention mechanism modification, no alignment loss, no sparsemax, no head selection. Our method applies sparse attention supervision directly to specific BERT heads — a different mechanism targeting the model's internal attention rather than building a post-hoc explanation.
- **Related work update:** Cite in Related Work as an independent approach to human-rationale-guided explainability using LLMs; note that it confirms the value of human rationale annotations but uses a post-hoc explanation method rather than attention supervision.

---

### Tchuente Mondjo (2026) — "Bi-Attention HateXplain: Taking into account the sequential aspect of data during explainability in a multi-task context" — arXiv:2601.13018

- **First found:** Sweep 1 (2026-04-01)
- **Published:** 2026-01-19
- **Severity:** `should_be_cited`
- **Overlap description:** BiRNN-based multi-task model (explainability + classification) on HateXplain; addresses attention variability in prior HateXplain-based methods; evaluates with HateXplain metrics.
- **Classification:** `subset` — uses HateXplain; different architecture (BiRNN, not BERT); no sparsemax, no rationale alignment loss, no head selection
- **Technical differential:** Uses BiRNN + bidirectional attention rather than BERT; multi-task classification + explainability without external rationale supervision signal. More similar to multi-task learning on BERT baselines than to rationale-supervised attention alignment.
- **Related work update:** Cite as an alternative architecture approach to explainable hate speech detection on HateXplain; note it uses a different mechanism (multi-task BiRNN) from ours.

---

### Mersha & Kalita (2026) — "CA-LIG: Context-Aware Layer-Wise Integrated Gradients for Explaining Transformer Models" — arXiv:2602.16608

- **First found:** Sweep 1 (2026-04-01)
- **Published:** 2026-02-18
- **Severity:** `should_be_cited`
- **Overlap description:** Proposes a layer-wise IG framework for Transformer explainability; applied to hate speech detection (XLM-R, AfroLM). Uses IG as the attribution method — directly relevant to our H4 hypothesis (IG vs. LIME stability).
- **Classification:** `independent_confirmation` — confirms the value of IG-based attribution for hate speech detection; strengthens our motivation for using IG over LIME; but is post-hoc attribution, not training-time attention supervision
- **Technical differential:** CA-LIG is a post-hoc attribution method (layer-wise IG for visualization), applied after training. Our work uses IG for faithfulness evaluation (comprehensiveness/sufficiency) under the ERASER framework — different use case (evaluation vs. explanation visualization). CA-LIG does not modify attention mechanisms or use rationale supervision.
- **Related work update:** Cite as independent evidence that IG provides more faithful attribution than post-hoc methods (LIME) for hate speech detection; strengthens H4 motivation.

---

### Vargas et al. (2026) — SMRA — arXiv:2601.03481

- **Status:** Already in `citation_ledger.json` as `vargas2026smra`
- **Last seen:** Sweep 1 (confirmed still the only forward citation of SRA that is relevant)
- **Severity:** MEDIUM (unchanged from Pass 2 assessment)
- **Action:** No new action required; existing differential statement stands

---

## Dismissed Papers (no_impact)

All other papers screened were immediately dismissed as irrelevant:
- LLM routing (NeuralUCB), speech timing, news reuse, radiology summarization, speech recognition — no overlap
- Claim detection, mechanistic interpretability, narratives — no overlap with rationale supervision or hate speech
- SemEval/CLEF shared tasks (climate fact-checking, historical texts, financial QA, spoken dialogue) — no overlap
- Medical EHR classification, crop disease VQA — no overlap

---

## Kill Signal Events

**No `blocks_project` papers found.** No paper appeared in the last 90 days that covers:
- Sparsemax as attention activation under rationale supervision
- Gradient-importance head selection for rationale supervision
- Both combined in hate speech or any classification task

---

## Concurrent Work Baseline Summary

**Pre-existing concurrent work (from prior passes):**

| Paper | arXiv | Published | Overlap | Severity |
|-------|-------|-----------|---------|---------|
| Eilertsen et al. (2025) SRA | 2511.07065 | Nov 2025 | Task + Result + 3 baselines | should_be_cited (concurrent work) |
| Vargas et al. (2026) SMRA | 2601.03481 | Jan 2026 | Task + Moral rationale extension | should_be_cited |

**New papers from Sweep 1:**

| Paper | arXiv | Published | Overlap | Severity |
|-------|-------|-----------|---------|---------|
| Rehman et al. (2026) X-MuTeST | 2601.03194 | Jan 2026 | Task + human rationales (different mechanism) | should_be_cited |
| Tchuente Mondjo (2026) BiAtt-HateXplain | 2601.13018 | Jan 2026 | Task (HateXplain, BiRNN, different arch) | should_be_cited |
| Mersha & Kalita (2026) CA-LIG | 2602.16608 | Feb 2026 | Evaluation method (IG for hate speech) | should_be_cited |

**Summary:** The concurrent work landscape confirms that the HateXplain explainability area is active (5 papers with HateXplain overlap in last 5 months), but no paper covers the sparsemax + head selection + BERT attention supervision combination. The mechanism gap (C1+C2) remains clean.
