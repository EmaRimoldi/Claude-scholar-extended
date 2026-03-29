#!/usr/bin/env python3
"""Generate publication-quality figures from experiment results.

Encodes visualization best practices so the LLM doesn't need to load
~80 lines of visualization-best-practices.md for standard analyses.

Usage:
    python scripts/generate_figures.py --results analysis-input/results.csv \
        --metric primary_metric --groupby strategy,task \
        --output-dir analysis-output/figures/
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: matplotlib and numpy required. Install with: uv pip install matplotlib numpy", file=sys.stderr)
    sys.exit(1)

# Okabe-Ito colorblind-safe palette
PALETTE = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
        "axes.titlesize": 10, "legend.fontsize": 8, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "figure.dpi": 300, "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02, "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.grid": True, "grid.alpha": 0.3,
        "axes.spines.top": False, "axes.spines.right": False,
    })


def load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def group_by(rows: list[dict], keys: list[str]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        k = tuple(r[k] for k in keys)
        groups[k].append(r)
    return dict(sorted(groups.items()))


def stats(values: list[float]) -> tuple[float, float, float, float]:
    n = len(values)
    if n == 0:
        return 0, 0, 0, 0
    mean = sum(values) / n
    if n < 2:
        return mean, 0, mean, mean
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))
    t_vals = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
              6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
    t = t_vals.get(n - 1, 1.96)
    ci = t * std / math.sqrt(n)
    return mean, std, mean - ci, mean + ci


def fig_bar_chart(rows: list[dict], metric: str, groupby: list[str],
                  outdir: Path, fmt: str) -> Path:
    """Grouped bar chart: primary groupby on x-axis, secondary as color."""
    primary = groupby[0]
    secondary = groupby[1] if len(groupby) > 1 else None

    if secondary:
        sec_vals = sorted(set(r[secondary] for r in rows))
        prim_vals = sorted(set(r[primary] for r in rows))
        n_sec = len(sec_vals)
        width = 0.8 / n_sec
        fig, ax = plt.subplots(figsize=(max(5.5, len(prim_vals) * 1.2), 4))
        for i, sv in enumerate(sec_vals):
            means, cis = [], []
            for pv in prim_vals:
                vals = [float(r[metric]) for r in rows if r[primary] == pv and r[secondary] == sv]
                m, _, lo, hi = stats(vals)
                means.append(m)
                cis.append(m - lo)
            x = np.arange(len(prim_vals)) + i * width - 0.4 + width / 2
            ax.bar(x, means, width, yerr=cis, capsize=3, label=sv,
                   color=PALETTE[i % len(PALETTE)], edgecolor="black", linewidth=0.4)
        ax.set_xticks(range(len(prim_vals)))
        ax.set_xticklabels(prim_vals, rotation=30, ha="right")
        ax.legend()
    else:
        groups = group_by(rows, [primary])
        labels = [k[0] for k in groups]
        means, cis = [], []
        for vals_list in groups.values():
            vals = [float(r[metric]) for r in vals_list]
            m, _, lo, hi = stats(vals)
            means.append(m)
            cis.append(m - lo)
        fig, ax = plt.subplots(figsize=(max(5.5, len(labels) * 0.8), 4))
        ax.bar(range(len(labels)), means, yerr=cis, capsize=3,
               color=PALETTE[:len(labels)], edgecolor="black", linewidth=0.4)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right")

    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(f"{metric.replace('_', ' ').title()} by {primary.replace('_', ' ').title()}")
    path = outdir / f"fig-bar-{primary}.{fmt}"
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_interaction(rows: list[dict], metric: str, groupby: list[str],
                    outdir: Path, fmt: str) -> Path | None:
    """Interaction plot: lines for secondary variable across primary."""
    if len(groupby) < 2:
        return None
    primary, secondary = groupby[0], groupby[1]
    prim_vals = sorted(set(r[primary] for r in rows))
    sec_vals = sorted(set(r[secondary] for r in rows))

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    for i, sv in enumerate(sec_vals):
        means, cis = [], []
        for pv in prim_vals:
            vals = [float(r[metric]) for r in rows if r[primary] == pv and r[secondary] == sv]
            m, _, lo, _ = stats(vals)
            means.append(m)
            cis.append(m - lo)
        ax.errorbar(range(len(prim_vals)), means, yerr=cis,
                     marker=MARKERS[i % len(MARKERS)], capsize=3, label=sv,
                     color=PALETTE[i % len(PALETTE)], linewidth=1.5, markersize=6)
    ax.set_xticks(range(len(prim_vals)))
    ax.set_xticklabels(prim_vals, rotation=30, ha="right")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_xlabel(primary.replace("_", " ").title())
    ax.legend(loc="best")
    ax.set_title(f"{primary} × {secondary} Interaction")
    path = outdir / f"fig-interaction-{primary}-{secondary}.{fmt}"
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_heatmap(rows: list[dict], metric: str, groupby: list[str],
                outdir: Path, fmt: str) -> Path | None:
    """Heatmap: primary on y-axis, secondary on x-axis."""
    if len(groupby) < 2:
        return None
    primary, secondary = groupby[0], groupby[1]
    prim_vals = sorted(set(r[primary] for r in rows))
    sec_vals = sorted(set(r[secondary] for r in rows))

    data = np.zeros((len(prim_vals), len(sec_vals)))
    for i, pv in enumerate(prim_vals):
        for j, sv in enumerate(sec_vals):
            vals = [float(r[metric]) for r in rows if r[primary] == pv and r[secondary] == sv]
            data[i, j] = sum(vals) / len(vals) if vals else float("nan")

    fig, ax = plt.subplots(figsize=(max(4, len(sec_vals) * 1.2), max(3, len(prim_vals) * 0.6)))
    vmin, vmax = np.nanmin(data), np.nanmax(data)
    im = ax.imshow(data, cmap="viridis", aspect="auto", vmin=vmin, vmax=vmax)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if not np.isnan(v):
                color = "white" if v < (vmin + vmax) / 2 else "black"
                ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=7, color=color)
    ax.set_xticks(range(len(sec_vals)))
    ax.set_xticklabels(sec_vals, rotation=30, ha="right")
    ax.set_yticks(range(len(prim_vals)))
    ax.set_yticklabels(prim_vals)
    plt.colorbar(im, ax=ax, label=metric.replace("_", " ").title(), shrink=0.8)
    path = outdir / f"fig-heatmap-{primary}-{secondary}.{fmt}"
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_violin(rows: list[dict], metric: str, groupby: list[str],
               outdir: Path, fmt: str) -> Path:
    """Violin plot showing distribution per primary group."""
    primary = groupby[0]
    groups = group_by(rows, [primary])
    labels = [k[0] for k in groups]
    data = [[float(r[metric]) for r in v] for v in groups.values()]

    fig, ax = plt.subplots(figsize=(max(5.5, len(labels) * 0.9), 4))
    parts = ax.violinplot(data, positions=range(len(labels)), showmeans=True, showmedians=True)
    for i, pc in enumerate(parts.get("bodies", [])):
        pc.set_facecolor(PALETTE[i % len(PALETTE)])
        pc.set_alpha(0.7)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(metric.replace("_", " ").title())
    path = outdir / f"fig-violin-{primary}.{fmt}"
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate publication-quality figures")
    parser.add_argument("--results", required=True, help="Path to results CSV")
    parser.add_argument("--metric", required=True, help="Primary metric column name")
    parser.add_argument("--groupby", default="strategy,task", help="Comma-separated grouping columns")
    parser.add_argument("--output-dir", default="analysis-output/figures/", help="Output directory")
    parser.add_argument("--format", default="pdf", choices=["pdf", "png", "svg"], help="Figure format")
    parser.add_argument("--seed-col", default="seed", help="Seed column name")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"ERROR: Results file not found: {results_path}", file=sys.stderr)
        return 1

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    groupby = [g.strip() for g in args.groupby.split(",")]

    apply_style()
    rows = load_csv(results_path)
    print(f"Loaded {len(rows)} rows from {results_path}")

    # Validate columns
    for col in groupby + [args.metric]:
        if col not in rows[0]:
            print(f"ERROR: Column '{col}' not found. Available: {list(rows[0].keys())}", file=sys.stderr)
            return 1

    generated = []

    # Always generate bar chart and violin
    p = fig_bar_chart(rows, args.metric, groupby, outdir, args.format)
    generated.append(p)
    print(f"  [1] Bar chart: {p}")

    p = fig_violin(rows, args.metric, groupby, outdir, args.format)
    generated.append(p)
    print(f"  [2] Violin plot: {p}")

    # Interaction plot and heatmap only if 2+ groupby variables
    if len(groupby) >= 2:
        p = fig_interaction(rows, args.metric, groupby, outdir, args.format)
        if p:
            generated.append(p)
            print(f"  [3] Interaction plot: {p}")

        p = fig_heatmap(rows, args.metric, groupby, outdir, args.format)
        if p:
            generated.append(p)
            print(f"  [4] Heatmap: {p}")

    print(f"\nGenerated {len(generated)} figures in {outdir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
