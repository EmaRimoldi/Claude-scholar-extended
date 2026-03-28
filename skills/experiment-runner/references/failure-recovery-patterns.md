# Failure Recovery Patterns

## OOM (Out of Memory)

### Detection

CUDA OOM and system OOM have different signatures:

```python
def detect_oom(job_id: str, log_path: str) -> bool:
    """Detect OOM from SLURM state and log content."""
    # Check SLURM state first (fast)
    state = get_sacct_state(job_id)
    if state == "OUT_OF_MEMORY":
        return True

    # Check log content (catches CUDA OOM not caught by SLURM)
    oom_patterns = [
        "CUDA out of memory",
        "RuntimeError: CUDA error: out of memory",
        "torch.cuda.OutOfMemoryError",
        "Killed",                    # OS OOM killer
        "oom-kill",                  # cgroup OOM
        "Cannot allocate memory",    # CPU OOM
    ]
    with open(log_path) as f:
        content = f.read()
    return any(pattern in content for pattern in oom_patterns)
```

### Recovery Strategies

Apply in order until the run succeeds:

1. **Reduce batch size by 50%**: Most common fix. Update config override and resubmit.

```bash
# Original: batch_size=64
# Retry 1: batch_size=32
sbatch --export=ALL,BATCH_SIZE=32 scripts/run_experiment.sh
```

2. **Enable gradient checkpointing**: Trades compute for memory. Add to training config.

```yaml
# Hydra override
training.gradient_checkpointing: true
```

3. **Enable mixed precision (fp16/bf16)**: Reduces memory by ~50% for activations.

```yaml
training.fp16: true
# or for newer GPUs:
training.bf16: true
```

4. **Request a node with more memory**: If available, use `--mem` or `--gres=gpu:a100_80gb:1`.

5. **Reduce model size**: Last resort. Smaller hidden dimensions or fewer layers. Flag this as a significant change that may affect results.

### OOM Recovery Record

```json
{
  "error_type": "OOM",
  "original_config": { "batch_size": 64, "fp16": false },
  "recovery_action": "reduce_batch_size",
  "new_config": { "batch_size": 32, "fp16": false },
  "retry_number": 1
}
```

## NaN (Not a Number)

### Detection

```python
def detect_nan(log_path: str, metrics_path: str | None = None) -> bool:
    """Detect NaN in training logs or output metrics."""
    # Check training log
    nan_patterns = [
        "loss.*nan",
        "NaN",
        "nan loss",
        "loss is NaN",
        "stopping training.*nan",
    ]
    with open(log_path) as f:
        content = f.read().lower()
    if any(re.search(p, content, re.IGNORECASE) for p in nan_patterns):
        return True

    # Check metrics file if available
    if metrics_path and os.path.exists(metrics_path):
        import json, math
        with open(metrics_path) as f:
            metrics = json.load(f)
        return any(
            isinstance(v, float) and math.isnan(v)
            for v in metrics.values()
        )
    return False
```

### Diagnosis Checklist

NaN is usually NOT recoverable by simple resubmission. Diagnose root cause first:

| Cause | Indicator | Fix |
|-------|-----------|-----|
| **Gradient explosion** | Loss spikes then NaN; gradients > 1e6 | Add gradient clipping (`max_grad_norm: 1.0`) |
| **Learning rate too high** | NaN within first few steps | Reduce LR by 10x; add warmup |
| **Bad data sample** | NaN at specific step (reproducible) | Check that data sample for missing values or infinities |
| **Numerical instability** | NaN in specific layer (e.g., softmax, log) | Use numerically stable implementations; add epsilon |
| **Mixed precision overflow** | NaN with fp16 enabled | Use bf16 instead, or disable mixed precision |

### NaN Recovery Policy

```
1. Do NOT auto-resubmit NaN runs (unlike OOM/timeout)
2. Log the failure with step number and last valid loss
3. Flag the run for manual investigation
4. Mark status as "nan_flagged" in experiment-state.json
5. Continue with remaining runs in the phase
```

## Timeout

### Detection

```python
def detect_timeout(job_id: str) -> bool:
    """Detect timeout from SLURM state."""
    state = get_sacct_state(job_id)
    return state == "TIMEOUT"
```

### Recovery from Checkpoint

```python
def recover_timeout(
    run_id: str,
    original_walltime: str,
    checkpoint_dir: str,
) -> dict:
    """Prepare timeout recovery: find checkpoint, extend walltime."""
    # Find latest checkpoint
    checkpoint = find_latest_checkpoint(checkpoint_dir)
    if checkpoint is None:
        return {
            "action": "resubmit_from_scratch",
            "new_walltime": multiply_walltime(original_walltime, 2.0),
            "note": "No checkpoint found. Doubling walltime.",
        }

    return {
        "action": "resume_from_checkpoint",
        "checkpoint_path": checkpoint,
        "new_walltime": multiply_walltime(original_walltime, 1.5),
        "note": f"Resuming from {checkpoint}. Walltime increased by 50%.",
    }
```

