"""Alignment loss functions for rationale-constrained attention supervision."""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from src.model.sparsemax import sparsemax_loss


class MSEAlignmentLoss(nn.Module):
    """Mean squared error between attention weights and rationale distribution.

    The rationale mask is sum-normalized to a probability distribution before
    computing MSE. Averaging is done over heads and batch.

    This is the primary loss for M2–M4a/b/c/M7 conditions.
    """

    def forward(self, attention: Tensor, rationale_mask: Tensor) -> Tensor:
        """Compute MSE alignment loss.

        Args:
            attention: Attention weights, shape (B, k, L).
                Already after softmax/sparsemax; should sum to 1 per head per position.
            rationale_mask: Binary/soft rationale mask, shape (B, L).
                Will be normalized to sum to 1 per example.

        Returns:
            Scalar loss.
        """
        # Normalize rationale to distribution
        target_sum = rationale_mask.sum(dim=-1, keepdim=True).clamp(min=1e-8)
        q = rationale_mask / target_sum  # (B, L)
        q = q.unsqueeze(1).expand_as(attention)  # (B, k, L)

        return 0.5 * ((attention - q) ** 2).sum(dim=-1).mean()


class KLAlignmentLoss(nn.Module):
    """KL divergence between attention weights and rationale distribution.

    KL(rationale || attention): measures information lost when approximating
    the rationale distribution with the attention distribution.

    Condition M5.
    """

    def __init__(self, eps: float = 1e-8) -> None:
        super().__init__()
        self.eps = eps

    def forward(self, attention: Tensor, rationale_mask: Tensor) -> Tensor:
        """Compute KL alignment loss.

        Args:
            attention: Attention weights, shape (B, k, L).
            rationale_mask: Rationale mask, shape (B, L).

        Returns:
            Scalar loss.
        """
        # Normalize rationale to distribution
        target_sum = rationale_mask.sum(dim=-1, keepdim=True).clamp(min=self.eps)
        q = rationale_mask / target_sum  # (B, L)
        q = q.unsqueeze(1).expand_as(attention)  # (B, k, L)

        # Add eps to avoid log(0)
        p = attention.clamp(min=self.eps)
        q = q.clamp(min=self.eps)

        # KL(q || p) = sum(q * log(q/p))
        kl = (q * (q / p).log()).sum(dim=-1)  # (B, k)
        return kl.mean()


class SparsemaxAlignmentLoss(nn.Module):
    """Sparsemax loss: natural conjugate of sparsemax operator as alignment loss.

    Uses the sparsemax_loss function from model.sparsemax which computes
    0.5 * ||sparsemax(z) - normalize(q)||^2 in pre-activation space.

    This loss requires access to the pre-activation attention scores (logits),
    not the post-sparsemax probabilities. The model must store pre-activation
    scores for this loss to function correctly.

    Condition M6.
    """

    def forward(self, attention_logits: Tensor, rationale_mask: Tensor) -> Tensor:
        """Compute sparsemax alignment loss.

        Args:
            attention_logits: Pre-activation attention scores, shape (B, k, L).
            rationale_mask: Rationale mask, shape (B, L).

        Returns:
            Scalar loss.
        """
        # Average over supervised heads
        losses = []
        for h in range(attention_logits.size(1)):
            losses.append(sparsemax_loss(attention_logits[:, h, :], rationale_mask))
        return torch.stack(losses).mean()


ALIGNMENT_LOSS_REGISTRY: dict[str, type[nn.Module]] = {
    "mse": MSEAlignmentLoss,
    "kl": KLAlignmentLoss,
    "sparsemax": SparsemaxAlignmentLoss,
}


def build_alignment_loss(loss_type: str) -> nn.Module:
    """Factory for alignment loss modules.

    Args:
        loss_type: One of "mse", "kl", "sparsemax".

    Returns:
        Instantiated alignment loss module.

    Raises:
        ValueError: If loss_type is not in registry.
    """
    if loss_type not in ALIGNMENT_LOSS_REGISTRY:
        raise ValueError(
            f"Unknown alignment loss type '{loss_type}'. "
            f"Choose from: {list(ALIGNMENT_LOSS_REGISTRY.keys())}"
        )
    return ALIGNMENT_LOSS_REGISTRY[loss_type]()
