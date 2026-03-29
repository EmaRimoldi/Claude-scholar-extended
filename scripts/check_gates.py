#!/usr/bin/env python3
"""Evaluate experiment phase gates against current results.

Gates: Completion, Baseline sanity, Variance (CV), No-crash (NaN/Inf).

Usage:
    python scripts/check_gates.py
    python scripts/check_gates.py --config scripts/gate_spec.json --verbose
"""
from __future__ import annotations

import argparse, json, math, statistics, sys
from pathlib import Path
from typing import Any

DEFAULT_STATE = "experiment-state.json"
DEFAULT_RESULTS = "results/"
DEFAULT_CV = 0.10


def load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def collect_results(results_dir: Path) -> list[dict[str, Any]]:
    """Walk results_dir for results.json files."""
    if not results_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(results_dir.rglob("results.json")):
        try:
            out.append(load_json(p))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _is_bad(v: Any) -> bool:
    return isinstance(v, (int, float)) and (math.isnan(v) or math.isinf(v))


def _group_by_condition(results: list[dict[str, Any]]) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = {}
    for r in results:
        cond = r.get("condition", r.get("name", ""))
        val = r.get("metric", r.get("eval_metric", r.get("accuracy")))
        if cond and val is not None and not _is_bad(val):
            groups.setdefault(cond, []).append(float(val))
    return groups


# ── Gate checks ───────────────────────────────────────────────────────

def check_completion(results: list[dict[str, Any]], total_runs: int,
                     threshold: float) -> tuple[str, str]:
    found = len(results)
    ratio = found / total_runs if total_runs > 0 else 0.0
    status = "PASS" if ratio >= threshold else "FAIL"
    return f"{found}/{total_runs} runs complete", status


def check_baseline(results: list[dict[str, Any]],
                   specs: dict[str, dict[str, float]]) -> list[tuple[str, str, str]]:
    if not specs:
        return []
    by_cond = _group_by_condition(results)
    reports: list[tuple[str, str, str]] = []
    for cond, spec in specs.items():
        exp, tol = spec["expected"], spec.get("tolerance", 0.05)
        vals = by_cond.get(cond, [])
        if not vals:
            reports.append(("Baseline sanity", f"{cond}: no results found", "FAIL"))
            continue
        mean = statistics.mean(vals)
        ok = exp * (1 - tol) <= mean <= exp * (1 + tol)
        status = "PASS" if ok else "WARN"
        reports.append(("Baseline sanity",
                        f"{cond} = {mean:.3f} (expected: {exp} ± {tol:.0%})", status))
    return reports


def check_variance(results: list[dict[str, Any]],
                   cv_threshold: float) -> list[tuple[str, str, str]]:
    reports: list[tuple[str, str, str]] = []
    for cond, vals in sorted(_group_by_condition(results).items()):
        if len(vals) < 2:
            continue
        mean = statistics.mean(vals)
        if mean == 0:
            continue
        cv = statistics.stdev(vals) / abs(mean)
        ok = cv <= cv_threshold
        status = "PASS" if ok else "WARN"
        reports.append(("Variance",
                        f"{cond} CV={cv:.1%} {'<=' if ok else '>'} {cv_threshold:.0%} threshold",
                        status))
    return reports


def check_crashes(results: list[dict[str, Any]]) -> tuple[str, str]:
    bad = sum(1 for r in results for v in r.values() if _is_bad(v))
    return f"{bad} NaN/Inf values detected", "PASS" if bad == 0 else "FAIL"


# ── Report ────────────────────────────────────────────────────────────

def print_report(entries: list[tuple[str, str, str]],
                 fail_on_warning: bool) -> int:
    print("\nPhase Gate Report")
    print("=" * 40)
    warnings = failures = 0
    for label, detail, status in entries:
        if status == "WARN":
            warnings += 1
        elif status == "FAIL":
            failures += 1
        print(f"  [{status}] {label}: {detail}")
    parts = []
    if failures:
        parts.append(f"{failures} failure(s)")
    if warnings:
        parts.append(f"{warnings} warning(s)")
    overall_fail = failures > 0 or (fail_on_warning and warnings > 0)
    verdict = "FAIL" if overall_fail else "PASS"
    suffix = f" ({', '.join(parts)})" if parts else ""
    print(f"\n  Overall: {verdict}{suffix}\n")
    return 1 if overall_fail else 0


# ── Main ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate experiment phase gates")
    ap.add_argument("--experiment-state", default=DEFAULT_STATE,
                    help="Path to experiment-state.json (default: %(default)s)")
    ap.add_argument("--results-dir", default=DEFAULT_RESULTS,
                    help="Directory with per-run results.json (default: %(default)s)")
    ap.add_argument("--config", default=None,
                    help="Optional gate_spec.json with custom thresholds")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    state_path = Path(args.experiment_state)
    if not state_path.is_file():
        print(f"Error: experiment state not found: {state_path}", file=sys.stderr)
        return 1
    state = load_json(state_path)
    total_runs: int = state.get("total_runs", 0)
    phase: str = state.get("phase", "unknown")

    # Load optional config
    cv_threshold, completion_thr = DEFAULT_CV, 1.0
    baseline_specs: dict[str, dict[str, float]] = {}
    fail_on_warning = False
    if args.config:
        cfg = load_json(Path(args.config))
        cv_threshold = cfg.get("cv_threshold", cv_threshold)
        completion_thr = cfg.get("completion_threshold", completion_thr)
        baseline_specs = cfg.get("baseline_conditions", {})
        fail_on_warning = cfg.get("fail_on_warning", False)

    if args.verbose:
        print(f"Phase: {phase} | Expected runs: {total_runs}")

    results = collect_results(Path(args.results_dir))
    entries: list[tuple[str, str, str]] = []

    # 1. Completion
    msg, st = check_completion(results, total_runs, completion_thr)
    entries.append(("Completion", msg, st))
    # 2. Baseline sanity
    entries.extend(check_baseline(results, baseline_specs))
    # 3. Variance
    entries.extend(check_variance(results, cv_threshold))
    # 4. No-crash
    msg, st = check_crashes(results)
    entries.append(("No crashes", msg, st))

    return print_report(entries, fail_on_warning)


if __name__ == "__main__":
    raise SystemExit(main())
