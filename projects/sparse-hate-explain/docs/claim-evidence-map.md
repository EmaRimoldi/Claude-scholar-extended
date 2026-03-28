# Claim-Evidence Map

## Paper Claims and Supporting Evidence

### Claim 1: RAG systems produce lower citation accuracy than human reviewers
- **Evidence needed**: H1 results — citation precision/recall comparison
- **Experiments**: C1-C3 vs C5 across 15 topics
- **Status**: Awaiting experiment results

### Claim 2: RAG reduces hallucinations vs. no-retrieval generation
- **Evidence needed**: H2 results — faithfulness score comparison
- **Experiments**: C1-C3 vs C4
- **Status**: Awaiting experiment results

### Claim 3: RAG-generated reviews have systematic coverage gaps
- **Evidence needed**: H3 results — KPR + bias correlations
- **Experiments**: KPR analysis + Spearman correlations
- **Status**: Awaiting experiment results

### Claim 4: RAG errors cluster into four categories
- **Evidence needed**: H4 results — annotation study
- **Experiments**: Error annotation on ≥5 topics, κ agreement
- **Status**: Awaiting annotation data

### Claim 5: Hybrid retrieval outperforms BM25 and dense-only
- **Evidence needed**: Ablation A1-A4 results
- **Experiments**: Condition comparison C1 vs C2 vs C3
- **Status**: Awaiting experiment results

### Claim 6: Our benchmark enables standardized RAG evaluation
- **Evidence needed**: Benchmark construction methodology + reproducibility
- **Experiments**: Data pipeline code + manifest
- **Status**: Code complete, data pipeline ready

## Scope Assessment

| Claim | Evidence Available | Include in Paper? |
|---|---|---|
| C1: Citation accuracy gap | Pending | Yes (primary) |
| C2: Hallucination reduction | Pending | Yes (primary) |
| C3: Coverage gaps | Pending | Yes (primary) |
| C4: Error taxonomy | Pending | Yes (primary) |
| C5: Hybrid advantage | Pending | Yes (secondary) |
| C6: Benchmark contribution | Available | Yes (contribution) |
