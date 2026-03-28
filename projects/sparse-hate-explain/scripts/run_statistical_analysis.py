#!/usr/bin/env python3
"""Rigorous statistical analysis of full evaluation results.

Reads full_evaluation.csv (or all_results.csv), runs paired bootstrap tests,
computes Cohen's d effect sizes, generates hypothesis verdict table, and
produces publication-quality figures.

Usage:
    python scripts/run_statistical_analysis.py
    python scripts/run_statistical_analysis.py --input results/full_evaluation.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Display names and ordering (reuse from analyze_results.py)
# ---------------------------------------------------------------------------
CONDITION_CATEGORIES = {
    "Baselines": ["vanilla", "softmax_all", "softmax_all_strong"],
    "Sparsemax": ["sparsemax_all", "sparsemax_top12", "sparsemax_top24", "sparsemax_top36"],
    "Sparsemax (strong)": ["sparsemax_top24_strong"],
    "Lambda ablation": [
        "sparsemax_top24_lam01",
        "sparsemax_top24_lam05",
        "sparsemax_top24_lam10",
        "sparsemax_top24_lam20",
    ],
}

DISPLAY_NAMES = {
    "vanilla": "Vanilla",
    "softmax_all": "Softmax (all)",
    "softmax_all_strong": "Softmax (all, lambda=2)",
    "softmax_top24": "Softmax (top-24)",
    "sparsemax_all": "Sparsemax (all)",
    "sparsemax_top12": "Sparsemax (top-12)",
    "sparsemax_top24": "Sparsemax (top-24)",
    "sparsemax_top36": "Sparsemax (top-36)",
    "sparsemax_top24_strong": "Sparsemax (top-24, lambda=2)",
    "sparsemax_top24_lam01": "lambda=0.1",
    "sparsemax_top24_lam05": "lambda=0.5",
    "sparsemax_top24_lam10": "lambda=1.0",
    "sparsemax_top24_lam20": "lambda=2.0",
}

CB_PALETTE = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "cyan": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#000000",
}

CAT_COLORS = {
    "Baselines": CB_PALETTE["blue"],
    "Sparsemax": CB_PALETTE["orange"],
    "Sparsemax (strong)": CB_PALETTE["red"],
    "Lambda ablation": CB_PALETTE["green"],
}

# Metrics to analyse against vanilla baseline
METRICS = [
    "macro_f1", "sufficiency", "comprehensiveness",
    "token_f1", "auprc", "entropy", "sparsity_ratio",
]


def _apply_style() -> None:
    """Set publication-quality matplotlib defaults."""
    plt.rcParams.update({
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    })


def _save(fig: plt.Figure, name: str) -> None:
    """Save figure as PNG (300 dpi) and PDF."""
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {name}.png and {name}.pdf")


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def paired_bootstrap_test(
    values_a: np.ndarray,
    values_b: np.ndarray,
    n_bootstrap: int = 10_000,
    rng_seed: int = 0,
) -> Tuple[float, Tuple[float, float]]:
    """Paired bootstrap test (two-sided) with 95% CI for the difference.

    Returns:
        (p_value, (ci_lower, ci_upper)) for the difference b - a.
    """
    rng = np.random.RandomState(rng_seed)
    n = len(values_a)
    observed_diff = np.mean(values_b) - np.mean(values_a)
    diffs = values_b - values_a
    centered = diffs - diffs.mean()

    boot_diffs = np.empty(n_bootstrap)
    count = 0
    for k in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        boot_diffs[k] = np.mean(diffs[idx])
        if abs(np.mean(centered[idx])) >= abs(observed_diff):
            count += 1

    p_value = count / n_bootstrap
    ci_lower = float(np.percentile(boot_diffs, 2.5))
    ci_upper = float(np.percentile(boot_diffs, 97.5))
    return p_value, (ci_lower, ci_upper)


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Cohen's d for paired samples."""
    diff = b - a
    if diff.std() == 0:
        return 0.0
    return float(diff.mean() / diff.std())


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def make_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Mean +/- std for each metric grouped by condition."""
    rows: List[Dict[str, Any]] = []
    all_conditions = [c for cats in CONDITION_CATEGORIES.values() for c in cats]

    for cond in all_conditions:
        sub = df[df["condition"] == cond]
        if sub.empty:
            continue
        row: Dict[str, Any] = {"condition": DISPLAY_NAMES.get(cond, cond)}
        for m in METRICS:
            if m not in sub.columns:
                row[f"{m}_mean"] = np.nan
                row[f"{m}_std"] = np.nan
                row[f"{m}_str"] = "N/A"
                continue
            vals = sub[m].dropna()
            if len(vals) > 0:
                row[f"{m}_mean"] = float(vals.mean())
                row[f"{m}_std"] = float(vals.std())
                row[f"{m}_str"] = f"{vals.mean():.4f} +/- {vals.std():.4f}"
            else:
                row[f"{m}_mean"] = np.nan
                row[f"{m}_std"] = np.nan
                row[f"{m}_str"] = "N/A"
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Pairwise comparisons vs vanilla
# ---------------------------------------------------------------------------

def run_comparisons_vs_vanilla(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Run paired bootstrap, CI, and Cohen's d for every condition vs vanilla."""
    vanilla = df[df["condition"] == "vanilla"].sort_values("seed")
    rows: List[Dict[str, Any]] = []

    all_conditions = [c for cats in CONDITION_CATEGORIES.values() for c in cats]
    for cond in all_conditions:
        if cond == "vanilla":
            continue
        sub = df[df["condition"] == cond].sort_values("seed")
        if len(sub) != len(vanilla):
            continue

        row: Dict[str, Any] = {"condition": DISPLAY_NAMES.get(cond, cond)}
        for m in METRICS:
            if m not in df.columns:
                continue
            a = vanilla[m].dropna().values
            b = sub[m].dropna().values
            if len(a) != len(b) or len(a) == 0:
                continue
            p, (ci_lo, ci_hi) = paired_bootstrap_test(a, b)
            d = cohens_d(a, b)

            sig = ""
            if p < 0.01:
                sig = "**"
            elif p < 0.05:
                sig = "*"

            row[f"{m}_p"] = p
            row[f"{m}_d"] = d
            row[f"{m}_ci"] = f"[{ci_lo:.4f}, {ci_hi:.4f}]"
            row[f"{m}_sig"] = sig
        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Hypothesis verdicts
