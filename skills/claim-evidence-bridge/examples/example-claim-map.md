# Example: Claim-Evidence Map

## Project: Contrastive Pre-training for Cross-Subject EEG
## Target Venue: NeurIPS

## Input Mode: Pipeline (analysis-report.md detected)

## Claim-Evidence Mapping

### Claim 1: "Contrastive pre-training significantly improves cross-subject EEG decoding"

- **Evidence**: Table 1 -- +4.2% +/- 0.6% balanced accuracy, p=0.003, paired t-test, 9 subjects, 5 seeds
- **Strength**: **STRONG**
- **Alternative interpretations**: None identified; ablation confirms contrastive loss is the driver
- **Language**: Claim as stated
- **Confounds**: None

### Claim 2: "EEG-specific augmentations are critical for contrastive EEG learning"

- **Evidence**: Table 3 (ablation) -- removing EEG augmentations drops improvement from +4.2% to +1.8% (p < 0.01)
- **Strength**: **STRONG**
- **Alternative interpretations**: Could be that any augmentation helps, not EEG-specific ones
- **Language**: Claim as stated, but acknowledge the alternative interpretation
- **Recommended addition**: Compare EEG-specific vs. generic augmentations directly

### Claim 3: "Our method achieves state-of-the-art on BCI-IV-2a"

- **Evidence**: Table 2 -- 71.2% vs. prior SOTA 69.8%
- **Strength**: **MODERATE** -- only 1.4% improvement, no significance test against prior SOTA
- **Alternative interpretations**: Prior SOTA used different preprocessing; comparison may not be fair
- **Language**: HEDGE -> "competitive with state-of-the-art" or add significance test
- **Recommended addition**: Run significance test or clarify preprocessing differences

### Claim 4: "The approach generalizes to different EEG paradigms"

- **Evidence**: Only tested on motor imagery (BCI-IV-2a)
- **Strength**: **UNSUPPORTED** -- no cross-paradigm experiments conducted
- **Language**: REMOVE from main claims, mention as future work
- **Remedy**: Run on MOABB speech dataset to support this claim (estimated 20 GPU-hours)

### Claim 5: "Benefits scale with pre-training data diversity"

- **Evidence**: Figure 3 -- positive slope of accuracy vs. number of pre-training subjects (R^2 = 0.72)
- **Strength**: **MODERATE** -- trend is clear but based on only 5 data points (3, 5, 7, 9, 12 subjects)
- **Language**: HEDGE -> "Our results suggest that benefits increase with pre-training data diversity"

## Scope Decision

| Decision | Claims | Action |
|---|---|---|
| **Include** | 1 (contrastive improvement), 2 (augmentation ablation) | Primary contributions -- abstract and introduction |
| **Hedge** | 3 (SOTA), 5 (scaling) | Soften language in results section |
| **Remove** | 4 (generalization) | Move to future work |
| **Supplementary** | Detailed augmentation comparison | Supports Claim 2 but too detailed for main paper |

## Venue Fit: NeurIPS

The primary contribution (+4.2% from contrastive pre-training with domain-specific augmentations) is a solid empirical finding. The augmentation ablation story strengthens the paper by explaining *why* it works. For NeurIPS, consider adding:
- A brief theoretical motivation for why EEG-specific augmentations matter
- Visualization of learned representations before/after augmentation
- These would elevate the paper from "solid empirical" to "empirical + insight"

## Writing Checklist

- [ ] Claim 1: Cite Table 1 with exact numbers and significance test
- [ ] Claim 2: Cite Table 3 (ablation), acknowledge alternative interpretation
- [ ] Claim 3: Use "competitive with" language, clarify preprocessing differences
- [ ] Claim 4: Mention in future work section ONLY
- [ ] Claim 5: Use "suggests" language, note the limited data points
- [ ] All claims trace to specific evidence in the analysis bundle
