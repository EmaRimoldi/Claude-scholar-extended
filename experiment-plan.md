# Experiment Plan: RAG for Scientific Literature Synthesis

## Overview

Evaluate RAG-based systems for scientific literature synthesis against expert-written reviews, measuring citation accuracy, factual consistency, coverage, and error patterns.

## Experiment Matrix

### Conditions

| Condition ID | System | Retrieval | Description |
|---|---|---|---|
| C1-RAG-DENSE | RAG + Dense Retrieval | Contriever/E5 | Dense passage retrieval + LLM generation |
| C2-RAG-SPARSE | RAG + Sparse Retrieval | BM25 | Lexical retrieval + LLM generation |
| C3-RAG-HYBRID | RAG + Hybrid Retrieval | BM25 + Dense rerank | Combined retrieval + LLM generation |
| C4-NO-RETRIEVAL | LLM Only | None | Generation from parametric knowledge only |
| C5-HUMAN | Expert Reviews | N/A | Published survey papers (ground truth) |

### Generator Models

| Model | Parameters | Notes |
|---|---|---|
| GPT-4o | API | Commercial baseline |
| LLaMA-3.1-8B | 8B | Open-source, instruction-tuned |
| Mistral-7B-v0.3 | 7B | Open-source alternative |

### Ablations

| Ablation | Modified Variable | Purpose |
|---|---|---|
| A1: Chunk size | 256 / 512 / 1024 tokens | Effect of retrieval granularity |
| A2: Top-k | 3 / 5 / 10 / 20 retrieved passages | Effect of retrieval breadth |
| A3: Prompt type | zero-shot / few-shot / CoT | Effect of generation strategy |
| A4: Corpus recency | Full corpus / last-3-years only | Detect recency bias |

## Dataset / Benchmark Construction

### Benchmark Topics
- Select 15 sub-topics from ML/NLP with existing published surveys (2022–2025)
- Source surveys from ACL Anthology, NeurIPS proceedings, arXiv
- Each topic: 1 expert review + corpus of ~50–200 cited papers

### Corpus
- **Source**: Semantic Scholar API (paper metadata + abstracts) + available full texts
- **Size per topic**: 200–500 candidate papers (retrieval pool)
- **Ground truth**: Expert survey citations + manual annotation subset

### Annotation
- 2 annotators per topic for error classification
- Inter-annotator agreement target: κ > 0.6
- Annotate: citation accuracy, attribution correctness, claim support

## Metrics

### Primary Metrics
| Metric | Formula | Target |
|---|---|---|
| Citation Precision | correct_citations / total_citations | H1 |
| Citation Recall | cited_relevant / total_relevant | H1 |
| Faithfulness Score | supported_claims / total_claims | H2 |
| Hallucination Rate | unsupported_claims / total_claims | H2 |
| Key Paper Recall (KPR) | expert_papers_found / expert_papers_total | H3 |

### Secondary Metrics
| Metric | Purpose |
|---|---|
| ROUGE-1/2/L | Surface overlap with expert review |
| BERTScore | Semantic similarity |
| Recency Correlation | Spearman ρ between paper year and inclusion |
| Citation Count Correlation | Spearman ρ between citation count and inclusion |

## Baselines

| Baseline | Expected Performance | Source |
|---|---|---|
| No-retrieval LLM | ~40% faithfulness, ~20% citation accuracy | Prior work estimates |
| BM25 + GPT-3.5 | ROUGE-1 ~0.36 | arxiv:2411.18583 |
| Expert reviews | >95% citation accuracy, >90% coverage | Ground truth |

## Resource Estimation

| Resource | Estimate |
|---|---|
| API calls (GPT-4o) | ~15 topics × 3 runs × ~5K tokens = ~225K tokens per condition |
| Local GPU (LLaMA/Mistral) | 1× A100 40GB, ~2h per topic per model |
| Total GPU hours | ~60–90h for local models |
| Annotation | ~40h human time (2 annotators × 15 topics × ~1.3h each) |
| Corpus construction | ~10h (API calls + filtering) |

## Phase Gates

### Gate 1: Data Ready
- [ ] 15 benchmark topics selected with expert surveys identified
- [ ] Corpus constructed with ≥200 papers per topic
- [ ] Annotation guidelines written and pilot-tested

### Gate 2: Baseline Complete
- [ ] No-retrieval baseline (C4) produces outputs for all topics
- [ ] BM25 baseline (C2) produces outputs for all topics
- [ ] Metrics pipeline computes all primary metrics correctly

### Gate 3: Full Sweep Done
- [ ] All conditions × all topics × 3 seeds completed
- [ ] Error annotation complete for ≥5 topics
- [ ] Statistical tests show sufficient power (≥0.8)

## Success Criteria

| Hypothesis | Pass Condition |
|---|---|
| H1 | RAG citation accuracy < 80%, significant difference from human (p < 0.05) |
| H2 | RAG hallucination < no-retrieval (p < 0.05, d > 0.5), RAG still >5% |
| H3 | KPR < 70%, significant recency/popularity bias |
| H4 | 4-category error taxonomy with κ > 0.6 |

## Seeds and Repetitions

- 3 random seeds per condition: {42, 123, 456}
- Temperature: 0.3 for generation (low variance, reproducible)
- Retrieval: deterministic (no sampling)

## Max Iterations

- Maximum 3 iterations of the experiment loop
- Pivot if no hypothesis shows significance after 2 iterations
