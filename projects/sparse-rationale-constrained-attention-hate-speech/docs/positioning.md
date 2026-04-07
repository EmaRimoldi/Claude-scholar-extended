# Contribution Positioning

**Date:** 2026-04-07 | **Step:** 27

---

## One-Sentence Contribution

We show that replacing softmax with sparsemax in BERT's final-layer CLS attention — supervised via MSE loss against HateXplain rationale masks — achieves +111% relative ERASER comprehensiveness over the state-of-the-art SRA method (Eilertsen et al., AAAI 2026), with zero classification accuracy cost, by structurally forcing non-rationale tokens to exact-zero attention weight rather than penalizing them via KL divergence.

---

## What We Are vs. What We Are Not

| We ARE | We ARE NOT |
|--------|------------|
| A new attention projection choice (sparsemax) for rationale-supervised BERT | A new dataset or annotation method |
| A structural faithfulness argument (range-of-operator) | A new ERASER benchmark |
| An empirical demonstration of operator-class effects on faithfulness | A general interpretability framework |
| A specific improvement over SRA (+111% comprehensiveness) | A replacement for attention-based XAI in general |

---

## Positioning vs. Direct Competitors

### vs. Eilertsen et al. (SRA, AAAI 2026) — arXiv 2511.07065
**Their claim:** "SRA achieves 2.4× better explainability vs baselines via softmax+KL alignment."  
**Our claim:** Sparsemax+MSE achieves +111% comprehensiveness over SRA itself.  
**Key differentiator:** Structural (range-of-operator) vs. regularization (penalty). Sparsemax can produce *exactly* zero; softmax cannot. This is a mathematical fact, not a design choice.  
**Relationship:** We build on and extend SRA. We replicate their baseline (C2) and surpass it. We are the natural next step.

### vs. Malaviya et al. (Constrained Sparsemax, ACL 2018)
**Their constraint:** Coverage budget (fertility scalar per source token).  
**Our constraint:** Binary human rationale mask from HateXplain.  
**Task:** NMT (generation) vs. classification. **Evaluation:** BLEU vs. ERASER faithfulness.  
**No overlap:** Different task, different constraint semantics, different evaluation.

### vs. Jain & Wallace (2019) / Wiegreffe & Pinter (2019)
**Their contribution:** Theoretical and empirical analysis of attention faithfulness.  
**Our contribution:** We apply their adversarial swap test and confirm sparsemax supervision yields more causally load-bearing attention than soft KL alignment.  
**Relationship:** We cite and extend their test to a new comparison (sparsemax vs. softmax supervision).

---

## Contribution Hierarchy

1. **Primary:** Structural operator argument + +111% comprehensiveness empirical demonstration (C-MAIN)
2. **Secondary:** Adversarial faithfulness test showing sparsemax > softmax even without supervision (C-OPERATOR)
3. **Supporting:** Zero accuracy cost under rationale supervision (C-NOCOST)
4. **Subsidiary:** Sufficiency improves alongside comprehensiveness (C-EQUIV-SUFF)

---

## Venue Fit: NeurIPS 2026

**Arguments for NeurIPS:**
- Structural operator argument is a theoretically grounded claim (not just empirical tuning)
- Effect size d=8.36 with mechanistic explanation is publishable as a clean finding
- ERASER is a well-accepted NLP benchmark; hate speech is a socially motivated application
- NeurIPS 2026 accepts ML theory + application papers

**Risks:**
- Single dataset (HateXplain only) — mitigated by Proposition 1 (theoretical generality)
- BERT-base only — acknowledged limitation
- n=5 seeds — standard for supervised BERT experiments on HateXplain

**Fallback:** ACL/EMNLP 2026 if NeurIPS reviewers require second dataset. Adding HatEval 2019 (1 GPU-day) would make the paper NeurIPS-strong.

---

## Abstract Draft (50 words)

We replace softmax with sparsemax in BERT's final-layer CLS attention, supervised by human rationale masks via MSE loss, for hate speech classification. Sparsemax's structural property — exact-zero attention on non-rationale tokens — yields +111% ERASER comprehensiveness over the SRA-softmax baseline (0.338 vs 0.160 AOPC; d=8.36; p=0.031) with no accuracy cost, establishing operator choice as a principled faithfulness design decision.
