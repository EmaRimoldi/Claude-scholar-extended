# SLURM Script Examples

Working examples for the ICL Circuit-Algorithm Bridge experiment.

## Single Run Script

`cluster/jobs/phase2_gpt2_124m_linreg_full.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=icl-gpt2_124m-linreg-full
#SBATCH --partition=pi_tpoggio
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=cluster/logs/%x_%j.out
#SBATCH --error=cluster/logs/%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=user@mit.edu
#SBATCH --requeue

# --- Environment ---
module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
source ~/envs/icl-bridge/bin/activate
cd /home/$USER/icl-bridge/code

# --- Checkpoint Resume ---
CHECKPOINT_DIR="/scratch/$USER/icl-bridge/checkpoints/${SLURM_JOB_NAME}"
mkdir -p ${CHECKPOINT_DIR}

RESUME_FLAG=""
if [ -f "${CHECKPOINT_DIR}/latest.pt" ]; then
    RESUME_FLAG="--resume_from_checkpoint ${CHECKPOINT_DIR}/latest.pt"
    echo "Resuming from: ${CHECKPOINT_DIR}/latest.pt"
fi

# --- Run ---
echo "Starting ${SLURM_JOB_NAME} on $(hostname) at $(date)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"

python run_experiment.py \
    --model gpt2-124m \
    --task linear_regression \
    --method full \
    --seed ${SLURM_ARRAY_TASK_ID:-0} \
    --output_dir /scratch/$USER/icl-bridge/outputs/${SLURM_JOB_NAME} \
    --checkpoint_dir ${CHECKPOINT_DIR} \
    --checkpoint_every 500 \
    ${RESUME_FLAG}

EXIT_CODE=$?

# --- Copy Results ---
if [ $EXIT_CODE -eq 0 ]; then
    rsync -av /scratch/$USER/icl-bridge/outputs/${SLURM_JOB_NAME}/ \
              /home/$USER/icl-bridge/results/${SLURM_JOB_NAME}/
fi

echo "Finished at $(date) with exit code ${EXIT_CODE}"
exit $EXIT_CODE
```

## Seed Sweep Array Job

`cluster/jobs/phase4_gpt2_124m_linreg_full_seeds.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=icl-gpt2_124m-linreg-full-seeds
#SBATCH --partition=ou_bcs_low
#SBATCH --array=0-4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=cluster/logs/%x_%A_%a.out
#SBATCH --error=cluster/logs/%x_%A_%a.err
#SBATCH --requeue

module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
source ~/envs/icl-bridge/bin/activate
cd /home/$USER/icl-bridge/code

SEED=${SLURM_ARRAY_TASK_ID}
RUN_NAME="gpt2_124m-linreg-full-seed_${SEED}"

CHECKPOINT_DIR="/scratch/$USER/icl-bridge/checkpoints/${RUN_NAME}"
mkdir -p ${CHECKPOINT_DIR}

RESUME_FLAG=""
if [ -f "${CHECKPOINT_DIR}/latest.pt" ]; then
    RESUME_FLAG="--resume_from_checkpoint ${CHECKPOINT_DIR}/latest.pt"
fi

python run_experiment.py \
    --model gpt2-124m \
    --task linear_regression \
    --method full \
    --seed ${SEED} \
    --output_dir /scratch/$USER/icl-bridge/outputs/${RUN_NAME} \
    --checkpoint_dir ${CHECKPOINT_DIR} \
    --checkpoint_every 500 \
    ${RESUME_FLAG}

if [ $? -eq 0 ]; then
    rsync -av /scratch/$USER/icl-bridge/outputs/${RUN_NAME}/ \
              /home/$USER/icl-bridge/results/${RUN_NAME}/
fi
```

## Master Launch Script

