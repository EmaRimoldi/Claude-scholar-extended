# Literature Review: Sparse Rationale-Constrained Attention for Faithful Hate Speech Explanations

## 1. Hate Speech Detection with Rationale Annotations

### HateXplain (Mathew et al., 2021, AAAI)
- **Dataset**: 20,148 social media posts annotated for hate speech / offensive / normal classification
- **Key innovation**: Token-level rationale annotations from 3 annotators per post — the first hate speech dataset with ground-truth explanations
- **Baselines**: BERT, BiRNN with attention supervision, LIME, SHAP post-hoc explanations
- **Key results**: Attention supervision improves plausibility (agreement with human rationales) but can degrade classification performance; vanilla BERT achieves ~69% macro-F1 on 3-class task
- **Gap identified**: Attention supervision applied uniformly across all heads, no mechanism for sparse or selective supervision

### Latent Hatred (ElSherief et al., 2021, ACL)
- Implicit hate speech with free-text explanations; demonstrates that explicit rationales are insufficient for implicit hate

### ToxiGen (Hartvigsen et al., 2022, ACL)
- Machine-generated hate speech dataset; 274K examples but no token-level rationale annotations

## 2. Sparsemax and Sparse Attention

### Sparsemax (Martins & Astudillo, 2016, ICML)
- **Core idea**: Replace softmax with sparsemax — produces sparse probability distributions by projecting onto the simplex
- **Properties**: Exact zeros in output (truly sparse attention), differentiable almost everywhere, same time complexity as softmax
- **Original evaluation**: Text classification and language modeling; improves interpretability of attention weights
- **Gap**: Never applied to rationale supervision or hate speech domain

### Entmax (Peters et al., 2019, ACL)
- Generalization of sparsemax (α-entmax family); α=1.5 is good compromise between softmax (α=1) and sparsemax (α=2)
- Learnable α per head; applied to machine translation
- Relevant but adds complexity; sparsemax is simpler and sufficient for our purposes

### Fusedmax and Regularized Attention (Niculae & Blondel, 2017, NIPS)
- Structured sparse attention via regularization; enables contiguous spans
- Potentially relevant for rationale extraction but higher computational cost

## 3. Attention as Explanation: Faithfulness Debate

### Attention is Not Explanation (Jain & Wallace, 2019, NAACL)
- **Key finding**: Attention weights often don't correlate with feature importance; adversarial attention distributions can yield same predictions
- **Implication**: Standard softmax attention is unreliable as explanation → motivates our work on making attention more faithful

### Attention is Not Not Explanation (Wiegreffe & Pinter, 2019, EMNLP)
- Counter-argument: Attention can be a useful explanation signal if properly calibrated
- The debate remains open → opportunity for sparsemax to bridge the gap

### Quantifying Attention Flow (Abnar & Zuidema, 2020, ACL)
- Attention rollout and attention flow methods for tracking information across layers
- Useful for analyzing which heads are semantically meaningful

## 4. Attention Supervision and Selective Head Training

### Supervising Attention for NER (Cui & Zhang, 2019, EMNLP)
- Supervise attention weights with alignment labels for named entity recognition
- Shows attention supervision can improve both performance and interpretability
- Applied to ALL heads → our approach of SELECTIVE supervision is novel

### Importance of Individual Heads (Voita et al., 2019, ACL)
- Not all attention heads are equal; many can be pruned without performance loss
- Identifies "positional", "syntactic", and "rare word" head roles
- **Key insight for our work**: Only semantically relevant heads should be supervised

### Are Sixteen Heads Really Better Than One? (Michel et al., 2019, NeurIPS)
- Most heads can be removed at test time with minimal performance degradation
- Supports selective supervision — supervising all heads wastes capacity on non-semantic heads

### What Does BERT Look At? (Clark et al., 2019, BlackboxNLP)
- Analyzes BERT attention patterns: some heads attend to [SEP], some to syntactic structure
- **Directly relevant**: Can identify which heads capture semantic content relevant to hate speech rationales

## 5. Faithfulness Metrics for Explanations

### Integrated Gradients (Sundararajan et al., 2017, ICML)
- Axiom-based attribution method: completeness, sensitivity, implementation invariance
- Gold standard for measuring faithfulness of any explanation method
- We use IG as ground-truth reference to measure attention faithfulness

### Sufficiency and Comprehensiveness (DeYoung et al., 2020, ACL)
- **Sufficiency**: Model confidence using only rationale tokens
- **Comprehensiveness**: Drop in confidence when rationale tokens are removed
- Standard metrics for rationale quality in NLP; we adopt both

### ERASER Benchmark (DeYoung et al., 2020, ACL)
- Standardized benchmark for evaluating rationale quality
- Metrics: token-level F1, IOU, sufficiency, comprehensiveness
- HateXplain is compatible with ERASER-style evaluation

## 6. Gap Analysis

| Gap | Description | Our Contribution |
|-----|-------------|-----------------|
| **G1: Sparsemax × Rationale Supervision** | Sparsemax has never been combined with human rationale supervision | First to use sparsemax attention targets for rationale-supervised training |
| **G2: Selective Head Supervision** | Prior work supervises ALL attention heads uniformly | Identify and supervise only semantically important heads via IG-based head importance scoring |
| **G3: Faithfulness in Hate Speech** | HateXplain baselines only measure plausibility, not faithfulness | Comprehensive faithfulness evaluation (sufficiency, comprehensiveness, IG correlation) |
| **G4: Attention Sparsity × Accuracy Trade-off** | No systematic study of how attention sparsity affects hate speech classification accuracy | Controlled ablation across sparsity levels and supervision strategies |

## Key References

1. Mathew, B., et al. (2021). HateXplain: A Benchmark Dataset for Explainable Hate Speech Detection. AAAI.
2. Martins, A. & Astudillo, R. (2016). From Softmax to Sparsemax: A Sparse Model of Attention and Multi-Label Classification. ICML.
3. Jain, S. & Wallace, B. (2019). Attention is not Explanation. NAACL.
4. Wiegreffe, S. & Pinter, Y. (2019). Attention is not not Explanation. EMNLP.
5. Sundararajan, M., et al. (2017). Axiomatic Attribution for Deep Networks. ICML.
6. DeYoung, J., et al. (2020). ERASER: A Benchmark to Evaluate Rationalized NLP Models. ACL.
7. Voita, E., et al. (2019). Analyzing Multi-Head Self-Attention: Specialized Heads Do the Heavy Lifting. ACL.
8. Michel, P., et al. (2019). Are Sixteen Heads Really Better Than One? NeurIPS.
9. Clark, K., et al. (2019). What Does BERT Look At? An Analysis of BERT's Attention. BlackboxNLP.
10. Peters, B., et al. (2019). Sparse Sequence-to-Sequence Models. ACL.
