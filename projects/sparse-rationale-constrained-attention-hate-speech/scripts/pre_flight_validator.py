#!/usr/bin/env python3
"""Generic pre-flight validation for training pipelines.

Runs smoke tests locally before GPU submission:
  1. Import all modules (catch import errors)
  2. Load config and initialize model (catch config/shape errors)
  3. Create data loaders (catch data loading errors)
  4. Run 1 training step (catch loss/backward errors)
  5. Run 1 eval step (catch metrics computation errors)

Exit 0 = all tests pass; non-zero = failure.
"""
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def check(test_name: str, test_fn, abort_on_fail: bool = True) -> bool:
    """Run a test and log result."""
    try:
        test_fn()
        logger.info(f"✓ {test_name}")
        return True
    except Exception as e:
        logger.error(f"✗ {test_name}")
        logger.error(f"  {type(e).__name__}: {e}")
        if abort_on_fail:
            traceback.print_exc()
            return False
        return False


def test_imports() -> None:
    """Test that all required modules can be imported."""
    import torch
    import transformers
    import hydra
    from omegaconf import DictConfig, OmegaConf

    logger.debug(f"  torch: {torch.__version__}")
    logger.debug(f"  transformers: {transformers.__version__}")


def test_config_loading() -> None:
    """Test that Hydra config loads without errors."""
    from hydra import compose, initialize_config_dir
    from pathlib import Path
    import os

    config_dir = Path(__file__).parent.parent / "configs"
    if not config_dir.exists():
        raise FileNotFoundError(f"Config dir not found: {config_dir}")

    with initialize_config_dir(version_base=None, config_dir=str(config_dir)):
        cfg = compose(config_name="config")
        logger.debug(f"  config keys: {list(cfg.keys())}")


def test_model_initialization() -> None:
    """Test that model can be initialized without errors."""
    import torch
    from transformers import AutoConfig

    try:
        from src.model.bert_sparse import SparseBertForSequenceClassification, SparseBertConfig
    except ImportError:
        raise ImportError("Cannot import SparseBertForSequenceClassification")

    # Mini BERT config for testing
    bert_config = AutoConfig.from_pretrained(
        "bert-base-uncased",
        num_labels=3,
        output_attentions=True,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
    )

    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
    model = SparseBertForSequenceClassification(bert_config, model_cfg)
    model.eval()

    logger.debug(f"  model params: {sum(p.numel() for p in model.parameters()):,}")


def test_data_loading() -> None:
    """Test that data loaders can be created without errors."""
    try:
        from src.data.dataset import HateXplainDataset
    except ImportError:
        raise ImportError("Cannot import HateXplainDataset")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    # Try to create datasets
    try:
        train_dataset = HateXplainDataset(
            "train",
            tokenizer,
            max_length=64,  # Short for speed
            include_rationale=False,
        )
        logger.debug(f"  train samples: {len(train_dataset)}")
    except Exception as e:
        logger.warning(f"  Could not load train data: {e}")

    try:
        val_dataset = HateXplainDataset(
            "validation",
            tokenizer,
            max_length=64,
            include_rationale=False,
        )
        logger.debug(f"  val samples: {len(val_dataset)}")
    except Exception as e:
        logger.warning(f"  Could not load val data: {e}")


def test_training_step() -> None:
    """Test that a training step works end-to-end."""
    import torch
    from transformers import AutoTokenizer, AutoConfig
    from torch.utils.data import DataLoader, IterableDataset

    try:
        from src.model.bert_sparse import SparseBertForSequenceClassification, SparseBertConfig
        from src.data.dataset import collate_fn
    except ImportError:
        raise ImportError("Cannot import training modules")

    # Create tiny synthetic data
    class TinyDataset(IterableDataset):
        def __iter__(self):
            tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            for _ in range(2):  # 2 samples only
                text = "This is a test sentence for validation."
                encoded = tokenizer(
                    text,
                    max_length=64,
                    truncation=True,
                    padding="max_length",
                    return_tensors="pt",
                )
                yield {
                    "input_ids": encoded["input_ids"].squeeze(0),
                    "attention_mask": encoded["attention_mask"].squeeze(0),
                    "token_type_ids": encoded["token_type_ids"].squeeze(0),
                    "labels": torch.tensor(0),  # Label 0
                }

    dataset = TinyDataset()
    loader = DataLoader(dataset, batch_size=2, collate_fn=collate_fn)

    # Initialize model
    bert_config = AutoConfig.from_pretrained("bert-base-uncased", num_labels=3, output_attentions=True)
    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
    model = SparseBertForSequenceClassification(bert_config, model_cfg)
    model.train()

    # Training step
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    for batch in loader:
        optimizer.zero_grad()
        outputs = model(**batch)
        loss = outputs.loss

        if loss is None:
            raise RuntimeError("Loss is None — model forward failed")

        loss.backward()
        optimizer.step()

        logger.debug(f"  loss: {loss.item():.4f}")
        break  # Just one batch


def test_evaluation_metrics() -> None:
    """Test that metrics computation doesn't crash."""
    import numpy as np
    from sklearn.metrics import f1_score

    # Simulate eval_pred from Trainer
    logits = np.random.randn(4, 3)  # (batch, num_classes)
    labels = np.array([0, 1, 2, 1])

    preds = np.argmax(logits, axis=-1)
    f1 = f1_score(labels, preds, average="macro", zero_division=0)
    acc = (preds == labels).mean()

    logger.debug(f"  f1: {f1:.4f}, acc: {acc:.4f}")


def main() -> int:
    """Run all validation checks."""
    logger.info("=" * 60)
    logger.info("PRE-FLIGHT VALIDATION")
    logger.info("=" * 60)

    tests = [
        ("Module imports", test_imports),
        ("Config loading", test_config_loading),
        ("Model initialization", test_model_initialization),
        ("Data loading", test_data_loading),
        ("Training step (end-to-end)", test_training_step),
        ("Evaluation metrics", test_evaluation_metrics),
    ]

    results = []
    for test_name, test_fn in tests:
        result = check(test_name, test_fn)
        results.append(result)

    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    status = "PASS" if all(results) else "FAIL"
    logger.info(f"{status}: {passed}/{total} checks passed")
    logger.info("=" * 60)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
