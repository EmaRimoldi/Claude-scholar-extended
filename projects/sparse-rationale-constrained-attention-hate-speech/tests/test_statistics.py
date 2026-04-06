"""Tests for statistical utility functions."""
import pytest
import numpy as np

from src.evaluation.statistics import (
    bootstrap_ci,
    bootstrap_paired_ci,
    cohens_d,
    effect_size_label,
    post_hoc_power,
)


class TestBootstrapCI:
    def test_ci_width(self):
        values = [0.5 + 0.01 * i for i in range(20)]
        est, lo, hi = bootstrap_ci(values, n_bootstrap=500, seed=0)
        assert lo < est < hi

    def test_ci_contains_true_mean(self):
        rng = np.random.default_rng(42)
        values = rng.normal(0.7, 0.05, size=50).tolist()
        _, lo, hi = bootstrap_ci(values, n_bootstrap=1000, ci=0.95, seed=0)
        assert lo < 0.7 < hi


class TestBootstrapPairedCI:
    def test_positive_diff(self):
        a = [0.8, 0.82, 0.79, 0.81, 0.83]
        b = [0.6, 0.61, 0.59, 0.62, 0.60]
        diff, lo, hi = bootstrap_paired_ci(a, b, n_bootstrap=500, seed=0)
        assert diff > 0
        assert lo > 0  # CI excludes 0 → significant


class TestCohensD:
    def test_equal_groups_d_zero(self):
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]
        assert cohens_d(a, b) == pytest.approx(0.0)

    def test_effect_size_labels(self):
        assert effect_size_label(0.1) == "negligible"
        assert effect_size_label(0.3) == "small"
        assert effect_size_label(0.6) == "medium"
        assert effect_size_label(1.0) == "large"


class TestPower:
    def test_power_increases_with_effect(self):
        p_small = post_hoc_power(0.2, 10)
        p_large = post_hoc_power(0.8, 10)
        assert p_small < p_large

    def test_power_in_range(self):
        p = post_hoc_power(0.5, 10)
        assert 0.0 <= p <= 1.0
