---
name: compute-planner
description: This skill should be used when the user asks to "plan compute", "estimate GPU hours", "generate SLURM scripts", "how much GPU do I need", "schedule jobs", "partition selection", "sbatch", "cluster scheduling", "engaging cluster", or after experiment design / setup validation and before running experiments on a cluster. Estimates GPU resources, selects cluster partitions, designs scheduling strategy, and generates SLURM scripts for MIT Engaging.
version: 0.1.0
tags: [Research, HPC, SLURM, GPU, Cluster, Scheduling]
---

# Compute Planner

Estimates GPU resources, selects cluster partitions, designs scheduling strategy, and generates production-ready SLURM scripts for MIT Engaging. Translates the experiment matrix from `experiment-plan.md` into a concrete execution plan with resource budgets, partition assignments, dependency chains, and ready-to-submit batch scripts -- so you commit GPU hours with confidence, not guesswork.

## Core Features

### 1. Resource Estimation

For each run in the experiment matrix, estimate three resource dimensions:

#### GPU Memory

- **Model parameters**: `num_params x bytes_per_param`
  - fp32: 4 bytes/param
  - fp16 / bf16: 2 bytes/param
  - int8: 1 byte/param
- **Optimizer states**: Adam/AdamW adds 2x model size (first and second moments)
  - Full Adam fp32: model_params x 4 bytes x 3 (weights + m + v)
  - Mixed precision: weights in fp16 + master weights + moments in fp32
- **Activation memory**: `batch_size x seq_len x hidden_dim x num_layers x bytes_per_activation`
  - Approximate: 2x model size for typical transformer training at batch_size=1
  - Scales linearly with batch_size
  - Gradient checkpointing reduces by ~sqrt(num_layers) factor
- **Peak memory formula**: `model_params + optimizer_states + activations + buffer`
  - Buffer: add 10-20% overhead for CUDA context, fragmentation, communication buffers
- **Load reference `references/gpu-memory-estimation.md`** for detailed formulas and practical examples

#### Wall Time

- **Primary source**: Smoke test timing from `validation-report.md` (setup-validation output)
  - Extract per-run wall time from the end-to-end smoke test
  - Scale by dataset size ratio if smoke test used a subset
  - Scale by number of epochs
- **Fallback source**: FLOPs-based estimate when no smoke test timing is available
  - Estimate FLOPs per forward pass: `6 x num_params x seq_len x batch_size` (training)
  - Divide by GPU throughput (A100: ~312 TFLOPS fp16, ~156 TFLOPS fp32; H100: ~990 TFLOPS fp16)
  - Multiply by number of steps
  - Apply efficiency factor (typically 0.3-0.5 for real workloads vs peak TFLOPS)
- **Safety margin**: Add 20% to account for data loading, evaluation, checkpointing, I/O

#### Storage

- **Checkpoints**: model_size x num_checkpoints (typically save best + last + every N epochs)
- **Logs**: ~10 MB per run (TensorBoard, CSV, JSON)
- **Intermediate outputs**: embeddings, activations, analysis artifacts
- **Total**: aggregate across all runs in the matrix

#### Aggregate Estimates

- **Per-run table**: rows = (model x dataset x method), columns = (GPU mem, wall time, storage)
- **Per-seed multiplier**: total_runs = matrix_rows x num_seeds
- **Total GPU-hours**: sum of (wall_time_hours x num_gpus) across all runs
- **Total storage**: sum across all runs + overhead for logs and intermediate data

### 2. Partition Selection

Select the optimal MIT Engaging partition for each job based on resource requirements and priority.

#### Available Partitions

| Partition | GPUs | CPUs | RAM | Time Limit | Priority | Use Case |
|-----------|------|------|-----|------------|----------|----------|
| `pi_tpoggio` | 8x A100 80GB | 192 | ~1TB | 7 days | Dedicated | Primary: long training runs |
| `ou_bcs_normal` | A100x8 or H100x4/node | Varies | Varies | 1 day | Normal | Overflow: medium runs |
| `ou_bcs_low` | A100x8 or H100x4/node | Varies | Varies | 1 day | Low | Background: non-urgent sweeps |
| `ou_bcs_high` | A100x8 or H100x4/node | Varies | Varies | 4 hours | High | Quick validation, debugging |
| `mit_normal_gpu` | Mixed | Varies | Varies | 1 day | Normal | Last resort fallback |

