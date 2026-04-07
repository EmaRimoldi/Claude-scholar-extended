# Paper Quality Report — Sparse Rationale-Constrained Attention (NeurIPS 2026)

**Date:** 2026-04-07
**Reviewer:** verify-paper (7-dimensional audit)
**Artifact:** `manuscript/paper.tex` (407 lines) vs `docs/claim-ledger.md`

---

## Dimension Scores

| # | Dimension | Score (1-5) |
|---|-----------|-------------|
| 1 | Claim-Evidence Alignment | **4** |
| 2 | Statistical Rigor | **4** |
| 3 | Novelty Clarity (structural argument) | **5** |
| 4 | Limitation Honesty | **5** |
| 5 | Related Work Coverage | **4** |
| 6 | Reproducibility | **3** |
| 7 | Narrative Coherence | **5** |

**Overall:** 30/35. No dimension scores ≤ 2 → **no hard blocks**.

---

## 1. Claim-Evidence Alignment — 4/5

Every headline claim in the abstract and contributions is traceable to Table 2 (`tab:main_results`, lines 235-254) and matches the ledger's E1-E11 exactly.

- Abstract F1 numbers (L41-42), comprehensiveness +111% (L42-43), sufficiency 47% (L44), H4 miss 1.47× (L46) all map to ledger C-MAIN, C-FAITHFUL, C-NOCOST.
- Wilcoxon stat=15, p=0.031, d=8.36 reproduced verbatim (L267-269).

**Minor issues:**
- L13 of ledger says C4 comp = 0.337 ± 0.026; paper says 0.338 ± 0.026 (L250, L265). Rounding drift — reconcile to a single value.
- C-NOCOST claim "all pairwise MWU p > 0.67" (ledger E10) is **not reported** in the paper. Add a line or supplementary table, otherwise the parity claim rests solely on TOST vs C1 while the ledger promises a broader parity story.
- M2 in the paper (L317-319) is phrased mechanistically but does not cite the M1→M2→M3 chain by an explicit result number.

## 2. Statistical Rigor — 4/5

Strong: paired Wilcoxon one-sided (pre-specified direction), TOST equivalence with declared ±1.0 pp margin, Cohen's d on per-seed differences, explicit n=5.

**Gaps:**
- No confidence intervals on AOPC gains — only mean ± std. A 95% CI (even bootstrap) would make the +0.178 absolute effect concrete.
- The "smallest possible p at n=5" note (L268) is correct but should be flagged as a **power ceiling**: any n=5 Wilcoxon can report at most p=0.031, so this is not a probability-of-replication statement.
- TOST margin ±1.0 pp is declared but the **pre-registration document is not cited**. Add a pointer (e.g., `hypotheses.md` commit hash or OSF link) in the reproducibility section.
- H4 Wilcoxon reports direction-significance (p=0.031) alongside a missed magnitude threshold — good honesty, but should explicitly state that the pre-registered test was **magnitude, not direction**.

## 3. Novelty Clarity (structural argument) — 5/5

The residual-escape-route framing (L69-72) and Proposition 1 (L188-205) are the clearest part of the paper. Sparsemax-range-vs-softmax-range is stated both intuitively ("softmax admits no such τ", L203) and operationally (M1→M2→M3, L312-324). This is the paper's strongest selling point and is communicated unambiguously.

## 4. Limitation Honesty — 5/5

All four skeptic-agent vulnerabilities from the ledger are disclosed:

- H4 miss: L46, L89-91, L275-282, L376-378, and conclusion L397-399. Reported four times without hedging or post-hoc reframing.
- Single dataset / BERT-base only: L378-380.
- Plausibility = 0: L284-288 and L380-383, correctly attributed to dataset artefact.
- n=5 ceiling: L384-386 with explicit suggestion of a 10-seed replication.

Exemplary disclosure; nothing to fix.

## 5. Related Work Coverage — 4/5

Covered: Jain & Wallace 2019 (L58, L350), Wiegreffe & Pinter 2019 (L58, L351), Martins sparsemax (L60, L357), Malaviya constrained sparsemax (L60, L358), Correia adaptively-sparse (L60, L359), DeYoung ERASER (L61, L363), Jacovi & Goldberg faithful-by-construction (L119, L353), SRA / Eilertsen 2025 (L62, L126, L365), HateXplain (L66, L102, L369).

