"""Plausibility metrics: IoU-F1 and Token-F1 vs. human rationale annotations.

Reference:
    Mathew et al. "HateXplain: A Benchmark Dataset for Explainable Hate Speech
    Detection." AAAI 2021.
    DeYoung et al. "ERASER: A Benchmark to Evaluate Rationalized NLP Models." ACL 2020.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score


def token_f1(
    pred_mask: list[int],
    gold_mask: list[int],
    ignore_special_tokens: bool = True,
) -> float:
    """Compute token-level F1 between predicted and gold rationale masks.

    Args:
        pred_mask: Binary list, 1 = predicted rationale token.
        gold_mask: Binary list, 1 = human-annotated rationale token.
        ignore_special_tokens: Whether to skip position 0 ([CLS]) and last ([SEP]).

    Returns:
        F1 score in [0, 1].
    """
    if ignore_special_tokens and len(pred_mask) > 2:
        pred_mask = pred_mask[1:-1]
        gold_mask = gold_mask[1:-1]

    if sum(gold_mask) == 0 and sum(pred_mask) == 0:
        return 1.0
    if sum(gold_mask) == 0 or sum(pred_mask) == 0:
        return 0.0

    return float(f1_score(gold_mask, pred_mask, zero_division=0))


def iou_f1(
    pred_mask: list[int],
    gold_mask: list[int],
    ignore_special_tokens: bool = True,
) -> float:
    """Compute Intersection over Union F1 (IoU-F1) between rationale masks.

    IoU = |intersection| / |union|
    This is equivalent to the Jaccard index and is commonly used in HateXplain
    evaluation (Mathew 2021).

    Args:
        pred_mask: Binary list of predicted rationale positions.
        gold_mask: Binary list of gold rationale positions.
        ignore_special_tokens: Skip [CLS] and [SEP] positions.

    Returns:
        IoU score in [0, 1].
    """
    if ignore_special_tokens and len(pred_mask) > 2:
        pred_mask = pred_mask[1:-1]
        gold_mask = gold_mask[1:-1]

    intersection = sum(p & g for p, g in zip(pred_mask, gold_mask))
    union = sum(p | g for p, g in zip(pred_mask, gold_mask))

    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return intersection / union


def attention_to_binary_mask(
    attention_weights: list[float] | np.ndarray,
    threshold: float = 0.0,
) -> list[int]:
    """Convert continuous attention weights to a binary rationale mask.

    For sparsemax: use threshold=0.0 (tokens with weight > 0 are in the rationale).
    For softmax: use a percentile-based threshold or fixed threshold.

    Args:
        attention_weights: Per-token attention weights (post-activation).
        threshold: Tokens with weight > threshold are marked as rationale.

    Returns:
        Binary list of same length as attention_weights.
    """
    return [1 if w > threshold else 0 for w in attention_weights]


def compute_plausibility_metrics(
    predicted_weights: list[list[float]],
    gold_masks: list[list[int]],
    threshold: float = 0.0,
) -> dict[str, float]:
    """Compute average IoU-F1 and Token-F1 over a dataset split.

    Args:
        predicted_weights: List of per-example attention weight lists.
            Each list has length = sequence length.
        gold_masks: List of per-example binary gold rationale masks.
        threshold: Binarization threshold for attention weights.

    Returns:
        Dict with keys "iou_f1" and "token_f1", values in [0, 1].
    """
    iou_scores = []
    tf1_scores = []

    for weights, gold in zip(predicted_weights, gold_masks):
        pred = attention_to_binary_mask(weights, threshold=threshold)
        # Trim both to same length
        min_len = min(len(pred), len(gold))
        pred = pred[:min_len]
        gold = gold[:min_len]

        iou_scores.append(iou_f1(pred, gold, ignore_special_tokens=False))
        tf1_scores.append(token_f1(pred, gold, ignore_special_tokens=False))

    return {
        "iou_f1": float(np.mean(iou_scores)),
        "token_f1": float(np.mean(tf1_scores)),
    }