### Walltime Extension Strategy

- **First timeout**: Extend to 1.5x original walltime
- **Second timeout**: Extend to 2.0x original walltime
- **Third timeout**: Flag as requiring manual intervention; may need algorithm optimization

```python
def multiply_walltime(walltime: str, factor: float) -> str:
    """Multiply a SLURM walltime string (HH:MM:SS) by a factor."""
    parts = walltime.split(":")
    total_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    new_seconds = int(total_seconds * factor)
    hours, remainder = divmod(new_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
```

## Preemption

### Detection

Preemption occurs when a higher-priority job takes resources:

```python
def detect_preemption(job_id: str) -> bool:
    """Detect preemption from SLURM state or exit code."""
    state = get_sacct_state(job_id)
    if state == "PREEMPTED":
        return True

    # Some clusters report preemption as exit code 271
    exit_code = get_sacct_exit_code(job_id)
    if exit_code == "271:0":
        return True

    # SIGTERM (signal 15) can also indicate preemption
    if exit_code.endswith(":15"):
        return True

    return False
```

### Checkpoint Callback for Preemption

Train scripts should handle SIGTERM gracefully:

```python
import signal

def setup_preemption_handler(trainer):
    """Register signal handler to save checkpoint on preemption."""
    def handler(signum, frame):
        print(f"Received signal {signum}, saving checkpoint...")
        trainer.save_checkpoint("checkpoint_preempted.pt")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGUSR1, handler)  # Some clusters use SIGUSR1
```

### Auto-Resubmit After Preemption

```bash
# Resubmit from last checkpoint, start immediately
sbatch --begin=now \
       --export=ALL,RESUME_CHECKPOINT=outputs/${RUN_ID}/checkpoints/checkpoint_preempted.pt \
       scripts/run_experiment.sh
```

Preempted runs do NOT count against the retry limit (preemption is not a run error).

## Node Failure

### Detection

```python
def detect_node_failure(job_id: str) -> bool:
    """Detect node failure from SLURM state."""
    state = get_sacct_state(job_id)
    return state == "NODE_FAIL"
```

### Recovery: Retry on Different Node

```bash
# Get the failed node name
FAILED_NODE=$(sacct --jobs=$JOB_ID --format=NodeList --noheader | head -1 | tr -d ' ')

# Resubmit excluding the failed node
sbatch --exclude=$FAILED_NODE scripts/run_experiment.sh
```

Node failures are infrastructure issues and do NOT count against the retry limit.

## Common Recovery Patterns

### Exponential Backoff

```python
import time

def get_retry_delay(retry_count: int, base_seconds: int = 60) -> int:
    """Calculate delay before next retry with exponential backoff."""
    return base_seconds * (2 ** retry_count)
    # retry 0: 60s, retry 1: 120s, retry 2: 240s
```

### Max Retry Policy

```python
MAX_RETRIES = 3  # Per run, configurable

def should_retry(run: dict) -> bool:
    """Decide whether to retry a failed run."""
    error_type = run["error_type"]

    # Never auto-retry NaN (needs investigation)
    if error_type == "NaN":
        return False

    # Preemption and node failure don't count toward retries
    if error_type in ("PREEMPTED", "NODE_FAIL"):
        return True

    # OOM, timeout: retry up to MAX_RETRIES
    return run.get("retry_count", 0) < MAX_RETRIES
```

### Failure Log Format

Every failure is recorded with a consistent structure:

```json
{
  "run_id": "p2_contrastive_bci4_s3",
  "job_id": "12389",
  "error_type": "OOM",
  "slurm_state": "OUT_OF_MEMORY",
  "exit_code": "0:9",
  "timestamp": "2026-03-28T14:22:00Z",
  "retry_count": 1,
  "max_retries": 3,
  "log_snippet": "CUDA out of memory. Tried to allocate 2.00 GiB...",
  "recovery_action": "reduce_batch_size",
  "recovery_details": { "old_batch_size": 64, "new_batch_size": 32 },
  "resubmitted_job_id": "12401"
}
```

### End-of-Phase Failure Summary

After a phase completes, generate a summary of all failures:

```
Phase 2 Failure Summary:
  Total runs: 270
  Succeeded: 264
  Failed (recovered): 4 (3 OOM, 1 timeout)
  Failed (permanent): 2 (2 NaN -- flagged for investigation)
  Preempted (recovered): 3

  Action items:
  - Investigate NaN in p2_contrastive_bci4_s3 and p2_ablation1_bci4_s1
  - OOM trend: 3/4 OOM failures on node gpu-07, consider excluding
```
