# Analytical Reference Catalog

Canonical PyTorch/NumPy implementations for common analytical references used in ML research. Each entry is a self-contained, numerically stable implementation ready to be placed into `src/metrics/analytical/`.

---

## A. Ordinary Least Squares (OLS)

### Mathematical Definition

Given design matrix X (n x d) and target vector y (n x 1), the OLS solution minimizes ||Xw - y||^2:

```
beta = (X^T X)^{-1} X^T y
```

### PyTorch Implementation

```python
import torch


def ols_solution(X: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Closed-form OLS: beta = (X^T X)^{-1} X^T y. Numerically stable via lstsq.

    Args:
        X: Design matrix of shape (n, d). Must have n >= d.
        y: Target vector of shape (n,) or (n, 1).

    Returns:
        beta: Coefficient vector of shape (d,) or (d, 1) matching y.

    Raises:
        ValueError: If X has more columns than rows (underdetermined system).
    """
    if X.shape[0] < X.shape[1]:
        raise ValueError(
            f"Underdetermined system: n={X.shape[0]} < d={X.shape[1]}. "
            "Use ridge regression or pseudoinverse instead."
        )
    # lstsq is numerically superior to explicit (X^T X)^{-1} X^T y
    result = torch.linalg.lstsq(X, y if y.ndim == 2 else y.unsqueeze(1))
    solution = result.solution
    return solution.squeeze(-1) if y.ndim == 1 else solution


def ols_predict(X: torch.Tensor, beta: torch.Tensor) -> torch.Tensor:
    """Predict y = X @ beta."""
    return X @ beta
```

### Numerical Stability Notes

- **Never** compute `torch.inverse(X.T @ X) @ X.T @ y` directly. The matrix X^T X amplifies the condition number squared. Use `torch.linalg.lstsq` which internally uses QR or SVD decomposition.
- Check condition number before solving: if `torch.linalg.cond(X) > 1e10`, warn the user and suggest ridge regression.
- Use fp64 for small matrices (d < 100) to avoid precision loss.

### When This Reference Is Appropriate

- Hypothesis compares a neural network's learned solution to the OLS closed-form (e.g., "Does the model converge to the OLS solution?")
- Hypothesis examines implicit regularization by comparing model weights to OLS weights
- Baseline comparison: model should do at least as well as OLS on linear tasks

### Common Implementation Mistakes

1. Using `torch.inverse` instead of `torch.linalg.lstsq` -- leads to numerical instability for ill-conditioned X
2. Forgetting to handle the case where n < d (underdetermined system)
3. Not matching dtypes -- X in fp32 and y in fp64 will cause silent precision issues
4. Not centering X and y when intercept is expected -- the formula above assumes X includes a column of ones if an intercept is needed

---

## B. Ridge Regression

### Mathematical Definition

Ridge regression adds L2 regularization to OLS:

```
beta = (X^T X + lambda * I)^{-1} X^T y
```

### PyTorch Implementation

```python
import torch


def ridge_solution(
    X: torch.Tensor, y: torch.Tensor, lam: float = 1.0
) -> torch.Tensor:
    """Ridge regression: beta = (X^T X + lambda I)^{-1} X^T y.

    Args:
        X: Design matrix of shape (n, d).
        y: Target vector of shape (n,) or (n, 1).
        lam: Regularization strength. Must be > 0.

    Returns:
        beta: Coefficient vector of shape (d,) or (d, 1) matching y.
    """
    if lam <= 0:
        raise ValueError(f"Regularization lambda must be > 0, got {lam}")
    d = X.shape[1]
    A = X.T @ X + lam * torch.eye(d, dtype=X.dtype, device=X.device)
    b = X.T @ (y if y.ndim == 2 else y.unsqueeze(1))
    # A is positive definite (since lam > 0), so Cholesky is safe and fast
    beta = torch.linalg.solve(A, b)
    return beta.squeeze(-1) if y.ndim == 1 else beta
```

