"""Training pipeline for SparseBertForSequenceClassification.

Wraps HuggingFace Trainer with alignment loss injection and custom metrics.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from torch import Tensor
from transformers import (
    AutoConfig,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainerCallback,
    TrainingArguments,
)
from transformers.trainer_utils import EvalPrediction

from src.data.dataset import HateXplainDataset, collate_fn
from src.evaluation.plausibility import compute_plausibility_metrics
from src.head_selection.importance import load_importance, rank_heads
from src.losses.alignment import build_alignment_loss
from src.model.bert_sparse import (
    SparseBertConfig,
    SparseBertForSequenceClassification,
    inject_sparsemax_attention,
)

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Full experiment configuration.

    Loaded from Hydra YAML; all fields must be serializable.
    """

    # Model
    pretrained_model_name: str = "bert-base-uncased"
    num_labels: int = 3
    dropout: float = 0.1

    # Head selection
    use_head_selection: bool = False
    top_k_heads: int = 6
    importance_scores_path: Optional[str] = None  # path to .pt file from Phase 1

    # Attention activation
    use_sparsemax: bool = True  # False = softmax (M0, M1, M2, M7)

    # Alignment loss
    use_alignment_loss: bool = True  # False = M0 (CE only)
    alignment_loss_type: str = "mse"  # "mse", "kl", "sparsemax"
    alignment_loss_weight: float = 0.1

    # Fixed heads (M1 SRA replication only)
    fixed_supervised_heads: list[tuple[int, int]] = field(default_factory=list)

    # Training
    seed: int = 42
    max_length: int = 128
    batch_size: int = 32
    learning_rate: float = 2e-5
    num_epochs: int = 5
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    output_dir: str = "outputs/run"

    # Evaluation
    eval_steps: int = 500
    save_steps: int = 500
    metric_for_best_model: str = "iou_f1"
    max_steps: int = -1  # -1 = use num_epochs; set >0 for quick smoke tests
    dataloader_num_workers: int = 4


