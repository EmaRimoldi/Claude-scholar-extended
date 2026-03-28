# Literature Review: RAG for Scientific Literature Synthesis

## 1. Overview of RAG Systems

Retrieval-Augmented Generation (RAG) combines retrieval mechanisms with generative language models to produce grounded, factual outputs. Recent systematic reviews (Gao et al., 2024; arxiv:2506.00054) survey architectures across naive RAG, advanced RAG (query refinement, re-ranking), and modular RAG (graph-of-thoughts, hierarchical planning).

### Key surveys
- Gao et al. (2024) — "Retrieval-Augmented Generation for Large Language Models: A Survey" — comprehensive taxonomy of RAG approaches
- arxiv:2506.00054 (2025) — "Comprehensive Survey of Architectures, Enhancements, and Robustness Frontiers" — 128 articles, Jan 2020–May 2025
- arxiv:2507.18910 (2025) — systematic review of key RAG systems identifying progress and gaps
- MDPI Big Data and Cognitive Computing (2025) — systematic literature review of techniques, metrics, and challenges

## 2. RAG for Literature Review Generation

### Automated review generation
- arxiv:2411.18583 (2024) — "Automated Literature Review Using NLP Techniques and LLM-Based RAG" — direct comparison of RAG-based vs traditional NLP approaches for literature review automation
- arxiv:2407.20906 (2024) — "Automated Review Generation Method Based on Large Language Models" — multi-layered quality control achieving <0.5% hallucination rate
- EMNLP 2025 — "Large Language Models for Automated Literature Review" — evaluation framework assessing reference generation, abstract writing, and review composition
- NSR (2025) — Automated literature research and review-generation method — end-to-end pipeline

### Performance benchmarks
- GPT-3.5-turbo achieves ROUGE-1 of 0.364 for review generation
- AI tools reduce manual screening by >60% while maintaining >90% recall
- Expert verification confirms hallucination risks below 0.5% with multi-layer QC

## 3. Hallucination and Citation Accuracy in RAG

### Benchmarks
- **FaithJudge** (EMNLP 2025) — LLM-as-a-judge framework for faithfulness evaluation across summarization, QA, data-to-text
- **MIRAGE** — medical RAG benchmark with 7,663 questions, zero-shot evaluation
- **RAGTruth** — hallucination detection benchmark and evaluation protocols
- **Confabulations Benchmark** (GitHub: lechmazur/confabulations) — human-verified QA for document-based RAG
- **HHEM** — Hughes Hallucination Evaluation Model, tracking hallucination rates since 2023

### Detection methods
- LLM-as-a-Judge, Prometheus, Lynx, HHEM, TLM (arxiv:2503.21157)
- Faithfulness metric: fraction of claims supported by provided context
- Citation verification: mapping answer spans to retrieved passage spans

## 4. Evaluation Metrics for Literature Synthesis

| Metric Category | Specific Metrics | Purpose |
|---|---|---|
| Lexical overlap | ROUGE-1/2/L, BLEU | Surface similarity to reference |
| Factual consistency | FaithJudge, HHEM, TLM | Hallucination detection |
| Citation accuracy | Citation precision/recall, attribution score | Correct source mapping |
| Coverage | KPR, recall of key papers | Completeness of review |
| Human evaluation | Expert ratings, inter-rater κ | Quality assessment |

## 5. Research Gaps Identified

1. **No benchmark for citation-grounded literature synthesis**: Existing benchmarks evaluate QA or summarization, not multi-document scientific review with citation requirements
2. **Limited evaluation of citation accuracy**: Most RAG evaluations focus on factual consistency but not on whether citations map correctly to claims
3. **Missing comparison to human-written reviews**: No systematic comparison between RAG-generated and expert-written literature reviews on the same topic
4. **Error taxonomy**: No structured taxonomy of errors specific to RAG-based literature synthesis (hallucinated citations, attribution errors, coverage gaps, recency bias)

## References

- Gao et al. (2024). Retrieval-Augmented Generation for Large Language Models: A Survey. Semantic Scholar.
- arxiv:2506.00054 (2025). Comprehensive Survey of Architectures, Enhancements, and Robustness Frontiers.
- arxiv:2507.18910 (2025). Systematic Review of Key RAG Systems.
- arxiv:2411.18583 (2024). Automated Literature Review Using NLP Techniques and LLM-Based RAG.
- arxiv:2407.20906 (2024). Automated Review Generation Method Based on Large Language Models.
- EMNLP 2025. Large Language Models for Automated Literature Review.
- arxiv:2505.04847 (2025). Benchmarking LLM Faithfulness in RAG with Evolving Leaderboards.
- arxiv:2503.21157 (2025). Real-Time Evaluation Models for RAG.
- lechmazur/confabulations. Hallucinations Document-Based Benchmark for RAG.
