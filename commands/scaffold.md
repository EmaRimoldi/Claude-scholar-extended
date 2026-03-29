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

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- `src/` → `$PROJECT_DIR/src/`
- `configs/` → `$PROJECT_DIR/configs/`
- `data/` → `$PROJECT_DIR/data/`
- `tests/` → `$PROJECT_DIR/tests/`
- `pyproject.toml` → `$PROJECT_DIR/pyproject.toml`

Never write project scaffold files to the repository root.

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

## EFFICIENCY: Batch file creation

When creating project structure (configs, __init__.py files, boilerplate):
- Use Python scripts or bash loops to create repetitive files in bulk
- Do NOT write each config file individually if they follow a pattern
- Example: generate all strategy configs from a Python dict in one script

This saves context window and execution time for the reasoning-heavy steps.

## Integration

- **Primary skill**: `project-scaffold`
- **Prerequisite**: `experiment-design` output (recommended) or user description
- **Feeds into**: `experiment-data-builder`, `model-setup`, `measurement-implementation`
