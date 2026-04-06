#!/usr/bin/env python3
"""Collect and aggregate results from all training runs.

Gathers metrics from all conditions/seeds into structured tables.
"""
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def collect_training_metrics(output_dir: Path) -> Dict[str, Any]:
    """Collect training metrics from all model outputs."""
    results = {}
    conditions = ["M0", "M1", "M3", "M4b", "M2", "M4a", "M4c", "M5", "M6", "M7"]
    seeds = [42, 43, 44]

    for condition in conditions:
        cond_results = []

        for seed in seeds:
            model_dir = output_dir / condition / f"seed{seed}"

            if not model_dir.exists():
                print(f"Warning: {model_dir} not found")
                continue

            # Try to find training metrics from trainer_state.json
            trainer_state_path = model_dir / "trainer_state.json"
            if trainer_state_path.exists():
                with open(trainer_state_path) as f:
                    trainer_state = json.load(f)

                # Extract final metrics
                best_metric = trainer_state.get("best_metric", None)
                metrics = {
                    "seed": seed,
                    "best_metric": best_metric,
                    "num_train_epochs": trainer_state.get("num_train_epochs"),
                }
                cond_results.append(metrics)

        if cond_results:
            results[condition] = cond_results

    return results


def create_summary_tables(metrics: Dict[str, List[Dict]]) -> Dict[str, pd.DataFrame]:
    """Create summary tables from collected metrics."""
    tables = {}

    # Table 1: Best metrics by condition and seed
    rows = []
    for condition, seeds_data in metrics.items():
        for data in seeds_data:
            rows.append({
                "Condition": condition,
                "Seed": data["seed"],
                "Best Metric": data["best_metric"],
            })

    if rows:
        df = pd.DataFrame(rows)
        tables["by_seed"] = df

        # Table 2: Aggregate statistics
        agg_rows = []
        for condition, seeds_data in metrics.items():
            values = [d["best_metric"] for d in seeds_data if d["best_metric"] is not None]
            if values:
                agg_rows.append({
                    "Condition": condition,
                    "Mean": np.mean(values),
                    "Std": np.std(values),
                    "Min": np.min(values),
                    "Max": np.max(values),
                })

        if agg_rows:
            tables["aggregated"] = pd.DataFrame(agg_rows)

    return tables


def main() -> None:
    """Collect and save results."""
    output_dir = Path("outputs")

    print("Collecting training metrics...")
    metrics = collect_training_metrics(output_dir)

    print("Creating summary tables...")
    tables = create_summary_tables(metrics)

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Save tables as CSV
    for name, df in tables.items():
        output_file = results_dir / f"metrics_{name}.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved: {output_file}")

    # Save JSON summary
    json_output = results_dir / "metrics_summary.json"
    with open(json_output, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"Saved: {json_output}")

    print("\nSummary:")
    for name, df in tables.items():
        print(f"\n{name}:")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
