# Synthetic Data Patterns

Comprehensive reference for generating synthetic datasets in ML experiment pipelines. Each pattern includes the mathematical definition, sampling code, parameter distributions, noise models, and known pitfalls.

---

## A. Regression Tasks

### Linear Regression (y = w^T x + epsilon)

The canonical synthetic task for in-context learning research.

**Mathematical definition:**
- Task vector: `w ~ N(0, I_d)` -- sampled fresh per episode
- Inputs: `x_i ~ N(0, I_d)`
- Noise: `epsilon ~ N(0, sigma^2)`
- Output: `y_i = w^T x_i + epsilon_i`

```python
import torch

def sample_linear_regression(
    d_input: int,
    n_points: int,
    noise_std: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Sample a single linear regression task.

    Args:
        d_input: Input dimensionality.
        n_points: Number of (x, y) pairs to generate.
        noise_std: Standard deviation of additive Gaussian noise.
        generator: Seeded torch.Generator for reproducibility.

    Returns:
        xs: Input points, shape (n_points, d_input).
        ys: Noisy outputs, shape (n_points,).
        w: Ground-truth weight vector, shape (d_input,).
    """
    w = torch.randn(d_input, generator=generator)
    xs = torch.randn(n_points, d_input, generator=generator)
    ys = xs @ w
    if noise_std > 0:
        ys = ys + noise_std * torch.randn(n_points, generator=generator)
    return xs, ys, w
```

**Parameter distributions:**
- `d_input` typically 5--100 for ICL research
- `noise_std` typically 0 (noiseless), 0.1, 0.25, or 1.0
- `w` can also be drawn from `Uniform(-1, 1)` or restricted to unit sphere

**Pitfalls:**
- Forgetting to sample a fresh `w` per episode leaks task identity across sequences
- Using the global RNG instead of a seeded `Generator` makes data non-reproducible

### Ridge Regression

Same data generation as linear regression. The distinction is in the analytical solution used as a reference baseline:

```python
def ridge_solution(
    xs: torch.Tensor, ys: torch.Tensor, lam: float
) -> torch.Tensor:
    """Compute the ridge regression solution w_hat = (X^T X + lam I)^{-1} X^T y.

    Args:
        xs: Input matrix, shape (n, d).
        ys: Output vector, shape (n,).
        lam: Regularization strength (>= 0).

    Returns:
        w_hat: Estimated weight vector, shape (d,).
    """
    d = xs.shape[1]
    A = xs.T @ xs + lam * torch.eye(d)
    b = xs.T @ ys
    return torch.linalg.solve(A, b)
```

### Polynomial Regression (y = sum_k a_k (w_k^T x)^k + epsilon)

**Mathematical definition:**
- Degree: `K` (typically 2--5)
- Per-degree vectors: `w_k ~ N(0, I_d / d)` -- the `/d` prevents magnitude explosion
- Coefficients: `a_k ~ N(0, 1)` or fixed (e.g., `a_k = 1` for all `k`)
- Output: `y = sum_{k=1}^{K} a_k (w_k^T x)^k + epsilon`

```python
def sample_polynomial_regression(
    d_input: int,
    n_points: int,
    degree: int,
    noise_std: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample a polynomial regression task up to given degree.

    Args:
        d_input: Input dimensionality.
        n_points: Number of points.
        degree: Maximum polynomial degree.
        noise_std: Noise standard deviation.
        generator: Seeded generator.

    Returns:
        xs: Inputs, shape (n_points, d_input).
        ys: Outputs, shape (n_points,).
    """
    xs = torch.randn(n_points, d_input, generator=generator)
    ys = torch.zeros(n_points)
    for k in range(1, degree + 1):
        w_k = torch.randn(d_input, generator=generator) / (d_input ** 0.5)
        a_k = torch.randn(1, generator=generator).item()
        projections = xs @ w_k
        ys = ys + a_k * projections.pow(k)
    if noise_std > 0:
        ys = ys + noise_std * torch.randn(n_points, generator=generator)
    return xs, ys
```

**Pitfalls:**
- Numerical overflow for high degrees -- always scale by `1/sqrt(d)` or clamp outputs
- Broadcasting errors when `w_k` shape is `(d,)` but `xs` shape is `(n, d, 1)`

