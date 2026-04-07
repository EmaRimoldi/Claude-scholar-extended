# Experiment Plan — Sparse Rationale-Constrained Attention for Hate Speech Detection

**Date:** 2026-04-07
**Pipeline Step:** 9 (`/design-experiments`)
**Gate:** N2 input (design novelty check follows)
**Target venue:** NeurIPS 2026

---

## 1. Research Questions

| ID | Question | Hypothesis | Priority |
|----|----------|-----------|---------|
| RQ1 | Does sparsemax-supervised attention achieve higher ERASER comprehensiveness than SRA without accuracy cost? | H1 | MUST |
| RQ2 | Are HateXplain rationale annotations structurally sparse (density < 30%)? | H2 | MUST |
| RQ3 | Does the adversarial attention swap produce larger output perturbation on sparsemax vs. softmax models? | H4 | MUST |
| RQ4 | Does head-selective supervision outperform all-head supervision? | H3 | SHOULD |
| RQ5 | Does sparsemax supervision reduce identity-term false positive rate? | H5 | SHOULD |
| RQ6 | Do results transfer cross-lingually to HateBRXplain? | W5a | SHOULD (venue fit) |

---

## 2. Models and Conditions

### 2.1 Condition Matrix

| Condition ID | Model | Attention | Supervision Loss | Notes |
|-------------|-------|-----------|-----------------|-------|
| C0 | BERT-base-uncased | softmax (frozen pre-trained) | None | Unsupervised baseline |
| C1 | BERT-base-uncased | softmax | None (fine-tune CE only) | Fine-tuned baseline |
| C2 | BERT-base-uncased | softmax (final layer) | KL(softmax ∥ rationale_target) | SRA replication (`eilertsen2025aligning`) |
| C3 | BERT-base-uncased | sparsemax (final layer, all 12 heads) | MSE(sparsemax ∥ rationale_target) | **Ours — primary** |
| C4 | BERT-base-uncased | sparsemax (final layer, top-6 heads only) | MSE(sparsemax ∥ rationale_target) | **Ours — head-selective (H3)** |

**Primary comparison:** C3 vs. C2 (tests H1).
**Head-selection ablation:** C4 vs. C3 (tests H3).
**Unsupervised sparsemax check:** C3 without alignment loss (confirms that comprehensiveness improvement requires supervision, not just sparsemax per se — important for novelty claim).

Add: C3-unsup (sparsemax, no supervision loss) — additional ablation to separate sparsity effect from supervision effect.

Updated condition matrix:

| Condition ID | Attention | Supervision | Purpose |
|-------------|-----------|------------|---------|
| C1 | softmax | None | Unsupervised baseline |
| C2 | softmax | KL (SRA-style) | Primary competitor |
| C3 | sparsemax | None | Disentangle sparsity from supervision |
| C4 | sparsemax | MSE (all 12 heads) | **Primary contribution** |
| C5 | sparsemax | MSE (top-6 heads, H3) | Head-selective variant |

Total conditions: 5. Primary contrast: C4 vs. C2.

### 2.2 Architecture Details

**Backbone:** `bert-base-uncased` (HuggingFace transformers ≥ 4.46)

**Sparsemax implementation:** Replace `torch.nn.functional.softmax` with `sparsemax` operator in `BertSelfAttention.forward()` — final encoder layer only (layer 11, 0-indexed). All earlier layers retain softmax.

Sparsemax forward (differentiable, from `martins2016sparsemax`):
```
sparsemax(z) = argmin_{p ∈ Δ} ||p - z||²
             = [z - τ(z)]₊   where τ(z) is the threshold
```

**Rationale target construction:**
1. Load HateXplain majority-vote rationale annotations (3 annotators → majority)
2. For each post, binary mask r ∈ {0,1}^T where r_t = 1 if majority of annotators highlighted token t
3. Normalize: r̃ = r / ||r||₁ (gives valid simplex target where rationale tokens share mass equally)
4. For non-rationale tokens: r̃_t = 0 (exact zero — compatible with sparsemax range)

**CLS attention supervision:** Apply alignment loss on the [CLS] attention weights w ∈ Δ^T from the final-layer multi-head attention (averaged across heads for C4; top-6 heads only for C5).