Load `references/engaging-cluster-config.md` for full partition details.

#### Selection Rules

1. **Single-GPU runs (most common)**:
   - Default to `pi_tpoggio` -- pack up to 8 concurrent single-GPU jobs
   - If pi_tpoggio is full or queue is long: spill to `ou_bcs_normal`
   - For non-urgent seed sweeps: use `ou_bcs_low` (may be preempted)
   - For quick validation (< 4 hours): use `ou_bcs_high` for faster scheduling

2. **Multi-GPU runs (data parallel or model parallel)**:
   - 2-8 GPUs: single node on `pi_tpoggio` (7-day limit is critical for large runs)
   - If wall time < 1 day: `ou_bcs_normal` is acceptable
   - Never split a multi-GPU job across partitions

3. **Priority assignment**:
   - **Phase 1 (quick validation)**: `ou_bcs_high` (fast turnaround, < 4 hours)
   - **Phase 2 (core experiments)**: `pi_tpoggio` (long runs need 7-day limit)
   - **Phase 3 (ablations)**: `pi_tpoggio` primary, `ou_bcs_normal` overflow
   - **Phase 4 (seed sweeps)**: `ou_bcs_low` for bulk, `pi_tpoggio` for stragglers

4. **Preemption handling**:
   - Jobs on `ou_bcs_low` may be preempted -- checkpoint every N steps
   - Include `--requeue` flag and checkpoint-resume logic in SLURM scripts
   - Never place critical-path jobs on low-priority partitions

### 3. Scheduling Strategy

Design the execution order and dependency structure for the full experiment matrix.

#### Parallelization

- **Independent runs**: Different model/task/seed combinations run in parallel
  - Example: model_A-task_1-seed_0, model_A-task_1-seed_1, model_B-task_1-seed_0 all independent
- **Maximum concurrency**: limited by partition GPU count (pi_tpoggio: 8 concurrent single-GPU jobs)
- **Array jobs**: Use SLURM `--array` for identical configurations with different seeds
  - `--array=0-4` for 5 seeds of the same (model, task, method) combination
  - Cleaner than N separate sbatch scripts
  - Easier to cancel/monitor as a group

#### Phased Execution

- **Phase 1 -- Quick validation**: 1 model, 1 task, 1 seed. Stop-or-go gate.
  - Submit immediately. If it fails, do not proceed.
  - Partition: `ou_bcs_high` (fast turnaround)
- **Phase 2 -- Core experiments**: Full model x task matrix, 1 seed per cell.
  - Depends on Phase 1: `--dependency=afterok:<phase1_jobid>`
  - Partition: `pi_tpoggio`
- **Phase 3 -- Ablation study**: Ablation variants, 1 seed each.
  - Depends on Phase 2: `--dependency=afterok:<phase2_jobid>`
  - Partition: `pi_tpoggio` primary, `ou_bcs_normal` overflow
- **Phase 4 -- Full seed sweep**: All cells x N seeds.
  - Depends on Phase 3: `--dependency=afterok:<phase3_jobid>`
  - Partition: `ou_bcs_low` for bulk parallelism
- **Phase 5 -- Extended experiments**: Secondary hypotheses, additional datasets.
  - Depends on Phase 4 analysis (manual gate)

#### Dependency Chains

- Use `--dependency=afterok:<jobid>` for sequential phases
- Use `--dependency=afterok:<jobid1>:<jobid2>` for jobs that depend on multiple predecessors
- The master launch script (`launch.sh`) captures job IDs and wires dependencies automatically
- Load `references/slurm-patterns.md` for dependency chain patterns

### 4. SLURM Script Generation

Generate production-ready sbatch scripts from templates.

#### Per-Run Script Template

Each run gets an sbatch script with:

```bash
#!/bin/bash
#SBATCH --job-name=<project>-<model>-<task>-<seed>
#SBATCH --partition=<selected_partition>
#SBATCH --gres=gpu:<num_gpus>
#SBATCH --cpus-per-task=<cpus>
#SBATCH --mem=<memory>
#SBATCH --time=<wall_time_with_margin>
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<user_email>
#SBATCH --requeue

# --- Environment Setup ---
module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
source <virtualenv_path>/bin/activate

# --- Checkpoint Resume ---
CHECKPOINT_DIR="<checkpoint_path>"
RESUME_FLAG=""
if [ -f "${CHECKPOINT_DIR}/latest.pt" ]; then
    RESUME_FLAG="--resume ${CHECKPOINT_DIR}/latest.pt"
    echo "Resuming from checkpoint: ${CHECKPOINT_DIR}/latest.pt"
fi

# --- Run Experiment ---
python <script> \
    --model <model> \
    --task <task> \
    --seed ${SLURM_ARRAY_TASK_ID:-<default_seed>} \
    --output_dir <output_dir> \
    --checkpoint_dir ${CHECKPOINT_DIR} \
    ${RESUME_FLAG} \
    <additional_args>

# --- Copy Results to Home ---
echo "Copying results from scratch to home..."
rsync -av <scratch_output_dir>/ <home_output_dir>/

echo "Job ${SLURM_JOB_ID} completed at $(date)"
```

#### Master Launch Script

`launch.sh` orchestrates the full experiment:

- Submits Phase 1 jobs, captures job IDs
- Submits Phase 2 with `--dependency=afterok:$PHASE1_ID`
- Submits Phase 3 with `--dependency=afterok:$PHASE2_IDS`
- Submits Phase 4 with `--dependency=afterok:$PHASE3_IDS`
- Prints summary of all submitted jobs and dependency graph
- Writes `job-manifest.txt` with job IDs, names, and statuses

#### Monitoring Script

`monitor.sh` provides real-time status:

- Polls `squeue` for running/pending jobs
- Polls `sacct` for completed/failed jobs
- Checks output logs for errors or convergence issues
- Prints color-coded summary table
- Optionally sends notification on completion/failure

### 5. Filesystem Strategy

Organize files across MIT Engaging storage tiers for performance and safety.

#### Storage Tiers

| Location | Use | Quota | Speed | Backup |
|----------|-----|-------|-------|--------|
| `/home/<user>/` | Code, configs, final results | Limited | Slow | Yes |
| `/pool001/<lab>/` | Shared datasets, pretrained models | Large | Medium | No |
| `/scratch/<user>/` | Active training data, checkpoints, logs | Large | Fast | No (purged) |

#### Layout Convention

```
/home/<user>/<project>/
    code/               # Git repo (symlink or clone)
    configs/            # Experiment configs (Hydra YAML)
    results/            # Final results (copied from scratch after each phase)
    cluster/            # SLURM scripts (generated by this skill)
        launch.sh
        monitor.sh
        jobs/           # Individual sbatch scripts
        logs/           # SLURM stdout/stderr

/scratch/<user>/<project>/
    data/               # Active datasets (copied from pool or generated)
    checkpoints/        # Training checkpoints (auto-cleaned after copy)
    outputs/            # Raw experiment outputs (copied to home after phase)
```

#### Safety Rules

- **Code on `/home/`**: Always. Git-tracked, backed up.
- **Active data on `/scratch/`**: Fast I/O during training.
- **Results copied back after each phase**: `rsync` from scratch to home in the sbatch epilogue.
- **Checkpoint cleanup**: After successful copy, optionally remove scratch checkpoints to free quota.
- **Dataset caching**: Large datasets on `/pool001/`, symlinked into scratch.

### 6. Cost/Time Summary

Generate `compute-plan.md` with a complete resource overview.

#### Resource Table

| Phase | Runs | GPUs/Run | Hours/Run | Total GPU-h | Partition |
|-------|------|----------|-----------|-------------|-----------|
| Phase 1: Validation | 1 | 1 | 0.5 | 0.5 | ou_bcs_high |
| Phase 2: Core | 12 | 1 | 4.0 | 48.0 | pi_tpoggio |
| Phase 3: Ablation | 8 | 1 | 4.0 | 32.0 | pi_tpoggio |
| Phase 4: Seeds | 60 | 1 | 4.0 | 240.0 | ou_bcs_low |
| **Total** | **81** | | | **320.5** | |

