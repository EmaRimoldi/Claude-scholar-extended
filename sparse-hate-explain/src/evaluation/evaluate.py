"""Full evaluation pipeline orchestrating classification, faithfulness, and plausibility."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader

from ..metrics.classification import compute_classification_metrics
from ..metrics.faithfulness import (
    compute_attention_ig_correlation,
    compute_comprehensiveness,
    compute_sufficiency,
)
from ..metrics.plausibility import compute_plausibility_metrics

logger = logging.getLogger(__name__)


class Evaluator:
    """Orchestrates all evaluation metrics for a single model.

    Args:
        model: Transformer model with ``output_attentions`` support.
        test_dataloader: DataLoader for the test split.
        device: Torch device to run evaluation on.
    """

    def __init__(
        self,
        model: torch.nn.Module,
        test_dataloader: DataLoader,
        device: torch.device,
    ) -> None:
        self.model = model
        self.test_dataloader = test_dataloader
        self.device = device

    # ------------------------------------------------------------------
    # Internal collectors
    # ------------------------------------------------------------------

    def _collect_predictions(self) -> Dict[str, np.ndarray]:
        """Run inference and collect predictions, attention, and rationales."""
        self.model.eval()
        all_preds: list[int] = []
        all_labels: list[int] = []
        all_attention: list[np.ndarray] = []
        all_rationale: list[np.ndarray] = []
        all_attn_mask: list[np.ndarray] = []

        with torch.no_grad():
            for batch in self.test_dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"]
                rationale_mask = batch["rationale_mask"]

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                )
                logits = outputs.logits
                preds = logits.argmax(dim=-1).cpu().numpy()

                # Last-layer CLS attention averaged over heads
                last_attn = outputs.attentions[-1]
                cls_attn = last_attn[:, :, 0, :].mean(dim=1).cpu().numpy()

                all_preds.extend(preds.tolist())
                all_labels.extend(labels.numpy().tolist())
                all_attention.append(cls_attn)
                all_rationale.append(rationale_mask.numpy())
                all_attn_mask.append(attention_mask.cpu().numpy())

        return {
            "predictions": np.array(all_preds),
            "labels": np.array(all_labels),
            "attention_weights": np.concatenate(all_attention, axis=0),
            "rationale_masks": np.concatenate(all_rationale, axis=0),
            "attention_masks": np.concatenate(all_attn_mask, axis=0),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_classification(self) -> Dict[str, Any]:
        """Run classification metrics only."""
        collected = self._collect_predictions()
        return compute_classification_metrics(
            collected["predictions"], collected["labels"]
        )

    def evaluate_faithfulness(
        self,
        rationale_threshold: float = 0.5,
        ig_n_steps: int = 50,
    ) -> Dict[str, Any]:
        """Run all faithfulness metrics."""
        corr = compute_attention_ig_correlation(
            self.model, self.test_dataloader, self.device, n_steps=ig_n_steps
        )
        suff = compute_sufficiency(
            self.model, self.test_dataloader, self.device, rationale_threshold
        )
        comp = compute_comprehensiveness(
            self.model, self.test_dataloader, self.device, rationale_threshold
        )
        return {**corr, **suff, **comp}

    def evaluate_plausibility(
        self,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Run plausibility metrics."""
        collected = self._collect_predictions()
        return compute_plausibility_metrics(
            collected["attention_weights"],
            collected["rationale_masks"],
            collected["attention_masks"],
            threshold=threshold,
        )

    def evaluate_all(
        self,
        rationale_threshold: float = 0.5,
        ig_n_steps: int = 50,
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the complete evaluation pipeline.

        Args:
            rationale_threshold: Threshold for binarising rationale masks.
            ig_n_steps: Number of IG interpolation steps.
            save_path: If provided, save results as JSON to this path.

        Returns:
            Dict with keys: classification, faithfulness, plausibility.
        """
        logger.info("Running classification evaluation...")
        classification = self.evaluate_classification()

        logger.info("Running faithfulness evaluation...")
        faithfulness = self.evaluate_faithfulness(
            rationale_threshold=rationale_threshold,
            ig_n_steps=ig_n_steps,
        )

        logger.info("Running plausibility evaluation...")
        plausibility = self.evaluate_plausibility(
            threshold=rationale_threshold,
        )

        results: Dict[str, Any] = {
            "classification": classification,
            "faithfulness": faithfulness,
            "plausibility": plausibility,
        }

        if save_path is not None:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(results, f, indent=2)
            logger.info("Results saved to %s", save_path)

        return results


# ---------------------------------------------------------------------------
# Multi-model comparison
# ---------------------------------------------------------------------------

def compare_models(
    models: Dict[str, torch.nn.Module],
    test_dataloader: DataLoader,
    device: torch.device,
    save_path: Optional[str] = None,
    rationale_threshold: float = 0.5,
    ig_n_steps: int = 50,
) -> Dict[str, Dict[str, Any]]:
    """Evaluate and compare multiple models side by side.

    Args:
        models: Mapping from model name to model instance.
        test_dataloader: Shared test dataloader.
        device: Torch device.
        save_path: If provided, save comparison JSON to this path.
        rationale_threshold: Threshold for rationale binarisation.
        ig_n_steps: Number of IG interpolation steps.

    Returns:
        Dict mapping model name to its full evaluation results.
    """
    all_results: Dict[str, Dict[str, Any]] = {}

    for name, model in models.items():
        logger.info("Evaluating model: %s", name)
        evaluator = Evaluator(model, test_dataloader, device)
        all_results[name] = evaluator.evaluate_all(
            rationale_threshold=rationale_threshold,
            ig_n_steps=ig_n_steps,
        )

    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info("Comparison results saved to %s", save_path)

    return all_results
