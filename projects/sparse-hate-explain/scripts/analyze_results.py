#!/usr/bin/env python
"""Comprehensive analysis of sparse-hate-explain experiment results.

Produces summary tables, bootstrap significance tests, and publication-quality
figures (PNG 300 dpi + PDF) suitable for NeurIPS / Nature submissions.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
SEEDS = [42, 123, 456]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Colorblind-friendly palette (Okabe-Ito)
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

# Category -> conditions mapping (display order)
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

# Nice display names
DISPLAY_NAMES = {
    "vanilla": "Vanilla",
    "softmax_all": "Softmax (all)",
    "softmax_all_strong": "Softmax (all, λ=2)",
    "softmax_top24": "Softmax (top-24)",
    "sparsemax_all": "Sparsemax (all)",
    "sparsemax_top12": "Sparsemax (top-12)",
    "sparsemax_top24": "Sparsemax (top-24)",
    "sparsemax_top36": "Sparsemax (top-36)",
    "sparsemax_top24_strong": "Sparsemax (top-24, λ=2)",
    "sparsemax_top24_lam01": "λ=0.1",
    "sparsemax_top24_lam05": "λ=0.5",
    "sparsemax_top24_lam10": "λ=1.0",
    "sparsemax_top24_lam20": "λ=2.0",
}

# Condition -> number of supervised heads (for Figure 2)
HEADS_MAP = {
    "vanilla": 0,
    "softmax_all": 144,
    "softmax_all_strong": 144,
    "sparsemax_all": 144,
    "sparsemax_top12": 12,
    "sparsemax_top24": 24,
    "sparsemax_top36": 36,
    "sparsemax_top24_strong": 24,
}

# Lambda map (for Figure 3)
LAMBDA_MAP = {
    "sparsemax_top24_lam01": 0.1,
    "sparsemax_top24_lam05": 0.5,
    "sparsemax_top24_lam10": 1.0,
    "sparsemax_top24_lam20": 2.0,
}


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


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all_results() -> pd.DataFrame:
    """Load every results.json into a DataFrame."""
    rows: list[dict[str, Any]] = []
    for rdir in sorted(RESULTS_DIR.iterdir()):
        rjson = rdir / "results.json"
        if not rjson.exists():
            continue
        # Parse condition name and seed from directory name
        name = rdir.name
        m = re.match(r"^(.+?)_s(\d+)$", name)
        if not m:
            continue
        condition, seed = m.group(1), int(m.group(2))
        with open(rjson) as f:
            data = json.load(f)
        tm = data.get("test_metrics", {})
        rows.append({
            "condition": condition,
            "seed": seed,
            "best_val_f1": data.get("best_val_f1", np.nan),
            "test_loss": data.get("test_loss", np.nan),
            "macro_f1": tm.get("macro_f1", np.nan),
            "accuracy": tm.get("accuracy", np.nan),
            "per_class_f1_0": tm.get("per_class_f1", [np.nan])[0],
            "per_class_f1_1": tm.get("per_class_f1", [np.nan, np.nan])[1],
            "per_class_f1_2": tm.get("per_class_f1", [np.nan, np.nan, np.nan])[2],
        })
    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} result files across {df['condition'].nunique()} conditions.")
    return df


def load_head_importance() -> dict[str, Any]:
    """Load head importance data."""
    path = RESULTS_DIR / "head_importance" / "head_importance.json"
    with open(path) as f:
        return json.load(f)


def load_training_history(condition_seed: str) -> list[dict]:
    """Load training_history.json for a given condition_seed directory name."""
    path = RESULTS_DIR / condition_seed / "training_history.json"
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def make_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create mean +/- std summary table across seeds."""
    metrics = ["macro_f1", "accuracy", "per_class_f1_0", "per_class_f1_1", "per_class_f1_2"]
    rows = []
    for cat_name, conditions in CONDITION_CATEGORIES.items():
        for cond in conditions:
            sub = df[df["condition"] == cond]
            if sub.empty:
                continue
            row: dict[str, Any] = {"category": cat_name, "condition": DISPLAY_NAMES.get(cond, cond)}
            for m in metrics:
                vals = sub[m].dropna()
                if len(vals) > 0:
                    row[f"{m}_mean"] = vals.mean()
                    row[f"{m}_std"] = vals.std()
                    row[f"{m}_str"] = f"{vals.mean():.4f} ± {vals.std():.4f}"
                else:
                    row[f"{m}_str"] = "N/A"
            rows.append(row)
    summary = pd.DataFrame(rows)
    return summary


