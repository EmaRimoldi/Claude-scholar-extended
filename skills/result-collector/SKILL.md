---
name: result-collector
description: This skill should be used when the user asks to "collect results", "aggregate results", "gather outputs", "collect metrics", "build results table", "prepare data for analysis", or after experiment runs complete and before results-analysis. Scans experiment outputs, extracts metrics, assembles structured tables, detects missing runs, and organizes figures into analysis-input/.
version: 0.1.0
tags: [Research, Experiment, Data Collection, Metrics, Pipeline]
---

# Result Collector

Aggregate raw per-run experiment outputs into structured tables and artifacts ready for `results-analysis`.

Use this skill to bridge the gap between experiment execution and strict analysis. It scans `outputs/`, extracts metrics from heterogeneous formats, assembles canonical CSV/JSON tables, detects gaps in the run matrix, and organizes figures -- producing a complete `analysis-input/` directory that matches exactly what `results-analysis` Step 1 expects.

## Core contract

### This skill is responsible for
- recursively scanning experiment output directories for completed runs,
- extracting metrics from multiple output formats (JSON, CSV, pickle, torch),
- assembling structured results tables with consistent schemas,
- detecting missing or failed runs against the expected experiment matrix,
- organizing per-run figures into a canonical directory with consistent naming.

### This skill is not responsible for
- running statistical tests or significance analysis,
- generating new figures or visualizations,
- interpreting results or drawing conclusions,
- writing analysis reports or paper sections.

If the user wants statistical analysis after collection, hand off to `results-analysis`.

## Non-negotiable quality bar

1. **Never fabricate or impute metric values.**
   If a run's output is missing or unreadable, mark it as failed in the manifest and gap report. Do not fill in numbers.
2. **Preserve full numeric precision.**
   Do not round metric values during collection. Rounding is for reporting, not aggregation.
3. **One row per run in results.csv.**
   Every completed run maps to exactly one row. No aggregation in results.csv.
4. **Explicit gap accounting.**
   Every expected run that is missing or failed must appear in the gap report with a reason.
5. **Deterministic output.**
   Running the collector twice on the same outputs/ must produce identical analysis-input/ content.

## Core Features

### 1. Output Scanning

Recursively scan the `outputs/` directory for completed runs:

- **Hydra convention**: Look for `.hydra/` subdirectories containing `config.yaml` and `overrides.yaml` to identify run configurations.
- **Filename convention**: When Hydra metadata is absent, parse run directory names for structured fields (model, dataset, seed, method).
- **Completion detection**: A run is "complete" if it contains a recognized output file (metrics.json, results.csv, eval_results.json, or similar). Runs with only logs but no output files are flagged as incomplete.
- **Nested scanning**: Handle both flat (`outputs/run_001/`) and nested (`outputs/model/dataset/seed/`) directory layouts.

### 2. Metric Extraction

For each completed run, extract:

- **Primary metric value**: Identified from experiment-plan.md or from the most prominent metric in the output file.
- **Secondary metrics**: All additional numeric metrics found in the output.
- **Timing info**: Wall-clock time from logs, Hydra timestamps, or output metadata.
- **GPU memory peak**: From training logs, torch profiler output, or nvidia-smi logs if available.

Handle multiple output formats:

- **JSON**: Parse `metrics.json`, `eval_results.json`, `trainer_state.json`, or any `.json` with numeric fields.
- **CSV**: Read metric columns from `results.csv`, `eval_results.csv`, or similar tabular outputs.
- **Pickle / Torch**: Load `.pkl` or `.pt` files containing metric dictionaries when JSON/CSV are absent.
- **Log parsing**: As a fallback, extract final metric values from training log files using regex patterns.

When a metric cannot be extracted, record `null` in the output and note the failure in the run manifest.

### 3. Table Assembly

Aggregate extracted data into three canonical output files:

#### `analysis-input/results.csv`
One row per individual run. Columns:
- identifiers: `model`, `dataset`, `seed`, `method`, `ablation`
- metrics: `primary_metric`, plus one column per secondary metric
- metadata: `wall_time_seconds`, `gpu_memory_peak_mb`

See `references/output-schema.md` for the full column specification.

#### `analysis-input/summary.csv`
One row per experimental condition (aggregated across seeds). Columns:
- grouping: `model`, `dataset`, `method`, `ablation`
- aggregates: `metric_mean`, `metric_std`, `metric_ci_lower`, `metric_ci_upper`, `n_seeds`

Confidence intervals use 95% CI by default (t-distribution with n-1 degrees of freedom).

#### `analysis-input/run-manifest.json`
Array of objects, one per expected run (both completed and missing). Each entry:
- `config_path`, `output_dir`, `wall_time`, `gpu_memory_peak`, `status`, `error_message`

Status values: `"completed"`, `"failed"`, `"missing"`, `"incomplete"`.

### 4. Gap Detection

Compare completed runs against the expected run matrix:

- **Load experiment plan**: Read `experiment-plan.md` to determine the expected (model x dataset x seed x method x ablation) matrix.
- **Cross-reference**: Match each expected run against discovered outputs.
- **Classify gaps**:
  - `missing` -- no output directory found
  - `failed` -- output directory exists but run crashed (check stderr logs, error files)
  - `incomplete` -- output directory exists but final metrics are absent (possible timeout or early stop)
- **Failure diagnosis**: For failed runs, extract the last error message from logs (OOM, timeout, NaN loss, assertion error).
- **Generate gap-report.md**: Table of all missing/failed/incomplete runs with expected configuration and failure reason.

### 5. Figure Organization

Collect per-run plots into a canonical figures directory:

