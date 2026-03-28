# Example: Contribution Positioning

## Project: Contrastive Pre-training for Cross-Subject EEG Decoding
## Target Venue: NeurIPS
## Input Mode: Pipeline (novelty-assessment.md detected)

Using novelty-assessment.md as starting point for positioning.

## Closest Works Selected

| # | Paper | Justification |
|---|---|---|
| 1 | Kostas et al. (2021) -- "BENDR: EEG Pre-training" | Same pre-training paradigm applied to EEG; direct methodological predecessor |
| 2 | Zhang et al. (2023) -- "Subject-Adaptive EEG Decoding" | Subject adaptation is a core concern of our work; overlapping evaluation |
| 3 | Zhao et al. (2022) -- "Domain-Adversarial EEG Transfer" | Dominant baseline for cross-subject EEG transfer; reviewers will expect this comparison |
| 4 | Li et al. (2024) -- "Contrastive EEG with Temporal Augmentations" | Most similar recent work; uses contrastive learning on EEG with different augmentation strategy |

## Differentiation Matrix

### vs. Kostas et al. (2021) -- "BENDR: EEG Pre-training"

| Dimension | Kostas et al. | Our Work | Comparative Statement |
|---|---|---|---|
| Research Question | Can masked prediction pre-training transfer EEG representations? | Can contrastive learning with domain-specific augmentations eliminate subject calibration? | Kostas et al. ask whether pre-training helps at all; we ask whether a specific pre-training strategy can remove calibration entirely. |
| Method | Masked autoencoding on raw EEG | Contrastive loss on augmented temporal segments | We replace reconstruction with a contrastive objective operating on domain-specific temporal augmentations, which captures subject-invariant features rather than signal-level statistics. |
| Models / Data | Transformer encoder, Temple University EEG | Transformer encoder, BCI-IV-2a + MOABB + clinical dataset | We evaluate on motor imagery specifically and add a private clinical dataset, testing a narrower but clinically relevant domain. |
| Key Findings | Pre-training improves downstream by ~2% on average | Pre-training improves by +4.2%, and the gain is driven by augmentation choice | We show that the augmentation strategy, not the pre-training paradigm alone, drives the improvement -- a finding absent from Kostas et al. |
| Limitation Addressed | BENDR still requires 50+ calibration trials per subject | Our approach requires zero calibration trials | We address their stated limitation of calibration dependence. |

### vs. Zhang et al. (2023) -- "Subject-Adaptive EEG Decoding"

| Dimension | Zhang et al. | Our Work | Comparative Statement |
|---|---|---|---|
| Research Question | How to adapt a shared model to individual subjects? | How to learn subject-invariant representations without per-subject adaptation? | Zhang et al. solve adaptation at test time; we avoid the need for adaptation by learning invariant features during pre-training. |
| Method | Subject-specific adapter layers fine-tuned on calibration data | Contrastive pre-training with temporal augmentations; no per-subject components | Our method has no subject-specific parameters, eliminating the calibration requirement. |
| Models / Data | EEGNet backbone, BCI-IV-2a | Transformer backbone, BCI-IV-2a + MOABB + clinical | We use a larger backbone and evaluate on additional datasets, but the key difference is the removal of calibration data. |
| Key Findings | Adapters improve accuracy by 3.5% with 50 calibration trials | We achieve +4.2% with zero calibration trials | We match or exceed their calibration-dependent accuracy without any subject-specific data, suggesting the calibration step is unnecessary given sufficient pre-training. |
| Limitation Addressed | Requires calibration session before each use; impractical for clinical deployment | No calibration needed | This directly addresses their acknowledged limitation of clinical impracticality. |

### vs. Zhao et al. (2022) -- "Domain-Adversarial EEG Transfer"

