# MIT Engaging Cluster Configuration

Complete reference for the MIT Engaging cluster, covering access, partitions, modules, filesystem, SLURM commands, and operational patterns.

## Access

### SSH Login

```bash
ssh <username>@orcd-login.mit.edu
```

- Authenticate with MIT Kerberos or SSH keys
- Login nodes are for job submission and light file management only -- do not run experiments on login nodes
- Multiple login nodes behind a load balancer; hostname may vary between sessions

### File Transfer

```bash
# SCP
scp local_file <username>@orcd-login.mit.edu:/home/<username>/path/

# rsync (preferred for large transfers)
rsync -avz --progress local_dir/ <username>@orcd-login.mit.edu:/home/<username>/path/
```

## Partitions

### Partition Table

| Partition | GPU Type | GPUs/Node | CPUs/Node | RAM/Node | Time Limit | Priority | Preemption | Notes |
|-----------|----------|-----------|-----------|----------|------------|----------|------------|-------|
| `pi_tpoggio` | A100 80GB | 8 | 192 | ~1TB | 7 days | Dedicated | No | Primary partition for lab members |
| `ou_bcs_normal` | A100 80GB / H100 80GB | 8 (A100) or 4 (H100) | Varies | Varies | 1 day | Normal | No | Overflow for medium runs |
| `ou_bcs_low` | A100 80GB / H100 80GB | 8 (A100) or 4 (H100) | Varies | Varies | 1 day | Low | Yes | Background jobs, may be preempted |
| `ou_bcs_high` | A100 80GB / H100 80GB | 8 (A100) or 4 (H100) | Varies | Varies | 4 hours | High | No | Quick validation, debugging |
| `mit_normal_gpu` | Mixed (V100, A100) | Varies | Varies | Varies | 1 day | Normal | No | General MIT pool, last resort |

### Partition Selection Guidelines

- **`pi_tpoggio`**: First choice for all lab work. 7-day limit supports long training runs. 8 GPUs per node allows packing 8 concurrent single-GPU jobs or running multi-GPU distributed training.
- **`ou_bcs_normal`**: Use when pi_tpoggio queue is long or for runs that fit within 1 day. Check for H100 availability -- faster than A100 for most workloads.
- **`ou_bcs_low`**: Use for non-critical seed sweeps and background jobs. Must implement checkpoint-resume because jobs can be preempted at any time.
- **`ou_bcs_high`**: Use for quick validation runs (< 4 hours). Higher scheduling priority means shorter queue wait times. Ideal for Phase 1 smoke tests.
- **`mit_normal_gpu`**: Last resort. Mixed hardware makes performance unpredictable. Use only if all other partitions are fully occupied.

### Checking Partition Status

```bash
# Show all partitions and their state
sinfo -p pi_tpoggio,ou_bcs_normal,ou_bcs_low,ou_bcs_high

# Show available GPUs per partition
sinfo -p pi_tpoggio -O partition,gres,available,statecompact

# Show running and pending jobs on a partition
squeue -p pi_tpoggio

# Show your running jobs
squeue -u $USER
```

## Module System

### Required Modules

```bash
# CUDA toolkit
module load cuda/12.4.0

# cuDNN
module load cudnn/9.8.0.87-cuda12
```

### Listing and Searching Modules

```bash
# List all loaded modules
module list

# Search for available CUDA versions
module avail cuda

# Search for Python versions
module avail python

# Show module details
module show cuda/12.4.0
```

### Virtual Environment Setup

```bash
# Create a virtualenv (do this once)
module load cuda/12.4.0
module load cudnn/9.8.0.87-cuda12
python -m venv ~/envs/<project_env>
source ~/envs/<project_env>/bin/activate
pip install -r requirements.txt

# In sbatch scripts, activate the same way
source ~/envs/<project_env>/bin/activate
```

## Filesystem Layout

### Storage Tiers

| Path | Purpose | Quota | Speed | Backed Up | Purge Policy |
|------|---------|-------|-------|-----------|--------------|
| `/home/<user>/` | Code, configs, small results | ~50 GB (varies) | NFS (slow) | Yes | Never |
| `/pool001/<lab>/` | Shared datasets, pretrained models | Large (lab-level) | NFS (medium) | No | Never |
| `/scratch/<user>/` | Active training, checkpoints, large outputs | Large | Lustre (fast) | No | Purged after ~30 days of inactivity |

### Best Practices

- **Code**: Keep in `/home/` under Git. Small, backed up, always available.
- **Datasets**: Store in `/pool001/<lab>/shared/datasets/`. Symlink into scratch for fast I/O during training.
- **Checkpoints**: Write to `/scratch/` during training. Copy final results to `/home/` after each phase.
- **Logs**: SLURM stdout/stderr go to `/home/<user>/<project>/cluster/logs/`.
- **Cleanup**: Remove scratch checkpoints after successful result copy. Scratch is purged automatically after inactivity.

