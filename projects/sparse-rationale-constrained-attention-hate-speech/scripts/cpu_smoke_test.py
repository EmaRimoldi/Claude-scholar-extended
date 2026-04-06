#!/usr/bin/env python3
"""Run a real training loop on CPU with minimal data to catch runtime errors.

This is NOT a unit test — it actually runs the training pipeline with:
  - max_steps=2 (2 training steps only)
  - batch_size=8 (small batch)
  - CPU only (no GPU)
  - Real data (small HateXplain subset)

If this passes, the actual GPU training will almost certainly work.

Exit 0 = code runs on CPU; non-zero = training loop has issues.
"""
import logging
import sys
import os
from pathlib import Path
from omegaconf import OmegaConf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set CPU-only mode
os.environ["CUDA_VISIBLE_DEVICES"] = ""

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def cpu_smoke_test_m0():
    """Run 2 training steps on CPU with M0 (baseline softmax)."""
    import torch
    from transformers import set_seed, AutoTokenizer, AutoConfig
    from src.data.dataset import HateXplainDataset, collate_fn
    from src.trainer.train import AlignmentTrainer, build_compute_metrics
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification
    from transformers import TrainingArguments, EarlyStoppingCallback

    logger.info("=== M0 CPU Smoke Test (max_steps=2) ===")

    set_seed(42)

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    # Load real datasets (small)
    train_dataset = HateXplainDataset("train", tokenizer, max_length=128, include_rationale=False)
    val_dataset = HateXplainDataset("validation", tokenizer, max_length=128, include_rationale=False)

    logger.info(f"Train dataset: {len(train_dataset)} samples")
    logger.info(f"Val dataset: {len(val_dataset)} samples")

    # Model: M0 baseline (no supervised heads, softmax)
    bert_config = AutoConfig.from_pretrained(
        "bert-base-uncased",
        num_labels=3,
        output_attentions=True,
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
    )
    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
    model = SparseBertForSequenceClassification.from_pretrained(
        "bert-base-uncased",
        config=bert_config,
        model_cfg=model_cfg,
        ignore_mismatched_sizes=True,
    )

    # Training arguments: CPU, max_steps=2, no fp16
    training_args = TrainingArguments(
        output_dir="/tmp/cpu_smoke_test_m0",
        num_train_epochs=1,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        learning_rate=2e-5,
        warmup_ratio=0.1,
        weight_decay=0.01,
        max_grad_norm=1.0,
        eval_strategy="steps",
        eval_steps=1,
        save_strategy="steps",
        save_steps=1,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        max_steps=2,  # Only 2 training steps
        report_to="none",
        dataloader_num_workers=0,
        remove_unused_columns=False,
        seed=42,
        # CPU mode (CUDA_VISIBLE_DEVICES="" already set in main)
    )

    # Trainer
    trainer = AlignmentTrainer(
        alignment_loss_fn=None,
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=collate_fn,
        compute_metrics=build_compute_metrics(tokenizer, val_dataset),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    # Run training
    logger.info("Starting 2-step training on CPU...")
    trainer.train()
    logger.info("✓ M0 CPU smoke test passed")


def main() -> int:
    """Run CPU smoke test."""
    logger.info("=" * 60)
    logger.info("CPU SMOKE TEST: Real training loop on CPU with minimal data")
    logger.info("=" * 60)

    try:
        cpu_smoke_test_m0()
        logger.info("=" * 60)
        logger.info("SUCCESS: Training loop works on CPU")
        logger.info("=" * 60)
        return 0
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"FAILED: {type(e).__name__}: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
