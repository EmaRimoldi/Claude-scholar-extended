# Example: Experiment Plan

## Context

**Hypotheses source**: `hypotheses.md` (pipeline mode)
**Research question**: Can contrastive pre-training improve cross-subject EEG decoding?
**Target venue**: NeurIPS

---

# Experiment Plan: Contrastive Pre-training for Cross-Subject EEG

## Input Mode: Pipeline (hypotheses.md detected)

## Baselines (4)

| # | Baseline | Justification |
|---|----------|---------------|
| 1 | Supervised from scratch | H0 baseline: no pre-training |
| 2 | Fine-tuning from ImageNet pre-trained encoder | Transfer learning control (different domain) |
| 3 | MMD domain adaptation (Pan et al., 2020) | Strongest classical domain adaptation for EEG |
| 4 | EEGNet supervised (Lawhern et al., 2018) | Standard EEG architecture baseline |

## Ablations (3)

| # | Ablation | Tests | Expected Impact |
|---|----------|-------|-----------------|
| 1 | Remove contrastive loss (supervised only) | Is contrastive pre-training needed? | Large drop (core hypothesis H1) |
| 2 | Remove subject-specific adapters | Are adapters needed for transfer? | Moderate drop |
| 3 | Reduce pre-training subjects to 50% | Does data diversity matter? | Tests H2 (scaling behavior) |

## Datasets & Splits

### Primary Dataset
- **BCI Competition IV-2a** (Brunner et al., 2008)
  - 9 subjects, 4 motor imagery classes
  - Evaluation: Leave-one-subject-out cross-validation (9 folds)
  - Pre-training: 8 subjects, fine-tuning + testing: 1 held-out subject

### Secondary Dataset (validation)
- **MOABB PhysioNet Motor Imagery** (Schalk et al., 2004)
  - 109 subjects, 2 motor imagery classes
  - Evaluation: Same leave-one-subject-out protocol
  - Purpose: Validate generalization to different paradigm/recording setup

## Metrics

| Metric | Type | Justification |
|--------|------|---------------|
| Balanced accuracy | Primary | Standard for BCI-IV-2a, handles class imbalance |
| Cohen's kappa | Secondary | Standard for BCI competitions, chance-corrected |
| Training time (GPU-hours) | Efficiency | Pre-training adds overhead, must quantify |

## Sample Size

- **5 seeds** per configuration (community convention for BCI-IV-2a)
- **9 folds** per seed (leave-one-subject-out)
- Total per method: 45 runs

**Power analysis skipped** -- no prior effect size or variance estimates available for contrastive pre-training on EEG. 5 seeds is standard for this benchmark. If the observed effect is small (<2%), consider increasing to 10 seeds before drawing conclusions.

## Resource Estimate

| Phase | Configurations | Runs | GPU-hours (est.) |
|-------|---------------|------|-----------------|
| Quick validation | 2 methods x 1 seed x 3 subjects | 6 | ~12h |
| Full sweep | 6 methods x 5 seeds x 9 subjects | 270 | ~540h |
| Ablations | 3 ablations x 5 seeds x 9 subjects | 135 | ~270h |
| Secondary dataset | 2 methods x 3 seeds x 20 subjects | 120 | ~240h |
| **Total** | | **531** | **~1,062h** |

Hardware: A100 40GB, ~2 GPU-hours per run

## Execution Order

### Phase 1: Quick Validation (Stop-or-Go)
**Budget**: ~12 GPU-hours | **Duration**: ~1 day

1. Run proposed method + supervised baseline
2. 1 seed, 3 subjects only
3. **Go criterion**: >+1% improvement over baseline
4. **Stop criterion**: <+1% -- activate `failure-diagnosis` before spending more compute

### Phase 2: Core Experiments
**Budget**: ~540 GPU-hours | **Duration**: ~5 days

1. All 4 baselines + proposed method + 1 ablation (no contrastive loss)
2. 5 seeds, all 9 subjects
3. **Checkpoint**: After 2 seeds, check variance. If std > 5%, investigate before continuing.

### Phase 3: Ablation Studies
**Budget**: ~270 GPU-hours | **Duration**: ~3 days

1. Remaining 2 ablations
2. 5 seeds, all 9 subjects
3. Run only if Phase 2 confirms the main effect

### Phase 4: Secondary Dataset (Optional)
**Budget**: ~240 GPU-hours | **Duration**: ~3 days

1. Proposed method + supervised baseline on MOABB
2. 3 seeds, 20 subjects (subset)
3. Run only if Phase 2 confirms AND reviewers/advisor recommend

## Decision Points

```
Phase 1 complete
    |
    +-- improvement > +1% --> Proceed to Phase 2
    +-- improvement < +1% --> Activate failure-diagnosis

Phase 2 complete
    |
    +-- H1 confirmed (>+3%, p<0.05) --> Proceed to Phase 3
    +-- H1 ambiguous (+1-3%) --> Increase seeds to 10, then decide
    +-- H1 rejected (<+1%) --> Activate failure-diagnosis

Phase 3 complete
    |
    +-- All ablations informative --> Proceed to Phase 4 or writing
    +-- Surprising ablation result --> Investigate, may revise hypothesis
```

## State File

Created `experiment-state.json`:

```json
{
  "$schema": "experiment-state-v1",
  "project": "contrastive-eeg-transfer",
  "created": "2026-03-27T10:00:00Z",
  "updated": "2026-03-27T10:00:00Z",
  "iteration": 0,
  "max_iterations": 3,
  "active_hypothesis": {
    "id": "H1",
    "summary": "Contrastive pre-training improves cross-subject EEG transfer by +5% balanced accuracy",
    "source_file": "hypotheses.md"
  },
  "status": "planned",
  "latest_analysis": null,
  "history": [],
  "resource_budget": {
    "total_gpu_hours": 1062,
    "used_gpu_hours": 0,
    "remaining_gpu_hours": 1062
  },
  "deadline": null
}
```
