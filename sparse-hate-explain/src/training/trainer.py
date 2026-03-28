"""Training loop with mixed-precision, early stopping, and checkpoint saving."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from omegaconf import DictConfig
from torch.optim import Optimizer
from torch.optim.lr_scheduler import LRScheduler
from torch.utils.data import DataLoader

from src.metrics.classification import compute_classification_metrics

logger = logging.getLogger(__name__)


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        optimizer: Optimizer,
        scheduler: LRScheduler,
        cfg: DictConfig,
        device: torch.device,
    ) -> None:
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.cfg = cfg
        self.device = device

        self.num_epochs: int = cfg.training.num_epochs
        self.max_grad_norm: float = cfg.training.get("max_grad_norm", 1.0)
        self.patience: int = cfg.training.get("patience", 3)

        self.scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))
        self.best_val_f1: float = 0.0
        self.epochs_no_improve: int = 0
        self.history: list[Dict[str, Any]] = []

        self.output_dir = Path(cfg.get("output_dir", "."))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def train_epoch(self) -> Dict[str, float]:
        self.model.train()
        total_loss = total_ce = total_attn = 0.0
        n_batches = 0

        for batch in self.train_loader:
            batch = {k: v.to(self.device) for k, v in batch.items()}
            self.optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast("cuda", enabled=(self.device.type == "cuda")):
                outputs = self.model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"],
                    rationale_mask=batch["rationale_mask"],
                )
                loss = outputs.loss

            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
            self.scaler.step(self.optimizer)
            self.scaler.update()
            self.scheduler.step()

            total_loss += loss.item()
            total_ce += outputs.ce_loss.item()
            total_attn += outputs.attn_loss.item()
            n_batches += 1

        d = max(n_batches, 1)
        return {"train_loss": total_loss / d, "train_ce_loss": total_ce / d, "train_attn_loss": total_attn / d}

    @torch.no_grad()
    def validate(self) -> Tuple[float, Dict[str, Any]]:
        self.model.eval()
        total_loss = 0.0
        n_batches = 0
        all_preds: list[int] = []
        all_labels: list[int] = []

        for batch in self.val_loader:
            batch = {k: v.to(self.device) for k, v in batch.items()}
            with torch.amp.autocast("cuda", enabled=(self.device.type == "cuda")):
                outputs = self.model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"],
                    rationale_mask=batch["rationale_mask"],
                )
            total_loss += outputs.loss.item()
            n_batches += 1
            all_preds.extend(outputs.logits.argmax(dim=-1).cpu().tolist())
            all_labels.extend(batch["labels"].cpu().tolist())

        val_loss = total_loss / max(n_batches, 1)
        metrics = compute_classification_metrics(np.array(all_preds), np.array(all_labels))
        return val_loss, metrics

    def train(self) -> Dict[str, Any]:
        logger.info("Training for %d epochs (patience=%d)", self.num_epochs, self.patience)

        for epoch in range(1, self.num_epochs + 1):
            t0 = time.time()
            train_metrics = self.train_epoch()
            val_loss, val_metrics = self.validate()
            elapsed = time.time() - t0

            record = {
                "epoch": epoch, **train_metrics,
                "val_loss": val_loss, "val_macro_f1": val_metrics["macro_f1"],
                "val_accuracy": val_metrics["accuracy"], "lr": self.optimizer.param_groups[0]["lr"],
                "elapsed_s": round(elapsed, 1),
            }
            self.history.append(record)

            logger.info(
                "Epoch %d/%d | loss=%.4f (ce=%.4f attn=%.4f) | val_loss=%.4f | F1=%.4f | acc=%.4f | %.1fs",
                epoch, self.num_epochs,
                train_metrics["train_loss"], train_metrics["train_ce_loss"], train_metrics["train_attn_loss"],
                val_loss, val_metrics["macro_f1"], val_metrics["accuracy"], elapsed,
            )

            if val_metrics["macro_f1"] > self.best_val_f1:
                self.best_val_f1 = val_metrics["macro_f1"]
                self.epochs_no_improve = 0
                self._save_checkpoint(epoch, val_metrics)
                logger.info("  -> New best val F1: %.4f", self.best_val_f1)
            else:
                self.epochs_no_improve += 1
                if self.epochs_no_improve >= self.patience:
                    logger.info("Early stopping after %d epochs without improvement.", self.patience)
                    break

        history_path = self.output_dir / "training_history.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)
        return {"history": self.history, "best_val_f1": self.best_val_f1}

    def _save_checkpoint(self, epoch: int, metrics: Dict[str, Any]) -> None:
        torch.save({
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "best_val_f1": self.best_val_f1,
            "metrics": metrics,
        }, self.output_dir / "best_model.pt")

    def load_checkpoint(self, path: Optional[str] = None) -> Dict[str, Any]:
        ckpt_path = Path(path) if path else self.output_dir / "best_model.pt"
        checkpoint = torch.load(ckpt_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.best_val_f1 = checkpoint["best_val_f1"]
        logger.info("Loaded checkpoint (epoch %d, F1=%.4f)", checkpoint["epoch"], checkpoint["best_val_f1"])
        return checkpoint
