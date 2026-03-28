"""Sparsemax activation function (Martins & Astudillo, 2016).

Replaces softmax with a sparse probability mapping that projects onto the
probability simplex, yielding exactly-zero attention weights for irrelevant
tokens.

Reference:
    Andre F. T. Martins and Ramon F. Astudillo. "From Softmax to Sparsemax:
    A Sparse Model of Attention and Multi-Label Classification." ICML 2016.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


class SparsemaxFunction(torch.autograd.Function):
    """Autograd-compatible sparsemax with efficient custom backward."""

    @staticmethod
    def forward(ctx: torch.autograd.function.FunctionCtx, input: Tensor, dim: int = -1) -> Tensor:
        """Project *input* onto the probability simplex along *dim*.

        Algorithm (Martins & Astudillo 2016, Algorithm 1):
        1. Sort z in descending order.
        2. Compute cumulative sums and find the support size k(z).
        3. Compute threshold tau(z) and project.
        """
        dim = dim if dim >= 0 else input.dim() + dim
        n_features = input.size(dim)

        # Sort descending along target dim.
        z_sorted, _ = input.sort(dim=dim, descending=True)

        # Cumulative sum of sorted values.
        cumsum = z_sorted.cumsum(dim=dim)

        # k-vector: 1, 2, ..., n  (broadcast-compatible shape).
        shape = [1] * input.dim()
        shape[dim] = n_features
        k_vec = torch.arange(1, n_features + 1, device=input.device, dtype=input.dtype).view(shape)

        # Support condition: 1 + k * z_k > cumsum_k
        support = (1.0 + k_vec * z_sorted > cumsum).to(input.dtype)

        # k(z) = max k such that support condition holds.
        k_z = support.sum(dim=dim, keepdim=True)

        # Threshold tau(z) = (cumsum_{k(z)} - 1) / k(z).
        # Gather cumulative sum at k(z) - 1 index.
        k_z_idx = (k_z - 1).clamp(min=0).long()
        tau_sum = cumsum.gather(dim, k_z_idx)
        tau = (tau_sum - 1.0) / k_z.clamp(min=1.0)

        output = (input - tau).clamp(min=0.0)

        ctx.save_for_backward(output)
        ctx.dim = dim
        return output

    @staticmethod
    def backward(ctx: torch.autograd.function.FunctionCtx, grad_output: Tensor) -> tuple[Tensor | None, None]:
        """Backward pass: project gradient onto the support set."""
        (output,) = ctx.saved_tensors
        dim = ctx.dim

        # Support mask: where output > 0.
        support = (output > 0).to(grad_output.dtype)
        support_size = support.sum(dim=dim, keepdim=True).clamp(min=1.0)

        # v_hat = sum of grad_output over support / |support|
        v_hat = (grad_output * support).sum(dim=dim, keepdim=True) / support_size

        grad_input = support * (grad_output - v_hat)
        return grad_input, None


def sparsemax(input: Tensor, dim: int = -1) -> Tensor:
    """Functional sparsemax: project *input* onto the simplex along *dim*."""
    return SparsemaxFunction.apply(input, dim)


class Sparsemax(nn.Module):
    """Sparsemax activation as an ``nn.Module``.

    Parameters
    ----------
    dim : int
        Dimension along which to apply sparsemax (default: -1).
    """

    def __init__(self, dim: int = -1) -> None:
        super().__init__()
        self.dim = dim

    def forward(self, input: Tensor) -> Tensor:
        return sparsemax(input, dim=self.dim)

    def extra_repr(self) -> str:
        return f"dim={self.dim}"


def sparsemax_transform(attention_scores: Tensor, dim: int = -1) -> Tensor:
    """Convert raw attention scores to sparse probabilities via sparsemax.

    Drop-in replacement for ``torch.softmax(attention_scores, dim)``.

    Parameters
    ----------
    attention_scores : Tensor
        Raw (unnormalized) attention logits of shape ``(..., n_features)``.
    dim : int
        Dimension along which to normalize (default: -1).

    Returns
    -------
    Tensor
        Sparse probability tensor (same shape), entries in [0, 1] summing to 1
        along *dim*.
    """
    return sparsemax(attention_scores, dim=dim)
