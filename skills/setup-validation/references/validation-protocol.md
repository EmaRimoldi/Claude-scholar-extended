# Validation Protocol

Complete pre-flight checklist for experiment pipelines. Run all applicable checks before committing to a full experiment sweep.

## Check 1: Data Integrity

### 1.1 Shape Check

```python
def check_data_shapes(dataset, expected_shapes: dict):
    """Verify dataset output shapes match expectations."""
    sample = dataset[0]
    for key, expected in expected_shapes.items():
        actual = sample[key].shape
        assert actual == expected, f"{key}: expected {expected}, got {actual}"
```

**Pass**: All tensor shapes match the config specification.
**Fail**: Shape mismatch — check dataset `__getitem__` implementation, especially sequence formatting and padding.

### 1.2 Distribution Check

```python
def check_distributions(dataset, n_samples=1000):
    """Verify statistical properties of generated data."""
    samples = torch.stack([dataset[i]["input"] for i in range(n_samples)])
    mean, std = samples.mean(), samples.std()
    # For N(0,I) data: mean ≈ 0, std ≈ 1
    assert abs(mean) < 0.1, f"Mean {mean:.3f} too far from 0"
    assert abs(std - 1.0) < 0.2, f"Std {std:.3f} too far from 1"
```

**Pass**: Sample statistics within tolerance of specification.
**Fail**: Wrong distribution — check sampling code, random seed, or parameterization.

### 1.3 Label Verification

Manually compute labels for 3-5 samples:
1. Take sample input x and task parameters w
2. Hand-compute y = f(x, w) using the specified formula
3. Compare against dataset output y
4. Must match within floating-point tolerance (1e-6)

### 1.4 Reproducibility Check

```python
def check_reproducibility(dataset_cls, config, seed=42):
    """Same seed must produce identical data."""
    d1 = dataset_cls(config, seed=seed)
    d2 = dataset_cls(config, seed=seed)
    for i in range(10):
        for key in d1[i]:
            assert torch.equal(d1[i][key], d2[i][key]), f"Sample {i} key {key} differs"
```

### 1.5 No Data Leakage

For train/test splits: verify no sequence appears in both sets. For ICL tasks: verify task parameters (w vectors) are independent across episodes.

## Check 2: Model Loading

### 2.1 Non-trivial Output

```python
def check_model_output(model, sample_input):
    """Model must produce non-trivial, finite output."""
    with torch.no_grad():
        output = model(sample_input)
    assert not torch.isnan(output).any(), "Model output contains NaN"
    assert not torch.isinf(output).any(), "Model output contains Inf"
    assert output.abs().sum() > 0, "Model output is all zeros"
```

### 2.2 Hook Extraction

```python
def check_hooks(model, hook_targets, sample_input):
    """Verify hooks extract tensors of expected shape."""
    cache = {}
    hooks = []
    for name in hook_targets:
        layer = dict(model.named_modules())[name]
        hook = layer.register_forward_hook(
            lambda m, i, o, n=name: cache.__setitem__(n, o.detach())
        )
        hooks.append(hook)

    with torch.no_grad():
        model(sample_input)

    for h in hooks:
        h.remove()

    for name in hook_targets:
        assert name in cache, f"Hook for {name} did not fire"
        assert not torch.isnan(cache[name]).any(), f"Hook output {name} contains NaN"
```

### 2.3 Device Consistency

Verify model parameters and input data are on the same device. A common bug: model on GPU, data on CPU (or vice versa).

## Check 3: Measurement Correctness

### 3.1 Identity Test

For similarity metrics: `metric(x, x)` must equal 1.0 (or 0.0 for distance metrics).

### 3.2 Known-Answer Test

For analytical references: compute on a case with a known closed-form answer.

Example for OLS: generate X, w_true, y = Xw_true (no noise). The OLS solution must recover w_true exactly (within float precision).