**Head selection for C5 (H3):** Rank final-layer heads by gradient importance (expected gradient magnitude: E[||∂L/∂w_h||] over training set) in the first epoch; select top-6 for supervision in subsequent epochs. Heads 7-12 (bottom half by importance) retain softmax.

### 2.3 Loss Function

```
L_total = L_CE + α × L_align

L_CE = CrossEntropy(logits, labels)    [3-class: hate / offensive / normal]

For C2 (SRA replication):
  L_align = KL(softmax(z) ∥ r̃)         [r̃ is softmax-compatible rationale target]

For C4/C5 (ours):
  L_align = MSE(sparsemax(z), r̃)        [L2 distance between sparsemax output and normalized rationale mask]
          = (1/T) Σ_t (sparsemax_t(z) - r̃_t)²
```

**Rationale for MSE over sparsemax-loss:** The `sparsemax loss` (Martins 2016) computes negative sparsemax log-likelihood, which requires the target to be a one-hot label. For soft rationale targets (normalized mask), MSE is the natural alignment objective for sparse distributions. MSE is also directly comparable to the KL used in SRA — both measure distributional distance from the rationale target, but MSE is well-defined when target has exact zeros (KL diverges when support of target is smaller than support of softmax).

**Alignment weight α:** Grid search over {0.1, 0.3, 0.5, 1.0}; select on validation comprehensiveness while keeping F1 ≥ 0.8. Report results for optimal α per method.

---

## 3. Training Protocol

### 3.1 Dataset Splits (HateXplain)

- **Source:** `hate_speech_and_offensive_language` → HateXplain dataset from mathew2021hatexplain
- **Pre-defined splits** (use official train/val/test to ensure comparability with SRA):
  - Train: ~15,000 posts
  - Val: ~2,500 posts
  - Test: ~2,500 posts
- **Labels:** hate / offensive / normal (3-class)
- **Rationale annotations:** Available for train and val; test rationales held out for evaluation

### 3.2 Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Backbone | bert-base-uncased | 110M params |
| Max sequence length | 128 | Sufficient for HateXplain avg ~23 tokens |
| Batch size | 32 | Per GPU |
| Learning rate | 2e-5 | AdamW; consistent with SRA |
| LR schedule | Linear warmup (10%) + linear decay | |
| Epochs | 5 | Early stop on val macro-F1 |
| Optimizer | AdamW, weight_decay=0.01 | |
| Seeds | 5 per condition: {42, 43, 44, 45, 46} | Per compute-budget.md |
| GPU | 1× NVIDIA A100/V100 per run | Per compute-budget.md |
| SLURM | Job array (0-4) per condition | 5 conditions × 5 seeds = 25 jobs |

### 3.3 Evaluation Protocol

**Primary metrics (H1):**
- ERASER comprehensiveness AOPC (area-over-perturbation-curve): delete top-k% tokens by descending attention weight; measure prediction change. k ∈ {0.1, 0.2, 0.3, 0.5, 0.8}. Higher = more faithful.
- ERASER sufficiency AOPC: retain only top-k% tokens; measure prediction preservation. Higher = more sufficient.
- Macro-F1 on 3-class HateXplain test set.
- Token F1 / IoU F1 against human rationale annotations (plausibility).

**Statistical tests (H1):**
- Bootstrap 95% CI (10,000 resamples) for all metrics across 5 seeds.
- TOST equivalence test for macro-F1 (Δ ≤ 1.0 F1 points, margin ±1.0; α=0.05).
- Paired t-test (or Wilcoxon if non-normal) comparing C4 vs. C2 comprehensiveness across 5 seeds.

**Adversarial swap test (H4):**
- For each trained C2 (SRA) and C4 (ours) checkpoint:
  1. Forward pass → get original prediction distribution P_orig
  2. Replace CLS attention weights with uniform (1/T for all T tokens)
  3. Forward pass with same encoder hidden states → get P_swap
  4. Compute KL(P_swap ∥ P_orig) for each test example
- Aggregate: mean KL per model; test ratio KL(C4_swap) / KL(C2_swap) ≥ 2.0
- Statistical test: Wilcoxon signed-rank p < 0.01 on per-example KL values

