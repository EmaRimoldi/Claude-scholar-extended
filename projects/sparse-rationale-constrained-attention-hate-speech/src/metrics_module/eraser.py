"""ERASER faithfulness metrics: comprehensiveness and sufficiency AOPC.

Reference: DeYoung et al., "ERASER: A Benchmark to Evaluate Rationalized NLP
Models", ACL 2020. https://arxiv.org/abs/1911.03429

Comprehensiveness: How much does prediction change when top-k% attention
tokens are *removed*? Higher = more faithful (model depended on those tokens).

Sufficiency: How much of the prediction is preserved when only top-k% tokens
are *retained*? Higher = sufficient explanation.

AOPC (Area Over the Perturbation Curve) aggregates across perturbation levels
k ∈ {0.1, 0.2, 0.3, 0.5, 0.8}.
"""
import logging
from typing import Callable

import torch
import torch.nn.functional as F
from torch import Tensor

logger = logging.getLogger(__name__)

AOPC_LEVELS = [0.1, 0.2, 0.3, 0.5, 0.8]


def compute_comprehensiveness_aopc(
    model_fn: Callable[[Tensor, Tensor], Tensor],
    input_ids: Tensor,
    attention_mask: Tensor,
    cls_attention_weights: Tensor,
    levels: list[float] = AOPC_LEVELS,
) -> float:
    """Compute AOPC comprehensiveness score.

    Deletes the top-k% tokens by descending attention weight; measures how
    much the output probability of the predicted class changes.

    Args:
        model_fn: Callable(input_ids, attention_mask) -> logits (B, C).
        input_ids: Original token ids, shape (B, T).
        attention_mask: Original padding mask, shape (B, T).
        cls_attention_weights: CLS attention over tokens, shape (B, T).
            Tokens with higher weight are considered more important.
        levels: List of deletion fractions in (0, 1).

    Returns:
        Scalar AOPC comprehensiveness (mean over levels and batch).
    """
    with torch.no_grad():
        orig_logits = model_fn(input_ids, attention_mask)
        orig_probs = F.softmax(orig_logits, dim=-1)
        pred_class = orig_probs.argmax(dim=-1)
        orig_pred_probs = orig_probs.gather(1, pred_class.unsqueeze(1)).squeeze(1)  # (B,)

    level_scores = []
    for level in levels:
        masked_attention = _mask_top_k(attention_mask, cls_attention_weights, level)
        with torch.no_grad():
            perturbed_logits = model_fn(input_ids, masked_attention)
            perturbed_probs = F.softmax(perturbed_logits, dim=-1)
            perturbed_pred_probs = perturbed_probs.gather(
                1, pred_class.unsqueeze(1)
            ).squeeze(1)
        # Drop = original - perturbed (positive when model depended on deleted tokens)
        level_drop = (orig_pred_probs - perturbed_pred_probs).mean().item()
        level_scores.append(level_drop)

    return sum(level_scores) / len(level_scores)


def compute_sufficiency_aopc(
    model_fn: Callable[[Tensor, Tensor], Tensor],
    input_ids: Tensor,
    attention_mask: Tensor,
    cls_attention_weights: Tensor,
    levels: list[float] = AOPC_LEVELS,
) -> float:
    """Compute AOPC sufficiency score.

    Retains only the top-k% tokens by descending attention weight; measures
    how much of the predicted-class probability is preserved.

    Args:
        model_fn: Callable(input_ids, attention_mask) -> logits (B, C).
        input_ids: Original token ids, shape (B, T).
        attention_mask: Original padding mask, shape (B, T).
        cls_attention_weights: CLS attention over tokens, shape (B, T).
        levels: List of retention fractions in (0, 1).

    Returns:
        Scalar AOPC sufficiency (mean over levels and batch).
    """
    with torch.no_grad():
        orig_logits = model_fn(input_ids, attention_mask)
        orig_probs = F.softmax(orig_logits, dim=-1)
        pred_class = orig_probs.argmax(dim=-1)
        orig_pred_probs = orig_probs.gather(1, pred_class.unsqueeze(1)).squeeze(1)

    level_scores = []
    for level in levels:
        kept_attention = _retain_top_k(attention_mask, cls_attention_weights, level)
        with torch.no_grad():
            perturbed_logits = model_fn(input_ids, kept_attention)
            perturbed_probs = F.softmax(perturbed_logits, dim=-1)
            perturbed_pred_probs = perturbed_probs.gather(
                1, pred_class.unsqueeze(1)
            ).squeeze(1)
        # Gap = original - retained (lower = more sufficient)
        level_gap = (orig_pred_probs - perturbed_pred_probs).mean().item()
        level_scores.append(level_gap)

    # Sufficiency AOPC: lower gap = more sufficient
    # Return as positive score: 1 - mean_gap would scale it, but ERASER reports gap directly
    return sum(level_scores) / len(level_scores)