**Gaps:**
- No citation to **post-hoc rationale extraction** line (Lei et al. 2016, Bastings et al. 2019) — relevant to "most rationale-supervised models use post-hoc extractors" (L363-364). Add at least Lei-Barzilay-Jaakkola.
- No citation to **entmax / α-entmax** (Peters et al. 2019) — a natural contemporary of sparsemax that reviewers will expect to see alongside Correia 2019.
- Hate-speech XAI paragraph (L368-371) is thin — one citation only. At least reference Mathew's follow-ups or a recent (2024-2025) hate-speech interpretability paper to show awareness.

## 6. Reproducibility — 3/5

Declared (L216-223): BERT-base-uncased, 5 epochs, batch 16, AdamW, lr 2e-5, weight decay 0.01, 10% linear warmup, λ=0.1, seeds {13,17,29,42,71}, single A100.

**Missing:**
- No HateXplain **version / split hash** (the paper itself notes that "the public HateXplain release" has rationale issues — which release? commit? HuggingFace revision?).
- No mention of **code release URL** (even an anonymized placeholder).
- No **software versions** (transformers, torch, CUDA).
- No **sparsemax implementation** pointer (from-scratch? entmax package?).
- No tokenizer max-length, no mention of how rationales are projected onto BERT wordpieces (critical for MSE computation).
- Rationale normalization `r / ||r||_1` is stated (L141) but the handling of **all-zero rationales** (no majority) is undefined — given plausibility=0 caveat, this is load-bearing.
- Figure 1 references `figures/main_results.pdf` but no data/plot script is cited.

This is the weakest dimension and the single largest reviewer risk.

## 7. Narrative Coherence — 5/5

Problem (attention unfaithful) → diagnosis (residual escape route) → theory (Proposition 1) → method (C4/C5) → results (H1-H3 ✓, H4 ✗) → mechanism (M1→M2→M3) → honest limits → crisp recipe. The story flows end-to-end and the "right idea, wrong instantiation" framing (L391-392) is memorable and defensible.

---

## Hard Blocks

**None.** No dimension scores ≤ 2.

---

## Overall Verdict

### **NEEDS_MINOR_REVISION**

The paper is substantively ready. All fixes below are bounded edits (≈1 day total), not re-experiments.

---

## Top 5 Actionable Fixes (ordered by impact)

1. **Reproducibility artefact block (Dim 6).** Add a "Reproducibility" paragraph in §5.1 or an appendix listing: HateXplain HuggingFace revision, transformers/torch/CUDA versions, sparsemax implementation (entmax package or custom), tokenizer max length, wordpiece-rationale projection rule, handling of all-zero rationales, and a code release URL (anonymized for review). Highest reviewer-risk-per-edit.

2. **Report full pairwise MWU parity table (Dim 1).** The ledger's C-NOCOST promises "all pairwise p > 0.67" but the paper only shows TOST vs C1. Add a 5×5 pairwise-F1 supplementary table or at least one sentence in §4.3 referencing it. Aligns paper with ledger and pre-empts "but did you compare C2 vs C4 on F1?"

3. **Confidence intervals on AOPC gains (Dim 2).** Add bootstrap or analytic 95% CIs for comprehensiveness (+0.178) and sufficiency (−0.158) deltas in Table 2 caption or a footnote. Also add a one-sentence caveat that p=0.031 is the n=5 Wilcoxon floor, not evidence of strong replication probability.

4. **Close related-work gaps (Dim 5).** Add citations for: Lei-Barzilay-Jaakkola 2016 (rationalizing NN), Bastings et al. 2019 (interpretable extractive), Peters et al. 2019 (α-entmax), and one 2024-2025 hate-speech interpretability paper. Prevents a "superficial related work" reviewer complaint.

5. **Reconcile 0.337 vs 0.338 and clarify H4 test semantics (Dim 1, 2).** Pick one rounding for C4 comprehensiveness across ledger + paper. In the H4 paragraph (L275-282), explicitly note that the **pre-registered criterion was on magnitude (≥2×)** and the p=0.031 refers to direction — this frames the honest miss even more sharply and removes ambiguity.

---

## Summary

The paper is honest, structurally coherent, and mechanistically well-argued. The statistical story is tight, and the H4 miss is handled with unusual integrity. The only real gap is reproducibility metadata; everything else is polish. With the five fixes above, this is submission-ready for NeurIPS 2026.
