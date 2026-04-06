"""Statistical tests: bootstrap CIs, Cohen's d, effect size analysis.

Implements H5 statistical rigor requirements from experiment-plan.md.
Bootstrap B=1000 resamples, 95% CIs, paired comparison.
"""
from __future__ import annotations

import logging

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


def bootstrap_ci(
    values: list[float] | np.ndarray,
    statistic: str = "mean",
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for a statistic.

    Args:
        values: Sample values.
        statistic: "mean" or "median".
        n_bootstrap: Number of bootstrap resamples.
        ci: Confidence level (e.g., 0.95 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (point_estimate, lower_bound, upper_bound).
    """
    rng = np.random.default_rng(seed)
    arr = np.asarray(values)
    n = len(arr)

    stat_fn = np.mean if statistic == "mean" else np.median
    point_est = float(stat_fn(arr))

    boot_stats = np.array([
        stat_fn(rng.choice(arr, size=n, replace=True))
        for _ in range(n_bootstrap)
    ])

    alpha = 1 - ci
    lower = float(np.percentile(boot_stats, 100 * alpha / 2))
    upper = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))

    return point_est, lower, upper


def bootstrap_paired_ci(
    values_a: list[float] | np.ndarray,
    values_b: list[float] | np.ndarray,
    statistic: str = "mean_diff",
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap CI for the paired difference (A - B).

    Args:
        values_a: Metric values for condition A (e.g., M4b).
        values_b: Metric values for condition B (e.g., M0).
        statistic: "mean_diff" for mean(A) - mean(B).
        n_bootstrap: Number of bootstrap resamples.
        ci: Confidence level.
        seed: Random seed.

    Returns:
        Tuple of (point_estimate_diff, lower, upper).
        If CI excludes 0, difference is statistically significant at level (1 - ci).
    """
    rng = np.random.default_rng(seed)
    a = np.asarray(values_a)
    b = np.asarray(values_b)

    point_est = float(np.mean(a) - np.mean(b))
    n_a, n_b = len(a), len(b)

    diffs = []
    for _ in range(n_bootstrap):
        boot_a = rng.choice(a, size=n_a, replace=True)
        boot_b = rng.choice(b, size=n_b, replace=True)
        diffs.append(np.mean(boot_a) - np.mean(boot_b))

    diffs = np.array(diffs)
    alpha = 1 - ci
    lower = float(np.percentile(diffs, 100 * alpha / 2))
    upper = float(np.percentile(diffs, 100 * (1 - alpha / 2)))

    return point_est, lower, upper


def cohens_d(
    values_a: list[float] | np.ndarray,
    values_b: list[float] | np.ndarray,
    pooled: bool = True,
) -> float:
    """Compute Cohen's d effect size for two independent groups.

    Args:
        values_a: Group A metric values.
        values_b: Group B metric values.
        pooled: Use pooled standard deviation (default True).

    Returns:
        Cohen's d. Positive = A > B.
    """
    a = np.asarray(values_a, dtype=float)
    b = np.asarray(values_b, dtype=float)

    mean_diff = np.mean(a) - np.mean(b)

    if pooled:
        # Pooled std
        n_a, n_b = len(a), len(b)
        var_a = np.var(a, ddof=1)
        var_b = np.var(b, ddof=1)
        pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    else:
        pooled_std = np.std(a, ddof=1)

    if pooled_std == 0:
        return 0.0
    return float(mean_diff / pooled_std)


def effect_size_label(d: float) -> str:
    """Classify Cohen's d effect size by convention (Cohen 1988)."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    if abs_d < 0.5:
        return "small"
    if abs_d < 0.8:
        return "medium"
    return "large"


def post_hoc_power(
    d: float,
    n_per_group: int,
    alpha: float = 0.05,
    two_tailed: bool = True,
) -> float:
    """Estimate achieved statistical power for a two-sample t-test.

    Args:
        d: Observed Cohen's d effect size.
        n_per_group: Number of observations per group.
        alpha: Significance level.
        two_tailed: Whether the test is two-tailed.

    Returns:
        Estimated power in [0, 1].
    """
    from scipy.stats import norm, t

    df = 2 * n_per_group - 2
    ncp = d * np.sqrt(n_per_group / 2)  # non-centrality parameter

    if two_tailed:
        t_crit = t.ppf(1 - alpha / 2, df)
    else:
        t_crit = t.ppf(1 - alpha, df)

    # Power = P(|T| > t_crit | ncp)
    power = 1 - t.cdf(t_crit, df, loc=ncp) + t.cdf(-t_crit, df, loc=ncp)
    return float(np.clip(power, 0, 1))


def compare_conditions(
    metric_values: dict[str, list[float]],
    comparisons: list[tuple[str, str]],
    metric_name: str,
    n_bootstrap: int = 1000,
) -> list[dict]:
    """Run all pairwise comparisons for a metric across conditions.

    Args:
        metric_values: Dict mapping condition name → list of per-seed metric values.
        comparisons: List of (condition_a, condition_b) pairs to compare.
        metric_name: Name of the metric being compared (for reporting).
        n_bootstrap: Bootstrap resamples.

    Returns:
        List of result dicts, one per comparison.
    """
    results = []
    for cond_a, cond_b in comparisons:
        vals_a = np.asarray(metric_values[cond_a])
        vals_b = np.asarray(metric_values[cond_b])

        diff, lower, upper = bootstrap_paired_ci(vals_a, vals_b, n_bootstrap=n_bootstrap)
        d = cohens_d(vals_a, vals_b)
        power = post_hoc_power(d, n_per_group=len(vals_a))
        significant = lower > 0 or upper < 0  # CI excludes 0

        results.append({
            "metric": metric_name,
            "condition_a": cond_a,
            "condition_b": cond_b,
            "mean_a": float(np.mean(vals_a)),
            "mean_b": float(np.mean(vals_b)),
            "diff": diff,
            "ci_lower": lower,
            "ci_upper": upper,
            "cohens_d": d,
            "effect_size": effect_size_label(d),
            "power": power,
            "significant": significant,
        })

        logger.info(
            f"{metric_name}: {cond_a} vs {cond_b} → "
            f"Δ={diff:.4f} [{lower:.4f}, {upper:.4f}], "
            f"d={d:.2f} ({effect_size_label(d)}), power={power:.2f}, "
            f"significant={significant}"
        )

    return results
