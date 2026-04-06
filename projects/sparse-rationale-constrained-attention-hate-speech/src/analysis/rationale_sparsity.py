"""Phase 0 data analysis: rationale sparsity statistics for HateXplain.

Gate G0: median rationale coverage < 0.50 across HateXplain train set.
Coverage = fraction of tokens marked as rationale per example.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def compute_sparsity_stats(
    dataset,
    output_path: str | Path | None = None,
) -> dict:
    """Compute rationale coverage statistics over a HateXplainDataset split.

    Args:
        dataset: HateXplainDataset instance with include_rationale=True.
        output_path: Optional path to write JSON summary.

    Returns:
        Dict with sparsity statistics:
          - mean_coverage: average fraction of tokens with non-zero rationale
          - median_coverage: median coverage across examples
          - std_coverage: standard deviation
          - pct_zero_rationale: fraction of examples with no rationale (all zeros)
          - gate_g0_pass: bool, median_coverage < 0.50
    """
    coverages = []
    zero_rationale_count = 0

    for i in range(len(dataset)):
        item = dataset[i]
        if "rationale_mask" not in item:
            logger.warning(f"Example {i} missing rationale_mask; skipping.")
            continue

        rat = item["rationale_mask"]
        attn = item["attention_mask"]

        # Count only non-padding positions
        seq_len = int(attn.sum().item())
        rat_vals = rat[:seq_len].numpy()

        n_rationale = (rat_vals > 0).sum()
        coverage = n_rationale / max(seq_len, 1)
        coverages.append(coverage)

        if n_rationale == 0:
            zero_rationale_count += 1

    coverages = np.array(coverages)
    mean_cov = float(np.mean(coverages))
    median_cov = float(np.median(coverages))
    std_cov = float(np.std(coverages))
    pct_zero = zero_rationale_count / max(len(coverages), 1)
    gate_pass = median_cov < 0.50

    stats = {
        "n_examples": len(coverages),
        "mean_coverage": mean_cov,
        "median_coverage": median_cov,
        "std_coverage": std_cov,
        "pct_zero_rationale": pct_zero,
        "gate_g0_pass": gate_pass,
        "gate_g0_criterion": "median_coverage < 0.50",
    }

    logger.info(
        f"Rationale sparsity: median={median_cov:.3f}, mean={mean_cov:.3f}, "
        f"zero_rationale={pct_zero:.1%}, G0 PASS={gate_pass}"
    )

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved sparsity stats to {path}")

    return stats
