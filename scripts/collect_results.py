#!/usr/bin/env python3
"""
Result Collector — scan experiment outputs, extract metrics, assemble tables, detect gaps.

Automates the result-collector skill's procedural pipeline.
Produces analysis-input/ with results.csv, summary.csv, run-manifest.json,
gap-report.md, and organized figures.

Usage:
    python scripts/collect_results.py --results-dir outputs/
    python scripts/collect_results.py --results-dir outputs/ --experiment-plan experiment-plan.md
"""

import argparse
import csv
import json
import math
import re
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Optional: scipy for exact t-distribution CI
try:
    from scipy.stats import t as t_dist  # type: ignore[import-untyped]
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Hardcoded t-distribution critical values (two-tailed) for common df
_T_CRIT = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
           6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}  # type: Dict[int, float]

JSON_CANDIDATES = ("results.json", "metrics.json", "eval_results.json")
CSV_CANDIDATES = ("results.csv", "eval_results.csv")
TIMING_KEYS = {"elapsed_seconds", "wall_time", "training_time"}
GPU_KEYS = {"gpu_memory", "peak_memory", "gpu_memory_peak_mb"}
FIGURE_EXTS = {".pdf", ".png", ".svg"}
RUN_NAME_RE = re.compile(
    r"^(?P<strategy>[A-Za-z0-9_-]+?)_(?P<task>[A-Za-z0-9_-]+?)_seed(?P<seed>\d+)$"
)


def _t_critical(df: int, ci_level: float) -> float:
    """Return t critical value for *df* degrees of freedom."""
    alpha = 1.0 - ci_level
    if HAS_SCIPY:
        return float(t_dist.ppf(1.0 - alpha / 2.0, df))
    if ci_level == 0.95 and df in _T_CRIT:
        return _T_CRIT[df]
    if df >= 30:
        return 1.96
    # Rough approximation for unlisted df via linear interpolation
    lo = max(k for k in _T_CRIT if k <= df) if any(k <= df for k in _T_CRIT) else 1
    hi = min(k for k in _T_CRIT if k >= df) if any(k >= df for k in _T_CRIT) else 30
    if lo == hi:
        return _T_CRIT.get(lo, 1.96)
    t_lo = _T_CRIT.get(lo, 1.96)
    t_hi = _T_CRIT.get(hi, 1.96)
    return t_lo + (t_hi - t_lo) * (df - lo) / (hi - lo)


# ── Scanning ────────────────────────────────────────────────────────────────

def _parse_run_dir(run_dir: Path) -> Dict[str, Any]:
    """Extract run config from Hydra metadata or directory name."""
    info = {"run_id": run_dir.name, "path": str(run_dir)}  # type: Dict[str, Any]
    hydra_cfg = run_dir / ".hydra" / "config.yaml"
    if hydra_cfg.exists():
        info["config_source"] = "hydra"
        # Lightweight YAML key extraction (no pyyaml dependency)
        for line in hydra_cfg.read_text(errors="replace").splitlines():
            m = re.match(r"^(\w+):\s*(.+)$", line)
            if m:
                info.setdefault(m.group(1), m.group(2).strip())
    else:
        m = RUN_NAME_RE.match(run_dir.name)
        if m:
            info.update(m.groupdict())
            info["config_source"] = "dirname"
        else:
            info["config_source"] = "unknown"
    return info


def scan_runs(results_dir: Path) -> List[Dict[str, Any]]:
    """Walk *results_dir* and classify every subdirectory."""
    runs = []  # type: List[Dict[str, Any]]
    if not results_dir.is_dir():
        return runs
    for child in sorted(results_dir.rglob("*")):
        if not child.is_dir():
            continue
        # Only consider leaf-ish directories (contain files, not just subdirs)
        files = [f for f in child.iterdir() if f.is_file()]
        if not files:
            continue
        info = _parse_run_dir(child)
        has_output = any(
            (child / n).exists() for n in (JSON_CANDIDATES + CSV_CANDIDATES)
        )
        has_logs = any(f.suffix in {".log", ".err", ".out"} for f in files)
        if has_output:
            info["status"] = "completed"
        elif has_logs:
            info["status"] = "failed"
        else:
            info["status"] = "incomplete"
        runs.append(info)
    return runs


# ── Metric Extraction ───────────────────────────────────────────────────────

def _extract_numeric(data: Dict[str, Any], prefix: str = "") -> Dict[str, float]:
    """Recursively extract numeric fields from a (possibly nested) dict."""
    out = {}  # type: Dict[str, float]
    for k, v in data.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
            out[key] = float(v)
        elif isinstance(v, dict):
            out.update(_extract_numeric(v, key))
    return out


