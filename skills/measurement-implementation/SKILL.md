---
name: measurement-implementation
description: This skill should be used when the user asks to "implement metrics", "implement measurements", "compute cosine similarity", "add statistical tests", "analytical reference", "compare to OLS", "significance testing", "effect size", or after project-scaffold creates src/metrics/ and before experiment-runner executes runs. Implements core measurements, analytical references, comparison functions, and statistical tests for experiment execution.
version: 0.1.0
tags: [Research, Metrics, Statistics, Measurement, Analytical Reference]
---

# Measurement Implementation

Implements core measurements, analytical references, comparison functions, and statistical tests. For each hypothesis in `hypotheses.md` and each metric in `experiment-plan.md`, this skill produces production-ready, numerically stable code that registers into the MetricFactory from `project-scaffold`.

## Core Features

### 1. Empirical Metric Implementation

For each metric listed in `experiment-plan.md`, produce a function that takes model outputs or activations and computes the metric:

- **Classification metrics**: Accuracy, balanced accuracy, F1 (macro/micro/weighted), AUC-ROC (one-vs-rest for multiclass)
- **Similarity metrics**: Cosine similarity (numerically stable: handle zero vectors, eps clamping)
- **Representational similarity**: CKA (linear and RBF kernel), RSA (Representational Similarity Analysis), probing accuracy (linear probe on frozen representations)
- **Scaling law fits**: Power-law regression on log-log data (y = a * x^b), with R^2 goodness-of-fit
- **Information-theoretic measures**: Shannon entropy, mutual information estimates (binning-based and KSG estimator)
- **All metrics register via `@register_metric`** into the MetricFactory from `project-scaffold`

Each metric implementation must include:
- Type hints on all parameters and return values
- Docstring with mathematical definition
- Input validation (shape checks, dtype checks)
- Return dict with: `value`, `ci_lower`, `ci_upper`, `p_value` (if applicable), `effect_size` (if applicable)

### 1b. Metric Definition Requirements

For every metric reported in the paper:

1. **Mathematical definition**: Write the formula explicitly. If using a library implementation, cite which function and version.
2. **Well-definedness check**: Is this metric well-defined for your model type? (e.g., perplexity is not standard for masked LMs — use pseudo-log-likelihood and DEFINE it explicitly).
3. **Cross-condition comparability**: If the same metric is compared across conditions that use different underlying measures (e.g., MCC vs. accuracy), you CANNOT pool them in a single statistical test. Either:
   a. Normalize to a common scale (e.g., delta from baseline, z-score, rank).
   b. Run separate analyses per metric type.
   c. Use a metric that IS comparable (e.g., always use accuracy, or always use macro-F1).
4. **Reproduction recipe**: Someone reading the paper must be able to recompute every number. If using non-standard metrics, provide code or pseudocode.

Include the metric definition table in `src/metrics/README.md`:

| Metric | Formula | Library | Well-defined? | Comparable across conditions? |
|--------|---------|---------|--------------|-------------------------------|
| [name] | [formula or reference] | [function, version] | [yes/no + note] | [yes/no + note] |

### 2. Analytical Reference Implementation

If the hypothesis compares model behavior to a known algorithm, implement that algorithm's analytical solution:

- Read the "Mathematical Framework" section from `hypotheses.md`
- Look up the formula in the **reference catalog** (`references/analytical-reference-catalog.md`)
- Implement in PyTorch/NumPy with correct numerical handling
- Examples:
  - OLS solution: beta = (X^T X)^{-1} X^T y (via `torch.linalg.lstsq`)
  - Gradient descent update rule for linear regression with MSE loss
  - Ridge regression: beta = (X^T X + lambda I)^{-1} X^T y
  - Kernel regression (Nadaraya-Watson): weighted average with Gaussian kernel
  - Bayes-optimal classifier: for Gaussian class-conditionals with known parameters
  - Neural Tangent Kernel prediction: linearized model prediction
  - Scaling law fits: power-law regression on log-log data
- If no analytical reference is needed (purely empirical hypothesis), note this in a comment and skip

Output: one file per analytical reference in `src/metrics/analytical/`, each registered via `@register_metric` with prefix `analytical_`.

### 3. Comparison Functions

Implement the function that compares an empirical measurement to an analytical reference (or baseline):

- **Point comparison**: Cosine similarity between two vectors, correlation coefficient
- **Distribution comparison**: KL divergence (with smoothing), Wasserstein distance (via `scipy.stats.wasserstein_distance`)
- **Curve comparison**: MSE between learning curves, Pearson/Spearman correlation between scaling curves
- **Threshold comparison**: "Is metric > threshold?" with bootstrap CI for the difference

