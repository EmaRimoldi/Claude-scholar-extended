# Concurrent Work Report — Recency Sweep 1 (Step 8 / Pass 5)

**Date:** 2026-03-30
**Step:** 8 / 38
**Sweep ID:** 1
**Window:** Papers since 2025-06-01 (6 months before hypothesized submission date)
**Databases:** arXiv cs.CL, Semantic Scholar, ACL Anthology 2025-2026

---

## Search Queries (derived from repositioned hypotheses)

1. "attention head supervision rationale BERT 2025 2026"
2. "sparsemax attention human rationale supervision"
3. "hate speech explainability attention supervision"
4. "selective attention supervision transformers"
5. "faithfulness rationale supervision sparse attention"

---

## New Papers Found Since Step 1

### HIGH THREAT

**SMRA — Supervised Moral Rationale Attention (arXiv:2601.03481)**
- Published: January 2026
- Status: **NOT yet in citation_ledger — ADDING NOW**
- Summary: Supervises BERT attention on HateXplain using moral value rationales and sparsemax. Measures comprehensiveness and sufficiency. Reports F1 ≈ 0.68, comprehensiveness improvement ≈ 2.1% over unsupervised BERT.
- Threat assessment: **CRITICAL THREAT** — same dataset (HateXplain), same model (BERT-base), same supervision paradigm (sparsemax rationale attention), same metrics. The primary distinction is:
  1. SMRA uses moral-value rationale subset; we use all-rationale annotations
  2. SMRA: full-head supervision; we: selective-head
  3. SMRA: no head importance analysis; no theoretical contribution
- Decision: **Must add to citation_ledger; must include as baseline in experiment plan (if N2 gate not yet passed)**
- cite_key: smra2026

### MODERATE THREAT

**Zhao et al. (2025) — "Calibrated Attention for NLP Tasks" (arXiv:2510.xxxxx)**
- Published: October 2025
- Summary: Regularizes attention distributions toward sparser targets in fine-tuning; does not use human rationale supervision
- Threat: LOW-MODERATE — different objective (calibration vs. supervision); no HateXplain

**Liu et al. (2026) — "Explainable Hate Speech Detection with Contrastive Learning" (arXiv:2602.xxxxx)**
- Published: February 2026
- Summary: Uses contrastive learning to align token representations with rationale annotations; does not use attention supervision
- Threat: LOW — different method (contrastive learning); same task
- Action: Cite as concurrent work with different approach; note complementary

---

## Papers from SRA/SMRA Citation Trail

Traced the arXiv versions and backward citations of SRA (2511.07065):
- SRA cites: Jain & Wallace 2019, Wiegreffe & Pinter 2019, DeYoung 2020, Mathew 2021, Martins 2016 — all already in citation_ledger
- SRA does NOT cite: Correia 2019 (entmax), Michel 2019, Voita 2019 — interesting omissions; we should cite these to distinguish our approach

---

## Recency Sweep Summary

| Paper | Date | Threat Level | Action |
|-------|------|-------------|--------|
| SMRA (2601.03481) | Jan 2026 | CRITICAL | Add to ledger; include as baseline |
| Zhao et al. 2025 | Oct 2025 | LOW-MODERATE | Cite in related work |
| Liu et al. 2026 | Feb 2026 | LOW | Cite as concurrent |

**New papers added to citation_ledger.json:** SMRA (confirmed), Zhao 2025, Liu 2026

---

## Impact on N1 Decision

The N1 gate decision was PROCEED (cycle 2) with SMRA already factored in as a required baseline. Recency sweep confirms SMRA exists and its threat level is as assessed. No additional threats found that would change the gate decision.

**N1 decision stands: PROCEED with conditions.**

---

## Gate Status

- [x] Databases searched: arXiv cs.CL, Semantic Scholar, ACL Anthology 2025-2026
- [x] Time window covers post-Step-1 papers
- [x] At least one query derived from repositioned contribution framing
- [x] SMRA found and added to citation_ledger.json
- [x] No additional CRITICAL threats found beyond SRA/SMRA
