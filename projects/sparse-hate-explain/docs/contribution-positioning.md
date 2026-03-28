# Contribution Positioning

## Differentiation Matrix

| Aspect | Our Work | Gao et al. (2024) RAG Survey | FaithJudge (2025) | MIRAGE (2024) | arxiv:2411.18583 |
|---|---|---|---|---|---|
| Focus | Literature synthesis | General RAG taxonomy | Faithfulness eval | Medical RAG | Auto lit review |
| Citation eval | Yes (primary) | No | No | No | Partial |
| Multi-doc synthesis | Yes | No | No | Single-doc QA | Yes |
| Error taxonomy | Yes (4-category) | No | Hallucination only | No | No |
| Benchmark provided | Yes (15 topics) | No | Yes (FaithJudge) | Yes (MIRAGE) | No |
| Human comparison | Yes (expert reviews) | No | Human annotation | No | ROUGE only |

## Contribution Statement

We make three contributions:

1. **LitSynthBench**: A benchmark of 15 ML/NLP topics with expert-written survey papers, candidate corpora, and human annotations for evaluating RAG-based literature synthesis.

2. **A comprehensive evaluation framework** measuring citation accuracy, factual consistency, coverage completeness, and error patterns — the first to jointly assess all four dimensions for multi-document scientific synthesis.

3. **An error taxonomy** for RAG-based literature synthesis, categorizing failures into citation hallucination, attribution error, omission, and recency bias, with inter-annotator agreement analysis.

## Anticipated Reviewer Objections

| Objection | Response |
|---|---|
| "ROUGE is not meaningful for review quality" | We use ROUGE only as secondary metric; primary eval is citation accuracy + faithfulness |
| "15 topics is small" | Each topic has ~200 papers; total evaluation covers ~3000 papers across topics |
| "Token overlap for faithfulness is too simple" | Lightweight proxy; we also include LLM-as-judge comparison in ablations |
| "Only ML/NLP domain" | Deliberate scope choice for controlled comparison; methodology transfers to other domains |
| "No human evaluation of review quality" | We include expert comparison as ground truth + plan annotation study |
