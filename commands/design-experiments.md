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
   - `experiment-plan.md` in project root
   - `experiment-state.json` in project root (if not already present)
4. **Obsidian write-back** (if bound):
   - Create `Experiments/{experiment-line}.md` with planned status
   - Append to `Daily/YYYY-MM-DD.md`

## Integration

- **Prerequisite skill**: `hypothesis-formulation` (recommended but not required)
- **Primary skill**: `experiment-design`
- **Feeds into**: Experiment execution by the researcher
- **State tracking**: `experiment-state.json` enables session-start reminders
