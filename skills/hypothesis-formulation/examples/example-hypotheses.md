# Example: Hypothesis Formulation

## Context

**Research question**: Can contrastive pre-training improve cross-subject EEG decoding?
**Input Mode**: Standalone (no research-proposal.md found)
**Domain**: Brain-Computer Interfaces / EEG decoding
**Target venue**: NeurIPS

---

## H1 (Primary): Contrastive pre-training improves cross-subject transfer

- **Prediction**: Contrastive pre-training on multi-subject EEG data yields higher decoding accuracy on held-out subjects compared to training from scratch
- **Metric**: Balanced accuracy on held-out subjects (leave-one-subject-out)
- **Baseline**: Supervised training from scratch (no pre-training)
- **Expected effect**: +5% balanced accuracy (based on similar gains in NLP/vision transfer learning: Devlin et al. 2019, Chen et al. 2020)
- **Success threshold**: +3% with p < 0.05 (paired t-test across 9 subjects)
- **Failure threshold**: <+1% or p > 0.10
- **Ambiguous zone**: +1-3% or 0.05 < p < 0.10 -- collect more seeds before concluding

## H2 (Secondary): Benefits scale with pre-training data diversity

- **Prediction**: More subjects in the pre-training pool leads to larger transfer gains
- **Metric**: Slope of balanced accuracy vs. number of pre-training subjects
- **Baseline**: Single-subject pre-training (no diversity)
- **Expected effect**: Positive linear relationship
- **Success threshold**: Positive slope with R^2 > 0.5 across at least 4 data points
- **Failure threshold**: Flat or negative slope

## H3 (Secondary): Learned representations capture task-relevant structure

- **Prediction**: Contrastive representations cluster by task condition, not by subject identity
- **Metric**: Silhouette score of t-SNE embeddings (task clusters vs. subject clusters)
- **Baseline**: Raw EEG features (no learned representation)
- **Success threshold**: Task silhouette > subject silhouette
- **Failure threshold**: Subject silhouette dominates (representations encode subject, not task)

## Null Hypothesis (H0)

Contrastive pre-training provides no statistically significant improvement over supervised training from scratch for cross-subject EEG decoding (balanced accuracy difference not significantly different from zero, paired t-test, p >= 0.05).

## Risk Assessment

### If H1 Fails

- **Fallback H1'**: Try different contrastive objectives (SimCLR vs. BYOL vs. VICReg)
  - Cost: ~3x original experiment (3 objectives)
  - Rationale: The loss function choice is critical for contrastive learning
- **Fallback H1''**: Restrict to within-session transfer (easier setting)
  - Cost: ~1x original experiment
  - Rationale: Cross-subject may be too hard; within-session validates the method
- **Abandon criteria**: If 3+ contrastive objectives fail on 2+ datasets, the approach is unlikely to work for EEG

### If H2 Fails

- Suggests the benefit is not from data diversity but from the pre-training task itself
- Pivot to investigating which pre-training tasks (not data quantity) matter most

### Resource Estimate

| Hypothesis | Minimum experiments | Estimated GPU-hours |
|-----------|-------------------|-------------------|
| H1 | 5 seeds x 9 subjects x 2 methods | ~90h |
| H2 | 4 data points x 5 seeds x 9 subjects | ~180h |
| H3 | Reuses H1 checkpoints | ~2h (inference only) |
| **Total** | | **~272h** |
