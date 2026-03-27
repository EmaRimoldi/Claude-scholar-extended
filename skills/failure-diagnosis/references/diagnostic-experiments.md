# Diagnostic Experiment Design

## Principles

### 1. Minimum Viable Test
Each diagnostic experiment should answer exactly one question:
- "Is the implementation correct?" → overfit one batch
- "Are hyperparameters reasonable?" → small sweep on key params
- "Is the data clean?" → visualize distributions
- "Is the metric appropriate?" → compute multiple metrics

### 2. Cost-Benefit Prioritization

Prioritize diagnostics by: `priority = likelihood(cause) × (1 / cost_to_verify)`

| Diagnostic | Typical Cost | Information Value |
|---|---|---|
| Overfit one batch | Minutes | High (catches implementation bugs) |
| Visualize data | Minutes | Medium (catches data issues) |
| Compute multiple metrics | Minutes | Medium (catches metric issues) |
| Small hyperparameter sweep | Hours | High (catches tuning issues) |
| Run on known-good benchmark | Hours | High (catches hypothesis issues) |
| Full ablation study | Days | Medium (isolates components) |

### 3. Expected Outcomes

For each diagnostic, define:
- **If cause X**: we expect to see outcome Y
- **If not cause X**: we expect to see outcome Z

This turns diagnostics into falsifiable tests.

## Standard Diagnostic Suite

### Quick Checks (< 30 minutes)

1. **Overfit check**: Train on 1 batch for 1000 steps. Training loss should approach 0.
2. **Gradient check**: Print gradient norms. Should be non-zero and not exploding.
3. **Data check**: Visualize 10 random samples with their labels.
4. **Output check**: Print model outputs for a known input. Should be reasonable.

### Medium Checks (< 1 day)

5. **Sanity benchmark**: Run method on MNIST or equivalent. Should achieve near-SOTA.
6. **Hyperparameter sensitivity**: Sweep learning rate (5 values) on a small data subset.
7. **Baseline verification**: Re-run the baseline to confirm published numbers.

### Deep Checks (1-3 days)

8. **Representation analysis**: t-SNE or PCA of learned representations.
9. **Component ablation**: Remove each novel component and measure impact.
10. **Cross-validation**: Check if failure is consistent across all folds or specific to some.

## Control Experiments

Always have at least one control that you KNOW should work:
- A trivial baseline (majority class, random) that establishes the floor
- A known-good method on the same data that establishes the ceiling
- The proposed method on a known-good benchmark that verifies implementation
