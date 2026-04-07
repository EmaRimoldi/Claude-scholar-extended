"""Training loop for hate speech classifier with optional alignment supervision.

Handles all 5 conditions (C1-C5) through a unified interface:
- C1: CE loss only (softmax, no supervision)
- C2: CE + KL alignment (SRA replication)
- C3: CE only (sparsemax, no supervision — C3-unsup)
- C4: CE + MSE alignment all-12-heads (primary)
- C5: CE + MSE alignment top-6-heads (H3)
"""
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
from torch import Tensor
from torch.optim import AdamW
from torch.optim.lr_scheduler import LinearLR, SequentialLR
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup

from ..model_module.bert_classifier import BertHateSpeechClassifier
from ..model_module.losses import JointLoss, KLAlignmentLoss, MSEAlignmentLoss

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training hyperparameters.

    Args:
        learning_rate: AdamW initial LR.
        weight_decay: AdamW weight decay.
        num_epochs: Maximum training epochs.
        warmup_ratio: Fraction of total steps used for linear warmup.
        alpha: Alignment loss weight (0 = classification only).
        use_kl_loss: True = KL alignment (SRA); False = MSE alignment (ours).
        output_dir: Directory to save checkpoints.
        seed: Random seed for this run.
        device: 'cuda' or 'cpu'.
        eval_strategy: 'epoch' or 'steps'.
        early_stop_patience: Stop if val macro-F1 doesn't improve for N epochs.
    """

    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    num_epochs: int = 5
    warmup_ratio: float = 0.1
    alpha: float = 0.3
    use_kl_loss: bool = False
    output_dir: str = "checkpoints"
    seed: int = 42
    device: str = "cuda"
    eval_strategy: str = "epoch"
    early_stop_patience: int = 3


class Trainer:
    """Unified trainer for all conditions.

    Args:
        model: BertHateSpeechClassifier instance.
        train_loader: Training DataLoader.
        val_loader: Validation DataLoader.
        cfg: TrainingConfig.
    """

    def __init__(
        self,
        model: BertHateSpeechClassifier,
        train_loader: DataLoader,
        val_loader: DataLoader,
        cfg: TrainingConfig,
    ) -> None:
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.cfg = cfg
        self.device = torch.device(cfg.device if torch.cuda.is_available() else "cpu")

        self.model.to(self.device)

        # Set up loss function
        if cfg.alpha > 0:
            align_loss = KLAlignmentLoss() if cfg.use_kl_loss else MSEAlignmentLoss()
            self.loss_fn = JointLoss(align_loss, alpha=cfg.alpha)
        else:
            self.loss_fn = None  # CE only

        self.ce = nn.CrossEntropyLoss()

        # Optimizer and scheduler
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
        )
        total_steps = len(train_loader) * cfg.num_epochs
        warmup_steps = int(total_steps * cfg.warmup_ratio)
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        self.best_val_f1 = 0.0
        self.epochs_without_improvement = 0

        os.makedirs(cfg.output_dir, exist_ok=True)
        logger.info(
            f"Trainer initialized: device={self.device}, "
            f"alpha={cfg.alpha}, use_kl={cfg.use_kl_loss}, seed={cfg.seed}"
        )

    def train(self) -> dict[str, list[float]]:
        """Run full training loop.

        Returns:
            History dict with train_loss, val_f1 per epoch.
        """
        history: dict[str, list[float]] = {"train_loss": [], "val_f1": []}

        for epoch in range(self.cfg.num_epochs):
            train_loss = self._train_epoch(epoch)
            val_metrics = self._evaluate(self.val_loader)
            val_f1 = val_metrics["macro_f1"]

            history["train_loss"].append(train_loss)
            history["val_f1"].append(val_f1)

            logger.info(
                f"Epoch {epoch+1}/{self.cfg.num_epochs} | "
                f"train_loss={train_loss:.4f} | val_f1={val_f1:.4f}"
            )

            # Save best model
            if val_f1 > self.best_val_f1:
                self.best_val_f1 = val_f1
                self.epochs_without_improvement = 0
                self._save_checkpoint(epoch, val_f1, "best_model.pt")
            else:
                self.epochs_without_improvement += 1

            if self.epochs_without_improvement >= self.cfg.early_stop_patience:
                logger.info(f"Early stop at epoch {epoch+1} (no F1 improvement for {self.cfg.early_stop_patience} epochs)")
                break

        return history

    def _train_epoch(self, epoch: int) -> float:
        """Run a single training epoch."""
        self.model.train()
        total_loss = 0.0

        for batch in self.train_loader:
            input_ids = batch["input_ids"].to(self.device)
            attn_mask = batch["attention_mask"].to(self.device)
            token_type_ids = batch["token_type_ids"].to(self.device)
            labels = batch["labels"].to(self.device)
            rationale_mask = batch["rationale_mask"].to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attn_mask,
                token_type_ids=token_type_ids,
            )
            logits = outputs["logits"]
            cls_attention = outputs["cls_attention"]

            if self.loss_fn is not None and cls_attention is not None:
                loss, ce_loss, align_loss = self.loss_fn(
                    logits, labels, cls_attention, rationale_mask
                )
            else:
                loss = self.ce(logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            self.scheduler.step()
            total_loss += loss.item()

        return total_loss / len(self.train_loader)

    def _evaluate(self, loader: DataLoader) -> dict[str, float]:
        """Evaluate on a DataLoader; return macro-F1 and accuracy."""
        from sklearn.metrics import f1_score  # type: ignore

        self.model.eval()
        all_preds: list[int] = []
        all_labels: list[int] = []

        with torch.no_grad():
            for batch in loader:
                input_ids = batch["input_ids"].to(self.device)
                attn_mask = batch["attention_mask"].to(self.device)
                token_type_ids = batch["token_type_ids"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attn_mask,
                    token_type_ids=token_type_ids,
                )
                preds = outputs["logits"].argmax(dim=-1)
                all_preds.extend(preds.cpu().tolist())
                all_labels.extend(labels.cpu().tolist())

        macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        accuracy = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)
        return {"macro_f1": macro_f1, "accuracy": accuracy}

    def _save_checkpoint(self, epoch: int, val_f1: float, filename: str) -> None:
        """Save model checkpoint with metadata."""
        path = os.path.join(self.cfg.output_dir, filename)
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "val_f1": val_f1,
                "config": self.cfg,
            },
            path,
        )
        logger.info(f"Checkpoint saved: {path} (val_f1={val_f1:.4f})")
