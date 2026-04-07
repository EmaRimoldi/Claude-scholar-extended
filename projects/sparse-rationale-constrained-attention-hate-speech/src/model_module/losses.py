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
        # = sum_t [attention_t * log(attention_t)] - [attention_t * log_target_t]
        # Use torch.xlogy for the entropy term: xlogy(p, p) = p*log(p), with xlogy(0, 0)=0
        # This avoids NaN from BERT padding tokens where softmax underflows to exactly 0.0
        # (float32: exp(-3.4e38) = 0 exactly), which causes 0*log(0) = 0*(-inf) = NaN in F.kl_div.
        kl_per_token = torch.xlogy(attention, attention) - attention * log_target
        return kl_per_token.sum(dim=-1).mean()


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
