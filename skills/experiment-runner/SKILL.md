---
name: experiment-runner
description: This skill should be used when the user asks to "run experiments", "submit SLURM jobs", "run experiment sweep", "monitor experiment progress", "phase gate", "resubmit failed jobs", "check experiment status", or after experiment design and before results analysis. Executes the experiment matrix via SLURM with phased gates, failure recovery, and progress tracking. Integrates the experiment-reproducibility rule.
version: 0.1.0
tags: [Research, Experiment Execution, SLURM, HPC, Reproducibility]
---

# Experiment Runner

Execute the experiment matrix via SLURM with phased gates, failure recovery, and progress tracking. This skill takes the outputs of `experiment-design` (and optionally `compute-planner`) and orchestrates the actual execution of all planned runs on an HPC cluster.

**Deployment note**: When Claude Code runs directly on the cluster (recommended — see `compute-planner` engaging reference), this skill can execute `sbatch`, `squeue`, `sacct`, and all SLURM commands natively via the Bash tool. No SSH or remote execution needed.

## Core Features

### 1. Run Matrix Construction

Parse `experiment-plan.md` to enumerate all run combinations and organize them by phase:

- **Enumerate combinations**: Cross-product of (model, dataset, seed, method, ablation) from the plan
- **Group by phase**: Map each combination to its execution phase (Phase 1: quick validation, Phase 2: core, Phase 3: ablation, Phase 4: extended)
- **Calculate totals**: Total runs per phase, total GPU-hours per phase, cumulative budget
- **Assign run IDs**: Deterministic naming: `{phase}_{method}_{dataset}_{seed}` (e.g., `p1_contrastive_bci4_s42`)
- **Generate run manifest**: `run-manifest.json` listing every run with its parameters, phase, and expected resource usage

```
run-manifest.json structure:
{
  "total_runs": 531,
  "phases": {
    "phase_1": { "runs": [...], "gpu_hours_est": 12 },
    "phase_2": { "runs": [...], "gpu_hours_est": 540 },
    ...
  }
}
```

### 2. Job Submission

Submit SLURM jobs from prepared scripts, tracking all job IDs:

- **Single jobs**: `sbatch` for individual runs, capture job ID from stdout
- **Array jobs**: Use SLURM job arrays for seed sweeps (`--array=0-4` for 5 seeds)
- **Dependency chains**: Phase N+1 jobs depend on Phase N completion (`--dependency=afterok:{phase_n_job_id}`)
- **Resource requests**: Map resource estimates from `experiment-plan.md` to SLURM directives (`--gres=gpu:1`, `--time`, `--mem`)
- **Job naming**: Consistent `--job-name` matching run ID for easy tracking
- **Submission log**: Record all submitted job IDs in `experiment-state.json`

```bash
# Example: submit Phase 1 with array job for seeds
sbatch --job-name=p1_contrastive_bci4 \
       --array=0-4 \
       --gres=gpu:a100:1 \
       --time=02:00:00 \
       --output=outputs/p1_contrastive_bci4_s%a/slurm-%A_%a.out \
       cluster/jobs/run_experiment.sh --method contrastive --dataset bci4 --seed_index $SLURM_ARRAY_TASK_ID
```

### 3. Progress Monitoring

Poll SLURM for job status and report progress:

- **Active monitoring**: Query `squeue -u $USER --format` for running/pending jobs
- **Completed status**: Query `sacct --jobs={id} --format=JobID,State,Elapsed,MaxRSS,ExitCode`
- **Progress calculation**: `completed_runs / total_runs_in_phase x 100%`
- **Estimated time remaining**: Based on average elapsed time of completed runs and remaining count
- **Status dashboard**: Per-phase summary table

```
Phase 1: [======----] 60% (6/10 runs)  ~45 min remaining
Phase 2: [----------]  0% (0/270 runs) waiting on Phase 1 gate
```

- **Alerting**: Log phase completion and failure events; optionally trigger email or webhook notification

### 4. Failure Handling

Detect, classify, and recover from each failure type:

| Failure Type | Detection | Recovery Action |
|-------------|-----------|-----------------|
| **OOM** | Exit code + "CUDA out of memory" in stderr | Log, reduce batch size by 50%, resubmit |
| **NaN** | "NaN" in training log or output tensors | Log, flag for investigation, skip run |
| **Timeout** | SLURM `TIMEOUT` state | Check for checkpoint, resubmit with 1.5x walltime |
| **Preemption** | Exit code 271 or `PREEMPTED` state | Detect last checkpoint, resubmit with `--begin=now` |
| **Node failure** | `NODE_FAIL` state | Resubmit with `--exclude={failed_node}` |

