#!/usr/bin/env python3
"""
Pipeline State Manager for Claude Scholar.

Manages persistent state for the end-to-end research pipeline orchestrator.
State is stored in pipeline-state.json in the project root.

Usage:
    python pipeline_state.py init [--force]
    python pipeline_state.py status
    python pipeline_state.py start <step_id>
    python pipeline_state.py complete <step_id>
    python pipeline_state.py skip <step_id>
    python pipeline_state.py fail <step_id> [--reason REASON]
    python pipeline_state.py next
    python pipeline_state.py reset
"""

import sys

if sys.version_info < (3, 6):
    sys.stderr.write("Error: pipeline_state.py requires Python 3.6+\n")
    sys.exit(1)

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STATE_FILE = "pipeline-state.json"

# Default project directory structure created for each project.
PROJECT_SUBDIRS = ["docs", "configs", "src", "data", "results", "results/tables",
                   "results/figures", "manuscript", "logs", "notebooks"]

# Canonical pipeline steps in execution order.
# Each tuple: (step_id, slash_command, description, prerequisite_files, needs_online)
# prerequisite_files are relative to project_dir (e.g. "docs/hypotheses.md").
PIPELINE_STEPS = [
    (
        "research-init",
        "/research-init",
        "Literature review, gap analysis, hypothesis formulation",
        [],
        True,
    ),
    (
        "check-competition",
        "/check-competition",
        "Competitive landscape check",
        [],
        True,
    ),
    (
        "design-experiments",
        "/design-experiments",
        "Experiment plan from hypotheses",
        ["docs/hypotheses.md"],
        False,
    ),
    (
        "scaffold",
        "/scaffold",
        "Generate runnable project structure",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "build-data",
        "/build-data",
        "Create dataset generators and loaders",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "setup-model",
        "/setup-model",
        "Load, configure, introspect models",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "implement-metrics",
        "/implement-metrics",
        "Implement metrics and statistical tests",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "validate-setup",
        "/validate-setup",
        "Pre-flight validation checklist",
        [],
        False,
    ),
    (
        "plan-compute",
        "/plan-compute",
        "GPU estimation and SLURM script generation",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "run-experiment",
        "/run-experiment",
        "Submit experiment matrix via SLURM",
        [],
        False,
    ),
    (
        "collect-results",
        "/collect-results",
        "Aggregate run outputs into structured tables",
        [],
        False,
    ),
    (
        "analyze-results",
        "/analyze-results",
        "Statistical analysis and figure generation",
        [],
        False,
    ),
    (
        "map-claims",
        "/map-claims",
        "Map paper claims to experimental evidence",
        [],
        False,
    ),
    (
        "position",
        "/position",
        "Contribution positioning against prior work",
        [],
        False,
    ),
    (
        "story",
        "/story",
        "Narrative arc, figure plan, paper blueprint",
        [],
        False,
    ),
    (
        "produce-manuscript",
        "/produce-manuscript",
        "Generate figures, prose, LaTeX, submission package",
        [],
        False,
    ),
    (
        "quality-review",
        "/quality-review",
        "Quality gate: claim-evidence, statistical rigor, baselines",
        [],
        False,
    ),
    (
        "compile-manuscript",
        "/compile-manuscript",
        "Compile LaTeX to PDF and create Overleaf package",
        [],
        False,
    ),
    (
        "rebuttal",
        "/rebuttal",
        "Systematic reviewer response",
        [],
        False,
    ),
]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state(project_dir: str) -> dict:
    state_path = os.path.join(project_dir, STATE_FILE)
    if not os.path.exists(state_path):
        return {}
    with open(state_path, "r") as f:
        return json.load(f)


def save_state(project_dir: str, state: dict):
    state_path = os.path.join(project_dir, STATE_FILE)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def ensure_project_structure(base_dir: str, project_slug: str) -> str:
    """Create the canonical project folder structure and return the project_dir (relative)."""
    project_dir_rel = os.path.join("projects", project_slug)
    project_dir_abs = os.path.join(base_dir, project_dir_rel)

    for subdir in PROJECT_SUBDIRS:
        os.makedirs(os.path.join(project_dir_abs, subdir), exist_ok=True)

    return project_dir_rel


