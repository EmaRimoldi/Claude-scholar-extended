# Example: Failure Diagnosis

## Observed vs. Expected

- **Hypothesis**: H1 — Contrastive pre-training improves cross-subject EEG decoding by +5% balanced accuracy
- **Expected**: +5% balanced accuracy over supervised baseline
- **Observed**: +0.5% +/- 1.2% (not significant, p=0.42)
- **Gap**: 4.5 percentage points below target; effect not even directionally reliable

## Failure Mode Analysis

### 1. Hyperparameter Issue — LIKELY

**Evidence for**:
- No hyperparameter sweep was performed; used default SimCLR settings from vision domain
- Contrastive learning is known to be sensitive to temperature, batch size, and augmentation strategy
- Training curves show the contrastive loss plateauing early (possible temperature issue)

**Evidence against**:
- Learning rate was chosen from prior EEG work (reasonable starting point)

**Diagnostic test**: Grid search over temperature {0.05, 0.1, 0.5} and batch size {64, 256, 1024}
**Cost**: ~6 GPU-hours
**Expected outcome if cause**: At least one configuration shows >+2% improvement

### 2. Data Issue — POSSIBLE

**Evidence for**:
- EEG signals have high inter-subject variability
- Standard vision augmentations (crop, flip) are not meaningful for time-series EEG data
- No domain-specific augmentations were used

**Evidence against**:
- Data preprocessing followed the standard benchmark pipeline
- Training loss decreased normally

**Diagnostic test**: Visualize learned representations with t-SNE; check if contrastive learning clusters by subject (bad) or by task (good)
**Cost**: ~1 hour
**Expected outcome if cause**: Representations cluster by subject, not by task class

### 3. Hypothesis Wrong — POSSIBLE but premature

**Evidence for**:
- EEG is fundamentally different from vision/NLP where contrastive learning succeeds
- Signal-to-noise ratio in EEG is very low

**Evidence against**:
- Contrastive learning works for medical imaging transfer (similar domain)
- Only one configuration tested — insufficient evidence to reject the hypothesis

**Diagnostic test**: Run on a vision benchmark (CIFAR-10 with synthetic domain shift) to verify the implementation works in a known-good setting
**Cost**: ~2 GPU-hours
**Expected outcome if cause**: Method works on vision (implementation correct), but EEG is genuinely harder

### 4. Implementation Bug — UNLIKELY

**Evidence for**: None specific
**Evidence against**: Training loss decreased; model produced non-trivial predictions; overfit check passed

### 5. Metric Issue — UNLIKELY

**Evidence for**: None; balanced accuracy is standard for this benchmark
**Evidence against**: Multiple metrics (accuracy, balanced accuracy, kappa) all show similar results

### 6. Baseline Stronger Than Expected — UNLIKELY

**Evidence for**: None; baseline matches published numbers
**Evidence against**: Baseline performance is within expected range

## Recommended Next Steps (priority order)

1. **Run hyperparameter sweep** (6 GPU-hours) — highest likelihood, moderate cost
2. **Visualize representations** (1 hour) — possible cause, very low cost
3. **Sanity-check on vision benchmark** (2 GPU-hours) — rules out implementation bug
4. If all above pass: consider EEG-specific augmentation strategies before concluding hypothesis is wrong

## State Update

`experiment-state.json` -> status: "diagnosing", iteration: 1
