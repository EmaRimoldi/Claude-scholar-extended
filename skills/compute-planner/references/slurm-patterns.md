# SLURM Job Management Patterns

Reference for common SLURM patterns used in compute planning: script templates, array jobs, dependency chains, monitoring, preemption recovery, and resource cleanup.

## sbatch Script Template

Complete template with all common flags:

```bash
#!/bin/bash
#SBATCH --job-name=exp-model_a-task_1-seed_0
#SBATCH --partition=pi_tpoggio
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=cluster/logs/%x_%j.out
#SBATCH --error=cluster/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=user@mit.edu
#SBATCH --requeue

# --- Environment ---
module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
source ~/envs/project_env/bin/activate

# --- Working Directory ---
cd /home/$USER/project/code

# --- Checkpoint Resume Logic ---
CHECKPOINT_DIR="/scratch/$USER/project/checkpoints/${SLURM_JOB_NAME}"
mkdir -p ${CHECKPOINT_DIR}

RESUME_FLAG=""
if [ -f "${CHECKPOINT_DIR}/latest.pt" ]; then
    RESUME_FLAG="--resume_from_checkpoint ${CHECKPOINT_DIR}/latest.pt"
    echo "Resuming from: ${CHECKPOINT_DIR}/latest.pt"
fi

# --- Run ---
echo "Starting job ${SLURM_JOB_ID} on $(hostname) at $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"

python train.py \
    --model model_a \
    --task task_1 \
    --seed 0 \
    --output_dir /scratch/$USER/project/outputs/${SLURM_JOB_NAME} \
    --checkpoint_dir ${CHECKPOINT_DIR} \
    ${RESUME_FLAG}

EXIT_CODE=$?

# --- Copy Results ---
if [ $EXIT_CODE -eq 0 ]; then
    echo "Job succeeded. Copying results to home..."
    rsync -av /scratch/$USER/project/outputs/${SLURM_JOB_NAME}/ \
              /home/$USER/project/results/${SLURM_JOB_NAME}/
    echo "Results copied successfully."
else
    echo "Job failed with exit code ${EXIT_CODE}."
fi

echo "Job ${SLURM_JOB_ID} finished at $(date) with exit code ${EXIT_CODE}"
exit $EXIT_CODE
```

### Key Flags Explained

| Flag | Purpose | Example |
|------|---------|---------|
| `--job-name` | Human-readable name (used in logs, squeue) | `exp-gpt2-linreg-s0` |
| `--partition` | Target partition | `pi_tpoggio` |
| `--gres=gpu:N` | Number of GPUs | `gpu:1`, `gpu:4` |
| `--cpus-per-task` | CPU cores (for data loading) | `8` |
| `--mem` | RAM per node | `32G`, `64G` |
| `--time` | Wall time limit (HH:MM:SS or D-HH:MM:SS) | `08:00:00`, `7-00:00:00` |
| `--output` / `--error` | Log file paths (`%x`=job name, `%j`=job ID) | `logs/%x_%j.out` |
| `--mail-type` | When to email | `END,FAIL`, `ALL`, `NONE` |
| `--requeue` | Auto-requeue on preemption | (no value) |

## Array Jobs for Seed Sweeps

Array jobs run identical configurations with different indices (seeds):

```bash
#!/bin/bash
#SBATCH --job-name=exp-model_a-task_1-seeds
#SBATCH --partition=pi_tpoggio
#SBATCH --array=0-4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=cluster/logs/%x_%A_%a.out
#SBATCH --error=cluster/logs/%x_%A_%a.err

# %A = array master job ID, %a = array task index
SEED=${SLURM_ARRAY_TASK_ID}

module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
source ~/envs/project_env/bin/activate

python train.py \
    --model model_a \
    --task task_1 \
    --seed ${SEED} \
    --output_dir /scratch/$USER/project/outputs/model_a-task_1-seed_${SEED}
```

### Array Job Control

```bash
# Limit concurrent array tasks (e.g., max 4 at once)
#SBATCH --array=0-19%4

# Cancel specific array task
scancel <array_job_id>_3

# Cancel entire array
scancel <array_job_id>

# Check array job status
squeue -j <array_job_id>
```

### When to Use Array Jobs vs. Separate Scripts

- **Array jobs**: Same code, same config, different seeds. Cleaner, easier to monitor.
- **Separate scripts**: Different models, tasks, or hyperparameters. More flexible per-job configuration.