# ---------------------------------------------------------------------------
# Bootstrap significance tests
# ---------------------------------------------------------------------------

def paired_bootstrap_test(
    values_a: np.ndarray,
    values_b: np.ndarray,
    n_bootstrap: int = 10000,
    rng_seed: int = 0,
) -> float:
    """Paired bootstrap test: H0: mean(a) == mean(b).

    Returns p-value (two-sided).  When we have only 3 seeds, the bootstrap
    over the seed-level aggregates gives a conservative but principled test.
    """
    rng = np.random.RandomState(rng_seed)
    n = len(values_a)
    observed_diff = np.mean(values_b) - np.mean(values_a)
    diffs = values_b - values_a
    centered = diffs - diffs.mean()  # center under H0
    count = 0
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        boot_diff = np.mean(centered[idx])
        if abs(boot_diff) >= abs(observed_diff):
            count += 1
    return count / n_bootstrap


def run_significance_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Run paired bootstrap tests comparing each condition to vanilla."""
    vanilla = df[df["condition"] == "vanilla"].sort_values("seed")["macro_f1"].values
    rows = []
    for cat_name, conditions in CONDITION_CATEGORIES.items():
        for cond in conditions:
            if cond == "vanilla":
                continue
            sub = df[df["condition"] == cond].sort_values("seed")["macro_f1"].values
            if len(sub) != len(vanilla):
                continue
            p = paired_bootstrap_test(vanilla, sub)
            diff = sub.mean() - vanilla.mean()
            sig = ""
            if p < 0.01:
                sig = "**"
            elif p < 0.05:
                sig = "*"
            rows.append({
                "condition": DISPLAY_NAMES.get(cond, cond),
                "mean_diff": diff,
                "p_value": p,
                "significance": sig,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _save(fig: plt.Figure, name: str) -> None:
    """Save figure as both PNG and PDF."""
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {name}.png and {name}.pdf")


def figure1_bar_chart(df: pd.DataFrame, sig_df: pd.DataFrame) -> None:
    """Bar chart comparing macro-F1 across all conditions with error bars."""
    print("Figure 1: Macro-F1 bar chart ...")

    # Build ordered list of conditions
    ordered_conditions: list[str] = []
    category_labels: list[str] = []
    for cat, conds in CONDITION_CATEGORIES.items():
        for c in conds:
            if c in df["condition"].values:
                ordered_conditions.append(c)
                category_labels.append(cat)

    means, stds, colors, display = [], [], [], []
    cat_colors = {
        "Baselines": CB_PALETTE["blue"],
        "Sparsemax": CB_PALETTE["orange"],
        "Sparsemax (strong)": CB_PALETTE["red"],
        "Lambda ablation": CB_PALETTE["green"],
    }

    sig_map = {}
    for _, row in sig_df.iterrows():
        sig_map[row["condition"]] = row["significance"]

    for cond, cat in zip(ordered_conditions, category_labels):
        sub = df[df["condition"] == cond]["macro_f1"]
        means.append(sub.mean())
        stds.append(sub.std())
        colors.append(cat_colors.get(cat, CB_PALETTE["black"]))
        display.append(DISPLAY_NAMES.get(cond, cond))

    x = np.arange(len(means))
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(x, means, yerr=stds, capsize=3, color=colors, edgecolor="white",
                  linewidth=0.5, width=0.7, error_kw={"linewidth": 1})

    # Significance markers
    for i, label in enumerate(display):
        sig = sig_map.get(label, "")
        if sig:
            ax.text(i, means[i] + stds[i] + 0.003, sig, ha="center", va="bottom",
                    fontsize=12, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(display, rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("Macro-F1")
    ax.set_title("Test Macro-F1 Across Conditions (mean ± std over 3 seeds)")
    ax.set_ylim(bottom=min(means) - 0.05, top=max(means) + max(stds) + 0.02)

    # Category legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=cat_colors[c], label=c) for c in cat_colors if c in set(category_labels)]
    ax.legend(handles=legend_elements, loc="lower right", frameon=False)

    fig.tight_layout()
    _save(fig, "fig1_macro_f1_bar")


def figure2_accuracy_vs_heads(df: pd.DataFrame) -> None:
    """Accuracy vs number of supervised heads trade-off."""
    print("Figure 2: Accuracy vs supervised heads ...")

    fig, ax = plt.subplots(figsize=(7, 5))

    for transform, marker, color, label_prefix in [
        ("softmax", "s", CB_PALETTE["blue"], "Softmax"),
        ("sparsemax", "o", CB_PALETTE["orange"], "Sparsemax"),
    ]:
        # Gather conditions for this transform type
        points: dict[int, list[float]] = {}
        for cond, n_heads in HEADS_MAP.items():
            if transform == "softmax" and not (cond.startswith("softmax") or cond == "vanilla"):
                continue
            if transform == "sparsemax" and not (cond.startswith("sparsemax") or cond == "vanilla"):
                continue
            # Skip lambda ablations and strong variants for clarity
            if "lam" in cond or "strong" in cond:
                continue
            sub = df[df["condition"] == cond]["macro_f1"].values
            if len(sub) == 0:
                continue
            points.setdefault(n_heads, []).extend(sub.tolist())

        xs = sorted(points.keys())
        ymeans = [np.mean(points[x]) for x in xs]
        ystds = [np.std(points[x]) for x in xs]

        ax.errorbar(xs, ymeans, yerr=ystds, marker=marker, color=color,
                    label=label_prefix, capsize=4, linewidth=2, markersize=7)
        # Error band
        ax.fill_between(xs,
                        np.array(ymeans) - np.array(ystds),
                        np.array(ymeans) + np.array(ystds),
                        alpha=0.15, color=color)

    ax.set_xlabel("Number of Supervised Heads")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Macro-F1 vs. Number of Supervised Attention Heads")
    ax.set_xticks([0, 12, 24, 36, 144])
    ax.legend(frameon=False)
    fig.tight_layout()
    _save(fig, "fig2_heads_tradeoff")


def figure3_lambda_ablation(df: pd.DataFrame) -> None:
    """Lambda ablation curve for sparsemax_top24."""
    print("Figure 3: Lambda ablation ...")

    lambdas, means, stds = [], [], []
    for cond, lam in sorted(LAMBDA_MAP.items(), key=lambda x: x[1]):
        sub = df[df["condition"] == cond]["macro_f1"]
        if sub.empty:
            continue
        lambdas.append(lam)
        means.append(sub.mean())
        stds.append(sub.std())

    means = np.array(means)
    stds = np.array(stds)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.errorbar(lambdas, means, yerr=stds, marker="o", color=CB_PALETTE["orange"],
                capsize=4, linewidth=2, markersize=8)
    ax.fill_between(lambdas, means - stds, means + stds,
                    alpha=0.15, color=CB_PALETTE["orange"])
    ax.set_xlabel("Attention Loss Weight (λ)")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Lambda Ablation — Sparsemax (top-24)")
    ax.set_xticks(lambdas)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    fig.tight_layout()
    _save(fig, "fig3_lambda_ablation")


def figure4_head_importance(hi_data: dict) -> None:
    """Head importance heatmap with top-24 heads highlighted."""
    print("Figure 4: Head importance heatmap ...")

    matrix = np.array(hi_data["head_importance"])  # 12x12
    top24 = set(tuple(x) for x in hi_data["top_24"])

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(matrix, ax=ax, cmap="YlOrRd", linewidths=0.3, linecolor="white",
                xticklabels=range(1, 13), yticklabels=range(1, 13),
                cbar_kws={"label": "Importance Score"})

    # Highlight top-24 with border
    for (layer, head) in top24:
        ax.add_patch(plt.Rectangle((head, layer), 1, 1, fill=False,
                                   edgecolor=CB_PALETTE["blue"], linewidth=2))

    ax.set_xlabel("Head")
    ax.set_ylabel("Layer")
    ax.set_title("Attention Head Importance (top-24 highlighted)")
    fig.tight_layout()
    _save(fig, "fig4_head_importance")


def figure5_training_curves() -> None:
    """Training curves for vanilla, softmax_all, sparsemax_all (seed 42)."""
    print("Figure 5: Training curves ...")

    conditions = {
        "vanilla_s42": ("Vanilla", CB_PALETTE["black"], "--"),
        "softmax_all_s42": ("Softmax (all)", CB_PALETTE["blue"], "-"),
        "sparsemax_all_s42": ("Sparsemax (all)", CB_PALETTE["orange"], "-"),
    }

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax_loss, ax_f1 = axes

    for cond_seed, (label, color, ls) in conditions.items():
        try:
            history = load_training_history(cond_seed)
        except FileNotFoundError:
            print(f"  Warning: {cond_seed}/training_history.json not found, skipping")
            continue
        epochs = [h["epoch"] for h in history]
        train_loss = [h["train_loss"] for h in history]
        val_f1 = [h["val_macro_f1"] for h in history]

        ax_loss.plot(epochs, train_loss, color=color, linestyle=ls, linewidth=2, label=label)
        ax_f1.plot(epochs, val_f1, color=color, linestyle=ls, linewidth=2, label=label)

    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("Train Loss")
    ax_loss.set_title("Training Loss")
    ax_loss.legend(frameon=False)

    ax_f1.set_xlabel("Epoch")
    ax_f1.set_ylabel("Val Macro-F1")
    ax_f1.set_title("Validation Macro-F1")
    ax_f1.legend(frameon=False)

    fig.tight_layout()
    _save(fig, "fig5_training_curves")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _apply_style()

    # 1. Load data
    df = load_all_results()
    if df.empty:
        print("ERROR: No results found.", file=sys.stderr)
        sys.exit(1)

    # 2. Summary table
    print("\n=== Summary Table ===")
    summary = make_summary_table(df)
    cols_show = ["category", "condition", "macro_f1_str", "accuracy_str",
                 "per_class_f1_0_str", "per_class_f1_1_str", "per_class_f1_2_str"]
    cols_show = [c for c in cols_show if c in summary.columns]
    print(summary[cols_show].to_string(index=False))

    # 3. Significance tests
    print("\n=== Paired Bootstrap Tests vs. Vanilla ===")
    sig_df = run_significance_tests(df)
    if not sig_df.empty:
        print(sig_df.to_string(index=False))
    else:
        print("No significance tests could be run.")

    # 4. Figures
    print("\n=== Generating Figures ===")
    figure1_bar_chart(df, sig_df)
    figure2_accuracy_vs_heads(df)
    figure3_lambda_ablation(df)

    try:
        hi_data = load_head_importance()
        figure4_head_importance(hi_data)
    except FileNotFoundError:
        print("  Warning: head_importance.json not found, skipping Figure 4")

    figure5_training_curves()

    print(f"\nAll figures saved to {FIGURES_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
