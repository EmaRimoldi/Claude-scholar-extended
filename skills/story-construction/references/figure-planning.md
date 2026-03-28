# Figure Planning Guide

## Choosing Figure Type Based on Data

The figure type follows from the comparison being made, not from personal preference.

| Data Pattern | Figure Type | When to Use |
|-------------|-------------|-------------|
| Method A vs. Method B on metrics | Grouped bar chart | Discrete comparisons across methods |
| Performance over training steps/epochs | Line plot | Trends, convergence, dynamics |
| Performance across a swept parameter | Line plot with error bands | Sensitivity, scaling behavior |
| Correlation between two variables | Scatter plot | Relationship analysis |
| Performance across many conditions | Heatmap | Dense comparisons (datasets x methods) |
| Exact numbers matter | Table | When the reader needs precise values |
| System architecture or pipeline | Schematic diagram | Method overview (Figure 1) |
| Class-level performance breakdown | Confusion matrix | Error analysis, class imbalance effects |
| Distribution of results | Box plot or violin plot | Variability across seeds/subjects |
| Component contributions | Stacked bar chart | Ablation results, decomposition |

**Decision rule**: If the reader needs exact numbers, use a table. If the reader needs to see a pattern, use a figure. If both, use a figure in the main paper and a table in the appendix.

## Multi-Panel Layout Conventions

### Single Panel

Use when one comparison tells the story. Most figures in ML papers should be single-panel unless there is a strong reason to combine.

### 2-Panel (Side-by-Side)

Use when two views of the same result reinforce each other:
- Left: main comparison bar chart; Right: scaling curve
- Left: quantitative metric; Right: qualitative example
- Left: aggregate result; Right: per-class breakdown

### 2-Panel (Stacked)

Use when the panels share an x-axis:
- Top: primary metric; Bottom: secondary metric
- Top: training loss; Bottom: validation metric

### Multi-Panel Grid (e.g., 2x3, 3x3)

Use when showing the same analysis across conditions:
- Each panel: one dataset or one subject
- Shared axes and legend across all panels
- Clearly label each panel with the condition name

**Common mistake**: Using a 3x3 grid when a single grouped bar chart would be clearer. Multi-panel grids are justified only when per-condition patterns differ and that difference matters to the story.

## Statistical Annotation Conventions

### Error Bars

Always specify what the error bars represent in the caption:
- **Standard deviation (std)**: Shows spread of individual runs -- use when variability itself is the point
- **Standard error of the mean (SEM)**: Shows precision of the mean estimate -- use for method comparisons
- **95% confidence interval**: Shows statistical uncertainty -- preferred for publication

**Never** show error bars without stating what they are. "Error bars show X" must appear in the caption.

### Significance Brackets

Use horizontal brackets connecting compared bars with significance notation:
- `*` for p < 0.05
- `**` for p < 0.01
- `***` for p < 0.001
- `n.s.` for not significant (when the comparison is expected or relevant)

Place brackets above the bars, not overlapping. For multiple comparisons, show only the comparisons that matter for the story (typically: proposed method vs. each baseline).

### Effect Size Annotations

Report effect size alongside p-values when space permits:
- Cohen's d for pairwise comparisons
- Partial eta-squared for multi-group comparisons
- Include in the figure caption or as text annotations on the figure

### Baseline Reference Lines

Add a horizontal dashed line for important baselines:
- Random chance level
- Human performance (if available)
- Previous SOTA

Label the reference line directly on the figure, not only in the legend.

## Figure-to-Text Ratio Guidelines by Venue

| Venue | Main Paper Figures | Tables | Total Visual Elements | Notes |
|-------|-------------------|--------|----------------------|-------|
| NeurIPS/ICML/ICLR | 3-5 | 1-3 | 5-6 | Prefer figures over tables for main results |
| Nature/Science | 3-4 | 0-1 | 3-4 | Clean, high-impact; extended data in supplement |
| ACL/EMNLP | 3-4 | 2-3 | 5-6 | Tables common for NLP benchmarks |
| Workshop | 2-3 | 1-2 | 3-4 | Space is tight; one key figure can carry the paper |
| Journal (JMLR/TMLR) | 5-8 | 3-5 | 8-12 | Comprehensive; include all relevant analyses |

**General rule**: Each figure should earn its page space by communicating something that text alone cannot. If a figure can be replaced by a single sentence, remove it.

## Designing the Method Figure (Figure 1)

Most ML papers include a schematic of the method as Figure 1. Design principles:

- **Left-to-right flow**: Input on the left, output on the right
- **Annotate the novel part**: Highlight what is new (color, bold box, annotation)
- **Minimal text**: Labels, not sentences
- **Consistent notation**: Match symbols in the figure to symbols in the text
- **No unnecessary detail**: Show the conceptual architecture, not every layer

## Common Figure Mistakes

### Too Many Panels

**Symptom**: A 4x4 grid where each panel has 3 bars, for a total of 48 data points displayed.

**Fix**: Aggregate. Show the main comparison in one panel and per-condition breakdowns in the appendix.

### Unclear Legends

**Symptom**: Five methods with similar colors and abbreviated names that require reading the text to decode.

**Fix**: Use distinct colors from a colorblind-safe palette (e.g., Okabe-Ito). Use full method names. Place the legend where it does not overlap data.

### Missing Error Bars

**Symptom**: Bar chart comparing 5 methods with single-point estimates and no indication of variability.

**Fix**: Always show variability when multiple runs exist. If only one run was performed, state this explicitly and acknowledge it as a limitation.

### Inconsistent Scales

**Symptom**: Two panels in the same figure use different y-axis ranges, making visual comparison misleading.

**Fix**: Use shared axes when panels are meant to be compared. If different scales are necessary (e.g., different metrics), state this clearly.

### Decorative Figures

**Symptom**: A figure that looks visually interesting but does not communicate a specific finding. The caption describes what is shown but not what the reader should learn.

**Fix**: Every figure must have a reader takeaway: "This figure shows that [finding]." If you cannot write that sentence, the figure is decorative and should be removed or redesigned.

### Overly Complex Schematics

**Symptom**: Method figure with 20+ boxes, arrows crossing, and text in 6-point font.

**Fix**: Show the high-level architecture in the main paper. Move detailed component diagrams to the appendix. The method figure should be understandable in 30 seconds.
