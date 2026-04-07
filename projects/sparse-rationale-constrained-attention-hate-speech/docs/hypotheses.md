# Hypotheses — Sparse Rationale-Constrained Attention for Hate Speech Detection

**Project:** sparse-rationale-constrained-attention-hate-speech
**Target venue:** NeurIPS 2026
**Date:** 2026-04-07

---

## Core Contribution Statement

We show that **sparsemax-projected CLS attention supervised by HateXplain rationale masks** achieves **higher ERASER comprehensiveness without macro-F1 degradation** on **HateXplain hate speech detection** by **structurally forcing exactly-zero attention weight on non-rationale tokens, eliminating probability-mass leakage by construction rather than by KL/MSE penalty**.

---

## H1 — Primary Hypothesis: Structural Sparsity Improves Comprehensiveness Without Accuracy Cost

**Formal statement.** Replacing softmax with sparsemax in the final-layer CLS attention of BERT-base, with a supervised sparsemax loss against HateXplain majority-vote rationale masks (median rationale density ~25% of tokens, `mathew2021hatexplain`), yields a statistically significant improvement in ERASER **comprehensiveness** over the SRA-style softmax+KL baseline (`eilertsen2025aligning`), at a macro-F1 indistinguishable from the unsupervised softmax BERT baseline (within ±1.0 F1 points), measured across 5 seeds on HateXplain.

**Motivation.**
- The HateXplain rationale density (~5–6 of ~23 tokens, ~25%; `mathew2021hatexplain`) makes a structurally sparse target *epistemically appropriate*: a softmax target at this density is necessarily a distorted prior because softmax cannot represent exact zeros.
- `eilertsen2025aligning` (SRA) uses softmax + KL alignment, which can only *penalize* mass on non-rationale tokens; it cannot *eliminate* it. `martins2016sparsemax` provides the projection operator that does so.
- Mini-project evidence (3 seeds, BERT-base, HateXplain): comprehensiveness improved significantly under sparsemax supervision; sufficiency was inconsistent.
- `deyoung2020eraser` provides the standardized comprehensiveness/sufficiency protocol; `jacovi2020faithful` provides the conceptual basis for treating structural exclusion as a stronger faithfulness claim than soft penalty.

