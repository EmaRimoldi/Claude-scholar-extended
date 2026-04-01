---
schema_version: 1

# Required (this is what Step 1 consumes)
project_slug: sparse-rationale-constrained-attention-hate-speech
research_topic: "Sparse Rationale-Constrained Attention for Hate Speech Detection"

# Optional (leave out anything you don't care about)
display_title: "Sparse Rationale-Constrained Attention for Hate Speech Detection"
domain_hints:
  - optional keyword
  - optional adjacent field
target_venue: neurips
skip_online: false
seeds_per_condition: 5
gpus_per_job: 1
---

# RESEARCH_PLAN.md
# Sparse Rationale-Constrained Attention for Hate Speech Detection
## NeurIPS 2026 Submission — Working Research Plan

---

## 0. Context and Goal

This plan extends a mini-project (EE-559, Group 49) that investigated replacing softmax
with sparsemax in BERT's CLS-token attention, supervised against human-annotated
rationales from HateXplain. The original project found a statistically significant
improvement in comprehensiveness but no consistent gains elsewhere, over only 3 training
runs. This document identifies every assumption the original project made, designs
experiments to test each one, lists the known weaknesses of the current approach, and
proposes experiments to challenge or refute them.

---

## 1. Assumptions of the Original Paper — and How to Test Them

### A1 — Human rationale annotations are inherently sparse

**Claim:** The motivation for sparsemax over softmax as a target distribution is that
human annotators mark only a few key tokens per post — making a dense softmax target
epistemically wrong.

**Why this matters:** If annotators actually cover the majority of tokens, the sparse
target is just a distortion, not a better prior. The whole paper collapses.

**Test (E-A1):**
- Compute, for every hate/offensive post in HateXplain train+test, the fraction of
  tokens receiving ≥1 annotator rationale vote and the fraction receiving majority
  vote (≥2/3 annotators).
- Report mean, median, and distribution (histogram).
- Acceptance criterion: median coverage < 30% of tokens.
- If violated: the sparsemax motivation weakens to a regularisation argument only,
  which must be stated explicitly.

```python
# pseudo-code
for post in hatexplain["hate", "offensive"]:
    n_tokens = len(post.tokens)
    n_any_vote = sum(1 for t in post.tokens if any_annotator_flagged(t))
    n_majority_vote = sum(1 for t in post.tokens if majority_flagged(t))
    coverage_any.append(n_any_vote / n_tokens)
    coverage_majority.append(n_majority_vote / n_tokens)
```

---

### A2 — Supervising all 12 final-layer heads is equivalent to supervising the
### "right" heads

**Claim (implicit in the original paper):** The paper applies the sparsemax supervision
loss uniformly to all 12 heads of BERT's final layer without justification.

**Why this matters:** Clark et al. (2019) and Voita et al. (2019) showed that BERT heads
specialise. Applying a semantic rationale loss to syntactic/positional heads may degrade
those representations and introduce noise into the alignment signal.

**Test (E-A2a) — Head Importance Scoring:**
- Compute gradient-based importance of each head h in layer ℓ:
  I(h, ℓ) = E_x [ |∂L_cls / ∂A^{CLS,h,ℓ}| ]
  over the training set.
- Rank heads by importance; cluster into high-importance (semantic) and low-importance
  (structural) groups.
- Train four variants: supervise top-3 / top-6 / top-9 / all-12 heads (final layer).
- Metric: compare comprehensiveness, plausibility IoU-F1, and F1 across variants.
- Expected result: supervising top-6 outperforms all-12.

**Test (E-A2b) — Layer Selection:**
- Train variants supervising: final layer only / layers {8,9,10,11} / layers {4,5,6,7}.
- Acceptance criterion: at least one intermediate-layer variant matches or beats
  final-layer-only on comprehensiveness.

---

### A3 — Sparsemax supervision does not alter the classification decision boundary
### (Functional Invariance)

**Claim:** The paper observes that F1 does not degrade under sparsemax supervision and
treats this as a non-result. In fact it is a non-trivial claim: enforcing exact zeros
in CLS attention removes token-to-CLS information pathways.

**Why this matters:** If the boundary shifts, then accuracy and interpretability are
in tension. If it does not shift, we have a result: transparency without accuracy cost.

**Test (E-A3a) — Subspace Principal Angle Analysis:**
- Extract value matrices V_soft (softmax model) and V_sparse (sparsemax model) for the
  supervised heads across the test set.
- Compute the principal angles between span(V_soft) and span(V_sparse) using SVD.
- If angles ≈ 0, the value subspaces are aligned → span condition holds → boundary
  stable → confirms A3.
- If angles are large, boundary stability must be explained differently.

