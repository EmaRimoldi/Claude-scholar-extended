# Experiment Plan
# Sparse Rationale-Constrained Attention for Hate Speech Detection

**Date:** 2026-04-01
**Pipeline step:** design-experiments (Step 9)
**Target venue:** NeurIPS 2026
**Seeds/condition:** 3 (experimental phase; upgrade to 5 before camera-ready)
**GPUs/job:** 1 (A100 or equivalent)

---

## 0. Overview

This plan operationalizes hypotheses H1–H6 (from `docs/hypotheses.md`) and experiments E-A1 through E-W8 (from `RESEARCH_PROPOSAL.md`) into a structured, executable matrix. The plan is organized into 5 execution phases, with explicit stop-or-go gates, full baseline justification, power analysis, and threat-to-validity documentation.

---

## 1. Experimental Conditions Matrix

### 1.1 Primary Model Conditions

| ID | Architecture | Attention | Heads Supervised | Loss | Role |
|----|-------------|-----------|-----------------|------|------|
| M0 | BERT-base-uncased | Softmax (default) | None | CE only | Mathew et al. (2021) baseline |
| M1 | BERT-base-uncased | Softmax | Fixed: layer 8, head 7 | CE + MSE | SRA (Eilertsen et al. 2025) replication |
| M2 | BERT-base-uncased | Softmax | All-12 final-layer | CE + MSE | Softmax all-heads supervision |
| M3 | BERT-base-uncased | Sparsemax (supervised heads) | All-12 final-layer | CE + MSE | Sparsemax all-heads (ablate head selection) |
| M4a | BERT-base-uncased | Sparsemax (supervised heads) | Top-3 by gradient importance | CE + MSE | Head selection k=3 |
| M4b | BERT-base-uncased | Sparsemax (supervised heads) | Top-6 by gradient importance | CE + MSE | **Primary proposed method** |
| M4c | BERT-base-uncased | Sparsemax (supervised heads) | Top-9 by gradient importance | CE + MSE | Head selection k=9 |
| M5 | BERT-base-uncased | Sparsemax (supervised heads) | Top-6 by gradient importance | CE + KL | Loss ablation: KL divergence |
| M6 | BERT-base-uncased | Sparsemax (supervised heads) | Top-6 by gradient importance | CE + sparsemax_loss | Loss ablation: natural conjugate loss |
| M7 | BERT-base-uncased | Softmax | Top-6 by gradient importance | CE + MSE | Importance selection without sparsemax |

**Primary comparison: M0 vs M4b** — this is the key claim (sparsemax + importance selection > no supervision).

**Secondary comparison: M1 vs M4b** — contribution over SRA.

**Ablation comparisons:**
- H1 (head selection): M3 vs M4a/M4b/M4c vs M2
- H2 (sparsemax vs softmax): M2 vs M3 (holding heads = all-12 and loss = MSE)
- H3 (loss function): M4b vs M5 vs M6 (holding heads = top-6, activation = sparsemax)
- Interaction: M7 vs M4b (importance selection without vs with sparsemax)

### 1.2 Head Importance Pre-Experiment (E-A2a)

Before training M4a/M4b/M4c/M5/M6/M7, run a gradient importance scoring pass:

```
I(h, ℓ) = E_x [ |∂L_CE / ∂A^{CLS,h,ℓ}| ]
```

- Use M0 fine-tuned on HateXplain training set (seed 0 checkpoint)
- Compute importance over full training set
- Store head rankings as JSON: `results/head_importance_scores.json`
- Select top-k based on this ranking for M4a (k=3), M4b (k=6), M4c (k=9)

**This is a one-time computation, not per-seed.** Head ranking is a dataset-level property, not training-run dependent. (Sensitivity: run on 3 checkpoints to verify stability of ranking; report Spearman ρ across checkpoints in supplementary.)

---

## 2. Dataset and Split Strategy

### 2.1 Primary Dataset: HateXplain (English)

