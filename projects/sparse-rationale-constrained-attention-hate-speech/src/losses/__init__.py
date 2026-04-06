"""Losses module: alignment loss functions for rationale supervision."""
from .alignment import (
    ALIGNMENT_LOSS_REGISTRY,
    KLAlignmentLoss,
    MSEAlignmentLoss,
    SparsemaxAlignmentLoss,
    build_alignment_loss,
)

__all__ = [
    "MSEAlignmentLoss",
    "KLAlignmentLoss",
    "SparsemaxAlignmentLoss",
    "build_alignment_loss",
    "ALIGNMENT_LOSS_REGISTRY",
]