**Testable prediction.** With 5 seeds × {softmax-baseline, SRA softmax+KL, sparsemax+sparsemax-loss (ours)}:
- Comprehensiveness (AOPC): **Δ ≥ +0.04** absolute over SRA (Cohen's d ≥ 0.5; bootstrap 95% CI excludes 0).
- Macro-F1: **|Δ| ≤ 1.0** vs. unsupervised BERT baseline (equivalence test, TOST, margin 1.0 F1).
- Sufficiency (AOPC): **no significant degradation** (95% CI overlaps SRA).

**Supporting evidence.** `mathew2021hatexplain` (rationale density), `martins2016sparsemax` (operator), `eilertsen2025aligning` (closest competitor that we beat on comprehensiveness), `deyoung2020eraser` (metric protocol), mini-project pilot.

**Kill condition.** If on 5 seeds the sparsemax model's comprehensiveness gain over SRA is < +0.02 AOPC OR macro-F1 drops > 1.0 vs. baseline OR sufficiency degrades significantly (95% CI below SRA), H1 is falsified.

---

## H2 — Rationale Sparsity Assumption (from A1)

**Formal statement.** In the HateXplain hate+offensive subset, the median fraction of tokens receiving majority-vote rationale annotation is **< 30%**, validating that sparsemax (which produces exactly-sparse distributions) is structurally aligned with the annotation prior, whereas softmax (`eilertsen2025aligning`) is not.

**Testable prediction.** Median majority-vote coverage < 0.30; mean < 0.35; histogram right-skewed with mode in [0.10, 0.25].

**Supporting evidence.** `mathew2021hatexplain` reports avg ~5.47/23.42 ≈ 23%; needs verification at majority-vote threshold.

**Kill condition.** If median majority coverage ≥ 30%, the structural-sparsity motivation collapses to a regularization argument and H1's framing must be weakened.

---

## H3 — Head-Selective Supervision Beats Uniform Supervision (from A2/W7)

**Formal statement.** Supervising only the top-k (k=6) gradient-importance heads in BERT's final layer with sparsemax+rationale loss achieves higher comprehensiveness AND lower syntactic-probe degradation than supervising all 12 heads, by avoiding interference with positional/syntactic specialist heads.

**Testable prediction.** Top-6 head variant: comprehensiveness ≥ all-12 variant (within noise or higher), AND POS-tagging linear probe accuracy on unsupervised heads drops by < 2 points (vs. > 5 points for all-12).

**Supporting evidence.** `correia2019adaptively` shows heads naturally specialize sparsity levels; `eilertsen2025aligning` does not address head selection.

**Kill condition.** All-12 variant matches or exceeds top-6 on comprehensiveness AND no measurable probe degradation.

---

## H4 — Structural Sparsity Causally Constrains the Decision (from A3/W6)

**Formal statement.** Under the Jain & Wallace (`jain2019attention`) adversarial-attention-swap test, replacing the sparsemax model's CLS attention with uniform weights produces a **larger** output KL-divergence shift than the same swap on a softmax-supervised model, demonstrating that sparsemax supervision genuinely *constrains the model's computation* rather than producing post-hoc-correlated weights.

**Testable prediction.** Mean KL(pred(uniform) || pred(original)) for sparsemax model ≥ 2× the value for softmax baseline; Wilcoxon signed-rank p < 0.01.

**Supporting evidence.** `jain2019attention`, `wiegreffe2019attention` define the test; `eilertsen2025aligning` does not run it.

**Kill condition.** KL shift for sparsemax ≤ softmax baseline → attention is not causal → sparsemax provides only cosmetic faithfulness.

---

## H5 — Sparsemax Supervision Reduces Identity-Term Shortcut Bias (from Cluster 5)

**Formal statement.** Sparsemax-supervised BERT exhibits **lower false-positive rate on minority-identity-mention non-hate posts** (HateXplain target community subgroups) than both unsupervised BERT and SRA softmax+KL, because exact-zero attention on non-rationale identity tokens structurally prevents identity-term shortcut activation.

**Testable prediction.** On HateXplain test subset filtered to non-hate posts containing identity terms (`chen2024fairness` protocol), FPR(sparsemax) ≤ FPR(SRA) − 0.03, and ≤ FPR(BERT-base) − 0.05; bootstrap 95% CI excludes zero.

**Supporting evidence.** `chen2024fairness`, `elsafoury2022bias`, `causal2023emnlp`. `eilertsen2025aligning` claims fairness gains from soft alignment; we predict structural sparsity strengthens this.

**Kill condition.** FPR(sparsemax) ≥ FPR(SRA) (no improvement) → structural constraint does not amplify fairness benefit.

---

## Null Hypotheses

- **H1₀:** Sparsemax+rationale supervision yields no comprehensiveness improvement over SRA (`eilertsen2025aligning`); any difference is within seed noise.
- **H2₀:** HateXplain majority-vote rationale coverage ≥ 30% — annotations are not structurally sparse.
- **H3₀:** Head selection has no effect; all-12-head supervision is statistically equivalent to top-6.
- **H4₀:** Adversarial attention swap produces equal output shifts across softmax and sparsemax models — attention is not causal in either.
- **H5₀:** Identity-term FPR is unchanged or worsened under sparsemax supervision relative to SRA.

---

## Novelty Positioning

**vs. `eilertsen2025aligning` (SRA, AAAI 2026):** SRA aligns *softmax* attention to rationale masks via a KL penalty. Softmax's range is the open simplex — non-rationale tokens always retain *some* probability mass; the penalty only shrinks it. Our sparsemax projection is a *closed-form Euclidean projection onto the simplex* (`martins2016sparsemax`) whose output range *includes the boundary*: non-rationale tokens can receive **exactly zero** weight, with zero gradient flow through the masked-out positions. This is a **structural** (range-of-the-operator) difference, not a tuning-of-the-loss difference. Empirically it predicts (i) higher comprehensiveness because deletion of exactly-zero-weight tokens cannot perturb the representation, and (ii) a stronger Jain–Wallace causal-attention signature (H4).

**vs. `malaviya2018sparse` (Constrained Sparsemax for NMT, ACL 2018):** Malaviya et al. apply constrained sparsemax in *encoder-decoder NMT*, with the constraint being a **fertility/coverage budget** (each source token's total attention across decoder steps is upper-bounded by an algorithmically-derived scalar). Our constraint is a **binary support mask from human rationale annotations**, applied in an **encoder-only classification** setting, with the optimization objective being **joint classification + ERASER faithfulness** (`deyoung2020eraser`), not BLEU. The constraint mechanism (annotation mask vs. coverage counter), task family (classification vs. generation), and evaluation framework (faithfulness vs. translation quality) are all distinct.

---

## Hypothesis Priority Ranking

| ID | Hypothesis | Novelty | Testability | NeurIPS Impact |
|----|-----------|---------|-------------|----------------|
| H1 | Sparsemax structural sparsity → comprehensiveness gain w/o F1 cost | **HIGH** | **HIGH** (ERASER on HateXplain, 5 seeds, equivalence test) | **HIGH** (core contribution, differentiates from SRA) |
| H4 | Adversarial swap shows sparsemax causally constrains computation | **HIGH** | **HIGH** (single-pass test on existing checkpoints) | **HIGH** (addresses Jain–Wallace debate with new evidence) |
| H3 | Top-k head supervision > all-head supervision | MEDIUM | **HIGH** (4 variants × 5 seeds + linear probe) | MEDIUM (mechanistic insight, ablation depth) |
| H5 | Sparsemax reduces identity-term FPR more than SRA | MEDIUM | MEDIUM (subgroup FPR, requires careful subset) | **HIGH** (fairness narrative for moderation deployment) |
| H2 | HateXplain rationales are structurally sparse (median <30%) | LOW | **HIGH** (analysis only, no GPU) | LOW (validation, not contribution) |

**Top priority for NeurIPS submission:** H1 (core), H4 (mechanistic validation), H5 (impact narrative). H2 and H3 are supporting/ablation experiments.
