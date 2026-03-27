# Ablation Study Planning Guide

## Purpose of Ablation Studies

Ablation studies answer: "Which components of my method actually matter?"

They isolate the contribution of each novel component by systematically removing or replacing it and measuring the impact on performance.

## Component Identification

### Step 1: List All Novel Components

For each element of your method that differs from the standard approach:

```markdown
| Component | What It Does | Is It Novel? |
|-----------|-------------|-------------|
| Contrastive pre-training | Learns representations before fine-tuning | Yes (core) |
| Subject-specific adapters | Adapt shared model to each subject | Yes (supporting) |
| EEG-specific augmentations | Time warping, channel dropout | Partially (novel combination) |
| Transformer encoder | Processes EEG sequences | No (standard architecture) |
```

### Step 2: Classify by Importance

- **Core components**: The main contribution (must ablate)
- **Supporting components**: Help the core work better (should ablate)
- **Standard components**: Common building blocks (ablate only if surprising)

## Ablation Ordering Strategies

### Strategy 1: Remove One at a Time (Standard)

Remove each novel component independently while keeping everything else:

```
Full method:           A + B + C = 85%
Remove A:              _ + B + C = 78%  → A contributes ~7%
Remove B:              A + _ + C = 82%  → B contributes ~3%
Remove C:              A + B + _ = 80%  → C contributes ~5%
```

**Best for**: Independent components, small number of ablations.

### Strategy 2: Build Up (Additive)

Start from the simplest baseline and add components one at a time:

```
Baseline:              _         = 70%
Add A:                 A         = 77%  → A adds +7%
Add A + B:             A + B     = 80%  → B adds +3%
Add A + B + C:         A + B + C = 85%  → C adds +5%
```

**Best for**: When components build on each other, clear dependency chain.

### Strategy 3: Factorial (Comprehensive)

Test all combinations of components:

```
_         = 70%
A         = 77%
B         = 73%
C         = 72%
A + B     = 80%
A + C     = 82%
B + C     = 76%
A + B + C = 85%
```

**Best for**: When interaction effects matter. Expensive (2^N combinations).

### Choosing a Strategy

| # of components | Recommended strategy |
|----------------|---------------------|
| 1-2 | Remove-one-at-a-time (complete) |
| 3-4 | Build-up OR remove-one-at-a-time |
| 5+ | Build-up with selected pairwise interactions |

## Interaction Effect Detection

### When to Check for Interactions

- When two components operate on the same data
- When one component's output feeds into another
- When the combined effect seems larger than the sum of individual effects

### How to Check

Compare:
- Effect of A alone: full - (full without A) = delta_A
- Effect of B alone: full - (full without B) = delta_B
- Effect of removing both: full - (full without A and B) = delta_AB

If delta_AB >> delta_A + delta_B: **positive interaction** (synergy)
If delta_AB << delta_A + delta_B: **negative interaction** (redundancy)

## Reporting Ablation Results

### Standard Table Format

```markdown
| Method | Metric 1 | Metric 2 | Delta |
|--------|----------|----------|-------|
| Full method | 85.0 +/- 1.2 | 0.82 | -- |
| w/o Component A | 78.0 +/- 1.5 | 0.75 | -7.0 |
| w/o Component B | 82.0 +/- 1.1 | 0.79 | -3.0 |
| w/o Component C | 80.0 +/- 1.3 | 0.77 | -5.0 |
| Baseline | 70.0 +/- 2.0 | 0.65 | -15.0 |
```

### Reporting Checklist

- [ ] Report mean +/- std across seeds
- [ ] Include statistical significance for key ablations
- [ ] State what "w/o Component X" means concretely (what was removed or replaced)
- [ ] Order by impact (largest delta first) or by conceptual importance
- [ ] Discuss surprising results (component that helped less/more than expected)
- [ ] Link ablation results back to hypotheses

## Common Ablation Mistakes

### 1. Ablating Too Little

Only removing the most obvious component. Reviewers expect thorough ablations.

### 2. Unfair Ablations

Removing a component without adjusting hyperparameters. The ablated model may need different learning rate, etc.

### 3. Not Reporting Negative Ablations

If removing a component doesn't hurt (or helps), report it! This is valuable information.

### 4. Ablation Without Hypothesis

Every ablation should test a specific prediction:
- "We predict that removing the contrastive loss will cause a large drop because it is the core contribution"
- If the prediction is wrong, discuss why
