---
name: project-scaffold
description: This skill should be used when the user asks to "scaffold a project", "create project structure", "initialize experiment project", "set up pyproject.toml", "create src directory", or after experiment-design produces an experiment plan and before writing any experiment code. Generates a runnable ML experiment project from experiment-plan.md with Factory/Registry patterns, Hydra configs, and entry points.
version: 0.1.0
tags: [Development, Scaffolding, ML, Project Structure]
---

# Project Scaffold

Generates a complete, runnable ML experiment project from `experiment-plan.md`. Produces all boilerplate -- dependency file, source tree, config templates, entry point, Makefile -- so that subsequent skills (`experiment-data-builder`, `model-setup`, `measurement-implementation`) write into a working structure.

## Core Features

### 1. Dependency Inference

Read experiment-plan.md to determine required packages:

- **Always included**: `torch`, `numpy`, `hydra-core`, `omegaconf`, `matplotlib`, `pandas`, `scipy`
- **If HuggingFace models**: add `transformers`, `accelerate`, `datasets`
- **If NLP tasks**: add `tokenizers`, `sentencepiece` if needed
- **If cluster execution**: add `submitit` (SLURM integration)
- **Package manager**: `uv` (per CLAUDE.md preference). Generate `pyproject.toml` with `[project]` metadata and `[tool.uv]` section.

### 2. Source Tree Generation

Create the `src/` directory tree following `architecture-design` patterns exactly:

```
src/
├── data_module/
│   ├── __init__.py
│   └── dataset/
│       └── __init__.py          # DatasetFactory + register_dataset + auto-import
├── model_module/
│   ├── __init__.py
│   └── model/
│       └── __init__.py          # ModelFactory + register_model + auto-import
├── metrics/
│   ├── __init__.py              # MetricFactory + register_metric + auto-import
│   └── (empty, filled by measurement-implementation)
└── utils/
    ├── __init__.py
    ├── seed.py                  # set_seed() from experiment-reproducibility rule
    ├── environment.py           # log_environment() from experiment-reproducibility rule
    └── registry.py              # Shared import_modules() utility
```

Each `__init__.py` with a Factory implements the pattern from `architecture-design`:
- `FACTORY: Dict = {}`
- `register_X(name)` decorator
- `XFactory(name)` lookup function
- `import_modules()` auto-discovery

### 3. Hydra Configuration Templates

Create `run/conf/` structure:

```
run/conf/
├── config.yaml                  # Default composition
├── dataset/
│   └── (empty, filled by experiment-data-builder)
├── model/
│   └── (empty, filled by model-setup)
└── experiment/
    └── default.yaml             # seed, output_dir, device
```

`config.yaml` uses Hydra defaults composition:
```yaml
defaults:
  - dataset: ???
  - model: ???
  - experiment: default

hydra:
  run:
    dir: outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}
```

### 4. Entry Point

Create `run_experiment.py` with Hydra main:

```python
@hydra.main(config_path="run/conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    set_seed(cfg.experiment.seed)
    log_environment()
    # Placeholder: experiment logic goes here
    # Filled by experiment-runner skill
```

### 5. Makefile

Generate `Makefile` with common targets:

```makefile
.PHONY: setup test run collect analyze clean

setup:
	uv sync

test:
	uv run pytest tests/ -v

run:
	uv run python run_experiment.py $(ARGS)

collect:
	uv run python -m src.collect_results

analyze:
	@echo "Run /analyze-results in Claude Code"

clean:
	rm -rf outputs/__pycache__ .pytest_cache
```

### 6. Supporting Files

- `.gitignore` (outputs/, .venv/, __pycache__, *.pt, wandb/, .hydra/)
- `tests/__init__.py` (empty, for pytest discovery)
- `tests/test_smoke.py` (minimal import smoke test)

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Experiment plan** -- from `experiment-design` output (`experiment-plan.md`)
2. The skill reads the plan to infer: which models (HuggingFace? custom?), which datasets (synthetic? real?), which metrics, which compute target

### Mode B: Standalone (manual)

1. **Project description** -- user describes what the project needs
2. **Tech stack** -- user specifies dependencies
3. The skill generates a generic ML project scaffold

When running in Mode B, state: "No experiment-plan.md found. Generating generic ML project scaffold."

## Outputs

- `pyproject.toml` with inferred dependencies
- `src/` directory tree with Factory/Registry wiring
- `run/conf/` Hydra config templates
- `run_experiment.py` entry point
- `Makefile` with common targets
- `.gitignore`, `tests/` skeleton

## When to Use

### Scenarios for This Skill

1. **After experiment design** -- have an experiment plan, need a project to implement it in
2. **Starting a new ML project** -- need standard structure with Factory/Registry
3. **After hypothesis revision** -- new iteration may need updated dependencies

### Typical Workflow

```
experiment-design -> [project-scaffold] -> experiment-data-builder / model-setup / measurement-implementation
```

**Output Files:**
- Complete project directory structure ready for experiment code

## Integration with Other Systems

### Complete Pipeline

```
experiment-plan.md
    |
project-scaffold (Create project)  <-- THIS SKILL
    |
    ├── experiment-data-builder (Fill src/data_module/)
    ├── model-setup (Fill src/model_module/)
    └── measurement-implementation (Fill src/metrics/)
```

### Data Flow

- **Depends on**: `experiment-design` output (Mode A) OR user description (Mode B)
- **Feeds into**: `experiment-data-builder`, `model-setup`, `measurement-implementation` (all write into the scaffolded structure)
- **Extends**: `architecture-design` (uses its patterns for Factory/Registry)
- **References**: `experiment-reproducibility` rule (imports seed and environment utilities)
- **Hook activation**: Keyword trigger in `skill-forced-eval.js`
- **New command**: `/scaffold`

### Key Configuration

- **Package manager**: `uv` (per CLAUDE.md)
- **Config system**: Hydra + OmegaConf (per CLAUDE.md)
- **Patterns**: Factory/Registry from `architecture-design`
- **Reproducibility**: `set_seed()` and `log_environment()` from `experiment-reproducibility` rule

## Additional Resources

### Reference Files

- **`references/template-catalog.md`** -- Template Catalog
  - Complete listing of all generated files with their contents
  - Factory/Registry implementation code (canonical versions)
  - Hydra config templates
  - Entry point template
  - Makefile template (with pre-flight-validate and cpu-smoke-test targets)
  - Pre-flight validation script template (unit tests + config checks)
  - CPU smoke test script template (real training on CPU with minimal data)
  - When to add optional dependencies (transformers, datasets, etc.)

### Example Files

- **`examples/example-scaffold-output.md`** -- Example Scaffold Output
  - Shows the complete file tree for a sample interpretability experiment
  - Includes full content of key files (pyproject.toml, __init__.py, run_experiment.py)
