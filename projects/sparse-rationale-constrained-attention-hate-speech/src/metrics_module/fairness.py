"""Identity-term fairness evaluation (H5).

Measures false positive rate (FPR) on non-hate posts that contain identity terms,
testing whether sparsemax supervision reduces shortcut bias on minority mentions.

Reference: Chen et al., "Hate Speech Detection with Generalizable Target-aware
Fairness", KDD 2024. Protocol follows HateXplain identity-term subgroup analysis.
"""
import logging
from typing import Optional

import torch
from torch import Tensor

logger = logging.getLogger(__name__)

# Identity terms from HateXplain target community annotations
# Covers: race, religion, gender, sexual orientation, disability
IDENTITY_TERMS = {
    # Race/ethnicity
    "black", "white", "asian", "hispanic", "latino", "latina", "arab",
    "african", "jewish", "jew", "muslim", "islam", "christian",
    # Gender/sexuality
    "woman", "women", "man", "men", "female", "male", "gay", "lesbian",
    "trans", "transgender", "queer", "lgbt",
    # Disability
    "disabled", "disability",
}

HATE_LABEL = 2       # 'hatespeech'
OFFENSIVE_LABEL = 1  # 'offensive'
NORMAL_LABEL = 0     # 'normal'


def identify_identity_term_posts(
    texts: list[str],
    labels: list[int],
    identity_terms: Optional[set[str]] = None,
) -> list[int]:
    """Find indices of non-hate/non-offensive posts containing identity terms.

    Args:
        texts: List of post strings.
        labels: List of integer class labels.
        identity_terms: Set of identity term strings to search for.

    Returns:
        List of indices where post is NORMAL and contains ≥1 identity term.
    """
    if identity_terms is None:
        identity_terms = IDENTITY_TERMS

    indices = []
    for i, (text, label) in enumerate(zip(texts, labels)):
        if label != NORMAL_LABEL:
            continue
        text_lower = text.lower()
        if any(term in text_lower for term in identity_terms):
            indices.append(i)

    logger.info(f"Found {len(indices)} normal posts with identity terms.")
    return indices


def compute_identity_fpr(
    preds: Tensor,
    labels: Tensor,
    identity_mask: Tensor,
) -> dict[str, float]:
    """Compute FPR on identity-term normal posts.

    FPR = (normal posts with identity terms misclassified as hate or offensive)
          / (total normal posts with identity terms)

    Args:
        preds: Predicted class labels, shape (N,).
        labels: True class labels, shape (N,).
        identity_mask: Boolean mask of identity-term normal posts, shape (N,).

    Returns:
        Dict with fpr, total_identity_normal, misclassified_count.
    """
    # Filter to normal posts with identity terms
    normal_identity = identity_mask & (labels == NORMAL_LABEL)
    subset_preds = preds[normal_identity]
    total = normal_identity.sum().item()

    if total == 0:
        logger.warning("No normal identity-term posts found in evaluation set.")
        return {"fpr": 0.0, "total_identity_normal": 0, "misclassified": 0}

    # FP: predicted as hate or offensive when actually normal
    misclassified = ((subset_preds == HATE_LABEL) | (subset_preds == OFFENSIVE_LABEL)).sum().item()
    fpr = misclassified / total

    return {
        "fpr": fpr,
        "total_identity_normal": int(total),
        "misclassified": int(misclassified),
    }
