#!/usr/bin/env python3
"""Submit and monitor SLURM jobs.

Usage:
    python submit.py --profile gpu-single --command "python src/main.py"
    python submit.py --profile gpu-single --command "..." --wait
    python submit.py --status JOB_ID
    python submit.py --cancel JOB_ID
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

sys.path.insert(0, str(SCRIPT_DIR))
from job_builder import load_cluster_profile, resolve_profile, generate_sbatch


def run(cmd: str, check: bool = True) -> str:
    """Run shell command, return stdout."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def submit_job(sbatch_path: str) -> int:
    """Submit sbatch script and return job ID."""
    output = run(f"sbatch {sbatch_path}")
    # "Submitted batch job 12345"
    match = re.search(r"(\d+)", output)
    if not match:
        print(f"Failed to parse job ID from: {output}", file=sys.stderr)
        sys.exit(1)
    job_id = int(match.group(1))
    print(f"Submitted job {job_id}")
    return job_id


def job_status(job_id: int) -> dict:
    """Get job status via sacct."""
    raw = run(
        f"sacct -j {job_id} --format=JobID,State,ExitCode,Elapsed,MaxRSS,NodeList --parsable2 --noheader",
        check=False,
    )
    if not raw:
        # Try squeue for pending/running jobs
        sq = run(f"squeue -j {job_id} -o '%T|%M|%N' --noheader", check=False)
        if sq:
            parts = sq.split("|")
            return {"state": parts[0], "elapsed": parts[1] if len(parts) > 1 else "",
                    "node": parts[2] if len(parts) > 2 else ""}
        return {"state": "UNKNOWN"}

    # Parse first non-.batch line
    for line in raw.splitlines():
        parts = line.split("|")
        if ".batch" in parts[0] or ".extern" in parts[0]:
            continue
        return {
            "job_id": parts[0],
            "state": parts[1] if len(parts) > 1 else "UNKNOWN",
            "exit_code": parts[2] if len(parts) > 2 else "",
            "elapsed": parts[3] if len(parts) > 3 else "",
            "max_rss": parts[4] if len(parts) > 4 else "",
            "node": parts[5] if len(parts) > 5 else "",
        }
    return {"state": "UNKNOWN"}


def wait_for_job(job_id: int, poll_interval: int = 30) -> dict:
    """Wait for a job to complete, polling periodically."""
    terminal_states = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY",
                       "NODE_FAIL", "PREEMPTED"}
    print(f"Waiting for job {job_id}...", end="", flush=True)
    while True:
        status = job_status(job_id)
        state = status.get("state", "UNKNOWN")
        if state in terminal_states:
            print(f" {state}")
            return status
        print(".", end="", flush=True)
        time.sleep(poll_interval)


def show_job_output(job_id: int, job_name: str = None):
    """Print the last lines of job output."""
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = PROJECT_ROOT / "logs" / "slurm" / date_str

    # Find matching log files
    patterns = [f"*-{job_id}.out", f"*-{job_id}.err"]
    for pattern in patterns:
        for f in log_dir.glob(pattern):
            print(f"\n--- {f.name} ---")
            text = f.read_text()
            lines = text.splitlines()
            if len(lines) > 30:
                print(f"  ... ({len(lines) - 30} lines omitted) ...")
                print("\n".join(lines[-30:]))
            else:
                print(text)


def main():
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Submit and monitor SLURM jobs")
    sub = parser.add_subparsers(dest="action")

    # Submit subcommand
    p_submit = sub.add_parser("submit", help="Submit a new job")
    p_submit.add_argument("--profile", default="gpu-single")
    p_submit.add_argument("--command", required=True)
    p_submit.add_argument("--job-name", default=None)
    p_submit.add_argument("--wait", action="store_true", help="Wait for job completion")
    p_submit.add_argument("--partition", default=None)
    p_submit.add_argument("--gpus", type=int, default=None)
    p_submit.add_argument("--gpu-type", default=None)
    p_submit.add_argument("--cpus", type=int, default=None)
    p_submit.add_argument("--mem-gb", type=int, default=None)
    p_submit.add_argument("--time", default=None)
    p_submit.add_argument("--test", action="store_true", help="Print script without submitting")

    # Status subcommand
    p_status = sub.add_parser("status", help="Check job status")
    p_status.add_argument("job_id", type=int)
    p_status.add_argument("--output", action="store_true", help="Show job output")

    # Cancel subcommand
    p_cancel = sub.add_parser("cancel", help="Cancel a job")
    p_cancel.add_argument("job_id", type=int)

    # Queue subcommand
    p_queue = sub.add_parser("queue", help="Show user's job queue")

    args = parser.parse_args()

    if args.action == "submit":
        cluster = load_cluster_profile()
        overrides = {
            "partition": args.partition, "gpus": args.gpus, "gpu_type": args.gpu_type,
            "cpus": args.cpus, "mem_gb": args.mem_gb, "time": args.time,
        }
        config = resolve_profile(cluster, args.profile, overrides)
        job_name = args.job_name or f"cls-{args.profile}-{datetime.now().strftime('%H%M%S')}"
        script = generate_sbatch(job_name, args.command, config, cluster)

        if args.test:
            print(script)
            return

        date_str = datetime.now().strftime("%Y-%m-%d")
        log_dir = PROJECT_ROOT / "logs" / "slurm" / date_str
        log_dir.mkdir(parents=True, exist_ok=True)

        sbatch_path = log_dir / f"{job_name}.sbatch"
        sbatch_path.write_text(script)

        job_id = submit_job(str(sbatch_path))
        print(f"Job ID: {job_id}")
        print(f"Script: {sbatch_path}")
        print(f"Logs:   {log_dir}/{job_name}-{job_id}.out")

        if args.wait:
            status = wait_for_job(job_id)
            show_job_output(job_id, job_name)
            if status.get("state") != "COMPLETED":
                sys.exit(1)

    elif args.action == "status":
        status = job_status(args.job_id)
        print(json.dumps(status, indent=2))
        if args.output:
            show_job_output(args.job_id)

    elif args.action == "cancel":
        run(f"scancel {args.job_id}")
        print(f"Cancelled job {args.job_id}")

    elif args.action == "queue":
        output = run(f"squeue -u {os.environ.get('USER', '')} -o '%.8i %.12P %.30j %.2t %.10M %.6D %R'")
        if output:
            print(output)
        else:
            print("No active jobs.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