```python
def check_ols_implementation(ols_fn):
    """OLS on noise-free data must recover true parameters."""
    d = 5
    X = torch.randn(100, d)
    w_true = torch.randn(d, 1)
    y = X @ w_true
    w_hat = ols_fn(X, y)
    error = (w_hat - w_true).norm() / w_true.norm()
    assert error < 1e-5, f"OLS recovery error: {error:.2e}"
```

### 3.3 Numerical Edge Cases

Test metrics with: zero vectors, very large values (1e10), very small values (1e-10), near-singular matrices.

## Check 4: Ablation Verification

### 4.1 Zero Check

After zero-ablating a component, verify its output is actually zero:

```python
def check_ablation_zeros(model, ablated_component, sample_input):
    """Ablated component must produce zero output."""
    cache = {}
    hook = ablated_component.register_forward_hook(
        lambda m, i, o: cache.__setitem__("out", o.detach())
    )
    with torch.no_grad():
        model(sample_input)
    hook.remove()
    assert cache["out"].abs().max() < 1e-10, "Ablated component not zeroed"
```

### 4.2 Restoration Check

```python
def check_ablation_reversible(model, ablation_context, sample_input):
    """Output must be identical before and after reversible ablation."""
    with torch.no_grad():
        out_before = model(sample_input).clone()
    with ablation_context:
        out_during = model(sample_input).clone()
    with torch.no_grad():
        out_after = model(sample_input)
    assert torch.equal(out_before, out_after), "Ablation not properly reversed"
    assert not torch.equal(out_before, out_during), "Ablation had no effect"
```

## Check 5: Baseline Replication

### Protocol

1. Identify the published baseline result (paper, table, metric value)
2. Run the pipeline with the same configuration
3. Compare: `|reproduced - published| / published < tolerance`
4. Default tolerance: 1% for accuracy, 5% for loss, 0.05 absolute for correlation/similarity

### If No Published Baseline

Run a trivial baseline (random predictions, majority class) and verify it matches the expected floor (e.g., 50% for balanced binary classification, 1/C for C-class classification).

## Check 6: End-to-End Smoke Test

### Protocol

1. Select 1 model, 1 dataset, 1 seed, no ablations
2. Run the full pipeline: data → model → metric → save
3. Time the run (wall clock)
4. Verify output file exists with expected format
5. Verify metric value is plausible (not NaN, not exactly 0 or 1 unless expected)
6. Record timing for `compute-planner`

### Timing Data Format

```json
{
  "model": "gpt2-medium",
  "dataset": "linear_regression",
  "device": "cuda:0",
  "gpu_model": "NVIDIA A100",
  "wall_time_seconds": 45.2,
  "peak_gpu_memory_mb": 3200,
  "num_forward_passes": 10000,
  "time_per_forward_pass_ms": 4.52
}
```

## Interpreting Failures

| Check Failed | Likely Cause | Fix |
|---|---|---|
| Shape mismatch | Wrong data formatting or model config | Check `__getitem__` and config dimensions |
| Distribution wrong | Wrong sampling function or parameterization | Check `torch.randn` vs `torch.rand`, scale parameters |
| NaN in model output | Numerical overflow, bad input scaling | Check input normalization, dtype, learning rate |
| Hook not firing | Hook on container module, not leaf | Use `named_modules()` to find the correct leaf module |
| Ablation no effect | Wrong component targeted | Verify component index matches the intended head/layer |
| Baseline mismatch | Different preprocessing or hyperparameters | Check exact configuration matches published setup |
| Smoke test crash | Missing dependency, path error | Check imports, file paths, device placement |

## When to Skip Checks

- **No published baseline**: Skip Check 5.3 (published replication), use trivial baseline instead.
- **No ablations in experiment plan**: Skip Check 4 entirely.
- **No analytical reference**: Skip Check 3.2 (known-answer test for analytical reference).
- **CPU-only experiment**: Skip device consistency checks.
