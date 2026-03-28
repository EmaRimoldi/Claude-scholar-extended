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

## Integration

- **Primary skill**: `experiment-data-builder`
- **Prerequisite**: `project-scaffold` (directory structure must exist)
- **Feeds into**: `setup-validation` (data integrity checks), `experiment-runner`
