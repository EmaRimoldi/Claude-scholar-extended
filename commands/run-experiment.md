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

Activates the `experiment-runner` skill to autonomously:
1. Run pre-flight validation (10-15 seconds) — catches import/config errors
2. Run CPU smoke test (1-5 minutes) — catches training loop errors
3. Submit SLURM jobs (if both validation steps pass)
4. Monitor progress and evaluate phase gates
5. Handle failures gracefully (display errors, suggest fixes, abort before GPU waste)

## Usage

```text
/run-experiment              # runs next pending phase from experiment-state.json
/run-experiment phase=2      # runs execution phase 2 explicitly (numeric; not a path)
```

There is **no** required string in quotes. The only optional argument is **`phase=<integer>`**, matching the phased structure in `experiment-plan.md` / `experiment-state.json`. See [docs/PIPELINE_INPUTS.md](../docs/PIPELINE_INPUTS.md) for prerequisites and a minimal project layout example.

## CRITICAL: Always run the autonomous script first

**Do NOT manually assess whether the cluster is available.**

At Step 18, the FIRST action is always:

```bash
python scripts/run_experiment_autonomously.py --repo-root .
```

This script auto-detects the cluster, runs preflight, and submits — with no manual
intervention required. Do not reason about whether `sbatch` might be available;
run the script and let it report the environment. Exit codes:
- 0 = submitted OK
- 1 = preflight failed — fix the code, then rerun
- 2 = not on a SLURM cluster — script prints manual instructions
- 3 = missing state files — check pipeline-state.json and project structure

## Workflow

**Autonomous Execution** (no manual intervention required after `/run-experiment`):

1. **Run** `python scripts/run_experiment_autonomously.py --repo-root .`
2. Script auto-detects: sbatch in PATH + SLURM_JOB_ID not set → login node confirmed
3. Script runs `scripts/preflight_validate.py` in the project directory (10-30s)
   - If fails → abort, display error, suggest fix
   - If passes → continue
4. Script auto-discovers `slurm/train_*.sh` and submits each via `sbatch`
5. Script updates `experiment-state.json` with job IDs and timestamps
6. Return control to user with job IDs and monitoring info

**Example Output**:
```
EXPERIMENT RUNNER: Phase 2

[1/3] PRE-FLIGHT VALIDATION
  ✓ Config files exist
  ✓ Hydra syntax correct
  ... (all 7 checks pass)
  Result: PASS (7/7)

[2/3] CPU SMOKE TEST (max_steps=2)
  Train dataset: 15383 samples
  Step 1/2: loss=0.8641
  Step 2/2: loss=0.7234
  Result: PASS

[3/3] SLURM SUBMISSION
  Job 11483264: M0 + M1 (SBATCH ACCEPTED)
  Job 11483265: M3 + M4b (SBATCH ACCEPTED)
  Result: SUCCESS

Jobs submitted. Monitoring status.
```

## Implementation

The autonomous runner is:

```bash
python scripts/run_experiment_autonomously.py --repo-root .
# Optional flags:
#   --project-dir PATH   override project dir (default: read from pipeline-state.json)
#   --dry-run            print sbatch commands but do not submit
#   --skip-preflight     skip preflight_validate.py (not recommended)
```

**What this script does**:
1. **Detects cluster**: checks `which sbatch` and `$SLURM_JOB_ID` — does not assume
2. **Pre-flight**: runs `scripts/preflight_validate.py` in the project directory
3. **Discovers scripts**: finds all `slurm/train_*.sh` automatically
4. **Submits**: calls `sbatch` for each script; collects job IDs
5. **Updates state**: writes job IDs to `experiment-state.json`

**Key properties**:
- ✅ Works on any SLURM cluster — no hardcoded partition or hostname
- ✅ Exit 2 (not 1) when cluster unavailable — clean signal, not an error
- ✅ Prints manual fallback commands when sbatch is absent
- ✅ Never stalls waiting for human to confirm cluster availability

## Integration

- **Primary skill**: `experiment-runner` (located in `skills/experiment-runner/SKILL.md`)
- **Implementation**: `scripts/run_experiment_autonomously.py`
- **Prerequisite**: `compute-plan.md` (SLURM scripts), validated pipeline, `experiment-state.json`
- **Feeds into**: Job monitoring, `result-collector` (outputs/ directory), `failure-diagnosis` (if gate fails)
- **Related documentation**: `docs/VALIDATION_PIPELINE.md` (two-layer validation system)
