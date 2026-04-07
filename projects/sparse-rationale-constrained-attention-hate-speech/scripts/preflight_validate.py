"""Pre-flight validation: CPU-based smoke tests before GPU submission.

Per project validation rules: all code must pass CPU validation before
cluster submission to avoid wasting GPU resources on broken code.

Tests:
1.  Sparsemax forward/backward correctness
2.  Sparsemax produces exactly-zero values on known inputs
3.  Sparsemax gradient flow
4.  MSE alignment loss
5.  KL alignment loss (non-degenerate inputs)
5b. KL alignment loss with BERT padding zeros (regression: float32 underflow → NaN)
5c. KL loss backward with padding zeros (gradient must be finite, not NaN)
6.  Joint loss (CE + MSE)
7.  BERT softmax forward (no-grad, no padding)
8.  BERT sparsemax forward with supervision (no-grad, no padding)
9.  ERASER comprehensiveness metric
10. Sparsemax CLS attention zero count
11. End-to-end training step for all 5 conditions with realistic padded batch
    (forward + loss + backward; catches NaN loss/gradient before GPU submission)

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
    # Allow tiny float32 rounding (~2e-8) when distributions are identical;
    # clamp(min=0) in the loss function handles this in real training.
    assert loss.item() >= -1e-6, f"KL loss is significantly negative: {loss.item()}"


# ---- Check 5b: KL loss with BERT padding zeros (regression: float32 underflow) ----
def check_kl_loss_with_padding_zeros() -> None:
    """Regression test: BERT adds torch.finfo().min to padding scores.
    softmax(score + finfo.min) underflows to exactly 0.0 in float32.
    F.kl_div naively computes 0 * (log(0) - input) = 0 * (-inf) = NaN.
    torch.xlogy handles xlogy(0, 0) = 0 correctly.
    """
    from src.model_module.losses import KLAlignmentLoss

    loss_fn = KLAlignmentLoss()
    # Simulate BERT CLS attention: real tokens have softmax mass, padding is exactly 0
    # Sequence length 8: first 3 tokens real, last 5 are padding → attention=0
    attention = torch.tensor([[0.4, 0.35, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0]])
    # Binary rationale mask: only first 3 positions have any signal
    rationale = torch.tensor([[1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    loss = loss_fn(attention, rationale)
    assert not torch.isnan(loss), f"KL loss is NaN with padding zeros (got {loss})"
    assert not torch.isinf(loss), f"KL loss is inf with padding zeros (got {loss})"
    assert loss.item() >= 0, f"KL loss should be non-negative, got {loss.item()}"


# ---- Check 5c: KL loss backward with padding zeros ----
def check_kl_loss_backward_with_padding() -> None:
    """Verify that backward through KL with exact-zero attention produces finite gradients.

    The forward NaN check (5b) is necessary but not sufficient: even if loss is finite,
    the gradient could be NaN if the backward pass encounters a 0*log(0) branch.
    This checks both forward and backward are clean.
    """
    from src.model_module.losses import KLAlignmentLoss

    loss_fn = KLAlignmentLoss()
    # attention has exact zeros at padding positions (as BERT produces in float32)
    attention = torch.tensor([[0.4, 0.35, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0]], requires_grad=True)
    rationale = torch.tensor([[1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    loss = loss_fn(attention, rationale)
    assert not torch.isnan(loss), f"KL backward test: loss is NaN"
    loss.backward()
    assert attention.grad is not None, "KL backward test: no gradient"
    assert not torch.isnan(attention.grad).any(), (
        f"KL backward test: NaN gradient at positions {torch.where(torch.isnan(attention.grad))}"
    )
    assert not torch.isinf(attention.grad).any(), "KL backward test: inf gradient"


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


# ---- Check 11: End-to-end training step for all 5 conditions with padded batch ----
def check_training_step_all_conditions() -> None:
    """Run forward+loss+backward for each condition on a realistic padded batch.

    This is the critical integration test. It catches NaN losses and gradients
    that only appear during actual training, not in isolated unit tests.

    Why padding matters: BERT adds torch.finfo(float32).min (~-3.4e38) to padding
    scores as the additive attention mask. exp(-3.4e38) underflows to exactly 0.0
    in float32. Any loss that naively calls log(0) on these zeros will produce NaN.

    Batch: B=2, T=32, first 10 tokens real, positions 10-31 are padding.
    Rationale: tokens 1 and 2 marked (sparse, as typical of HateXplain).
    """
    import torch.nn as nn
    from src.model_module.bert_classifier import BertHateSpeechClassifier, ClassifierConfig
    from src.model_module.losses import JointLoss, KLAlignmentLoss, MSEAlignmentLoss

    B, T, real_len = 2, 32, 10
    input_ids = torch.randint(100, 30000, (B, T))
    attention_mask = torch.zeros(B, T, dtype=torch.long)
    attention_mask[:, :real_len] = 1          # first 10 tokens are real
    labels = torch.randint(0, 3, (B,))
    rationale = torch.zeros(B, T)
    rationale[:, 1:3] = 0.5                   # tokens 1-2 are rationale

    condition_cfgs = [
        ("C1", ClassifierConfig(use_sparsemax=False, supervised_heads=None,         alpha=0.0, use_kl_loss=False)),
        ("C2", ClassifierConfig(use_sparsemax=False, supervised_heads=list(range(12)), alpha=0.3, use_kl_loss=True)),
        ("C3", ClassifierConfig(use_sparsemax=True,  supervised_heads=None,         alpha=0.0, use_kl_loss=False)),
        ("C4", ClassifierConfig(use_sparsemax=True,  supervised_heads=list(range(12)), alpha=0.3, use_kl_loss=False)),
        ("C5", ClassifierConfig(use_sparsemax=True,  supervised_heads=list(range(6)),  alpha=0.3, use_kl_loss=False)),
    ]
    ce_fn = nn.CrossEntropyLoss()

    for cond, cfg in condition_cfgs:
        model = BertHateSpeechClassifier(cfg)
        model.train()
        model.zero_grad()

        out = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = out["logits"]
        cls_attn = out["cls_attention"]

        if cfg.alpha > 0 and cls_attn is not None:
            align_loss = KLAlignmentLoss() if cfg.use_kl_loss else MSEAlignmentLoss()
            loss_fn = JointLoss(align_loss, alpha=cfg.alpha)
            loss, ce_val, align_val = loss_fn(logits, labels, cls_attn, rationale)
        else:
            loss = ce_fn(logits, labels)

        assert not torch.isnan(loss), (
            f"{cond}: loss is NaN — check loss function for 0*log(0) with padding zeros"
        )
        assert not torch.isinf(loss), f"{cond}: loss is inf"
        assert loss.item() > 0, f"{cond}: loss={loss.item()} should be positive"

        loss.backward()

        grad_norm = sum(
            p.grad.data.norm(2).item() ** 2
            for p in model.parameters()
            if p.grad is not None
        ) ** 0.5
        assert grad_norm > 0, f"{cond}: gradient norm is 0 (backward did not propagate)"
        assert not (grad_norm != grad_norm), f"{cond}: gradient norm is NaN"
        logger.info(f"  {cond}: loss={loss.item():.4f}  grad_norm={grad_norm:.2f}")


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
        ("Sparsemax valid probabilities",                       check_sparsemax_valid),
        ("Sparsemax exact zeros",                               check_sparsemax_exact_zeros),
        ("Sparsemax gradient flow",                             check_sparsemax_gradient),
        ("MSE alignment loss",                                  check_mse_loss),
        ("KL alignment loss",                                   check_kl_loss),
        ("KL loss with BERT padding zeros (regression)",        check_kl_loss_with_padding_zeros),
        ("KL loss backward with padding zeros",                 check_kl_loss_backward_with_padding),
        ("Joint loss (CE + MSE)",                               check_joint_loss),
        ("BERT softmax forward",                                check_bert_softmax_forward),
        ("BERT sparsemax forward with supervision",             check_bert_sparsemax_forward),
        ("ERASER comprehensiveness metric",                     check_eraser_comprehensiveness),
        ("Sparsemax CLS attention zero count",                  check_sparsemax_cls_has_zeros),
        ("Training step all conditions C1-C5 (padded batch)",  check_training_step_all_conditions),
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
