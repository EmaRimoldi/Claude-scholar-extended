# Example: Hypothesis Evolution

## Project: Contrastive Pre-training for Cross-Subject EEG

## Evolution Chain

### Iteration 0: Original Hypothesis

**H1**: Contrastive pre-training (SimCLR) improves cross-subject EEG decoding by +5% balanced accuracy over supervised baseline

**Result**: +0.5% +/- 1.2% (not significant, p=0.42)

**Diagnosis**: Hyperparameter issue (LIKELY) — used default vision hyperparameters. Data issue (POSSIBLE) — standard augmentations not appropriate for EEG.

**Decision**: PERSEVERE — fixable hyperparameter issue, budget allows iteration

---

### Iteration 1: Persevere with Tuned Hyperparameters

**H1 (persevered)**: Same hypothesis, with tuned temperature (0.1) and batch size (256)

**Result**: +3.0% +/- 0.8% (significant, p=0.02, but below +5% target)

**Diagnosis**: Effect is real but below target. Representation analysis shows subjects are partially clustered — domain-specific augmentations may help.

**Decision**: PIVOT — effect confirmed but target not met; revise to include EEG-specific augmentations

---

### Iteration 2: Pivot to EEG-Specific Augmentations

**H1'**: Contrastive pre-training with EEG-specific augmentations (time warping, channel dropout, frequency masking) improves cross-subject EEG decoding by +4% balanced accuracy

- **What changed**: Added domain-specific augmentation strategy
- **Why**: Representation analysis showed standard augmentations did not capture EEG-relevant invariances
- **New prediction**: +4% (revised down from +5% based on Iteration 1 evidence)
- **Success threshold**: +3.5% with p < 0.05

**Result**: +4.2% +/- 0.6% (significant, p=0.003)

**Decision**: CONFIRMED — hypothesis H1' supported. Proceed to claim-evidence-bridge.

---

## Cumulative Learning

1. Contrastive learning does improve cross-subject EEG transfer, but the effect is moderate (+3-4%), not dramatic (+5%)
2. Domain-specific augmentations are critical — standard vision augmentations are insufficient for EEG
3. Temperature and batch size are the most sensitive hyperparameters for EEG contrastive learning
4. The combination of contrastive pre-training + EEG augmentations produces reliable, significant improvements

## Resource Summary

| Iteration | GPU-hours Used | Cumulative |
|---|---|---|
| 0 (original) | 360 | 360 |
| 1 (tuned) | 180 | 540 |
| 2 (augmented) | 228 | 768 |
| **Total** | | **768 / 1000** |

## Final State

```json
{
  "status": "confirmed",
  "iteration": 2,
  "active_hypothesis": "H1': Contrastive pre-training + EEG augmentations -> +4% balanced accuracy"
}
```
