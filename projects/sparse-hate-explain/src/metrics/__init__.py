"""Metrics for hate speech explanation evaluation."""

from .classification import compute_classification_metrics
from .faithfulness import (
    compute_attention_ig_correlation,
    compute_comprehensiveness,
    compute_sufficiency,
)
from .plausibility import compute_plausibility_metrics

__all__ = [
    "compute_classification_metrics",
    "compute_attention_ig_correlation",
    "compute_comprehensiveness",
    "compute_sufficiency",
    "compute_plausibility_metrics",
]
