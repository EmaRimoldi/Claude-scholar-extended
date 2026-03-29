---
name: build-data
description: Translate dataset specifications from experiment-plan.md into working data generators and loaders. Produces @register_dataset classes and Hydra configs.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to experiment-plan.md)
    required: false
    default: experiment-plan.md
tags: [Development, Data, ML]
---

# Build Data Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Data files → `$PROJECT_DIR/data/`
- Data loader scripts → `$PROJECT_DIR/src/`

Never write data files to the repository root.

Translate dataset specifications into working code.

## Goal

Activates the `experiment-data-builder` skill to produce data generators (synthetic tasks) and loaders (HuggingFace/local) that register with the project's DatasetFactory.

## Usage

```bash
/build-data                        # reads experiment-plan.md
/build-data path/to/my-plan.md     # explicit plan file
```

## Workflow

1. Parse Datasets & Splits section from experiment-plan.md
2. Activate `experiment-data-builder` skill
3. Write: src/data_module/dataset/{task}.py + run/conf/dataset/{task}.yaml per dataset
4. Run data validation checks

## COMPLETION CRITERIA

This step is NOT complete until:
1. The dataset loading code has been RUN (not just written)
2. At least one example has been loaded, tokenized, and printed
3. Train/val/test splits are confirmed to exist with expected sizes
4. Output: print `Dataset validated: N_train train, N_val val, N_test test examples`

Do NOT mark this step complete by just saying "code exists in src/data.py". You must execute the code and verify output.

## Integration

- **Primary skill**: `experiment-data-builder`
- **Prerequisite**: `project-scaffold` (directory structure must exist)
- **Feeds into**: `setup-validation` (data integrity checks), `experiment-runner`
