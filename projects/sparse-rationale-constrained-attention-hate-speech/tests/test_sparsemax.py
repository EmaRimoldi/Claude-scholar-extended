"""Tests for sparsemax activation and loss functions."""
import pytest
import torch

from src.model.sparsemax import Sparsemax, sparsemax, sparsemax_loss


class TestSparsemax:
    def test_output_sums_to_one(self):
        x = torch.randn(4, 10)
        out = sparsemax(x)
        assert torch.allclose(out.sum(dim=-1), torch.ones(4), atol=1e-5)

    def test_non_negative(self):
        x = torch.randn(4, 10)
        out = sparsemax(x)
        assert (out >= 0).all()

    def test_sparsity(self):
        # Highly peaked input → only 1 non-zero
        x = torch.zeros(1, 10)
        x[0, 3] = 10.0
        out = sparsemax(x)
        assert (out == 0).sum() == 9
        assert torch.allclose(out[0, 3], torch.tensor(1.0))

    def test_uniform_input(self):
        # Uniform input → uniform output (all 1/n)
        x = torch.zeros(1, 5)
        out = sparsemax(x)
        expected = torch.full((1, 5), 0.2)
        assert torch.allclose(out, expected, atol=1e-5)

    def test_module_matches_function(self):
        x = torch.randn(3, 8)
        module = Sparsemax(dim=-1)
        assert torch.allclose(module(x), sparsemax(x))

    def test_2d_case(self):
        # dim=1 on 2D tensor
        x = torch.randn(5, 12)
        out = sparsemax(x, dim=1)
        assert out.shape == (5, 12)
        assert torch.allclose(out.sum(dim=1), torch.ones(5), atol=1e-5)

    def test_batch_3d(self):
        # (B, H, L) — attention score case
        x = torch.randn(2, 4, 15)
        out = sparsemax(x, dim=-1)
        assert out.shape == (2, 4, 15)
        assert torch.allclose(out.sum(dim=-1), torch.ones(2, 4), atol=1e-5)


class TestSparsemaxLoss:
    def test_loss_non_negative(self):
        x = torch.randn(4, 10)
        target = torch.zeros(4, 10)
        target[:, 2] = 1.0
        loss = sparsemax_loss(x, target)
        assert loss.item() >= 0

    def test_loss_zero_at_perfect_prediction(self):
        # If sparsemax(x) == normalize(target), loss should be ~0
        target = torch.zeros(1, 5)
        target[0, 2] = 1.0
        # Create x such that sparsemax concentrates on index 2
        x = torch.zeros(1, 5)
        x[0, 2] = 10.0
        loss = sparsemax_loss(x, target)
        assert loss.item() < 0.01

    def test_loss_scalar(self):
        x = torch.randn(8, 20)
        target = (torch.rand(8, 20) > 0.7).float()
        loss = sparsemax_loss(x, target)
        assert loss.shape == ()