| Split | Size | Source |
|-------|------|--------|
| Train | 15,383 posts | `datasets.load_dataset("hatexplain")["train"]` |
| Validation | 1,985 posts | `["validation"]` |
| Test | 2,780 posts | `["test"]` |

**Rationale target construction:**
- For each post in hate/offensive class: compute majority-vote binary rationale mask (token receives 1 if ≥ 2/3 annotators flagged it)
- For normal class posts: rationale mask = all zeros (no rationale expected)
- No smoothing — binary 0/1 targets

**Pre-experiment verification (E-A1):**
- Compute token coverage statistics (fraction of tokens with majority rationale) over hate/offensive training posts
- Expected: median coverage < 30% (motivates sparsemax target)
- Report as Table 1 in manuscript

### 2.2 Data Pipeline

```
HateXplain JSON → tokenize (BERT WordPiece) → align rationale masks to WordPiece tokens
  → handle [CLS]/[SEP] (mask = 0) → batch with attention_mask
```

All preprocessing deterministic (no randomness, no augmentation).

---

## 3. Sample Size and Statistical Analysis

### 3.1 Seeds Per Condition

**Experimental phase:** 3 seeds for all conditions. Before camera-ready, increase to 5 (ablations) with a final compute budget check.

| Comparison | Seeds (experimental) | Seeds (camera-ready) |
|------------|---------------------|----------------------|
| M0 vs M4b (primary) | 3 | 5 |
| M1 vs M4b (SRA vs proposed) | 3 | 5 |
| All other conditions | 3 | 5 |

**Power analysis (for reference):**
- HateXplain training is fast (~1.5h/epoch on A100); variance across seeds is 1–2% F1, ~0.02 IoU-F1
- For d=0.3 (small effect): n=10 required for 80% power; n=5 gives ~45% power
- For d=0.5 (medium effect): n=5 required for 70% power; n=3 gives ~40% power
- For d=0.8 (large effect): n=3 sufficient for 80% power
- **Decision (experimental phase):** 3 seeds is sufficient to validate the experimental setup and check directional trends. Statistical conclusions require at minimum n=5 before submission.

### 3.2 Statistical Tests

| Test | Applied To |
|------|-----------|
| Paired bootstrap (B=1000) | All pairwise comparisons on test set |
| Cohen's d | Effect size for all main comparisons |
| Bootstrap 95% CI | All reported metrics (not normal-approximation CIs) |
| Wilcoxon signed-rank | Non-parametric alternative for robustness check on primary comparison |
| Fleiss' κ per post (H6) | Annotator agreement computation for test set stratification |
| Kendall's τ (H4 LIME stability) | Cross-run ranking agreement |
| Spearman ρ (H4 IG vs LIME) | Attribution method correlation |

---

## 4. Metrics Specification

### 4.1 Primary Metrics

| Metric | Operationalizes | Evaluation |
|--------|----------------|-----------|
| IoU-F1 | Plausibility (H1, H2, H3) | IG-based (primary), LIME-based (secondary) |
| Token-F1 | Plausibility (H1, H2, H3) | IG-based (primary), LIME-based (secondary) |
| Comprehensiveness | Faithfulness (H2, H4) | IG-based (primary), LIME-based (secondary) |
| Sufficiency | Faithfulness (H2, H4) | IG-based (primary), LIME-based (secondary) |
| Macro-F1 | Classification (H5) | Standard; must be ≥ M0 (non-degradation constraint) |

### 4.2 Metric-Claim Alignment Check (Mandatory)

| Claim | Key Terms | Metric(s) | Status |
|-------|-----------|-----------|--------|
| H1: head selection improves plausibility | "plausibility" | IoU-F1, Token-F1 | ✓ covered |
| H2: sparsemax improves faithfulness | "faithfulness" | Comprehensiveness, Sufficiency | ✓ covered |
| H3: loss function trade-off | "plausibility-faithfulness trade-off" | IoU-F1, Comprehensiveness | ✓ covered |
| H4: LIME unreliability | "evaluation reliability" | Kendall's τ, Spearman ρ(LIME,IG) | ✓ covered |
| H5: SRA statistical fragility | "statistical significance" | Bootstrap CI, Cohen's d, power | ✓ covered |
| H6: annotator agreement stratification | "agreement quality" | Per-stratum IoU-F1, F1 | ✓ covered |