- **Scan for figures**: Look for `.pdf`, `.png`, `.svg` files in each run's output directory.
- **Rename consistently**: Copy to `analysis-input/figures/` using the naming convention `{model}_{dataset}_{seed}_{metric}.{ext}`.
- **Preserve originals**: Copy, never move. Original files in outputs/ remain untouched.
- **Index**: Add figure paths to the run manifest for traceability.

## Standard workflow

### 1. Locate and validate inputs

Confirm the following exist:
- `outputs/` directory with at least one run subdirectory
- `experiment-plan.md` (optional but strongly recommended for gap detection)

If `experiment-plan.md` is missing, state: "No experiment-plan.md found. Gap detection will be skipped. Only discovered runs will be collected."

### 2. Scan and classify runs

Recursively walk `outputs/`. For each subdirectory:
1. Check for Hydra `.hydra/config.yaml` -- if found, parse run configuration.
2. Otherwise, parse directory name for structured fields.
3. Check for completion markers (output files with metrics).
4. Classify as completed, failed, incomplete, or in-progress.

Report: "Found N run directories: X completed, Y failed, Z incomplete."

### 3. Extract metrics

For each completed run:
1. Identify the output format (JSON > CSV > pickle/torch > log parsing).
2. Extract primary metric, secondary metrics, timing, GPU memory.
3. Record extraction method in the manifest for reproducibility.

If extraction fails for a completed run, downgrade its status to `incomplete` and log the reason.

### 4. Assemble tables

1. Build `results.csv` from all completed runs.
2. Compute `summary.csv` by grouping on (model, dataset, method, ablation) and aggregating across seeds.
3. Build `run-manifest.json` from all discovered and expected runs.

### 5. Detect gaps

If `experiment-plan.md` is available:
1. Parse the expected run matrix.
2. Cross-reference against completed runs.
3. Generate `gap-report.md` with missing/failed/incomplete entries.

### 6. Organize figures

1. Scan each run directory for figure files.
2. Copy to `analysis-input/figures/` with consistent naming.
3. Log figure mappings in the manifest.

### 7. Final validation

Do not finish until all are true:
- [ ] `analysis-input/results.csv` exists with one row per completed run
- [ ] `analysis-input/summary.csv` exists with one row per condition
- [ ] `analysis-input/run-manifest.json` exists with entries for all runs
- [ ] no metric values were fabricated or imputed
- [ ] gap report accounts for every expected-but-missing run
- [ ] figures are copied (not moved) with consistent naming
- [ ] output is deterministic (re-running produces identical files)

## Output structure

```text
analysis-input/
├── results.csv
├── summary.csv
├── run-manifest.json
├── gap-report.md
└── figures/
    ├── transformer_cifar10_42_accuracy.pdf
    ├── transformer_cifar10_42_loss_curve.png
    └── ...
```

## Input Modes

### Mode A: Pipeline (from experiment execution)

1. **outputs/** -- directory tree of completed experiment runs
2. **experiment-plan.md** -- expected run matrix from `experiment-design`
3. Output feeds directly into `results-analysis` Step 1

### Mode B: Standalone (manual)

1. **outputs/** -- user points to a directory of experiment outputs
2. No experiment plan available -- gap detection is skipped
3. State: "No experiment-plan.md found. Collecting all discovered runs without gap detection."

## When to Use

### Scenarios for This Skill

1. **After experiment execution** -- runs are complete, need structured tables before analysis
2. **Incremental collection** -- new runs added, need to update results tables
3. **Multi-format consolidation** -- outputs are in mixed formats across runs
4. **Missing run identification** -- need to know which runs to re-launch before analysis

### Typical Workflow

```
experiment-design -> execution -> [result-collector] -> results-analysis
                                        |
                                   gap-report -> re-run missing experiments
```

**Output Files:**
- `analysis-input/results.csv` -- per-run metric table
- `analysis-input/summary.csv` -- aggregated metrics per condition
- `analysis-input/run-manifest.json` -- full run metadata
- `analysis-input/gap-report.md` -- missing/failed run inventory
- `analysis-input/figures/` -- organized per-run plots

## Integration with Other Systems

### Complete Research Workflow

```
research-ideation (Research initiation)
    |
hypothesis-formulation (Testable predictions)
    |
experiment-design (Plan experiments)
    |
Experiment execution (completed by user)
    |
result-collector (Aggregate outputs)  <-- THIS SKILL
    |
results-analysis (Strict statistical analysis)
    |
results-report (Summary reporting)
```

### Data Flow

- **Depends on**: Experiment execution outputs + `experiment-design` (`experiment-plan.md`)
- **Feeds into**: `results-analysis` (analysis-input/ matches its Step 1 inventory)
- **Hook activation**: "aggregate results", "collect metrics", "collect results", "gather outputs"
- **Command**: `/collect-results` -- scan outputs and build analysis-input/
- **Obsidian integration**: If bound, updates `Experiments/{experiment-line}.md` with collection status

### Key Configuration

- **Output format**: CSV + JSON for machine readability, Markdown for gap report
- **Confidence interval**: 95% CI using t-distribution (configurable)
- **Figure formats**: `.pdf`, `.png`, `.svg` supported
- **Naming convention**: `{model}_{dataset}_{seed}_{metric}.{ext}` for figures

## Additional Resources

### Reference Files

Detailed schema definitions, loaded on demand:

- **`references/output-schema.md`** -- Output Schema Reference
  - results.csv column specification
  - summary.csv column specification
  - run-manifest.json field specification
  - gap-report.md format specification
  - Figure naming convention

### Example Files

Complete working examples:

- **`examples/example-collection-output.md`** -- Collection Output Example
  - Sample results.csv with 3 models x 2 datasets x 3 seeds
  - Corresponding summary.csv
  - Gap report showing missing runs with failure reasons
