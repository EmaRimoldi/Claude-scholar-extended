"""Evaluation module: plausibility, faithfulness, attribution, and statistics."""
from .attribution import (
    compute_ig_attributions,
    compute_ig_batch,
    compute_ig_lime_agreement,
    compute_lime_attributions,
    compute_lime_stability,
)
from .faithfulness import compute_faithfulness_metrics, mask_tokens
from .plausibility import (
    attention_to_binary_mask,
    compute_plausibility_metrics,
    iou_f1,
    token_f1,
)
from .statistics import (
    bootstrap_ci,
    bootstrap_paired_ci,
    cohens_d,
    compare_conditions,
    post_hoc_power,
)

__all__ = [
    "iou_f1",
    "token_f1",
    "attention_to_binary_mask",
    "compute_plausibility_metrics",
    "mask_tokens",
    "compute_faithfulness_metrics",
    "compute_ig_attributions",
    "compute_ig_batch",
    "compute_lime_attributions",
    "compute_lime_stability",
    "compute_ig_lime_agreement",
    "bootstrap_ci",
    "bootstrap_paired_ci",
    "cohens_d",
    "compare_conditions",
    "post_hoc_power",
]
