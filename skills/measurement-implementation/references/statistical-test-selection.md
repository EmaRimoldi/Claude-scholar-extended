# Statistical Test Selection Guide

Reference for selecting and implementing statistical tests in ML experiments. Used by `statistical_tests.py` in `src/metrics/`.

---

## A. Decision Tree for Test Selection

```
Is the comparison paired?
(same model on different conditions, or same data with different methods)
├── YES (paired)
│   ├── n >= 30 AND Shapiro-Wilk p > 0.05?
│   │   ├── YES → Paired t-test
│   │   └── NO  → Wilcoxon signed-rank test
│   └── Want nonparametric regardless? → Bootstrap CI or Permutation test
│
└── NO (unpaired, independent groups)
    ├── n >= 30 AND Shapiro-Wilk p > 0.05?
    │   ├── YES → Independent t-test (Welch's)
    │   └── NO  → Mann-Whitney U test
    └── Want nonparametric regardless? → Bootstrap CI or Permutation test
```

**Default recommendation**: If n < 30 (common in ML: 5-10 seeds), use nonparametric tests. When in doubt, report both parametric and nonparametric results.

---

## B. Implementation of Common Tests

### Paired t-test

```python
from scipy import stats
import numpy as np


def paired_ttest(
    a: np.ndarray, b: np.ndarray, alpha: float = 0.05
) -> dict:
    """Paired t-test with effect size and CI.

    Args:
        a, b: Paired observations, same length.
        alpha: Significance level.

    Returns:
        Dict with statistic, p_value, effect_size, ci_lower, ci_upper.
    """
    diff = a - b
    t_stat, p_value = stats.ttest_rel(a, b)
    # Cohen's d for paired data
    d = diff.mean() / diff.std(ddof=1)
    # CI for the mean difference
    se = diff.std(ddof=1) / np.sqrt(len(diff))
    t_crit = stats.t.ppf(1 - alpha / 2, df=len(diff) - 1)
    ci_lower = diff.mean() - t_crit * se
    ci_upper = diff.mean() + t_crit * se
    return {
        "test": "paired_ttest",
        "statistic": float(t_stat),
        "p_value": float(p_value),
        "effect_size": float(d),
        "effect_size_type": "cohens_d",
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n": len(a),
    }
```

### Wilcoxon Signed-Rank Test

```python
def wilcoxon_test(
    a: np.ndarray, b: np.ndarray, alpha: float = 0.05
) -> dict:
    """Wilcoxon signed-rank test with rank-biserial effect size.

    Args:
        a, b: Paired observations, same length.
        alpha: Significance level.

    Returns:
        Dict with statistic, p_value, effect_size, ci_lower, ci_upper.
    """
    stat, p_value = stats.wilcoxon(a, b, alternative="two-sided")
    n = len(a)
    # Rank-biserial correlation as effect size
    r = 1 - (2 * stat) / (n * (n + 1) / 2)
    # CI via bootstrap (see Section E below)
    ci = bootstrap_ci(a - b, statistic=np.median, n_bootstrap=10000, alpha=alpha)
    return {
        "test": "wilcoxon",
        "statistic": float(stat),
        "p_value": float(p_value),
        "effect_size": float(r),
        "effect_size_type": "rank_biserial",
        "ci_lower": ci["ci_lower"],
        "ci_upper": ci["ci_upper"],
        "n": n,
    }
```

### Mann-Whitney U Test

```python
def mann_whitney_test(
    a: np.ndarray, b: np.ndarray, alpha: float = 0.05
) -> dict:
    """Mann-Whitney U test for unpaired samples.

    Args:
        a, b: Independent samples (may differ in length).
        alpha: Significance level.

    Returns:
        Dict with statistic, p_value, effect_size, ci_lower, ci_upper.
    """
    stat, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
    n1, n2 = len(a), len(b)
    # Rank-biserial correlation
    r = 1 - (2 * stat) / (n1 * n2)
    # CI via bootstrap on the difference of means
    ci = bootstrap_ci_two_sample(a, b, n_bootstrap=10000, alpha=alpha)
    return {
        "test": "mann_whitney_u",
        "statistic": float(stat),
        "p_value": float(p_value),
        "effect_size": float(r),
        "effect_size_type": "rank_biserial",
        "ci_lower": ci["ci_lower"],
        "ci_upper": ci["ci_upper"],
        "n1": n1,
        "n2": n2,
    }
```

