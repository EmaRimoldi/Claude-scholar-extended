"""Gradient-based attention head importance scoring (Michel et al. 2019).

Reference:
    Michel et al. "Are Sixteen Heads Really Better than One?" NeurIPS 2019.
    Importance formula: I(h,l) = E_x[ |∂L_CE / ∂A^{CLS,h,l}| ]

We use CLS-token attention (row 0 of the attention matrix) as our target
because downstream classification uses the CLS representation.
"""
from __future__ import annotations

import logging
from pathlib import Path

import torch
import torch.nn as nn
from torch import Tensor
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


def compute_head_importance(
    model: nn.Module,
    dataloader: DataLoader,
    num_layers: int = 12,
    num_heads: int = 12,
    device: str = "cuda",
    max_batches: int = 200,
) -> Tensor:
    """Compute gradient-based head importance scores over a data split.

    Computes E_x[|∂L_CE/∂A^{CLS,h,l}|] for each (layer, head) pair.
    The gradient is taken with respect to attention weights (post-softmax).

    Args:
        model: SparseBertForSequenceClassification (must return attentions).
        dataloader: DataLoader over the training set (shuffle=True recommended).
        num_layers: Number of transformer layers (12 for bert-base-uncased).
        num_heads: Number of attention heads per layer.
        device: Compute device.
        max_batches: Number of batches to use for the expectation estimate.

    Returns:
        Importance tensor of shape (num_layers, num_heads). Higher = more important.
    """
    model.eval()
    model = model.to(device)

    importance_sum = torch.zeros(num_layers, num_heads, device=device)
    n_samples = 0

    for batch_idx, batch in enumerate(dataloader):
        if batch_idx >= max_batches:
            break

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        token_type_ids = batch.get("token_type_ids", None)
        if token_type_ids is not None:
            token_type_ids = token_type_ids.to(device)
        labels = batch["labels"].to(device)

        # Enable gradients on attention weights.
        # retain_grad() must be called on each attention tensor before backward
        # so that .grad is populated (attention weights are non-leaf tensors).
        model.zero_grad()

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            labels=labels,
            output_attentions=True,
        )
        for attn in outputs.attentions:
            attn.retain_grad()
        loss = outputs.loss
        loss.backward()

        # Extract |∂L/∂A^{CLS,h,l}| for each head
        # outputs.attentions: tuple of (B, H, L, L) per layer
        batch_importance = _extract_cls_grad_importance(
            outputs.attentions, num_layers, num_heads
        )
        importance_sum += batch_importance * input_ids.size(0)
        n_samples += input_ids.size(0)

        if batch_idx % 50 == 0:
            logger.info(f"Head importance: processed {batch_idx + 1}/{max_batches} batches")

    importance = importance_sum / max(n_samples, 1)
    return importance


def _extract_cls_grad_importance(
    attentions: tuple[Tensor, ...],
    num_layers: int,
    num_heads: int,
) -> Tensor:
    """Extract per-head gradient magnitudes at the CLS token.

    Args:
        attentions: Tuple of attention tensors, one per layer.
            Each tensor shape (B, H, L, L).
        num_layers: Number of layers.
        num_heads: Number of heads.

    Returns:
        Importance tensor (num_layers, num_heads): mean |grad| at CLS row.
    """
    importance = torch.zeros(num_layers, num_heads, device=attentions[0].device)
    for layer_idx, attn in enumerate(attentions):
        if attn.grad is None:
            # Gradients not retained (e.g. eval mode without retain_graph)
            continue
        # attn.grad shape: (B, H, L, L) — gradient of loss w.r.t. attention weights
        # Take CLS row (index 0) and compute mean absolute gradient
        cls_grad = attn.grad[:, :, 0, :]  # (B, H, L)
        importance[layer_idx] = cls_grad.abs().mean(dim=(0, 2))  # (H,)
    return importance


def rank_heads(importance: Tensor, top_k: int) -> list[tuple[int, int]]:
    """Return top-k (layer, head) pairs by importance score.

    Args:
        importance: Importance tensor (num_layers, num_heads).
        top_k: Number of heads to select.

    Returns:
        List of (layer_idx, head_idx) tuples, ordered by descending importance.
    """
    flat = importance.view(-1)
    top_indices = flat.topk(min(top_k, flat.numel())).indices
    result = []
    num_heads = importance.size(1)
    for idx in top_indices:
        layer_idx = (idx // num_heads).item()
        head_idx = (idx % num_heads).item()
        result.append((int(layer_idx), int(head_idx)))
    return result


def save_importance(importance: Tensor, path: str | Path) -> None:
    """Save importance scores to a .pt file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(importance.cpu(), path)
    logger.info(f"Saved importance scores to {path}")


def load_importance(path: str | Path) -> Tensor:
    """Load importance scores from a .pt file."""
    return torch.load(path, map_location="cpu")
