#!/usr/bin/env python3
"""Autonomous experiment runner for ALETHEIA pipeline (Step 18: /run-experiment).

Called automatically by the pipeline orchestrator. Handles cluster detection,
pre-flight validation, and SLURM submission without requiring manual intervention.

Decision flow:
  1. Detect cluster (sbatch in PATH, not inside a running job)
  2. Run project preflight_validate.py — abort if it fails
  3. Auto-discover slurm/train_*.sh scripts (or read experiment-state.json)
  4. Submit all job arrays via sbatch
  5. Update experiment-state.json with job IDs

Exit codes:
  0 = jobs submitted (or dry-run completed)
  1 = preflight failed — do not submit
  2 = sbatch not available — print manual instructions and exit cleanly
  3 = experiment state / project directory missing

Usage:
    python scripts/run_experiment_autonomously.py [--project-dir DIR] [--dry-run] [--skip-preflight]

The pipeline orchestrator (run-pipeline.md) calls this at Step 18.
Claude should ALWAYS run this script at Step 18 rather than checking manually.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PIPELINE_STATE_FILE = "pipeline-state.json"


# ── Cluster detection ─────────────────────────────────────────────────────────

def detect_cluster() -> dict:
    """Detect SLURM availability.

    Checks:
    - sbatch binary in PATH
    - SLURM_JOB_ID not set (we are NOT inside a running job)
    - sinfo responds (cluster is actually reachable)

    Returns dict with: slurm_available, login_node, inside_job, hostname, partitions.
    """
    hostname = os.uname().nodename
    slurm_available = shutil.which("sbatch") is not None
    inside_job = "SLURM_JOB_ID" in os.environ

    partitions: list[str] = []
    if slurm_available:
        try:
            r = subprocess.run(["sinfo", "-h", "-o", "%P"], capture_output=True, text=True, timeout=10)
            partitions = [p.strip().rstrip("*") for p in r.stdout.splitlines() if p.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return {
        "slurm_available": slurm_available,
        "inside_job": inside_job,
        "login_node": slurm_available and not inside_job,
        "hostname": hostname,
        "partitions": partitions,
    }


# ── Venv discovery ────────────────────────────────────────────────────────────

def find_venv_python(repo_root: str) -> str:
    """Return the venv Python path, falling back to sys.executable."""
    for candidate in [
        os.path.join(repo_root, ".venv", "bin", "python"),
        os.path.join(repo_root, ".venv", "bin", "python3"),
        os.path.join(repo_root, "venv", "bin", "python"),
    ]:
        if os.path.isfile(candidate):
            return candidate
    return sys.executable


# ── Pre-flight validation ─────────────────────────────────────────────────────

def run_preflight(project_dir: str, venv_python: str) -> bool:
    """Run scripts/preflight_validate.py in project_dir.

    Returns True if the script exits 0 (all checks pass).
    Falls back gracefully if the script does not exist.
    """
    script = os.path.join(project_dir, "scripts", "preflight_validate.py")
    if not os.path.exists(script):
        print(f"  [SKIP] preflight_validate.py not found at {script}")
        return True

    print("\n[1/3] PRE-FLIGHT VALIDATION")
    r = subprocess.run([venv_python, script], cwd=project_dir, timeout=180)
    if r.returncode != 0:
        print(f"\n  [FAIL] Pre-flight returned exit code {r.returncode}. Aborting.")
        return False
    return True


# ── SLURM job discovery + submission ─────────────────────────────────────────

def discover_slurm_scripts(project_dir: str) -> list[dict]:
    """Discover slurm/train_*.sh scripts, sorted by condition name."""
    slurm_dir = os.path.join(project_dir, "slurm")
    if not os.path.isdir(slurm_dir):
        return []
    scripts = sorted(Path(slurm_dir).glob("train_*.sh"))
    return [
        {
            "condition": p.stem.replace("train_", "").upper(),
            "script": str(p),
        }
        for p in scripts
    ]


def submit_jobs(entries: list[dict], dry_run: bool) -> dict[str, int]:
    """Submit sbatch jobs and return {condition: job_id} mapping."""
    print("\n[3/3] SLURM SUBMISSION")
    job_ids: dict[str, int] = {}

    for entry in entries:
        condition = entry["condition"]
        script = entry["script"]

        if not os.path.exists(script):
            print(f"  [SKIP] {condition}: script not found ({script})")
            continue

        cmd = ["sbatch", script]
        if dry_run:
            print(f"  [DRY-RUN] sbatch {script}")
            job_ids[condition] = -1
            continue

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            # "Submitted batch job 12345678"
            job_id = int(r.stdout.strip().split()[-1])
            job_ids[condition] = job_id
            print(f"  [OK] {condition}: job array {job_id}")
        else:
            print(f"  [FAIL] {condition}: {r.stderr.strip()}")

    return job_ids


# ── Experiment state I/O ──────────────────────────────────────────────────────

def update_experiment_state(project_dir: str, job_ids: dict[str, int]) -> None:
    """Write/update experiment-state.json with submitted job IDs."""
    path = os.path.join(project_dir, "experiment-state.json")
    state: dict = {}
    if os.path.exists(path):
        with open(path) as f:
            state = json.load(f)

    state.setdefault("submissions", [])
    state["submissions"].append({
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "job_ids": job_ids,
        "status": "pending",
    })
    state["latest_job_ids"] = job_ids

    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"\n  experiment-state.json updated: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="ALETHEIA autonomous experiment runner")
    parser.add_argument("--project-dir", default=None)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--dry-run", action="store_true", help="Print sbatch commands but do not submit")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)

    # Resolve project_dir from pipeline-state.json if not given
    if args.project_dir:
        project_dir = os.path.abspath(args.project_dir)
    else:
        state_file = os.path.join(repo_root, PIPELINE_STATE_FILE)
        if not os.path.exists(state_file):
            print(f"[ERROR] {state_file} not found. Pass --project-dir explicitly.")
            return 3
        with open(state_file) as f:
            pipeline_state = json.load(f)
        rel = pipeline_state.get("project_dir", "")
        if not rel:
            print("[ERROR] project_dir not set in pipeline-state.json.")
            return 3
        project_dir = os.path.join(repo_root, rel.rstrip("/"))

    if not os.path.isdir(project_dir):
        print(f"[ERROR] Project directory not found: {project_dir}")
        return 3

    venv_python = find_venv_python(repo_root)

    # ── Step 0: Cluster detection (ALWAYS runs first) ─────────────────────────
    print("\n" + "=" * 60)
    print("ALETHEIA EXPERIMENT RUNNER — cluster detection")
    print("=" * 60)
    env = detect_cluster()
    print(f"  hostname:     {env['hostname']}")
    print(f"  sbatch found: {env['slurm_available']}")
    print(f"  inside job:   {env['inside_job']}")
    print(f"  login node:   {env['login_node']}")
    if env["partitions"]:
        print(f"  partitions:   {', '.join(env['partitions'][:6])}")

    if not env["slurm_available"]:
        print("\n[EXIT 2] sbatch not found — not on a SLURM cluster.")
        print("Transfer to a login node and rerun:")
        print(f"  python {os.path.relpath(__file__, repo_root)} --repo-root {repo_root}")
        _print_manual_cmds(project_dir)
        return 2

    if env["inside_job"]:
        print(f"\n[EXIT 2] SLURM_JOB_ID={os.environ['SLURM_JOB_ID']} is set.")
        print("Running inside an existing SLURM job. Do not submit from inside a job.")
        return 2

    print("\n  [OK] Login node confirmed. Proceeding with submission.")

    # ── Step 1: Pre-flight validation ─────────────────────────────────────────
    if not args.skip_preflight:
        if not run_preflight(project_dir, venv_python):
            return 1
    else:
        print("\n[1/3] PRE-FLIGHT VALIDATION — skipped")

    # ── Step 2: Skipped (preflight covers init + forward) ────────────────────
    print("\n[2/3] CPU SMOKE TEST — skipped (preflight covers model init and forward pass)")

    # ── Step 3: Discover + submit ─────────────────────────────────────────────
    entries = discover_slurm_scripts(project_dir)
    if not entries:
        print("[ERROR] No slurm/train_*.sh scripts found. Run /plan-compute first.")
        return 3

    print(f"\n  Found {len(entries)} job scripts: {[e['condition'] for e in entries]}")
    job_ids = submit_jobs(entries, dry_run=args.dry_run)

    if not job_ids:
        print("[ERROR] No jobs submitted.")
        return 1

    # ── Step 4: Update state ──────────────────────────────────────────────────
    if not args.dry_run:
        update_experiment_state(project_dir, job_ids)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"SUBMITTED: {len(job_ids)} job arrays ({sum(1 for v in job_ids.values() if v > 0) * 5} total runs)")
    for cond, jid in sorted(job_ids.items()):
        tag = f"job {jid}" if jid > 0 else "dry-run"
        print(f"  {cond}: {tag}")
    print("\nMonitor:  squeue -u $USER")
    print("Resume:   /run-pipeline --resume  (after jobs complete)")
    print("=" * 60)
    return 0


def _print_manual_cmds(project_dir: str) -> None:
    slurm_dir = os.path.join(project_dir, "slurm")
    if os.path.isdir(slurm_dir):
        scripts = sorted(Path(slurm_dir).glob("train_*.sh"))
        if scripts:
            print("\nManual commands (run from login node):")
            for s in scripts:
                print(f"  sbatch {s}")


if __name__ == "__main__":
    sys.exit(main())
