# Power Analysis Guide

## When Power Analysis Is Appropriate

Power analysis is a statistical method for determining the minimum sample size needed to detect an effect of a given size with a specified confidence level.

### Use Power Analysis When

- You have prior effect size estimates (from pilot data or published work)
- You have variance estimates for the metric
- The cost of runs is high and you need to justify the budget
- Reviewers at your target venue expect it (common in medical/clinical ML)

### Skip Power Analysis When

- No prior effect size data exists (most novel ML experiments)
- The benchmark has a community convention for number of seeds/folds
- The experiment is exploratory (effect size unknown)
- Computational cost per run is low

## Required Parameters

| Parameter | Symbol | Description | How to Estimate |
|-----------|--------|-------------|-----------------|
| Effect size | d | Expected difference / std deviation | From prior work or domain conventions |
| Significance level | alpha | False positive rate | Typically 0.05 |
| Power | 1-beta | Probability of detecting true effect | Typically 0.80 or 0.90 |
| Variance | sigma^2 | Variability of the metric | From pilot data or prior work |

## Convention-Based Defaults by Domain

When power analysis is not feasible, use community conventions:

| Domain / Benchmark | Convention | Source |
|-------------------|------------|--------|
| ImageNet classification | 1 run (deterministic except augmentation) | Community standard |
| CIFAR-10/100 | 3-5 seeds | Bhojanapalli et al. (2021) |
| NLP (GLUE/SuperGLUE) | 5 seeds with different initialization | Dodge et al. (2020) |
| EEG/BCI (BCI-IV-2a) | 5 seeds x leave-one-subject-out | Community standard |
| Reinforcement learning | 10+ seeds (high variance) | Henderson et al. (2018) |
| Graph neural networks | 10 seeds | Shchur et al. (2018) |
| Medical imaging | 5-fold CV, report mean +/- std | Community standard |
| Generative models (FID) | 3-5 evaluations | Community standard |

## Computing Power Analysis

### For Paired Comparisons (Most Common in ML)

```
n = (z_{alpha/2} + z_{beta})^2 * 2 * sigma^2 / delta^2
```

Where:
- n = required sample size per group
- z_{alpha/2} = 1.96 for alpha=0.05 (two-tailed)
- z_{beta} = 0.84 for power=0.80, 1.28 for power=0.90
- sigma^2 = variance of the difference
- delta = minimum detectable effect size

### Python Implementation

```python
from scipy import stats
import numpy as np

def compute_sample_size(
    effect_size: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Compute minimum sample size for a paired t-test."""
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    n = ((z_alpha + z_beta) ** 2 * 2 * std_dev ** 2) / effect_size ** 2
    return int(np.ceil(n))
```

## Common Mistakes

### 1. Post-Hoc Power Analysis

- NEVER compute power analysis after seeing results
- Post-hoc power is a function of the p-value and adds no information
- If you want to assess whether your study was adequately powered, do it BEFORE the experiment

### 2. Assuming Effect Sizes Without Marking Them

- If you assume d=0.5 (medium effect) without evidence, mark it explicitly:
  "ASSUMED: effect size d=0.5 (medium, no prior data). This power analysis is illustrative only."

### 3. Ignoring Multiple Comparisons

- If you test multiple hypotheses, the effective alpha is lower
- Apply Bonferroni correction: alpha_effective = alpha / number_of_tests
- This increases the required sample size

### 4. Confusing Seeds with Independent Samples

- Different random seeds on the same train/test split are NOT independent samples
- They measure variance due to initialization, not data sampling
- True independent samples require different data splits or subjects