**All key terms have corresponding metrics. Plan is NOT blocked.**

### 4.3 IG Evaluation Implementation

```python
from captum.attr import IntegratedGradients

ig = IntegratedGradients(model.forward_for_ig)
attributions, delta = ig.attribute(
    inputs=token_embedding,
    baselines=pad_token_embedding,
    target=predicted_class,
    n_steps=50,
    return_convergence_delta=True
)
# Aggregate over embedding dimension → token-level scores
token_scores = attributions.sum(dim=-1).abs()
```

**Comprehensiveness:**
```
comprehensiveness(x, S) = f(x)[y] - f(x \ S)[y]
```
where S = tokens with highest IG scores (top-k% of tokens = rationale coverage).

**Sufficiency:**
```
sufficiency(x, S) = f(x)[y] - f(S)[y]
```

Both implemented per ERASER (DeYoung et al. 2020). Use predicted class y, not ground truth.

---

## 5. Execution Plan

### Phase 0: Data Verification (E-A1) — No GPU — Day 1

**Objective:** Verify rationale sparsity assumption, compute annotator agreement per post.

**Jobs:**
1. `python src/analysis/rationale_sparsity.py` — compute token coverage statistics
2. `python src/analysis/annotator_agreement.py` — compute Fleiss' κ per post, save `results/kappa_per_post.json`

**Outputs:**
- `results/rationale_sparsity_stats.json`: {mean_coverage, median_coverage, pct_below_30, histogram}
- `results/kappa_per_post.json`: {post_id → fleiss_kappa}

**Stop-or-go gate G0:**
- IF median_coverage > 0.50: WARN — sparsemax motivation weakened. Do NOT stop. Update manuscript framing: "even at >50% coverage, sparsemax induces useful structural alignment." Continue.
- IF median_coverage ≤ 0.30: PASS — sparsemax motivation confirmed.

---

### Phase 1: Head Importance Pre-Computation (E-A2a) — ~2h GPU — Day 1-2

**Objective:** Score all 144 BERT heads (12 heads × 12 layers) by gradient importance on HateXplain train set. Identify top-k heads for M4a/M4b/M4c conditions.

**Jobs:**
1. Train M0 (seed=0) — this checkpoint is the reference for gradient computation
2. `python src/head_selection/compute_importance.py --checkpoint results/M0/seed0/ --output results/head_importance_scores.json`
3. Verify ranking stability: compute on 3 M0 seeds, report Spearman ρ; if ρ < 0.7, use union of top-k across seeds

**Outputs:**
- `results/head_importance_scores.json`: {(layer, head) → importance_score}
- `results/head_ranking.json`: sorted list of (layer, head) pairs
- `results/top3_heads.json`, `top6_heads.json`, `top9_heads.json`

**Stop-or-go gate G1:**
- IF all importance scores are approximately uniform (variance < 0.01): WARN — gradient importance is uninformative. Add uniform-random selection as additional baseline. Do NOT stop.
- IF clear variance in importance: PASS.

---

### Phase 2: Main Ablation Training — ~80 GPU-hours — Day 2-7

**Objective:** Train all 10 model conditions × appropriate seeds.

**SLURM job structure (sequential seeds, grouped conditions):**
```bash
# Wave 1 — 2 jobs, ~9h each:
sbatch scripts/train.sh --conditions M0 M1    # GPU-A: M0 seed42,43,44 → M1 seed42,43,44
sbatch scripts/train.sh --conditions M3 M4b   # GPU-B: M3 seed42,43,44 → M4b seed42,43,44

# Wave 2 (after Gate G2 passes) — 3 jobs, ~9h each:
sbatch scripts/train.sh --conditions M2 M4a   # GPU-C
sbatch scripts/train.sh --conditions M4c M5   # GPU-D
sbatch scripts/train.sh --conditions M6 M7    # GPU-E
```

