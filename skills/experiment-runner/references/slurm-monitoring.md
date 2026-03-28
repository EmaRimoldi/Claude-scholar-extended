# SLURM Monitoring Reference

## squeue: Active Job Monitoring

### Useful Format Strings

Query running and pending jobs with custom output columns:

```bash
# Compact status for all user jobs
squeue -u $USER --format="%.8i %.40j %.2t %.10M %.6D %.4C %.20R"

# Columns: JobID, JobName, State, TimeUsed, NumNodes, NumCPUs, ReasonOrNodeList
```

**Common state codes**:
- `PD` -- Pending (waiting for resources)
- `R` -- Running
- `CG` -- Completing (finalizing)
- `CF` -- Configuring (nodes being prepared)

### Filtering by Job Name

Filter jobs belonging to a specific experiment phase:

```bash
# All Phase 1 jobs
squeue -u $USER --name="p1_*" --format="%.8i %.40j %.2t %.10M"

# Count running jobs in Phase 2
squeue -u $USER --name="p2_*" -t R --noheader | wc -l
```

### Filtering by Job State

```bash
# Only pending jobs (to estimate queue wait)
squeue -u $USER -t PD --format="%.8i %.40j %.20R"

# Only running jobs (to estimate completion)
squeue -u $USER -t R --format="%.8i %.40j %.10M %.10l"
# Columns include TimeUsed and TimeLimit
```

## sacct: Completed Job Information

### Querying Completed Jobs

```bash
# Detailed info for a specific job
sacct --jobs=12345 --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,MaxVMSize,AllocCPUS,AllocGRES

# All jobs from today
sacct --starttime=$(date +%Y-%m-%d) --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS
```

### Key sacct Fields

| Field | Purpose |
|-------|---------|
| `State` | Final state: COMPLETED, FAILED, TIMEOUT, OUT_OF_MEMORY, NODE_FAIL, PREEMPTED, CANCELLED |
| `ExitCode` | `exit_code:signal` format (e.g., `0:0` success, `1:0` error, `0:9` killed) |
| `Elapsed` | Wall time used |
| `MaxRSS` | Peak resident memory (useful for detecting near-OOM) |
| `MaxVMSize` | Peak virtual memory |
| `AllocGRES` | Allocated GPUs |

### Parsing Exit Codes

```bash
# Extract exit code for a job
sacct --jobs=12345 --format=ExitCode --noheader --parsable2
# Output: "1:0" means exit code 1, no signal
# Output: "0:9" means exit code 0, killed by signal 9 (SIGKILL)
# Output: "0:15" means exit code 0, killed by signal 15 (SIGTERM, preemption)
```

## Detecting Failure Types

### From SLURM State

```bash
STATE=$(sacct --jobs=$JOB_ID --format=State --noheader --parsable2 | head -1)

case "$STATE" in
    "COMPLETED")    echo "Success" ;;
    "FAILED")       echo "Check exit code and stderr" ;;
    "TIMEOUT")      echo "Walltime exceeded" ;;
    "OUT_OF_MEMORY")echo "OOM killed by SLURM" ;;
    "NODE_FAIL")    echo "Node hardware failure" ;;
    "PREEMPTED")    echo "Preempted by higher-priority job" ;;
    "CANCELLED")    echo "Cancelled by user or admin" ;;
esac
```

### From Log Patterns

```bash
# OOM detection in stderr/stdout
grep -l "CUDA out of memory" outputs/*/slurm-*.out
grep -l "RuntimeError: CUDA error: out of memory" outputs/*/slurm-*.out
grep -l "Killed" outputs/*/slurm-*.out  # OS-level OOM killer

# NaN detection in training logs
grep -l "loss.*nan" outputs/*/train.log
grep -l "NaN" outputs/*/train.log

# Gradient explosion indicators
grep -l "gradient.*overflow" outputs/*/train.log
grep -l "inf" outputs/*/train.log
```

### From Exit Codes

| Exit Code | Signal | Meaning |
|-----------|--------|---------|
| `0:0` | -- | Success |
| `1:0` | -- | General error (check stderr) |
| `2:0` | -- | Script error (missing file, bad argument) |
| `0:9` | SIGKILL | OOM killer or admin kill |
| `0:15` | SIGTERM | Preemption or cancellation |
| `0:12` | SIGUSR2 | SLURM step timeout |
| `271:0` | -- | Preempted (SLURM-specific) |

## Progress Calculation

### Basic Progress

```python
def calculate_progress(phase_runs: list[dict]) -> dict:
    """Calculate phase progress from run statuses."""
    total = len(phase_runs)
    completed = sum(1 for r in phase_runs if r["status"] == "COMPLETED")
    failed = sum(1 for r in phase_runs if r["status"] == "FAILED")
    running = sum(1 for r in phase_runs if r["status"] == "RUNNING")
    pending = total - completed - failed - running

    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "pending": pending,
        "percent": round(completed / total * 100, 1) if total > 0 else 0.0,
    }
```

### Estimated Time Remaining

```python
from datetime import datetime, timedelta

def estimate_remaining_time(
    completed_runs: list[dict],
    remaining_count: int,
) -> timedelta | None:
    """Estimate remaining wall time from completed run durations."""
    if not completed_runs:
        return None

    durations = [r["elapsed_seconds"] for r in completed_runs]
    avg_duration = sum(durations) / len(durations)

    # Account for parallelism (runs executing concurrently)
    running_count = max(1, len([r for r in completed_runs if r.get("parallel", False)]))
    estimated_seconds = (remaining_count / running_count) * avg_duration

    return timedelta(seconds=estimated_seconds)
```

## Automatic Alerting

### Email Notification via SLURM

Add to SLURM submission scripts:

```bash
#SBATCH --mail-type=END,FAIL,TIME_LIMIT_90
#SBATCH --mail-user=user@university.edu
```

**Mail types**:
- `END` -- job completed (success or failure)
- `FAIL` -- job failed
- `TIME_LIMIT_90` -- job reached 90% of walltime (early warning)

### Webhook Notification (Custom)

```python
import requests

def notify_webhook(event: str, details: dict, webhook_url: str) -> None:
    """Send notification to a webhook (Slack, Discord, etc.)."""
    payload = {
        "text": f"Experiment event: {event}",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*{event}*\n```{json.dumps(details, indent=2)}```"}}
        ],
    }
    requests.post(webhook_url, json=payload, timeout=10)
```

### Phase Completion Check Script

```bash
#!/bin/bash
# check_phase.sh -- Run periodically (cron or watch) to detect phase completion
PHASE=$1
EXPECTED_RUNS=$2

COMPLETED=$(sacct --name="${PHASE}_*" --state=COMPLETED --noheader | wc -l)
FAILED=$(sacct --name="${PHASE}_*" --state=FAILED,TIMEOUT,OUT_OF_MEMORY --noheader | wc -l)
TOTAL=$((COMPLETED + FAILED))

if [ "$TOTAL" -ge "$EXPECTED_RUNS" ]; then
    echo "Phase $PHASE complete: $COMPLETED succeeded, $FAILED failed"
    # Trigger gate evaluation
fi
```