**Head analysis (H3):**
- Compare C4 (all-12) vs. C5 (top-6) on comprehensiveness AOPC and macro-F1
- POS-tagging linear probe: train linear classifier on frozen BERT representations; measure POS accuracy on PTB WSJ test; compare between C4 and C5 (controls that head-selective preserves syntactic structure)

**Fairness evaluation (H5):**
- Define identity-term subgroup: posts in HateXplain test set classified as *normal* but containing ≥1 identity term from list (race, religion, gender, sexuality — per HateXplain target community annotations)
- FPR metric: fraction of normal/non-hate posts with identity terms misclassified as hate or offensive
- Compare FPR across C1, C2, C4

### 3.4 H2 — Data Analysis (No GPU Required)

- Load HateXplain train+val rationale annotations
- Compute per-post majority-vote coverage = |{t : majority(r_1,r_2,r_3) = 1}| / total_tokens
- Report: median, mean, histogram, mode interval
- Expected: median ≈ 0.23 (from mathew2021hatexplain report of avg 5.47/23.42 tokens)

---

## 4. Ablation Matrix

| Ablation | Purpose | Conditions Compared |
|----------|---------|-------------------|
| No-supervision sparsemax | Separate sparsity effect from supervision effect | C3 vs. C4 on comprehensiveness |
| All-head vs. top-6-head | H3: head selection | C4 vs. C5 |
| α sweep | Alignment weight sensitivity | C4 with α ∈ {0.1, 0.3, 0.5, 1.0} |
| Final layer only vs. all layers | Robustness of final-layer-only choice | C4 (layer 11) vs. C4-all-layers |

**Priority:** All-head vs. top-6 (H3) and no-supervision-sparsemax are essential for paper; α sweep and all-layers are supplementary.

---

## 5. Extension Experiments (Venue Fit)

### W5a — Cross-Lingual: HateBRXplain

- **Purpose:** Second dataset for NeurIPS venue fit (addresses venue warning from N1)
- **Protocol:** Same conditions (C1, C2, C4) on HateBRXplain (Portuguese HSD dataset with rationale annotations; from `vargas2026smra`)
- **Seeds:** 3 (not full 5; W5a is a secondary claim)
- **Metrics:** Same ERASER protocol

**Note:** HateBRXplain may require a multilingual backbone (`bert-base-multilingual-cased` or `xlm-roberta-base`). Use xlm-roberta-base for cross-lingual conditions; re-run HateXplain baseline with xlm-roberta as well for fair comparison.

### W5b — Cross-Domain: Davidson 2017

- **Purpose:** Generalization test (primary training on HateXplain, zero-shot eval on Davidson)
- **Protocol:** Train on HateXplain (C1, C2, C4), evaluate directly on Davidson 2017 test set (2-class: hate+offensive vs. normal)
- **Seeds:** 3

---

## 6. Formal Contribution: Proposition 1

**Required (per N1 novelty assessment routing instructions).**

> **Proposition 1 (Structural Zero Faithfulness Guarantee):** Let f be a BERT-based classifier with sparsemax attention in the final encoder layer. Let w = sparsemax(z) ∈ Δ^T be the CLS attention weights over tokens t_1, ..., t_T. Let S = {t : w_t > 0} be the attention support set. For any token t_i ∉ S (i.e., w_{t_i} = 0), removing t_i from the input sequence and recomputing the forward pass yields an identical CLS representation, and therefore an identical prediction distribution.
>
> *Proof sketch:* The CLS representation is computed as h_CLS = Σ_t w_t × V_t where V_t is the value projection of token t. For t_i with w_{t_i} = 0: the contribution of t_i to h_CLS is exactly 0 × V_{t_i} = 0. Therefore h_CLS is unchanged by removing t_i. Since the classification head is a deterministic function of h_CLS, the output distribution is unchanged. ∎
>
> *Consequence:* The ERASER comprehensiveness score for the token set {t : t ∉ S} is exactly 0 by construction — these tokens cannot change the prediction when deleted. This provides an analytically maximal comprehensiveness bound that softmax-supervised models (where w_t > 0 for all t) cannot achieve.

This proposition must appear in Section 3 (Method) of the manuscript. The proof sketch formalizes the structural-zero argument used throughout the paper.