## Dependency Chains for Phased Execution

### Linear Chain (Phase 1 -> 2 -> 3 -> 4)

```bash
#!/bin/bash
# launch.sh -- Master launch script with dependency chains

set -euo pipefail

echo "=== Experiment Launch ==="
echo "Date: $(date)"
echo ""

# Create log directory
mkdir -p cluster/logs

# --- Phase 1: Quick Validation ---
echo "Submitting Phase 1 (validation)..."
P1=$(sbatch --parsable cluster/jobs/phase1_validation.sh)
echo "  Phase 1 job: ${P1}"

# --- Phase 2: Core Experiments (depends on Phase 1) ---
echo "Submitting Phase 2 (core)..."
P2_JOBS=""
for script in cluster/jobs/phase2_*.sh; do
    JID=$(sbatch --parsable --dependency=afterok:${P1} "${script}")
    P2_JOBS="${P2_JOBS}:${JID}"
    echo "  ${script##*/}: ${JID}"
done
P2_JOBS="${P2_JOBS#:}"  # Remove leading colon

# --- Phase 3: Ablations (depends on all Phase 2 jobs) ---
echo "Submitting Phase 3 (ablations)..."
P3_JOBS=""
for script in cluster/jobs/phase3_*.sh; do
    JID=$(sbatch --parsable --dependency=afterok:${P2_JOBS} "${script}")
    P3_JOBS="${P3_JOBS}:${JID}"
    echo "  ${script##*/}: ${JID}"
done
P3_JOBS="${P3_JOBS#:}"

# --- Phase 4: Seed Sweeps (depends on all Phase 3 jobs) ---
echo "Submitting Phase 4 (seeds)..."
P4_JOBS=""
for script in cluster/jobs/phase4_*.sh; do
    JID=$(sbatch --parsable --dependency=afterok:${P3_JOBS} "${script}")
    P4_JOBS="${P4_JOBS}:${JID}"
    echo "  ${script##*/}: ${JID}"
done

# --- Write Job Manifest ---
echo ""
echo "=== Job Manifest ==="
echo "Phase 1 (validation): ${P1}"
echo "Phase 2 (core):       ${P2_JOBS}"
echo "Phase 3 (ablation):   ${P3_JOBS}"
echo "Phase 4 (seeds):      ${P4_JOBS}"

# Save manifest to file
cat > cluster/job-manifest.txt <<MANIFEST
# Job Manifest -- $(date)
# Phase 1 (validation)
${P1}
# Phase 2 (core)
$(echo ${P2_JOBS} | tr ':' '\n')
# Phase 3 (ablation)
$(echo ${P3_JOBS} | tr ':' '\n')
# Phase 4 (seeds)
$(echo ${P4_JOBS} | tr ':' '\n')
MANIFEST

echo ""
echo "Manifest written to cluster/job-manifest.txt"
echo "Monitor with: bash cluster/monitor.sh"
```

### Fan-Out / Fan-In Pattern

```bash
# Fan-out: multiple independent jobs after a single predecessor
SETUP_ID=$(sbatch --parsable setup.sh)
JOB_A=$(sbatch --parsable --dependency=afterok:$SETUP_ID job_a.sh)
JOB_B=$(sbatch --parsable --dependency=afterok:$SETUP_ID job_b.sh)
JOB_C=$(sbatch --parsable --dependency=afterok:$SETUP_ID job_c.sh)

# Fan-in: single job after all predecessors complete
AGGREGATE=$(sbatch --parsable --dependency=afterok:$JOB_A:$JOB_B:$JOB_C aggregate.sh)
```

## Job Monitoring

### Status Checking Script