Each comparison function returns a standardized dict:
```python
{
    "comparison_type": "point" | "distribution" | "curve" | "threshold",
    "value": float,          # the comparison statistic
    "p_value": float | None, # if a test was performed
    "ci_lower": float,       # 95% CI lower bound
    "ci_upper": float,       # 95% CI upper bound
    "effect_size": float | None,
    "interpretation": str,   # human-readable one-line summary
}
```

### 4. Statistical Test Selection and Implementation

Based on the experimental design from `experiment-plan.md`, select and implement the appropriate tests:

- **Paired vs. unpaired**: Same model evaluated on different conditions --> paired; different models --> unpaired
- **Parametric vs. nonparametric**: Check normality assumption with Shapiro-Wilk; default to nonparametric if n < 30
- **Multiple comparisons**: Apply Bonferroni or Holm-Bonferroni correction when testing multiple hypotheses simultaneously

Implement the following tests (see `references/statistical-test-selection.md`):

| Test | When to Use |
|------|-------------|
| Paired t-test | Paired, normal, n >= 30 |
| Wilcoxon signed-rank | Paired, non-normal or n < 30 |
| Bootstrap CI | Any setting, nonparametric, flexible |
| Permutation test | Exact test, no distributional assumptions |
| Mann-Whitney U | Unpaired, non-normal or n < 30 |
| Independent t-test | Unpaired, normal, n >= 30 |

Always report:
- Test statistic
- p-value (two-sided by default)
- Effect size: Cohen's d (parametric) or rank-biserial correlation (nonparametric)
- 95% confidence interval
- Multiple comparison correction applied (if any)

### 5. Numerical Stability

Enforce safe computation throughout all implementations:

- **Cosine similarity**: Use `torch.nn.functional.cosine_similarity` with `eps` parameter, or manual computation with norm clamping: `norm = max(||v||, eps)`
- **Matrix inversion**: Use `torch.linalg.lstsq` instead of explicit inverse for OLS; use `torch.linalg.solve` for systems with known positive-definite matrices
- **Log-space for probabilities**: Compute `log_softmax` instead of `softmax` then `log`; use `torch.logsumexp` for log-space addition
- **Condition number checks**: Before matrix operations, check `torch.linalg.cond(A)` and warn if > 1e10
- **NaN/Inf detection**: Wrap metric computation with a guard that checks for NaN/Inf in inputs and outputs; raise informative errors with the source of the issue
- **Floating-point precision**: Use fp64 for statistical tests and small-sample computations; fp32 is acceptable for large-batch forward passes

See `references/numerical-stability.md` for complete guidelines.

## Execution Procedure

When this skill is triggered, follow these steps in order:

### Step 1: Read Inputs

1. Check for `experiment-plan.md` in the project root. If found, extract the **Metrics** section to determine which metrics to implement.
2. Check for `hypotheses.md` in the project root. If found, extract the **Mathematical Framework** section to determine which analytical references are needed.
3. Check that `src/metrics/__init__.py` exists with MetricFactory wiring (from `project-scaffold`). If not, advise the user to run `project-scaffold` first.

### Step 2: Implement Metrics

For each metric in the plan:
1. Identify the metric type (classification, similarity, scaling, information-theoretic).
2. Look up the implementation pattern in this skill's Core Features section.
3. Write the implementation into the appropriate file in `src/metrics/`.
4. Register via `@register_metric("metric_name")`.
5. Include a unit test function `test_<metric_name>()` at the bottom of the file that verifies correctness on a known input.

### Step 3: Implement Analytical References (if needed)

For each analytical reference identified in `hypotheses.md`:
1. Look up the formula in `references/analytical-reference-catalog.md`.
2. Create a file in `src/metrics/analytical/` with the implementation.
3. Add a correctness test: e.g., for OLS, verify that the solution satisfies the normal equations.
4. If the hypothesis is purely empirical, skip this step and add a comment in `src/metrics/analytical/__init__.py`.

### Step 4: Implement Comparisons

For each hypothesis, implement the comparison function that connects the empirical measurement to the analytical reference or baseline:
1. Determine the comparison type from the hypothesis structure (point, distribution, curve, or threshold).
2. Write the comparison into `src/metrics/comparison.py`.
3. Each comparison returns the standardized dict described in Core Features section 3.

