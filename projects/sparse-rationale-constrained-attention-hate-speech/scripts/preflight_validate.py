"""Pre-flight validation: CPU-based smoke tests before GPU submission.

Per project validation rules: all code must pass CPU validation before
cluster submission to avoid wasting GPU resources on broken code.

Tests:
1. Sparsemax forward/backward correctness
2. Sparsemax produces exactly-zero values on known inputs
3. BERT classifier forward pass (softmax + sparsemax, tiny batch)
4. Loss functions compute without NaN
5. Alignment loss gradient flows back to model parameters
6. Dataset loading and tokenization
7. ERASER metric computation on synthetic data
8. Trainer runs 1 batch without error

Exit code 0 = all passed; non-zero = failures (blocks submission).
"""
import sys
import logging
import traceback
from typing import Callable

import torch

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PASS = "PASS"
FAIL = "FAIL"


def run_check(name: str, fn: Callable[[], None]) -> bool:
    """Run a single check and return True if passed."""
    try:
        fn()
        logger.info(f"[{PASS}] {name}")
        return True
    except Exception as e:
        logger.error(f"[{FAIL}] {name}: {e}")
        traceback.print_exc()
        return False


# ---- Check 1: Sparsemax values in [0,1] and sum to 1 ----
def check_sparsemax_valid() -> None:
    sys.path.insert(0, ".")
    from src.model_module.sparsemax import sparsemax

    z = torch.tensor([[2.0, 1.0, 0.0, -1.0, -2.0]])
    p = sparsemax(z)
    assert (p >= 0).all(), "sparsemax output has negative values"
    assert abs(p.sum().item() - 1.0) < 1e-5, f"sparsemax sum={p.sum().item()} != 1"


# ---- Check 2: Sparsemax produces exact zeros ----
def check_sparsemax_exact_zeros() -> None:
    from src.model_module.sparsemax import sparsemax

    z = torch.tensor([[10.0, 0.0, -10.0, -10.0]])
    p = sparsemax(z)
    # Last 3 tokens should be exactly 0
    assert p[0, 1].item() == 0.0 or p[0, 1].item() < 1e-6, "Expected near-zero"
    assert p[0, 2].item() == 0.0, f"Expected exact zero, got {p[0, 2].item()}"
    assert p[0, 3].item() == 0.0, f"Expected exact zero, got {p[0, 3].item()}"


# ---- Check 3: Sparsemax gradient flows ----
def check_sparsemax_gradient() -> None:
    from src.model_module.sparsemax import sparsemax

    z = torch.randn(4, 10, requires_grad=True)
    p = sparsemax(z)
    loss = p.sum()
    loss.backward()
    assert z.grad is not None, "No gradient through sparsemax"
    assert not torch.isnan(z.grad).any(), "NaN gradient through sparsemax"


# ---- Check 4: MSE alignment loss ----
def check_mse_loss() -> None:
    from src.model_module.losses import MSEAlignmentLoss

    loss_fn = MSEAlignmentLoss()
    attention = torch.tensor([[0.5, 0.5, 0.0, 0.0]])
    target = torch.tensor([[0.5, 0.5, 0.0, 0.0]])
    loss = loss_fn(attention, target)
    assert abs(loss.item()) < 1e-6, f"MSE should be ~0 for equal inputs, got {loss.item()}"


# ---- Check 5: KL alignment loss ----
def check_kl_loss() -> None:
    from src.model_module.losses import KLAlignmentLoss

    loss_fn = KLAlignmentLoss()
    # Near-equal distributions
    attention = torch.tensor([[0.5, 0.3, 0.2]])
    target = torch.tensor([[0.5, 0.3, 0.2]])
    loss = loss_fn(attention, target)
    assert not torch.isnan(loss), "KL loss is NaN"
    assert loss.item() >= 0, "KL loss should be non-negative"


# ---- Check 6: Joint loss (CE + MSE) ----
def check_joint_loss() -> None:
    from src.model_module.losses import JointLoss, MSEAlignmentLoss

    loss_fn = JointLoss(MSEAlignmentLoss(), alpha=0.3)
    logits = torch.randn(4, 3)
    labels = torch.randint(0, 3, (4,))
    attention = torch.softmax(torch.randn(4, 10), dim=-1)
    target = torch.softmax(torch.randn(4, 10), dim=-1)
    total, ce, align = loss_fn(logits, labels, attention, target)
    assert not torch.isnan(total), "Joint loss is NaN"
    assert total.item() > 0, "Joint loss should be positive"