### Sinusoidal Regression (y = A sin(omega^T x + phi) + epsilon)

```python
def sample_sinusoidal_regression(
    d_input: int,
    n_points: int,
    noise_std: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample a sinusoidal regression task with random amplitude, frequency, phase."""
    omega = torch.randn(d_input, generator=generator)
    phi = torch.rand(1, generator=generator).item() * 2 * 3.14159265
    amplitude = 0.5 + torch.rand(1, generator=generator).item() * 2.0
    xs = torch.randn(n_points, d_input, generator=generator)
    ys = amplitude * torch.sin(xs @ omega + phi)
    if noise_std > 0:
        ys = ys + noise_std * torch.randn(n_points, generator=generator)
    return xs, ys
```

### Sparse Linear Regression (y = w_sparse^T x + epsilon)

Only `s` of `d` components of `w` are non-zero:

```python
def sample_sparse_linear_regression(
    d_input: int,
    sparsity: int,
    n_points: int,
    noise_std: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Sample a sparse linear regression task.

    Args:
        d_input: Total input dimensionality.
        sparsity: Number of non-zero components in w.
        n_points: Number of data points.
        noise_std: Noise standard deviation.
        generator: Seeded generator.

    Returns:
        xs: Inputs, shape (n_points, d_input).
        ys: Outputs, shape (n_points,).
        w: Sparse weight vector, shape (d_input,).
    """
    w = torch.zeros(d_input)
    indices = torch.randperm(d_input, generator=generator)[:sparsity]
    w[indices] = torch.randn(sparsity, generator=generator)
    xs = torch.randn(n_points, d_input, generator=generator)
    ys = xs @ w
    if noise_std > 0:
        ys = ys + noise_std * torch.randn(n_points, generator=generator)
    return xs, ys, w
```

---

## B. Classification Tasks

### Linear Boundary (y = sign(w^T x))

Binary classification with a random linear decision boundary.

```python
def sample_linear_classification(
    d_input: int,
    n_points: int,
    noise_prob: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample a linear binary classification task.

    Args:
        d_input: Input dimensionality.
        n_points: Number of points.
        noise_prob: Probability of flipping each label (label noise).
        generator: Seeded generator.

    Returns:
        xs: Inputs, shape (n_points, d_input).
        ys: Binary labels in {0, 1}, shape (n_points,).
    """
    w = torch.randn(d_input, generator=generator)
    xs = torch.randn(n_points, d_input, generator=generator)
    ys = (xs @ w > 0).float()
    if noise_prob > 0:
        flip_mask = torch.rand(n_points, generator=generator) < noise_prob
        ys[flip_mask] = 1.0 - ys[flip_mask]
    return xs, ys
```

### XOR Classification

Non-linearly separable task based on the sign product of two random projections:

```python
def sample_xor_classification(
    d_input: int,
    n_points: int,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample an XOR classification task in d dimensions."""
    w1 = torch.randn(d_input, generator=generator)
    w2 = torch.randn(d_input, generator=generator)
    xs = torch.randn(n_points, d_input, generator=generator)
    proj1 = (xs @ w1 > 0).float()
    proj2 = (xs @ w2 > 0).float()
    ys = (proj1 != proj2).float()  # XOR: label 1 when signs differ
    return xs, ys
```

### Concentric Circles

2D classification by radial distance from origin:

```python
def sample_concentric_circles(
    n_points: int,
    noise_std: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample 2D concentric circles (inner=0, outer=1)."""
    radii = torch.rand(n_points, generator=generator)
    angles = torch.rand(n_points, generator=generator) * 2.0 * 3.14159265
    ys = (radii > 0.5).float()
    xs = torch.stack([radii * torch.cos(angles), radii * torch.sin(angles)], dim=1)
    if noise_std > 0:
        xs = xs + noise_std * torch.randn(n_points, 2, generator=generator)
    return xs, ys
```

### Multi-Class (Softmax) Classification

Linear boundaries generalized to `C` classes:

```python
def sample_multiclass_classification(
    d_input: int,
    n_classes: int,
    n_points: int,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample a multi-class classification task with random linear boundaries.

    Returns:
        xs: Inputs, shape (n_points, d_input).
        ys: Labels in {0, ..., n_classes - 1}, shape (n_points,).
    """
    W = torch.randn(d_input, n_classes, generator=generator)
    xs = torch.randn(n_points, d_input, generator=generator)
    logits = xs @ W
    ys = logits.argmax(dim=1)
    return xs, ys
```

**Class balance verification:**

```python
counts = torch.bincount(ys.long(), minlength=n_classes)
if (counts == 0).any():
    empty_classes = (counts == 0).nonzero(as_tuple=True)[0].tolist()
    raise ValueError(f"Classes {empty_classes} have zero samples. Resample or increase n_points.")
```

---

## C. Sequence / ICL Formatting

### ICL Episode Structure

An in-context learning episode presents `k` labeled examples followed by a query point:

```
input:  [x_1, y_1, x_2, y_2, ..., x_k, y_k, x_query]
target: y_query
```

Each episode has **fresh task parameters** (e.g., a new weight vector `w`), so the model must infer the task from the in-context examples rather than memorizing a fixed function.

```python
def build_icl_episode(
    task_fn,
    d_input: int,
    n_examples: int,
    noise_std: float,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Build a single ICL episode with interleaved x/y pairs.

    The episode tensor has shape (2 * n_examples + 1, d_input + 1):
    - Even positions (0, 2, 4, ...): x vectors with 0 appended
    - Odd positions (1, 3, 5, ...): y scalar in dim 0, rest zero-padded
    - Last position (2k): x_query with 0 appended

    Args:
        task_fn: Callable(xs, w) -> ys. Receives inputs and task params.
        d_input: Dimensionality of each input vector.
        n_examples: Number of in-context examples (k).
        noise_std: Additive noise standard deviation.
        generator: Per-episode seeded generator.

    Returns:
        episode: shape (2 * n_examples + 1, d_input + 1).
        target: y_query, shape (1,).
    """
    # Sample fresh task vector
    w = torch.randn(d_input, generator=generator)

    # Sample n_examples + 1 input points (last is query)
    n_total = n_examples + 1
    xs = torch.randn(n_total, d_input, generator=generator)
    ys = task_fn(xs, w)

    if noise_std > 0:
        ys = ys + noise_std * torch.randn(n_total, generator=generator)

    # Build interleaved sequence
    seq_len = 2 * n_examples + 1
    dim = d_input + 1
    episode = torch.zeros(seq_len, dim)

    for i in range(n_examples):
        episode[2 * i, :d_input] = xs[i]       # x_i in first d dims
        episode[2 * i + 1, 0] = ys[i]          # y_i in first dim

    episode[2 * n_examples, :d_input] = xs[-1]  # x_query
    target = ys[-1].unsqueeze(0)

    return episode, target
```

**Critical invariants:**
- `y_query` is NEVER included in the episode tensor -- it is the target
- Each episode uses a different `w` -- this is the entire point of ICL data
- The generator must be seeded per episode to allow reproducibility

### Autoregressive Token Sequences

For language-model-style data where input is a flat token sequence:

```python
def build_autoregressive_pair(
    tokens: torch.Tensor,
    context_len: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Build input/target pair for causal language modeling.

    Args:
        tokens: 1D tensor of token IDs, length >= context_len + 1.
        context_len: Context window length.

    Returns:
        input_ids: shape (context_len,).
        target_ids: shape (context_len,), shifted right by 1.
    """
    input_ids = tokens[:context_len]
    target_ids = tokens[1:context_len + 1]
    return input_ids, target_ids
```

### Classification Feature/Label Pairs

Standard `(features, label)` format with optional class balancing via undersampling:

```python
def balance_classes(
    xs: torch.Tensor, ys: torch.Tensor, generator: torch.Generator
) -> tuple[torch.Tensor, torch.Tensor]:
    """Undersample majority classes to match the smallest class."""
    classes = ys.unique()
    min_count = min((ys == c).sum().item() for c in classes)
    indices = []
    for c in classes:
        c_idx = (ys == c).nonzero(as_tuple=True)[0]
        perm = torch.randperm(c_idx.shape[0], generator=generator)[:min_count]
        indices.append(c_idx[perm])
    all_idx = torch.cat(indices)
    shuffle = torch.randperm(all_idx.shape[0], generator=generator)
    return xs[all_idx[shuffle]], ys[all_idx[shuffle]]
```

