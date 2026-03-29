---
name: run-experiment
description: Execute the experiment matrix via SLURM. Submit jobs, monitor progress, handle failures, evaluate phase gates, and update experiment-state.json.
args:
  - name: phase
    description: Which phase to run (defaults to next pending phase from experiment-state.json)
    required: false
tags: [Research, Execution, SLURM, Experiment]
---

# Run Experiment Command

## PRE-FLIGHT CHECKS (mandatory before submitting ANY job)

Before submitting SLURM jobs, verify:

1. **Data cached**: Run `python -c "import os; os.environ['HF_DATASETS_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'; <load each dataset and model>"` — must succeed
2. **Dry run passes**: Run `python -m src.main --dry-run` on the login node — must complete without errors
3. **SLURM accessible**: Run `sinfo -s` — must show available partitions
4. **Project directory exists**: $PROJECT_DIR/src/, $PROJECT_DIR/configs/ must exist with code

If ANY check fails, do NOT submit jobs. Fix the issue first.

## JOB BATCHING STRATEGY

Do NOT submit one SLURM job per experimental condition. Instead:

1. **Count total runs**: conditions x seeds = N
2. **If N < 20**: submit as a single GPU job that iterates internally
3. **If 20 <= N < 100**: group by task type (one job per task, each iterates over strategies x seeds)
4. **If N >= 100**: group by task type AND split strategies into chunks of ~20 runs per job

Each job script must:
- Iterate over its assigned conditions in a Python loop (not separate SLURM submissions)
- Save results incrementally (after each condition, not just at the end)
- Log progress so partial results are recoverable if the job times out

Example for 15 strategies x 3 tasks x 5 seeds = 225 runs:
- Submit 3 jobs (one per task), each running 15 strategies x 5 seeds = 75 runs internally
- NOT 225 separate SLURM submissions

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Experiment outputs → `$PROJECT_DIR/results/`
- Experiment logs → `$PROJECT_DIR/logs/`
- `experiment-state.json` → `$PROJECT_DIR/experiment-state.json`

Never write experiment outputs to the repository root.

Execute the experiment sweep on the cluster.

## Goal

Activates the `experiment-runner` skill to submit SLURM jobs, monitor progress, handle failures (OOM/NaN/timeout/preemption), evaluate phase gates, and update experiment-state.json.

## Usage

```bash
/run-experiment              # runs next pending phase
/run-experiment phase=2      # runs specific phase
```

## Workflow

1. Read compute-plan.md and SLURM scripts from cluster/
2. Activate `experiment-runner` skill
3. Submit jobs, monitor, handle failures
4. After phase completion: evaluate gate, update experiment-state.json
5. Report: completed/failed/remaining runs, gate decision

## Integration

- **Primary skill**: `experiment-runner`
- **Prerequisite**: `compute-planner` output (SLURM scripts), validated pipeline
- **Feeds into**: `result-collector` (outputs/ directory), `failure-diagnosis` (if gate fails)
