# Example: Novelty Assessment

## Contribution
"Using domain-adversarial training with subject-specific adapters for cross-subject EEG transfer learning"

## Target Venue: NeurIPS

## Input Mode: Pipeline (literature-review.md detected)

## Closest Related Works

| # | Paper | What They Do | What You Add | Overlap | Delta Type |
|---|---|---|---|---|---|
| 1 | Kostas et al. (2021) | Domain adaptation for EEG via MMD | Adversarial training instead of MMD | Medium | Method variant |
| 2 | Zhang et al. (2023) | Subject-specific adapters for EEG | Adapters without adversarial component | Medium | Complementary |
| 3 | Zhao et al. (2022) | Domain-adversarial EEG classification | No subject-specific adapters | Medium | Architecture extension |
| 4 | Li et al. (2024) | Adversarial + adapter for EEG-BCI | Very similar combination, different adapter design | **High** | Direct overlap |
| 5 | Wang et al. (2023) | Self-supervised EEG pre-training | Different paradigm entirely | Low | Complementary |

## Novelty Classification: INCREMENTAL (method combination)

The core idea (adversarial training + subject adapters) has been explored by Li et al. (2024). The proposed delta is the specific adapter architecture design. This falls into the "method combination" pitfall — combining two known techniques (adversarial training + adapters) without a novel theoretical insight or surprising empirical finding.

## Venue Calibration: NeurIPS

For NeurIPS, method combination without a novel theoretical insight or surprising empirical finding is typically **below the novelty bar**. The contribution would need one of:
- A theoretical analysis of why adversarial + adapters work better together
- A surprising finding (e.g., the combination works dramatically better than expected)
- A fundamentally different adapter architecture with clear justification

## Differentiation Suggestions

1. **Add a theoretical contribution**: Derive a generalization bound for the adapter that explains why subject-specific adapters help adversarial training
2. **Target a harder setting**: Cross-dataset transfer (not just cross-subject) where the gap over Li et al. would be larger
3. **Demonstrate surprising behavior**: Show that the method exhibits qualitatively different behavior at scale (more subjects in pre-training)
4. **Novel adapter architecture**: If your adapter design is truly different from Li et al., emphasize the architectural novelty and why it matters
