"""ICL Linear Regression Dataset.

A complete example of a @register_dataset class for in-context learning
with linear regression tasks. Each episode samples a fresh weight vector,
generates input/output pairs, and formats them as an interleaved ICL sequence.

Usage:
    from src.data_module.dataset import DatasetFactory
    dataset = DatasetFactory("icl_linear_regression")(cfg)
    episode, target = dataset[0]
"""

from __future__ import annotations

import torch
from torch.utils.data import Dataset

from src.data_module.dataset import register_dataset


@register_dataset("icl_linear_regression")
class ICLLinearRegressionDataset(Dataset):
    """Synthetic linear regression dataset for in-context learning.

    Each item is an ICL episode: k labeled examples (x_i, y_i) followed by
    a query x_query. The target is y_query. A fresh weight vector w is
    sampled per episode so the model must infer the task from context.

    Episode format (returned tensor):
        Shape: (2 * n_examples + 1, d_input + 1)
        Even rows [0, 2, ...]: x vectors (d_input dims) + 0 padding
        Odd rows  [1, 3, ...]: y scalars in dim 0 + 0 padding
        Last row  [2k]:        x_query (d_input dims) + 0 padding

    Attributes:
        num_samples: Total number of episodes in this split.
        d_input: Dimensionality of input vectors.
        n_examples: Number of in-context (x, y) pairs per episode.
        noise_std: Standard deviation of additive Gaussian noise on y.
        base_seed: Base random seed; episode i uses seed = base_seed + i.
    """

    def __init__(self, cfg) -> None:
        self.num_samples: int = cfg.dataset.num_train  # or num_val / num_test
        self.d_input: int = cfg.dataset.d_input
        self.n_examples: int = cfg.dataset.n_examples
        self.noise_std: float = cfg.dataset.get("noise_std", 0.0)
        self.base_seed: int = cfg.dataset.get("seed", 42)

        # Validate on a small probe batch at construction time
        self.validate(n=8)

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Generate a single ICL episode.

        Args:
            idx: Episode index, used to derive a deterministic seed.

        Returns:
            episode: Interleaved sequence, shape (2*n_examples + 1, d_input + 1).
            target: y value for the query point, shape (1,).
        """
        generator = torch.Generator().manual_seed(self.base_seed + idx)

        # Fresh task vector for this episode
        w = torch.randn(self.d_input, generator=generator)

        # Sample n_examples + 1 input points (last one is the query)
        n_total = self.n_examples + 1
        xs = torch.randn(n_total, self.d_input, generator=generator)
        ys = xs @ w  # shape: (n_total,)

        # Add noise
        if self.noise_std > 0:
            noise = self.noise_std * torch.randn(n_total, generator=generator)
            ys = ys + noise

        # Build interleaved episode tensor
        seq_len = 2 * self.n_examples + 1
        dim = self.d_input + 1
        episode = torch.zeros(seq_len, dim)

        for i in range(self.n_examples):
            episode[2 * i, : self.d_input] = xs[i]
            episode[2 * i + 1, 0] = ys[i]

        # Query point (no y in the episode)
        episode[2 * self.n_examples, : self.d_input] = xs[-1]
        target = ys[-1].unsqueeze(0)

        return episode, target

    def validate(self, n: int = 8) -> dict[str, bool]:
        """Run sanity checks on a probe batch of n episodes.

        Checks:
            shape: Episode and target tensor shapes match expected values.
            finite: No NaN or Inf values in episodes or targets.
            reproducible: Same index returns identical tensors on two calls.

        Args:
            n: Number of episodes to validate.

        Returns:
            Dict mapping check name to pass/fail bool.
        """
        results: dict[str, bool] = {}
        expected_seq_len = 2 * self.n_examples + 1
        expected_dim = self.d_input + 1

        # Shape check
        shape_ok = True
        for i in range(min(n, len(self))):
            episode, target = self[i]
            if episode.shape != (expected_seq_len, expected_dim):
                shape_ok = False
                break
            if target.shape != (1,):
                shape_ok = False
                break
        results["shape"] = shape_ok

        # Finite values check
        finite_ok = True
        for i in range(min(n, len(self))):
            episode, target = self[i]
            if not torch.isfinite(episode).all() or not torch.isfinite(target).all():
                finite_ok = False
                break
        results["finite"] = finite_ok

        # Reproducibility check
        repro_ok = True
        for i in range(min(n, len(self))):
            ep1, t1 = self[i]
            ep2, t2 = self[i]
            if not torch.equal(ep1, ep2) or not torch.equal(t1, t2):
                repro_ok = False
                break
        results["reproducible"] = repro_ok

        # Print summary
        print(f"Validation ({self.__class__.__name__}, n={min(n, len(self))}):")
        for check, passed in results.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {check}: {status}")

        return results