#### Scheduling Diagram

```
Phase 1 (validation):  [==]                              ~0.5h
Phase 2 (core):             [========]                   ~6h (8 concurrent)
Phase 3 (ablation):                    [======]          ~4h (8 concurrent)
Phase 4 (seeds):                              [========] ~30h (8 concurrent)
                       ──────────────────────────────────
Total wall time:       ~40.5 hours (~1.7 days)
```

#### Partition Assignments

- Summary of which jobs go to which partition and why
- Queue wait time estimates (based on typical Engaging load)
- Fallback plan if primary partition is congested

#### Risk Factors

- **Preemption risk**: Quantify how many jobs are on preemptible partitions
- **Wall time risk**: Flag any jobs approaching the partition time limit
- **Storage risk**: Flag if total storage exceeds scratch quota
- **Queue risk**: Estimate wait times based on current cluster load
- **Mitigation**: Checkpoint frequency, auto-requeue, fallback partitions

## Input Modes

### Mode A: Pipeline (from predecessors)

1. **Experiment plan** -- from `experiment-plan.md` (experiment-design output)
   - Experiment matrix: models x tasks x methods x seeds
   - Baselines and ablation variants
   - Execution ordering (phases and checkpoints)
2. **Validation report** -- from `validation-report.md` (setup-validation output)
   - Smoke test timing (per-run wall time estimate)
   - GPU memory usage observed during smoke test
3. **Available resources** -- user specifies partition access, time constraints, priority

### Mode B: Standalone (manual)

1. **Experiment description** -- user describes the experiment matrix in free text
2. **Model information** -- user provides: model name, parameter count, precision
3. **Hardware information** -- user specifies: GPU type, number of GPUs, partition preferences
4. The skill estimates resources from the description and generates SLURM scripts

When running in Mode B, state: "No experiment-plan.md or validation-report.md found. Estimating resources from user-provided description. Wall time estimates may be less accurate without smoke test timing."

### Mode C: Re-plan (iteration)

1. **Updated experiment plan** -- revised after results analysis or hypothesis revision
2. **Previous compute plan** -- to diff against and estimate incremental cost
3. The skill generates only the delta: new/modified SLURM scripts, updated resource table

When running in Mode C, state: "Previous compute-plan.md found. Computing incremental changes only."

## Outputs

### Primary Output

- `compute-plan.md` containing:
  - **Resource table**: Per-run and aggregate GPU memory, wall time, storage estimates
  - **Partition assignments**: Which partition for each phase, with justification
  - **Scheduling diagram**: ASCII timeline showing phases, concurrency, dependencies
  - **Total estimates**: GPU-hours, wall clock time, storage
  - **Risk factors**: Preemption, wall time limits, storage, queue wait
  - **Filesystem layout**: Where code, data, checkpoints, results live

### Generated Scripts

- `cluster/` directory containing:
  - `launch.sh` -- Master launch script with dependency chains
  - `monitor.sh` -- Job monitoring and status script
  - `jobs/` -- Individual sbatch scripts for each run
    - Named: `<phase>_<model>_<task>_<method>.sh`
    - Array jobs for seed sweeps: `<phase>_<model>_<task>_<method>_seeds.sh`

### State Update

- Updates `experiment-state.json`:
  - Sets `resource_budget.total_gpu_hours` from aggregate estimate
  - Preserves existing state fields

## When to Use

### Scenarios for This Skill

1. **After setup validation passes** -- smoke test timing is available, ready to plan the full sweep
2. **After experiment design** -- have the experiment matrix, need to translate to cluster jobs
3. **Before submitting to cluster** -- want resource estimates and partition selection before committing GPU hours
4. **Mid-project re-planning** -- hypothesis revision produced a new experiment plan, need updated compute plan
5. **Resource-constrained planning** -- limited GPU budget, need to optimize partition usage and scheduling

### Typical Workflow

```
experiment-design -> setup-validation -> [compute-planner] -> experiment-runner
                          OR
user describes experiment -> [compute-planner] -> manual sbatch submission
```