### Numerical Stability Notes

- The regularization term `lambda * I` makes A positive definite, so `torch.linalg.solve` (Cholesky-based) is safe and faster than lstsq.
- For very small lambda, the solution approaches OLS -- consider using lstsq as a fallback.
- For cross-validation over lambda, precompute SVD of X once: `U, S, Vt = torch.linalg.svd(X, full_matrices=False)`, then beta(lambda) = V diag(S / (S^2 + lambda)) U^T y.

### When This Reference Is Appropriate

- Hypothesis about implicit regularization in neural networks (compare model weights to ridge solution at various lambda)
- Baseline comparison: model should outperform ridge regression to justify complexity
- Studying the bias-variance tradeoff by sweeping lambda

### Common Implementation Mistakes

1. Using lambda=0 (degenerates to OLS, loses positive-definiteness guarantee)
2. Not scaling X before ridge regression -- regularization penalizes large coefficients, so features on different scales get penalized differently
3. Regularizing the intercept -- typically the intercept should not be penalized (center X and y first)

---

## C. Gradient Descent Update

### Mathematical Definition

For linear regression with MSE loss L = (1/2n) ||Xw - y||^2, the gradient is:

```
grad = (1/n) X^T (Xw - y)
w' = w - lr * grad
```

### PyTorch Implementation

```python
import torch


def gd_update(
    X: torch.Tensor,
    y: torch.Tensor,
    w: torch.Tensor,
    lr: float = 0.01,
) -> torch.Tensor:
    """One step of gradient descent on MSE loss for linear regression.

    Args:
        X: Design matrix of shape (n, d).
        y: Target vector of shape (n,) or (n, 1).
        w: Current weight vector of shape (d,) or (d, 1).
        lr: Learning rate.

    Returns:
        w_new: Updated weight vector, same shape as w.
    """
    n = X.shape[0]
    y_flat = y.squeeze(-1) if y.ndim == 2 else y
    w_flat = w.squeeze(-1) if w.ndim == 2 else w
    residual = X @ w_flat - y_flat
    grad = X.T @ residual / n
    w_new = w_flat - lr * grad
    return w_new.unsqueeze(-1) if w.ndim == 2 else w_new


def gd_trajectory(
    X: torch.Tensor,
    y: torch.Tensor,
    w_init: torch.Tensor,
    lr: float = 0.01,
    steps: int = 100,
) -> list[torch.Tensor]:
    """Run multiple GD steps and return the full weight trajectory.

    Args:
        X: Design matrix of shape (n, d).
        y: Target vector of shape (n,).
        w_init: Initial weight vector of shape (d,).
        lr: Learning rate.
        steps: Number of GD steps.

    Returns:
        trajectory: List of weight vectors [w_0, w_1, ..., w_steps].
    """
    trajectory = [w_init.clone()]
    w = w_init.clone()
    for _ in range(steps):
        w = gd_update(X, y, w, lr)
        trajectory.append(w.clone())
    return trajectory
```

### Numerical Stability Notes

- Learning rate must satisfy `lr < 2 / sigma_max(X)^2` for convergence, where sigma_max is the largest singular value. Compute via `torch.linalg.svdvals(X)[0]`.
- For very large X, use mini-batch gradient descent instead.
- The trajectory can diverge with too-large lr -- check for NaN/Inf after each step.

### When This Reference Is Appropriate

- Hypothesis about whether a neural network implements gradient descent internally (mesa-optimization)
- Comparing model's weight trajectory to analytical GD trajectory
- Studying learning dynamics: does the model converge at the same rate as GD?

### Common Implementation Mistakes

1. Off-by-one in the loss: using (1/2n) vs. (1/n) -- the gradient differs by a factor of 2
2. Not matching the loss function to the gradient -- e.g., computing cross-entropy loss but using MSE gradient
3. Forgetting to clone tensors in the trajectory (all entries point to the same memory)

