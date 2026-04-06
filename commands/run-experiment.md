---
name: run-experiment
description: Execute the experiment matrix via SLURM. Submit jobs, monitor progress, handle failures, evaluate phase gates, and update experiment-state.json.
args:
  - name: phase
    description: Optional. Use `phase=1`, `phase=2`, … to run a specific execution phase. Omit to run the next pending phase from experiment-state.json. This is not a file path — do not wrap in quotes.
    required: false
tags: [Research, Execution, SLURM, Experiment]
---

# Run Experiment Command

## PRE-FLIGHT CHECKS (mandatory before submitting ANY job)

Before submitting SLURM jobs, verify (in this order):

1. **Pre-flight validation** (MANDATORY, ~10-15 seconds):
   ```bash
   make pre-flight-validate
   # Checks: configs, Hydra syntax, imports, model init, training step, metrics
   # Exit 0 = code is syntactically correct and imports work
   ```

2. **CPU smoke test** (MANDATORY, ~1-5 minutes):
   ```bash
   make cpu-smoke-test
   # Runs: 2 training steps on CPU with real data
   # Catches: data loading errors, training loop bugs, compute_metrics failures
   # Exit 0 = code runs end-to-end on CPU
   ```

3. **Data cached**: Run `python -c "import os; os.environ['HF_DATASETS_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'; <load each dataset and model>"` — must succeed
4. **SLURM accessible**: Run `sinfo -s` — must show available partitions
5. **Project directory exists**: $PROJECT_DIR/src/, $PROJECT_DIR/configs/ must exist with code
6. **Venv Python**: Verify that the Python used in SLURM job scripts points to the venv Python (3.10+), not system Python. Check with: `head -20 cluster/job_*.sh | grep python` — must show a path containing `.venv/bin/python`, NOT bare `python`.

**Rationale**: Steps 1-2 catch 95% of failures (config errors, import bugs, training loop issues) on CPU in minutes, preventing wasted GPU time.

If ANY check fails, do NOT submit jobs. Fix the issue first.

## MANDATORY: Commit before submission

Before submitting ANY SLURM job:
1. Stage all project files: `git add projects/$PROJECT_NAME/`
2. Commit with message: `experiment: submit $PROJECT_NAME runs — $N_JOBS jobs, $N_RUNS total runs`
3. Record the commit hash in experiment-state.json under `code_version`
4. Include the commit hash in each SLURM job script as a comment at the top

This ensures every experiment run is traceable to a specific code version, failed jobs can be reproduced, and results can be linked to code changes.

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

```text
/run-experiment              # runs next pending phase from experiment-state.json
/run-experiment phase=2      # runs execution phase 2 explicitly (numeric; not a path)
```

There is **no** required string in quotes. The only optional argument is **`phase=<integer>`**, matching the phased structure in `experiment-plan.md` / `experiment-state.json`. See [docs/PIPELINE_INPUTS.md](../docs/PIPELINE_INPUTS.md) for prerequisites and a minimal project layout example.

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
