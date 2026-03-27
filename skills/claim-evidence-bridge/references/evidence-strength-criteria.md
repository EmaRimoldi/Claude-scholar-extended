# Evidence Strength Assessment

## The Four Levels

### Strong Evidence

The claim is well-supported and can be stated confidently.

**Criteria** (ALL must be met):
- Statistically significant (p < 0.05 or equivalent)
- Replicated across multiple seeds, folds, or runs
- Consistent across primary AND secondary metrics
- No obvious confounding variables
- Comparison against appropriate baselines

**Language**: "We show that...", "Our method achieves...", "X significantly improves Y"

### Moderate Evidence

The claim has support but with caveats.

**Criteria** (ANY of these):
- Significant but small effect size (may not be practically meaningful)
- Significant on one dataset but not tested on others
- Significant on primary metric but inconsistent on secondary metrics
- Missing an important control or baseline
- Based on standard train/test split without cross-validation

**Language**: "Our results suggest...", "We observe that...", "competitive with...", "In our experiments, X tends to..."

### Weak Evidence

The claim has minimal support and should be heavily qualified.

**Criteria** (ANY of these):
- Not statistically significant (p > 0.05)
- Based on a single run without replication
- Contradicted by some metrics or settings
- Large confidence intervals that include zero effect
- Only qualitative support (looks good but no quantitative measure)

**Language**: "Preliminary results indicate...", "We note a trend toward...", move to supplementary or future work

### Unsupported

The claim has no evidence or evidence contradicts it.

**Criteria** (ANY of these):
- No experiment was conducted to test this claim
- Evidence contradicts the claim
- The claim goes beyond what the evidence shows (e.g., claiming "generalizes" based on one dataset)
- The claim is about a different setting than what was tested

**Language**: Remove from main claims. At most: "We hypothesize that... [future work]"

## Common Patterns That Inflate Perceived Strength

1. **Cherry-picking metrics**: Reporting only the metric that looks good
2. **Cherry-picking seeds**: Reporting the best seed instead of the mean
3. **Missing baselines**: Not comparing against the strongest available baseline
4. **p-hacking**: Testing many comparisons and reporting only significant ones
5. **Conflating significance with importance**: A statistically significant but tiny effect
6. **Generalization overclaims**: "Our method works for X" when tested only on one instance of X
7. **Implying causation from correlation**: "X improves Y" when X and Y are confounded

## Statistical Significance vs. Practical Significance

A result can be:
- **Statistically significant AND practically significant**: Report confidently
- **Statistically significant but NOT practically significant**: Hedge -- "While statistically significant, the effect is small (0.5%)"
- **NOT statistically significant but practically meaningful**: Report with caveat -- "We observe a +3% improvement that did not reach significance with N=5 seeds; a larger study is needed"
- **Neither**: Do not claim