---

## D. Distribution Sampling Techniques

### Standard Distributions

| Distribution | PyTorch code | Typical use |
|-------------|-------------|-------------|
| Standard normal | `torch.randn(shape, generator=g)` | Inputs, weight vectors |
| Uniform [0, 1) | `torch.rand(shape, generator=g)` | Angles, probabilities, masks |
| Uniform [a, b) | `a + (b-a) * torch.rand(shape, generator=g)` | Bounded parameter ranges |
| Categorical | `torch.multinomial(probs, n, generator=g)` | Discrete label sampling |
| Bernoulli | `(torch.rand(shape, generator=g) < p).float()` | Binary masks, label noise |

### Truncated Normal (Rejection Sampling)

```python
def truncated_normal(
    shape: tuple[int, ...],
    low: float,
    high: float,
    generator: torch.Generator,
) -> torch.Tensor:
    """Sample from a truncated standard normal in [low, high]."""
    out = torch.empty(shape)
    remaining = torch.ones(shape, dtype=torch.bool)
    while remaining.any():
        candidates = torch.randn(remaining.sum().item(), generator=generator)
        valid = (candidates >= low) & (candidates <= high)
        fill_idx = remaining.nonzero(as_tuple=True)
        # Fill in valid candidates
        n_valid = valid.sum().item()
        out[fill_idx[0][:n_valid]] = candidates[valid]
        remaining[fill_idx[0][:n_valid]] = False
    return out
```

### Reparameterization Trick

For sampling from `N(mu, sigma^2)` in a differentiable way:

```python
def reparameterize(mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
    """Sample z ~ N(mu, sigma^2) using the reparameterization trick."""
    std = torch.exp(0.5 * log_var)
    eps = torch.randn_like(std)
    return mu + eps * std
```

---

## E. Common Data Bugs

### 1. Data Leakage: Shared Task Vector Across Episodes

**Bug:** Sampling `w` once in `__init__` and reusing across all `__getitem__` calls.

**Why it matters:** The model memorizes a single task instead of learning to infer tasks from context. ICL accuracy appears high but the model has zero transfer capability.

**Fix:** Always sample `w` inside `__getitem__` with a per-episode generator:

```python
def __getitem__(self, idx: int):
    g = torch.Generator().manual_seed(self.base_seed + idx)
    w = torch.randn(self.d_input, generator=g)
    ...
```

### 2. Data Leakage: Train/Test Overlap

**Bug:** Synthetic datasets that use sequential seeds `0..N-1` for train and `0..M-1` for test -- the first `M` episodes are identical.

**Fix:** Offset test seeds: `train_seed = base_seed + idx`, `test_seed = base_seed + num_train + idx`.

### 3. Off-by-One in ICL Sequence

**Bug:** Including `y_query` in the input episode (model sees the answer).

**Fix:** The episode ends at `x_query`. The target `y_query` is returned separately and never included in the input tensor.

### 4. Incorrect Broadcasting in Matrix Multiply

**Bug:** `xs @ w` fails or produces wrong shape when dimensions are misaligned.

**Fix:** Explicit shape management:

```python
# w shape: (d,) -- 1D vector
# xs shape: (n, d) -- 2D matrix
ys = xs @ w  # Result: (n,) -- correct
# If w is (d, 1), result is (n, 1) -- squeeze if you need (n,)
```

### 5. Numerical Overflow in Polynomial Tasks

**Bug:** `(w^T x)^5` with `d=100` easily overflows float32 (~3.4e38 max).

**Fix:** Scale inputs by `1/sqrt(d)` and/or clamp outputs:

```python
w_k = torch.randn(d, generator=g) / (d ** 0.5)
ys = ys.clamp(-1e6, 1e6)
```

### 6. Non-Deterministic Data from Global RNG

**Bug:** Using `torch.randn(d)` without a generator (depends on global RNG state, which changes based on prior operations).

**Fix:** Always pass an explicit `torch.Generator`:

```python
# Non-deterministic:
w = torch.randn(d)

# Deterministic:
g = torch.Generator().manual_seed(seed)
w = torch.randn(d, generator=g)
```
