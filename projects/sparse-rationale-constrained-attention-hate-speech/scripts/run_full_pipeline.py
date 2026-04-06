#!/usr/bin/env python3
"""Autonomous pipeline runner for sparse-hate experiment.

Monitors Wave 1 training, then submits Wave 2, then runs phases 3-5.
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
EXPERIMENT_STATE_FILE = PROJECT_DIR / "experiment-state.json"


def log(msg: str) -> None:
    """Print timestamped log message."""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {msg}")


def load_state() -> dict:
    """Load experiment state from JSON."""
    if EXPERIMENT_STATE_FILE.exists():
        with open(EXPERIMENT_STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    """Save experiment state to JSON."""
    with open(EXPERIMENT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def wait_for_jobs(job_ids: list[int], poll_interval: int = 60) -> bool:
    """Wait for all SLURM jobs to complete.

    Args:
        job_ids: List of SLURM job IDs
        poll_interval: Seconds between status checks

    Returns:
        True if all jobs completed successfully, False if any failed
    """
    completed = set()
    failed = set()

    while len(completed) + len(failed) < len(job_ids):
        # Check job status
        for job_id in job_ids:
            if job_id in completed or job_id in failed:
                continue

            result = subprocess.run(
                ["squeue", "-j", str(job_id), "-h"],
                capture_output=True,
                text=True,
            )

            # If job not in queue, check exit status
            if not result.stdout.strip():
                # Job is not in queue - check if it completed
                exit_result = subprocess.run(
                    ["sacct", "-j", str(job_id), "-p"],
                    capture_output=True,
                    text=True,
                )

                if "COMPLETED" in exit_result.stdout:
                    completed.add(job_id)
                    log(f"Job {job_id} completed successfully")
                elif "FAILED" in exit_result.stdout or "TIMEOUT" in exit_result.stdout:
                    failed.add(job_id)
                    log(f"Job {job_id} failed or timed out")
                    print(exit_result.stdout)
                # else: still processing, check again next iteration

        if len(completed) + len(failed) < len(job_ids):
            log(f"Progress: {len(completed)} completed, {len(failed)} failed, waiting...")
            time.sleep(poll_interval)

    return len(failed) == 0


def submit_wave2() -> list[int]:
    """Submit Wave 2 training jobs."""
    job_ids = []

    log("Submitting Wave 2 Job A: M2 + M4a")
    result = subprocess.run(
        ["sbatch", "scripts/train.sh", "--conditions", "M2", "M4a"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    job_id = int(result.stdout.split()[-1])
    job_ids.append(job_id)
    log(f"Wave 2 Job A submitted: {job_id}")

    time.sleep(2)

    log("Submitting Wave 2 Job B: M4c + M5")
    result = subprocess.run(
        ["sbatch", "scripts/train.sh", "--conditions", "M4c", "M5"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    job_id = int(result.stdout.split()[-1])
    job_ids.append(job_id)
    log(f"Wave 2 Job B submitted: {job_id}")

    time.sleep(2)

    log("Submitting Wave 2 Job C: M6 + M7")
    result = subprocess.run(
        ["sbatch", "scripts/train.sh", "--conditions", "M6", "M7"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    job_id = int(result.stdout.split()[-1])
    job_ids.append(job_id)
    log(f"Wave 2 Job C submitted: {job_id}")

    return job_ids


def main() -> int:
    """Run full pipeline autonomously."""
    log("=== Sparse-Hate Full Pipeline Runner ===")

    # Wave 1 job IDs (from submission)
    wave1_jobs = [11464115, 11464117]

    log(f"Waiting for Wave 1 jobs to complete: {wave1_jobs}")
    if not wait_for_jobs(wave1_jobs, poll_interval=300):  # Check every 5 minutes
        log("ERROR: Wave 1 jobs failed")
        return 1

    log("Wave 1 complete! Submitting Wave 2...")
    wave2_jobs = submit_wave2()

    log(f"Waiting for Wave 2 jobs to complete: {wave2_jobs}")
    if not wait_for_jobs(wave2_jobs, poll_interval=300):
        log("ERROR: Wave 2 jobs failed")
        return 1

    log("Wave 2 complete!")
    log("Training phases complete. Next steps:")
    log("  1. Run Phase 3: Attributions (IG, LIME)")
    log("  2. Run Phase 4: Statistics (bootstrap, power analysis)")
    log("  3. Run Phase 5: Adversarial (attention swap)")
    log("  4. Collect results and analyze")
    log("  5. Generate manuscript")

    # TODO: Implement phases 3-5 automation

    return 0


if __name__ == "__main__":
    sys.exit(main())
