"""Tests for plausibility metrics: IoU-F1 and Token-F1."""
import pytest

from src.evaluation.plausibility import (
    attention_to_binary_mask,
    compute_plausibility_metrics,
    iou_f1,
    token_f1,
)


class TestIoUF1:
    def test_perfect_agreement(self):
        pred = [1, 0, 1, 1, 0]
        gold = [1, 0, 1, 1, 0]
        assert iou_f1(pred, gold, ignore_special_tokens=False) == pytest.approx(1.0)

    def test_no_overlap(self):
        pred = [1, 0, 0, 0, 0]
        gold = [0, 0, 0, 1, 0]
        assert iou_f1(pred, gold, ignore_special_tokens=False) == pytest.approx(0.0)

    def test_partial_overlap(self):
        pred = [1, 1, 0, 0]
        gold = [1, 0, 1, 0]
        # Intersection = {0}, union = {0, 1, 2}
        assert iou_f1(pred, gold, ignore_special_tokens=False) == pytest.approx(1 / 3)

    def test_both_empty(self):
        assert iou_f1([0, 0, 0], [0, 0, 0], ignore_special_tokens=False) == 1.0


class TestTokenF1:
    def test_perfect(self):
        pred = [1, 0, 1]
        gold = [1, 0, 1]
        assert token_f1(pred, gold, ignore_special_tokens=False) == pytest.approx(1.0)

    def test_no_match(self):
        assert token_f1([1, 0, 0], [0, 0, 1], ignore_special_tokens=False) == pytest.approx(0.0)

    def test_partial(self):
        # TP=1, FP=1, FN=1 → precision=0.5, recall=0.5, F1=0.5
        pred = [1, 1, 0, 0]
        gold = [1, 0, 1, 0]
        assert token_f1(pred, gold, ignore_special_tokens=False) == pytest.approx(0.5)


class TestAttentionBinarization:
    def test_sparsemax_threshold(self):
        # Sparsemax: threshold=0.0 keeps all non-zero weights
        weights = [0.0, 0.3, 0.0, 0.7]
        mask = attention_to_binary_mask(weights, threshold=0.0)
        assert mask == [0, 1, 0, 1]

    def test_positive_threshold(self):
        weights = [0.05, 0.3, 0.0, 0.7]
        mask = attention_to_binary_mask(weights, threshold=0.1)
        assert mask == [0, 1, 0, 1]


class TestComputePlausibility:
    def test_returns_both_metrics(self):
        preds = [[0.0, 0.5, 0.0, 0.5], [0.0, 0.0, 1.0, 0.0]]
        golds = [[0, 1, 0, 1], [0, 0, 1, 0]]
        result = compute_plausibility_metrics(preds, golds, threshold=0.0)
        assert "iou_f1" in result
        assert "token_f1" in result
        assert 0.0 <= result["iou_f1"] <= 1.0
        assert 0.0 <= result["token_f1"] <= 1.0