**Training configuration (all conditions):**
```yaml
model: bert-base-uncased
max_seq_len: 128
batch_size: 32
learning_rate: 2e-5
warmup_ratio: 0.1
max_epochs: 5
early_stopping_patience: 3  # on validation macro-F1
alignment_loss_weight: 0.1   # λ in: L = L_CE + λ * L_align
optimizer: AdamW
```

**Per-condition training time (A100):** ~1.5h per seed
**Total Phase 2 GPU-hours:** (8 conditions × 5 seeds + 2 conditions × 5 extra seeds) × 1.5h = 75h

**Stop-or-go gate G2 (mid-Phase 2 check):**
- After M0, M1, M3, M4b training completes (first wave):
  - Check: does M4b IoU-F1 > M1 IoU-F1 on validation set?
  - IF M4b_IoU-F1 < M1_IoU-F1 - 0.02: INVESTIGATE before running remaining conditions. Likely causes: λ tuning, head ranking. Run λ sweep (λ ∈ {0.01, 0.05, 0.1, 0.5}) on 1 seed before proceeding.
  - IF normal: PROCEED.

---

### Phase 3: IG/LIME Evaluation (E-A4a/b, E-W8) — ~6 GPU-hours — Day 7-8

**Objective:** Compute IG and LIME attributions on test set for all checkpoints. Run H4 stability tests.

**Jobs:**
1. `python src/evaluation/compute_attributions.py --method ig --checkpoints results/*/seed*/`
2. `python src/evaluation/compute_attributions.py --method lime --checkpoints results/*/seed0/`  (LIME on seed0 only — high variance)
3. `python src/evaluation/lime_stability.py --n_runs 10 --n_posts 50` — H4a LIME stability test
4. `python src/evaluation/lime_ig_agreement.py` — H4b LIME-IG correlation

**Outputs:**
- `results/attributions/ig_{model_id}_{seed}.pt`
- `results/attributions/lime_{model_id}_seed0.pt`
- `results/h4a_lime_stability.json`: {mean_kendall_tau, std, verdict}
- `results/h4b_lime_ig_agreement.json`: {spearman_rho, verdict}
- `results/faithfulness_metrics_ig.csv`: comprehensiveness + sufficiency under IG for all models
- `results/faithfulness_metrics_lime.csv`: same under LIME (for comparability with SRA)

---

### Phase 4: Metric Computation and Statistical Analysis — Day 8-9

**Objective:** Compute all metrics, bootstrap CIs, effect sizes, annotator agreement stratification.

**Jobs:**
1. `python src/evaluation/compute_plausibility.py` — IoU-F1, Token-F1 for all models
2. `python src/evaluation/compute_faithfulness.py` — comprehensiveness, sufficiency (IG + LIME)
3. `python src/evaluation/bootstrap_tests.py` — all pairwise bootstrap comparisons
4. `python src/evaluation/effect_sizes.py` — Cohen's d for all key comparisons
5. `python src/evaluation/agreement_stratification.py` — H6: per-stratum metrics using kappa_per_post.json
6. `python src/evaluation/power_analysis.py` — post-hoc power per metric

**Statistical test plan:**

For each pairwise comparison (A vs B):
```python
from scipy.stats import bootstrap, wilcoxon

# Primary: paired bootstrap
result = bootstrap(
    (metric_A - metric_B,),
    statistic=np.mean,
    n_resamples=1000,
    confidence_level=0.95
)

# Effect size
d = (mean_A - mean_B) / pooled_std(A, B)

# Non-parametric check
wilcoxon_stat, p = wilcoxon(metric_A, metric_B)
```

---

### Phase 5: Adversarial Validation and Diagnostics (E-A3b, E-W7 optional) — Day 9-10

