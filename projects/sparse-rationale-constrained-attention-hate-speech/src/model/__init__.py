"""Model module: sparsemax activation and BERT classifier."""
from .bert_sparse import (
    SparseBertConfig,
    SparseBertForSequenceClassification,
    inject_sparsemax_attention,
)
from .sparsemax import Sparsemax, sparsemax, sparsemax_loss

__all__ = [
    "Sparsemax",
    "sparsemax",
    "sparsemax_loss",
    "SparseBertConfig",
    "SparseBertForSequenceClassification",
    "inject_sparsemax_attention",
]
