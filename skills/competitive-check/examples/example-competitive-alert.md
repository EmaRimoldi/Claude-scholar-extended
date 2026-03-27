# Example: Competitive Check

## Turn 1: Query Generation

### Contribution
"Cross-subject EEG transfer learning using contrastive pre-training with EEG-specific augmentations"

### Key Differentiators
1. EEG-specific augmentations (time warping, channel dropout, frequency masking)
2. Focus on speech decoding paradigm (not motor imagery)
3. Analysis of augmentation impact on learned representations

### Search Queries

#### Semantic Scholar
1. `"cross-subject" "EEG" "contrastive learning"` (year:2025-2026)
2. `"EEG" "self-supervised" "transfer learning"` (year:2025-2026)
3. `"brain-computer interface" "contrastive pre-training"` (year:2025-2026)
4. `"EEG" "domain adaptation" "augmentation"` (year:2025-2026)

#### arXiv
1. `https://arxiv.org/search/?query=cross-subject+EEG+contrastive&searchtype=all&order=-announced_date_first`
2. `https://arxiv.org/search/?query=EEG+self-supervised+transfer&searchtype=all&order=-announced_date_first`
3. `https://arxiv.org/search/?query=BCI+contrastive+augmentation&searchtype=all&order=-announced_date_first`

#### Google Scholar
1. `"cross-subject EEG" "contrastive learning" after:2025`
2. `"EEG transfer" "self-supervised pre-training" after:2025`
3. `"EEG augmentation" "contrastive" after:2025`

### Instructions
Run these queries on each platform. Copy the top 10-15 results (title + abstract or snippet) and paste them back. I will analyze the overlap.

---

## Turn 2: Results Analysis

### Competitive Landscape Alert -- 2026-03-27

**Status**: CAUTION

### High Overlap (1 paper)

**Wang et al. (2026)** "ContraEEG: Contrastive Learning for Cross-Subject EEG Decoding"
- **What they do**: SimCLR-style contrastive learning for cross-subject EEG, motor imagery
- **Overlap**: Same core method (contrastive pre-training for cross-subject EEG)
- **Difference**: They focus on motor imagery; you focus on speech decoding. They use standard augmentations; you use EEG-specific augmentations.
- **Threat level**: MEDIUM — same method family, different paradigm and augmentation strategy

### Medium Overlap (2 papers)

**Chen et al. (2025)** "Self-Supervised EEG Representation Learning for BCI"
- **Overlap**: Self-supervised learning for EEG, but uses masked autoencoding, not contrastive
- **Threat level**: LOW — different self-supervised method

**Park et al. (2026)** "Augmentation Strategies for EEG Deep Learning"
- **Overlap**: Studies EEG-specific augmentations, but for supervised learning only
- **Threat level**: LOW — complements your work rather than competing

### Low/No Overlap (remaining papers)
- Other results were about different modalities or different problems

### Recommendations
1. **Cite Wang et al.** in related work and clearly differentiate on paradigm + augmentation
2. **Run your method on motor imagery** to provide a direct comparison with ContraEEG
3. **Emphasize the augmentation contribution** — this is your unique angle that Wang et al. lack
4. **Consider reaching out to Wang et al.** — if your approaches are complementary, concurrent work can strengthen both papers
