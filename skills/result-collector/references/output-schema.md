# Output Schema Reference

Canonical schemas for all files produced by `result-collector`.

## results.csv

One row per individual experiment run. No aggregation -- every completed run is a separate row.

### Required columns

| Column | Type | Description |
|--------|------|-------------|
| `model` | string | Model identifier (e.g., `transformer`, `resnet50`, `gpt2-small`) |
| `dataset` | string | Dataset identifier (e.g., `cifar10`, `imagenet`, `wikitext-103`) |
| `seed` | integer | Random seed for this run |
| `method` | string | Method or variant name (e.g., `proposed`, `baseline`, `full-finetune`) |
| `ablation` | string | Ablation label, or `none` for non-ablation runs |
| `primary_metric` | float | Value of the primary evaluation metric |

### Optional metric columns

Additional columns are added dynamically based on extracted secondary metrics. Common examples:

| Column | Type | Description |
|--------|------|-------------|
| `accuracy` | float | Classification accuracy |
| `f1_score` | float | F1 score (macro/micro as specified) |
| `loss` | float | Final evaluation loss |
| `perplexity` | float | Language model perplexity |
| `auc_roc` | float | Area under ROC curve |
| `bleu` | float | BLEU score for generation tasks |
| `wall_time_seconds` | float | Total training + evaluation time in seconds |
| `gpu_memory_peak_mb` | float | Peak GPU memory usage in megabytes |

### Column ordering

1. Identifier columns: `model`, `dataset`, `seed`, `method`, `ablation`
2. Primary metric: `primary_metric`
3. Secondary metrics: alphabetical order
4. Metadata: `wall_time_seconds`, `gpu_memory_peak_mb`

### Null handling

- Missing metric values are recorded as empty cells (not `0`, not `NaN`, not `N/A`).
- The corresponding run-manifest entry must explain why the value is missing.

---

## summary.csv

One row per experimental condition, aggregated across seeds. Computed from results.csv.

### Required columns

| Column | Type | Description |
|--------|------|-------------|
| `model` | string | Model identifier |
| `dataset` | string | Dataset identifier |
| `method` | string | Method or variant name |
| `ablation` | string | Ablation label, or `none` |
| `metric_mean` | float | Mean of `primary_metric` across seeds |
| `metric_std` | float | Standard deviation of `primary_metric` across seeds |
| `metric_ci_lower` | float | Lower bound of 95% confidence interval |
| `metric_ci_upper` | float | Upper bound of 95% confidence interval |
| `n_seeds` | integer | Number of completed seeds for this condition |

### Confidence interval computation

Default: 95% CI using the t-distribution.

```
ci = t(alpha/2, df=n-1) * std / sqrt(n)
metric_ci_lower = metric_mean - ci
metric_ci_upper = metric_mean + ci
```

When `n_seeds < 3`, confidence intervals are not computed. Set `metric_ci_lower` and `metric_ci_upper` to empty.

### Aggregation rules

- Group by (`model`, `dataset`, `method`, `ablation`).
- Only include runs with `status == "completed"` from the manifest.
- If a condition has zero completed runs, omit it from summary.csv entirely.

---

## run-manifest.json

JSON array of objects. One entry per run (both completed and expected-but-missing).

### Per-run fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | Unique identifier: `{model}_{dataset}_{seed}_{method}_{ablation}` |
| `config_path` | string | yes | Path to Hydra config or parsed directory name |
| `output_dir` | string | yes | Path to the run's output directory |
| `status` | string | yes | One of: `completed`, `failed`, `missing`, `incomplete` |
| `wall_time` | float | no | Wall-clock time in seconds (null if unavailable) |
| `gpu_memory_peak` | float | no | Peak GPU memory in MB (null if unavailable) |
| `error_message` | string | no | Last error message for failed/incomplete runs (null if completed) |
| `metrics_source` | string | no | File from which metrics were extracted (e.g., `metrics.json`) |
| `figures` | array | no | List of figure file paths copied to analysis-input/figures/ |

### Status definitions

| Status | Meaning |
|--------|---------|
| `completed` | Run finished and produced extractable metrics |
| `failed` | Run directory exists but the process crashed before producing metrics |
| `incomplete` | Run directory exists with partial output but final metrics are absent |
| `missing` | Expected by experiment-plan.md but no output directory found |

### Example entry

```json
{
  "run_id": "transformer_cifar10_42_proposed_none",
  "config_path": "outputs/transformer/cifar10/seed_42/.hydra/config.yaml",
  "output_dir": "outputs/transformer/cifar10/seed_42/",
  "status": "completed",
  "wall_time": 3842.5,
  "gpu_memory_peak": 11234.0,
  "error_message": null,
  "metrics_source": "metrics.json",
  "figures": [
    "analysis-input/figures/transformer_cifar10_42_accuracy.pdf",
    "analysis-input/figures/transformer_cifar10_42_loss_curve.png"
  ]
}
```

---

## gap-report.md

Markdown document listing all runs that were expected but not successfully completed.

### Format

```markdown
# Gap Report

Generated: {ISO-8601 timestamp}
Expected runs: {N}
Completed: {X}
Missing/Failed/Incomplete: {Y}

## Missing Runs

| Model | Dataset | Seed | Method | Ablation | Status | Reason |
|-------|---------|------|--------|----------|--------|--------|
| ... | ... | ... | ... | ... | missing/failed/incomplete | ... |

## Failure Details

### {run_id}
- **Status**: failed
- **Output directory**: outputs/...
- **Last error**: {extracted error message}
- **Log tail**: {last 5 lines of stderr or training log}

## Recommended Actions

- Re-run {N} missing experiments with: {suggested command or config}
- Investigate OOM failures: consider reducing batch size or enabling gradient checkpointing
- Check timeout failures: consider increasing wall-time limit
```

### Failure reason categories

| Category | Detection method |
|----------|-----------------|
| OOM | `RuntimeError: CUDA out of memory` or `OutOfMemoryError` in logs |
| Timeout | No output file and wall time exceeds expected duration |
| NaN loss | `NaN` or `nan` detected in training loss logs |
| Assertion error | `AssertionError` in stderr |
| Missing data | `FileNotFoundError` for dataset paths |
| Unknown | Crash with no recognizable error pattern |

---

## Figure naming convention

All figures copied to `analysis-input/figures/` follow this pattern:

```
{model}_{dataset}_{seed}_{figure_type}.{ext}
```

### Components

| Component | Format | Example |
|-----------|--------|---------|
| `model` | lowercase, hyphens for compound names | `transformer`, `resnet-50` |
| `dataset` | lowercase, hyphens for compound names | `cifar10`, `imagenet-1k` |
| `seed` | integer | `42`, `123` |
| `figure_type` | lowercase, underscores for compound names | `accuracy`, `loss_curve`, `attention_map`, `confusion_matrix` |
| `ext` | original file extension | `pdf`, `png`, `svg` |

### Deduplication

If multiple figures of the same type exist for one run, append a numeric suffix:
```
transformer_cifar10_42_loss_curve_01.png
transformer_cifar10_42_loss_curve_02.png
```