```bash
#!/bin/bash
# monitor.sh -- Check status of all experiment jobs

echo "=== Job Status at $(date) ==="
echo ""

# Read job IDs from manifest
if [ ! -f cluster/job-manifest.txt ]; then
    echo "No job manifest found. Run launch.sh first."
    exit 1
fi

# Show all jobs from manifest
JOB_IDS=$(grep -v '^#' cluster/job-manifest.txt | tr '\n' ',' | sed 's/,$//')
if [ -n "$JOB_IDS" ]; then
    echo "--- Running / Pending ---"
    squeue -j "$JOB_IDS" -o "%.10i %.30j %.8T %.10M %.10l %.6D %.4C %.12P %R" 2>/dev/null || true
    echo ""
    echo "--- Completed / Failed ---"
    sacct -j "$JOB_IDS" --format=JobID,JobName%30,Partition,State,ExitCode,Elapsed,MaxRSS -n 2>/dev/null || true
fi

echo ""
echo "--- Summary ---"
RUNNING=$(squeue -j "$JOB_IDS" -t RUNNING -h 2>/dev/null | wc -l)
PENDING=$(squeue -j "$JOB_IDS" -t PENDING -h 2>/dev/null | wc -l)
COMPLETED=$(sacct -j "$JOB_IDS" --format=State -n 2>/dev/null | grep -c "COMPLETED" || echo 0)
FAILED=$(sacct -j "$JOB_IDS" --format=State -n 2>/dev/null | grep -c "FAILED" || echo 0)

echo "Running:   ${RUNNING}"
echo "Pending:   ${PENDING}"
echo "Completed: ${COMPLETED}"
echo "Failed:    ${FAILED}"
```

### Monitoring Commands

```bash
# Watch your jobs update in real time
watch -n 30 'squeue -u $USER -o "%.10i %.25j %.8T %.10M %.10l %.12P"'

# Check GPU utilization for a running job
srun --jobid=<jobid> nvidia-smi

# View job output in real time
tail -f cluster/logs/<job_name>_<job_id>.out
```

## Preemption Recovery

### Checkpoint + Auto-Resubmit Pattern

For jobs on preemptible partitions (`ou_bcs_low`):

```bash
#!/bin/bash
#SBATCH --partition=ou_bcs_low
#SBATCH --requeue
#SBATCH --signal=B:SIGTERM@120
#SBATCH --open-mode=append

# Append mode ensures logs accumulate across requeues

# The SIGTERM handler in the Python script should:
# 1. Save a checkpoint
# 2. Exit cleanly (exit code 0)
# SLURM --requeue will resubmit the job
# The checkpoint resume logic at the top of the script picks up where it left off

REQUEUE_COUNT=${SLURM_RESTART_COUNT:-0}
echo "Job start (requeue count: ${REQUEUE_COUNT})"

# ... (standard resume logic from template above)
```

### Python SIGTERM Handler

```python
import signal
import sys

class PreemptionHandler:
    def __init__(self, checkpoint_fn):
        self.checkpoint_fn = checkpoint_fn
        signal.signal(signal.SIGTERM, self._handle)

    def _handle(self, signum, frame):
        print("SIGTERM received -- saving checkpoint for requeue...")
        self.checkpoint_fn()
        sys.exit(0)

# Usage:
handler = PreemptionHandler(lambda: trainer.save_checkpoint("latest.pt"))
```

## Resource Cleanup on Abort

### Trap-Based Cleanup

```bash
#!/bin/bash

# Define cleanup function
cleanup() {
    echo "Cleaning up job ${SLURM_JOB_ID}..."
    # Kill any background processes
    kill $(jobs -p) 2>/dev/null
    # Optional: remove temporary files
    rm -rf /scratch/$USER/project/tmp/${SLURM_JOB_ID}
    echo "Cleanup complete."
}

# Register cleanup on EXIT (covers normal exit, error, and signal)
trap cleanup EXIT

# ... rest of the job script
```

## Common Pitfalls

1. **Forgetting `--parsable`**: Without it, `sbatch` returns a human-readable string, not just the job ID. Dependency chains break.

2. **Wrong time format**: Use `HH:MM:SS` for hours or `D-HH:MM:SS` for days. `7-00:00:00` = 7 days. `7:00:00` = 7 hours.

3. **Log directory does not exist**: SLURM will silently fail if the `--output` directory is missing. Always `mkdir -p cluster/logs` before submitting.

4. **Memory vs. memory-per-cpu**: `--mem` is per node. `--mem-per-cpu` is per CPU core. Use `--mem` for clarity.

5. **Array job log naming**: Use `%A` (master job ID) and `%a` (array index), not `%j` (which gives the individual sub-job ID).

6. **Dependency on array jobs**: `--dependency=afterok:<array_job_id>` waits for ALL array tasks. To depend on a single task, use `<array_job_id>_<index>`.

7. **Scratch purge**: Files on `/scratch/` may be purged after ~30 days of inactivity. Always copy results to `/home/` after completion.

8. **GPU type mismatch**: If your code assumes A100 but lands on V100 (on `mit_normal_gpu`), it may OOM. Specify `--gres=gpu:a100:1` if needed, or use `--constraint=a100`.
