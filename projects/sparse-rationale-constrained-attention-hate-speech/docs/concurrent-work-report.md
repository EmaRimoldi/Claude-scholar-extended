# Concurrent Work Report (Canonical — Sweep 1)

**Date:** 2026-04-07
**Last Sweep:** Sweep 1 (2025-11-01 to 2026-04-07)
**Next Sweep Due:** After Gate N3 (post-experiment analysis)

---

## Concurrent Works in Scope

### PRIMARY COMPETITOR — eilertsen2025aligning (SRA)

- **Full title:** Aligning Attention with Human Rationales for Self-Explaining Hate Speech Detection
- **Authors:** Brage Eilertsen, Røskva Bjørgfinsdóttir, Francielle Vargas, Ali Ramezani-Kebrya
- **Venue:** AAAI 2026 (arXiv 2511.07065, Nov 2025)
- **Threat level:** HIGH
- **Overlap:** Task (HateXplain HSD), Result (comprehensiveness + faithfulness), partial Method (supervised attention — softmax not sparsemax)
- **Differential:** SRA uses softmax + KL loss; we use sparsemax (closed simplex, zero-weight tokens possible). Structural zero vs. soft penalty. Three distinct testable predictions: H1 (comprehensiveness), H4 (adversarial swap), H3 (head selection).
- **Positioning:** Primary related work. Must appear first in related work section with explicit operator-range differential.

### SECONDARY COMPETITOR — vargas2026smra (SMRA)

- **Full title:** Self-Explaining Hate Speech Detection with Moral Rationales
- **Authors:** Francielle Vargas et al.
- **Venue:** arXiv cs.CL (2601.03481, Jan 2026)
- **Threat level:** MEDIUM
- **Overlap:** Task (HSD), Result (faithfulness improvement). Different rationale type (MFT moral spans), language (Portuguese), dataset (HateBRMoralXplain), operator (softmax).
- **Differential:** Three dimensions: rationale semantics (moral MFT vs. crowd-annotated evidential), language (Portuguese vs. English), operator (softmax vs. sparsemax).
- **Positioning:** Secondary related work; grouped with SRA as "supervised attention for HSD" cluster; explicitly differentiated on three axes.

---

## Gap Statement (Post Sweep 1)

The combination of **(sparsemax) × (human rationale annotation constraint) × (HSD on HateXplain)** remains unoccupied in the literature as of April 7, 2026.

No paper published between November 2025 and April 2026 changes this assessment.

---

## Research Group Trajectory Note

The SRA → SMRA progression suggests an active research group (Vargas and collaborators) working on supervised attention for HSD. The submission timeline and positioning of our sparsemax contribution should be aware that a potential "SMRA-2" or "SRA follow-up with sparsemax" could be submitted to the same venues. This is a competitive risk, not a current kill signal.

**Mitigation:** Expedite submission timeline. Target NeurIPS 2026 or ACL 2026.

---

## Sweep History

| Sweep | Date | Window | New Threats | Action |
|-------|------|--------|-------------|--------|
| 1 | 2026-04-07 | 2025-11-01 to 2026-04-07 | 0 | None — proceed to design |