| Dimension | Zhao et al. | Our Work | Comparative Statement |
|---|---|---|---|
| Research Question | Can adversarial training reduce subject distribution shift? | Can contrastive pre-training learn subject-invariant representations without adversarial training? | Zhao et al. use adversarial alignment; we test whether contrastive learning achieves invariance through augmentation rather than alignment. |
| Method | Domain adversarial neural network (DANN) with subject labels | Contrastive loss on augmented segments; no subject labels needed | Our method requires no subject labels during pre-training, simplifying the pipeline and enabling pre-training on unlabeled data. |
| Models / Data | Shallow CNN, BCI-IV-2a | Transformer, BCI-IV-2a + MOABB + clinical | We use a larger model and more datasets; our ablation isolates the contribution of augmentations vs. the objective. |
| Key Findings | DANN reduces cross-subject gap by ~2.8% | Contrastive pre-training reduces the gap by 4.2%, and augmentation ablation shows this is not due to the loss function alone | We demonstrate that the augmentation strategy contributes more than the training objective, which reframes the domain adaptation question. |
| Limitation Addressed | Requires subject labels; performance degrades with many subjects | Label-free; scales with number of pre-training subjects | We address their scaling limitation: our method improves as more unlabeled subjects are added. |

### vs. Li et al. (2024) -- "Contrastive EEG with Temporal Augmentations"

| Dimension | Li et al. | Our Work | Comparative Statement |
|---|---|---|---|
| Research Question | Do temporal augmentations improve contrastive EEG learning? | Which augmentations drive contrastive EEG learning, and can they eliminate calibration? | Li et al. test whether augmentations help; we test which augmentations matter and push toward zero-calibration deployment. |
| Method | SimCLR-style contrastive loss with time-shift and jitter | Contrastive loss with EEG-specific augmentations (phase perturbation, band-specific masking) | We use physiologically motivated augmentations rather than generic signal augmentations, yielding larger and more consistent improvements. |
| Models / Data | CNN backbone, BCI-IV-2a only | Transformer backbone, BCI-IV-2a + MOABB + clinical | We evaluate on three datasets vs. one, demonstrating cross-paradigm robustness. |
| Key Findings | Contrastive + temporal augmentations improve by +2.5% | EEG-specific augmentations yield +4.2%; removing EEG-specific augmentations and using generic ones recovers only +1.8% | We show that augmentation design is the primary driver, not the contrastive framework itself -- a distinction Li et al. do not make. |
| Limitation Addressed | Does not compare augmentation types; unclear what drives improvements | Systematic augmentation ablation isolates the contribution | We fill their analytical gap by providing the first augmentation ablation study in this setting. |

## Contribution Statement Candidates

**Variant 1 (Finding-first)**:
We find that EEG-specific augmentations, not the contrastive objective itself, drive cross-subject transfer in EEG pre-training. While prior work has shown that contrastive learning improves EEG decoding (Kostas et al., 2021; Li et al., 2024), our systematic ablation reveals that physiologically motivated augmentations -- phase perturbation and band-specific masking -- account for over 70% of the improvement. This insight enables zero-calibration cross-subject decoding that matches or exceeds calibration-dependent methods.

**Variant 2 (Method-first)**:
We introduce a contrastive pre-training framework for EEG that uses physiologically grounded augmentations -- phase perturbation and frequency-band masking -- to learn subject-invariant representations without any calibration data. Unlike domain adaptation approaches (Zhao et al., 2022; Zhang et al., 2023) that require subject labels or calibration trials, our method requires neither, while achieving a +4.2% improvement over supervised baselines. A systematic augmentation ablation demonstrates that augmentation design, rather than the learning objective, is the primary driver of transfer performance.

**Variant 3 (Problem-first)**:
Cross-subject EEG decoding remains limited by the need for per-subject calibration, which is impractical in clinical and consumer settings. We show that contrastive pre-training with EEG-specific augmentations eliminates this calibration requirement entirely, achieving +4.2% over supervised baselines with zero calibration trials. Our ablation study reveals that the augmentation strategy is the critical design choice, reframing the cross-subject transfer problem from one of domain alignment to one of augmentation design.

## Reviewer Objection Anticipation

