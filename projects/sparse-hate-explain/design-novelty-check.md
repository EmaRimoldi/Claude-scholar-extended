# Design Novelty Check — Gate N2 (Step 10)

**Date:** 2026-03-30
**Step:** 10 / 38
**Gate:** N2
**Inputs:** experiment-plan.md (v3), novelty-assessment-reposition.md, claim-overlap-report.md

---

## Decision: PASS

---

## Checklist

### Critical baselines (blocking if absent)

- [x] **SRA baseline included** (B2: `sra-replication`) — REQUIRED by N1 reposition
- [x] **SMRA baseline included** (B3: `smra-replication`) — REQUIRED by N1 reposition
- [x] **Entmax baseline included** (B4: `entmax-full`) — required by cross-field-report.md finding
- [x] **Random head selection control included** (B5) — isolates importance scoring contribution
- [x] **Vanilla BERT included** (B0) — minimum baseline

### Novelty claim coverage

- [x] H1 tests the primary novelty claim (selective > full-head supervision on comprehensiveness)
- [x] H2 tests the comparison against SRA specifically
- [x] H3 tests the comparison against SMRA specifically
- [x] H4 tests whether importance scoring matters (vs. random selection)
- [x] H5 tests the theoretical span condition
- [x] 2×2×2 ablation isolates all three factors independently

### Statistical adequacy

- [x] ≥10 seeds per condition (10 seeds specified)
- [x] Bootstrap CIs specified (10,000 samples)
- [x] Multiple comparison correction (Bonferroni)
- [x] Effect size reporting (Cohen's d)

### Design-novelty alignment

| Novelty Claim | Tested By | Adequate? |
|--------------|----------|----------|
| Selective-head > full-head on comprehensiveness | H1, M7 vs. M3 | YES |
| Selective-head ≥ SRA (full-head sparsemax) | H2, M7 vs. B2 | YES |
| Importance-based > random head selection | H4, M7 vs. B5 | YES |
| Value-subspace span predicts invariance | H5, K-sweep analysis | YES |
| 2×2×2 ablation disentangles factors | 8-condition design | YES |

---

## Issues Found

### MINOR (non-blocking)

1. **K-sweep not included in 10-seed budget**: The K-sweep (K1–K6) is specified at 10 seeds × 6 conditions = 60 additional runs. Total revised to 260 runs (~65 GPU-hours). Budget should be updated to reflect this.

2. **No out-of-domain dataset**: H6 would ideally test a second dataset (e.g., OffComEval). This is flagged as a limitation, not a blocking issue. The single-dataset concern will be raised in adversarial review.

3. **SMRA replication fidelity**: SMRA uses moral-value subset rationales; replication requires access to SMRA's annotation splits. If unavailable, note this in limitations.

---

## Gate Status

- [x] All novelty claims have corresponding tests
- [x] SRA/SMRA as direct baselines — VERIFIED
- [x] ≥10 seeds — VERIFIED
- [x] 2×2×2 ablation — VERIFIED
- [x] Entmax baseline — VERIFIED
- [x] Decision: PASS
