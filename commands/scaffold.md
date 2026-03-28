---
name: scaffold
description: Generate a runnable ML experiment project from experiment-plan.md. Creates pyproject.toml, src/ with Factory/Registry, Hydra configs, entry point, and Makefile.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to experiment-plan.md)
    required: false
    default: experiment-plan.md
tags: [Development, Scaffolding, ML]
---

# Scaffold Command

Generate a complete, runnable ML experiment project structure.

## Goal

Activates the `project-scaffold` skill to produce all boilerplate: dependency file, source tree with Factory/Registry wiring, Hydra config templates, entry point, and Makefile.

## Usage

```bash
/scaffold                          # reads experiment-plan.md
/scaffold path/to/my-plan.md       # explicit plan file
```

## Workflow

1. Read experiment-plan.md to infer dependencies and components
2. Activate `project-scaffold` skill
3. Write: pyproject.toml, src/, run/conf/, run_experiment.py, Makefile, .gitignore, tests/

## Integration

- **Primary skill**: `project-scaffold`
- **Prerequisite**: `experiment-design` output (recommended) or user description
- **Feeds into**: `experiment-data-builder`, `model-setup`, `measurement-implementation`