### Step 5: Wire Statistical Tests

1. Read the experiment plan to determine the experimental design (paired/unpaired, number of conditions, number of seeds).
2. Use the decision tree from `references/statistical-test-selection.md` to select the appropriate test.
3. Implement the test selection logic in `src/metrics/statistical_tests.py` as a `select_and_run_test()` function.
4. If multiple hypotheses are tested, configure Holm-Bonferroni correction by default.

### Step 6: Verify

1. Run all unit test functions in the generated files.
2. Verify that all metrics are discoverable via MetricFactory: `MetricFactory("metric_name")` should not raise.
3. Check numerical stability: run each metric with edge-case inputs (zero vectors, single element, very large values).

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Experiment plan** -- from `experiment-design` output (`experiment-plan.md`), specifically the Metrics section
2. **Hypotheses** -- from `hypothesis-formulation` output (`hypotheses.md`), specifically the Mathematical Framework section
3. **Project scaffold** -- from `project-scaffold` output (`src/metrics/` directory with MetricFactory wiring)

The skill reads:
- `experiment-plan.md` --> list of metrics to implement
- `hypotheses.md` --> analytical references needed
- `src/metrics/__init__.py` --> MetricFactory pattern to follow

### Mode B: Standalone (manual)

1. **Metric description** -- user describes what they want to measure
2. **Comparison description** -- user describes what they want to compare against
3. **Statistical requirements** -- user specifies significance level, number of comparisons

When running in Mode B, state: "No experiment-plan.md or hypotheses.md found. Implementing metrics from user description."

The skill asks clarifying questions if:
- The metric is ambiguous (e.g., "accuracy" without specifying balanced vs. standard)
- The comparison type is unclear (empirical vs. analytical)
- The number of comparisons is not specified (needed for multiple comparison correction)

## Outputs

### Files Created in `src/metrics/`

```
src/metrics/
├── __init__.py              # MetricFactory (from project-scaffold, not modified)
├── classification.py        # Accuracy, balanced accuracy, F1, AUC-ROC
├── similarity.py            # Cosine similarity, CKA, RSA
├── scaling.py               # Power-law fits, scaling curve metrics
├── information.py           # Entropy, mutual information
├── comparison.py            # Point, distribution, curve, threshold comparisons
├── statistical_tests.py     # All statistical tests with effect sizes
├── numerical_utils.py       # Shared numerical stability utilities
└── analytical/
    ├── __init__.py
    ├── ols.py               # Ordinary Least Squares
    ├── ridge.py             # Ridge regression
    ├── gradient_descent.py  # GD update rules
    ├── kernel_regression.py # Nadaraya-Watson
    └── ...                  # One file per analytical reference needed
```

### What Each File Contains

