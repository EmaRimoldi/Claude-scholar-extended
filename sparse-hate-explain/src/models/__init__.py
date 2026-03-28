"""Model module for sparse attention hate speech detection."""

from .sparsemax import Sparsemax, sparsemax, sparsemax_transform
from .bert_sparse import BertSparseForClassification, BertSparseOutput
from .head_importance import (
    compute_head_importance,
    select_top_k_heads,
    select_top_k_per_layer,
)

__all__ = [
    # Sparsemax
    "Sparsemax",
    "sparsemax",
    "sparsemax_transform",
    # BERT with sparse attention
    "BertSparseForClassification",
    "BertSparseOutput",
    # Head importance
    "compute_head_importance",
    "select_top_k_heads",
    "select_top_k_per_layer",
]
