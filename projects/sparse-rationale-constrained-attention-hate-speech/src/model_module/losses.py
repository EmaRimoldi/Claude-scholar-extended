"""Alignment loss functions for supervised attention.

Two variants:
- KL divergence (SRA-style, for softmax attention baselines)
- MSE (for sparsemax attention; well-defined when target has exact zeros)

Reference: Eilertsen et al., "Aligning Attention with Human Rationales", AAAI 2026.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


class KLAlignmentLoss(nn.Module):
    """KL-divergence alignment loss between softmax attention and rationale target.

    Used for SRA replication (Condition C2). Penalizes divergence between
    the softmax attention distribution and the normalized rationale mask.
    Non-rationale tokens retain nonzero mass (KL can only reduce, not eliminate).

    L = KL(softmax(z) || r_tilde) = sum_t softmax_t * log(softmax_t / r_tilde_t)

    Note: KL is undefined when target r_tilde_t = 0 (as in softmax output > 0 but
    target = 0). Standard approach (SRA): add epsilon to target before KL.
    """

    def __init__(self, epsilon: float = 1e-8) -> None:
        super().__init__()
        self.epsilon = epsilon

    def forward(self, attention: Tensor, rationale_mask: Tensor) -> Tensor:
        """Compute KL alignment loss.

        Computes KL(attention || rationale_target) using F.kl_div which is
        numerically stable and guaranteed non-negative.
        F.kl_div(input=log_Q, target=P) computes sum_t P_t * (log P_t - input_t)
        i.e. KL(P || Q). We use P=attention, Q=rationale_target.

        Args:
            attention: Softmax attention weights, shape (B, T). Must sum to 1 per row.
            rationale_mask: Normalized rationale target, shape (B, T). Values in [0,1], sums to 1.

        Returns:
            Scalar mean KL divergence over the batch.
        """
        # Add epsilon to target to handle zero entries (target may have zeros for
        # non-rationale tokens; KL diverges when P > 0 and Q = 0)
        target_smooth = rationale_mask + self.epsilon
        target_smooth = target_smooth / target_smooth.sum(dim=-1, keepdim=True)
        log_target = torch.log(target_smooth)
        # KL(attention || target_smooth) = sum_t attention_t * log(attention_t / target_smooth_t)
        #
        # BERT padding tokens: BERT adds torch.finfo(float32).min (~-3.4e38) as additive mask.
        # exp(-3.4e38) underflows to exactly 0.0 in float32 → attention=0 at padding positions.
        # By KL convention, 0 * log(0 / q) = 0 for any q > 0.
        #
        # torch.xlogy fixes the FORWARD (returns 0 at p=0) but NOT the BACKWARD
        # (derivative of x*log(x) at x=0 is log(0)+1 = -inf → NaN gradients).
        #
        # The correct fix uses torch.where to route padding positions to a constant branch
        # (zero output), completely eliminating the gradient path through those positions:
        #   - nonzero mask: True for real tokens, False for padding
        #   - safe_attn: attention for real tokens, 1.0 (constant) for padding
        #   - kl_per_token: attention*(log(attention)-log_target) for real, 0 for padding
        # Backward: torch.where multiplies grad by 0 at padding positions → no NaN.
        nonzero = attention > 0
        safe_attn = torch.where(nonzero, attention, torch.ones_like(attention))
        kl_per_token = torch.where(
            nonzero,
            safe_attn * (torch.log(safe_attn) - log_target),
            torch.zeros_like(attention),
        )
        # KL divergence is non-negative by definition; clamp to avoid tiny float32
        # rounding errors (e.g., ~-2e-8) when attention ≈ target distribution.
        return kl_per_token.sum(dim=-1).mean().clamp(min=0.0)


class MSEAlignmentLoss(nn.Module):
    """MSE alignment loss between sparsemax attention and rationale target.

    Used for sparsemax conditions (C4, C5). MSE is well-defined when target
    has exact zeros (unlike KL), making it the natural choice for sparsemax.

    L = (1/T) * sum_t (sparsemax_t(z) - r_tilde_t)^2

    Gradient w.r.t. sparsemax output is exact; chain rule through sparsemax
    Jacobian handles the thresholding correctly (see sparsemax.py backward).
    """

    def forward(self, attention: Tensor, rationale_mask: Tensor) -> Tensor:
        """Compute MSE alignment loss.

        Args:
            attention: Sparsemax attention weights, shape (B, T). Can have exact zeros.
            rationale_mask: Normalized rationale target, shape (B, T). Values in [0,1], sums to 1.

        Returns:
            Scalar mean MSE over the batch.
        """
        return F.mse_loss(attention, rationale_mask)


class JointLoss(nn.Module):
    """Combined classification + alignment loss.

    L_total = L_CE + alpha * L_align

    Args:
        alignment_loss: KLAlignmentLoss or MSEAlignmentLoss instance.
        alpha: Weighting coefficient for alignment term. Grid: {0.1, 0.3, 0.5, 1.0}.
        num_classes: Number of output classes (3 for HateXplain: hate/offensive/normal).
    """

    def __init__(
        self,
        alignment_loss: nn.Module,
        alpha: float = 0.3,
        num_classes: int = 3,
    ) -> None:
        super().__init__()
        self.alignment_loss = alignment_loss
        self.alpha = alpha
        self.ce = nn.CrossEntropyLoss()

    def forward(
        self,
        logits: Tensor,
        labels: Tensor,
        attention: Tensor,
        rationale_mask: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Compute joint classification + alignment loss.

        Args:
            logits: Classification logits, shape (B, num_classes).
            labels: Ground-truth class indices, shape (B,).
            attention: CLS attention weights over tokens, shape (B, T).
            rationale_mask: Normalized rationale target, shape (B, T).

        Returns:
            Tuple of (total_loss, ce_loss, align_loss).
        """
        ce_loss = self.ce(logits, labels)
        align_loss = self.alignment_loss(attention, rationale_mask)
        total_loss = ce_loss + self.alpha * align_loss
        return total_loss, ce_loss, align_loss