```python
from torch.linalg import svd
U_soft, _, _ = svd(V_soft, full_matrices=False)
U_sparse, _, _ = svd(V_sparse, full_matrices=False)
# principal angles via cosines of singular values of U_soft.T @ U_sparse
cos_angles = svd(U_soft.T @ U_sparse, full_matrices=False).S
```

**Test (E-A3b) — Adversarial Attention Swap:**
- Following Jain & Wallace (2019): replace the CLS attention weights of the sparsemax
  model with uniform weights, run inference, record output change (KL divergence of
  output distribution).
- If KL is small → attention weights are not causal for the prediction → the boundary
  is not actually constrained by attention supervision.
- If KL is large → attention supervision genuinely constrains the model's computation.

**Test (E-A3c) — Confidence Calibration Check:**
- Compare ECE (Expected Calibration Error) between softmax-supervised and
  sparsemax-supervised models.
- A shift in calibration would indicate that even if macro-F1 is stable, the model's
  confidence distribution has changed — a practically important effect.

---

### A4 — LIME is a valid faithfulness evaluator for this task

**Claim (implicit):** The original paper uses LIME-based comprehensiveness and
sufficiency as faithfulness metrics without questioning whether LIME is appropriate here.

**Why this matters:** LIME fits a local linear surrogate via input perturbation. For
short social media posts (avg ~20 tokens), the perturbation space is small and LIME
estimates are highly variable. More critically, LIME rationales are not tied to the
model's actual computation — they can disagree with gradient-based attributions for the
same input.

**Test (E-A4a) — LIME Stability:**
- Run LIME 10 times on the same 50 posts with different random seeds.
- Compute variance of the rationale token rankings across runs.
- Acceptance criterion: Kendall's τ > 0.8 between runs. If violated, LIME is
  unreliable for this evaluation.

**Test (E-A4b) — LIME vs. IG Agreement:**
- Compute Spearman correlation between LIME token scores and Integrated Gradients (IG)
  scores on the full test set.
- If correlation < 0.5, the two methods are measuring different things, and using LIME
  as the faithfulness oracle is unjustified.
- Report comprehensiveness and sufficiency under both LIME and IG attributions for all
  models.

**Recommended replacement:** Use IG (Captum library) as the primary faithfulness
evaluator:
```python
from captum.attr import IntegratedGradients
ig = IntegratedGradients(model)
attributions = ig.attribute(inputs=embedding, baselines=pad_embedding,
                            target=predicted_class, n_steps=50)
```

---

### A5 — Three training runs are sufficient for statistical conclusions

**Claim:** The original paper runs each model configuration 3 times and reports means
with 95% CIs assuming normality.

**Why this matters:** With effect sizes |d| ≤ 0.18 (as observed), and n=3 runs, the
power to detect true differences is very low (~30–40%). The paper's own analysis
shows most differences are non-significant.

**Test (E-A5):**
- Run every model configuration with 10 random seeds.
- Report bootstrap confidence intervals (B=1000) rather than t-distribution CIs.
- Compute power analysis post-hoc for each metric to determine the minimum effect size
  detectable at 80% power.
- Acceptance criterion: Cohen's d > 0.3 for at least comprehensiveness metric to
  justify a "significant improvement" claim.

---

### A6 — The sparsemax loss is the right alignment loss (vs. cross-entropy or MSE)

**Claim:** The paper uses sparsemax loss to align model attention with sparse targets,
but never compares against other loss functions that could also produce sparse attention.

**Test (E-A6):**
- Train four variants: (a) sparsemax target + sparsemax loss [original], (b) sparsemax
  target + KL divergence loss, (c) sparsemax target + L2 loss, (d) softmax target +
  cross-entropy loss [Mathew et al. baseline].
- Compare all metrics. This isolates whether it is the target construction or the loss
  that drives gains.

---

## 2. Weaknesses of the Current Paper and Experiments to Address Them

### W1 — The evaluation uses LIME, which is not faithful by construction

**Weakness:** As described in A4 above, LIME is a post-hoc surrogate. Using it to
evaluate "faithfulness" of attention is circular: we are asking whether attention aligns
with a surrogate of the model, not with the model itself.

**Fix:** Replace LIME with Integrated Gradients as primary faithfulness evaluator.
Keep LIME as a secondary baseline to allow comparison with prior work.

**Experiment:** E-A4b above. Additionally, report an "IG–Attention Agreement" score:
Spearman ρ between IG token rankings and CLS attention weight rankings, for all model
variants. This directly measures whether supervised attention aligns with causal
attributions.

---

### W2 — No ablation separating target construction from supervision design

**Weakness:** The paper compares "softmax supervision" vs. "sparsemax supervision"
but conflates three separate choices: (1) how to build ground-truth targets, (2) which
loss function to use, (3) which heads to supervise. It is impossible to know which
factor drives the comprehensiveness improvement.

