"""Entry point for sparse-hate-explain experiments.

Usage:
    python -m src.main                                 # default config
    python -m src.main +experiment=sparsemax_topk       # experiment override
    python -m src.main mode=evaluate checkpoint=path/to/best_model.pt
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from torch.optim import AdamW
from torch.optim.lr_scheduler import LinearLR
from torch.utils.data import DataLoader

from src.data import build_dataloaders
from src.metrics.classification import compute_classification_metrics
from src.models.bert_sparse import BertSparseForClassification
from src.models.head_importance import compute_head_importance, select_top_k_heads
from src.training import Trainer
from src.utils import set_seed

logger = logging.getLogger(__name__)


def _build_model(cfg: DictConfig, device: torch.device) -> BertSparseForClassification:
    supervised_heads = cfg.model.get("supervised_heads", "all")
    if isinstance(supervised_heads, str) and supervised_heads != "all":
        # Load from head importance results file
        hi_path = Path(cfg.model.get("head_importance_path", "results/head_importance/head_importance.json"))
        if hi_path.exists():
            with open(hi_path) as f:
                hi_data = json.load(f)
            importance = {}
            for layer_idx, row in enumerate(hi_data["head_importance"]):
                for head_idx, score in enumerate(row):
                    importance[(layer_idx, head_idx)] = score
            top_k = cfg.model.get("top_k", 24)
            supervised_heads = select_top_k_heads(importance, top_k)
            logger.info("Selected top-%d heads from %s", top_k, hi_path)
        else:
            logger.warning("Head importance file not found at %s, using all heads", hi_path)
            supervised_heads = "all"

    model = BertSparseForClassification(
        model_name=cfg.model.get("model_name", "bert-base-uncased"),
        num_labels=cfg.model.get("num_labels", 3),
        supervised_heads=supervised_heads,
        attention_transform=cfg.model.get("attention_transform", "softmax"),
        lambda_attn=cfg.model.get("lambda_attn", 0.0),
    )
    return model.to(device)


def _build_optimizer(model: torch.nn.Module, cfg: DictConfig) -> AdamW:
    return AdamW(
        model.parameters(),
        lr=cfg.training.learning_rate,
        weight_decay=cfg.training.weight_decay,
    )


def _build_scheduler(optimizer: AdamW, cfg: DictConfig, num_training_steps: int) -> LinearLR:
    warmup_steps = int(cfg.training.get("warmup_ratio", 0.1) * num_training_steps)
    start_factor = max(1e-7 / max(cfg.training.learning_rate, 1e-12), 1e-7)
    start_factor = min(start_factor, 1.0)
    return LinearLR(optimizer, start_factor=start_factor, end_factor=1.0, total_iters=max(warmup_steps, 1))


def _run_train(cfg: DictConfig, train_loader: DataLoader, val_loader: DataLoader,
               test_loader: DataLoader, device: torch.device) -> None:
    model = _build_model(cfg, device)
    optimizer = _build_optimizer(model, cfg)
    num_training_steps = len(train_loader) * cfg.training.num_epochs
    scheduler = _build_scheduler(optimizer, cfg, num_training_steps)

    trainer = Trainer(
        model=model, train_loader=train_loader, val_loader=val_loader,
        optimizer=optimizer, scheduler=scheduler, cfg=cfg, device=device,
    )

    train_result = trainer.train()

    # Load best checkpoint and evaluate on test set.
    trainer.load_checkpoint()
    original_loader = trainer.val_loader
    trainer.val_loader = test_loader
    test_loss, test_metrics = trainer.validate()
    trainer.val_loader = original_loader

    results = {
        "best_val_f1": train_result["best_val_f1"],
        "test_loss": test_loss,
        "test_metrics": test_metrics,
        "config": OmegaConf.to_container(cfg, resolve=True),
    }

    output_dir = Path(cfg.get("output_dir", "."))
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Test macro-F1: %.4f | accuracy: %.4f", test_metrics["macro_f1"], test_metrics["accuracy"])


def _run_evaluate(cfg: DictConfig, test_loader: DataLoader, device: torch.device) -> None:
    checkpoint_path = cfg.get("checkpoint", None)
    if checkpoint_path is None:
        raise ValueError("Must specify checkpoint=<path> for evaluate mode.")

    model = _build_model(cfg, device)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    all_preds, all_labels = [], []
    total_loss, n_batches = 0.0, 0

    with torch.no_grad():
        for batch in test_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                outputs = model(
                    input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                    labels=batch["labels"], rationale_mask=batch["rationale_mask"],
                )
            total_loss += outputs.loss.item()
            n_batches += 1
            all_preds.extend(outputs.logits.argmax(dim=-1).cpu().tolist())
            all_labels.extend(batch["labels"].cpu().tolist())

    metrics = compute_classification_metrics(np.array(all_preds), np.array(all_labels))
    output_dir = Path(cfg.get("output_dir", "."))
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "eval_results.json"
    with open(results_path, "w") as f:
        json.dump({"test_loss": total_loss / max(n_batches, 1), "test_metrics": metrics}, f, indent=2, default=str)
    logger.info("Test macro-F1: %.4f | accuracy: %.4f", metrics["macro_f1"], metrics["accuracy"])


def _run_head_importance(cfg: DictConfig, val_loader: DataLoader, device: torch.device) -> None:
    # Use vanilla model (lambda_attn=0) for head importance
    checkpoint_path = cfg.get("checkpoint", None)
    model = _build_model(cfg, device)
    if checkpoint_path:
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])

    importance = compute_head_importance(model, val_loader, device)

    # Convert to serializable format
    n_layers = model.config.num_hidden_layers
    n_heads = model.config.num_attention_heads
    importance_matrix = [[0.0] * n_heads for _ in range(n_layers)]
    for (layer, head), score in importance.items():
        importance_matrix[layer][head] = score

    output_dir = Path(cfg.get("output_dir", "."))
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {
        "head_importance": importance_matrix,
        "top_12": [list(h) for h in select_top_k_heads(importance, 12)],
        "top_24": [list(h) for h in select_top_k_heads(importance, 24)],
        "top_36": [list(h) for h in select_top_k_heads(importance, 36)],
        "num_samples": len(val_loader.dataset),
    }
    results_path = output_dir / "head_importance.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info("Head importance saved to %s", results_path)


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    logger.info("Configuration:\n%s", OmegaConf.to_yaml(cfg))

    set_seed(cfg.get("seed", 42))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    mode = cfg.get("mode", "train")
    if mode == "train":
        train_loader, val_loader, test_loader = build_dataloaders(cfg)
        _run_train(cfg, train_loader, val_loader, test_loader, device)
    elif mode == "evaluate":
        _, _, test_loader = build_dataloaders(cfg)
        _run_evaluate(cfg, test_loader, device)
    elif mode == "head_importance":
        _, val_loader, _ = build_dataloaders(cfg)
        _run_head_importance(cfg, val_loader, device)
    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