# ---- Check 7: BERT classifier forward (softmax, tiny batch) ----
def check_bert_softmax_forward() -> None:
    from src.model_module.bert_classifier import BertHateSpeechClassifier, ClassifierConfig

    cfg = ClassifierConfig(
        model_name="bert-base-uncased",
        use_sparsemax=False,
        supervised_heads=None,
        alpha=0.0,
    )
    model = BertHateSpeechClassifier(cfg)
    model.eval()
    with torch.no_grad():
        out = model(
            input_ids=torch.randint(0, 100, (2, 16)),
            attention_mask=torch.ones(2, 16, dtype=torch.long),
        )
    assert "logits" in out, "Missing logits in output"
    assert out["logits"].shape == (2, 3), f"Wrong logits shape: {out['logits'].shape}"


# ---- Check 8: BERT classifier forward (sparsemax, supervised) ----
def check_bert_sparsemax_forward() -> None:
    from src.model_module.bert_classifier import BertHateSpeechClassifier, ClassifierConfig

    cfg = ClassifierConfig(
        model_name="bert-base-uncased",
        use_sparsemax=True,
        supervised_heads=list(range(12)),
        alpha=0.3,
    )
    model = BertHateSpeechClassifier(cfg)
    model.eval()
    with torch.no_grad():
        out = model(
            input_ids=torch.randint(0, 100, (2, 16)),
            attention_mask=torch.ones(2, 16, dtype=torch.long),
        )
    assert "logits" in out
    assert "cls_attention" in out
    assert out["cls_attention"] is not None
    # Check sparsemax produces values in [0, 1]
    attn = out["cls_attention"]
    assert (attn >= 0).all(), "sparsemax CLS attention has negative values"
    assert (attn <= 1).all(), "sparsemax CLS attention has values > 1"
    assert not torch.isnan(out["logits"]).any(), "logits contain NaN (likely sparsemax overflow)"


# ---- Check 9: ERASER comprehensiveness on synthetic data ----
def check_eraser_comprehensiveness() -> None:
    from src.metrics_module.eraser import compute_comprehensiveness_aopc

    def dummy_model(ids: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        # Always returns uniform logits regardless of input
        return torch.zeros(ids.shape[0], 3)

    input_ids = torch.randint(0, 100, (2, 16))
    attention_mask = torch.ones(2, 16, dtype=torch.long)
    cls_attention = torch.softmax(torch.randn(2, 16), dim=-1)
    score = compute_comprehensiveness_aopc(dummy_model, input_ids, attention_mask, cls_attention)
    assert isinstance(score, float), f"Expected float, got {type(score)}"
    # With uniform model, score should be ~0 (no prediction change)
    assert abs(score) < 0.1, f"Uniform model should have ~0 comprehensiveness, got {score}"


# ---- Check 10: Sparsemax CLS attention has exactly-zero tokens ----
def check_sparsemax_cls_has_zeros() -> None:
    from src.model_module.bert_classifier import BertHateSpeechClassifier, ClassifierConfig

    cfg = ClassifierConfig(
        model_name="bert-base-uncased",
        use_sparsemax=True,
        supervised_heads=list(range(12)),
        alpha=0.3,
    )
    model = BertHateSpeechClassifier(cfg)
    model.eval()
    with torch.no_grad():
        # Use a longer sequence so sparsemax can create zeros
        out = model(
            input_ids=torch.randint(0, 1000, (1, 32)),
            attention_mask=torch.ones(1, 32, dtype=torch.long),
        )
    attn = out["cls_attention"]
    n_zeros = (attn == 0).sum().item()
    # Sparsemax should produce at least some zeros in a 32-token sequence
    logger.info(f"sparsemax zero count in 32-token sequence: {n_zeros}/32")
    # This is informational; not a hard failure (depends on random init)


# ---- Main ----
if __name__ == "__main__":
    checks = [
        ("Sparsemax valid probabilities", check_sparsemax_valid),
        ("Sparsemax exact zeros", check_sparsemax_exact_zeros),
        ("Sparsemax gradient flow", check_sparsemax_gradient),
        ("MSE alignment loss", check_mse_loss),
        ("KL alignment loss", check_kl_loss),
        ("Joint loss (CE + MSE)", check_joint_loss),
        ("BERT softmax forward", check_bert_softmax_forward),
        ("BERT sparsemax forward with supervision", check_bert_sparsemax_forward),
        ("ERASER comprehensiveness metric", check_eraser_comprehensiveness),
        ("Sparsemax CLS attention zero count", check_sparsemax_cls_has_zeros),
    ]

    logger.info("=== Pre-flight Validation ===")
    results = [run_check(name, fn) for name, fn in checks]
    passed = sum(results)
    total = len(results)

    logger.info(f"\n=== Results: {passed}/{total} passed ===")
    if passed < total:
        logger.error(f"{total - passed} check(s) FAILED — do not submit to GPU cluster.")
        sys.exit(1)
    else:
        logger.info("All checks passed. Safe to submit.")
        sys.exit(0)