---

## 7. Power Analysis

**Primary claim (H1):** Expected effect size = Cohen's d ≈ 0.5 (medium) from mini-project pilot.
- Power (1-β) = 0.80, α = 0.05, two-sided t-test: required n ≈ 26 runs per condition
- With 5 seeds: n = 5 per condition — this provides power ≈ 0.38 for the primary claim
- **Mitigation:** Bootstrap CI (10K resamples) across 5 seeds provides well-calibrated uncertainty estimates even at n=5. Report effect size + 95% CI rather than relying on p-value alone. This is standard practice for 5-seed NLP experiments at NeurIPS/ACL.

**Adversarial swap (H4):** Each model produces T-length per-example KL values on ~2,500 test posts; n ≈ 12,500 paired observations per model (5 seeds × 2,500 posts). Power for H4 Wilcoxon test is not a concern.

---

## 8. Compute Plan

| Condition | Seeds | GPUs | Est. Time/Run | Total GPU-hours |
|-----------|-------|------|--------------|----------------|
| C1 (BERT-base FT) | 5 | 1 | ~1.5h | 7.5h |
| C2 (SRA softmax+KL) | 5 | 1 | ~2h | 10h |
| C3 (sparsemax, no sup) | 5 | 1 | ~2h | 10h |
| C4 (sparsemax+MSE all-12) | 5 | 1 | ~2.5h | 12.5h |
| C5 (sparsemax+MSE top-6) | 5 | 1 | ~2.5h | 12.5h |
| H2 (data analysis) | 1 | 0 | ~0.25h | 0h |
| H4 (adversarial swap) | — | 0 | ~0.5h | 0h (uses saved checkpoints) |
| W5a (HateBRXplain, 3 seeds) | 3×3 | 1 | ~2h | 18h |
| Ablation: α sweep (4 vals) | 5 | 1 | ~2h | 40h |
| **TOTAL** | | | | **~110 GPU-hours** |

**SLURM:** Array jobs per condition; `#SBATCH --array=0-4` for 5-seed conditions. Single GPU per task. See compute plan for full SLURM scripts (Step 17).

---

## 9. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| H1 comprehensiveness Δ < 0.02 (fail) | LOW (pilot supports) | HIGH (paper kills) | Report negative result as characterization study; publish W5a/H4 anyway |
| sparsemax training instability | MEDIUM | MEDIUM | Use small α=0.1 initially; anneal |
| HateBRXplain not publicly available | MEDIUM | LOW (W5a is optional) | Contact Vargas et al.; use HateBRXplain v1 (language-agnostic rationales) |
| KL-divergence H4 near 2.0 boundary | MEDIUM | MEDIUM | Report ratio + 95% CI; borderline is still informative |
| SRA hyperparameter replication mismatch | MEDIUM | MEDIUM | Use SRA paper hyperparams exactly; report both if discrepancy |
| F1 drop > 1.0 (H1 equivalence fails) | LOW | HIGH | Reduce α; report α-sensitivity analysis |

---

## 10. Output Files

- `docs/experiment-plan.md` — this document
- `src/` — scaffolded in Step 11 (`/scaffold`)
- `results/` — populated in Steps 18-19
- `docs/analysis-report.md` — produced in Step 20

---

## 11. Gate N2 Readiness Checklist

Gate N2 (`/design-novelty-check`) checks that the experiment design actually tests the novelty claim. Pre-assessment:

| Check | Status |
|-------|--------|
| Primary comparison (C4 vs C2) directly tests sparsemax vs. softmax on comprehensiveness | YES |
| Novelty differentiator (operator range) is empirically testable as H1 | YES |
| H4 adversarial swap explicitly tests the structural-causality claim | YES |
| Baselines include unsupervised BERT (C1) and SRA (C2) — no cherry-picking | YES |
| C3 (sparsemax without supervision) isolates sparsity effect from supervision | YES |
| 5 seeds per condition per compute-budget.md | YES |
| Proposition 1 in manuscript confirms formal theoretical contribution | YES |
| W5a (second dataset) addresses venue fit warning | YES |
| No cyclic design (test hypotheses are pre-registered; no post-hoc selection) | YES |
