# Paper Blueprint — Sparse Rationale-Constrained Attention for Hate Speech Detection

**Date:** 2026-04-07 | **Step:** 28 (story)  
**Target venue:** NeurIPS 2026 (9 pages + refs)

---

## Narrative Arc

**The Problem:** Hate speech models are black boxes. SRA (Eilertsen et al., AAAI 2026) aligns BERT's softmax attention to rationale masks via KL loss — but softmax's range excludes exact zero, so non-rationale tokens always retain some probability mass. The KL penalty can shrink but never *eliminate* this leakage.

**The Insight:** Sparsemax is a projection onto the closed simplex — its range *includes* the boundary. Non-rationale tokens can receive exactly zero weight. This is not a hyperparameter choice; it is a consequence of the operator's mathematical range. Exact zeros mean that deletion of those tokens *cannot* change the attention-weighted representation — which is precisely the condition ERASER comprehensiveness tests.

**The Result:** +111% comprehensiveness AOPC over SRA, with zero accuracy cost. The effect is mechanistically determined (visible in every seed, d=8.36). Even without supervision, unsupervised sparsemax (C3) is more causally faithful than supervised softmax (C2).

**The Takeaway:** When your targets are structurally sparse (HateXplain rationale density ~23%), the choice of attention operator is a faithfulness design decision — not just a regularization knob.

---

## Section Structure

### 1. Introduction (1 page)
- Hook: hate speech models deployed at scale, opacity creates accountability gaps
- Motivate rationale supervision as interpretability path
- Introduce SRA as state-of-the-art; identify the softmax structural limitation
- State contribution: sparsemax + MSE → structural faithfulness
- Preview key number: +111% comprehensiveness, zero accuracy cost
- Roadmap sentence

### 2. Background (0.75 page)
- HateXplain dataset and rationale annotation protocol
- Sparsemax vs. softmax: range-of-operator difference (Martins & Astudillo 2016)
- ERASER faithfulness metrics (DeYoung et al. 2020): comprehensiveness, sufficiency
- Adversarial swap test (Jain & Wallace 2019)
- SRA framework (Eilertsen et al. 2025)

### 3. Method (1.5 pages)
- 3.1: Architecture — BERT-base, sparsemax injection into final-layer CLS attention
- 3.2: Loss function — JointLoss = CrossEntropy + α·MSEAlignmentLoss
- 3.3: Proposition 1 (proof sketch): *For any rational mask r with support S, sparsemax(z)[i]=0 for i∉S whenever the projection solution concentrates on S; removing i then cannot perturb the attention-weighted representation.*
- 3.4: Experimental conditions (Table 1: C1-C5 description)
- 3.5: Baseline (SRA, C2): replication of Eilertsen et al. with KL loss

### 4. Experiments (2 pages)
- 4.1: Setup — HateXplain, BERT-base-uncased, 5 seeds, AdamW, SLURM cluster
- 4.2: Classification results (Table 2: F1 across conditions, equivalence test)
- 4.3: Interpretability results — ERASER (Table 3 + Fig 1A,B), adversarial swap KL (Table 3 + Fig 1C)
- 4.4: Per-seed analysis (Fig 3 scatter — every seed C4>C2)
- 4.5: Figure 2: Accuracy-Interpretability trade-off (no free lunch is not the story — it's a free lunch)
- 4.6: Plausibility: note dataset artifact (no majority-vote rationale), cite Mathew et al. 2021

### 5. Analysis (1 page)
- 5.1: Why does it work? Walk through M1→M2→M3 mechanism
- 5.2: C3>C2 (structural operator vs. supervision): sparsemax without supervision beats SRA — structural property dominates
- 5.3: C2<C1 (SRA reduces causal load): soft alignment may allow model to hide information in hidden states
- 5.4: Head selection (C4 vs C5): inconclusive at n=5; report honestly as exploratory

### 6. Related Work (0.5 page)
- Attention interpretability (Jain & Wallace 2019, Wiegreffe & Pinter 2019, Brunner et al. 2020)
- Sparse attention (Martins & Astudillo 2016, Correia et al. 2019, Malaviya et al. 2018)
- Rationale supervision (SRA, FRESH, ERASER)
- Hate speech interpretability (HateXplain, fairness work)

### 7. Limitations & Future Work (0.25 page)
- Single dataset (HateXplain); HatEval 2019 generalization = future work
- BERT-base only; larger model generalization untested
- Plausibility metric not evaluable due to annotation sparsity
- H4 ratio (1.47×) below the pre-registered 2× threshold — transparent disclosure
- H5 (fairness) not tested

### 8. Conclusion (0.25 page)
- Sparsemax operator choice is a principled faithfulness decision when rationale targets are structurally sparse
- +111% comprehensiveness over SRA, zero accuracy cost
- Unsupervised sparsemax outperforms supervised softmax on causal faithfulness

---

## Figure Plan

| Figure | Content | Claim served |
|--------|---------|--------------|
| Fig 1 | Three-panel: (A) comprehensiveness AOPC bar, (B) sufficiency AOPC bar, (C) adversarial swap KL bar — all 5 conditions | C-MAIN, C-FAITHFUL |
| Fig 2 | Scatter: macro-F1 vs comprehensiveness per condition | C-NOCOST (no trade-off) |
| Fig 3 | Per-seed scatter C2 vs C4 comprehensiveness (all above diagonal) | C-MAIN (deterministic) |
| Table 1 | Condition definitions | Context |
| Table 2 | Classification F1 mean±std, TOST result | C-NOCOST |
| Table 3 | Interpretability: comp, suff, swap-KL for C2/C4/C5 | C-MAIN, C-FAITHFUL |

---

## Confidence Tracker

| Section | Confidence | Blocker |
|---------|------------|---------|
| Introduction | High | None |
| Background | High | None |
| Method | High | Proposition 1 proof sketch needed |
| Experiments | High | None — data complete |
| Analysis | High | C3>C2 finding is the highlight |
| Limitations | High | Must disclose H4 pre-registration miss |
| Related work | Medium | Check for any Dec 2025-Apr 2026 papers missed |
