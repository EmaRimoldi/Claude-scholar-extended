"""Example: Analytical reference comparison pipeline.

This example demonstrates the full measurement pipeline:
1. Generate synthetic linear regression data
2. Compute the OLS analytical solution
3. Run gradient descent to simulate a model's learned solution
4. Compare the model output to the analytical prediction via cosine similarity
5. Compute bootstrap CI on the comparison metric

This is the pattern used when a hypothesis compares model behavior
to a known algorithm (e.g., "Does the model converge to the OLS solution?").
"""

import numpy as np
import torch


# -- Analytical References --


def ols_solution(X: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Closed-form OLS: beta = (X^T X)^{-1} X^T y. Numerically stable via lstsq."""
    result = torch.linalg.lstsq(X, y if y.ndim == 2 else y.unsqueeze(1))
    return result.solution.squeeze(-1) if y.ndim == 1 else result.solution


def gd_update(
    X: torch.Tensor, y: torch.Tensor, w: torch.Tensor, lr: float = 0.01
) -> torch.Tensor:
    """One step of GD on MSE loss: w' = w - lr * X^T(Xw - y) / n."""
    n = X.shape[0]
    residual = X @ w - y
    grad = X.T @ residual / n
    return w - lr * grad


# -- Comparison Function --


def compare_cosine(
    empirical: torch.Tensor,
    reference: torch.Tensor,
    eps: float = 1e-8,
) -> float:
    """Cosine similarity between empirical and reference vectors."""
    e_norm = empirical.norm().clamp(min=eps)
    r_norm = reference.norm().clamp(min=eps)
    return float((empirical / e_norm) @ (reference / r_norm))


# -- Bootstrap CI --


def bootstrap_ci_on_metric(
    X: torch.Tensor,
    y: torch.Tensor,
    w_model: torch.Tensor,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Bootstrap CI on cosine similarity between model weights and OLS solution.

    Resamples (X, y) rows, recomputes OLS on each resample, and measures
    cosine similarity between w_model and the resampled OLS solution.
    """
    rng = np.random.default_rng(seed=seed)
    n = X.shape[0]
    sims = []

    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        X_boot = X[idx]
        y_boot = y[idx]
        beta_boot = ols_solution(X_boot, y_boot)
        sim = compare_cosine(w_model, beta_boot)
        sims.append(sim)

    sims = np.array(sims)
    return {
        "point_estimate": compare_cosine(w_model, ols_solution(X, y)),
        "ci_lower": float(np.percentile(sims, 100 * alpha / 2)),
        "ci_upper": float(np.percentile(sims, 100 * (1 - alpha / 2))),
        "bootstrap_se": float(sims.std()),
        "n_bootstrap": n_bootstrap,
    }


# -- Full Pipeline Demo --

if __name__ == "__main__":
    torch.manual_seed(42)

    # 1. Generate synthetic data: y = X @ beta_true + noise
    n, d = 200, 10
    X = torch.randn(n, d, dtype=torch.float64)
    beta_true = torch.randn(d, dtype=torch.float64)
    noise = torch.randn(n, dtype=torch.float64) * 0.1
    y = X @ beta_true + noise

    # 2. Compute OLS analytical solution
    beta_ols = ols_solution(X, y)
    print(f"OLS solution norm:     {beta_ols.norm():.4f}")
    print(f"True beta norm:        {beta_true.norm():.4f}")
    print(f"OLS vs true (cosine):  {compare_cosine(beta_ols, beta_true):.6f}")

    # 3. Simulate model learning via gradient descent
    w = torch.zeros(d, dtype=torch.float64)  # init at zero
    lr = 0.01
    for step in range(500):
        w = gd_update(X, y, w, lr=lr)

    print(f"\nGD solution norm:      {w.norm():.4f}")
    print(f"GD vs OLS (cosine):    {compare_cosine(w, beta_ols):.6f}")
    print(f"GD vs true (cosine):   {compare_cosine(w, beta_true):.6f}")

    # 4. Compare GD to OLS with bootstrap CI
    result = bootstrap_ci_on_metric(X, y, w, n_bootstrap=10000, alpha=0.05)

    print(f"\nComparison: GD weights vs OLS solution")
    print(f"  Cosine similarity:   {result['point_estimate']:.6f}")
    print(f"  95% CI:              [{result['ci_lower']:.6f}, {result['ci_upper']:.6f}]")
    print(f"  Bootstrap SE:        {result['bootstrap_se']:.6f}")

    # 5. Interpretation
    if result["ci_lower"] > 0.99:
        print("\n  Interpretation: GD has converged to the OLS solution (cos sim > 0.99).")
    elif result["ci_lower"] > 0.95:
        print("\n  Interpretation: GD is very close to OLS but has not fully converged.")
    else:
        print("\n  Interpretation: GD has NOT converged to the OLS solution.")