- **classification.py**: One class per metric, each decorated with `@register_metric`, each returning the standardized dict
- **similarity.py**: Numerically stable implementations with eps handling
- **scaling.py**: Power-law fits and scaling curve metrics with R^2 goodness-of-fit
- **information.py**: Entropy (Shannon), mutual information (binning and KSG), with appropriate bias correction
- **comparison.py**: Functions that take (empirical, reference) and return comparison dict
- **statistical_tests.py**: All tests plus a `select_test()` function that auto-selects based on data properties, and a `run_all_tests()` function for batch hypothesis testing with correction
- **numerical_utils.py**: `check_nan_inf()`, `safe_cosine_similarity()`, `condition_number_check()`, `to_fp64()`
- **analytical/*.py**: One file per analytical reference, each registered with `analytical_` prefix

### Standardized Return Format

Every metric function returns a dict. The minimum required keys are:

```python
{
    "value": float,       # The primary metric value
    "ci_lower": float,    # Lower bound of 95% confidence interval
    "ci_upper": float,    # Upper bound of 95% confidence interval
}
```

Optional keys (included when applicable):

```python
{
    "p_value": float,          # p-value from significance test (if performed)
    "effect_size": float,      # Effect size measure
    "effect_size_type": str,   # "cohens_d", "rank_biserial", "eta_squared"
    "n": int,                  # Number of observations
    "details": dict,           # Additional metric-specific information
}
```

This contract is enforced so that `result-collector` and `experiment-runner` can consume metrics uniformly without knowing which specific metric was called.

## When to Use

### Scenarios for This Skill

1. **After project scaffold** -- `src/metrics/` exists with MetricFactory, ready to fill with implementations
2. **After hypothesis formulation** -- hypotheses specify what analytical references are needed
3. **Before experiment runner** -- metrics must exist before experiments can call them
4. **Standalone metric implementation** -- user needs a specific metric implemented correctly
5. **Adding statistical tests** -- user needs to test significance of results

### Typical Workflow

```
hypothesis-formulation -> experiment-design -> project-scaffold -> [measurement-implementation] -> experiment-runner
                                                                          |
                                                                    setup-validation (verify metrics work)
```

**Output Files:**
- `src/metrics/*.py` -- All metric implementations
- `src/metrics/analytical/*.py` -- All analytical reference implementations

## Integration with Other Systems

### Complete Pipeline

```
hypotheses.md (Mathematical Framework section)
    |
experiment-plan.md (Metrics section)
    |
project-scaffold (Creates src/metrics/ with MetricFactory)
    |
measurement-implementation (Fill src/metrics/)  <-- THIS SKILL
    |
    ├── setup-validation (Verify metrics produce correct values)
    ├── experiment-runner (Call metrics during each run)
    └── result-collector (Store metric values as raw data)
```

### Data Flow

- **Depends on**: `project-scaffold` (writes into `src/metrics/`), `hypothesis-formulation` (reads Mathematical Framework section), `model-setup` (gets activations to measure)
- **Feeds into**: `experiment-runner` (metrics called during each run), `result-collector` (metric values are the raw data), `setup-validation` (measurement correctness checks)
- **Hook activation**: Context-aware keyword trigger in `skill-forced-eval.js` on: "metric", "analytical", "cosine similarity", "statistical test", "measurement", "significance"
- **Command**: `/implement-metrics`
- **Obsidian integration**: If bound, writes measurement implementation notes to `Experiments/` with metric specifications

### Key Configuration

- **Registration pattern**: `@register_metric` decorator from `project-scaffold` MetricFactory
- **Return format**: Standardized dict with `value`, `ci_lower`, `ci_upper`, `p_value`, `effect_size`
- **Numerical precision**: fp64 for statistics, fp32 for forward passes
- **Default significance**: alpha = 0.05, two-sided tests, Holm-Bonferroni correction for multiple comparisons
- **Bootstrap defaults**: n_resamples = 10000, seed = 42 for reproducibility
- **Permutation defaults**: n_permutations = 10000
- **File size limit**: Each file follows the 200-400 line limit from `coding-style.md`; split into multiple files if a single file exceeds 400 lines

## Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| MetricFactory lookup fails | Metric not registered | Check `@register_metric` decorator is applied and `import_modules()` auto-discovery includes the file |
| NaN in cosine similarity | Zero-norm vector | Use `safe_cosine_similarity()` from `numerical_utils.py` |
| Statistical test gives p=0.0 | Exact zero from scipy | Use permutation test instead, or report as p < 1/n_permutations |
| Bootstrap CI is [NaN, NaN] | All bootstrap samples identical | Check that input data has variance > 0 |
| OLS solution diverges from expectation | Ill-conditioned X | Check condition number; switch to ridge regression |
| Comparison function returns unexpected sign | Convention mismatch | Verify which direction is "better" for the metric |

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/analytical-reference-catalog.md`** -- Analytical Reference Catalog
  - Canonical PyTorch implementations for common analytical references
  - OLS, ridge regression, gradient descent, kernel regression, Bayes-optimal, NTK, scaling laws
  - Each entry: mathematical definition, implementation, stability notes, when to use, common mistakes

- **`references/numerical-stability.md`** -- Numerical Stability Guide
  - Safe cosine similarity (eps clamping, zero-vector handling)
  - Safe matrix operations (lstsq vs. inverse, condition number checks)
  - Log-space computation for probabilities
  - NaN/Inf detection and handling
  - Floating-point precision guidelines

- **`references/statistical-test-selection.md`** -- Statistical Test Selection Guide
  - Decision tree for test selection
  - Implementation of each common test
  - Effect size computation
  - Multiple comparison correction
  - Bootstrap confidence intervals
  - Common mistakes

### Example Files

Complete working examples:

- **`examples/example-metric-implementation.py`** -- Metric Implementation Example
  - Complete `@register_metric` class implementing cosine similarity
  - Numerically stable computation
  - Returns standardized dict with value, CI, p-value, effect size

- **`examples/example-analytical-reference.py`** -- Analytical Reference Example
  - OLS analytical solution and GD update implementation
  - Comparison between model output and analytical prediction
  - Bootstrap CI on the comparison metric
  - Full pipeline: generate data, compute OLS, extract model output, compare
