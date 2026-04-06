#!/usr/bin/env python3
"""Phase 4: Statistical analysis and hypothesis testing.

Requires: All trained model outputs from Phase 2.
Outputs: Statistical test results, effect sizes, power analysis.
"""
import json
import logging
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from src.data.dataset import HateXplainDataset, collate_fn
from src.evaluation.faithfulness import compute_faithfulness
from src.evaluation.plausibility import compute_plausibility_metrics
from src.evaluation.statistics import (
    bootstrap_confidence_interval,
    cohens_d,
    power_analysis,
)
from src.model.bert_sparse import SparseBertForSequenceClassification, SparseBertConfig
from transformers import AutoTokenizer, AutoConfig

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_trained_model(condition: str, seed: int, output_dir: Path):
    """Load a trained model from Phase 2 outputs."""
    model_dir = output_dir / condition / f"seed{seed}"
    checkpoint_dir = model_dir / "checkpoint-best"

    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_dir}")

    bert_config = AutoConfig.from_pretrained(
        checkpoint_dir,
        output_attentions=True,
    )

    model_cfg = SparseBertConfig(num_labels=3)
    model = SparseBertForSequenceClassification.from_pretrained(
        checkpoint_dir,
        config=bert_config,
        model_cfg=model_cfg,
    )

    return model.eval()


def compute_metrics_for_condition(condition: str, output_dir: Path) -> dict:
    """Compute all metrics for one condition across all seeds."""
    results = {
        "condition": condition,
        "seeds": {},
        "aggregated": {},
    }

    seeds = [42, 43, 44]
    all_plausibilities = []
    all_faithfulness_comp = []
    all_faithfulness_suff = []

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    val_dataset = HateXplainDataset(
        "validation",
        tokenizer,
        max_length=128,
        include_rationale=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=16,
        collate_fn=collate_fn,
        shuffle=False,
    )

    for seed in seeds:
        try:
            logger.info(f"Computing metrics: {condition} seed={seed}")
            model = load_trained_model(condition, seed, output_dir)
            model = model.to(device)

            # Plausibility
            plaus = compute_plausibility_metrics(model, val_loader, device=device)
            all_plausibilities.append(plaus.get("iou_f1", 0.0))
            results["seeds"][f"seed_{seed}"] = {
                "plausibility": plaus,
            }

            # Faithfulness
            faith = compute_faithfulness(model, val_loader, device=device)
            all_faithfulness_comp.append(faith.get("comprehensiveness", 0.0))
            all_faithfulness_suff.append(faith.get("sufficiency", 0.0))
            results["seeds"][f"seed_{seed}"]["faithfulness"] = faith

        except Exception as e:
            logger.error(f"Failed for {condition} seed={seed}: {e}")

    # Aggregate statistics
    if all_plausibilities:
        results["aggregated"]["plausibility"] = {
            "mean": float(np.mean(all_plausibilities)),
            "std": float(np.std(all_plausibilities)),
            "ci_95": bootstrap_confidence_interval(all_plausibilities, ci=0.95),
        }

    if all_faithfulness_comp:
        results["aggregated"]["faithfulness_comprehensiveness"] = {
            "mean": float(np.mean(all_faithfulness_comp)),
            "std": float(np.std(all_faithfulness_comp)),
            "ci_95": bootstrap_confidence_interval(all_faithfulness_comp, ci=0.95),
        }

    if all_faithfulness_suff:
        results["aggregated"]["faithfulness_sufficiency"] = {
            "mean": float(np.mean(all_faithfulness_suff)),
            "std": float(np.std(all_faithfulness_suff)),
            "ci_95": bootstrap_confidence_interval(all_faithfulness_suff, ci=0.95),
        }

    return results


def compute_comparative_statistics(metrics_by_condition: dict) -> dict:
    """Compute comparative statistics between conditions."""
    comparisons = {}

    # M4b vs M0 (primary comparison)
    m4b = metrics_by_condition.get("M4b", {}).get("aggregated", {}).get("plausibility", {})
    m0 = metrics_by_condition.get("M0", {}).get("aggregated", {}).get("plausibility", {})

    if m4b and m0:
        m4b_values = metrics_by_condition["M4b"]["seeds"].values()
        m0_values = metrics_by_condition["M0"]["seeds"].values()
        m4b_plaus = [v.get("plausibility", {}).get("iou_f1", 0.0) for v in m4b_values]
        m0_plaus = [v.get("plausibility", {}).get("iou_f1", 0.0) for v in m0_values]

        comparisons["M4b_vs_M0"] = {
            "cohens_d": float(cohens_d(np.array(m4b_plaus), np.array(m0_plaus))),
            "power_0.8": power_analysis(
                np.mean(m4b_plaus),
                np.mean(m0_plaus),
                np.std(m0_plaus),
                alpha=0.05,
                power=0.8,
            ),
        }

    return comparisons


def main() -> None:
    """Run Phase 4 statistical analysis."""
    output_dir = Path("outputs")
    phase4_dir = output_dir / "phase4"
    phase4_dir.mkdir(parents=True, exist_ok=True)

    conditions = ["M0", "M1", "M3", "M4b", "M2", "M4a", "M4c", "M5", "M6", "M7"]

    all_metrics = {}
    for condition in conditions:
        metrics = compute_metrics_for_condition(condition, output_dir)
        all_metrics[condition] = metrics

    # Compute comparisons
    comparisons = compute_comparative_statistics(all_metrics)

    results = {
        "by_condition": all_metrics,
        "comparisons": comparisons,
    }

    # Save results
    output_file = phase4_dir / "phase4_summary.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Phase 4 complete. Results saved to {output_file}")


if __name__ == "__main__":
    main()