### Permutation Test

```python
def permutation_test(
    a: np.ndarray,
    b: np.ndarray,
    n_permutations: int = 10000,
    paired: bool = True,
) -> dict:
    """Permutation test for paired or unpaired comparisons.

    Args:
        a, b: Observations. Must be same length if paired.
        n_permutations: Number of random permutations.
        paired: If True, permute within pairs; if False, permute group labels.

    Returns:
        Dict with observed_diff, p_value, null_distribution summary.
    """
    rng = np.random.default_rng(seed=42)
    observed_diff = np.mean(a) - np.mean(b)
    count_extreme = 0

    if paired:
        diff = a - b
        for _ in range(n_permutations):
            signs = rng.choice([-1, 1], size=len(diff))
            perm_diff = np.mean(diff * signs)
            if abs(perm_diff) >= abs(observed_diff):
                count_extreme += 1
    else:
        combined = np.concatenate([a, b])
        n1 = len(a)
        for _ in range(n_permutations):
            rng.shuffle(combined)
            perm_diff = np.mean(combined[:n1]) - np.mean(combined[n1:])
            if abs(perm_diff) >= abs(observed_diff):
                count_extreme += 1

    p_value = (count_extreme + 1) / (n_permutations + 1)
    return {
        "test": "permutation",
        "observed_diff": float(observed_diff),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "paired": paired,
    }
```

---

## C. Effect Size Computation

### Cohen's d (Parametric)

```python
def cohens_d_paired(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d for paired samples."""
    diff = a - b
    return float(diff.mean() / diff.std(ddof=1))


def cohens_d_independent(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d for independent samples (pooled std)."""
    n1, n2 = len(a), len(b)
    pooled_std = np.sqrt(
        ((n1 - 1) * a.std(ddof=1) ** 2 + (n2 - 1) * b.std(ddof=1) ** 2)
        / (n1 + n2 - 2)
    )
    return float((a.mean() - b.mean()) / pooled_std)
```

### Interpretation Scale (Cohen, 1988)

| |d| | Interpretation |
|-----|----------------|
| 0.2 | Small |
| 0.5 | Medium |
| 0.8 | Large |
| 1.2+ | Very large |

### Eta-Squared (for ANOVA-like comparisons)

```python
def eta_squared(groups: list[np.ndarray]) -> float:
    """Eta-squared: proportion of variance explained by group membership."""
    all_data = np.concatenate(groups)
    grand_mean = all_data.mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_total = np.sum((all_data - grand_mean) ** 2)
    return float(ss_between / ss_total) if ss_total > 0 else 0.0
```

---

## D. Multiple Comparison Correction

### Bonferroni Correction

```python
def bonferroni_correction(
    p_values: list[float], alpha: float = 0.05
) -> list[dict]:
    """Bonferroni correction: reject if p < alpha / m."""
    m = len(p_values)
    adjusted_alpha = alpha / m
    return [
        {
            "original_p": p,
            "adjusted_alpha": adjusted_alpha,
            "reject": p < adjusted_alpha,
        }
        for p in p_values
    ]
```

### Holm-Bonferroni (Step-Down) -- Preferred

```python
def holm_bonferroni_correction(
    p_values: list[float], alpha: float = 0.05
) -> list[dict]:
    """Holm-Bonferroni step-down correction. More powerful than Bonferroni."""
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    results = [None] * m
    reject_remaining = True

    for rank, idx in enumerate(sorted_indices):
        adjusted_alpha = alpha / (m - rank)
        if reject_remaining and p_values[idx] < adjusted_alpha:
            results[idx] = {
                "original_p": p_values[idx],
                "adjusted_alpha": adjusted_alpha,
                "rank": rank + 1,
                "reject": True,
            }
        else:
            reject_remaining = False
            results[idx] = {
                "original_p": p_values[idx],
                "adjusted_alpha": adjusted_alpha,
                "rank": rank + 1,
                "reject": False,
            }
    return results
```

### Benjamini-Hochberg FDR

