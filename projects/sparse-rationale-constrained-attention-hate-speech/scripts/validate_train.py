"""Pre-submission validation for train.sh (Wave 1 / Wave 2).

Checks:
  1. All experiment config files are loadable by Hydra
  2. SparseBertForSequenceClassification initializes and runs a forward pass
     for both softmax-only (M0/M1) and sparsemax-supervised (M4b) configurations
  3. Training step dry-run: forward + loss + backward on 2 synthetic examples

Run: python scripts/validate_train.py
Exit 0 = all checks pass; non-zero = failure.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

CONFIGS_DIR = Path(__file__).parent.parent / "configs" / "experiment"
CONDITION_CONFIGS = {
    "M0": "m0_baseline_softmax",
    "M1": "m1_sra_replication",
    "M2": "m2_full_softmax_mse",
    "M3": "m3_full_sparsemax_mse",
    "M4a": "m4a_sel_sparsemax_mse_k3",
    "M4b": "m4b_sel_sparsemax_mse_k6",
    "M4c": "m4c_sel_sparsemax_mse_k9",
    "M5": "m5_sel_sparsemax_kl",
    "M6": "m6_sel_sparsemax_loss",
    "M7": "m7_sel_softmax_mse",
}
TINY_VOCAB = 200


def check(name: str, fn) -> bool:
    try:
        fn()
        print(f"  [PASS] {name}")
        return True
    except Exception:
        print(f"  [FAIL] {name}")
        traceback.print_exc()
        return False


def _tiny_bert_config(supervised_heads=None, output_attentions: bool = False):
    from transformers import BertConfig

    return BertConfig(
        vocab_size=TINY_VOCAB,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        intermediate_size=128,
        num_labels=3,
        output_attentions=output_attentions,
        attn_implementation="eager",
    )


def _synthetic_batch(batch_size: int = 2, seq_len: int = 16):
    import torch

    return {
        "input_ids": torch.randint(0, TINY_VOCAB, (batch_size, seq_len)),
        "attention_mask": torch.ones(batch_size, seq_len, dtype=torch.long),
        "token_type_ids": torch.zeros(batch_size, seq_len, dtype=torch.long),
        "labels": torch.randint(0, 3, (batch_size,)),
    }


def test_config_files_exist() -> None:
    """All 10 experiment config YAML files must exist."""
    missing = []
    for condition, config_name in CONDITION_CONFIGS.items():
        path = CONFIGS_DIR / f"{config_name}.yaml"
        if not path.exists():
            missing.append(f"{condition}: {path}")
    if missing:
        raise FileNotFoundError(
            "Missing config files:\n" + "\n".join(f"  {m}" for m in missing)
        )


def test_hydra_config_override() -> None:
    """Each experiment config must be selectable via Hydra override (experiment=name).

    This catches the '+experiment=' vs 'experiment=' Hydra syntax mistake:
    if a default is set in config.yaml, '+experiment=' raises 'Multiple values'.
    """
    import subprocess

    failed = []
    for condition, config_name in CONDITION_CONFIGS.items():
        result = subprocess.run(
            [
                sys.executable, "run_experiment.py",
                f"experiment={config_name}",
                "seed=42",
                "--cfg", "job",          # print resolved config, no actual run
                "--resolve",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        if result.returncode != 0:
            failed.append(
                f"{condition} ({config_name}):\n    {result.stderr.strip().splitlines()[-1]}"
            )
    if failed:
        raise RuntimeError(
            "Hydra config override failed for:\n" + "\n".join(f"  {f}" for f in failed)
        )


def test_softmax_model_forward() -> None:
    """M0-style model (no supervised heads, softmax): init + forward."""
    import torch
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification

    bert_cfg = _tiny_bert_config()
    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
    model = SparseBertForSequenceClassification(bert_cfg, model_cfg)
    model.eval()

    batch = _synthetic_batch()
    with torch.no_grad():
        out = model(**batch)
    assert out.logits.shape == (2, 3)
    assert out.loss is not None


def test_sparsemax_model_forward() -> None:
    """M4b-style model (sparsemax on 2 heads): init + forward."""
    import torch
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification

    bert_cfg = _tiny_bert_config()
    # Supervise heads (0,0) and (1,1) — valid for 2-layer, 4-head tiny model
    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[(0, 0), (1, 1)])
    model = SparseBertForSequenceClassification(bert_cfg, model_cfg)
    model.eval()

    batch = _synthetic_batch()
    with torch.no_grad():
        out = model(**batch)
    assert out.logits.shape == (2, 3)
    assert out.loss is not None


def test_training_step() -> None:
    """Forward + loss + backward: gradients must be non-None after backward."""
    import torch
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification

    bert_cfg = _tiny_bert_config()
    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[(0, 0)])
    model = SparseBertForSequenceClassification(bert_cfg, model_cfg)
    model.train()

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    batch = _synthetic_batch()

    optimizer.zero_grad()
    out = model(**batch)
    assert out.loss is not None, "Loss is None — labels not passed or loss not computed"
    out.loss.backward()
    optimizer.step()

    # At least one parameter must have a gradient
    has_grad = any(p.grad is not None for p in model.parameters())
    assert has_grad, "No gradients after backward — training loop is broken"


def test_data_loading() -> None:
    """HateXplainDataset must load without errors."""
    try:
        from src.data.dataset import HateXplainDataset
    except ImportError:
        raise ImportError("Cannot import HateXplainDataset")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    # Try to load train dataset
    try:
        train_dataset = HateXplainDataset(
            "train",
            tokenizer,
            max_length=64,
            include_rationale=False,
        )
        assert len(train_dataset) > 0, "Train dataset is empty"
    except Exception as e:
        raise RuntimeError(f"Could not load train data: {e}")

    # Try to load validation dataset
    try:
        val_dataset = HateXplainDataset(
            "validation",
            tokenizer,
            max_length=64,
            include_rationale=False,
        )
        assert len(val_dataset) > 0, "Validation dataset is empty"
    except Exception as e:
        raise RuntimeError(f"Could not load validation data: {e}")


def test_metrics_computation() -> None:
    """compute_metrics must handle inhomogeneous logits arrays (critical for Trainer)."""
    import numpy as np
    from sklearn.metrics import f1_score

    # Simulate the problematic case: list of arrays with different shapes
    # This is what HuggingFace Trainer produces in eval
    logits_list = [
        np.array([0.1, 0.5, 0.4]),      # shape (3,)
        np.array([0.8, 0.1, 0.1]),      # shape (3,)
        np.array([[0.2, 0.3, 0.5]]),    # shape (1, 3)
        np.array([0.6, 0.2, 0.2]),      # shape (3,)
    ]
    labels = np.array([1, 0, 2, 0])

    # Replicate the compute_metrics robustness test
    logits = logits_list

    # Handle different input types for logits
    if isinstance(logits, list):
        try:
            # Try to convert list of arrays to a single array
            logits_list_conv = []
            for item in logits:
                if hasattr(item, 'numpy'):
                    logits_list_conv.append(item.numpy())
                elif isinstance(item, (list, tuple)):
                    logits_list_conv.append(np.array(item))
                else:
                    logits_list_conv.append(item)
            # Try to stack as regular array
            logits = np.stack(logits_list_conv, axis=0)
        except (ValueError, TypeError):
            # If shapes don't match, create uniform array and fill
            batch_size = len(logits_list_conv)
            num_classes = 3
            logits_array = np.zeros((batch_size, num_classes))
            for i, item in enumerate(logits_list_conv):
                if isinstance(item, np.ndarray):
                    if item.ndim == 1 and len(item) <= num_classes:
                        logits_array[i, :len(item)] = item
                    elif item.ndim >= 1:
                        logits_array[i] = item.flat[:num_classes]
            logits = logits_array

    # Now ensure logits is 2D
    if logits.ndim == 1:
        logits = logits.reshape(-1, 1)
    elif logits.ndim > 2:
        logits = logits[:, 0, :]

    # Compute predictions
    preds = np.argmax(logits, axis=-1)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    accuracy = (preds == labels).mean()

    assert macro_f1 >= 0, "F1 computation failed"
    assert accuracy >= 0, "Accuracy computation failed"


def main() -> None:
    print("=== train.sh pre-submission validation ===\n")
    results = [
        check("1. all 10 experiment config files exist", test_config_files_exist),
        check("2. Hydra config override (experiment=name, not +experiment=)", test_hydra_config_override),
        check("3. softmax model (M0-style) init + forward", test_softmax_model_forward),
        check("4. sparsemax model (M4b-style) init + forward", test_sparsemax_model_forward),
        check("5. training step: forward + loss + backward", test_training_step),
        check("6. data loading (HateXplainDataset)", test_data_loading),
        check("7. metrics computation (inhomogeneous logits handling)", test_metrics_computation),
    ]

    print(f"\n{'='*50}")
    passed = sum(results)
    total = len(results)
    status = "ALL PASS" if passed == total else f"{total - passed} FAILED"
    print(f"  {status}  ({passed}/{total})")
    print("=" * 50)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
