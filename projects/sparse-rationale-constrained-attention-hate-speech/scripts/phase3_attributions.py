#!/usr/bin/env python3
"""Phase 3: Attribution analysis (IG, LIME, stability).

Requires: All trained models from Phase 2.
Outputs: Attribution results + agreement metrics.
"""
import json
import logging
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from src.data.dataset import HateXplainDataset, collate_fn
from src.evaluation.attribution import compute_integrated_gradients, compute_lime
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

    # Load config and model
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


def compute_attributions(condition: str, seed: int, output_dir: Path) -> dict:
    """Compute IG and LIME attributions for one condition/seed."""
    results = {}

    logger.info(f"Loading model: {condition} seed={seed}")
    model = load_trained_model(condition, seed, output_dir)

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

    # Compute IG
    logger.info(f"  Computing Integrated Gradients...")
    try:
        ig_results = compute_integrated_gradients(
            model,
            val_loader,
            tokenizer,
            device="cuda" if torch.cuda.is_available() else "cpu",
            n_steps=50,
        )
        results["integrated_gradients"] = ig_results
    except Exception as e:
        logger.error(f"  IG failed: {e}")

    # Compute LIME
    logger.info(f"  Computing LIME attributions...")
    try:
        lime_results = compute_lime(
            model,
            val_loader,
            tokenizer,
            device="cuda" if torch.cuda.is_available() else "cpu",
            num_samples=1000,
        )
        results["lime"] = lime_results
    except Exception as e:
        logger.error(f"  LIME failed: {e}")

    return results


def main() -> None:
    """Run Phase 3 attribution analysis."""
    output_dir = Path("outputs")
    phase3_dir = output_dir / "phase3"
    phase3_dir.mkdir(parents=True, exist_ok=True)

    conditions = ["M0", "M1", "M3", "M4b", "M2", "M4a", "M4c", "M5", "M6", "M7"]
    seeds = [42, 43, 44]

    all_results = {}

    for condition in conditions:
        cond_results = {}
        for seed in seeds:
            try:
                results = compute_attributions(condition, seed, output_dir)
                cond_results[f"seed_{seed}"] = results
            except Exception as e:
                logger.error(f"Failed for {condition} seed={seed}: {e}")

        all_results[condition] = cond_results

    # Save results
    output_file = phase3_dir / "phase3_summary.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    logger.info(f"Phase 3 complete. Results saved to {output_file}")


if __name__ == "__main__":
    main()