**Objective:** Validate causal claims about attention supervision.

**E-A3b — Adversarial attention swap (Jain & Wallace 2019):**
```python
# For M4b: replace supervised head attention weights with uniform distribution
# Run inference; measure KL(output_original || output_swapped)
for post in test_set:
    with model.swap_attention(heads=top6_heads, to=uniform_dist):
        logits_swapped = model(post)
    kl = kl_divergence(logits_original, logits_swapped)
```
- Expected: if KL is large, attention supervision genuinely constrains model computation (supports H2 causal claim)
- If KL is small: attention is not causal; faithfulness gain is not from attention supervision mechanism

**E-A1 IG-Attention Agreement (E-W8):**
```python
# For each model, compute Spearman ρ between:
# (a) CLS attention weights of supervised heads
# (b) IG attribution scores for same tokens
ig_attention_agreement = spearmanr(attn_weights, ig_scores)
```

---

## 6. Threat-to-Validity Analysis

### H1: Gradient Importance Head Selection

**Falsification test:** If IoU-F1(M4a/M4b/M4c) ≤ IoU-F1(M3) with overlapping CIs, H1 is falsified — head selection does not help.

**Confound:** The top-k heads may already be the ones that learned the most task-relevant features during pre-training, making the "selection" merely a proxy for pre-training specialization rather than rationale alignment capacity. *Counter:* We test multiple k values; if selection helps only at specific k, the confound explanation requires fine-tuned k to coincide with the "right" heads, which is non-parsimonious.

**Adversarial validation:** E-W7 (syntactic probe) tests whether importance-selected heads preserve specialized syntactic functions better than all-head supervision. If they do, it supports the mechanism: gradient importance selects semantic heads, preserving syntactic heads.

---

### H2: Sparsemax Improves Faithfulness

**Falsification test:** If comprehensiveness(M3) ≤ comprehensiveness(M2) with bootstrap CIs not overlapping at p < 0.05, H2 is falsified — sparsemax activation does not improve faithfulness over softmax under identical supervision.

**Confound:** The IG faithfulness evaluation may itself be correlated with sparsemax distributions (since IG gradients backpropagate through the sparsemax operator, which has different properties than softmax). If so, IG scores would mechanically favor sparsemax-trained models even if behavioral faithfulness is identical.

*Counter:* We also report LIME-based faithfulness (which does not backpropagate through the model), and the adversarial swap test (E-A3b) which tests behavioral sensitivity to attention weights directly.

**Adversarial validation:** E-A3b. If KL is large for M4b but small for M2, the causal path (attention weights → prediction) is stronger in the sparsemax model, supporting H2.

---

### H3: Loss Function Trade-off

**Falsification test:** If 95% bootstrap CIs for all three losses (MSE, KL, sparsemax_loss) overlap on both comprehensiveness and IoU-F1, H3 is falsified — loss function choice does not matter.

**Confound:** Learning rate sensitivity differs by loss function (sparsemax_loss has larger gradients than MSE due to different Lipschitz constants). If not properly tuned, the comparison is unfair.

*Counter:* We use the same learning rate schedule for all (AdamW 2e-5) and apply gradient clipping (max_norm=1.0). If results differ only in instability, we will report this explicitly.

**Adversarial validation:** Run each loss variant with λ ∈ {0.05, 0.1, 0.5} on seed 0; select λ independently per loss to maximize validation IoU-F1. Report both best-λ and fixed-λ results.

---

### H4: LIME Unreliability

**Falsification test:** If Kendall's τ ≥ 0.8 across 10 LIME runs on 50 posts, H4a is falsified. If Spearman ρ(LIME, IG) ≥ 0.5 on the full test set, H4b is falsified.

**Confound:** LIME instability may be masked at the post level but real at the token level. We compute Kendall's τ on the full token ranking, not just the top-k.

**Adversarial validation:** Even if LIME is reliable (H4 falsified), we report IG-based metrics as primary because of theoretical axiom satisfaction (Sensitivity + Implementation Invariance), which LIME does not satisfy by construction.

