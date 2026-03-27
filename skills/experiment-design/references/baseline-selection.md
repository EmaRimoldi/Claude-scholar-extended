# Baseline Selection Guide

## Baseline Categories

### 1. Trivial Baselines (Always Required)

The simplest possible approach that requires no learning:

| Task Type | Trivial Baseline |
|-----------|-----------------|
| Classification | Majority class prediction |
| Regression | Mean/median prediction |
| Generation | Random sampling from data distribution |
| Ranking | Random ordering |
| Retrieval | TF-IDF or BM25 |

**Purpose**: Establishes the floor. If your method doesn't beat trivial baselines, something is wrong.

### 2. Standard Baselines (Always Required)

The most commonly used methods in the field:

- Check the "Baselines" or "Compared Methods" sections of 5 recent papers on the same task
- Use the methods that appear in 3+ papers
- Reproduce with their published hyperparameters if available

**Purpose**: Shows where your method stands relative to common practice.

### 3. SOTA Baselines (Strongly Recommended)

The best published result on the same benchmark:

- Check Papers With Code for the current leaderboard
- Use the official implementation if available
- If no official code exists, use the published numbers with a citation

**Purpose**: Shows whether your method advances the state of the art.

### 4. Ablation Baselines (Required for Novel Methods)

Your method with key components removed:

- "Our method - contrastive loss" (tests whether the contrastive objective helps)
- "Our method - adapter modules" (tests whether the adapters help)
- "Our method with random initialization" (tests whether pre-training helps)

**Purpose**: Isolates the contribution of each novel component.

## Fairness Checklist

Before reporting baseline results, verify:

- [ ] Same preprocessing pipeline (normalization, augmentation, filtering)
- [ ] Same train/validation/test split
- [ ] Same number of hyperparameter search trials (or use published hyperparameters)
- [ ] Same hardware documented (for runtime comparisons)
- [ ] Same software versions documented (framework, CUDA, etc.)
- [ ] Same evaluation protocol (same metrics, same averaging method)
- [ ] Same random seeds (for reproducibility)

### Common Fairness Violations

| Violation | Why It's a Problem | Fix |
|-----------|-------------------|-----|
| Tuning your method but using default hyperparameters for baselines | Unfair advantage | Give baselines the same tuning budget |
| Different preprocessing for different methods | Confounds the comparison | Use identical preprocessing pipeline |
| Cherry-picking the best seed for your method | Inflates results | Report mean +/- std across seeds |
| Using a weaker implementation of the baseline | Straw man comparison | Use official implementations or reimplement carefully |

## Finding Published Baselines

### Sources

1. **Papers With Code** (paperswithcode.com): Benchmark leaderboards with code links
2. **Original benchmark papers**: Often include baseline results
3. **Survey papers**: Compare many methods on the same benchmarks
4. **Official repositories**: GitHub repos of compared methods

### When Published Numbers Are Unavailable

1. First: Try to run the official code with default settings
2. Second: Reimplement following the paper description
3. Third: Cite the published numbers with a note about different setup
4. Always: Document what you did and why

## How Many Baselines?

### Minimum Requirements by Venue

| Venue Tier | Minimum Baselines |
|-----------|------------------|
| Top conference (NeurIPS, ICML, ICLR) | 4-6 baselines + ablations |
| Second-tier conference (AAAI, IJCAI) | 3-5 baselines + ablations |
| Workshop paper | 2-3 baselines |
| Journal (extended) | 5-8 baselines + extensive ablations |

### Selection Strategy

1. Always include: trivial baseline + standard baseline + SOTA
2. Add domain-specific baselines relevant to your contribution
3. Add ablation baselines for each novel component
4. Avoid padding with too many weak baselines (reviewers notice)