---

## D. Kernel Regression (Nadaraya-Watson)

### Mathematical Definition

For a query point x*, the Nadaraya-Watson estimator is:

```
f(x*) = sum_i K(x*, x_i) * y_i / sum_i K(x*, x_i)
```

where K is a kernel function (typically Gaussian): K(x, x') = exp(-||x - x'||^2 / (2 * h^2))

### PyTorch Implementation

```python
import torch


def nadaraya_watson(
    X_train: torch.Tensor,
    y_train: torch.Tensor,
    X_query: torch.Tensor,
    bandwidth: float = 1.0,
) -> torch.Tensor:
    """Nadaraya-Watson kernel regression with Gaussian kernel.

    Args:
        X_train: Training inputs of shape (n, d).
        y_train: Training targets of shape (n,).
        X_query: Query inputs of shape (m, d).
        bandwidth: Gaussian kernel bandwidth h.

    Returns:
        y_pred: Predictions of shape (m,).
    """
    # Pairwise squared distances: (m, n)
    dists_sq = torch.cdist(X_query, X_train).pow(2)
    # Gaussian kernel weights in log-space for stability
    log_weights = -dists_sq / (2.0 * bandwidth ** 2)
    # Softmax gives normalized weights (numerically stable via logsumexp)
    weights = torch.softmax(log_weights, dim=-1)  # (m, n)
    y_pred = weights @ y_train  # (m,)
    return y_pred
```

### Numerical Stability Notes

- Use `torch.softmax` (which internally uses log-sum-exp) rather than manually computing `exp / sum(exp)`.
- Very small bandwidth causes all weight to concentrate on the nearest neighbor (overfitting); very large bandwidth gives the mean of all y (underfitting).
- For high-dimensional data, distances concentrate -- consider scaling bandwidth with dimension.

### When This Reference Is Appropriate

- Hypothesis about attention mechanisms implementing kernel regression
- Comparing transformer predictions to Nadaraya-Watson with attention weights as the kernel
- Nonparametric baseline for function approximation tasks

### Common Implementation Mistakes

1. Computing exp(-d^2) directly without log-space normalization -- causes underflow for large distances
2. Not squaring the bandwidth in the denominator (using h instead of h^2)
3. Using Euclidean distance instead of squared Euclidean distance in the Gaussian kernel formula

---

## E. Bayes-Optimal Classifier

### Mathematical Definition

For two-class Gaussian class-conditionals with known parameters:

```
P(y=1|x) = sigmoid(w^T x + b)
```

where w = Sigma^{-1}(mu_1 - mu_0) and b = -0.5 (mu_1 + mu_0)^T Sigma^{-1} (mu_1 - mu_0) + log(pi_1 / pi_0)

(assuming equal covariance Sigma for both classes)

### PyTorch Implementation

```python
import torch


def bayes_optimal_classifier(
    mu_0: torch.Tensor,
    mu_1: torch.Tensor,
    Sigma: torch.Tensor,
    prior_1: float = 0.5,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute Bayes-optimal linear classifier for Gaussian class-conditionals.

    Assumes equal covariance for both classes (LDA setting).

    Args:
        mu_0: Mean of class 0, shape (d,).
        mu_1: Mean of class 1, shape (d,).
        Sigma: Shared covariance matrix, shape (d, d). Must be positive definite.
        prior_1: Prior probability of class 1.

    Returns:
        w: Weight vector of shape (d,).
        b: Bias scalar.
    """
    if prior_1 <= 0 or prior_1 >= 1:
        raise ValueError(f"Prior must be in (0, 1), got {prior_1}")
    # Solve Sigma @ w = (mu_1 - mu_0) instead of inverting Sigma
    diff = mu_1 - mu_0
    w = torch.linalg.solve(Sigma, diff)
    mean_sum = 0.5 * (mu_1 + mu_0)
    b = -mean_sum @ w + torch.log(
        torch.tensor(prior_1 / (1.0 - prior_1), dtype=mu_0.dtype)
    )
    return w, b


def bayes_optimal_predict(
    X: torch.Tensor, w: torch.Tensor, b: torch.Tensor
) -> torch.Tensor:
    """Predict class probabilities using the Bayes-optimal classifier.

    Args:
        X: Input data of shape (n, d).
        w: Weight vector of shape (d,).
        b: Bias scalar.

    Returns:
        probs: P(y=1|x) of shape (n,).
    """
    logits = X @ w + b
    return torch.sigmoid(logits)
```