**Fix:** Full 2×2×2 ablation table:

| Target | Heads | Loss | Label |
|--------|-------|------|-------|
| Softmax | All-12 final | Cross-entropy | Baseline (Mathew et al.) |
| Softmax | All-12 final | Sparsemax loss | Tests loss function |
| Sparsemax | All-12 final | Sparsemax loss | Tests target construction |
| Sparsemax | Selected | Sparsemax loss | Full method |

Run each with 5 seeds, report all five metrics (F1, compr., suff., prec., recall).

---

### W3 — Only 3 training runs — insufficient statistical power for small effects

**Weakness:** See A5. The paper's own numbers show |d| < 0.18 for most metrics.
With 3 runs, this is undetectable.

**Fix:** E-A5 above. 10 seeds minimum. If compute is limited, prioritise the full
method vs. softmax baseline (the key comparison) with 10 seeds each.

---

### W4 — No analysis of annotator disagreement

**Weakness:** HateXplain posts where annotators disagree on the rationale provide a
noisy supervision signal. The paper averages over all posts without distinguishing
high-agreement from low-agreement instances.

**Experiment (E-W4):**
- Compute Fleiss' κ for each post's rationale annotations.
- Stratify test set into high (κ > 0.6), medium (0.3 ≤ κ ≤ 0.6), and low (κ < 0.3).
- Report all metrics separately per stratum for all model variants.
- Hypothesis: sparsemax supervision provides larger improvements on high-agreement
  posts (cleaner signal) and may degrade on low-agreement posts.

---

### W5 — No cross-lingual or cross-domain evaluation

**Weakness:** All results are on a single English dataset. It is unknown whether the
inductive bias introduced by sparse supervision generalises.

**Experiment (E-W5a) — Zero-shot cross-lingual transfer:**
- Fine-tune on HateXplain (English), evaluate on HateBRXplain (Portuguese) zero-shot.
- Compare all four model variants.
- Hypothesis: sparsemax-selected-head model transfers better because it has learned
  to concentrate on semantically evidential tokens rather than language-specific
  syntactic patterns.

**Experiment (E-W5b) — Cross-domain (Twitter → Gab):**
- HateXplain contains both Twitter and Gab posts. Train on Twitter subset, evaluate
  on Gab subset and vice versa.

---

### W6 — The functional invariance of F1 is observed but not explained

**Weakness:** The paper notes that F1 is stable under sparsemax supervision and treats
it as expected. But this is not obvious: forcing exact zeros in CLS attention removes
information pathways that the model previously used.

**Fix:** Proposition 1 in the rewritten paper (value subspace span condition).

**Experiment (E-W6):** E-A3a + E-A3b above. Additionally:
- Visualise the CLS representation trajectory during training (PCA of CLS embeddings)
  for softmax vs. sparsemax model.
- If trajectories diverge significantly, the representations are different even if
  the final decision boundary is not.

---

### W7 — Supervising all heads may harm specialised syntactic heads

**Weakness:** See A2. The paper does not test whether uniform head supervision
actively degrades the representations of specialised heads.

**Experiment (E-W7):**
- Probe all 12 heads of the final layer (and selected intermediate layers) for
  syntactic tasks (POS tagging, dependency parsing) using a lightweight linear probe
  [Tenney et al., 2019] before and after supervision.
- Report probe accuracy drop per head for softmax-supervised vs. sparsemax-selected.
- Hypothesis: syntactic probe accuracy drops more for all-head supervision than for
  selected-head supervision.

---

### W8 — No comparison with Integrated Gradients as a rationale extractor

**Weakness:** The paper only considers attention weights as the model's explanation.
IG is a principled alternative that may outperform attention as a rationale extractor
even without any supervision.

**Experiment (E-W8):**
- For all model variants, extract rationales using: (a) CLS attention weights,
  (b) IG attributions.
- Evaluate plausibility (IoU-F1 vs. human rationales) for both.
- This answers: "Does supervision help attention match human rationales better than
  IG does natively?"
- If IG without supervision already outperforms supervised attention on plausibility,
  the entire supervision pipeline's value proposition shifts to faithfulness only.

---

## 3. Experiment Priority Matrix