def _read_json_metrics(path: Path) -> Dict[str, float]:
    try:
        data = json.loads(path.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return {}
    if isinstance(data, dict):
        return _extract_numeric(data)
    if isinstance(data, list) and data and isinstance(data[-1], dict):
        return _extract_numeric(data[-1])
    return {}


def _read_csv_metrics(path: Path) -> Dict[str, float]:
    try:
        with path.open(newline="", errors="replace") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
    except OSError:
        return {}
    if not rows:
        return {}
    last = rows[-1]
    out = {}  # type: Dict[str, float]
    for k, v in last.items():
        if k is None:
            continue
        try:
            fv = float(v)  # type: ignore[arg-type]
            if math.isfinite(fv):
                out[k] = fv
        except (ValueError, TypeError):
            pass
    return out


def extract_metrics(run: Dict[str, Any]) -> Dict[str, float]:
    """Return all numeric metrics for a completed run."""
    run_dir = Path(run["path"])
    for name in JSON_CANDIDATES:
        p = run_dir / name
        if p.exists():
            metrics = _read_json_metrics(p)
            if metrics:
                return metrics
    for name in CSV_CANDIDATES:
        p = run_dir / name
        if p.exists():
            metrics = _read_csv_metrics(p)
            if metrics:
                return metrics
    return {}


def _split_metrics(metrics: Dict[str, float]) -> Tuple[Dict[str, float], Optional[float], Optional[float]]:
    """Separate timing and GPU info from regular metrics."""
    timing = None  # type: Optional[float]
    gpu = None  # type: Optional[float]
    clean = {}  # type: Dict[str, float]
    for k, v in metrics.items():
        kl = k.lower().replace(".", "_")
        if any(tk in kl for tk in TIMING_KEYS):
            timing = v
        elif any(gk in kl for gk in GPU_KEYS):
            gpu = v
        else:
            clean[k] = v
    return clean, timing, gpu


# ── Table Assembly ──────────────────────────────────────────────────────────

def assemble_tables(
    runs: List[Dict[str, Any]], ci_level: float
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build per-run rows and summary rows."""
    per_run_rows = []  # type: List[Dict[str, Any]]
    # Identify grouping columns (everything that isn't a metric, path, or internal)
    _skip = {"status", "path", "config_source", "metrics", "wall_time", "gpu_memory"}

    for run in runs:
        if run["status"] != "completed":
            continue
        raw_metrics = extract_metrics(run)
        clean, timing, gpu = _split_metrics(raw_metrics)
        row = {"run_id": run["run_id"]}  # type: Dict[str, Any]
        for k, v in run.items():
            if k not in _skip and k != "run_id":
                row[k] = v
        row.update(clean)
        if timing is not None:
            row["wall_time_seconds"] = timing
        if gpu is not None:
            row["gpu_memory_peak_mb"] = gpu
        per_run_rows.append(row)

    if not per_run_rows:
        return per_run_rows, []

    # Detect metric columns vs. grouping columns
    all_keys = set()
    for r in per_run_rows:
        all_keys.update(r.keys())
    meta_keys = {"run_id", "path", "config_source", "wall_time_seconds", "gpu_memory_peak_mb"}
    numeric_keys = {k for k in all_keys if all(isinstance(r.get(k), (int, float)) for r in per_run_rows if k in r)}
    group_keys = sorted(all_keys - numeric_keys - meta_keys - {"seed"})
    metric_keys = sorted(numeric_keys - meta_keys - {"seed"})

    # Build summary
    groups = defaultdict(list)  # type: Dict[Tuple[str, ...], List[Dict[str, Any]]]
    for r in per_run_rows:
        key = tuple(str(r.get(k, "")) for k in group_keys)
        groups[key].append(r)

    summary_rows = []  # type: List[Dict[str, Any]]
    for key, members in sorted(groups.items()):
        srow = {k: v for k, v in zip(group_keys, key)}  # type: Dict[str, Any]
        srow["n_seeds"] = len(members)
        for mk in metric_keys:
            vals = [m[mk] for m in members if mk in m and isinstance(m[mk], (int, float))]
            if not vals:
                continue
            mean = statistics.mean(vals)
            srow[f"{mk}_mean"] = mean
            if len(vals) >= 2:
                std = statistics.stdev(vals)
                srow[f"{mk}_std"] = std
                df = len(vals) - 1
                t_crit = _t_critical(df, ci_level)
                margin = t_crit * std / math.sqrt(len(vals))
                srow[f"{mk}_ci_lower"] = mean - margin
                srow[f"{mk}_ci_upper"] = mean + margin
            else:
                srow[f"{mk}_std"] = 0.0
        summary_rows.append(srow)

    return per_run_rows, summary_rows


# ── Gap Detection ───────────────────────────────────────────────────────────

def _parse_experiment_plan(plan_path: Path) -> List[Dict[str, str]]:
    """Extract expected runs from markdown tables in the experiment plan."""
    text = plan_path.read_text(errors="replace")
    expected = []  # type: List[Dict[str, str]]
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "|" in line and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            headers = [h.strip().lower() for h in line.split("|") if h.strip()]
            i += 2  # skip header + separator
            while i < len(lines) and "|" in lines[i]:
                vals = [v.strip() for v in lines[i].split("|") if v.strip()]
                if len(vals) == len(headers):
                    expected.append(dict(zip(headers, vals)))
                i += 1
            continue
        i += 1
    return expected


def detect_gaps(
    runs: List[Dict[str, Any]], plan_path: Path
) -> str:
    """Generate gap-report.md content."""
    expected = _parse_experiment_plan(plan_path)
    if not expected:
        return "# Gap Report\n\nNo expected runs parsed from experiment plan.\n"

    run_ids = {r["run_id"] for r in runs}
    status_map = {r["run_id"]: r["status"] for r in runs}

    lines = ["# Gap Report\n"]
    missing = failed = incomplete = 0
    table_rows = []  # type: List[str]
    for entry in expected:
        # Try to match by constructing possible run_id patterns
        parts = [entry.get(k, "") for k in ("strategy", "method", "task", "dataset")]
        seed = entry.get("seed", "")
        candidates = [f"{'_'.join(p for p in parts if p)}_seed{seed}"]
        # Also try raw values joined
        candidates.append("_".join(v for v in entry.values() if v))

        matched_status = None
        for c in candidates:
            if c in status_map:
                matched_status = status_map[c]
                break
        if matched_status is None:
            matched_status = "missing"

        if matched_status == "missing":
            missing += 1
            table_rows.append(f"| {' | '.join(entry.values())} | missing |")
        elif matched_status == "failed":
            failed += 1
            table_rows.append(f"| {' | '.join(entry.values())} | failed |")
        elif matched_status == "incomplete":
            incomplete += 1
            table_rows.append(f"| {' | '.join(entry.values())} | incomplete |")

    total_gaps = missing + failed + incomplete
    lines.append(f"**Total expected**: {len(expected)}  ")
    lines.append(f"**Gaps**: {total_gaps} ({missing} missing, {failed} failed, {incomplete} incomplete)\n")

    if table_rows:
        headers = list(expected[0].keys()) + ["status"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        lines.extend(table_rows)
    else:
        lines.append("All expected runs are completed.")

    return "\n".join(lines) + "\n"


# ── Figures ─────────────────────────────────────────────────────────────────

def organize_figures(runs: List[Dict[str, Any]], fig_dir: Path, dry_run: bool) -> int:
    """Copy figure files from run directories to *fig_dir*. Return count."""
    count = 0
    for run in runs:
        if run["status"] != "completed":
            continue
        run_dir = Path(run["path"])
        for f in run_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in FIGURE_EXTS:
                dest = fig_dir / f"{run['run_id']}_{f.name}"
                if not dry_run:
                    fig_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
                count += 1
    return count


# ── Write Helpers ───────────────────────────────────────────────────────────

def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Collect experiment results into analysis-input/.")
    ap.add_argument("--results-dir", required=True, type=Path, help="Root experiment output directory.")
    ap.add_argument("--experiment-plan", type=Path, default=None, help="Experiment plan .md for gap detection.")
    ap.add_argument("--output-dir", type=Path, default=Path("analysis-input"), help="Output directory (default: analysis-input/).")
    ap.add_argument("--ci-level", type=float, default=0.95, help="Confidence interval level (default: 0.95).")
    ap.add_argument("--dry-run", action="store_true", help="Print summary without writing files.")
    args = ap.parse_args()

    # 1. Scan
    runs = scan_runs(args.results_dir)
    n_completed = sum(1 for r in runs if r["status"] == "completed")
    n_failed = sum(1 for r in runs if r["status"] == "failed")
    n_incomplete = sum(1 for r in runs if r["status"] == "incomplete")
    print(f"Scanned {args.results_dir}: {len(runs)} runs "
          f"({n_completed} completed, {n_failed} failed, {n_incomplete} incomplete)")

    if not runs:
        print("No runs found. Nothing to collect.")
        return 1

    # 2-3. Extract metrics & assemble tables
    per_run, summary = assemble_tables(runs, args.ci_level)

    # 4. Gap detection
    gap_report = None  # type: Optional[str]
    if args.experiment_plan and args.experiment_plan.exists():
        gap_report = detect_gaps(runs, args.experiment_plan)
    elif args.experiment_plan:
        print(f"Warning: experiment plan {args.experiment_plan} not found. Skipping gap detection.")

    # 5. Build manifest
    manifest = []
    for run in runs:
        entry = {"run_id": run["run_id"], "status": run["status"], "path": run["path"]}
        if "config_source" in run:
            entry["config_source"] = run["config_source"]
        manifest.append(entry)

    # 6. Figures
    fig_dir = args.output_dir / "figures"
    n_figs = organize_figures(runs, fig_dir, args.dry_run)

    # Summary
    print(f"  Results rows: {len(per_run)}")
    print(f"  Summary groups: {len(summary)}")
    print(f"  Figures collected: {n_figs}")
    if gap_report:
        missing_count = gap_report.count("missing")
        print(f"  Gap report generated (see gap-report.md)")

    if args.dry_run:
        print("Dry run — no files written.")
        return 0

    # Write outputs
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "results.csv", per_run)
    _write_csv(args.output_dir / "summary.csv", summary)
    (args.output_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if gap_report:
        (args.output_dir / "gap-report.md").write_text(gap_report)

    print(f"Output written to {args.output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
