#!/usr/bin/env python3
"""Manage experiment-state.json lifecycle: init, update, status, iterate."""
import argparse, json, os, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUSES = (
    "planned", "running", "collecting", "analyzing",
    "confirmed", "diagnosing", "revising", "abandoned",
)
TRANSITIONS = {
    "planned":    {"running"},
    "running":    {"collecting", "analyzing", "diagnosing"},
    "collecting": {"analyzing", "diagnosing"},
    "analyzing":  {"confirmed", "diagnosing", "revising"},
    "diagnosing": {"revising", "planned", "running", "abandoned"},
    "revising":   {"planned", "running", "abandoned"},
    "confirmed":  set(), "abandoned": set(),
}
JOB_STATUSES = ("pending", "running", "completed", "failed")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(path, data):
    """Write JSON atomically via temp file + rename."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load_state(path):
    if not path.exists():
        print(f"Error: {path} not found. Use 'init' to create it.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def save_state(path, state):
    state["last_updated"] = now_iso()
    atomic_write(path, state)


# ── Subcommands ─────────────────────────────────────────────────────

def cmd_init(args, state_path):
    if state_path.exists() and not getattr(args, "force", False):
        print(f"Error: {state_path} already exists.", file=sys.stderr)
        return 1
    state = {
        "$schema": "experiment-state-v1", "project": args.project,
        "created": now_iso(), "last_updated": now_iso(),
        "iteration": 0, "status": "planned",
        "active_hypothesis": {"id": "H1", "summary": args.hypotheses},
        "total_runs": args.total_runs,
        "jobs": {}, "phases": {}, "failures": [], "history": [],
    }
    atomic_write(state_path, state)
    print(f"Initialized {state_path}")
    return 0


def cmd_status(_args, state_path):
    s = load_state(state_path)
    lines = [
        f"Project:    {s.get('project', 'N/A')}",
        f"Status:     {s.get('status', 'N/A')}",
        f"Iteration:  {s.get('iteration', 0)}",
        f"Total runs: {s.get('total_runs', 'N/A')}",
        f"Updated:    {s.get('last_updated', 'N/A')}",
    ]
    hyp = s.get("active_hypothesis", {})
    if hyp:
        lines.append(f"Hypothesis: [{hyp.get('id', '?')}] {hyp.get('summary', '')}")
    jobs = s.get("jobs", {})
    if jobs:
        lines.append(f"Jobs ({len(jobs)}):")
        for task, info in jobs.items():
            lines.append(f"  {task}: id={info.get('slurm_id', '?')}  status={info.get('status', '?')}")
    if s.get("failures"):
        lines.append(f"Failures: {len(s['failures'])}")
    print("\n".join(lines))
    return 0


def cmd_update(args, state_path):
    state = load_state(state_path)
    changed = False
    if args.status:
        new = args.status
        if new not in VALID_STATUSES:
            print(f"Error: invalid status '{new}'. Choose from {VALID_STATUSES}", file=sys.stderr)
            return 1
        cur = state.get("status", "planned")
        if cur != new:
            allowed = TRANSITIONS.get(cur, set())
            if new not in allowed:
                print(f"Error: cannot transition from '{cur}' to '{new}'. "
                      f"Allowed: {sorted(allowed) if allowed else 'none (terminal)'}", file=sys.stderr)
                return 1
            state["status"] = new
            changed = True
    if args.phase is not None:
        state["current_phase"] = args.phase
        changed = True
    if args.job_id:
        task, slurm_id = args.job_id
        state.setdefault("jobs", {}).setdefault(task, {})["slurm_id"] = slurm_id
        changed = True
    if args.job_status:
        task, jst = args.job_status
        if jst not in JOB_STATUSES:
            print(f"Error: invalid job status '{jst}'. Choose from {JOB_STATUSES}", file=sys.stderr)
            return 1
        state.setdefault("jobs", {}).setdefault(task, {})["status"] = jst
        changed = True
    if not changed:
        print("Nothing to update (no flags provided).", file=sys.stderr)
        return 1
    save_state(state_path, state)
    print("State updated.")
    return 0


def cmd_increment_iteration(_args, state_path):
    state = load_state(state_path)
    state["iteration"] = state.get("iteration", 0) + 1
    save_state(state_path, state)
    print(f"Iteration bumped to {state['iteration']}.")
    return 0


# ── CLI ─────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(description="Manage experiment-state.json lifecycle.")
    p.add_argument("--state-file", default="experiment-state.json",
                   help="Path to state file (default: experiment-state.json)")
    sub = p.add_subparsers(dest="command")
    sub.required = True
    ip = sub.add_parser("init", help="Create a new experiment-state.json")
    ip.add_argument("--project", required=True)
    ip.add_argument("--hypotheses", required=True, help="Hypothesis summary")
    ip.add_argument("--total-runs", required=True, type=int)
    ip.add_argument("--force", action="store_true", help="Overwrite existing file")
    sub.add_parser("status", help="Print current state summary")
    up = sub.add_parser("update", help="Update state fields")
    up.add_argument("--status", help="Set top-level status")
    up.add_argument("--phase", type=int, help="Set current phase number")
    up.add_argument("--job-id", nargs=2, metavar=("TASK", "ID"), help="Set SLURM ID")
    up.add_argument("--job-status", nargs=2, metavar=("TASK", "STATUS"), help="Set job status")
    sub.add_parser("increment-iteration", help="Bump iteration counter")
    return p


def main():
    args = build_parser().parse_args()
    handlers = {
        "init": cmd_init, "status": cmd_status,
        "update": cmd_update, "increment-iteration": cmd_increment_iteration,
    }
    return handlers[args.command](args, Path(args.state_file))


if __name__ == "__main__":
    sys.exit(main())
