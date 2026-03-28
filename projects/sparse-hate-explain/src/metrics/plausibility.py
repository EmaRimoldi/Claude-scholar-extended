"""Plausibility metrics: token-level F1, AUPRC, attention entropy, sparsity."""

from __future__ import annotations

from typing import Dict, Union

import numpy as np
from sklearn.metrics import auc, f1_score, precision_recall_curve


def compute_plausibility_metrics(
    attention_weights: Union[np.ndarray, "torch.Tensor"],
    rationale_masks: Union[np.ndarray, "torch.Tensor"],
    attention_masks: Union[np.ndarray, "torch.Tensor"],
    threshold: float = 0.5,
) -> Dict[str, float]:
    """Compute plausibility metrics comparing attention to human rationales.

    All inputs have shape (N, seq_len) where N is the number of samples.

    Args:
        attention_weights: Model attention weights (float, 0-1).
        rationale_masks: Binary human rationale annotations.
        attention_masks: Binary masks indicating non-padding positions.
        threshold: Threshold for binarising attention_weights into
            predicted rationale tokens.

    Returns:
        Dict with: token_f1, auprc, attention_entropy, sparsity_ratio.
    """
    # Ensure numpy arrays
    if not isinstance(attention_weights, np.ndarray):
        attention_weights = attention_weights.detach().cpu().numpy()
    if not isinstance(rationale_masks, np.ndarray):
        rationale_masks = rationale_masks.detach().cpu().numpy()
    if not isinstance(attention_masks, np.ndarray):
        attention_masks = attention_masks.detach().cpu().numpy()

    attention_weights = attention_weights.astype(np.float64)
    rationale_masks = rationale_masks.astype(np.float64)
    attention_masks = attention_masks.astype(np.float64)

    # Flatten to valid (non-padding) tokens only
    valid = attention_masks.flatten().astype(bool)
    attn_flat = attention_weights.flatten()[valid]
    rat_flat = rationale_masks.flatten()[valid]

    # --- Token-level F1 ---
    pred_binary = (attn_flat >= threshold).astype(int)
    gt_binary = rat_flat.astype(int)
    token_f1 = float(f1_score(gt_binary, pred_binary, zero_division=0.0))

    # --- AUPRC ---
    if gt_binary.sum() > 0:
        precision, recall, _ = precision_recall_curve(gt_binary, attn_flat)
        auprc = float(auc(recall, precision))
    else:
        auprc = 0.0

    # --- Attention entropy (per sample, then average) ---
    entropies: list[float] = []
    for i in range(attention_weights.shape[0]):
        mask_i = attention_masks[i].astype(bool)
        w = attention_weights[i][mask_i]
        # Normalise to distribution
        w_sum = w.sum()
        if w_sum > 0:
            p = w / w_sum
        else:
            p = np.ones_like(w) / len(w)
        # Clip to avoid log(0)
        p = np.clip(p, 1e-12, None)
        entropy = -float(np.sum(p * np.log(p)))
        entropies.append(entropy)
    attention_entropy = float(np.mean(entropies)) if entropies else 0.0

    # --- Sparsity ratio (fraction of attention weights exactly 0) ---
    sparsity_ratio = float((attn_flat == 0.0).sum() / len(attn_flat)) if len(attn_flat) > 0 else 0.0

    return {
        "token_f1": token_f1,
        "auprc": auprc,
        "attention_entropy": attention_entropy,
        "sparsity_ratio": sparsity_ratio,
    }
