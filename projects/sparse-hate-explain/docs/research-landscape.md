# Research Landscape — Pass 1 Broad Territorial Mapping

**Date:** 2026-03-30
**Step:** 1 / 38
**Papers retrieved:** 87
**Clusters identified:** 5

---

## Cluster A: Hate Speech Detection (28 papers)

Core papers:
- **Mathew et al. (2021)** — HateXplain: A Benchmark Dataset for Explainable Hate Speech Detection. AAAI. *Primary dataset. Provides token-level human rationales from three annotators.*
- **Davidson et al. (2017)** — Automated Hate Speech Detection. ICWSM.
- **Founta et al. (2018)** — Large Scale Crowdsourcing and Characterization of Twitter Abusive Behavior. ICWSM.
- **Zampieri et al. (2019)** — Predicting the Type and Target of Offensive Posts in Social Media. NAACL (OffComEval).
- **Vidgen & Derczynski (2020)** — Directions in Abusive Language Training Data. PLoS ONE. *Taxonomy survey.*
- **Kennedy et al. (2022)** — Conceptualizating Implicit Hate Speech. ACL.

**Gap:** Most detection work ignores *why* a classification was made. Explainability is an afterthought.

---

## Cluster B: Attention-Based Explainability (22 papers)

Core papers:
- **Jain & Wallace (2019)** — Attention is not Explanation. NAACL. *Adversarial swap shows attention can be exchanged without changing predictions.*
- **Wiegreffe & Pinter (2019)** — Attention is not not Explanation. EMNLP. *Counter-argument: under certain conditions, attention is explanatory.*
- **Clark et al. (2019)** — What Does BERT Look At? ACL BlackboxNLP. *Head specialization analysis; some heads attend to coreference, syntax, etc.*
- **Voita et al. (2019)** — Analyzing Multi-Head Self-Attention. ACL. *Head pruning; confirms functional specialization.*
- **Michel et al. (2019)** — Are Sixteen Heads Really Better Than One? NeurIPS. *Importance scoring by gradient magnitude; pruning without performance loss.*
- **Tenney et al. (2019)** — BERT Rediscovers the Classical NLP Pipeline. ACL. *Layer-wise probing.*
- **Sundararajan et al. (2017)** — Axiomatic Attribution (Integrated Gradients). ICML.

**Gap:** Head specialization well-studied in general BERT, but not in the context of hate speech, where *semantic* heads may attend to slurs/targets differently.

---

## Cluster C: Rationale Supervision (15 papers)

Core papers:
- **DeYoung et al. (2020)** — ERASER Benchmark. ACL. *Defines comprehensiveness and sufficiency as faithfulness metrics.*
- **Lei et al. (2016)** — Rationalizing Neural Predictions. EMNLP. *Rationale extraction as a latent variable.*
- **Bastings et al. (2019)** — Interpretable Neural Predictions with Differentiable Binary Variables. ACL.
- **Jain et al. (2020)** — Learning to Faithfully Rationalize by Construction. ACL. *FRESH framework.*
- **Chan et al. (2022)** — Unirex: A Unified Learning Framework for Language Model Rationale Extraction. EMNLP.

**Gap:** Rationale supervision in BERT-based hate speech is underexplored; most work uses sequence-level labels.

---

## Cluster D: Sparse Attention (14 papers)

Core papers:
- **Martins & Astudillo (2016)** — From Softmax to Sparsemax. ICML. *Defines sparsemax as Euclidean projection onto simplex; sparse and differentiable.*
- **Correia et al. (2019)** — Adaptively Sparse Transformers. EMNLP. *α-entmax generalizes sparsemax; adaptive sparsity per head.*
- **Peters et al. (2019)** — Sparse Sequence-to-Sequence Models. ACL. *Sparsemax in seq2seq.*
- **Child et al. (2019)** — Generating Long Sequences with Sparse Transformers. arXiv. *Structural sparsity (local + strided patterns) for long-range dependencies.*
- **Shi et al. (2021)** — Sparsebert: Rethinking the Importance Analysis in Self-attention. ICML. *Sparse attention patterns in BERT for efficiency.*

**Gap:** Sparse attention studied primarily for *efficiency* (long sequences) or *modeling* (seq2seq), not for *explainability* via human rationale alignment.

---

## Cluster E: Supervised Rationale Attention — HIGH-THREAT ZONE (8 papers)

**NOTE: This cluster emerged during Pass 1 keyword sweep on "supervised attention rationale BERT". Requires immediate deep-dive in Pass 2.**

- **SRA (arXiv:2511.07065, Nov 2025)** — Supervised Rational Attention for Text Classification. *Uses sparsemax to supervise BERT CLS-token attention against human rationales. **This is the closest prior work and represents a direct overlap with the proposed contribution method.** Must be assessed in Pass 6 adversarial search.*
- **Attention supervision prior work (2020–2022):** Several papers supervise attention weights against human labels in NLI, sentiment, and fact-checking domains.

**Gap / Threat:** SRA does essentially what we propose. The question is whether our *selective-head* component + *theoretical framing* constitute sufficient novelty. **Flag for N1 gate.**

---

## Cluster Analysis Summary

| Cluster | Papers | Maturity | Gap for Our Work |
|---------|--------|----------|-----------------|
| A: Hate Speech Detection | 28 | High | Explainability gap |
| B: Attention Explainability | 22 | High | Head specialization for hate speech |
| C: Rationale Supervision | 15 | Medium | BERT + hate speech + sparsemax |
| D: Sparse Attention | 14 | High | Explainability framing (not efficiency) |
| E: Supervised Rationale Attention | 8 | Emerging | **SRA (arXiv 2511.07065) is direct overlap** |

---

## Citation Ledger Status

Papers added to citation_ledger.json: 14
Critical papers found: 8/8 ✓
High-threat papers found: 1/2 (SRA found; SMRA not yet found — may be too recent for Pass 1)

---

## Step 1 Gate Status

- [x] ≥ 50 papers retrieved (87)
- [x] All 8 critical papers present
- [x] Cluster analysis complete
- [x] Citation Ledger initialized
- [⚠] HIGH-THREAT paper SRA found — requires immediate Pass 2 claim-level deep-dive
