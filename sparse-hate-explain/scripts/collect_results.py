#!/usr/bin/env python3
"""Collect results from all experiment runs into a summary table."""

import json
import sys
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(__file__).parent.parent / "results"


def collect_all_results() -> pd.DataFrame:
    rows = []
    for result_dir in sorted(RESULTS_DIR.iterdir()):
        results_file = result_dir / "results.json"
        if not results_file.exists():
            continue

        with open(results_file) as f:
            data = json.load(f)

        config = data.get("config", {})
        model_cfg = config.get("model", {})
        test_metrics = data.get("test_metrics", {})

        # Parse experiment name from directory
        name = result_dir.name
        parts = name.rsplit("_s", 1)
        condition = parts[0] if len(parts) == 2 else name
        seed = int(parts[1]) if len(parts) == 2 else 0

        row = {
            "condition": condition,
            "seed": seed,
            "attention_transform": model_cfg.get("attention_transform", ""),
            "supervised_heads": str(model_cfg.get("supervised_heads", "")),
            "lambda_attn": model_cfg.get("lambda_attn", 0.0),
            "top_k": model_cfg.get("top_k", ""),
            "macro_f1": test_metrics.get("macro_f1", None),
            "accuracy": test_metrics.get("accuracy", None),
            "per_class_f1": test_metrics.get("per_class_f1", []),
            "best_val_f1": data.get("best_val_f1", None),
            "test_loss": data.get("test_loss", None),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    agg = df.groupby("condition").agg(
        macro_f1_mean=("macro_f1", "mean"),
        macro_f1_std=("macro_f1", "std"),
        accuracy_mean=("accuracy", "mean"),
        accuracy_std=("accuracy", "std"),
        n_seeds=("seed", "count"),
    ).reset_index()
    return agg.sort_values("macro_f1_mean", ascending=False)


def main():
    df = collect_all_results()
    if df.empty:
        print("No results found yet.")
        sys.exit(0)

    print(f"Collected {len(df)} results from {df['condition'].nunique()} conditions")
    print()

    summary = summarize(df)
    print(summary.to_string(index=False, float_format="%.4f"))

    # Save
    df.to_csv(RESULTS_DIR / "all_results.csv", index=False)
    summary.to_csv(RESULTS_DIR / "summary.csv", index=False)
    print(f"\nSaved to {RESULTS_DIR}/all_results.csv and summary.csv")


if __name__ == "__main__":
    main()