def init_state(base_dir: str, force: bool = False,
               project_slug: Optional[str] = None) -> dict:
    state_path = os.path.join(base_dir, STATE_FILE)
    if os.path.exists(state_path) and not force:
        print(f"State file already exists: {state_path}")
        print("Use --force to reinitialize.")
        return load_state(base_dir)

    # Determine project_dir
    project_dir_rel = None
    if project_slug:
        project_dir_rel = ensure_project_structure(base_dir, project_slug)
        print(f"Project structure created: {project_dir_rel}/")

    state = {
        "version": 2,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "mode": "interactive",
        "project_dir": project_dir_rel,
        "steps": {},
    }

    for step_id, command, description, prereqs, needs_online in PIPELINE_STEPS:
        state["steps"][step_id] = {
            "command": command,
            "description": description,
            "prerequisite_files": prereqs,
            "needs_online": needs_online,
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "skipped": False,
            "failure_reason": None,
            "slurm_job_id": None,
        }

    save_state(base_dir, state)
    print(f"Pipeline state initialized: {state_path}")
    if project_dir_rel:
        print(f"Project directory: {project_dir_rel}")
    return state


def get_step_order():
    return [s[0] for s in PIPELINE_STEPS]


def find_next_step(state: dict) -> Optional[str]:
    order = get_step_order()
    for step_id in order:
        step = state["steps"].get(step_id, {})
        if step.get("status") in ("pending", "failed"):
            return step_id
    return None


def print_status(state: dict):
    order = get_step_order()
    symbols = {
        "pending": "  ",
        "running": ">>",
        "completed": "OK",
        "skipped": "--",
        "failed": "!!",
    }

    print()
    print("Pipeline Status")
    print("=" * 70)
    print(f"  Created:     {state.get('created_at', 'N/A')}")
    print(f"  Updated:     {state.get('updated_at', 'N/A')}")
    print(f"  Mode:        {state.get('mode', 'interactive')}")
    project_dir = state.get('project_dir')
    if project_dir:
        print(f"  Project dir: {project_dir}/")
    else:
        print(f"  Project dir: (not set — legacy state)")
    print()

    for i, step_id in enumerate(order, 1):
        step = state["steps"].get(step_id, {})
        status = step.get("status", "pending")
        sym = symbols.get(status, "??")
        cmd = step.get("command", "")
        desc = step.get("description", "")

        line = f"  [{sym}] {i:2d}. {cmd:<25s} {desc}"
        if status == "completed" and step.get("completed_at"):
            line += f"  ({step['completed_at'][:10]})"
        elif status == "failed" and step.get("failure_reason"):
            line += f"  FAIL: {step['failure_reason'][:40]}"
        elif status == "skipped":
            line += "  (skipped)"
        print(line)

    next_step = find_next_step(state)
    print()
    if next_step:
        print(f"  Next step: {state['steps'][next_step]['command']}")
    else:
        completed = sum(
            1
            for s in state["steps"].values()
            if s.get("status") in ("completed", "skipped")
        )
        total = len(state["steps"])
        print(f"  All {total} steps done ({completed} completed).")
    print()


def mark_start(state: dict, step_id: str) -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "running"
    state["steps"][step_id]["started_at"] = now_iso()
    state["updated_at"] = now_iso()
    return state


def mark_complete(state: dict, step_id: str) -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "completed"
    state["steps"][step_id]["completed_at"] = now_iso()
    state["updated_at"] = now_iso()
    return state


def mark_skip(state: dict, step_id: str) -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "skipped"
    state["steps"][step_id]["skipped"] = True
    state["steps"][step_id]["completed_at"] = now_iso()
    state["updated_at"] = now_iso()
    return state


