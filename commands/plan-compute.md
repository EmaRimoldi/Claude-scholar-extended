---
name: plan-compute
description: Estimate GPU resources, select cluster partitions, design scheduling strategy, and generate SLURM scripts for MIT Engaging or other HPC clusters.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to experiment-plan.md)
    required: false
    default: experiment-plan.md
tags: [Research, HPC, SLURM, Cluster]
---

# Plan Compute Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- `compute-plan.md` → `$PROJECT_DIR/docs/compute-plan.md`
- `cluster-profile.json` → `$PROJECT_DIR/cluster-profile.json`
- SLURM scripts → `$PROJECT_DIR/scripts/`

Never write compute plans to the repository root.

Estimate resources and generate cluster submission scripts.

## Goal

Activates the `compute-planner` skill to estimate GPU memory/time/storage, select partitions, design scheduling strategy, and generate SLURM sbatch scripts.

## Usage

```bash
/plan-compute                      # reads experiment-plan.md + validation-report.md
/plan-compute path/to/plan.md      # explicit plan file
```

## Workflow

1. Parse run matrix from experiment-plan.md (conditions × seeds). **Default: 5 seeds per condition**; do not plan 10 unless the user explicitly asked and `compute_budget_check.py` is run with `--allow-extra-seeds`.
2. Read timing data from validation-report.md (smoke test)
3. Activate `compute-planner` skill and apply **`rules/compute-budget.md`**: **1 GPU per job**, seed sweeps via **SLURM arrays**, not one job requesting `conditions × seeds` GPUs.
4. Run validation:
   ```bash
   python scripts/compute_budget_check.py --seeds <N> --conditions <C> --gpus-per-job 1
   ```
5. Write: compute-plan.md, cluster/ directory with sbatch scripts, launch.sh, monitor.sh

## MANDATORY: Venv activation in generated SLURM scripts

When generating SLURM job scripts, ALWAYS include venv activation at the top:
```bash
source /path/to/repo/.venv/bin/activate
```
Never rely on bare `python` being correct on compute nodes. Use the absolute path to the repo's `.venv` (not a relative path — SLURM jobs may run from a different CWD).

## Generated SLURM scripts must include

At the top of every generated .sh file:
```bash
# Code version: $(git rev-parse HEAD)
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Project: $PROJECT_NAME
```

## Integration

- **Primary skill**: `compute-planner`
- **Prerequisite**: `experiment-plan.md`, `validation-report.md` (smoke test timing)
- **Feeds into**: `experiment-runner` (provides SLURM scripts)
