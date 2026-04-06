"""Phase 0 data analysis: annotator agreement statistics for HateXplain.

Computes Fleiss' kappa for label agreement and per-example rationale consistency.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

LABEL_MAP = {"hatespeech": 0, "offensive": 1, "normal": 2}
LABEL_NAMES = ["hatespeech", "offensive", "normal"]
N_LABELS = 3

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "hatexplain"


def fleiss_kappa(ratings_matrix: np.ndarray) -> float:
    """Compute Fleiss' kappa for a ratings matrix.

    Args:
        ratings_matrix: Array of shape (N_subjects, N_categories) where each
            row sums to the number of raters per subject.

    Returns:
        Fleiss' kappa in [-1, 1]. > 0.6 = substantial agreement.
    """
    n_subjects, n_categories = ratings_matrix.shape
    n_raters = int(ratings_matrix[0].sum())

    # Proportion of rater pairs who agreed per subject
    p_i = (
        (ratings_matrix ** 2).sum(axis=1) - n_raters
    ) / (n_raters * (n_raters - 1))
    p_bar = p_i.mean()

    # Proportion of assignments to each category
    p_j = ratings_matrix.sum(axis=0) / (n_subjects * n_raters)

    # Expected agreement by chance
    p_e_bar = (p_j ** 2).sum()

    if p_e_bar == 1.0:
        return 1.0
    kappa = (p_bar - p_e_bar) / (1 - p_e_bar)
    return float(kappa)


def compute_annotator_agreement(
    output_path: str | Path | None = None,
    data_dir: Path | None = None,
) -> dict:
    """Compute annotator agreement statistics for the HateXplain train split.

    Args:
        output_path: Optional path to write JSON summary.

    Returns:
        Dict with agreement statistics:
          - label_kappa: Fleiss' kappa for class label agreement
          - mean_rationale_overlap: mean fraction of annotators agreeing on each token
          - pct_unanimous_label: fraction of examples with unanimous label
    """
    data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    divisions = json.loads((data_dir / "post_id_divisions.json").read_text())
    all_data = json.loads((data_dir / "dataset.json").read_text())
    train_ids = set(divisions["train"])
    raw = [v for k, v in all_data.items() if k in train_ids]

    label_ratings = []
    rationale_overlaps = []
    unanimous = 0

    for ex in raw:
        # Raw JSON: annotators is a list of dicts with "label" key
        annotators = ex["annotators"]
        annotator_labels = [a["label"] for a in annotators]
        n_annotators = len(annotator_labels)

        # Build ratings vector for this example
        counts = [0] * N_LABELS
        for lbl in annotator_labels:
            lbl_str = lbl if isinstance(lbl, str) else LABEL_NAMES[int(lbl)]
            counts[LABEL_MAP[lbl_str]] += 1
        label_ratings.append(counts)

        if max(counts) == n_annotators:
            unanimous += 1

        # Rationale overlap: for each token, fraction of annotators who marked it
        rationales = ex["rationales"]
        n_tokens = len(ex["post_tokens"])
        valid = [r for r in rationales if len(r) == n_tokens]
        if valid:
            per_token = [
                sum(r[i] for r in valid) / len(valid)
                for i in range(n_tokens)
            ]
            # Mean overlap across tokens that at least one annotator marked
            marked = [p for p in per_token if p > 0]
            if marked:
                rationale_overlaps.append(np.mean(marked))

    ratings_matrix = np.array(label_ratings, dtype=float)
    kappa = fleiss_kappa(ratings_matrix)
    mean_overlap = float(np.mean(rationale_overlaps)) if rationale_overlaps else 0.0
    pct_unanimous = unanimous / max(len(label_ratings), 1)

    stats = {
        "n_examples": len(label_ratings),
        "label_kappa": kappa,
        "label_kappa_interpretation": _kappa_label(kappa),
        "mean_rationale_overlap": mean_overlap,
        "pct_unanimous_label": pct_unanimous,
    }

    logger.info(
        f"Annotator agreement: κ={kappa:.3f} ({_kappa_label(kappa)}), "
        f"mean_rationale_overlap={mean_overlap:.3f}, "
        f"unanimous_label={pct_unanimous:.1%}"
    )

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved annotator agreement to {path}")

    return stats


def _kappa_label(kappa: float) -> str:
    if kappa < 0:
        return "poor"
    if kappa < 0.2:
        return "slight"
    if kappa < 0.4:
        return "fair"
    if kappa < 0.6:
        return "moderate"
    if kappa < 0.8:
        return "substantial"
    return "almost_perfect"
