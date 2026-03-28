# Validation Report: ICL Circuit-Algorithm Bridge

**Project**: icl-circuit-algorithm-bridge
**Date**: 2026-03-28
**Configuration**: GPT-2 350M, linear regression ICL, seed 42

---

## Check 1: Data Integrity

| Check | Status | Details |
|---|---|---|
| 1.1 Shape | PASS | Input: (32, 21, 20), Label: (32,) — matches config (batch=32, k=10 examples, d=20) |
| 1.2 Distribution | PASS | x: mean=-0.003, std=0.998 (expected N(0,1)). w: mean=0.012, std=1.005 (expected N(0,1)) |
| 1.3 Label verification | PASS | 5/5 samples verified: y = wᵀx_query + ε matches within 1e-6 |
| 1.4 Reproducibility | PASS | 10 samples identical across two runs with seed=42 |
| 1.5 No data leakage | PASS | Task vectors (w) are independent across episodes (correlation < 0.02) |

## Check 2: Model Loading

| Check | Status | Details |
|---|---|---|
| 2.1 Non-trivial output | PASS | Output shape (32, 21, 50257), max logit 18.4, no NaN/Inf |
| 2.2 Hook extraction | PASS | 24 attention layers hooked, outputs shape (32, 12, 21, 21) for attention patterns |
| 2.3 Device consistency | PASS | Model on cuda:0, data on cuda:0 |
| 2.4 Dtype | PASS | Model in fp32 as expected |

## Check 3: Measurement Correctness

| Check | Status | Details |
|---|---|---|
| 3.1 Identity test | PASS | cosine_similarity(x, x) = 1.0000 |
| 3.2 Orthogonal test | PASS | cosine_similarity(e1, e2) = 0.0000 |
| 3.3 Known-answer (OLS) | PASS | OLS recovers w_true with relative error 3.2e-7 on noise-free data |
| 3.4 GD update | PASS | Single GD step matches analytical formula within 1e-6 |
| 3.5 Numerical stability | PASS | cosine_similarity handles zero vector (returns 0.0, no NaN) |

## Check 4: Ablation Verification

| Check | Status | Details |
|---|---|---|
| 4.1 Zero check | PASS | Ablated head L11H7 output is zero-tensor (max abs: 0.0) |
| 4.2 Impact check | PASS | Model output changes after ablation (L2 diff: 2.34) |
| 4.3 Restoration check | PASS | Post-restoration output matches pre-ablation bitwise |
| 4.4 Specificity check | PASS | Ablating L11H7 does not affect L11H8 output |

## Check 5: Baseline Replication

| Check | Status | Details |
|---|---|---|
| 5.1 Trivial baseline | PASS | Random head cosine similarity: mean 0.012 ± 0.089 (expected ~0) |
| 5.2 Published baseline | **FAIL** | Expected IH prefix matching score ~0.8 (Olsson et al.), observed 0.62 |

**Failure analysis**: Prefix matching score below expected range. Possible causes:
- Different tokenization or input format than Olsson et al.
- GPT-2 medium may have weaker induction heads than GPT-2 small (used in the original)
- Score threshold for IH identification may need adjustment

**Suggested fix**: Run prefix matching on GPT-2 small (125M) first to verify implementation matches published results, then re-run on medium.

## Check 6: End-to-End Smoke Test

| Check | Status | Details |
|---|---|---|
| 6.1 Pipeline completion | PASS | Full run completed without error |
| 6.2 Output format | PASS | results.json contains expected fields |
| 6.3 Metric plausibility | PASS | IH-GD cosine similarity: 0.43 (nonzero, finite) |
| 6.4 Timing | PASS | See below |

### Timing Data

```json
{
  "model": "gpt2-medium",
  "dataset": "linear_regression_icl",
  "device": "cuda:0",
  "gpu_model": "NVIDIA A100",
  "wall_time_seconds": 127.3,
  "peak_gpu_memory_mb": 4800,
  "num_forward_passes": 10000,
  "time_per_forward_pass_ms": 12.7
}
```

---

## Overall Verdict: **NOT READY**

### Blocking Issues (1)

1. **Baseline replication failure** (Check 5.2): IH identification score below expected range. Must verify on GPT-2 small before proceeding to full sweep.

### Non-Blocking Notes

- All data, model, measurement, and ablation checks pass.
- Smoke test timing suggests ~127s per run → full matrix (233 GPU-hours estimated) is feasible on pi_tpoggio.
- Pipeline structure is correct; only the IH identification threshold needs calibration.

### Recommended Next Steps

1. Run prefix matching on GPT-2 small (125M) — compare to Olsson et al. Table 1
2. If match: adjust threshold for medium model and re-validate
3. If no match: debug prefix matching implementation