**Recovery policies**:
- **Max retries**: 3 per run (configurable)
- **Backoff**: Exponential (1 min, 2 min, 4 min between retries)
- **Escalation**: After max retries, mark run as `failed` in state and continue with remaining runs
- **Failure log**: All failures recorded in `experiment-state.json` with timestamps, error type, and recovery actions taken

See `references/failure-recovery-patterns.md` for detailed detection patterns and recovery strategies.

### 5. Phase Gate Evaluation

After all Phase N jobs complete, evaluate the gate criterion before proceeding.

#### Deterministic gate checking (preferred)

When the project was scaffolded with `project-scaffold`, use the deterministic gate checker:

```bash
make check-gates                                    # uses default gate_spec
python scripts/check_gates.py --config scripts/gate_spec.json  # custom gates
```

The script reads `experiments/results_summary.csv` (produced by `make collect`) and evaluates pass/fail criteria. Exit code 0 = all gates pass, 1 = any failure. See `project-scaffold/references/template-catalog.md` section N for the full script source and gate specification format.

**Use agent reasoning for gate evaluation only when**: gate criteria require comparison against a specific baseline condition (not just a threshold), criteria involve statistical tests (p-values, effect sizes), or when the DIAGNOSE decision requires human judgment.

#### Agent-driven gate evaluation (fallback)

1. **Collect results**: Load metrics from `outputs/{run_id}/metrics.json` for all runs in the phase
2. **Compute aggregate**: Mean +/- std of primary metric across seeds
3. **Evaluate criterion**: Compare against the gate criterion defined in `experiment-plan.md`
   - Example Phase 1 gate: "improvement > +1% over baseline"
   - Example Phase 2 gate: "H1 confirmed at p<0.05 with effect > +3%"
4. **Decision**:
   - **PROCEED**: Criterion met, submit Phase N+1 jobs
   - **STOP**: Criterion clearly failed, activate `failure-diagnosis`
   - **DIAGNOSE**: Ambiguous result, pause and request user decision
5. **Record**: Log gate decision, metric values, and rationale in `experiment-state.json`

```
Phase 1 Gate Evaluation:
  Primary metric (balanced accuracy):
    Proposed: 72.3% +/- 1.2%
    Baseline: 69.8% +/- 1.5%
    Improvement: +2.5% (> +1% threshold)
  Decision: PROCEED to Phase 2
```

### 6. State Management

Maintain `experiment-state.json` throughout the execution lifecycle. This file is shared with `experiment-design`, `hypothesis-revision`, `failure-diagnosis`, and `hooks/session-start.js` — preserve all top-level fields when updating.

#### Deterministic state updates (preferred)

When the project was scaffolded with `project-scaffold`, use `scripts/update_experiment_state.py` for mechanical state transitions:

```bash
python scripts/update_experiment_state.py --status running          # set status
python scripts/update_experiment_state.py --job-id 12345 --gpu-hours 10.5  # record job
python scripts/update_experiment_state.py --advance-iteration --status planned  # next iteration
python scripts/update_experiment_state.py --analysis experiments/analysis-report.md
```

See `project-scaffold/references/template-catalog.md` section O for the full script source and usage patterns. **Use agent reasoning for state updates only when**: writing complex `phases` sub-objects, recording failure details with diagnosis, or when upstream skill fields need careful preservation during concurrent updates.

**Full schema** (top-level fields set by upstream skills, preserved by the runner):

```jsonc
{
  "$schema": "experiment-state-v1",
  "project": "<project-name>",              // set by experiment-design
  "created": "<ISO-8601>",                  // set by experiment-design
  "updated": "<ISO-8601>",                  // updated by runner on every change
  "iteration": 0,                           // incremented by hypothesis-revision
  "max_iterations": 3,                      // set by experiment-design
  "active_hypothesis": {                    // set by hypothesis-formulation/revision
    "id": "H1",
    "summary": "<one-line>",
    "source_file": "hypotheses.md"
  },
  "status": "running",                      // updated by runner (see below)
  "latest_analysis": null,                  // set by results-analysis
  "resource_budget": {                      // updated by runner after each phase
    "total_gpu_hours": null,
    "used_gpu_hours": 0,
    "remaining_gpu_hours": null
  },
  "deadline": null,                         // set by experiment-design
  "history": [],                            // appended by hypothesis-revision
  "phases": { ... },                        // managed by runner (see below)
  "failures": [ ... ]                       // managed by runner (see below)
}
```

