"""Classification metrics for hate speech detection."""

from __future__ import annotations

from typing import Any, Dict, List, Union

import numpy as np
from sklearn.metrics import accuracy_score, f1_score


def compute_classification_metrics(
    predictions: Union[List[int], np.ndarray],
    labels: Union[List[int], np.ndarray],
) -> Dict[str, Any]:
    """Compute classification metrics for hate speech detection.

    Args:
        predictions: Predicted class indices (N,).
        labels: Ground-truth class indices (N,).

    Returns:
        Dict with keys: macro_f1, per_class_f1, accuracy.
    """
    predictions = np.asarray(predictions)
    labels = np.asarray(labels)

    macro_f1: float = float(f1_score(labels, predictions, average="macro"))
    per_class_f1: List[float] = f1_score(
        labels, predictions, average=None
    ).tolist()
    accuracy: float = float(accuracy_score(labels, predictions))

    return {
        "macro_f1": macro_f1,
        "per_class_f1": per_class_f1,
        "accuracy": accuracy,
    }