### Numerical Stability Notes

- Use `torch.linalg.solve` instead of `torch.inverse(Sigma) @ diff` -- avoids explicit inversion.
- Check that Sigma is positive definite: `torch.linalg.cholesky(Sigma)` should not raise.
- For near-singular Sigma, add small regularization: `Sigma + eps * I`.

### When This Reference Is Appropriate

- Hypothesis about whether a model achieves Bayes-optimal accuracy on a known data distribution
- Studying how close a learned classifier is to the theoretical optimum
- Measuring the gap between learned and optimal decision boundaries

### Common Implementation Mistakes

1. Inverting the covariance matrix instead of solving the linear system
2. Forgetting the prior term when classes are imbalanced
3. Using the wrong sign convention for the bias term

---

## F. Neural Tangent Kernel (NTK) Prediction

### Mathematical Definition

For a linearized neural network around initialization theta_0:

```
f_lin(x) = f(x; theta_0) + nabla_theta f(x; theta_0)^T (theta - theta_0)
```

The NTK kernel is: K(x, x') = nabla_theta f(x; theta_0)^T nabla_theta f(x'; theta_0)

The NTK prediction after infinite training time with MSE loss is:

```
f_NTK(X_test) = K(X_test, X_train) @ K(X_train, X_train)^{-1} @ y_train
```

### PyTorch Implementation

```python
import torch
import torch.nn as nn


def compute_ntk(
    model: nn.Module,
    X1: torch.Tensor,
    X2: torch.Tensor,
) -> torch.Tensor:
    """Compute the empirical Neural Tangent Kernel between X1 and X2.

    Args:
        model: Neural network (must be in eval mode, single output).
        X1: First set of inputs, shape (n1, d).
        X2: Second set of inputs, shape (n2, d).

    Returns:
        K: NTK matrix of shape (n1, n2).
    """
    def get_jacobian(X: torch.Tensor) -> torch.Tensor:
        """Compute Jacobian of model output w.r.t. parameters for each input."""
        jac_rows = []
        for i in range(X.shape[0]):
            model.zero_grad()
            out = model(X[i : i + 1]).squeeze()
            out.backward()
            grads = []
            for p in model.parameters():
                if p.grad is not None:
                    grads.append(p.grad.detach().flatten())
            jac_rows.append(torch.cat(grads))
        return torch.stack(jac_rows)  # (n, num_params)

    J1 = get_jacobian(X1)  # (n1, P)
    J2 = get_jacobian(X2)  # (n2, P)
    return J1 @ J2.T  # (n1, n2)


def ntk_predict(
    model: nn.Module,
    X_train: torch.Tensor,
    y_train: torch.Tensor,
    X_test: torch.Tensor,
    reg: float = 1e-6,
) -> torch.Tensor:
    """NTK prediction: f(X_test) = K(test, train) @ (K(train, train) + reg I)^{-1} @ y.

    Args:
        model: Neural network at initialization.
        X_train: Training inputs, shape (n_train, d).
        y_train: Training targets, shape (n_train,).
        X_test: Test inputs, shape (n_test, d).
        reg: Tikhonov regularization for numerical stability.

    Returns:
        y_pred: Predictions of shape (n_test,).
    """
    K_train = compute_ntk(model, X_train, X_train)  # (n_train, n_train)
    K_test_train = compute_ntk(model, X_test, X_train)  # (n_test, n_train)
    n = K_train.shape[0]
    K_reg = K_train + reg * torch.eye(n, dtype=K_train.dtype, device=K_train.device)
    alpha = torch.linalg.solve(K_reg, y_train.unsqueeze(1)).squeeze(1)
    return K_test_train @ alpha
```