**Output Files:**
- `compute-plan.md` -- Complete compute plan with resource estimates
- `cluster/launch.sh` -- Master launch script
- `cluster/monitor.sh` -- Monitoring script
- `cluster/jobs/*.sh` -- Individual sbatch scripts

## Integration with Other Systems

### Pipeline Position

```
experiment-design (experiment matrix)
    |
setup-validation (smoke test timing)
    |
compute-planner  <-- THIS SKILL
    |
experiment-runner (submits SLURM jobs)
    |
results-analysis (analyzes outputs)
```

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
project-scaffold (Create project structure)
    |
experiment-data-builder + model-setup + measurement-implementation
    |
setup-validation (Pre-flight checks + smoke test timing)
    |
compute-planner (Resource estimation + SLURM scripts)  <-- THIS SKILL
    |
experiment-runner (Execute on cluster)
    |
results-analysis (Analyze results)
    |
failure-diagnosis / claim-evidence-bridge (Iterate or write)
```

### Data Flow

- **Depends on**: `experiment-plan.md` (experiment-design), `validation-report.md` (setup-validation, for smoke test timing)
- **Feeds into**: `experiment-runner` (provides SLURM scripts and compute plan for cluster execution)
- **Hook activation**: Context-aware keyword trigger in `skill-forced-eval.js` -- triggers on: "SLURM", "sbatch", "GPU hours", "cluster", "engaging", "partition", "compute plan"
- **New command**: `/plan-compute` -- generate compute plan and SLURM scripts from experiment plan
- **Obsidian integration**: If bound, writes compute plan summary to `Experiments/` notes
- **State file**: Updates `experiment-state.json` with `resource_budget.total_gpu_hours`

### Key Configuration

- **Target cluster**: MIT Engaging (configurable for other SLURM clusters)
- **Default partition**: `pi_tpoggio` (8x A100, 7-day limit)
- **Module loads**: `cuda/12.4.0`, `cudnn/9.8.0.87-cuda12`
- **Checkpoint frequency**: Every N steps (configurable, default: every 1000 steps)
- **Safety margin**: 20% added to wall time estimates
- **Output format**: Markdown plan + executable shell scripts

## Additional Resources

### Reference Files

Detailed cluster and estimation guides, loaded on demand:

- **`references/engaging-cluster-config.md`** -- MIT Engaging Cluster Configuration
  - Deployment model: Claude Code runs directly on the cluster (no SSH needed)
  - Complete partition table with hardware specs, time limits, priority levels
  - Module system and available software
  - Filesystem layout, quotas, and storage tiers
  - SLURM commands reference
  - Job array syntax
  - Dependency chains
  - Preemption handling and auto-requeue
  - Queue monitoring and diagnostics
  - Storage quotas and cleanup policies

- **`references/gpu-memory-estimation.md`** -- GPU Memory Estimation Guide
  - Model parameter memory (fp32, fp16, bf16, int8)
  - Optimizer state memory (Adam, SGD, mixed precision)
  - Activation memory estimation for transformers
  - Peak memory formula with buffer allocation
  - Gradient checkpointing savings
  - Practical examples: GPT-2 124M, 350M, 1.3B on A100
  - Memory profiling tools and commands

- **`references/slurm-patterns.md`** -- SLURM Job Management Patterns
  - sbatch script template with all common flags
  - Array jobs for seed sweeps
  - Dependency chains for phased execution
  - Job monitoring with squeue and sacct
  - Preemption recovery with checkpoint + auto-resubmit
  - Resource cleanup on job abort
  - Common pitfalls and debugging

### Example Files

Complete working examples:

- **`examples/example-compute-plan.md`** -- Compute Plan Example
  - Full compute plan for an ICL circuit-algorithm bridge experiment
  - Resource table with per-phase breakdown
  - Partition assignments with justification
  - Scheduling diagram with dependency chains
  - Total estimates and risk factors

- **`examples/example-slurm-scripts.md`** -- SLURM Script Examples
  - Complete sbatch script for a single training run
  - Master launch script with dependency chains
  - Monitoring script snippet
  - Array job for seed sweeps
