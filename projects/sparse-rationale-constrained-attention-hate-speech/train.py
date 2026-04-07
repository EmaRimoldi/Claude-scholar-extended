"""Main training entry point for sparse-rationale-constrained-attention experiments.

Supports all conditions C1-C5 via Hydra configuration.

Usage:
    python train.py                          # C4 (sparsemax primary, seed=42)
    python train.py model=bert_softmax_sra   # C2 (SRA replication)
    python train.py seed=43 condition=C4     # different seed
    python train.py -m seed=42,43,44,45,46  # sweep 5 seeds
"""
import logging
import os
import sys

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

# Allow importing from src/
sys.path.insert(0, os.path.dirname(__file__))

from src.utils.seed import set_seed

logger = logging.getLogger(__name__)


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main training function.

    Args:
        cfg: Hydra configuration composed from configs/.
    """
    logger.info(f"Starting experiment: condition={cfg.condition}, seed={cfg.seed}")
    logger.info(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    set_seed(cfg.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")

    # ---- Data loading ----
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(cfg.model.model_name)

    from src.data_module.dataset import HateXplainDataset
    from src.data_module.loader import load_jsonl

    data_dir = cfg.data.get("data_dir", "data/hatexplain")
    train_examples = load_jsonl(os.path.join(data_dir, "train.jsonl"))
    val_examples = load_jsonl(os.path.join(data_dir, "validation.jsonl"))

    train_dataset = HateXplainDataset(train_examples, tokenizer, cfg.data.max_length)
    val_dataset = HateXplainDataset(val_examples, tokenizer, cfg.data.max_length)

    from torch.utils.data import DataLoader

    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg.data.batch_size,
        shuffle=True,
        num_workers=cfg.data.num_workers,
        pin_memory=(device == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=cfg.data.batch_size,
        shuffle=False,
        num_workers=cfg.data.num_workers,
        pin_memory=(device == "cuda"),
    )

    # ---- Model ----
    from src.model_module.bert_classifier import BertHateSpeechClassifier, ClassifierConfig

    model_cfg = ClassifierConfig(
        model_name=cfg.model.model_name,
        use_sparsemax=cfg.model.use_sparsemax,
        supervised_heads=list(cfg.model.supervised_heads) if cfg.model.supervised_heads else None,
        alpha=cfg.model.alpha,
        use_kl_loss=cfg.model.use_kl_loss,
        num_labels=cfg.model.num_labels,
        dropout=cfg.model.dropout,
    )
    model = BertHateSpeechClassifier(model_cfg)

    # ---- Training ----
    from src.trainer_module.trainer import Trainer, TrainingConfig

    train_cfg = TrainingConfig(
        learning_rate=cfg.training.learning_rate,
        weight_decay=cfg.training.weight_decay,
        num_epochs=cfg.training.num_epochs,
        warmup_ratio=cfg.training.warmup_ratio,
        alpha=cfg.model.alpha,
        use_kl_loss=cfg.model.use_kl_loss,
        output_dir=os.path.join(cfg.training.output_dir, f"cond_{cfg.condition}_seed_{cfg.seed}"),
        seed=cfg.seed,
        device=device,
        eval_strategy=cfg.training.eval_strategy,
        early_stop_patience=cfg.training.early_stop_patience,
    )

    trainer = Trainer(model, train_loader, val_loader, train_cfg)
    history = trainer.train()

    logger.info(f"Training complete. Best val_f1={trainer.best_val_f1:.4f}")

    # Save run summary
    import json
    summary = {
        "condition": cfg.condition,
        "seed": cfg.seed,
        "best_val_f1": trainer.best_val_f1,
        "history": history,
        "config": OmegaConf.to_container(cfg),
    }
    summary_path = os.path.join(train_cfg.output_dir, "run_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    main()
