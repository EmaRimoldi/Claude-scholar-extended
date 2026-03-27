# Failure Taxonomy

Detailed reference for diagnosing research-level experiment failures.

## Mode 1: Hypothesis Wrong

The fundamental approach does not work for this problem.

### Diagnostic Signals
- Effect is absent across ALL configurations (not just the default)
- Known working baselines that use similar ideas also fail in your setting
- Theoretical analysis suggests the approach shouldn't work here
- Multiple independent implementations show the same negative result

### Red Flags
- Rushing to conclude "hypothesis wrong" after only one configuration
- Not distinguishing between "doesn't work at all" and "works less than expected"

### Diagnostic Experiments
- Run the method on a known-good benchmark where it should work
- If it fails on the known-good benchmark → likely implementation bug, not wrong hypothesis
- If it works on known-good but not your task → hypothesis may genuinely be wrong for this setting

## Mode 2: Implementation Bug

The code does not do what the researcher intended.

### Diagnostic Signals
- Results are much worse than expected (not just slightly worse)
- Training loss does not decrease at all, or decreases then diverges
- Results are inconsistent across seeds in unexpected ways
- Known sanity checks fail (e.g., overfitting a small batch)

### Red Flags
- Assuming the code is correct because "it runs without errors"
- Not checking intermediate outputs (embeddings, attention patterns, gradients)

### Diagnostic Experiments
- Overfit a single batch (should reach ~100% training accuracy)
- Print gradient norms per layer (check for vanishing/exploding)
- Verify data loading by visualizing raw inputs and labels
- Compare outputs with a reference implementation if available

## Mode 3: Hyperparameter Issue

The approach works but the configuration is not tuned.

### Diagnostic Signals
- Performance varies significantly across hyperparameter settings
- Default hyperparameters from a different domain/setting are being used
- Training curves show instability (oscillation, slow convergence)
- The method works on some data splits but not others

### Red Flags
- Running a full hyperparameter sweep without first confirming the approach works at all
- Tuning only learning rate when the issue may be architectural (hidden dim, depth)

### Diagnostic Experiments
- Quick sweep over the 2-3 most sensitive hyperparameters (usually: learning rate, batch size, key architectural choice)
- Use logarithmic spacing for learning rate (1e-5 to 1e-2)
- Start with the hyperparameters from the closest prior work

## Mode 4: Data Issue

Data quality, distribution, or quantity problems.

### Diagnostic Signals
- Performance varies dramatically across data splits or subgroups
- Training accuracy is high but test accuracy is low (overfitting → insufficient/biased data)
- Class imbalance or label noise patterns visible in confusion matrix
- Features show unexpected distributions (check for preprocessing errors)

### Red Flags
- Assuming data is clean without inspection
- Not checking for data leakage between train and test sets
- Using a different preprocessing pipeline than the baseline

### Diagnostic Experiments
- Visualize data distributions (histograms, t-SNE of features)
- Check label accuracy on a random subsample (manual inspection)
- Run on a clean, well-studied benchmark to isolate data issues from method issues
- Check for leakage: train on test set, test on train set (should overfit perfectly)

## Mode 5: Metric Issue

The evaluation metric does not capture what the researcher cares about.

### Diagnostic Signals
- Quantitative metrics look bad but qualitative results look reasonable
- Different metrics tell contradictory stories (e.g., accuracy good, F1 bad)
- The metric is sensitive to factors orthogonal to the contribution (e.g., class imbalance)

### Red Flags
- Using only a single metric
- Using accuracy with imbalanced classes
- Not reporting confidence intervals or significance tests

### Diagnostic Experiments
- Compute multiple complementary metrics (accuracy, balanced accuracy, F1, AUC)
- Check metric sensitivity to class distribution (resample and re-evaluate)
- Qualitative evaluation: look at actual predictions, not just numbers

## Mode 6: Baseline Stronger Than Expected

The comparison baseline performs better than anticipated.

### Diagnostic Signals
- Baseline performance is above published numbers (possible data leakage or different setup)
- Baseline used a different (better) preprocessing or hyperparameter tuning
- The field has progressed since the hypothesis was formulated
- Your baseline implementation may be stronger than the one in the original paper

### Red Flags
- Not using the same preprocessing for proposed method and baseline
- Not verifying that your baseline reproduction matches published numbers
- Using a "straw man" baseline that is weaker than current SOTA

### Diagnostic Experiments
- Verify baseline implementation matches published results
- Check if baseline uses the exact same data preprocessing
- Compare with independently reproduced baselines (e.g., from OpenML, Papers With Code)
