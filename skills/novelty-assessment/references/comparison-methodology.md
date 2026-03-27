# Comparison Methodology Guide

## Identifying Closest Related Works

### Step 1: Decompose Your Contribution

Break your contribution into atomic claims:
- What problem do you solve?
- What method do you use?
- What domain/setting do you target?
- What is your key insight?

### Step 2: Search Along Each Axis

For each atomic claim, find papers that match:
- **Same problem, different method**: Method competitors
- **Same method, different problem**: Application variants
- **Same problem, same method, different setting**: Direct competitors (highest overlap risk)

### Step 3: Rank by Overlap

Score each paper on overlap with your contribution:
- **0 (None)**: Different problem and method
- **1 (Low)**: Shares problem or method but not both
- **2 (Medium)**: Shares problem and method, different setting or analysis
- **3 (High)**: Shares problem, method, and setting — direct competitor

Papers scoring 2-3 are your closest related works.

## Comparison Framework

### The Comparison Matrix

For each related work, document:

| Dimension | Related Work | Your Proposal | Delta |
|---|---|---|---|
| Problem setting | ... | ... | ... |
| Method | ... | ... | ... |
| Key insight | ... | ... | ... |
| Evaluation | ... | ... | ... |
| Limitations | ... | ... | ... |

### Delta Assessment Rules

- **Method variant**: Same overall approach, different component (e.g., different loss function)
- **Architecture extension**: Adding a module to an existing framework
- **Complementary**: Addresses a different aspect of the same problem
- **Direct overlap**: Very similar contribution — highest risk

## Venue-Specific Novelty Bars

### Tier 1: NeurIPS, ICML, ICLR
- **Required**: Novel method with theoretical or surprising empirical insight
- **Not sufficient**: Method combination without new understanding
- **Not sufficient**: Same method on a new benchmark without new findings
- **Typical delta**: Must clearly articulate what the community learns that it didn't know before

### Tier 2: AAAI, IJCAI, AISTATS, COLM
- **Accepted**: Novel applications of known methods with interesting findings
- **Accepted**: Significant engineering contributions with thorough evaluation
- **Still required**: Clear contribution beyond incremental improvement

### Workshops and Smaller Venues
- **Accepted**: Preliminary results, interesting negative results
- **Accepted**: Incremental improvements with good analysis
- **Good for**: Testing ideas before committing to a full paper

## Common Novelty Pitfalls

1. **Method combination ≠ novelty**: Combining two existing techniques (A+B) is not automatically novel unless the combination reveals something unexpected
2. **New benchmark ≠ contribution**: Running existing methods on a new dataset is not a contribution unless it reveals new insights
3. **Scale ≠ insight**: Running at larger scale is interesting only if qualitatively new behaviors emerge
4. **Concurrent work overlap**: If very similar work appears on arXiv during your project, you must clearly articulate your unique delta
5. **Self-comparison only**: Comparing only against your own baselines without established SOTA is insufficient
