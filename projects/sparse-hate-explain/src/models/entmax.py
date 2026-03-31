"""α-entmax activation (Correia, Niculae & Martins, EMNLP 2019).

Generalises softmax (α=1) and sparsemax (α=2) via a bisection-based
projection.  We implement the numerical bisection approach from the paper
rather than relying on the optional ``entmax`` package so that the codebase
has no extra dependency.

Reference:
    Correia, G.M., Niculae, V., & Martins, A.F.T. (2019).
    Adaptively Sparse Transformers. EMNLP 2019.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


def entmax_bisect(
    input: Tensor,
    alpha: float = 1.5,
    dim: int = -1,
    n_iter: int = 50,
    eps: float = 1e-6,
) -> Tensor:
    """α-entmax via bisection (differentiable, O(n_iter · N) complexity).

    For α=1 reduces to softmax; for α=2 reduces to sparsemax.
    Uses the bisection algorithm from Correia et al. (2019) Appendix A.

    Parameters
    ----------
    input : Tensor
        Raw (unnormalized) scores of shape ``(..., N, ...)``.
    alpha : float
        Sparsity-controlling parameter (α ≥ 1).  Values > 1 produce sparse
        distributions; α=2 is sparsemax.
    dim : int
        Dimension over which to normalize.
    n_iter : int
        Number of bisection iterations (50 is overkill; 20 suffices in practice).
    eps : float
        Convergence tolerance (unused explicitly; n_iter controls quality).

    Returns
    -------
    Tensor
        Probability tensor of same shape, summing to 1 along *dim*.
    """
    if alpha == 1.0:
        return torch.softmax(input, dim=dim)

    # Shift for numerical stability: subtract max along dim.
    z = input - input.max(dim=dim, keepdim=True).values

    # α-1 coefficient.
    am1 = alpha - 1.0

    # Bisection on the threshold τ.
    # Equation: p_i(τ) = max(0, ((α-1)*z_i - τ))^{1/(α-1)}
    # Constraint: sum_i p_i = 1

    # Find bracket [lo, hi] for τ.
    z_sort, _ = z.sort(dim=dim, descending=True)
    n = z.size(dim)
    # Upper bound: τ < (α-1)*z_max (since p_0 > 0 at τ → -∞).
    hi = (z_sort.select(dim, 0) * am1).unsqueeze(dim)
    # Lower bound: τ > (α-1)*z_max - 1 (rough; will be refined).
    lo = hi - 1.0

    # Expand lo/hi to match z shape for vectorised bisection.
    shape = [1] * z.dim()
    shape[dim] = 1

    # Pre-compute (α-1)*z once.
    am1_z = am1 * z  # (..., N, ...)

    def _sum_probs(tau: Tensor) -> Tensor:
        """Sum of p_i(tau) = sum of max(0, am1_z - tau)^{1/am1}."""
        diff = (am1_z - tau).clamp(min=0.0)
        return diff.pow(1.0 / am1).sum(dim=dim, keepdim=True)

    # Expand bracket until sum(lo) >= 1 and sum(hi) <= 1.
    # In practice a single expansion step is sufficient.
    for _ in range(64):
        lo_sum = _sum_probs(lo)
        if (lo_sum >= 1.0).all():
            break
        lo = lo - 1.0

    # Bisection loop.
    for _ in range(n_iter):
        mid = (lo + hi) / 2.0
        mid_sum = _sum_probs(mid)
        lo = torch.where(mid_sum > 1.0, mid, lo)
        hi = torch.where(mid_sum <= 1.0, mid, hi)

    tau_star = (lo + hi) / 2.0
    p = (am1_z - tau_star).clamp(min=0.0).pow(1.0 / am1)
    # Re-normalise to correct for numerical drift.
    p = p / p.sum(dim=dim, keepdim=True).clamp(min=1e-12)
    return p


class Entmax(nn.Module):
    """α-entmax activation as an ``nn.Module``.

    Parameters
    ----------
    alpha : float
        Sparsity parameter (α ≥ 1).  α=1 → softmax, α=2 → sparsemax.
    dim : int
        Dimension to normalise over (default: -1).
    """

    def __init__(self, alpha: float = 1.5, dim: int = -1) -> None:
        super().__init__()
        self.alpha = alpha
        self.dim = dim

    def forward(self, input: Tensor) -> Tensor:
        return entmax_bisect(input, alpha=self.alpha, dim=self.dim)

    def extra_repr(self) -> str:
        return f"alpha={self.alpha}, dim={self.dim}"
