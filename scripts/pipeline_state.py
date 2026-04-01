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

# Canonical v3 pipeline steps in execution order (38 steps across 6 phases).
# Each tuple: (step_id, slash_command, description, prerequisite_files, needs_online)
# prerequisite_files are relative to project_dir (e.g. "docs/hypotheses.md").
# Steps with command "—" are inline orchestrator sub-tasks (no separate slash command).
PIPELINE_STEPS = [
    # --- Phase 1: Research & Novelty Assessment (Days 1–5) ---
    (
        "research-landscape",
        "/research-landscape",
        "Pass 1: Broad territory mapping, 50–100 papers, Citation Ledger init",
        [],
        True,
    ),
    (
        "cross-field-search",
        "/cross-field-search",
        "Pass 4: Abstract problem, identify adjacent fields, produce cross-field-report.md",
        ["docs/research-landscape.md"],
        True,
    ),
    (
        "formulate-hypotheses",
        "/research-init",
        "Hypothesis generation from gaps (hypothesis-generator agent)",
        ["docs/research-landscape.md"],
        False,
    ),
    (
        "claim-search",
        "/claim-search",
        "Pass 2: Decompose hypothesis into atomic claims, search each",
        ["docs/hypotheses.md"],
        True,
    ),
    (
        "citation-traversal",
        "/citation-traversal",
        "Pass 3: Citation graph traversal from top seed papers",
        ["docs/research-landscape.md"],
        True,
    ),
    (
        "adversarial-search",
        "/adversarial-search",
        "Pass 6: Actively attempt to kill novelty claim",
        ["docs/claim-overlap-report.md"],
        True,
    ),
    (
        "novelty-gate-n1",
        "/novelty-gate gate=N1",
        "Gate N1: Full novelty evaluation. PROCEED/REPOSITION/PIVOT/KILL",
        ["docs/adversarial-novelty-report.md", "docs/cross-field-report.md"],
        False,
    ),
    (
        "recency-sweep-1",
        "/recency-sweep sweep_id=1",
        "Pass 5: First recency check for concurrent work",
        ["docs/hypotheses.md"],
        True,
    ),
    # --- Phase 2: Experiment Design (Days 5–6) ---
    (
        "design-experiments",
        "/design-experiments",
        "Full experiment plan with baselines, ablations, power analysis",
        ["docs/hypotheses.md", "docs/novelty-assessment.md"],
        False,
    ),
    (
        "design-novelty-check",
        "/design-novelty-check",
        "Gate N2: Does design test the novelty claim? Baselines correct?",
        ["docs/experiment-plan.md", "docs/claim-overlap-report.md"],
        False,
    ),
    # --- Phase 3: Implementation (Days 6–10) ---
    (
        "scaffold",
        "/scaffold",
        "Generate project structure",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "build-data",
        "/build-data",
        "Dataset generators and loaders",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "setup-model",
        "/setup-model",
        "Load and configure models",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "implement-metrics",
        "/implement-metrics",
        "Metrics and statistical tests",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "validate-setup",
        "/validate-setup",
        "Pre-flight validation checklist (hard block)",
        [],
        False,
    ),
    # --- Phase 4: Execution (Days 10–19, SLURM) ---
    (
        "download-data",
        "/download-data",
        "Download datasets/models to cluster cache",
        ["docs/experiment-plan.md"],
        True,
    ),
    (
        "plan-compute",
        "/plan-compute",
        "GPU estimation, SLURM scripts",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "run-experiment",
        "/run-experiment",
        "Submit experiment matrix, monitor, recover",
        [],
        False,
    ),
    (
        "collect-results",
        "/collect-results",
        "Aggregate outputs into structured tables",
        [],
        False,
    ),
    # --- Phase 5A: Analysis & Epistemic Grounding (Days 19–23) ---
    (
        "analyze-results",
        "/analyze-results",
        "Statistical analysis, figures, hypothesis outcomes",
        [],
        False,
    ),
    (
        "gap-detection",
        "—",
        "Gap Detection: missing ablations/baselines (inline; may loop back to step 9)",
        ["docs/analysis-report.md"],
        False,
    ),
    (
        "post-results-novelty",
        "/novelty-gate gate=N3",
        "Gate N3: Re-evaluate novelty given actual results",
        ["docs/analysis-report.md", "docs/hypothesis-outcomes.md"],
        False,
    ),
    (
        "recency-sweep-2",
        "/recency-sweep sweep_id=2",
        "Pass 5 again: concurrent work during execution",
        ["docs/novelty-reassessment.md"],
        True,
    ),
    (
        "literature-rescan",
        "—",
        "Results-contextualized literature re-scan (inline)",
        ["docs/analysis-report.md", "docs/novelty-reassessment.md"],
        True,
    ),
    (
        "method-code-reconciliation",
        "—",
        "Method-Code consistency check (hard block on discrepancy; inline)",
        ["experiment-state.json"],
        False,
    ),
    # --- Phase 5B: Claim Architecture & Writing Cycle (Days 23–29) ---
    (
        "map-claims",
        "/map-claims",
        "Claim-evidence architecture, Claim Dependency Graph, Skeptic Agent",
        ["docs/analysis-report.md"],
        False,
    ),
    (
        "position",
        "/position",
        "Contribution positioning using novelty-reassessment.md as primary input",
        ["docs/novelty-reassessment.md", "docs/claim-ledger.md"],
        False,
    ),
    (
        "story",
        "/story",
        "Narrative arc, paper blueprint, figure plan",
        ["docs/positioning.md"],
        False,
    ),
    (
        "narrative-gap-detect",
        "—",
        "Narrative Gap Detector: may loop back to Step 20 or Step 9 (inline)",
        ["docs/paper-blueprint.md"],
        False,
    ),
    (
        "argument-figure-align",
        "—",
        "Figure-argument alignment; redesign figures that don't serve their claim (inline)",
        ["docs/figure-plan.md"],
        False,
    ),
    (
        "produce-manuscript",
        "/produce-manuscript",
        "Full prose + Citation Audit sub-step",
        ["docs/paper-blueprint.md"],
        False,
    ),
    (
        "cross-section-consistency",
        "—",
        "5-check cross-section consistency (hard block on failure; inline)",
        ["manuscript/"],
        False,
    ),
    (
        "claim-source-align",
        "—",
        "Claim-Source Alignment Verifier (hard block on untraced claims; inline)",
        ["manuscript/"],
        False,
    ),
    (
        "verify-paper",
        "/verify-paper",
        "7-dimensional quality verifier (45 criteria)",
        ["docs/claim-alignment-report.md", "docs/cross-section-report.md"],
        False,
    ),
    # --- Phase 6: Pre-Submission & Publication (Days 29–38) ---
    (
        "adversarial-review",
        "—",
        "3 hostile simulated reviewers, routes upstream (inline)",
        ["manuscript/"],
        False,
    ),
    (
        "recency-sweep-final",
        "/recency-sweep sweep_id=final",
        "Pass 5 final: last concurrent work check within 48h of submission",
        ["docs/novelty-reassessment.md"],
        True,
    ),
    (
        "novelty-gate-n4",
        "/novelty-gate gate=N4",
        "Gate N4: Final novelty confirmation before compilation",
        ["docs/concurrent-work-report.md"],
        False,
    ),
    (
        "compile-manuscript",
        "/compile-manuscript",
        "Compile LaTeX to PDF, Overleaf ZIP, chktex",
        ["manuscript/"],
        False,
    ),
]

