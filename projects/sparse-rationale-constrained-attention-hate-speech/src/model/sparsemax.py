"""Sparsemax activation function (Martins & Astudillo, ICML 2016)."""
from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


class Sparsemax(nn.Module):
    """Sparsemax activation: projects onto the probability simplex with sparsity.

    Produces exact zeros for low-weight tokens, unlike softmax which assigns
    positive probability to all tokens. This structural property aligns naturally
    with binary rationale annotation targets (token is/isn't a rationale).
    """

    def __init__(self, dim: int = -1) -> None:
        super().__init__()
        self.dim = dim

    def forward(self, input: Tensor) -> Tensor:
        return sparsemax(input, dim=self.dim)


def sparsemax(input: Tensor, dim: int = -1) -> Tensor:
    """Compute sparsemax activation along the specified dimension.

    Algorithm: sort input descending, find threshold k*, project onto simplex.

    Args:
        input: Input tensor of any shape.
        dim: Dimension along which to apply sparsemax.

    Returns:
        Sparse probability distribution, same shape as input.
    """
    # Move target dim to last position for easier indexing
    input = input.transpose(0, dim)
    original_size = input.size()
    input = input.reshape(input.size(0), -1)
    input = input.transpose(0, 1)
    dim = -1

    n = input.size(dim)
    input_sorted, _ = torch.sort(input, dim=dim, descending=True)
    input_cumsum = torch.cumsum(input_sorted, dim=dim)
    rho = torch.arange(1, n + 1, dtype=input.dtype, device=input.device)
    # threshold: z_{(i)} - (cumsum - 1) / i > 0
    threshold = (input_cumsum - 1.0) / rho
    # find last i where z_{(i)} > threshold_{(i)}
    support = (input_sorted > threshold).int()
    k_star = support.sum(dim=dim, keepdim=True).clamp(min=1)
    tau = threshold.gather(dim, k_star - 1)

    output = torch.clamp(input - tau, min=0.0)

    # Restore original shape
    output = output.transpose(0, 1)
    output = output.reshape(original_size)
    output = output.transpose(0, dim)
    return output


def sparsemax_loss(input: Tensor, target: Tensor, dim: int = -1) -> Tensor:
    """Sparsemax loss: natural convex conjugate of the sparsemax operator.

    This is the natural alignment loss when using sparsemax attention, as it
    shares the same structural assumptions as the activation function.

    Loss = -<z, q> + (1/2)*||p - q||^2 + (1/2)*||p||^2 - (1/2)*||q||^2
    where p = sparsemax(z) and q = target.

    In practice implemented as: 0.5 * ||sparsemax(z) - q||^2 (MSE in the output space)
    which is equivalent under the sparsemax map.

    Args:
        input: Pre-activation logits (before sparsemax).
        target: Target distribution (binary rationale mask, sum-normalized).
        dim: Dimension of the distribution.

    Returns:
        Scalar loss value.
    """
    p = sparsemax(input, dim=dim)
    # Normalize target to be a valid distribution if not already
    target_sum = target.sum(dim=dim, keepdim=True).clamp(min=1e-8)
    q = target / target_sum
    return 0.5 * ((p - q) ** 2).sum(dim=dim).mean()