---

### H5: SRA Statistical Fragility

**Falsification test:** If bootstrap 95% CI for IoU-F1 improvement (M1 vs M0) with 10 seeds does NOT include 0, H5 is falsified — SRA gains are statistically robust.

**Confound:** Our M1 replication may differ from the original SRA due to different hyperparameters, HateXplain preprocessing, or BERT checkpoint version.

*Counter:* We document every deviation from the original SRA configuration explicitly. The falsification test is valid regardless: if SRA gains are real, they will replicate. The comparison is between our M1 (SRA replication) and M0 (baseline), not our results vs. their reported numbers.

**Adversarial validation:** Post-hoc power analysis. If the original SRA n=3 had power < 50% for the reported effects, we report this directly as evidence of underpowering regardless of whether our replication succeeds.

---

### H6: Annotator Agreement Stratification

**Falsification test:** If 95% CI for (IoU-F1_high_κ - IoU-F1_low_κ) includes 0 across model variants, H6 is falsified — supervision quality does not depend on annotator agreement.

**Confound:** High-agreement posts may be easier (more stereotypical hate speech), making gains attributable to content difficulty rather than supervision quality.

*Counter:* We report classification macro-F1 stratified by agreement as well. If F1 is also higher for high-agreement posts, the confound is active. We then isolate the supervision quality effect by comparing within difficulty level.

**Adversarial validation:** Compare IoU-F1 gain (M4b - M0) stratified by κ. If gain is larger for high-κ posts, supervision quality drives the improvement — which is the claim.

---

## 7. Baseline Completeness Checklist

- [x] **Each method has at least one alternative:** M4b can be explained by (a) importance selection alone (M7), (b) sparsemax alone (M3), (c) loss function (M5/M6). All alternatives tested.
- [x] **Attention as explanation → gradient-based baseline:** IG computed for all models (E-W8). Spearman ρ(IG, attention) reported.
- [x] **Claiming faithfulness → adversarial test:** E-A3b (attention swap) validates causal claim.
- [x] **Claiming improvement → ablation isolating each component:** M2 (softmax, all heads) vs M3 (sparsemax, all heads) vs M7 (softmax, selected) vs M4b (sparsemax, selected) — all components tested independently.
- [ ] **Multi-dataset:** Single dataset (HateXplain English). **Justification:** HateXplain is the established benchmark for this specific problem (rationale-supervised hate speech detection); SMRA/SRA baseline numbers are available for direct comparison; cross-lingual extension (E-W5a) is listed as a secondary experiment if compute allows. **Documented limitation for manuscript.**

---

## 8. Resource Estimation

| Phase | GPU-hours | Wall time | Jobs | Priority |
|-------|-----------|----------|------|---------|
| Phase 0: Data analysis | 0 | ~5 min | 1 (CPU) | Required |
| Phase 1: Head importance | 2h | 2h | 1 GPU | Required |
| Phase 2: Wave 1 (M0, M1, M3, M4b × 3 seeds) | 18h | 9h | 2 GPU | Required |
| Phase 2: Wave 2 (M2, M4a, M4c, M5, M6, M7 × 3 seeds) | 27h | 9h | 3 GPU | Required |
| Phase 3: IG/LIME evaluation | 4h | 4h | 1 GPU | Required |
| Phase 4: Statistics | 2h | 2h | 1 (CPU) | Required |
| Phase 5: Adversarial validation | 2h | 2h | 1 (CPU) | Required |
| **Total** | **~55 GPU-hours** | **~9h parallel** | **7 GPU jobs** | |
| E-W7: Syntactic probing (optional) | 8h | 8h | 1 GPU | Optional |
| E-A3a: Subspace analysis (optional) | 4h | 4h | 1 GPU | Optional |
| E-W5a: Cross-lingual (optional) | 10h | 10h | 1 GPU | Optional |

