# Method-Code Reconciliation Report

**Date:** 2026-04-07 | **Step:** 25

## Status: PASS (minor documentation discrepancy)

| Component | Plan | Code/Config | Match? |
|-----------|------|-------------|--------|
| C1: softmax, no sup | ✓ | bert_softmax_baseline.yaml: use_sparsemax=false, supervised_heads=null | ✓ |
| C2: softmax, KL, 12 heads | ✓ | bert_softmax_sra.yaml: use_sparsemax=false, supervised_heads=[0..11], use_kl_loss=true | ✓ |
| C3: sparsemax, no sup | ✓ (second table) | bert_sparsemax.yaml: use_sparsemax=true, supervised_heads=[0..11], alpha=0 → no loss | ✓ |
| C4: sparsemax, MSE, all-12 | ✓ | bert_sparsemax.yaml with alpha=0.3 | ✓ |
| C5: sparsemax, MSE, top-6 | ✓ | bert_sparsemax_top6.yaml: supervised_heads=[0..5] | ✓ |
| Seeds: 42–46 | 5 seeds | --array=0-4 → SEED=42+task_id | ✓ |

## Discrepancy Found (Documentation Only)

experiment-plan.md contains two condition tables with inconsistent C3/C4 labeling — an older draft where C3=sparsemax+MSE-all-12 and the final version where C3=sparsemax-no-sup. The actual configs and results use the correct final labeling. **No code change needed.**

## Decision: PROCEED — no blocking discrepancy