`cluster/launch.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "=== ICL Bridge Experiment Launch ==="
echo "Date: $(date)"
echo ""

mkdir -p cluster/logs

# --- Phase 1: Quick Validation ---
echo "[Phase 1] Submitting validation run..."
P1=$(sbatch --parsable cluster/jobs/phase1_validation.sh)
echo "  Job ${P1}: phase1_validation"

# --- Phase 2: Core Experiments (depends on Phase 1) ---
echo "[Phase 2] Submitting core experiments (dependency: Phase 1)..."
P2_IDS=""
for script in cluster/jobs/phase2_*.sh; do
    JID=$(sbatch --parsable --dependency=afterok:${P1} "${script}")
    P2_IDS="${P2_IDS}:${JID}"
    echo "  Job ${JID}: $(basename ${script})"
done
P2_IDS="${P2_IDS#:}"

# --- Phase 3: Ablations (depends on Phase 2) ---
echo "[Phase 3] Submitting ablation experiments (dependency: Phase 2)..."
P3_IDS=""
for script in cluster/jobs/phase3_*.sh; do
    JID=$(sbatch --parsable --dependency=afterok:${P2_IDS} "${script}")
    P3_IDS="${P3_IDS}:${JID}"
    echo "  Job ${JID}: $(basename ${script})"
done
P3_IDS="${P3_IDS#:}"

# --- Phase 4: Seed Sweeps (depends on Phase 3) ---
echo "[Phase 4] Submitting seed sweeps (dependency: Phase 3)..."
P4_IDS=""
for script in cluster/jobs/phase4_*.sh; do
    JID=$(sbatch --parsable --dependency=afterok:${P3_IDS} "${script}")
    P4_IDS="${P4_IDS}:${JID}"
    echo "  Job ${JID}: $(basename ${script})"
done
P4_IDS="${P4_IDS#:}"

# --- Write Manifest ---
cat > cluster/job-manifest.txt <<EOF
# ICL Bridge Job Manifest -- $(date)
# Phase 1 (validation)
${P1}
# Phase 2 (core)
$(echo ${P2_IDS} | tr ':' '\n')
# Phase 3 (ablation)
$(echo ${P3_IDS} | tr ':' '\n')
# Phase 4 (seeds)
$(echo ${P4_IDS} | tr ':' '\n')
EOF

echo ""
echo "=== Summary ==="
echo "Phase 1: 1 job"
echo "Phase 2: $(echo ${P2_IDS} | tr ':' '\n' | wc -l | tr -d ' ') jobs"
echo "Phase 3: $(echo ${P3_IDS} | tr ':' '\n' | wc -l | tr -d ' ') jobs"
echo "Phase 4: $(echo ${P4_IDS} | tr ':' '\n' | wc -l | tr -d ' ') jobs"
echo ""
echo "Manifest: cluster/job-manifest.txt"
echo "Monitor:  bash cluster/monitor.sh"
```

## Monitoring Script Snippet

`cluster/monitor.sh`:

```bash
#!/bin/bash
echo "=== Job Status at $(date) ==="

if [ ! -f cluster/job-manifest.txt ]; then
    echo "No job manifest found. Run launch.sh first."
    exit 1
fi

JOB_IDS=$(grep -v '^#' cluster/job-manifest.txt | grep -v '^$' | tr '\n' ',' | sed 's/,$//')

echo ""
echo "--- Active Jobs ---"
squeue -j "${JOB_IDS}" -o "%.10i %.35j %.8T %.10M %.10l %.12P" 2>/dev/null || echo "(none)"

echo ""
echo "--- Completed ---"
sacct -j "${JOB_IDS}" --format=JobID,JobName%35,State,ExitCode,Elapsed -n 2>/dev/null || echo "(none)"

echo ""
RUNNING=$(squeue -j "${JOB_IDS}" -t RUNNING -h 2>/dev/null | wc -l | tr -d ' ')
PENDING=$(squeue -j "${JOB_IDS}" -t PENDING -h 2>/dev/null | wc -l | tr -d ' ')
echo "Running: ${RUNNING}  |  Pending: ${PENDING}"
```
