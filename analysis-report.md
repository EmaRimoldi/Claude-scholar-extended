# Analysis Report: RAG for Scientific Literature Synthesis

> **Status**: Template — awaiting experiment results. Synthetic placeholders marked with [PLACEHOLDER].

## 1. Summary Statistics

### Citation Accuracy (H1)

| Condition | Citation Precision | Citation Recall | F1 |
|---|---|---|---|
| C1: RAG + Dense | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| C2: RAG + BM25 | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| C3: RAG + Hybrid | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| C4: No Retrieval | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| C5: Expert Human | >0.95 (expected) | >0.90 (expected) | >0.92 (expected) |

### Factual Consistency (H2)

| Condition | Faithfulness | Hallucination Rate |
|---|---|---|
| C1: RAG + Dense | [PLACEHOLDER] | [PLACEHOLDER] |
| C4: No Retrieval | [PLACEHOLDER] | [PLACEHOLDER] |

### Coverage (H3)

| Condition | Key Paper Recall | Recency ρ | Popularity ρ |
|---|---|---|---|
| C1: RAG + Dense | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| C3: RAG + Hybrid | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

## 2. Statistical Tests

- H1: Paired t-test / Wilcoxon signed-rank between RAG and human
- H2: Mann-Whitney U between RAG and no-retrieval
- H3: Spearman correlation for bias analysis
- All tests: p < 0.05 threshold, Bonferroni correction for multiple comparisons

## 3. Ablation Analysis

### Chunk size effect (A1)
[PLACEHOLDER: Table of metrics across chunk sizes 256/512/1024]

### Top-k effect (A2)
[PLACEHOLDER: Table of metrics across top_k 3/5/10/20]

### Prompt type effect (A3)
[PLACEHOLDER: Table of metrics across zero_shot/few_shot/CoT]

## 4. Error Taxonomy (H4)

| Error Category | Definition | Expected Frequency |
|---|---|---|
| Citation hallucination | Citing non-existent papers | ~15-25% of errors |
| Attribution error | Correct paper, wrong claim | ~20-30% of errors |
| Omission | Missing key papers | ~30-40% of errors |
| Recency bias | Over-representing recent work | ~10-20% of errors |

## 5. Figures Plan

1. **Fig 1**: Bar chart — Citation precision by condition
2. **Fig 2**: Scatter plot — Faithfulness vs. hallucination rate
3. **Fig 3**: Heatmap — Key Paper Recall across topics × conditions
4. **Fig 4**: Error distribution pie chart
5. **Fig 5**: Ablation curves (top-k vs. citation precision)

## 6. Key Findings

[PLACEHOLDER: Will be populated after experiments complete]

## Next Steps

- Run experiments after setting up Python 3.10+ environment
- Populate this report with actual results
- Run statistical tests
- Generate publication-quality figures
