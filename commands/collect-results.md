---
name: collect-results
description: Aggregate raw per-run outputs into structured tables for results-analysis. Produces results.csv, summary.csv, run-manifest.json, and gap report.
args:
  - name: outputs_dir
    description: Path to outputs directory (defaults to outputs/)
    required: false
    default: outputs
tags: [Research, Data, Analysis]
---

# Collect Results Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Result tables → `$PROJECT_DIR/results/tables/`
- Aggregated data → `$PROJECT_DIR/results/`

Never write result files to the repository root.

Aggregate experiment outputs into analysis-ready tables.

## Goal

Activates the `result-collector` skill to scan outputs/, extract metrics from each run, assemble structured CSV/JSON tables, and detect missing runs.

## Usage

```bash
/collect-results                   # scans outputs/
/collect-results outputs/phase2    # specific directory
```

## Workflow

1. Scan outputs/ for completed runs
2. Activate `result-collector` skill
3. Write: analysis-input/results.csv, summary.csv, run-manifest.json, gap-report.md

## Integration

- **Primary skill**: `result-collector`
- **Prerequisite**: `experiment-runner` output (completed runs in outputs/)
- **Feeds into**: `results-analysis` (consumes analysis-input/)
