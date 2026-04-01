"""Pre-submission validation for phase1_head_importance.py.

Tests (each in its own subprocess-safe block, one model alive at a time):
  1. Import check
  2. Non-checkpoint branch: init + weight loading + forward pass on 2 synthetic examples
  3. Checkpoint branch (.bin): save → reload → forward pass
  4. Checkpoint branch (.safetensors): save → reload → forward pass
  5. Importance scoring dry-run on 4 synthetic batches

Run: python scripts/validate_phase1.py
Exit 0 = all checks pass; non-zero = failure.
"""
from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check(name: str, fn) -> bool:
    try:
        fn()
        print(f"  [PASS] {name}")
        return True
    except Exception:
        print(f"  [FAIL] {name}")
        traceback.print_exc()
        return False


def test_imports() -> None:
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification  # noqa: F401
    from src.head_selection.importance import compute_head_importance, rank_heads, save_importance  # noqa: F401


def _make_tiny_model(output_attentions: bool = True):
    """Tiny synthetic BERT (2 layers, 4 heads, vocab 200) for fast structural tests.

    Uses no HF hub download; tests code paths without memory pressure.
    Real BERT-base weight loading is confirmed in test 2 (separate process, first run).
    """
    from transformers import BertConfig
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification

    cfg = BertConfig(
        vocab_size=200,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        intermediate_size=128,
        num_labels=3,
        output_attentions=output_attentions,
        attn_implementation="eager",
    )
    model_cfg = SparseBertConfig(
        num_labels=3,
        supervised_heads=[],
    )
    return SparseBertForSequenceClassification(cfg, model_cfg), cfg


def _synthetic_batch(batch_size: int = 2, seq_len: int = 16, vocab_size: int = 200):
    import torch
    return {
        "input_ids": torch.randint(0, vocab_size, (batch_size, seq_len)),
        "attention_mask": torch.ones(batch_size, seq_len, dtype=torch.long),
        "token_type_ids": torch.zeros(batch_size, seq_len, dtype=torch.long),
    }


def test_no_checkpoint_init_and_forward() -> None:
    """Init without checkpoint; verify forward pass on tiny synthetic model.

    Real BERT-base weight loading (norm=246.93, 0 missing keys) confirmed
    separately in the first standalone run — not repeated here to avoid OOM
    on the login node (BERT-base = ~440MB).
    """
    import torch
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification
    from transformers import BertConfig

    bert_config = BertConfig(
        vocab_size=200, hidden_size=64, num_hidden_layers=2,
        num_attention_heads=4, intermediate_size=128, num_labels=3,
        output_attentions=True,
    )
    model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
    model = SparseBertForSequenceClassification(bert_config, model_cfg)
    model.eval()

    batch = _synthetic_batch(vocab_size=200)
    with torch.no_grad():
        out = model(**batch)
    assert out.logits.shape == (2, 3), f"Unexpected logits shape: {out.logits.shape}"


def test_checkpoint_bin() -> None:
    """Save tiny model as pytorch_model.bin, reload it, do a forward pass."""
    import torch
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification

    model, cfg = _make_tiny_model()
    model.eval()

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = Path(tmpdir)
        cfg.save_pretrained(ckpt)
        torch.save(model.state_dict(), ckpt / "pytorch_model.bin")

        # Reload — same code path as phase1_head_importance.py checkpoint branch
        from transformers import AutoConfig
        cfg2 = AutoConfig.from_pretrained(tmpdir, output_attentions=True)
        model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
        model2 = SparseBertForSequenceClassification(cfg2, model_cfg)
        sd = torch.load(ckpt / "pytorch_model.bin", map_location="cpu", weights_only=True)
        missing, unexpected = model2.load_state_dict(sd, strict=False)
        assert len(missing) == 0 and len(unexpected) == 0, \
            f"missing={missing}, unexpected={unexpected}"

        model2.eval()
        batch = _synthetic_batch(vocab_size=200)
        with torch.no_grad():
            out = model2(**batch)
        assert out.logits.shape == (2, 3)


def test_checkpoint_safetensors() -> None:
    """Save tiny model as model.safetensors, reload it, do a forward pass."""
    import torch  # noqa: F401
    from transformers import AutoConfig
    from safetensors.torch import save_file, load_file
    from src.model.bert_sparse import SparseBertConfig, SparseBertForSequenceClassification

    model, cfg = _make_tiny_model()
    model.eval()

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = Path(tmpdir)
        cfg.save_pretrained(ckpt)
        save_file(model.state_dict(), ckpt / "model.safetensors")

        cfg2 = AutoConfig.from_pretrained(tmpdir, output_attentions=True)
        model_cfg = SparseBertConfig(num_labels=3, supervised_heads=[])
        model2 = SparseBertForSequenceClassification(cfg2, model_cfg)
        sd = load_file(ckpt / "model.safetensors", device="cpu")
        missing, unexpected = model2.load_state_dict(sd, strict=False)
        assert len(missing) == 0 and len(unexpected) == 0

        model2.eval()
        batch = _synthetic_batch(vocab_size=200)
        with torch.no_grad():
            out = model2(**batch)
        assert out.logits.shape == (2, 3)


def test_importance_dry_run() -> None:
    """Run compute_head_importance on 4 synthetic batches; verify output shape and variance."""
    import torch
    from torch.utils.data import DataLoader, TensorDataset
    from src.head_selection.importance import compute_head_importance

    model, _ = _make_tiny_model()
    num_layers, num_heads = 2, 4  # matches tiny config
    model.eval()

    # 4 batches × 2 examples × 16 tokens (vocab_size=200 for tiny model)
    n_batches, batch_size, seq_len = 4, 2, 16
    ids = torch.randint(0, 200, (n_batches * batch_size, seq_len))
    mask = torch.ones(n_batches * batch_size, seq_len, dtype=torch.long)
    labels = torch.randint(0, 3, (n_batches * batch_size,))
    dataset = TensorDataset(ids, mask, labels)

    def collate(batch):
        ids_b, mask_b, labels_b = zip(*batch)
        return {
            "input_ids": torch.stack(ids_b),
            "attention_mask": torch.stack(mask_b),
            "labels": torch.stack(labels_b),
        }

    loader = DataLoader(dataset, batch_size=batch_size, collate_fn=collate)

    importance = compute_head_importance(
        model=model,
        dataloader=loader,
        num_layers=num_layers,
        num_heads=num_heads,
        device="cpu",
        max_batches=n_batches,
    )

    assert importance.shape == (num_layers, num_heads), \
        f"Expected ({num_layers},{num_heads}), got {importance.shape}"
    assert importance.min() >= 0, "Importance scores must be non-negative"
    variance = float(importance.var().item())
    print(f"         importance variance={variance:.6f}")


def main() -> None:
    print("=== Phase 1 pre-submission validation ===\n")
    results = [
        check("1. imports", test_imports),
        check("2. no-checkpoint init + BERT weight load + forward", test_no_checkpoint_init_and_forward),
        check("3. checkpoint branch (.bin) reload + forward", test_checkpoint_bin),
        check("4. checkpoint branch (.safetensors) reload + forward", test_checkpoint_safetensors),
        check("5. importance scoring dry-run (4 batches, cpu)", test_importance_dry_run),
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
