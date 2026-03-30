#!/usr/bin/env python3
"""
recency_sweep.py — Manage recency sweep state, query caching, and watchlists.

This script handles the persistent state for the three recency sweeps
(sweep-1, sweep-2, sweep-final) run by the /recency-sweep command.

Usage:
    # Record a completed sweep and cache its queries
    python scripts/recency_sweep.py record \
        --sweep-id 1 \
        --project $PROJECT_DIR \
        --queries queries_used.json \
        --results concurrent_work_raw.json

    # Get queries to run for the next sweep (delta from last sweep)
    python scripts/recency_sweep.py watchlist \
        --project $PROJECT_DIR \
        --sweep-id 2

    # Show sweep history
    python scripts/recency_sweep.py status \
        --project $PROJECT_DIR

    # Check if a specific sweep has been run
    python scripts/recency_sweep.py check \
        --project $PROJECT_DIR \
        --sweep-id final
    # Exit 0 if run, exit 1 if not run

State files:
    $PROJECT_DIR/.cache/recency_sweeps/
        sweep_1_state.json
        sweep_2_state.json
        sweep_final_state.json
        watchlist.json       <- active query watchlist
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


SWEEP_IDS = ("1", "2", "final")


def get_cache_dir(project_dir: Path) -> Path:
    return project_dir / ".cache" / "recency_sweeps"


def load_state(cache_dir: Path, sweep_id: str) -> dict:
    state_file = cache_dir / f"sweep_{sweep_id}_state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def save_state(cache_dir: Path, sweep_id: str, state: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    state_file = cache_dir / f"sweep_{sweep_id}_state.json"
    state_file.write_text(json.dumps(state, indent=2))


def load_watchlist(cache_dir: Path) -> dict:
    wl_file = cache_dir / "watchlist.json"
    if wl_file.exists():
        return json.loads(wl_file.read_text())
    return {"queries": [], "last_updated": None}


def save_watchlist(cache_dir: Path, watchlist: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "watchlist.json").write_text(json.dumps(watchlist, indent=2))


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_record(args: argparse.Namespace) -> int:
    project = Path(args.project)
    cache_dir = get_cache_dir(project)
    sweep_id = args.sweep_id

    if sweep_id not in SWEEP_IDS:
        print(f"ERROR: sweep_id must be one of {SWEEP_IDS}", file=sys.stderr)
        return 2

    # Load new queries and results
    queries: list[dict] = []
    if args.queries:
        qp = Path(args.queries)
        if qp.exists():
            queries = json.loads(qp.read_text())
            if not isinstance(queries, list):
                queries = [queries]

    results: list[dict] = []
    if args.results:
        rp = Path(args.results)
        if rp.exists():
            results = json.loads(rp.read_text())
            if not isinstance(results, list):
                results = list(results.values()) if isinstance(results, dict) else [results]

    # Count severity distribution
    severity_counts: dict[str, int] = {
        "blocks_project": 0,
        "requires_repositioning": 0,
        "should_be_cited": 0,
        "no_impact": 0,
    }
    for paper in results:
        sev = paper.get("severity", "no_impact")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    state = {
        "sweep_id": sweep_id,
        "completed_at": datetime.utcnow().isoformat() + "Z",
        "lookback_days": getattr(args, "lookback_days", 90),
        "queries_run": queries,
        "papers_found": len(results),
        "severity_counts": severity_counts,
        "results_path": args.results or "",
    }
    save_state(cache_dir, sweep_id, state)

    # Update watchlist with queries from this sweep (for delta tracking in next sweep)
    watchlist = load_watchlist(cache_dir)
    existing_query_texts = {q.get("query") or q if isinstance(q, str) else "" for q in watchlist["queries"]}
    new_queries_added = 0
    for q in queries:
        q_text = q.get("query") or q if isinstance(q, str) else str(q)
        if q_text not in existing_query_texts:
            watchlist["queries"].append({
                "query": q_text,
                "first_used_sweep": sweep_id,
                "last_used_sweep": sweep_id,
            })
            existing_query_texts.add(q_text)
            new_queries_added += 1
    watchlist["last_updated"] = datetime.utcnow().isoformat() + "Z"
    save_watchlist(cache_dir, watchlist)

    print(f"Sweep {sweep_id} recorded: {len(results)} papers found, {new_queries_added} queries added to watchlist")
    print(f"Severity: {severity_counts}")
    return 0


def cmd_watchlist(args: argparse.Namespace) -> int:
    """Output the watchlist queries to run for the next sweep."""
    project = Path(args.project)
    cache_dir = get_cache_dir(project)
    watchlist = load_watchlist(cache_dir)

    # Get previous sweep state for date context
    prev_sweep_id = {"2": "1", "final": "2"}.get(args.sweep_id)
    prev_state = load_state(cache_dir, prev_sweep_id) if prev_sweep_id else {}
    prev_date = prev_state.get("completed_at", "")

    output = {
        "sweep_id": args.sweep_id,
        "previous_sweep_date": prev_date,
        "lookback_days": getattr(args, "lookback_days", 90),
        "queries": watchlist.get("queries", []),
        "note": (
            f"Run all queries with date filter: papers published after {prev_date[:10] if prev_date else 'project start'}"
            if prev_date
            else "Run all queries — no previous sweep to delta against"
        ),
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2))
        print(f"Watchlist written to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show recency sweep history."""
    project = Path(args.project)
    cache_dir = get_cache_dir(project)

    rows = []
    for sid in SWEEP_IDS:
        state = load_state(cache_dir, sid)
        if state:
            rows.append({
                "sweep_id": sid,
                "completed_at": state.get("completed_at", ""),
                "papers_found": state.get("papers_found", 0),
                "blocks_project": state.get("severity_counts", {}).get("blocks_project", 0),
                "requires_reposition": state.get("severity_counts", {}).get("requires_repositioning", 0),
            })
        else:
            rows.append({"sweep_id": sid, "status": "not_run"})

    watchlist = load_watchlist(cache_dir)
    print(f"Recency Sweep Status — {project.name}")
    print(f"{'Sweep':<10} {'Date':<25} {'Papers':<8} {'Blocks':<8} {'Reposition':<12}")
    print("-" * 65)
    for row in rows:
        if "status" in row:
            print(f"{row['sweep_id']:<10} {'not run':<25}")
        else:
            print(
                f"{row['sweep_id']:<10} "
                f"{row['completed_at'][:19]:<25} "
                f"{row['papers_found']:<8} "
                f"{row['blocks_project']:<8} "
                f"{row['requires_reposition']:<12}"
            )
    print(f"\nWatchlist queries: {len(watchlist.get('queries', []))}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check if a sweep has been run. Exit 0 if yes, 1 if no."""
    project = Path(args.project)
    cache_dir = get_cache_dir(project)
    state = load_state(cache_dir, args.sweep_id)
    if state:
        print(f"Sweep {args.sweep_id} completed at {state.get('completed_at', 'unknown')}")
        return 0
    else:
        print(f"Sweep {args.sweep_id} not yet run")
        return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Manage recency sweep state and watchlists")
    sub = parser.add_subparsers(dest="command")

    # record
    p_record = sub.add_parser("record", help="Record a completed sweep")
    p_record.add_argument("--sweep-id", required=True, choices=SWEEP_IDS)
    p_record.add_argument("--project", required=True)
    p_record.add_argument("--queries", help="JSON file with queries that were run")
    p_record.add_argument("--results", help="JSON file with papers found")
    p_record.add_argument("--lookback-days", type=int, default=90)

    # watchlist
    p_wl = sub.add_parser("watchlist", help="Get queries for next sweep")
    p_wl.add_argument("--project", required=True)
    p_wl.add_argument("--sweep-id", required=True, choices=SWEEP_IDS)
    p_wl.add_argument("--output", help="Write watchlist JSON to this path")
    p_wl.add_argument("--lookback-days", type=int, default=90)

    # status
    p_status = sub.add_parser("status", help="Show sweep history")
    p_status.add_argument("--project", required=True)

    # check
    p_check = sub.add_parser("check", help="Check if a sweep has been run")
    p_check.add_argument("--project", required=True)
    p_check.add_argument("--sweep-id", required=True, choices=SWEEP_IDS)

    args = parser.parse_args()

    dispatch = {
        "record": cmd_record,
        "watchlist": cmd_watchlist,
        "status": cmd_status,
        "check": cmd_check,
    }

    if not args.command or args.command not in dispatch:
        parser.print_help()
        sys.exit(2)

    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
