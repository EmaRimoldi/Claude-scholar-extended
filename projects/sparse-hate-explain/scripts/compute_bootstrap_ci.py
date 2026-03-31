#!/usr/bin/env python3
"""
compute_bootstrap_ci.py — Bootstrap confidence intervals and Bonferroni-
corrected pairwise significance tests for all experiment conditions.

Reads per-seed test_metrics.json files from results/<condition>/seed_*/,
pools macro_f1 (and optionally comprehensiveness, sufficiency) across seeds,
then computes:
  - Mean ± bootstrap 95% CI (10 000 resamples)
  - Pairwise two-sided permutation test vs. chosen baseline (default: vanilla)
  - Bonferroni-corrected p-values across all (n_conditions - 1) comparisons

Usage:
    python scripts/compute_bootstrap_ci.py \\
        --results-dir results/ \\
        --baseline vanilla \\
        --output results/bootstrap_ci.json \\
        --n-bootstrap 10000

Output: results/bootstrap_ci.json
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

METRICS = ["macro_f1", "comprehensiveness", "sufficiency", "accuracy"]
N_BOOTSTRAP_DEFAULT = 10_000
RNG_SEED = 0  # fixed for reproducibility of CI computation


def load_condition_scores(
    results_dir: Path,
    metric: str,
) -> Dict[str, List[float]]:
    """Scan results_dir for per-seed metric values.

    Expected layout:
        results_dir/<condition>/seed_<N>/test_metrics.json

    Returns {condition_name: [seed_score_1, seed_score_2, ...]}
    """
    condition_scores: Dict[str, List[float]] = {}
    for cond_dir in sorted(results_dir.iterdir()):
        if not cond_dir.is_dir():
            continue
        scores: List[float] = []
        for seed_dir in sorted(cond_dir.glob("seed_*")):
            metrics_path = seed_dir / "test_metrics.json"
            if not metrics_path.exists():
                continue
            with open(metrics_path) as fh:
                m = json.load(fh)
            val = m.get(metric)
            if val is not None:
                scores.append(float(val))
        if scores:
            condition_scores[cond_dir.name] = scores
    return condition_scores


def bootstrap_ci(
    scores: List[float],
    n_bootstrap: int,
    rng: np.random.Generator,
    ci: float = 0.95,
) -> Tuple[float, float, float]:
    """Return (mean, lower, upper) bootstrap CI."""
    arr = np.array(scores)
    means = np.array([
        rng.choice(arr, size=len(arr), replace=True).mean()
        for _ in range(n_bootstrap)
    ])
    alpha = (1 - ci) / 2
    lower = float(np.percentile(means, 100 * alpha))
    upper = float(np.percentile(means, 100 * (1 - alpha)))
    return float(arr.mean()), lower, upper


def permutation_test(
    a: List[float],
    b: List[float],
    n_permutations: int,
    rng: np.random.Generator,
) -> float:
    """Two-sided permutation test of H0: mean(a) == mean(b).

    Returns p-value.
    """
    arr_a = np.array(a)
    arr_b = np.array(b)
    observed = abs(arr_a.mean() - arr_b.mean())
    combined = np.concatenate([arr_a, arr_b])
    n_a = len(arr_a)
    count = 0
    for _ in range(n_permutations):
        perm = rng.permutation(combined)
        diff = abs(perm[:n_a].mean() - perm[n_a:].mean())
        if diff >= observed:
            count += 1
    return count / n_permutations


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Bootstrap CIs and significance tests")
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--baseline", default="vanilla",
                        help="Condition name to use as pairwise test baseline")
    parser.add_argument("--metric", default="macro_f1",
                        choices=METRICS, help="Primary metric")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP_DEFAULT)
    parser.add_argument("--n-permutations", type=int, default=10_000)
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    rng = np.random.default_rng(RNG_SEED)

    condition_scores = load_condition_scores(results_dir, args.metric)
    if not condition_scores:
        logger.error("No results found in %s", results_dir)
        return

    logger.info("Found %d conditions", len(condition_scores))

    baseline_scores: Optional[List[float]] = condition_scores.get(args.baseline)
    if baseline_scores is None:
        logger.warning("Baseline '%s' not found; skipping pairwise tests.", args.baseline)

    n_comparisons = len(condition_scores) - 1  # Bonferroni denominator

    results: Dict[str, dict] = {}
    for cond, scores in sorted(condition_scores.items()):
        mean, lo, hi = bootstrap_ci(scores, args.n_bootstrap, rng)
        entry: dict = {
            "n_seeds": len(scores),
            "mean": mean,
            "ci_95_lower": lo,
            "ci_95_upper": hi,
            "scores_per_seed": scores,
        }

        if baseline_scores is not None and cond != args.baseline:
            p_raw = permutation_test(
                scores, baseline_scores, args.n_permutations, rng
            )
            p_bonf = min(1.0, p_raw * n_comparisons)
            entry["p_vs_baseline_raw"] = p_raw
            entry["p_vs_baseline_bonferroni"] = p_bonf
            entry["significant_bonferroni"] = p_bonf < 0.05

        results[cond] = entry

    output = {
        "metric": args.metric,
        "baseline": args.baseline,
        "n_bootstrap": args.n_bootstrap,
        "n_permutations": args.n_permutations,
        "bonferroni_n_comparisons": n_comparisons,
        "conditions": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fh:
        json.dump(output, fh, indent=2)

    # Print summary table.
    print(f"\n{'Condition':<35} {'Mean':>8} {'95% CI':>20} {'p(Bonf)':>10} {'Sig':>5}")
    print("-" * 82)
    sorted_results = sorted(
        results.items(), key=lambda x: x[1]["mean"], reverse=True
    )
    for cond, data in sorted_results:
        p_str = f"{data.get('p_vs_baseline_bonferroni', float('nan')):.4f}"
        sig_str = "*" if data.get("significant_bonferroni", False) else ""
        ci_str = f"[{data['ci_95_lower']:.4f}, {data['ci_95_upper']:.4f}]"
        print(f"{cond:<35} {data['mean']:>8.4f} {ci_str:>20} {p_str:>10} {sig_str:>5}")

    logger.info("Results written to %s", output_path)


if __name__ == "__main__":
    main()