### Checking Quotas

```bash
# Home directory usage
du -sh /home/$USER/

# Scratch usage
du -sh /scratch/$USER/

# Check filesystem quotas (if available)
quota -s
```

## SLURM Commands Reference

### Job Submission

```bash
# Submit a job
sbatch job.sh

# Submit with overrides
sbatch --partition=ou_bcs_high --time=01:00:00 job.sh

# Submit an array job (seeds 0-4)
sbatch --array=0-4 seed_sweep.sh

# Submit with dependency
sbatch --dependency=afterok:12345 next_phase.sh

# Submit with multiple dependencies
sbatch --dependency=afterok:12345:12346:12347 next_phase.sh
```

### Job Monitoring

```bash
# Show your jobs (running and pending)
squeue -u $USER

# Show detailed job info
squeue -u $USER -o "%.10i %.20j %.8T %.10M %.10l %.6D %.4C %.10P %R"

# Show job details by ID
scontrol show job <jobid>

# Show completed job statistics
sacct -j <jobid> --format=JobID,JobName,Partition,AllocCPUS,State,ExitCode,Elapsed,MaxRSS,MaxVMSize

# Show GPU utilization for running jobs
sstat -j <jobid> --format=JobID,MaxRSS,MaxVMSize
```

### Job Control

```bash
# Cancel a job
scancel <jobid>

# Cancel all your jobs
scancel -u $USER

# Cancel all jobs in an array
scancel <array_jobid>

# Hold a pending job
scontrol hold <jobid>

# Release a held job
scontrol release <jobid>
```

### Job Arrays

```bash
#!/bin/bash
#SBATCH --array=0-4          # 5 tasks (seeds 0-4)
#SBATCH --job-name=sweep

# Access the array index
SEED=${SLURM_ARRAY_TASK_ID}

python train.py --seed $SEED
```

Array syntax variations:
- `--array=0-4` -- indices 0, 1, 2, 3, 4
- `--array=0-4%2` -- max 2 concurrent tasks
- `--array=1,3,5,7` -- specific indices
- `--array=0-100:10` -- step size of 10 (0, 10, 20, ...)

### Dependency Chains

```bash
# Submit Phase 1
PHASE1_ID=$(sbatch --parsable phase1.sh)

# Submit Phase 2 after Phase 1 succeeds
PHASE2_ID=$(sbatch --parsable --dependency=afterok:$PHASE1_ID phase2.sh)

# Submit Phase 3 after Phase 2 succeeds
PHASE3_ID=$(sbatch --parsable --dependency=afterok:$PHASE2_ID phase3.sh)

# Submit after ANY of the listed jobs complete (regardless of status)
sbatch --dependency=afterany:$JOB1:$JOB2 cleanup.sh
```

Dependency types:
- `afterok:<jobid>` -- run after job completes successfully (exit code 0)
- `afternotok:<jobid>` -- run after job fails (non-zero exit code)
- `afterany:<jobid>` -- run after job completes (any exit code)
- `after:<jobid>` -- run after job starts (not commonly used)
- `singleton` -- only one job with this name can run at a time

### Preemption Handling

Jobs on `ou_bcs_low` can be preempted. To handle this:

```bash
#SBATCH --requeue                    # Auto-requeue if preempted
#SBATCH --signal=B:SIGTERM@120       # Send SIGTERM 120s before kill

# In Python: catch SIGTERM and save checkpoint
import signal
import sys

def handle_preemption(signum, frame):
    print("Preemption signal received. Saving checkpoint...")
    save_checkpoint(model, optimizer, epoch, step)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_preemption)
```

### Queue Monitoring

```bash
# Overview of cluster utilization
sinfo -s

# Show pending jobs and estimated start times
squeue -u $USER --start

# Show partition utilization
sinfo -p pi_tpoggio -N -l

# Show fairshare priority (affects queue position)
sshare -u $USER

# Historical job accounting
sacct -u $USER --starttime=2026-03-01 --format=JobID,JobName,Partition,Elapsed,State,MaxRSS
```

## Storage Quotas and Cleanup

### Monitoring Usage

```bash
# Check home quota
quota -s

# Check scratch usage
du -sh /scratch/$USER/*

# Find large files on scratch
find /scratch/$USER/ -size +1G -exec ls -lh {} \;
```

### Cleanup Strategy

- After each experiment phase completes successfully, `rsync` results from scratch to home
- Remove scratch checkpoints for completed phases (keep only the final model)
- Compress and archive old experiment data
- Scratch files inactive for ~30 days may be automatically purged
