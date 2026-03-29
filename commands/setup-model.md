---
name: setup-model
description: Load, configure, introspect, and prepare models for experiments. Handles HuggingFace loading, hook attachment, architecture discovery, and ablation setup.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to experiment-plan.md)
    required: false
    default: experiment-plan.md
tags: [Development, Model, ML, Interpretability]
---

# Setup Model Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Model code → `$PROJECT_DIR/src/`
- Model configs → `$PROJECT_DIR/configs/`

Never write model files to the repository root.

Prepare models for the experiment pipeline.

## Goal

Activates the `model-setup` skill to load models, discover architecture, attach hooks for activation extraction, and prepare ablation utilities.

## Usage

```bash
/setup-model                       # reads experiment-plan.md
/setup-model path/to/my-plan.md    # explicit plan file
```

## Workflow

1. Parse model specifications from experiment-plan.md
2. Activate `model-setup` skill
3. Write: model loading code, hook infrastructure, ablation utilities in src/model_module/
4. Generate model-architecture.json for each model

## COMPLETION CRITERIA

This step is NOT complete until:
1. The model has been loaded from cache (no download needed)
2. A forward pass on 1 batch succeeds (even on CPU)
3. The freezing/modification logic has been tested on the loaded model
4. Output: print `Model validated: N params total, M trainable with strategy X`

Do NOT mark this step complete by just saying "code exists in src/model.py". You must execute the code and verify output.

## Integration

- **Primary skill**: `model-setup`
- **Prerequisite**: `project-scaffold` (directory structure must exist)
- **Feeds into**: `measurement-implementation` (provides activations), `setup-validation`, `experiment-runner`
