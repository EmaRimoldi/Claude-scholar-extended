# Research Hypotheses: Sparse Rationale-Constrained Attention for Hate Speech Explanations

## Research Question

Can sparse rationale-constrained attention (sparsemax) improve the faithfulness of hate speech explanations in BERT without degrading classification accuracy, and which attention heads should be supervised?

## Hypothesis H1: Sparsemax Attention Supervision Improves Faithfulness

**Statement**: Training BERT with sparsemax-transformed rationale targets for attention supervision produces more faithful explanations (higher correlation with Integrated Gradients attributions) than softmax attention supervision, as measured on the HateXplain test set.

**Rationale**: Sparsemax produces exact zeros, concentrating attention mass on rationale-relevant tokens and eliminating diffuse probability mass on irrelevant tokens. This makes the supervised attention distribution closer to a binary rationale mask, aligning attention with actual decision-relevant features.

**Success criterion**: Attention-IG correlation (Spearman ρ) ≥ 0.05 higher than softmax-supervised baseline (p < 0.05, paired bootstrap test).

**Failure criterion**: ρ difference < 0.02 or not significant → sparsemax offers no faithfulness benefit over softmax supervision.

## Hypothesis H2: Selective Head Supervision Preserves Accuracy

**Statement**: Supervising only the top-K semantically important attention heads (identified via Integrated Gradients head importance scoring on a held-out set) maintains or improves 3-class macro-F1 compared to supervising all 144 heads, while achieving comparable or better faithfulness.

**Rationale**: Not all attention heads encode task-relevant semantics (Voita et al., 2019; Michel et al., 2019). Supervising positional or syntactic heads with semantic rationale targets creates conflicting training signals that degrade performance. Selective supervision avoids this.

**Success criterion**: macro-F1 within 1% of vanilla BERT AND faithfulness (sufficiency, comprehensiveness) at least as good as all-head supervision.

**Failure criterion**: macro-F1 drops >2% compared to vanilla BERT → selective supervision still harmful.

## Hypothesis H3: Combined Sparsemax + Selective Supervision is Pareto-Optimal

**Statement**: The combination of sparsemax attention targets with selective head supervision achieves the best trade-off between classification accuracy and explanation faithfulness (Pareto-dominates all other configurations).

**Rationale**: Sparsemax provides better supervision targets (sharper, sparser), and selective supervision avoids degrading non-semantic heads. Together they should maximize both accuracy and faithfulness.

**Success criterion**: The combined model is on the Pareto frontier of (macro-F1, faithfulness) across all experimental conditions.

**Failure criterion**: Another configuration dominates it on both axes.

## Hypothesis H4: Head Importance is Layer-Dependent

**Statement**: Semantically important heads for hate speech detection cluster in middle layers (layers 5-8) of BERT-base, consistent with prior work showing these layers encode task-relevant semantics.

**Rationale**: Lower layers capture surface patterns, upper layers capture task-specific features. Middle layers have been shown to contain the most transferable semantic representations.

**Success criterion**: >60% of top-K important heads come from layers 4-8.

**Failure criterion**: Important heads are uniformly distributed across layers.

## Variables

### Independent Variables
- **Attention transformation**: {softmax, sparsemax} for supervision targets
- **Supervision scope**: {all heads, top-K heads, top-K per layer}
- **K values**: {12, 24, 36, 48} (out of 144 total heads)
- **Supervision loss weight (λ)**: {0.1, 0.5, 1.0, 2.0}

### Dependent Variables
- **Classification**: macro-F1, per-class F1, accuracy
- **Faithfulness**: attention-IG Spearman ρ, sufficiency, comprehensiveness
- **Plausibility**: token-level F1, AUPRC against human rationales
- **Sparsity**: attention entropy, % zero attention weights

### Controls
- Random seed: {42, 123, 456} (3 seeds per condition)
- Learning rate: 2e-5 (standard for BERT fine-tuning)
- Epochs: 10 with early stopping (patience=3)
- Batch size: 16
- Max sequence length: 128
- Model: bert-base-uncased
- Optimizer: AdamW with linear warmup (10% steps)
