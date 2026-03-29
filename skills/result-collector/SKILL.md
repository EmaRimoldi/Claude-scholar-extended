---
name: result-collector
description: This skill should be used when the user asks to "collect results", "aggregate results", "gather outputs", "collect metrics", "build results table", "prepare data for analysis", or after experiment runs complete and before results-analysis. Scans experiment outputs, extracts metrics, assembles structured tables, detects missing runs, and organizes figures into analysis-input/.
version: 0.1.0
tags: [Research, Experiment, Data Collection, Metrics, Pipeline]
---

# Result Collector

Aggregate raw per-run experiment outputs into structured tables and artifacts ready for `results-analysis`.

Use this skill to bridge the gap between experiment execution and strict analysis. It scans `outputs/`, extracts metrics from heterogeneous formats, assembles canonical CSV/JSON tables, detects gaps in the run matrix, and organizes figures -- producing a complete `analysis-input/` directory that matches exactly what `results-analysis` Step 1 expects.

## Deterministic scripts (prefer over agent reasoning)

When the project was scaffolded with `project-scaffold`, deterministic scripts already handle the most common collection tasks. **Use them first**; fall back to agent reasoning only for non-standard formats or layouts.

| Task | Script | Invocation |
|------|--------|------------|
| Metric aggregation (Hydra outputs + SLURM log fallback) | `scripts/aggregate_metrics.py` | `make collect` or `python scripts/aggregate_metrics.py [--slurm-log FILE]` |
| Experiment state update | `scripts/update_experiment_state.py` | `python scripts/update_experiment_state.py --status collecting --job-id <ID>` |

See `project-scaffold/references/template-catalog.md` sections L and O for full script source and configuration.

**When to use the scripts**: The project has standard Hydra `outputs/` layout or SLURM logs with `=== <run_name>` headers and `val {dict}` metric lines.

**When to fall back to agent reasoning**: Non-standard output formats (pickle, torch, custom log patterns), nested multi-level directory layouts not matching Hydra convention, or when gap detection against `experiment-plan.md` is needed.

After running `make collect`, this skill's remaining value is gap detection, figure organization, and summary table computation — steps the deterministic script does not cover.

## Core contract

### This skill is responsible for
- running `make collect` (or `scripts/aggregate_metrics.py`) as the first step for standard projects,
- recursively scanning experiment output directories for completed runs when the deterministic script is insufficient,
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

## Deterministic Script

The procedural pipeline (scanning, extraction, assembly, gap detection) is implemented in `scripts/collect_results.py`. **Use this script first**; fall back to agent reasoning only for non-standard formats.

```bash
python scripts/collect_results.py \
    --results-dir results/ \
    --experiment-plan docs/experiment-plan.md \
    --output-dir analysis-input/
```

The script handles: recursive output scanning (Hydra + filename conventions), metric extraction (JSON > CSV > log fallback), table assembly (`results.csv` + `summary.csv` with t-distribution CI), gap detection against the experiment plan, figure organization, and run manifest generation.

Run with `--dry-run` to preview without writing files. Run with `--help` for all options.

**When to fall back to agent reasoning**: Non-standard output formats (pickle, torch, custom log patterns), nested multi-level directory layouts not matching conventions, or when the script reports errors it cannot resolve.

After running the script, verify the outputs match the quality bar above.

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
