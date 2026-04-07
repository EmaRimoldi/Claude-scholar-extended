"""Sparsemax operator: Euclidean projection onto the probability simplex.

Reference: Martins & Astudillo, "From Softmax to Sparsemax", ICML 2016.
https://arxiv.org/abs/1602.02068

Implements sparsemax as a differentiable torch.autograd.Function with
the correct Jacobian for backpropagation.
"""
import torch
import torch.nn as nn
from torch import Tensor


class SparsemaxFunction(torch.autograd.Function):
    """Differentiable sparsemax activation.

    Forward: projects z onto the probability simplex in L2 norm.
    Backward: applies the sparsemax Jacobian (identity on support, zero off).
    """

    @staticmethod
    def forward(ctx: torch.autograd.function.FunctionCtx, z: Tensor) -> Tensor:  # type: ignore[override]
        """Compute sparsemax(z).

        Args:
            ctx: Autograd context for saving tensors.
            z: Input logits of shape (..., dim).

        Returns:
            Sparse probability vector of shape (..., dim), values in [0, 1].
        """
        dim = z.shape[-1]
        # Sort descending along last dimension
        z_sorted, _ = torch.sort(z, dim=-1, descending=True)
        # Cumulative sum: z_sorted[k] compared to (cumsum - 1) / (k+1)
        cumsum = torch.cumsum(z_sorted, dim=-1)
        k = torch.arange(1, dim + 1, dtype=z.dtype, device=z.device)
        # threshold: the largest k such that 1 + k*z_sorted[k] > cumsum[k-1]
        threshold_sum = (cumsum - 1.0) / k
        # support indicator: z_sorted > threshold_sum
        support = z_sorted > threshold_sum
        # tau(z) = threshold for the support boundary
        # For each row: tau = (sum of z in support - 1) / |support|
        support_sum = (support * z_sorted).sum(dim=-1, keepdim=True)
        support_size = support.sum(dim=-1, keepdim=True).float()
        tau = (support_sum - 1.0) / support_size
        output = torch.clamp(z - tau, min=0.0)
        ctx.save_for_backward(output)
        return output

    @staticmethod
    def backward(ctx: torch.autograd.function.FunctionCtx, grad_output: Tensor) -> Tensor:  # type: ignore[override]
        """Compute gradient through sparsemax.

        The Jacobian is: d(sparsemax_i)/d(z_j) = delta_{ij} * I[i in support]
            - (1/|S|) * I[i in support] * I[j in support]
        where S is the support set.

        Args:
            ctx: Autograd context with saved sparsemax output.
            grad_output: Upstream gradient of shape (..., dim).

        Returns:
            Gradient w.r.t. input z.
        """
        (output,) = ctx.saved_tensors
        support = (output > 0).float()
        # sum of upstream grad over support
        support_sum = (grad_output * support).sum(dim=-1, keepdim=True)
        # gradient: g_i * I[i in S] - (1/|S|) * sum_j(g_j * I[j in S]) * I[i in S]
        support_size = support.sum(dim=-1, keepdim=True).clamp(min=1.0)
        grad = support * (grad_output - support_sum / support_size)
        return grad


def sparsemax(z: Tensor) -> Tensor:
    """Apply sparsemax activation to input tensor.

    Args:
        z: Input logits of shape (..., dim).

    Returns:
        Sparse probability vector; non-support entries are exactly 0.
    """
    return SparsemaxFunction.apply(z)


class Sparsemax(nn.Module):
    """Sparsemax module for use as drop-in replacement for softmax layers."""

    def forward(self, z: Tensor) -> Tensor:
        """Apply sparsemax.

        Args:
            z: Input logits of shape (..., dim).

        Returns:
            Sparse probability vector.
        """
        return sparsemax(z)