# ---------------------------------------------------------------------------

def compute_hypothesis_verdicts(
    df: pd.DataFrame,
    comp_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Generate verdict for each pre-registered hypothesis."""
    verdicts: List[Dict[str, Any]] = []

    # H1: sparsemax improves faithfulness
    h1_conditions = ["sparsemax_all", "sparsemax_top24"]
    h1_evidence = []
    for cond in h1_conditions:
        display = DISPLAY_NAMES.get(cond, cond)
        row = comp_df[comp_df["condition"] == display]
        if row.empty:
            continue
        for m in ["sufficiency", "comprehensiveness"]:
            p_col = f"{m}_p"
            d_col = f"{m}_d"
            if p_col in row.columns and d_col in row.columns:
                p = float(row[p_col].iloc[0]) if not row[p_col].isna().iloc[0] else 1.0
                d = float(row[d_col].iloc[0]) if not row[d_col].isna().iloc[0] else 0.0
                h1_evidence.append({
                    "condition": display, "metric": m, "p": p, "d": d,
                })

    h1_supported = any(
        e["p"] < 0.05 and e["d"] > 0 for e in h1_evidence
    )
    verdicts.append({
        "hypothesis": "H1: Sparsemax improves faithfulness",
        "verdict": "SUPPORTED" if h1_supported else "NOT SUPPORTED",
        "evidence": h1_evidence,
        "summary": (
            "Sparsemax conditions show significantly higher sufficiency/comprehensiveness"
            if h1_supported else
            "No significant improvement in faithfulness metrics"
        ),
    })

    # H2: selective supervision preserves accuracy (F1 within 1% of vanilla)
    vanilla_f1 = df[df["condition"] == "vanilla"]["macro_f1"].mean()
    h2_conditions = ["sparsemax_top24", "sparsemax_top12", "sparsemax_top36"]
    h2_evidence = []
    for cond in h2_conditions:
        sub = df[df["condition"] == cond]
        if sub.empty:
            continue
        cond_f1 = sub["macro_f1"].mean()
        diff = cond_f1 - vanilla_f1
        within_1pct = abs(diff) <= 0.01
        h2_evidence.append({
            "condition": DISPLAY_NAMES.get(cond, cond),
            "f1": float(cond_f1),
            "diff": float(diff),
            "within_1pct": within_1pct,
        })

    h2_supported = all(e["within_1pct"] for e in h2_evidence) if h2_evidence else False
    verdicts.append({
        "hypothesis": "H2: Selective supervision preserves accuracy",
        "verdict": "SUPPORTED" if h2_supported else "NOT SUPPORTED",
        "evidence": h2_evidence,
        "summary": (
            f"All selective-supervision conditions within 1% of vanilla F1 ({vanilla_f1:.4f})"
            if h2_supported else
            f"Some conditions exceed 1% F1 difference from vanilla ({vanilla_f1:.4f})"
        ),
    })

    # H3: combined (sparsemax + selective) is Pareto-optimal
    # Check if sparsemax_top24 is on the Pareto frontier of F1 vs sufficiency
    h3_evidence = []
    pareto_conds = ["vanilla", "softmax_all", "sparsemax_all", "sparsemax_top24"]
    for cond in pareto_conds:
        sub = df[df["condition"] == cond]
        if sub.empty:
            continue
        f1_val = sub["macro_f1"].mean()
        suff_col = "sufficiency" if "sufficiency" in sub.columns else None
        suff_val = float(sub[suff_col].mean()) if suff_col and not sub[suff_col].isna().all() else 0.0
        h3_evidence.append({
            "condition": DISPLAY_NAMES.get(cond, cond),
            "f1": float(f1_val),
            "sufficiency": suff_val,
        })

    # Check Pareto dominance: sparsemax_top24 should not be dominated
    top24_ev = next((e for e in h3_evidence if e["condition"] == "Sparsemax (top-24)"), None)
    h3_supported = False
    if top24_ev:
        dominated = False
        for other in h3_evidence:
            if other["condition"] == top24_ev["condition"]:
                continue
            if other["f1"] >= top24_ev["f1"] and other["sufficiency"] >= top24_ev["sufficiency"]:
                if other["f1"] > top24_ev["f1"] or other["sufficiency"] > top24_ev["sufficiency"]:
                    dominated = True
                    break
        h3_supported = not dominated

    verdicts.append({
        "hypothesis": "H3: Combined sparsemax+selective is Pareto-optimal",
        "verdict": "SUPPORTED" if h3_supported else "NOT SUPPORTED",
        "evidence": h3_evidence,
        "summary": (
            "Sparsemax (top-24) is not dominated on the F1-sufficiency frontier"
            if h3_supported else
            "Sparsemax (top-24) is dominated by another condition"
        ),
    })

    # H4: middle layers are most important
    hi_path = RESULTS_DIR / "head_importance" / "head_importance.json"
    h4_evidence = []
    h4_supported = False
    if hi_path.exists():
        with open(hi_path) as f:
            hi_data = json.load(f)
        matrix = np.array(hi_data["head_importance"])  # (12, 12)
        layer_importance = matrix.sum(axis=1)  # sum over heads per layer
        total = layer_importance.sum()
        layer_frac = layer_importance / total if total > 0 else layer_importance

        # Middle layers: 4-8 (0-indexed)
        middle_frac = float(layer_frac[4:9].sum())
        early_frac = float(layer_frac[0:4].sum())
        late_frac = float(layer_frac[9:12].sum())

        h4_evidence = [
            {"region": "early (0-3)", "fraction": early_frac},
            {"region": "middle (4-8)", "fraction": middle_frac},
            {"region": "late (9-11)", "fraction": late_frac},
        ]
        h4_supported = middle_frac > early_frac and middle_frac > late_frac

    verdicts.append({
        "hypothesis": "H4: Middle layers most important",
        "verdict": "SUPPORTED" if h4_supported else "NOT SUPPORTED",
        "evidence": h4_evidence,
        "summary": (
            "Middle layers (4-8) have the highest aggregate importance"
            if h4_supported else
            "Middle layers do not have the highest aggregate importance"
        ),
    })

    return verdicts


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def figure1_all_metrics_bar(df: pd.DataFrame) -> None:
    """Bar chart with F1, sufficiency, comprehensiveness, and token_f1."""
    print("Figure 1 (updated): Multi-metric bar chart ...")

    bar_metrics = ["macro_f1", "sufficiency", "comprehensiveness", "token_f1"]
    metric_labels = ["Macro-F1", "Sufficiency", "Comprehensiveness", "Token F1"]

    # Build ordered conditions
    ordered: List[str] = []
    cat_for: List[str] = []
    for cat, conds in CONDITION_CATEGORIES.items():
        for c in conds:
            if c in df["condition"].values:
                ordered.append(c)
                cat_for.append(cat)

    n_conds = len(ordered)
    n_metrics = len(bar_metrics)
    x = np.arange(n_conds)
    width = 0.8 / n_metrics

    fig, ax = plt.subplots(figsize=(14, 6))
    for mi, (metric, label) in enumerate(zip(bar_metrics, metric_labels)):
        if metric not in df.columns:
            continue
        means = []
        stds = []
        for cond in ordered:
            sub = df[df["condition"] == cond][metric].dropna()
            means.append(float(sub.mean()) if len(sub) > 0 else 0.0)
            stds.append(float(sub.std()) if len(sub) > 0 else 0.0)

        offset = (mi - n_metrics / 2 + 0.5) * width
        ax.bar(
            x + offset, means, width, yerr=stds, capsize=2,
            label=label, alpha=0.85,
        )

    display = [DISPLAY_NAMES.get(c, c) for c in ordered]
    ax.set_xticks(x)
    ax.set_xticklabels(display, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Score")
    ax.set_title("Full Evaluation Metrics Across Conditions (mean +/- std, 3 seeds)")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    _save(fig, "fig1_all_metrics_bar")


def figure6_sufficiency_vs_comprehensiveness(df: pd.DataFrame) -> None:
    """Scatter plot: sufficiency vs comprehensiveness by condition."""
    print("Figure 6: Sufficiency vs comprehensiveness scatter ...")

    if "sufficiency" not in df.columns or "comprehensiveness" not in df.columns:
        print("  Skipping: sufficiency/comprehensiveness columns not found.")
        return

    fig, ax = plt.subplots(figsize=(8, 6))

    all_conditions = [c for cats in CONDITION_CATEGORIES.values() for c in cats]
    cat_lookup = {}
    for cat, conds in CONDITION_CATEGORIES.items():
        for c in conds:
            cat_lookup[c] = cat

    for cond in all_conditions:
        sub = df[df["condition"] == cond]
        if sub.empty or sub["sufficiency"].isna().all() or sub["comprehensiveness"].isna().all():
            continue
        cat = cat_lookup.get(cond, "Other")
        color = CAT_COLORS.get(cat, CB_PALETTE["black"])
        display = DISPLAY_NAMES.get(cond, cond)

        suff_mean = float(sub["sufficiency"].mean())
        comp_mean = float(sub["comprehensiveness"].mean())
        suff_std = float(sub["sufficiency"].std())
        comp_std = float(sub["comprehensiveness"].std())

        ax.errorbar(
            suff_mean, comp_mean,
            xerr=suff_std, yerr=comp_std,
            marker="o", color=color, capsize=3,
            markersize=8, linewidth=1,
        )
        ax.annotate(
            display, (suff_mean, comp_mean),
            textcoords="offset points", xytext=(5, 5),
            fontsize=8, color=color,
        )

    ax.set_xlabel("Sufficiency (higher = rationale alone preserves prediction)")
    ax.set_ylabel("Comprehensiveness (higher = rationale removal hurts prediction)")
    ax.set_title("Faithfulness: Sufficiency vs. Comprehensiveness")

    # Category legend
    from matplotlib.patches import Patch
    seen = set()
    handles = []
    for cond in all_conditions:
        cat = cat_lookup.get(cond, "Other")
        if cat not in seen:
            seen.add(cat)
            handles.append(Patch(facecolor=CAT_COLORS.get(cat, "gray"), label=cat))
    ax.legend(handles=handles, frameon=False, loc="best")

    fig.tight_layout()
    _save(fig, "fig6_sufficiency_vs_comprehensiveness")


def figure7_per_class_f1_heatmap(df: pd.DataFrame) -> None:
    """Per-class F1 heatmap across conditions."""
    print("Figure 7: Per-class F1 heatmap ...")

    class_cols = ["per_class_f1_0", "per_class_f1_1", "per_class_f1_2"]
    available = [c for c in class_cols if c in df.columns]
    if not available:
        print("  Skipping: per-class F1 columns not found.")
        return

    class_names = ["Hate Speech", "Offensive", "Normal"]

    all_conditions = [c for cats in CONDITION_CATEGORIES.values() for c in cats]
    ordered: List[str] = []
    for cond in all_conditions:
        if cond in df["condition"].values:
            ordered.append(cond)

    matrix: List[List[float]] = []
    labels: List[str] = []
    for cond in ordered:
        sub = df[df["condition"] == cond]
        if sub.empty:
            continue
        row = []
        for col in available:
            vals = sub[col].dropna()
            row.append(float(vals.mean()) if len(vals) > 0 else 0.0)
        matrix.append(row)
        labels.append(DISPLAY_NAMES.get(cond, cond))

    if not matrix:
        print("  Skipping: no data for heatmap.")
        return

    mat = np.array(matrix)
    fig, ax = plt.subplots(figsize=(7, max(5, len(labels) * 0.4 + 1)))
    sns.heatmap(
        mat, ax=ax,
        xticklabels=class_names[:len(available)],
        yticklabels=labels,
        annot=True, fmt=".3f",
        cmap="YlOrRd", linewidths=0.5, linecolor="white",
        cbar_kws={"label": "F1 Score"},
    )
    ax.set_title("Per-Class F1 Across Conditions (mean over 3 seeds)")
    fig.tight_layout()
    _save(fig, "fig7_per_class_f1_heatmap")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run statistical analysis on full evaluation results.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to full_evaluation.csv (default: auto-detect).",
    )
    args = parser.parse_args()

    # Auto-detect input
    if args.input:
        input_path = Path(args.input)
    elif (RESULTS_DIR / "full_evaluation.csv").exists():
        input_path = RESULTS_DIR / "full_evaluation.csv"
    elif (RESULTS_DIR / "all_results.csv").exists():
        input_path = RESULTS_DIR / "all_results.csv"
    else:
        print("ERROR: No results CSV found. Run run_full_evaluation.py first.")
        sys.exit(1)

    print(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows, {df['condition'].nunique()} conditions.")

    _apply_style()

    # 1. Summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE (mean +/- std over seeds)")
    print("=" * 70)
    summary = make_summary_table(df)
    str_cols = [c for c in summary.columns if c.endswith("_str")]
    if str_cols:
        print(summary[["condition"] + str_cols].to_string(index=False))

    # 2. Pairwise comparisons vs vanilla
    print("\n" + "=" * 70)
    print("PAIRWISE COMPARISONS VS VANILLA (bootstrap p-value, Cohen's d, 95% CI)")
    print("=" * 70)
    comp_df = run_comparisons_vs_vanilla(df)
    if not comp_df.empty:
        # Show a readable selection
        show_cols = ["condition"]
        for m in METRICS:
            for suffix in ["_p", "_d", "_ci", "_sig"]:
                col = f"{m}{suffix}"
                if col in comp_df.columns:
                    show_cols.append(col)
        show_cols = [c for c in show_cols if c in comp_df.columns]
        print(comp_df[show_cols].to_string(index=False))
    else:
        print("No comparisons could be run (need matching seeds).")

    # 3. Hypothesis verdicts
    print("\n" + "=" * 70)
    print("HYPOTHESIS VERDICTS")
    print("=" * 70)
    verdicts = compute_hypothesis_verdicts(df, comp_df)
    for v in verdicts:
        status = v["verdict"]
        marker = "[PASS]" if "SUPPORTED" == status else "[FAIL]"
        print(f"\n{marker} {v['hypothesis']}")
        print(f"  Verdict: {status}")
        print(f"  Summary: {v['summary']}")

    # 4. Save results
    output = {
        "summary": summary.to_dict(orient="records"),
        "comparisons": comp_df.to_dict(orient="records") if not comp_df.empty else [],
        "verdicts": verdicts,
    }
    output_path = RESULTS_DIR / "statistical_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")

    # 5. Figures
    print("\n" + "=" * 70)
    print("GENERATING FIGURES")
    print("=" * 70)
    figure1_all_metrics_bar(df)
    figure6_sufficiency_vs_comprehensiveness(df)
    figure7_per_class_f1_heatmap(df)

    print(f"\nAll figures saved to {FIGURES_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
