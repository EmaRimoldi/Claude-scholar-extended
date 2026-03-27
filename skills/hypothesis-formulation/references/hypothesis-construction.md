# Hypothesis Construction Guide

## From Research Question to Testable Prediction

### Step 1: Identify the Core Claim

Extract the central assertion from the research question:

- **Research question**: "Can contrastive pre-training improve cross-subject EEG decoding?"
- **Core claim**: Contrastive pre-training improves cross-subject EEG decoding accuracy

### Step 2: Make It Specific (SMART Framework)

| Criterion | Question | Example |
|-----------|----------|---------|
| **Specific** | What exactly will improve? | Balanced accuracy on held-out subjects |
| **Measurable** | How will you measure it? | Paired t-test across N subjects |
| **Achievable** | Is the expected effect realistic? | +5% based on similar NLP/vision gains |
| **Relevant** | Does this matter for the field? | Cross-subject transfer is a key BCI bottleneck |
| **Time-bound** | When will you know? | After running on BCI-IV-2a (9 subjects) |

### Step 3: Formulate the Prediction

Structure each hypothesis with these fields:

```markdown
## H1: [One-line summary]
- **Prediction**: [What will happen]
- **Metric**: [How you measure it]
- **Baseline**: [What you compare against]
- **Expected effect**: [Quantitative prediction with justification]
- **Success threshold**: [Minimum to claim success + significance level]
- **Failure threshold**: [Below what result do you reject?]
```

### Step 4: State the Null Hypothesis

The null hypothesis must be:
- The default assumption (no effect)
- Falsifiable by the experiment
- Stated in terms of the same metric

Example: "Contrastive pre-training provides no statistically significant improvement over supervised training from scratch."

## Effect Size Estimation Strategies

### From Prior Work

1. Find 3-5 papers using similar methods on similar tasks
2. Extract their reported improvements
3. Use the median as your expected effect size
4. Use the range to set success/failure thresholds

### From Domain Conventions

| Domain | Typical "meaningful" effect |
|--------|---------------------------|
| NLP classification | +1-3% accuracy |
| Computer vision | +0.5-2% mAP |
| EEG/BCI | +2-5% balanced accuracy |
| Medical imaging | +1-3% AUC |
| Reinforcement learning | 2x-10x sample efficiency |

### When No Prior Exists

State explicitly: "No prior effect size available. Using [convention/pilot] as estimate. This is a rough guide, not an evidence-based prediction."

## Common Pitfalls

### 1. Unfalsifiable Hypotheses

- BAD: "Our method will provide insights into EEG transfer learning"
- GOOD: "Our method will achieve >70% balanced accuracy on cross-subject EEG (vs. 65% baseline)"

### 2. Moving the Goalposts

- Define success/failure criteria BEFORE running experiments
- Record them in `hypotheses.md` before starting

### 3. Too Many Hypotheses

- Limit to 1 primary + 2-3 secondary hypotheses
- Each hypothesis should require different evidence
- If two hypotheses need the same experiment, merge them

### 4. Ignoring Base Rates

- Always check: what does random chance achieve?
- Always check: what does the simplest baseline achieve?
- Your hypothesis must predict something ABOVE these floors

## Metric Selection Methodology

### Choosing the Primary Metric

1. **Standard for the benchmark**: Use what the community uses (enables comparison)
2. **Aligned with the hypothesis**: The metric must directly measure what you predict
3. **Robust to class imbalance**: Prefer balanced accuracy, F1, or AUC over raw accuracy
4. **Interpretable**: Reviewers must understand what the number means

### Secondary Metrics

Include 1-2 secondary metrics that:
- Capture different aspects of performance
- Serve as sanity checks
- May reveal unexpected behaviors (e.g., calibration, efficiency)
