---
name: design-experiments
description: Generate a full experiment plan from hypotheses. Takes hypotheses (from file or user input) and produces baselines, ablations, sample size, resource estimation, and execution ordering.
args:
  - name: hypotheses_file
    description: Path to hypotheses file (defaults to hypotheses.md in project root; if absent, prompts user for description)
    required: false
    default: hypotheses.md
tags: [Research, Experimental Design, Planning]
---

# Design Experiments Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- `experiment-plan.md` → `$PROJECT_DIR/docs/experiment-plan.md`
- `experiment-state.json` → `$PROJECT_DIR/experiment-state.json`

Never write research documents to the repository root.

Generate a complete experiment plan from testable hypotheses.

## Goal

This command activates the `experiment-design` skill to produce a structured experiment plan covering:

1. **Baseline selection** with justification
2. **Ablation study design** with predicted impacts
3. **Dataset and split strategy**
4. **Sample size determination** (convention-based or power analysis)
5. **Resource estimation** (GPU-hours, storage, wall time)
6. **Execution ordering** with stop-or-go gates
7. **`experiment-state.json`** initialization for the iteration loop

## Usage

### Basic (reads hypotheses.md from project root)

```bash
/design-experiments
```

### With explicit hypotheses file

```bash
/design-experiments path/to/my-hypotheses.md
```

### Without a hypotheses file (interactive)

If no `hypotheses.md` is found, the skill will:
1. Ask the user to describe what they want to test
2. Infer testable hypotheses from the description
3. Ask for confirmation before designing experiments

## Workflow

1. **Locate hypotheses**: Read `hypotheses.md` or prompt user
2. **Activate `experiment-design` skill**: Generate the full plan
3. **Write outputs**:
   - `experiment-plan.md` in `$PROJECT_DIR/docs/`
   - `experiment-state.json` in `$PROJECT_DIR/` (if not already present)
4. **Obsidian write-back** (if bound):
   - Create `Experiments/{experiment-line}.md` with planned status
   - Append to `Daily/YYYY-MM-DD.md`

## Integration

- **Prerequisite skill**: `hypothesis-formulation` (recommended but not required)
- **Primary skill**: `experiment-design`
- **Feeds into**: Experiment execution by the researcher
- **State tracking**: `experiment-state.json` enables session-start reminders

---

## Statistical Rigor Requirements

These rules are **mandatory** for every experiment plan produced by this command.

- **Minimum seeds**: 5 seeds per condition for the main experiment, 10 for the primary comparison. 3 seeds is ONLY acceptable for a quick smoke test, never for publishable results.
- **Statistical tests**: Every experiment plan MUST specify which statistical test will be used (paired bootstrap, Wilcoxon signed-rank, or permutation test). P-values or confidence intervals are mandatory.
- **Effect size**: Cohen's d or equivalent must be computed for every comparison. If expected effect size < 0.5, require minimum 10 seeds.
- **Power analysis**: If prior effect sizes are unknown, default to d=0.3 (small effect) and compute required seeds accordingly.

## Baseline Completeness Checklist

Before finalizing any experiment plan, the following checklist **must** be completed. Every unchecked item requires explicit justification.

- [ ] For each proposed method, identify at least ONE alternative method that could explain the results
- [ ] If using attention as explanation → must compare with gradient-based methods (IG, SHAP) as baselines
- [ ] If claiming faithfulness → must include adversarial tests (attention swap, counterfactual)
- [ ] If claiming improvement → must include ablation isolating EACH component
- [ ] Multi-dataset: require at least 2 datasets/settings. If only 1 dataset, explicitly document this as a limitation and justify

## Metric-Claim Alignment Check

A mandatory cross-reference step that **blocks** the experiment plan if any key term has zero corresponding metrics.

1. Extract every key term from the research question and hypotheses.
2. For each key term, verify at least one metric operationalizes it:
   - "faithfulness" → REQUIRE at least one of: comprehensiveness, sufficiency, AOPC, attention-IG correlation
   - "accuracy" → REQUIRE F1, accuracy, or AUC
   - "plausibility" → REQUIRE token-F1, AUPRC, IoU vs human rationales
3. If any key term has zero corresponding metrics, **BLOCK** the experiment plan and request the user to add appropriate metrics before proceeding.

## Threat-to-Validity Analysis

For **each hypothesis** in the experiment plan, the following three questions must be answered explicitly:

1. **Falsification test**: What experiment would DISPROVE this hypothesis?
2. **Confound identification**: What confound could explain the result without the proposed mechanism?
3. **Adversarial validation**: What adversarial test validates the causal claim?

The plan must document these answers alongside each hypothesis. If any hypothesis lacks all three answers, the plan is considered incomplete.