### Objection 1: "Incremental over Li et al. (2024) -- both use contrastive learning on EEG"

**Response**: We respectfully note that while both works employ contrastive learning for EEG, the key contribution of our paper is not the contrastive framework itself but the finding that augmentation design is the primary driver of transfer performance. Li et al. use generic temporal augmentations (time-shift, jitter) and report a +2.5% improvement without analyzing the source of the gain. Our systematic ablation (Table 3) shows that replacing EEG-specific augmentations with generic ones reduces the improvement from +4.2% to +1.8%, demonstrating that the augmentation strategy -- not the contrastive loss -- is the critical component. This analytical finding is absent from Li et al. and changes how the community should approach contrastive EEG learning.

### Objection 2: "Limited evaluation -- only motor imagery paradigm"

**Response**: We chose motor imagery as the primary evaluation paradigm because it is the standard benchmark for cross-subject EEG transfer (BCI-IV-2a) and allows direct comparison with all baselines. To address generalization, we additionally evaluate on MOABB (which includes P300 and SSVEP paradigms) and a private clinical motor imagery dataset with a different acquisition protocol (Table 2). The consistent improvements across three datasets with different paradigms and hardware provide evidence of robustness. We acknowledge that evaluation on speech or auditory EEG paradigms would further strengthen the generalization claim and note this as future work.

### Objection 3: "Missing comparison with BENDR (Kostas et al., 2021)"

**Response**: We include BENDR as a baseline in Table 1 (row 5), where our method outperforms it by +2.0% on BCI-IV-2a (71.2% vs. 69.2%). We also compare pre-training strategies directly in the ablation study (Table 3): replacing our contrastive objective with BENDR's masked prediction objective while keeping our augmentations yields 70.5%, suggesting that the augmentation strategy provides most of the benefit regardless of the pre-training loss. We have expanded the discussion of this comparison in Section 4.3 of the revised manuscript.

## Related Work Paragraph Drafts

### Kostas et al. (2021)

Kostas et al. [Kostas et al., 2021] demonstrated that self-supervised pre-training on large-scale EEG data can improve downstream decoding tasks, introducing BENDR, a masked autoencoding approach for EEG representation learning. While BENDR established the viability of EEG pre-training, it relies on signal reconstruction and still requires subject-specific calibration for optimal performance. Our work builds upon this foundation by replacing masked prediction with a contrastive objective paired with physiologically motivated augmentations, which we show learns more transferable subject-invariant features without any calibration requirement.

### Zhang et al. (2023)

Zhang et al. [Zhang et al., 2023] proposed subject-specific adapter layers that are fine-tuned on a small amount of per-subject calibration data, achieving strong cross-subject transfer on motor imagery benchmarks. Their approach represents the state of the art in calibration-dependent transfer, but the requirement for calibration data limits clinical deployability. Our work complements their contribution by demonstrating that contrastive pre-training with domain-specific augmentations can match the accuracy of adapter-based methods while eliminating the calibration step entirely.

### Zhao et al. (2022)

Zhao et al. [Zhao et al., 2022] applied domain-adversarial training to EEG transfer learning, using subject labels to align feature distributions across individuals. While effective for small numbers of subjects, adversarial alignment degrades as the number of source subjects increases and requires subject identity labels during training. Our approach avoids both constraints by learning subject-invariant representations through contrastive augmentation rather than explicit distribution alignment, and our results suggest that augmentation-driven invariance scales more favorably with the number of pre-training subjects.

### Li et al. (2024)

Li et al. [Li et al., 2024] explored contrastive learning for EEG with temporal augmentations, including time-shift and jitter, demonstrating improvements over supervised baselines on BCI-IV-2a. However, their work does not analyze which augmentations drive the improvement or whether the gains generalize beyond a single dataset. We extend their investigation by introducing EEG-specific augmentations (phase perturbation, band-specific masking) and providing a systematic ablation study that disentangles the contributions of the augmentation strategy from the contrastive objective, revealing that augmentation design is the dominant factor.
