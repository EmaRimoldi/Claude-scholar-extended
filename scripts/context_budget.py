#!/usr/bin/env python3
"""
context_budget.py — Context budget checker for the ALETHEIA pipeline.

Measures total prerequisite file sizes for one or all pipeline steps and
flags steps whose inputs exceed the 100K-char threshold where loading full
documents may saturate the model context window.

Usage:
    python scripts/context_budget.py --dir $PROJECT_DIR <step_id>
    python scripts/context_budget.py --dir $PROJECT_DIR --all
    python scripts/context_budget.py --dir $PROJECT_DIR --all --json
    python scripts/context_budget.py --dir $PROJECT_DIR --all --threshold 50000

Exit codes:
    0  All checked steps are within budget (OK)
    1  State file not found or unreadable
    2  At least one step exceeds the budget threshold (HIGH)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 100_000   # chars (~25K tokens for ASCII-heavy docs)
WARN_THRESHOLD    =  50_000   # chars — emit a soft warning below BLOCK level
STATE_FILE = "pipeline-state.json"
STATE_DIR  = "state"


def load_state(project_dir: str) -> dict[str, Any]:
    path = os.path.join(project_dir, STATE_FILE)
    if not os.path.isfile(path):
        return {}
    with open(path) as f:
        return json.load(f)


def resolve_project_dir(state: dict[str, Any], base_dir: str) -> str:
    """Resolve state['project_dir'] relative to base_dir."""
    pd = state.get("project_dir", "")
    if not pd:
        return base_dir
    if os.path.isabs(pd):
        return pd
    return os.path.join(base_dir, pd)


def list_handoff_alternatives(project_dir: str) -> list[str]:
    """Return all handoff file paths present in state/handoffs/."""
    handoffs_dir = os.path.join(project_dir, STATE_DIR, "handoffs")
    if not os.path.isdir(handoffs_dir):
        return []
    return sorted(
        f"state/handoffs/{f}"
        for f in os.listdir(handoffs_dir)
        if f.endswith(".json")
    )


def measure_prereqs(
    project_dir: str,
    prereqs: list[str],
    threshold: int,
) -> dict[str, Any]:
    """Measure total char size of prerequisite files for a step."""
    files: list[dict[str, Any]] = []
    total = 0
    for rel in prereqs:
        full = os.path.join(project_dir, rel)
        if os.path.isfile(full):
            try:
                size = os.path.getsize(full)
                files.append({"file": rel, "chars": size, "exists": True})
                total += size
            except OSError:
                files.append({"file": rel, "chars": 0, "exists": False, "error": "unreadable"})
        elif os.path.isdir(full):
            # For directory prereqs (e.g. manuscript/) count total size
            dir_size = sum(
                os.path.getsize(os.path.join(dp, fn))
                for dp, _, fns in os.walk(full)
                for fn in fns
            )
            files.append({"file": rel, "chars": dir_size, "exists": True, "type": "dir"})
            total += dir_size
        else:
            files.append({"file": rel, "chars": 0, "exists": False})

    if total > threshold:
        status = "HIGH"
    elif total > WARN_THRESHOLD:
        status = "WARN"
    else:
        status = "OK"

    return {"total_chars": total, "status": status, "files": files}


def check_step(
    base_dir: str,
    state: dict[str, Any],
    step_id: str,
    threshold: int,
    as_json: bool = False,
) -> int:
    """Check budget for one step. Returns exit code (0=OK, 2=HIGH)."""
    if step_id not in state.get("steps", {}):
        msg = f"Unknown step: {step_id}"
        if as_json:
            print(json.dumps({"error": msg}))
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
        return 1

    project_dir = resolve_project_dir(state, base_dir)
    prereqs = state["steps"][step_id].get("prerequisite_files", [])
    result = measure_prereqs(project_dir, prereqs, threshold)
    handoffs = list_handoff_alternatives(project_dir)

    output = {
        "step_id": step_id,
        "total_chars": result["total_chars"],
        "threshold": threshold,
        "budget_status": result["status"],
        "files": result["files"],
        "handoff_alternatives": handoffs,
    }

    if result["status"] == "HIGH":
        output["recommendation"] = (
            f"Total prereq size {result['total_chars']:,} chars exceeds {threshold:,}. "
            f"Load state/handoffs/<dep_step>.json summaries instead of full documents."
        )

    if as_json:
        print(json.dumps(output, indent=2))
    else:
        status_sym = {"OK": "✓", "WARN": "~", "HIGH": "!"}.get(result["status"], "?")
        print(f"  [{status_sym}] {step_id:<30s}  {result['total_chars']:>8,} chars  [{result['status']}]")
        for f in result["files"]:
            sym = "✓" if f["exists"] else "✗"
            print(f"       {sym} {f['file']:<50s} {f.get('chars', 0):>8,}")
        if result["status"] == "HIGH" and handoffs:
            print(f"       Handoff alternatives: {', '.join(handoffs)}")

    return 2 if result["status"] == "HIGH" else 0


def check_all(
    base_dir: str,
    state: dict[str, Any],
    threshold: int,
    as_json: bool = False,
) -> int:
    """Check budget for all steps. Returns 0 if all OK, 2 if any HIGH."""
    steps = state.get("steps", {})
    # Preserve canonical pipeline order via the steps dict order (Python 3.7+ dicts are ordered)
    results: list[dict[str, Any]] = []
    any_high = False

    project_dir = resolve_project_dir(state, base_dir)
    handoffs = list_handoff_alternatives(project_dir)

    for step_id, step_data in steps.items():
        prereqs = step_data.get("prerequisite_files", [])
        if not prereqs:
            continue
        r = measure_prereqs(project_dir, prereqs, threshold)
        entry = {
            "step_id": step_id,
            "total_chars": r["total_chars"],
            "budget_status": r["status"],
            "files": r["files"],
        }
        if r["status"] == "HIGH":
            any_high = True
        results.append(entry)

    if as_json:
        print(json.dumps({
            "threshold": threshold,
            "steps": results,
            "handoff_alternatives": handoffs,
            "any_high": any_high,
        }, indent=2))
    else:
        print(f"\nContext Budget Report  (threshold: {threshold:,} chars)\n{'='*60}")
        for entry in results:
            sym = {"OK": "✓", "WARN": "~", "HIGH": "!"}.get(entry["budget_status"], "?")
            print(
                f"  [{sym}] {entry['step_id']:<35s} "
                f"{entry['total_chars']:>8,} chars  [{entry['budget_status']}]"
            )
        print()
        high_steps = [e["step_id"] for e in results if e["budget_status"] == "HIGH"]
        if high_steps:
            print(f"  HIGH budget steps ({len(high_steps)}): {', '.join(high_steps)}")
            if handoffs:
                print(f"  Available handoffs: {', '.join(handoffs)}")
        else:
            print("  All steps within budget.")
        print()

    return 2 if any_high else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ALETHEIA context budget checker")
    ap.add_argument(
        "--dir", default=os.environ.get("PROJECT_DIR", os.getcwd()),
        help="Project base directory (default: cwd or $PROJECT_DIR)",
    )
    ap.add_argument(
        "step_id", nargs="?", default=None,
        help="Step ID to check (omit with --all to check every step)",
    )
    ap.add_argument("--all", action="store_true", help="Check all steps")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument(
        "--threshold", type=int, default=DEFAULT_THRESHOLD,
        help=f"Char threshold for HIGH status (default: {DEFAULT_THRESHOLD:,})",
    )
    args = ap.parse_args()

    state = load_state(args.dir)
    if not state:
        print(f"[ERROR] pipeline-state.json not found in {args.dir}", file=sys.stderr)
        return 1

    if args.all:
        return check_all(args.dir, state, args.threshold, as_json=args.json)
    elif args.step_id:
        return check_step(args.dir, state, args.step_id, args.threshold, as_json=args.json)
    else:
        ap.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