| ID | Assumption/Weakness | Priority | Compute Cost | Expected Impact |
|----|---------------------|----------|--------------|-----------------|
| E-A1 | Sparsity of rationales | HIGH | Low (analysis only) | Validates motivation |
| E-A4b | LIME vs. IG agreement | HIGH | Medium | May invalidate prior results |
| E-A2a | Head importance scoring | HIGH | Medium | Core contribution |
| E-A3b | Adversarial attention swap | HIGH | Low | Validates boundary claim |
| E-A5 | 10-seed runs | HIGH | High | Required for significance |
| E-A6 | Loss function ablation | MEDIUM | High | Isolates contributions |
| E-W4 | Annotator disagreement | MEDIUM | Low (analysis) | Novel insight |
| E-W5a | Cross-lingual transfer | MEDIUM | Medium | Generalisability |
| E-W7 | Syntactic probe | MEDIUM | Medium | Theoretical validation |
| E-W8 | IG as rationale extractor | MEDIUM | Medium | Evaluation depth |
| E-A3a | Subspace analysis | LOW | Medium | Theoretical depth |
| E-W5b | Cross-domain | LOW | Medium | Bonus result |

---

## 4. Minimum Viable Experiment Set for NeurIPS Submission

If compute is limited, the following subset is the minimum for a credible submission:

1. **E-A1** — Verify rationale sparsity in HateXplain (1 day, no GPU).
2. **E-A4b** — LIME vs. IG agreement + replace LIME with IG in all evaluations (2 days).
3. **E-A2a** — Head importance scoring + train 4 head-selection variants × 5 seeds (3 days GPU).
4. **E-A3b** — Adversarial attention swap test on existing checkpoints (0.5 days).
5. **E-A5** — Re-run main comparison (sparsemax-selected vs. softmax baseline) × 10 seeds.
6. **E-W4** — Annotator disagreement stratification (1 day, no GPU, uses existing checkpoints).
7. **E-W8** — IG vs. attention as rationale extractor (1 day, uses existing checkpoints).

Total estimated GPU time: ~4–6 days on a single A100.

---

## 5. Repo Structure (Recommended for Claude Code)

```
repo/
├── RESEARCH_PLAN.md               ← this file
├── README.md
├── configs/
│   ├── base.yaml                  # model, data, training defaults
│   ├── ablations/
│   │   ├── softmax_all_heads.yaml
│   │   ├── sparsemax_all_heads.yaml
│   │   ├── sparsemax_top6_heads.yaml
│   │   └── sparsemax_selected_heads.yaml
│   └── loss_ablation/
│       ├── sparsemax_target_kl_loss.yaml
│       └── sparsemax_target_l2_loss.yaml
├── src/
│   ├── model.py                   # BERT + sparsemax attention module
│   ├── sparsemax.py               # sparsemax transformation (Martins 2016)
│   ├── losses.py                  # sparsemax_loss, cross_entropy_attn, kl_attn
│   ├── ground_truth.py            # sparse + dense rationale construction
│   ├── head_selection.py          # gradient importance scoring
│   ├── evaluation/
│   │   ├── faithfulness.py        # comprehensiveness + sufficiency (IG and LIME)
│   │   ├── plausibility.py        # IoU-F1, token precision/recall
│   │   ├── ig_attention_agreement.py  # Spearman ρ between IG and attention
│   │   └── adversarial_swap.py    # Jain & Wallace attention swap test
│   └── probing/
│       └── syntactic_probe.py     # linear probe for POS/dependency on heads
├── experiments/
│   ├── run_ablation.sh
│   ├── run_cross_lingual.sh
│   └── run_disagreement_analysis.sh
├── notebooks/
│   ├── 01_rationale_sparsity_analysis.ipynb   # E-A1
│   ├── 02_lime_vs_ig_agreement.ipynb           # E-A4b
│   ├── 03_head_importance_scores.ipynb         # E-A2a
│   ├── 04_subspace_analysis.ipynb              # E-A3a
│   └── 05_annotator_disagreement.ipynb         # E-W4
└── results/
    ├── tables/
    └── figures/
```

---

## 6. Key References

- Mathew et al. (2021). HateXplain. AAAI.
- Martins & Astudillo (2016). Sparsemax. ICML.
- Clark et al. (2019). What does BERT look at? ACL BlackboxNLP.
- Voita et al. (2019). Analysing multi-head self-attention. ACL.
- Jain & Wallace (2019). Attention is not explanation. NAACL.
- Wiegreffe & Pinter (2019). Attention is not not explanation. EMNLP.
- Sundararajan et al. (2017). Integrated Gradients. ICML.
- DeYoung et al. (2020). ERASER. ACL.
- Michel et al. (2019). Are sixteen heads really better than one? NeurIPS.
- Davani et al. (2024). Annotator disagreements shaped by moral values. ACL.
- SRA — Supervised Rational Attention (arXiv 2511.07065, Nov 2025).
- SMRA — Supervised Moral Rationale Attention (arXiv 2601.03481, Jan 2026).

---

*Last updated: March 2026. Feed this file to Claude Code with the instruction:
"Read RESEARCH_PLAN.md and scaffold the repo structure described in Section 5,
with placeholder implementations for each module in src/."*