```python
def benjamini_hochberg_correction(
    p_values: list[float], alpha: float = 0.05
) -> list[dict]:
    """Benjamini-Hochberg FDR correction. Controls false discovery rate."""
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    results = [None] * m
    max_reject_rank = -1

    # Find the largest rank k such that p_(k) <= k/m * alpha
    for rank, idx in enumerate(sorted_indices):
        threshold = (rank + 1) / m * alpha
        if p_values[idx] <= threshold:
            max_reject_rank = rank

    for rank, idx in enumerate(sorted_indices):
        results[idx] = {
            "original_p": p_values[idx],
            "bh_threshold": (rank + 1) / m * alpha,
            "rank": rank + 1,
            "reject": rank <= max_reject_rank,
        }
    return results
```

---

## E. Bootstrap Confidence Intervals

### Percentile Method

```python
def bootstrap_ci(
    data: np.ndarray,
    statistic=np.mean,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Bootstrap percentile confidence interval.

    Args:
        data: 1D array of observations.
        statistic: Function to compute the statistic of interest.
        n_bootstrap: Number of bootstrap samples.
        alpha: Significance level (0.05 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        Dict with ci_lower, ci_upper, point_estimate, se.
    """
    rng = np.random.default_rng(seed=seed)
    n = len(data)
    boot_stats = np.array([
        statistic(rng.choice(data, size=n, replace=True))
        for _ in range(n_bootstrap)
    ])
    ci_lower = float(np.percentile(boot_stats, 100 * alpha / 2))
    ci_upper = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))
    return {
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "point_estimate": float(statistic(data)),
        "se": float(boot_stats.std()),
    }
```

### BCa (Bias-Corrected and Accelerated) Method

```python
def bootstrap_ci_bca(
    data: np.ndarray,
    statistic=np.mean,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """BCa bootstrap confidence interval. Corrects for bias and skewness.

    More accurate than percentile method, especially for skewed distributions.
    """
    from scipy.stats import norm as sp_norm

    rng = np.random.default_rng(seed=seed)
    n = len(data)
    theta_hat = statistic(data)

    # Bootstrap distribution
    boot_stats = np.array([
        statistic(rng.choice(data, size=n, replace=True))
        for _ in range(n_bootstrap)
    ])

    # Bias correction: z0
    prop_less = np.mean(boot_stats < theta_hat)
    z0 = sp_norm.ppf(max(min(prop_less, 1 - 1e-10), 1e-10))

    # Acceleration: a (jackknife estimate)
    jack_stats = np.array([
        statistic(np.delete(data, i)) for i in range(n)
    ])
    jack_mean = jack_stats.mean()
    num = np.sum((jack_mean - jack_stats) ** 3)
    denom = 6.0 * np.sum((jack_mean - jack_stats) ** 2) ** 1.5
    a = num / denom if denom != 0 else 0.0

    # Adjusted percentiles
    z_alpha_lower = sp_norm.ppf(alpha / 2)
    z_alpha_upper = sp_norm.ppf(1 - alpha / 2)

    def adjusted_percentile(z_alpha):
        numer = z0 + z_alpha
        adj = z0 + numer / (1 - a * numer)
        return sp_norm.cdf(adj) * 100

    ci_lower = float(np.percentile(boot_stats, adjusted_percentile(z_alpha_lower)))
    ci_upper = float(np.percentile(boot_stats, adjusted_percentile(z_alpha_upper)))

    return {
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "point_estimate": float(theta_hat),
        "se": float(boot_stats.std()),
        "method": "bca",
    }
```

---

## F. Common Mistakes

1. **Using paired test on unpaired data** -- inflates the test statistic because the variance estimate is too small. Check: are observations truly paired (same subject/seed in both conditions)?

2. **Not correcting for multiple comparisons** -- testing 10 hypotheses at alpha=0.05 gives ~40% chance of at least one false positive. Always apply correction when testing more than one hypothesis.

3. **Reporting p-value without effect size** -- a significant p-value with a tiny effect size is not a meaningful result. Always report both.

4. **Bootstrap with too few resamples** -- use at least 10,000 for CI estimation; 1,000 is insufficient for tail estimation.

5. **Using standard error instead of confidence interval** -- SE is not a CI. CI = point +/- t_crit * SE, not point +/- SE.

6. **Treating seeds as independent samples** -- 5 random seeds on the same train/test split measure initialization variance only. They are not independent samples of the data distribution.
