# Dataset Catalog — Sparse Rationale-Constrained Attention for Hate Speech Detection

**Date:** 2026-04-07
**Source:** research-landscape.md Pass 1 + research-init

---

## Primary Dataset

### HateXplain

| Field | Value |
|-------|-------|
| **Name** | HateXplain |
| **Source** | Mathew et al., AAAI 2021 (arXiv 2012.10289); GitHub: hate-alert/HateXplain |
| **Size** | 20,148 posts; train/val/test: ~15K/2.5K/2.5K |
| **Tasks** | 3-class hate speech classification (hate/offensive/normal), target community labeling, rationale span annotation |
| **License** | CC BY 4.0 |
| **Relevance** | PRIMARY: provides rationale span annotations (avg 5.47 of 23.42 tokens highlighted ≈ 25%) that serve as the supervision signal for sparsemax constraint. Also provides target community labels for H5 fairness analysis. Sources: Gab and Twitter. |
| **Limitations** | Inter-annotator disagreement on rationale spans; ~25K unique vocabulary; majority-vote rationales may miss minority annotator judgments; English only; binary hate/non-hate aggregation loses nuance; target labels are broad categories |
| **Annotation details** | 2–3 annotators per post; majority vote for rationale; disagreement measured by Fleiss' κ per post |

---

## Secondary / Cross-Lingual Dataset

### HateBRXplain

| Field | Value |
|-------|-------|
| **Name** | HateBRXplain |
| **Source** | Vargas et al. (referenced in eilertsen2025aligning) |
| **Size** | ~5K posts (Portuguese) |
| **Tasks** | 3-class hate speech classification + rationale annotations (Portuguese) |
| **License** | See original paper |
| **Relevance** | Used by SRA (`eilertsen2025aligning`) as cross-lingual evaluation; enables W5a zero-shot transfer experiment |
| **Limitations** | Portuguese only; smaller than HateXplain; rationale annotation style may differ |

---

## Baseline / Cross-Domain Dataset

### Davidson et al. (2017) — Hate Speech and Offensive Language

| Field | Value |
|-------|-------|
| **Name** | Crowdflower Hate Speech Dataset |
| **Source** | Davidson et al., ICWSM 2017; GitHub: t-davidson/hate-speech-and-offensive-language |
| **Size** | 24,783 tweets |
| **Tasks** | 3-class classification (hate speech / offensive language / neither) |
| **License** | GNU GPL v3 |
| **Relevance** | Standard cross-domain baseline; no rationale annotations (cannot be used for sparsemax supervision, only for cross-domain generalization eval W5b) |
| **Limitations** | No rationale annotations; crowdsourced; known bias toward African American English being over-flagged |

---

## Evaluation Framework

### ERASER Benchmark

| Field | Value |
|-------|-------|
| **Name** | ERASER (Evaluating Rationales And Simple English Reasoning) |
| **Source** | DeYoung et al., ACL 2020 (arXiv 1911.03429); GitHub: jayded/eraserbenchmark |
| **Size** | 8 datasets; metrics only (no standalone download needed for HateXplain eval) |
| **Tasks** | Comprehensiveness (AOPC), sufficiency (AOPC), plausibility (F1 vs. human rationales) |
| **License** | Apache 2.0 |
| **Relevance** | PRIMARY evaluation framework for faithfulness. Comprehensiveness and sufficiency metrics from ERASER are the main dependent variables for H1. |
| **Limitations** | Comprehensiveness/sufficiency conflate out-of-distribution effects with faithfulness (Hsia et al. 2023); no consensus metric for exact-zero vs. near-zero attention |

---

## Pre-trained Models

### BERT-base-uncased

| Field | Value |
|-------|-------|
| **Name** | BERT-base-uncased |
| **Source** | Devlin et al., NAACL 2019; HuggingFace: `bert-base-uncased` |
| **Size** | 110M parameters, 12 layers, 12 heads per layer, hidden dim 768 |
| **Tasks** | Pre-trained language model; fine-tuned for classification |
| **License** | Apache 2.0 |
| **Relevance** | PRIMARY model backbone; sparsemax replaces softmax in final-layer CLS attention heads. Choice follows `mathew2021hatexplain` and `eilertsen2025aligning` for comparability. |
| **Limitations** | 512 token max length (HateXplain posts are short ~23 tokens, well within limit); uncased may lose some signal |

---

## Dataset Selection Rationale

The experiment design uses:
1. **HateXplain** (primary): only dataset with rationale span annotations compatible with sparsemax supervision
2. **Davidson 2017** (cross-domain W5b): no rationale annotations; used for unsupervised cross-domain generalization test
3. **HateBRXplain** (cross-lingual W5a): tests whether rationale-supervised sparsemax transfers

All other hate speech datasets (OLID, Gab Hate Corpus, etc.) lack rationale annotations and are not candidates for the primary experiment.
