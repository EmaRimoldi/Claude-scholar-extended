# Research Hypotheses: RAG for Scientific Literature Synthesis

## Research Question

Can RAG-based systems produce accurate, citation-grounded research summaries comparable to expert-written reviews? Where do they fail?

## H1: Citation Accuracy

**Hypothesis**: RAG-based literature synthesis systems achieve less than 80% citation accuracy (correct paper cited for the correct claim) compared to >95% in expert-written reviews.

**Success criteria**: Statistically significant difference (p < 0.05) in citation accuracy between RAG-generated and human-written reviews, with RAG scoring below 80% on citation precision.

**Failure criteria**: RAG citation accuracy exceeds 85%, or the difference is not statistically significant.

**Measurement**: Citation precision (fraction of citations that correctly support the claim they are attached to), citation recall (fraction of relevant papers that are cited).

## H2: Factual Consistency

**Hypothesis**: RAG-based literature synthesis reduces factual hallucinations by at least 50% compared to generation without retrieval, but still produces measurable hallucinations (>5% of claims unsupported by sources).

**Success criteria**: (a) RAG hallucinates significantly less than no-retrieval baseline (p < 0.05, effect size d > 0.5); (b) RAG still produces >5% unsupported claims.

**Failure criteria**: RAG produces <5% unsupported claims (near-perfect), or RAG does not significantly outperform no-retrieval baseline.

**Measurement**: Faithfulness score (fraction of claims grounded in retrieved documents), hallucination rate per paragraph.

## H3: Coverage Completeness

**Hypothesis**: RAG-based reviews cover fewer than 70% of the key papers cited in expert-written reviews on the same topic, with systematic biases toward highly-cited and recent papers.

**Success criteria**: RAG recall of expert-cited papers is below 70%, and there is a significant correlation between citation count/recency and inclusion probability.

**Failure criteria**: RAG recall exceeds 80%, or no significant recency/popularity bias.

**Measurement**: Key Paper Recall (KPR), correlation analysis between inclusion and paper metadata (citation count, year, venue).

## H4: Error Taxonomy

**Hypothesis**: RAG-based literature synthesis errors cluster into four distinct categories: (a) citation hallucination (citing non-existent papers), (b) attribution error (correct paper, wrong claim), (c) omission (missing key papers), (d) recency bias (over-representing recent work).

**Success criteria**: At least 80% of errors can be classified into these four categories with inter-annotator agreement κ > 0.6.

**Failure criteria**: Error distribution does not cluster meaningfully, or a significant category is missing.

**Measurement**: Manual error annotation by 2+ annotators, Cohen's κ for agreement, category distribution analysis.

## Experimental Approach Summary

| Hypothesis | Independent Variable | Dependent Variable | Method |
|---|---|---|---|
| H1 | System type (RAG vs human) | Citation accuracy | Paired comparison on same topics |
| H2 | Retrieval (RAG vs no-retrieval) | Hallucination rate | Controlled generation experiment |
| H3 | System type (RAG vs human) | Key paper recall | Coverage analysis |
| H4 | Error instances | Error category | Annotation study |

## Domain Scope

- **Target domain**: ML/NLP literature (2020–2025)
- **Benchmark topics**: 10–20 specific sub-topics with existing expert-written survey papers
- **Comparison reviews**: Published survey/review papers from top venues (ACL, EMNLP, NeurIPS, ICML)