# Loop counter fields tracked in pipeline-state.json.
# These are incremented by the orchestrator when a feedback loop fires.
LOOP_COUNTERS = {
    "reposition_count":       {"max": 2, "loop": "N1 REPOSITION → Step 3"},
    "pivot_count":            {"max": 1, "loop": "N1 PIVOT → Step 1"},
    "design_novelty_loops":   {"max": 2, "loop": "N2 REVISE → Step 9"},
    "gap_detection_loops":    {"max": 2, "loop": "Gap Detection → Step 9"},
    "narrative_gap_loops":    {"max": 2, "loop": "Narrative Gap → Step 20 or Step 9"},
    "verify_paper_cycle":     {"max": 3, "loop": "Phase 5B Revision → Steps 26–33"},
    "adversarial_review_cycles": {"max": 2, "loop": "Adversarial Review → upstream"},
}


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
               project_slug: Optional[str] = None,
               research_topic: Optional[str] = None) -> dict:
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
        "research_topic": (research_topic.strip() if research_topic else None),
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
    topic = state.get("research_topic")
    if topic:
        print(f"  Research topic: {topic}")
    else:
        print(f"  Research topic: (not set — pass init --topic or set in pipeline-state.json for /run-pipeline)")
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
    p_init.add_argument(
        "--topic",
        default=None,
        help="Research question / topic string stored in pipeline-state.json for /run-pipeline (e.g. Pass 1 /research-landscape).",
    )

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

    p_inc = sub.add_parser(
        "increment-counter",
        help="Increment a feedback loop counter field in pipeline-state.json. "
             "Exits 0 if counter is below max, exits 1 if counter has reached or exceeded max.",
    )
    p_inc.add_argument("field", help="Counter field name (e.g. reposition_count)")
    p_inc.add_argument(
        "--max", type=int, default=0,
        help="Maximum allowed value (0 = no limit). Exits 1 if current >= max before incrementing.",
    )

    p_get = sub.add_parser(
        "get-field",
        help="Print the value of a top-level field in pipeline-state.json. "
             "Exits 0 if found, 1 if missing.",
    )
    p_get.add_argument("field", help="Field name to read")

    args = parser.parse_args()

    if args.action == "init":
        init_state(
            args.dir,
            force=args.force,
            project_slug=getattr(args, "project", None),
            research_topic=getattr(args, "topic", None),
        )
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

    elif args.action == "increment-counter":
        field = args.field
        max_val = args.max
        current = int(state.get(field, 0))

        if max_val > 0 and current >= max_val:
            print(
                f"Counter '{field}' has reached maximum ({current}/{max_val}). "
                f"Loop termination condition met.",
                file=sys.stderr,
            )
            sys.exit(1)

        state[field] = current + 1
        state["updated_at"] = now_iso()
        save_state(args.dir, state)

        new_val = state[field]
        limit_note = f"/{max_val}" if max_val > 0 else ""
        print(f"Counter '{field}' incremented to {new_val}{limit_note}")

        # Warn if one step below the limit
        if max_val > 0 and new_val >= max_val:
            print(
                f"WARNING: '{field}' is now at maximum ({new_val}/{max_val}). "
                f"Next loop trigger will terminate.",
                file=sys.stderr,
            )

    elif args.action == "get-field":
        field = args.field
        if field not in state:
            print(f"Field '{field}' not found in pipeline-state.json", file=sys.stderr)
            sys.exit(1)
        value = state[field]
        print(json.dumps(value) if not isinstance(value, str) else value)


if __name__ == "__main__":
    main()
