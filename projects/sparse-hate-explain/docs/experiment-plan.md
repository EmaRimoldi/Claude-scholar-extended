# Experiment Plan: Sparse Rationale-Constrained Attention for Hate Speech Explanations

## Overview

Evaluate whether sparsemax attention supervision with selective head targeting improves faithfulness of hate speech explanations in BERT-base-uncased on HateXplain, without degrading 3-class classification accuracy. Target venue: NeurIPS 2026.

## Dataset

- **Name**: HateXplain (Mathew et al., 2021)
- **Source**: `hatexplain` on HuggingFace Datasets (or GitHub: hate-alert/HateXplain)
- **Size**: 20,148 posts, 3-class (hate, offensive, normal)
- **Splits**: Use original train/val/test (15,383 / 1,922 / 2,843)
- **Rationale annotations**: Token-level binary masks from 3 annotators; aggregate via majority vote
- **Preprocessing**: Lowercase, BERT WordPiece tokenization, max_length=128, truncation

## Model Architecture

- **Base**: `bert-base-uncased` (12 layers, 12 heads, 768 hidden, 110M params)
- **Classification head**: Linear(768, 3) on [CLS] token
- **Precision**: fp16 mixed precision
- **Attention modification**: Replace softmax with sparsemax in supervised heads (configurable per-head)

## Experimental Conditions

### Phase 1: Baselines (3 conditions × 3 seeds = 9 runs)

| ID | Condition | Description |
|----|-----------|-------------|
| B1 | `vanilla` | BERT fine-tuned with CE loss only, no attention supervision |
| B2 | `softmax-all` | BERT + softmax attention supervision on ALL 144 heads |
| B3 | `softmax-all-strong` | Same as B2 but λ=2.0 (strong supervision) |

### Phase 2: Head Importance Analysis (1 run, no training)

| ID | Condition | Description |
|----|-----------|-------------|
| A1 | `head-importance` | Run IG head importance scoring on trained B1 model, identify top-K heads |

### Phase 3: Sparsemax Experiments (6 conditions × 3 seeds = 18 runs)

| ID | Condition | Attention | Scope | λ |
|----|-----------|-----------|-------|---|
| S1 | `sparsemax-all` | sparsemax | all 144 heads | 1.0 |
| S2 | `sparsemax-top12` | sparsemax | top-12 heads | 1.0 |
| S3 | `sparsemax-top24` | sparsemax | top-24 heads | 1.0 |
| S4 | `sparsemax-top36` | sparsemax | top-36 heads | 1.0 |
| S5 | `softmax-top24` | softmax | top-24 heads | 1.0 |
| S6 | `sparsemax-top24-strong` | sparsemax | top-24 heads | 2.0 |

### Phase 4: Ablation — Lambda Sweep (4 conditions × 3 seeds = 12 runs)

| ID | Condition | λ |
|----|-----------|---|
| L1 | `sparsemax-top24-lam01` | 0.1 |
| L2 | `sparsemax-top24-lam05` | 0.5 |
| L3 | `sparsemax-top24-lam10` | 1.0 |
| L4 | `sparsemax-top24-lam20` | 2.0 |

**Total runs**: 9 + 1 + 18 + 12 = 40 runs

## Training Configuration

```yaml
model:
  name: bert-base-uncased
  num_labels: 3
  max_length: 128

training:
  learning_rate: 2e-5
  weight_decay: 0.01
  warmup_ratio: 0.1
  num_epochs: 10
  early_stopping_patience: 3
  batch_size: 16
  fp16: true
  gradient_accumulation_steps: 1

supervision:
  attention_transform: sparsemax  # or softmax
  supervised_heads: all  # or list of (layer, head) tuples
  lambda_attn: 1.0
  rationale_aggregation: majority_vote  # from 3 annotators

seeds: [42, 123, 456, 789, 1024]
```

## Evaluation Metrics

### Classification
- macro-F1 (primary)
- Per-class F1 (hate, offensive, normal)
- Accuracy

### Faithfulness
- **Attention-IG correlation**: Spearman ρ between attention weights and Integrated Gradients attributions (per-token, averaged over test set)
- **Sufficiency**: P(y|rationale tokens only) — higher means rationale is sufficient
- **Comprehensiveness**: P(y|all tokens) - P(y|non-rationale tokens) — higher means rationale is important

### Plausibility
- **Token-level F1**: Against human rationale annotations (majority vote)
- **AUPRC**: Area under precision-recall curve for rationale token identification

### Attention Properties
- **Attention entropy**: Mean entropy of attention distributions (lower = sparser)
- **Sparsity ratio**: % of attention weights that are exactly 0

## Compute Requirements

- **Per run**: ~15 min on A100 80GB (BERT-base, 15K train samples, 10 epochs)
- **Total**: ~40 runs × 15 min = 10 GPU-hours
- **Head importance analysis**: ~5 min (single forward pass with IG)
- **Evaluation**: ~5 min per model
- **Buffer**: 2x → ~20 GPU-hours total
- **Cluster**: MIT Engaging, pi_tpoggio partition (A100 80GB), or mit_normal_gpu

## Execution Plan

### Step 1: Data Download (CPU, login node)
- Download HateXplain dataset
- Download bert-base-uncased model weights
- Preprocess and cache tokenized data

### Step 2: Phase 1 — Baselines (GPU)
- Submit 9 jobs (3 conditions × 3 seeds)
- Can run in parallel

### Step 3: Phase 2 — Head Importance (GPU)
- Run IG head importance on best B1 model
- Output: ranked list of (layer, head) by importance score
- Determine top-K head sets

### Step 4: Phase 3 — Sparsemax Experiments (GPU)
- Submit 18 jobs (6 conditions × 3 seeds)
- Can run in parallel

### Step 5: Phase 4 — Lambda Ablation (GPU)
- Submit 12 jobs (4 conditions × 3 seeds)
- Can run in parallel

### Step 6: Evaluation & Analysis
- Collect all results
- Statistical tests (paired bootstrap)
- Generate figures

## Expected Outputs

1. `results/` — Per-run metrics JSON files
2. `results/summary.csv` — Aggregated results table
3. `figures/` — Publication-quality figures
4. `manuscript/` — LaTeX paper

## Risk Mitigation

- **Risk**: Sparsemax gradient issues → Use entmax with α=1.99 as fallback
- **Risk**: HateXplain class imbalance → Use weighted CE loss
- **Risk**: Head importance unstable → Average IG over 3 B1 seeds
- **Risk**: Training instability with sparse attention → Gradient clipping (max_norm=1.0)
