"""Example: Implementing a metric with @register_metric.

This example shows a complete, production-ready cosine similarity metric
that follows all conventions from the measurement-implementation skill:
- Registers via @register_metric into MetricFactory
- Numerically stable computation (eps clamping, zero-vector handling)
- Returns standardized dict with value, CI, p-value, effect size
- Proper type hints and docstring
"""

import numpy as np
import torch
from scipy import stats

# -- In a real project, this import comes from src/metrics/__init__.py --
# from src.metrics import register_metric
# For this example, we define a minimal stub:
METRIC_FACTORY: dict[str, type] = {}


def register_metric(name: str):
    """Decorator to register a metric class into the MetricFactory."""
    def decorator(cls):
        METRIC_FACTORY[name] = cls
        return cls
    return decorator


@register_metric("cosine_similarity")
class CosineSimilarityMetric:
    """Cosine similarity between two sets of vectors with bootstrap CI.

    Computes the mean cosine similarity across paired vectors, with a
    bootstrap confidence interval and a one-sample t-test against zero.
    """

    def __init__(self, eps: float = 1e-8, n_bootstrap: int = 10000):
        self.eps = eps
        self.n_bootstrap = n_bootstrap

    def __call__(
        self,
        a: torch.Tensor,
        b: torch.Tensor,
        alpha: float = 0.05,
    ) -> dict:
        """Compute cosine similarity with CI and significance test.

        Args:
            a: First set of vectors, shape (n, d).
            b: Second set of vectors, shape (n, d).
            alpha: Significance level for CI and test.

        Returns:
            Dict with keys: value, ci_lower, ci_upper, p_value, effect_size.
        """
        if a.shape != b.shape:
            raise ValueError(f"Shape mismatch: a={a.shape}, b={b.shape}")

        # Numerically stable per-pair cosine similarity
        a_norm = a.norm(dim=-1, keepdim=True).clamp(min=self.eps)
        b_norm = b.norm(dim=-1, keepdim=True).clamp(min=self.eps)
        cos_sims = (a / a_norm * b / b_norm).sum(dim=-1)  # shape (n,)

        # Convert to numpy for statistical tests
        values = cos_sims.detach().cpu().to(torch.float64).numpy()
        mean_sim = float(values.mean())

        # Bootstrap CI (percentile method)
        rng = np.random.default_rng(seed=42)
        boot_means = np.array([
            rng.choice(values, size=len(values), replace=True).mean()
            for _ in range(self.n_bootstrap)
        ])
        ci_lower = float(np.percentile(boot_means, 100 * alpha / 2))
        ci_upper = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))

        # One-sample t-test: is mean cosine similarity significantly != 0?
        t_stat, p_value = stats.ttest_1samp(values, 0.0)

        # Effect size: Cohen's d (mean / std)
        effect_size = float(values.mean() / values.std(ddof=1)) if values.std(ddof=1) > 0 else 0.0

        return {
            "value": mean_sim,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "p_value": float(p_value),
            "effect_size": effect_size,
            "effect_size_type": "cohens_d",
            "n_pairs": len(values),
        }


# -- Demo usage --
if __name__ == "__main__":
    torch.manual_seed(42)

    # Generate two sets of vectors that are similar but not identical
    d = 128
    n = 50
    base = torch.randn(n, d)
    noise = torch.randn(n, d) * 0.1
    a = base + noise
    b = base + torch.randn(n, d) * 0.1

    metric = METRIC_FACTORY["cosine_similarity"](eps=1e-8, n_bootstrap=10000)
    result = metric(a, b, alpha=0.05)

    print("Cosine Similarity Metric Result:")
    print(f"  Mean similarity:  {result['value']:.4f}")
    print(f"  95% CI:           [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
    print(f"  p-value (!= 0):   {result['p_value']:.4e}")
    print(f"  Effect size (d):  {result['effect_size']:.4f}")
    print(f"  N pairs:          {result['n_pairs']}")