**Status values** (full lifecycle — runner manages transitions marked with →):

- `planned` — Initial state from `experiment-design`
- → `running` — Runner sets this when first job is submitted
- → `analyzing` — Runner sets this when all phases complete successfully
- → `diagnosing` — Runner sets this when a phase gate fails
- `revising` — Set by `hypothesis-revision` (runner preserves, never overwrites)
- `confirmed` — Set by the research loop when hypothesis is confirmed (runner preserves)
- `abandoned` — Set by `hypothesis-revision` when direction is abandoned (runner preserves)

**Rule**: The runner only writes `running`, `analyzing`, or `diagnosing`. It NEVER overwrites `revising`, `confirmed`, or `abandoned` — those are set by other skills in the iteration loop.

**Per-phase records**: Added to `phases` sub-object as phases complete:

```jsonc
{
  "phases": {
    "phase_1": {
      "status": "completed",
      "submitted_at": "2026-03-27T10:15:00Z",
      "completed_at": "2026-03-27T11:00:00Z",
      "job_ids": ["12345", "12346"],
      "runs_total": 6,
      "runs_completed": 6,
      "runs_failed": 0,
      "gate_result": "PROCEED",
      "gate_metric": { "proposed": 0.723, "baseline": 0.698, "improvement": 0.025 },
      "gpu_hours_used": 10.5
    }
  }
}
```

- **Resource tracking**: Update `resource_budget.used_gpu_hours` and `resource_budget.remaining_gpu_hours` after each phase
- **Failure records**: Append to `failures` array with run ID, error type, retry count, resolution

```jsonc
{
  "failures": [
    {
      "run_id": "p2_contrastive_bci4_s3",
      "job_id": "12389",
      "error_type": "OOM",
      "timestamp": "2026-03-28T14:22:00Z",
      "retry_count": 1,
      "resolution": "batch_size reduced 64->32, resubmitted as job 12401"
    }
  ]
}
```

### 7. Reproducibility Integration

Apply the `experiment-reproducibility` rule at every stage:

- **Seed management**: Each run calls `set_seed(seed)` before any stochastic operation. Seeds are drawn from the run manifest, not hardcoded.
- **Config recording**: Hydra auto-saves resolved config, overrides, and hydra config to `outputs/{run_id}/.hydra/`
- **Environment logging**: `log_environment()` called at run start; `pip freeze` saved to `outputs/{run_id}/requirements.txt`
- **Checkpoint management**: Save best + last N checkpoints per run; include optimizer and scheduler state for resumption
- **Dataset versioning**: Record dataset hash in `outputs/{run_id}/metadata.json`
- **Output directory**: `outputs/{run_id}/` with deterministic naming from run manifest

```
outputs/
  p1_contrastive_bci4_s42/
    .hydra/
      config.yaml
      overrides.yaml
    metrics.json
    train.log
    requirements.txt
    metadata.json
    checkpoints/
      best_model.pt
      checkpoint_latest.pt
```

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **`experiment-plan.md`** -- from `experiment-design`, containing phases, baselines, ablations, gate criteria, resource estimates
2. **Compute plan and SLURM scripts** -- `compute-plan.md` and `cluster/` directory from `compute-planner` (contains `launch.sh`, `monitor.sh`, `jobs/*.sh`), or user-prepared scripts
3. **Implemented experiment code** -- training scripts referenced by SLURM jobs
4. **`experiment-state.json`** -- existing state file from `experiment-design`

The skill reads all four inputs, constructs the run manifest, and begins submission of Phase 1.

### Mode B: Standalone (manual)

1. **User describes** which experiments to run, with what parameters
2. **SLURM scripts** provided or referenced by path
3. **No `experiment-plan.md`** -- the skill reconstructs a minimal run matrix from user input

When running in Mode B, state: "No experiment-plan.md found. I'll construct a run matrix from your description -- please confirm the run list before I submit."

The skill generates a minimal `experiment-plan.md` and `experiment-state.json` before proceeding.

## Outputs

