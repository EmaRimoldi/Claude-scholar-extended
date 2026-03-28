# Paper Blueprint: RAG for Scientific Literature Synthesis

## Title
"How Well Can RAG Systems Write Literature Reviews? A Benchmark for Citation-Grounded Scientific Synthesis"

## Narrative Arc

**Opening tension**: RAG promises grounded generation, but literature synthesis demands accurate citations, comprehensive coverage, and faithful attribution — can RAG deliver?

**Key finding**: RAG significantly reduces hallucinations vs. pure generation, but citation accuracy and coverage remain substantially below expert levels, with systematic biases toward recent and highly-cited papers.

**Resolution**: Our benchmark and error taxonomy provide the first standardized framework for measuring and improving RAG-based literature synthesis.

## Section Outline

### 1. Introduction (~1.5 pages)
- Motivate: growing use of LLMs for scientific writing
- Gap: no benchmark for citation-grounded literature synthesis
- Contributions: benchmark + evaluation framework + error taxonomy
- Preview results

### 2. Related Work (~1.5 pages)
- 2.1 RAG systems and architectures
- 2.2 Hallucination detection and faithfulness
- 2.3 Automated literature review generation
- 2.4 Evaluation benchmarks for RAG

### 3. LitSynthBench: Benchmark Construction (~2 pages)
- 3.1 Topic selection methodology
- 3.2 Corpus construction via Semantic Scholar
- 3.3 Expert review collection
- 3.4 Annotation protocol
- 3.5 Dataset statistics

### 4. Experimental Setup (~1.5 pages)
- 4.1 RAG conditions (dense, sparse, hybrid)
- 4.2 Generator models
- 4.3 Evaluation metrics
- 4.4 Baselines

### 5. Results (~3 pages)
- 5.1 Citation accuracy (H1) — Fig 1: bar chart
- 5.2 Factual consistency (H2) — Fig 2: scatter plot
- 5.3 Coverage analysis (H3) — Fig 3: heatmap
- 5.4 Error taxonomy (H4) — Fig 4: distribution
- 5.5 Ablation studies — Fig 5: curves

### 6. Discussion (~1 page)
- When RAG works and when it fails
- Implications for AI-assisted scientific writing
- Limitations

### 7. Conclusion (~0.5 page)

## Figure Plan

| Figure | Type | Data | Section |
|---|---|---|---|
| Fig 1 | Grouped bar chart | Citation P/R/F1 by condition | 5.1 |
| Fig 2 | Scatter + regression | Faithfulness vs hallucination rate | 5.2 |
| Fig 3 | Heatmap | KPR across topics × conditions | 5.3 |
| Fig 4 | Stacked bar / pie | Error category distribution | 5.4 |
| Fig 5 | Line plots | Ablation metrics vs top-k / chunk size | 5.5 |
| Table 1 | Summary table | Main results all conditions | 5 |
| Table 2 | Comparison | Our work vs prior benchmarks | 2 |

## Target Venue
- **Primary**: EMNLP 2026 (NLP + evaluation focus)
- **Alternative**: ACL 2026, NeurIPS 2026 Datasets & Benchmarks