def _mask_top_k(
    attention_mask: Tensor,
    weights: Tensor,
    level: float,
) -> Tensor:
    """Create attention mask with top-k% highest-weight tokens masked out (set to 0).

    Args:
        attention_mask: Original padding mask (B, T), 1=real token, 0=padding.
        weights: Token importance weights (B, T), higher = more important.
        level: Fraction of real tokens to remove in (0, 1).

    Returns:
        Modified attention mask with top-k% tokens zeroed out.
    """
    B, T = attention_mask.shape
    new_mask = attention_mask.clone().float()

    for b in range(B):
        real_count = attention_mask[b].sum().item()
        k = max(1, int(real_count * level))
        # Only consider real tokens (not padding) for ranking
        masked_weights = weights[b] * attention_mask[b].float()
        _, top_indices = torch.topk(masked_weights, k=k)
        new_mask[b, top_indices] = 0.0

    return new_mask.long()


def _retain_top_k(
    attention_mask: Tensor,
    weights: Tensor,
    level: float,
) -> Tensor:
    """Create attention mask retaining only top-k% highest-weight tokens.

    Args:
        attention_mask: Original padding mask (B, T).
        weights: Token importance weights (B, T).
        level: Fraction of real tokens to retain in (0, 1).

    Returns:
        Modified attention mask with only top-k% tokens active.
    """
    B, T = attention_mask.shape
    new_mask = torch.zeros_like(attention_mask).float()

    for b in range(B):
        real_count = attention_mask[b].sum().item()
        k = max(1, int(real_count * level))
        masked_weights = weights[b] * attention_mask[b].float()
        _, top_indices = torch.topk(masked_weights, k=k)
        new_mask[b, top_indices] = 1.0

    return new_mask.long()


def compute_plausibility_metrics(
    cls_attention_weights: Tensor,
    rationale_binary: Tensor,
    attention_mask: Tensor,
) -> dict[str, float]:
    """Compute token-level plausibility: IoU F1, Token Precision, Recall, F1.

    Args:
        cls_attention_weights: CLS attention over tokens, shape (B, T).
        rationale_binary: Binary gold rationale mask, shape (B, T).
        attention_mask: Padding mask, shape (B, T).

    Returns:
        Dict with keys: iou_f1, token_precision, token_recall, token_f1.
    """
    # Binarize attention: top-25% of real tokens (approx HateXplain density)
    B, T = cls_attention_weights.shape
    pred_binary = torch.zeros_like(cls_attention_weights)

    for b in range(B):
        real_count = attention_mask[b].sum().item()
        k = max(1, int(real_count * 0.25))
        masked_w = cls_attention_weights[b] * attention_mask[b].float()
        _, top_indices = torch.topk(masked_w, k=k)
        pred_binary[b, top_indices] = 1.0

    # Compute over non-padding tokens only
    real = attention_mask.float()
    tp = ((pred_binary * rationale_binary.float()) * real).sum().item()
    pred_pos = (pred_binary * real).sum().item()
    gold_pos = (rationale_binary.float() * real).sum().item()

    precision = tp / max(pred_pos, 1e-8)
    recall = tp / max(gold_pos, 1e-8)
    token_f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    intersection = tp
    union = pred_pos + gold_pos - tp
    iou_f1 = intersection / max(union, 1e-8)

    return {
        "iou_f1": iou_f1,
        "token_precision": precision,
        "token_recall": recall,
        "token_f1": token_f1,
    }