**SLURM job submission:**
- 1 GPU per job (A100 32GB)
- All seeds for a condition run sequentially within one job (no per-seed arrays)
- 2 conditions grouped per job; each job runs ~9h
- Max concurrent training jobs: 5 (2 Wave-1 + 3 Wave-2, gated by G2)
- Checkpoint every epoch; auto-resume on failure

---

## 9. Execution Ordering with Stop-or-Go Gates

```
E-A1 (data analysis)
    │
    ▼ Gate G0: sparsity verified?
Phase 1: Head importance scoring
    │
    ▼ Gate G1: importance variance > 0.01?
Phase 2: Training wave 1 (M0, M1, M3, M4b) — 5 seeds
    │
    ▼ Gate G2: M4b val IoU-F1 > M1 - 0.02?
Phase 2: Training wave 2 (M2, M4a, M4c, M5, M6, M7) — 5 seeds
         + Extra seeds for M0, M4b (5 more each = 10 total)
    │
    ▼ (parallel)
Phase 3: IG/LIME evaluation
    │
    ▼ Gate G3: attribution computation converged (IG delta < 0.01)?
Phase 4: All metrics + statistical analysis
    │
    ▼ Gate G4: H4 verdict (LIME reliable/unreliable)?
Phase 5: Adversarial validation (E-A3b, E-W8)
    │
    ▼ Results complete → Step 20 (analyze-results)
```

---

## 10. Config Files to Generate (Step 11: /scaffold)

```
configs/experiment/
├── M0_softmax_baseline.yaml
├── M1_sra_replication.yaml
├── M2_softmax_allheads.yaml
├── M3_sparsemax_allheads.yaml
├── M4a_sparsemax_top3.yaml
├── M4b_sparsemax_top6.yaml       ← primary proposed method
├── M4c_sparsemax_top9.yaml
├── M5_sparsemax_top6_kl.yaml
├── M6_sparsemax_top6_sparsemax_loss.yaml
└── M7_softmax_top6.yaml
```

All configs share base: `configs/config.yaml` with overrides per experiment.

---

## 11. Expected Results Summary (Falsifiable Predictions)

| Hypothesis | Predicted direction | Metric | Falsified if |
|-----------|--------------------|---------|----|
| H1 | M4b > M3 ≥ M2 on IoU-F1 | IoU-F1, Token-F1 | M3 ≥ M4b with non-overlapping CI |
| H2 | M3 > M2 on comprehensiveness | Comprehensiveness | M3 ≤ M2 with non-overlapping CI |
| H3 | sparsemax_loss → highest compr; MSE → highest IoU-F1 | Both | All CIs overlap across M4b, M5, M6 |
| H4a | Kendall's τ < 0.8 for LIME | Kendall's τ | τ ≥ 0.8 |
| H4b | Spearman ρ(LIME, IG) < 0.5 | Spearman ρ | ρ ≥ 0.5 |
| H5 | IoU-F1 CI for M1 vs M0 excludes 0; F1 CI includes 0 | Bootstrap CI | Both CIs exclude 0, or IoU-F1 CI includes 0 |
| H6 | IoU-F1 gain larger for high-κ posts | Per-stratum IoU-F1 | No gradient across κ strata |

---

## 12. Minimum Viable Results for NeurIPS Submission

Required for submission:
1. H2 confirmed (comprehensiveness(M3) > comprehensiveness(M2), p < 0.05 bootstrap)
2. M4b ≥ SRA (M1) on IoU-F1 AND comprehensiveness (combined improvement)
3. H4 result (LIME stability and IG-LIME agreement, regardless of direction)
4. H5: 10-seed replication of M0/M1/M4b with bootstrap CIs
5. H6: Per-stratum analysis (analysis only, no GPU, uses existing checkpoints)

If H2 is falsified: reframe contribution as H1 + H3 + methodology (H4, H5) — still publishable at EMNLP/ACL.
If H1+H2 both falsified: fall back to H4 + H5 as methodological contributions (venues: ACL, ARR).
