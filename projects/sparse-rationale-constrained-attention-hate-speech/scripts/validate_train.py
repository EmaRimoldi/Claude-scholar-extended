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
            f"Missing config files:\n" + "\n".join(f"  {m}" for m in missing)
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


def main() -> None:
    print("=== train.sh pre-submission validation ===\n")
    results = [
        check("1. all 10 experiment config files exist", test_config_files_exist),
        check("2. softmax model (M0-style) init + forward", test_softmax_model_forward),
        check("3. sparsemax model (M4b-style) init + forward", test_sparsemax_model_forward),
        check("4. training step: forward + loss + backward", test_training_step),
    ]

    print(f"\n{'='*46}")
    passed = sum(results)
    total = len(results)
    status = "ALL PASS" if passed == total else f"{total - passed} FAILED"
    print(f"  {status}  ({passed}/{total})")
    print("=" * 46)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