class AlignmentTrainer(Trainer):
    """HuggingFace Trainer subclass that injects alignment loss.

    Overrides compute_loss to add the alignment loss term when
    rationale_mask is present in the batch.
    """

    def __init__(self, alignment_loss_fn: Optional[nn.Module] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.alignment_loss_fn = alignment_loss_fn

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        rationale_mask = inputs.pop("rationale_mask", None)
        inputs.pop("post_ids", None)
        labels = inputs.pop("labels", None)

        outputs = model(
            **inputs,
            rationale_mask=rationale_mask,
            labels=labels,
            alignment_loss_fn=self.alignment_loss_fn,
        )
        loss = outputs.loss
        return (loss, outputs) if return_outputs else loss


def build_model(cfg: ExperimentConfig) -> SparseBertForSequenceClassification:
    """Construct SparseBertForSequenceClassification from experiment config.

    Head selection priority:
    1. fixed_supervised_heads (M1 SRA replication)
    2. Gradient-importance top-k (M4a/b/c/M5/M6/M7)
    3. All heads in final layer (M2/M3)
    4. No supervised heads (M0)

    Args:
        cfg: ExperimentConfig.

    Returns:
        Initialized model (weights loaded from pretrained_model_name).
    """
    bert_config = AutoConfig.from_pretrained(
        cfg.pretrained_model_name,
        num_labels=cfg.num_labels,
        output_attentions=True,
        hidden_dropout_prob=cfg.dropout,
        attention_probs_dropout_prob=cfg.dropout,
    )

    # Determine supervised heads
    supervised_heads: list[tuple[int, int]] = []

    if cfg.fixed_supervised_heads:
        supervised_heads = cfg.fixed_supervised_heads
        logger.info(f"Using fixed supervised heads: {supervised_heads}")

    elif cfg.use_head_selection and cfg.importance_scores_path:
        importance = load_importance(cfg.importance_scores_path)
        supervised_heads = rank_heads(importance, top_k=cfg.top_k_heads)
        logger.info(f"Top-{cfg.top_k_heads} supervised heads: {supervised_heads}")

    elif not cfg.use_head_selection and cfg.use_alignment_loss:
        # M2/M3: supervise all 12 heads in the final layer (layer 11)
        supervised_heads = [(11, h) for h in range(12)]
        logger.info("Supervising all 12 heads in layer 11")

    model_cfg = SparseBertConfig(
        pretrained_model_name=cfg.pretrained_model_name,
        num_labels=cfg.num_labels,
        supervised_heads=supervised_heads,
        alignment_loss_weight=cfg.alignment_loss_weight,
        dropout=cfg.dropout,
    )

    model = SparseBertForSequenceClassification.from_pretrained(
        cfg.pretrained_model_name,
        config=bert_config,
        model_cfg=model_cfg,
        ignore_mismatched_sizes=True,
    )

    if cfg.use_sparsemax and supervised_heads:
        model = inject_sparsemax_attention(model, supervised_heads)
        logger.info("Injected sparsemax attention in supervised heads")

    return model


def build_compute_metrics(tokenizer, eval_dataset):
    """Build the compute_metrics function for Trainer evaluation."""
    import numpy as np
    from sklearn.metrics import f1_score

    def compute_metrics(eval_pred: EvalPrediction) -> dict:
        logits, labels = eval_pred.predictions, eval_pred.label_ids
        preds = np.argmax(logits, axis=-1)
        macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
        accuracy = (preds == labels).mean()
        return {"macro_f1": float(macro_f1), "accuracy": float(accuracy)}

    return compute_metrics


def run_training(cfg: ExperimentConfig) -> None:
    """Run full training pipeline for one experimental condition.

    Args:
        cfg: ExperimentConfig loaded from Hydra.
    """
    # Set seed
    from transformers import set_seed
    set_seed(cfg.seed)

    logger.info(f"Starting training: seed={cfg.seed}, output_dir={cfg.output_dir}")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(cfg.pretrained_model_name)

    # Datasets
    include_rationale = cfg.use_alignment_loss
    train_dataset = HateXplainDataset(
        "train", tokenizer, max_length=cfg.max_length, include_rationale=include_rationale
    )
    val_dataset = HateXplainDataset(
        "validation", tokenizer, max_length=cfg.max_length, include_rationale=include_rationale
    )

    # Model
    model = build_model(cfg)

    # Alignment loss
    alignment_loss_fn = None
    if cfg.use_alignment_loss:
        alignment_loss_fn = build_alignment_loss(cfg.alignment_loss_type)
        logger.info(f"Alignment loss: {cfg.alignment_loss_type}, weight={cfg.alignment_loss_weight}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.num_epochs,
        per_device_train_batch_size=cfg.batch_size,
        per_device_eval_batch_size=cfg.batch_size,
        learning_rate=cfg.learning_rate,
        warmup_ratio=cfg.warmup_ratio,
        weight_decay=cfg.weight_decay,
        max_grad_norm=cfg.max_grad_norm,
        eval_strategy="steps",
        eval_steps=cfg.eval_steps,
        save_strategy="steps",
        save_steps=cfg.save_steps,
        load_best_model_at_end=True,
        metric_for_best_model=cfg.metric_for_best_model,
        greater_is_better=True,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        seed=cfg.seed,
        max_steps=cfg.max_steps,
        report_to="none",
        dataloader_num_workers=cfg.dataloader_num_workers,
        remove_unused_columns=False,
    )

    trainer = AlignmentTrainer(
        alignment_loss_fn=alignment_loss_fn,
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=collate_fn,
        compute_metrics=build_compute_metrics(tokenizer, val_dataset),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    trainer.train()
    trainer.save_model(os.path.join(cfg.output_dir, "best_model"))
    logger.info(f"Training complete. Best model saved to {cfg.output_dir}/best_model")
