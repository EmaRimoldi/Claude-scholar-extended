# Recency Sweep Report — Sweep 1

**Date:** 2026-04-07
**Sweep ID:** 1
**Window:** 2025-11-01 to 2026-04-07 (post-N1 recency check)
**Coverage:** arXiv cs.CL, arXiv cs.AI, ACL Anthology (AAAI 2026, NAACL 2026), ICLR 2026

---

## Purpose

Confirm that no paper published after the N1 novelty gate date constitutes a new concurrent-work threat. Specifically, check for:
1. Any paper combining sparsemax (or α-entmax) with human rationale supervision in any task
2. Any paper applying sparsemax or α-entmax to hate speech detection
3. Any paper achieving higher ERASER comprehensiveness via structural sparsity on HateXplain
4. Any extension or derivative of SRA (eilertsen2025aligning) or SMRA (vargas2026smra) published since N1

---

## Search Queries Executed

| Query | Tool | Papers Found | Relevant |
|-------|------|-------------|---------|
| `sparsemax entmax hate speech detection 2026 arxiv` | arXiv MCP | 0 | 0 |
| `sparsemax supervised rationale annotation classification 2026` | arXiv MCP | 0 | 0 |
| `HateXplain ERASER comprehensiveness attention faithfulness 2026` | arXiv MCP | 0 | 0 |
| `supervised attention alignment hate speech new 2026` | WebSearch | 2 | 0 (already in ledger) |
| `rationale-supervised BERT explainability arxiv 2025 2026` | WebSearch | 3 | 0 (SMRA already in ledger) |
| `sparsemax attention classification human annotation NLP 2025 2026` | WebSearch | 0 | 0 |

**Total queries:** 6
**New relevant papers found:** 0

---

## Known Concurrent Work (already in ledger)

| Cite Key | Published | Status | Threat Level |
|---------|-----------|--------|-------------|
| `eilertsen2025aligning` (SRA) | Nov 2025 / AAAI 2026 | In ledger; differentiated | HIGH (primary competitor) |
| `vargas2026smra` (SMRA) | Jan 2026 / arXiv | In ledger; differentiated | MEDIUM |

Both papers are already fully incorporated into the novelty assessment (Gate N1). Neither uses sparsemax. The sparsemax × human-rationale-supervision × HSD gap remains unoccupied as of April 7, 2026.

---

## New Concurrent Work Found

**None.**

---

## Threat Assessment Update

| Category | Status |
|----------|--------|
| New full-anticipation paper | NOT FOUND |
| New partial overlap paper (requires repositioning) | NOT FOUND |
| Extension of SRA/SMRA with sparsemax | NOT FOUND |
| New HateXplain ERASER evaluation paper | NOT FOUND |

**Gate N1 decision stands: PROCEED. No repositioning required.**

---

## Verdict

**No new concurrent work.** The recency window (Nov 2025 – Apr 2026) contains no papers that threaten the novelty claim established at Gate N1.

The project may proceed to `/design-experiments` (Step 9).

---

## Routing

Proceed to Step 9 (`/design-experiments`) with Gate N1 constraints:
- Must-have: H1 (comprehensiveness vs. SRA, 5 seeds), H4 (adversarial swap), H2 (rationale density)
- Should-have: H3 (head-selective), H5 (identity-term FPR), W5a (HateBRXplain cross-lingual)
- Required formal contribution: Proposition 1 (structural-zero faithfulness claim)
