# Experiment Plan v3 (Step 9 — Post-Reposition)

**Date:** 2026-03-30
**Step:** 9 / 38
**Version:** 3 (post N1 reposition, adds SRA/SMRA/entmax baselines, ≥10 seeds, 2×2×2 ablation)
**Supersedes:** docs/experiment-plan.md (v2, 5 seeds, no SRA/SMRA)

---

## Research Question (Repositioned)

Under what conditions does selective-head attention supervision outperform full-head supervision for faithful hate speech explanation? What value-subspace condition predicts functional invariance?

---

## Dataset

- **HateXplain** (Mathew et al., 2021) — 20,148 posts, 3-class (hate/offensive/normal)
- Splits: 15,383 train / 1,922 val / 2,843 test
- Rationale annotations: Token-level binary masks from 3 annotators; aggregate via majority vote (primary) and per-annotator (for E-W4 stratification)
- Annotator agreement stratification (E-W4): Compute Krippendorff's α per test instance; split into high/medium/low agreement tertiles

---

## Baselines (REQUIRED — absence would trigger N2 block)

| ID | Name | Description |
|----|------|-------------|
| B0 | `vanilla-bert` | BERT-base-uncased, CE loss only, no attention supervision |
| B1 | `softmax-full` | All 144 heads supervised with softmax-transformed rationale targets |
| B2 | `sra-replication` | **SRA (arXiv:2511.07065) replication**: sparsemax supervision, all heads, MSE loss, on HateXplain |
| B3 | `smra-replication` | **SMRA (arXiv:2601.03481) replication**: sparsemax supervision, all heads, moral-rationale subset, HateXplain |
| B4 | `entmax-full` | **Entmax (α=1.5) supervision**, all heads — "why sparsemax and not entmax?" reviewer defense |
| B5 | `random-head-sparsemax` | Sparsemax supervision of 24 randomly selected heads — control for importance scoring |

---

## Core 2×2×2 Ablation Design

The main novel contribution is isolating the contribution of each factor independently:

| Factor | Level A | Level B |
|--------|---------|---------|
| Supervision target | Full-head (all 144) | Selective-head (top-24 by gradient importance) |
| Attention transform | Softmax supervision targets | Sparsemax supervision targets |
| Loss function | MSE | KL divergence |

This gives 2³ = 8 conditions:

| ID | Name | Target | Transform | Loss |
|----|------|--------|-----------|------|
| M1 | `full-softmax-mse` | Full | Softmax | MSE |
| M2 | `full-softmax-kl` | Full | Softmax | KL |
| M3 | `full-sparsemax-mse` | Full | Sparsemax | MSE |
| M4 | `full-sparsemax-kl` | Full | Sparsemax | KL |
| M5 | `sel-softmax-mse` | Selective | Softmax | MSE |
| M6 | `sel-softmax-kl` | Selective | Softmax | KL |
| M7 | `sel-sparsemax-mse` | **Selective** | **Sparsemax** | **MSE** — PRIMARY |
| M8 | `sel-sparsemax-kl` | Selective | Sparsemax | KL |

---

## K Sweep (Head Count Sensitivity)

For the winning selective-head configuration (expected: M7), sweep K:

| ID | K | Notes |
|----|---|-------|
| K1 | 6 | 4.2% of heads |
| K2 | 12 | 8.3% |
| K3 | 24 | 16.7% — default |
| K4 | 36 | 25.0% |
| K5 | 48 | 33.3% |
| K6 | 72 | 50.0% |

---

## Statistical Specifications

- **Seeds:** 10 per condition (seeds: 42, 123, 456, 789, 1024, 2048, 3141, 6283, 7777, 9999)
- **Total runs:** (6 baselines + 8 2×2×2 + 6 K-sweep) × 10 seeds = 200 runs
- **Statistical tests:** Bootstrap CI (10,000 samples), two-sided, α=0.05; paired bootstrap for head-to-head comparisons
- **Effect size:** Report Cohen's d for all primary comparisons
- **Multiple comparisons:** Bonferroni correction across the 8 2×2×2 conditions

---

## Primary Hypotheses (Revised)

| ID | Hypothesis | Test |
|----|-----------|------|
| H1 | Selective-head (M7) > Full-head (M3) on comprehensiveness, same F1 | Bootstrap CI on mean comprehensiveness difference |
| H2 | M7 ≥ B2 (SRA replication) on comprehensiveness, with F1 within 1% | Paired bootstrap M7 vs. B2 |
| H3 | M7 ≥ B3 (SMRA replication) on comprehensiveness | Paired bootstrap M7 vs. B3 |
| H4 | Gradient-based head selection (M7) > random head selection (B5) on comprehensiveness | Paired bootstrap |
| H5 | Value-subspace principal angles correlate with F1 delta | Spearman ρ across K-sweep conditions |

---

## Value-Subspace Analysis (Theoretical Contribution)

For each configuration in the K-sweep:
1. Extract value matrices V_h for all heads h ∈ [1..144]
2. For selected heads S and unselected heads U, compute principal angles between span(V_S) and span(V_U)
3. Correlate mean principal angle with F1 degradation
4. Hypothesis H5: smaller principal angles → smaller F1 degradation

---

## Annotator Disagreement Stratification (E-W4)

For the primary model (M7) vs. B0:
1. Compute Krippendorff's α per test instance using the 3 annotator rationale masks
2. Split test set into tertiles: high (α>0.7), medium (0.4<α≤0.7), low (α≤0.4)
3. Compare comprehensiveness gain per stratum
4. Expected: larger gain on low-agreement examples (model learns to handle ambiguity)

---

## Evaluation Metrics

### Classification
- Macro-F1 (primary)
- Per-class F1 (hate, offensive, normal)

### Faithfulness (ERASER framework — DeYoung 2020)
- **Comprehensiveness:** P(y|X) - P(y|X\rationale) — higher = rationale is more important
- **Sufficiency:** P(y|rationale) — higher = rationale alone sufficient

### Plausibility
- **IoU-F1:** Jaccard overlap between predicted sparse attention and human rationale tokens
- **AUPRC:** Area under precision-recall for rationale token identification

### Attention Properties
- Mean attention entropy per head (lower = sparser)
- Sparsity ratio (% exactly-zero weights, sparsemax conditions only)

---

## Compute Budget

- Per run: ~15 min on A100 80GB
- 200 runs × 15 min = 50 GPU-hours
- K-sweep + analysis: +10 GPU-hours
- Total: ~60 GPU-hours

---

## Assumptions Being Tested

| ID | Assumption | Experiment |
|----|-----------|-----------|
| A1 | Gradient importance identifies semantically meaningful heads | H4: random vs. importance-based selection |
| A2 | Sparsemax produces sparser attention than softmax-transformed supervision | 2×2×2 ablation, sparsity ratio metric |
| A3 | Comprehensiveness/sufficiency are valid faithfulness proxies | Use ERASER-validated definitions |
| A4 | HateXplain rationales are meaningful | E-W4 stratification shows coherent patterns |
| A5 | Value-subspace span condition predicts invariance | K-sweep + principal angle analysis |
| A6 | Results generalize beyond HateXplain | **Out of scope — acknowledged limitation** |
