# Numerical Stability Guide

Reference for numerically stable computation in metric implementations. Every metric in `src/metrics/` must follow these guidelines.

---

## A. Numerically Stable Cosine Similarity

### The Problem

Cosine similarity = (a . b) / (||a|| * ||b||). Fails when either vector has zero or near-zero norm.

### Safe Implementation

```python
import torch


def safe_cosine_similarity(
    a: torch.Tensor, b: torch.Tensor, eps: float = 1e-8
) -> torch.Tensor:
    """Numerically stable cosine similarity.

    Handles zero vectors by clamping norms to eps.

    Args:
        a: First tensor, shape (..., d).
        b: Second tensor, shape (..., d).
        eps: Small constant to avoid division by zero.

    Returns:
        Cosine similarity, shape (...).
    """
    a_norm = a.norm(dim=-1, keepdim=True).clamp(min=eps)
    b_norm = b.norm(dim=-1, keepdim=True).clamp(min=eps)
    return (a / a_norm * b / b_norm).sum(dim=-1)
```

### Key Rules

1. **Always clamp norms**: `norm.clamp(min=eps)` before dividing. Never divide by raw norms.
2. **Use PyTorch built-in when possible**: `torch.nn.functional.cosine_similarity(a, b, dim=-1, eps=1e-8)` already handles this correctly.
3. **Zero-vector convention**: When both vectors are zero, cosine similarity is undefined. Return 0.0 and log a warning.
4. **Batch dimensions**: Support arbitrary batch dimensions with `dim=-1`.

---

## B. Safe Matrix Operations

### lstsq vs. Inverse

| Operation | Use | Avoid |
|-----------|-----|-------|
| Solve Ax = b | `torch.linalg.solve(A, b)` | `torch.inverse(A) @ b` |
| Least squares | `torch.linalg.lstsq(A, b)` | `torch.inverse(A.T @ A) @ A.T @ b` |
| Positive-definite solve | `torch.linalg.cholesky(A)` + `torch.cholesky_solve` | `torch.inverse(A)` |

### Condition Number Checks

```python
def check_condition(A: torch.Tensor, threshold: float = 1e10) -> None:
    """Warn if matrix is ill-conditioned."""
    cond = torch.linalg.cond(A).item()
    if cond > threshold:
        import warnings
        warnings.warn(
            f"Matrix condition number is {cond:.2e} (threshold: {threshold:.2e}). "
            "Results may be numerically unreliable. Consider adding regularization."
        )
```

### Pseudoinverse

When the system is underdetermined or ill-conditioned, use `torch.linalg.pinv` with an explicit rcond:

```python
# Default rcond truncates singular values below max(M, N) * eps * sigma_max
A_pinv = torch.linalg.pinv(A, rcond=1e-5)
```

### Key Rules

1. **Never explicitly invert a matrix** unless you have a specific reason and have verified the condition number.
2. **Check condition number** before any solve/lstsq operation on user-provided data.
3. **Use fp64** for matrix operations on small matrices (d < 100).
4. **Add regularization** when condition number exceeds 1e10: `A + eps * I`.

---

## C. Log-Space Computation

### The Problem

Probabilities can underflow to zero in fp32 (smallest positive ~1e-38). Products of probabilities underflow even faster.

### Rules

1. **Store log-probabilities** instead of probabilities whenever possible.
2. **Use `torch.logsumexp`** for log-space addition:
   ```python
   # Instead of: log(exp(a) + exp(b))
   # Use:
   torch.logsumexp(torch.stack([a, b]), dim=0)
   ```
3. **Use `torch.nn.functional.log_softmax`** instead of `softmax` then `log`:
   ```python
   # Avoid: torch.log(torch.softmax(logits, dim=-1))  # NaN when softmax gives 0
   # Use:
   torch.nn.functional.log_softmax(logits, dim=-1)
   ```
4. **Use `torch.special.xlogy`** for x * log(y) when x can be zero:
   ```python
   # Handles 0 * log(0) = 0 correctly
   torch.special.xlogy(p, q)
   ```

### KL Divergence in Log-Space

```python
def safe_kl_divergence(
    log_p: torch.Tensor, log_q: torch.Tensor
) -> torch.Tensor:
    """KL(P || Q) computed entirely in log-space.

    Args:
        log_p: Log-probabilities of P, shape (..., K).
        log_q: Log-probabilities of Q, shape (..., K).

    Returns:
        KL divergence, shape (...).
    """
    p = torch.exp(log_p)
    return (p * (log_p - log_q)).sum(dim=-1)
```

---

## D. Handling NaN and Inf

### Detection

```python
def check_nan_inf(
    tensor: torch.Tensor, name: str = "tensor"
) -> None:
    """Check for NaN or Inf values and raise informative error.

    Args:
        tensor: Tensor to check.
        name: Name for error messages.

    Raises:
        ValueError: If NaN or Inf detected, with count and location info.
    """
    nan_count = torch.isnan(tensor).sum().item()
    inf_count = torch.isinf(tensor).sum().item()
    if nan_count > 0:
        raise ValueError(
            f"NaN detected in '{name}': {nan_count}/{tensor.numel()} values. "
            f"Shape: {tuple(tensor.shape)}, dtype: {tensor.dtype}."
        )
    if inf_count > 0:
        raise ValueError(
            f"Inf detected in '{name}': {inf_count}/{tensor.numel()} values. "
            f"Shape: {tuple(tensor.shape)}, dtype: {tensor.dtype}."
        )
```

### Common Causes and Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| NaN in loss | 0/0 or log(0) | Add eps before division/log |
| Inf in logits | Exploding values before softmax | Gradient clipping, lower lr |
| NaN in gradients | Inf * 0 in backward pass | Gradient clipping, check inputs |
| NaN after exp | Very large input to exp | Use logsumexp instead |
| NaN in cosine sim | Zero-norm vector | Clamp norms to eps |

### Defensive Pattern

```python
def safe_metric_wrapper(metric_fn):
    """Wrap a metric function with NaN/Inf input and output checks."""
    def wrapper(*args, **kwargs):
        for i, arg in enumerate(args):
            if isinstance(arg, torch.Tensor):
                check_nan_inf(arg, name=f"input_{i}")
        result = metric_fn(*args, **kwargs)
        if isinstance(result, torch.Tensor):
            check_nan_inf(result, name="output")
        return result
    return wrapper
```

---

## E. Floating-Point Precision

### When to Use fp64

| Situation | Precision | Reason |
|-----------|-----------|--------|
| Statistical tests (t-test, etc.) | fp64 | Small differences matter for p-values |
| Matrix inversions / solves | fp64 for small matrices | Condition number amplification |
| Accumulating sums over many values | fp64 or Kahan summation | Catastrophic cancellation |
| Bootstrap resampling | fp64 | Many repeated operations amplify error |
| Log-likelihood computation | fp64 | Log transforms amplify relative error |

### When fp32 Is Fine

| Situation | Precision | Reason |
|-----------|-----------|--------|
| Forward pass of large models | fp32 (or fp16/bf16) | Speed matters, error is small |
| Large-batch metric computation | fp32 | Individual errors average out |
| Cosine similarity with eps | fp32 | eps handles the dangerous cases |

### Upcasting Pattern

```python
def to_fp64_for_stats(tensor: torch.Tensor) -> torch.Tensor:
    """Upcast to fp64 for statistical computations."""
    return tensor.to(torch.float64)
```

### Key Rule

When in doubt, upcast to fp64 for the computation, then cast the result back to the original dtype. The overhead is negligible for metric computation (metrics operate on summary statistics, not full batches).