def mark_fail(state: dict, step_id: str, reason: str = "") -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "failed"
    state["steps"][step_id]["failure_reason"] = reason
    state["updated_at"] = now_iso()
    return state


def main():
    parser = argparse.ArgumentParser(description="Pipeline state manager")
    parser.add_argument(
        "--dir",
        default=os.environ.get("PROJECT_DIR", os.getcwd()),
        help="Project directory (default: cwd or $PROJECT_DIR)",
    )
    sub = parser.add_subparsers(dest="action")
    sub.required = True

    p_init = sub.add_parser("init", help="Initialize pipeline state")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--project", help="Project slug (creates projects/<slug>/ structure)")

    sub.add_parser("status", help="Show pipeline status")

    p_start = sub.add_parser("start", help="Mark step as running")
    p_start.add_argument("step_id")

    p_complete = sub.add_parser("complete", help="Mark step as completed")
    p_complete.add_argument("step_id")

    p_skip = sub.add_parser("skip", help="Mark step as skipped")
    p_skip.add_argument("step_id")

    p_fail = sub.add_parser("fail", help="Mark step as failed")
    p_fail.add_argument("step_id")

    p_slurm = sub.add_parser("set-slurm-job", help="Associate a SLURM job ID with a step")
    p_slurm.add_argument("step_id")
    p_slurm.add_argument("job_id", type=int)
    p_fail.add_argument("--reason", default="")

    sub.add_parser("next", help="Print next pending step")

    sub.add_parser("reset", help="Reset all steps to pending")

    sub.add_parser("steps", help="List all step IDs")

    args = parser.parse_args()

    if args.action == "init":
        init_state(args.dir, force=args.force,
                   project_slug=getattr(args, 'project', None))
        return

    state = load_state(args.dir)
    if not state:
        print("No pipeline state found. Run: python pipeline_state.py init",
              file=sys.stderr)
        sys.exit(1)

    if args.action == "status":
        print_status(state)

    elif args.action == "start":
        state = mark_start(state, args.step_id)
        save_state(args.dir, state)
        print(f"Started: {args.step_id}")

    elif args.action == "complete":
        state = mark_complete(state, args.step_id)
        save_state(args.dir, state)
        print(f"Completed: {args.step_id}")

    elif args.action == "skip":
        state = mark_skip(state, args.step_id)
        save_state(args.dir, state)
        print(f"Skipped: {args.step_id}")

    elif args.action == "fail":
        state = mark_fail(state, args.step_id, reason=args.reason)
        save_state(args.dir, state)
        print(f"Failed: {args.step_id}")

    elif args.action == "next":
        next_id = find_next_step(state)
        if next_id:
            step = state["steps"][next_id]
            print(json.dumps({
                "step_id": next_id,
                "command": step["command"],
                "description": step["description"],
                "prerequisite_files": step["prerequisite_files"],
                "needs_online": step["needs_online"],
            }))
        else:
            print("{}")

    elif args.action == "reset":
        for step_id in state["steps"]:
            state["steps"][step_id]["status"] = "pending"
            state["steps"][step_id]["started_at"] = None
            state["steps"][step_id]["completed_at"] = None
            state["steps"][step_id]["skipped"] = False
            state["steps"][step_id]["failure_reason"] = None
            state["steps"][step_id]["slurm_job_id"] = None
        state["updated_at"] = now_iso()
        save_state(args.dir, state)
        print("All steps reset to pending.")

    elif args.action == "set-slurm-job":
        if args.step_id not in state["steps"]:
            print(f"Unknown step: {args.step_id}", file=sys.stderr)
            sys.exit(1)
        state["steps"][args.step_id]["slurm_job_id"] = args.job_id
        state["updated_at"] = now_iso()
        save_state(args.dir, state)
        print(f"Step {args.step_id} linked to SLURM job {args.job_id}")

    elif args.action == "steps":
        for step_id in get_step_order():
            print(step_id)


if __name__ == "__main__":
    main()
