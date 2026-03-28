---
name: slurm-status
description: Show SLURM job status, queue, and pipeline job tracking. Displays active jobs, completed job results, and resource utilization.
args:
  - name: job_id
    description: "Optional: specific job ID to check"
    required: false
tags: [SLURM, Cluster, Monitoring]
---

# /slurm-status - SLURM Job Status Dashboard

Show the current state of SLURM jobs and cluster resources.

## Workflow

### 1. Show user's active jobs

Run:
```bash
squeue -u $USER -o "%.10i %.12P %.30j %.2t %.10M %.4D %.4C %.10m %R"
```

Display the results in a formatted table.

### 2. If a specific job_id "$job_id" was provided

Run:
```bash
python3 scripts/slurm/submit.py status $job_id --output
```

Show the job state, exit code, elapsed time, and last 20 lines of output.

### 3. Show pipeline SLURM jobs

Check `pipeline-state.json` for any steps with `slurm_job_id` set. For each, check its status:

```bash
python3 scripts/slurm/submit.py status <job_id>
```

### 4. Show recent completed jobs

```bash
sacct -u $USER --starttime=$(date -d '24 hours ago' +%Y-%m-%d) --format=JobID,JobName,Partition,State,ExitCode,Elapsed,MaxRSS,NodeList --parsable2 | head -20
```

### 5. Show cluster utilization summary

```bash
sinfo -o "%P %a %D %T" --noheader | sort
```

Summarize: how many nodes are idle vs allocated per GPU partition.

## Output Format

```
━━━ SLURM Status ━━━

Active Jobs: N
  [job table]

Recent Jobs (24h): M
  [job table]

Pipeline Jobs:
  Step 10 (run-experiment): Job 12345 — COMPLETED
  Step 5 (build-data): Job 12340 — RUNNING

Cluster GPU Availability:
  mit_normal_gpu: 3/13 nodes idle (L40S×4, H100×4, H200×8)
  mit_preemptable: 45/78 nodes idle
```