### Numerical Stability Notes

- K(train, train) is often ill-conditioned -- always add Tikhonov regularization.
- The Jacobian computation is memory-intensive: O(n * P) where P is the number of parameters. For large models, use `torch.func.jacrev` or `torch.func.vmap` for efficiency.
- Use fp64 for the kernel matrix inversion.

### When This Reference Is Appropriate

- Hypothesis about whether a neural network operates in the "lazy" (kernel) regime
- Comparing finite-width network predictions to NTK predictions
- Studying how network width affects the NTK approximation quality

### Common Implementation Mistakes

1. Not freezing model parameters during Jacobian computation (gradients leak)
2. Forgetting regularization when inverting the kernel matrix
3. Using the NTK formula for multi-output networks without accounting for output dimension

---

## G. Scaling Law Fits

### Mathematical Definition

Power-law scaling: y = a * x^b, or equivalently log(y) = log(a) + b * log(x).

Fit via OLS on log-transformed data:

```
[log(a), b] = OLS(log(x), log(y))
```

### PyTorch Implementation

```python
import torch
import numpy as np


def fit_power_law(
    x: torch.Tensor, y: torch.Tensor
) -> dict[str, float]:
    """Fit a power law y = a * x^b via OLS on log-log data.

    Args:
        x: Independent variable (e.g., model size, dataset size). Must be > 0.
        y: Dependent variable (e.g., loss, error). Must be > 0.

    Returns:
        Dict with keys: a, b, r_squared, log_a, residual_std.
    """
    if (x <= 0).any() or (y <= 0).any():
        raise ValueError("Power-law fit requires all positive values for x and y.")

    log_x = torch.log(x.double())
    log_y = torch.log(y.double())

    # Design matrix for OLS: [1, log(x)]
    X = torch.stack([torch.ones_like(log_x), log_x], dim=-1)
    result = torch.linalg.lstsq(X, log_y)
    log_a, b = result.solution[0].item(), result.solution[1].item()
    a = np.exp(log_a)

    # R-squared on log scale
    log_y_pred = X @ result.solution
    ss_res = ((log_y - log_y_pred) ** 2).sum().item()
    ss_tot = ((log_y - log_y.mean()) ** 2).sum().item()
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    residual_std = np.sqrt(ss_res / max(len(x) - 2, 1))

    return {
        "a": a,
        "b": b,
        "r_squared": r_squared,
        "log_a": log_a,
        "residual_std": residual_std,
    }


def predict_power_law(x: torch.Tensor, a: float, b: float) -> torch.Tensor:
    """Predict y = a * x^b."""
    return a * x.double().pow(b)
```

### Numerical Stability Notes

- Always fit in log-space (OLS on log(x), log(y)), not in original space -- avoids heteroscedasticity.
- Check that all values are strictly positive before taking log.
- Use fp64 for the regression to avoid precision loss in log transforms.
- Report R^2 on the log scale, not the original scale.

### When This Reference Is Appropriate

- Hypothesis about neural scaling laws (loss vs. model size, dataset size, compute)
- Predicting performance at larger scales from smaller-scale experiments
- Comparing observed scaling exponents to theoretical predictions

### Common Implementation Mistakes

1. Fitting in original space instead of log-space -- gives biased estimates
2. Using R^2 from log-space and interpreting it as fit quality in original space
3. Not checking for zero or negative values before log transform
4. Extrapolating far beyond the range of observed data
