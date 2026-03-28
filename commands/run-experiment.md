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
