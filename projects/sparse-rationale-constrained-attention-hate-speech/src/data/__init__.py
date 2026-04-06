"""Data module: HateXplain dataset and tokenization utilities."""
from .dataset import HateXplainDataset, collate_fn
from .preprocessing import normalize_rationale, tokenize_with_rationale_alignment

__all__ = [
    "HateXplainDataset",
    "collate_fn",
    "tokenize_with_rationale_alignment",
    "normalize_rationale",
]
