"""Phase 1: gradient-based head importance scoring.

Loads an M0 checkpoint (or trains a fresh M0 for importance scoring),
then computes I(h,l) = E_x[|∂L_CE/∂A^{CLS,h,l}|] over the training set.

Gate G1: head importance variance > 0.01 (heads are not uniformly important).

Run: python scripts/phase1_head_importance.py [--checkpoint path/to/m0]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=None, help="Path to M0 checkpoint.")
    parser.add_argument("--max_batches", type=int, default=200)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoConfig, AutoTokenizer

    from src.data.dataset import HateXplainDataset, collate_fn
    from src.head_selection.importance import (
        compute_head_importance,
        rank_heads,
        save_importance,
    )
    from src.model.bert_sparse import (
        SparseBertConfig,
        SparseBertForSequenceClassification,
    )

    output_dir = Path("outputs/phase1")
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    train_dataset = HateXplainDataset(
        "train", tokenizer, max_length=128, include_rationale=False
    )
    dataloader = DataLoader(
        train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn, num_workers=4
    )

    # Instantiate directly in both branches to avoid transformers>=4.40 passing
    # model_cfg both positionally and as a keyword (causes "multiple values" TypeError).
    import torch
    from transformers import BertForSequenceClassification

    model_cfg = SparseBertConfig(supervised_heads=[])

    if args.checkpoint:
        logger.info(f"Loading M0 checkpoint from {args.checkpoint}")
        bert_config = AutoConfig.from_pretrained(args.checkpoint, output_attentions=True)
        model = SparseBertForSequenceClassification(bert_config, model_cfg)
        ckpt_path = Path(args.checkpoint)
        safetensor_path = ckpt_path / "model.safetensors"
        bin_path = ckpt_path / "pytorch_model.bin"
        if safetensor_path.exists():
            from safetensors.torch import load_file
            state_dict = load_file(safetensor_path, device="cpu")
        else:
            state_dict = torch.load(bin_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict, strict=False)
    else:
        logger.info("No checkpoint provided. Using pretrained bert-base-uncased for importance scoring.")
        bert_config = AutoConfig.from_pretrained(
            "bert-base-uncased", num_labels=3, output_attentions=True
        )
        model = SparseBertForSequenceClassification(bert_config, model_cfg)
        # Bootstrap BERT backbone from HF hub via a standard model to avoid the
        # custom-kwarg collision in from_pretrained; strict=False ignores the
        # classification head shape mismatch.
        tmp = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=3)
        model.load_state_dict(tmp.state_dict(), strict=False)
        del tmp

    logger.info("Computing head importance scores...")
    importance = compute_head_importance(
        model=model,
        dataloader=dataloader,
        num_layers=12,
        num_heads=12,
        device=args.device,
        max_batches=args.max_batches,
    )

    save_importance(importance, output_dir / "importance_scores.pt")

    # Gate G1 check
    variance = float(importance.var().item())
    gate_pass = variance > 0.01

    # Rank heads for different k values
    top3 = rank_heads(importance, top_k=3)
    top6 = rank_heads(importance, top_k=6)
    top9 = rank_heads(importance, top_k=9)

    logger.info(f"\n{'='*60}")
    logger.info(f"GATE G1: {'PASS' if gate_pass else 'FAIL'}")
    logger.info(f"  Importance variance: {variance:.4f} (criterion: > 0.01)")
    logger.info(f"  Top-3 heads: {top3}")
    logger.info(f"  Top-6 heads: {top6}")
    logger.info(f"  Top-9 heads: {top9}")
    logger.info(f"{'='*60}")

    summary = {
        "gate_g1": "PASS" if gate_pass else "FAIL",
        "importance_variance": variance,
        "top3_heads": top3,
        "top6_heads": top6,
        "top9_heads": top9,
        "importance_scores_path": str(output_dir / "importance_scores.pt"),
    }
    with open(output_dir / "phase1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    if not gate_pass:
        logger.error("Gate G1 FAILED. Head importance variance is too low.")
        sys.exit(1)
    logger.info("Gate G1 PASSED. Proceed to Phase 2 training.")


if __name__ == "__main__":
    main()
