# Success Criteria Definition Guide

## Setting Quantitative Thresholds

### The Three Zones

For every hypothesis, define three outcome zones:

```
|-- FAILURE --|-- AMBIGUOUS --|-- SUCCESS --|
     < T_fail      T_fail-T_succ      > T_succ
```

- **Success zone**: Effect size >= T_succ AND statistical significance achieved
- **Ambiguous zone**: Some improvement but below threshold or not significant
- **Failure zone**: No improvement, negative result, or clearly below threshold

### How to Set Thresholds

#### Success Threshold (T_succ)

- Based on the minimum effect that is **meaningful** for the field
- Must include both effect size AND significance:
  - e.g., "+3% balanced accuracy with p < 0.05 (paired t-test, N subjects)"
- Consider what reviewers at the target venue would find convincing

#### Failure Threshold (T_fail)

- The point below which you should not continue pursuing the hypothesis
- Typically: no improvement or statistically indistinguishable from baseline
- e.g., "<+1% or p > 0.10"

#### Ambiguous Zone

- Between T_fail and T_succ
- Requires a decision: collect more data, adjust method, or reframe the contribution
- Pre-plan what to do in the ambiguous zone

## Statistical Significance Requirements

### Minimum Standards

| Test Type | Requirement |
|-----------|-------------|
| Pairwise comparison | p < 0.05 (two-tailed) |
| Multiple comparisons | Bonferroni or Holm correction |
| Effect size | Report Cohen's d or equivalent |
| Confidence interval | 95% CI for the primary metric |
| Sample description | N, seeds, folds clearly stated |

### When to Use Non-Parametric Tests

- Small sample size (N < 30)
- Non-normal distributions
- Ordinal or ranked data
- Use Wilcoxon signed-rank instead of paired t-test
- Use Mann-Whitney U instead of independent t-test

## Baseline Selection for Comparisons

### Required Baselines

1. **Trivial baseline**: Random chance, majority class, or simplest heuristic
2. **Standard baseline**: The most common method in the field
3. **SOTA baseline**: The best published result on the same benchmark
4. **Ablation baseline**: Your method minus the key component

### Baseline Fairness Checklist

- Same preprocessing pipeline
- Same train/val/test split
- Same hyperparameter search budget (or use published hyperparameters)
- Same hardware and software versions documented

## Handling Ambiguous Results

### Pre-Planned Decision Tree

```
Result in ambiguous zone
    |
    +-- Is the trend in the right direction?
    |     +-- YES: Collect more data (increase seeds/folds)
    |     +-- NO: Activate failure-diagnosis
    |
    +-- Is the variance high?
    |     +-- YES: Investigate sources of variance
    |     +-- NO: The effect may be real but small
    |
    +-- Is the effect practically meaningful?
          +-- YES: Consider reframing as a "modest but reliable" contribution
          +-- NO: Consider pivoting (activate hypothesis-revision)
```

## Abandon Criteria Design

### When to Abandon a Hypothesis

Define concrete conditions:

1. **N consecutive failures**: e.g., "If 3 different configurations all fail to show improvement"
2. **Resource limit**: e.g., "If we've used >50% of GPU budget with no positive signal"
3. **Stronger alternative found**: Another approach shows better results
4. **Fundamental flaw discovered**: The assumption underlying the hypothesis is wrong

### Abandon != Failure

- Negative results can be published (negative results papers)
- The systematic exploration is itself a contribution
- Document what was learned for future work
- Update `hypothesis-evolution.md` with the full decision chain

## Fallback Hypothesis Design

### Structure

```markdown
## If H1 fails:
- **Fallback H1'**: [Modified version with weaker claim or different approach]
  - What changes from H1
  - Why this might succeed where H1 failed
  - Additional cost to test
- **Fallback H1''**: [Further modification]
  - Even weaker claim or different angle
- **Abandon criteria**: [When to stop entirely]
```

### Good Fallback Strategies

1. **Weaken the claim**: "works for all subjects" -> "works for subjects with >N trials"
2. **Change the setting**: Cross-subject -> within-subject, or different dataset
3. **Change the method variant**: SimCLR -> BYOL -> VICReg
4. **Change the scope**: Full pipeline -> single component analysis