- **`run-manifest.json`**: Complete enumeration of all runs with parameters, phase assignment, and expected resources
- **`outputs/` directory**: Per-run output directories following the reproducibility rule structure:
  - `outputs/{run_id}/metrics.json` -- training and evaluation metrics
  - `outputs/{run_id}/.hydra/` -- Hydra config snapshots
  - `outputs/{run_id}/train.log` -- training log
  - `outputs/{run_id}/checkpoints/` -- model checkpoints
  - `outputs/{run_id}/requirements.txt` -- frozen dependencies
  - `outputs/{run_id}/metadata.json` -- dataset hash, environment info, run parameters
- **Updated `experiment-state.json`**: Status transitions, per-phase records, resource tracking, failure log
- **Console progress reports**: Phase-by-phase status dashboard during monitoring

## When to Use

### Scenarios for This Skill

1. **After experiment design** -- have an `experiment-plan.md` and SLURM scripts, ready to execute
2. **Resuming after failure** -- some jobs failed, need to diagnose and resubmit
3. **Monitoring in-flight experiments** -- jobs are running on the cluster, need status update
4. **Phase gate check** -- a phase just completed, need to evaluate the go/stop criterion
5. **Scaling up** -- quick validation passed, ready to launch full sweep

### Scenarios NOT for This Skill

- **Designing experiments** -- use `experiment-design` instead
- **Analyzing results** -- use `results-analysis` after all phases complete
- **Writing SLURM scripts** -- use `compute-planner` or write manually
- **Debugging model code** -- use `bug-detective` for code-level issues

### Typical Workflow

```
experiment-design -> [experiment-runner] -> results-analysis
                          |
                          +-- failure -> failure-diagnosis -> hypothesis-revision
                          |                                       |
                          +-- proceed -> next phase               +-- experiment-design (revised)
```

**Output Files:**
- `run-manifest.json` -- Run matrix with all combinations
- `outputs/` -- Per-run results directory
- `experiment-state.json` -- Updated state file

## Integration with Other Systems

### Complete Research Workflow

```
research-ideation (Research initiation)
    |
novelty-assessment (Validate contribution)
    |
hypothesis-formulation (Testable predictions)
    |
experiment-design (Plan experiments)
    |
experiment-runner (Execute experiments)  <-- THIS SKILL
    |
results-analysis (Analyze results)
    |
failure-diagnosis / claim-evidence-bridge (Iterate or write)
```

### Data Flow

- **Depends on**: `experiment-design` (Mode A) OR user description (Mode B); SLURM scripts; experiment code
- **Feeds into**: `results-analysis` (on success), `failure-diagnosis` (on gate failure)
- **Hook activation**: Context-aware keyword trigger in `skill-forced-eval.js`
- **Command**: `/run-experiment` -- execute the experiment matrix from the plan
- **Obsidian integration**: If bound, updates `Experiments/{experiment-line}.md` with running/completed status and per-phase summaries
- **State file**: Reads and updates `experiment-state.json` throughout execution
- **Rule integration**: Enforces `experiment-reproducibility` rule for every run

### Key Configuration

- **Max retries per run**: 3 (configurable in run manifest)
- **Backoff strategy**: Exponential (1 min base)
- **Gate evaluation**: Automatic after phase completion; requires user confirmation for DIAGNOSE decisions
- **Monitoring interval**: 60 seconds between `squeue` polls (configurable)
- **Output format**: JSON for machine-readable state, Markdown for human-readable reports

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/slurm-monitoring.md`** -- SLURM Monitoring Guide
  - squeue format strings and filtering
  - sacct for completed job info
  - Detecting failure types from exit codes and log patterns
  - Progress calculation and estimated time remaining
  - Automatic alerting on phase completion or job failure

- **`references/failure-recovery-patterns.md`** -- Failure Recovery Patterns
  - OOM detection and recovery (batch size reduction, gradient checkpointing, mixed precision)
  - NaN detection and diagnosis (gradient explosion, learning rate, data issues)
  - Timeout recovery from checkpoints with extended walltime
  - Preemption detection and auto-resubmit from checkpoint
  - Node failure retry on different node
  - Exponential backoff, max retry count, failure log format

### Example Files

Complete working examples:

- **`examples/example-runner-implementation.md`** -- Runner Implementation Example
  - Phase gate evaluation function
  - Loading results from outputs directory
  - Checking metric against threshold from experiment plan
  - Updating experiment-state.json with gate decision
