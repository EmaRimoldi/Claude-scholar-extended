---
name: experiment-data-builder
description: This skill should be used when the user asks to "build data generators", "create synthetic data", "implement dataset loaders", "generate data from experiment plan", "data construction", "register dataset", or after project-scaffold creates the directory structure and before running experiments. Translates dataset specifications from experiment-plan.md into working data generators and loaders that register with the Factory/Registry from project-scaffold.
version: 0.1.0
tags: [Data, Synthetic Data, Dataset, ML, Experiment Pipeline]
---

# Experiment Data Builder

Translates dataset specifications from `experiment-plan.md` into working data generators and loaders that register with the Factory/Registry from `project-scaffold`. Produces `@register_dataset` classes, Hydra config YAML files, and validation methods for every dataset in the experiment plan.

## Core Features

### 1. Specification Parsing

Read the **Datasets & Splits** section from `experiment-plan.md` and extract a structured specification for each dataset:

- **Task name**: identifier used for `@register_dataset(name)` and the Hydra config filename
- **Type**: `synthetic` | `real` | `benchmark`
- **Mathematical definition** (synthetic only): the function family, parameter distributions, noise model
- **Source** (real only): HuggingFace identifier, local path, or download URL
- **Split strategy**: train/val/test ratios, cross-validation scheme, leave-one-out protocol
- **Dimensionality**: input dimensions, output dimensions, sequence length
- **Noise model** (synthetic only): additive Gaussian, label noise, heteroscedastic, none

When a field is missing from the plan, prompt the user: "The experiment plan specifies dataset `{name}` but does not include `{field}`. Please provide or confirm a default."

### 2. Synthetic Data Generation

For each synthetic task, produce a `@register_dataset` class implementing the mathematical specification:

- **Fresh task parameters per sequence**: Each episode (ICL) or sample batch draws new latent parameters (e.g., new weight vector `w`, new polynomial coefficients). This prevents the model from memorizing a single task.
- **Input distribution**: Gaussian (`torch.randn`), uniform (`torch.rand`), or user-specified distribution via `torch.distributions`.
- **Noise model**: Additive Gaussian (`y += sigma * randn`), label-flip noise (`P(flip) = p`), heteroscedastic noise, or none.
- **Sequence formatting**: Adapts to the paradigm:
  - **ICL (in-context learning)**: `[x1, y1, x2, y2, ..., xk, yk, x_query] -> y_query`
  - **Autoregressive**: Token sequence with causal ordering
  - **Classification**: `(features, label)` pairs
- **Reproducibility**: Use `torch.Generator` seeded per episode so that the dataset is deterministic given a global seed.

Implementation requirements:
- Inherit from `torch.utils.data.Dataset`
- Implement `__init__(self, cfg)`, `__len__`, `__getitem__`
- Accept all parameters from the Hydra config (dimensionality, noise scale, num_examples, etc.)
- Keep files 200-400 lines (per `coding-style.md` rule)

### 3. Real-World Data Loading

For HuggingFace datasets:

- Generate a loader class using `datasets.load_dataset()` with the exact name and version specified in the plan
- Apply preprocessing pipeline: tokenization, normalization, prompt template formatting
- Pin the dataset version: `datasets.load_dataset("name", revision="hash")` or `trust_remote_code=False`
- Cache processed data to `data/processed/` for reproducibility

For local files (CSV, JSON, Parquet):

- Generate a loader with `pandas` / `pyarrow` backend
- Apply type inference and schema validation on first load
- Store the inferred schema as a `.json` sidecar for future validation runs

### 4. Benchmark Wrappers

Standard benchmarks (GLUE, SuperGLUE, MMLU, BCI-IV-2a, etc.) get thin wrappers:

- Load via `datasets.load_dataset()` with the standard configuration and split
- Attach the standard metric from `evaluate` or `datasets.load_metric()`
- Verify loaded data against published baseline numbers (sample count, class distribution)
- Pin version for reproducibility

### 5. Data Validation

Each generated dataset class includes a `validate()` method that runs sanity checks:

- **Shape check**: Output tensor shapes match config (`d_input`, `d_output`, `seq_len`)
- **Value range check**: No NaN, no Inf, values within expected bounds (configurable)
- **Label distribution check**: Class balance within tolerance of expected distribution
- **Sequence formatting check**: ICL episodes have correct interleaving; autoregressive tokens are causally ordered
- **Leakage check**: For train/test splits, verify no sample overlap by hashing

`validate()` is called automatically during `__init__` on a small probe batch (default 8 samples) and can be invoked manually via `dataset.validate(n=100)`.

### 6. Hydra Config Generation

For each dataset, create a YAML config under `run/conf/dataset/`:

```yaml
# run/conf/dataset/{task_name}.yaml
name: "{task_name}"
type: "synthetic"           # or "real" / "benchmark"
d_input: 20
d_output: 1
n_examples: 40              # examples per ICL episode
noise_scale: 0.1
input_distribution: "gaussian"
split:
  train: 100000
  val: 10000
  test: 10000
seed: 42
```

Config files use `_target_` references when appropriate for Hydra instantiation.

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Experiment plan** -- from `experiment-design` output (`experiment-plan.md`)
2. **Project scaffold** -- from `project-scaffold` output (existing `src/data_module/dataset/` directory)
3. The skill reads the Datasets & Splits section, extracts each dataset specification, and generates files

### Mode B: Standalone (manual)

1. **Dataset description** -- user describes dataset requirements in free text
2. **Paradigm** -- user specifies: ICL, autoregressive, classification, regression
3. **Parameters** -- user provides dimensionality, noise, distribution, split sizes
4. The skill generates a single dataset class with config

When running in Mode B, state: "No experiment-plan.md found. Generating dataset from user-provided description."

## Outputs

For each dataset in the plan:

- **`src/data_module/dataset/{task_name}.py`** -- Dataset class with `@register_dataset`, `__getitem__`, and `validate()` method
- **`run/conf/dataset/{task_name}.yaml`** -- Hydra config with all parameters
- **Data validation report** -- printed to console after generation, showing shape/range/label checks for a probe batch

Summary output:

```
Data Builder Report
----------------------------------------------------
Dataset              Type        Shape           Valid
----------------------------------------------------
linear_regression    synthetic   [41, 21]        PASS
sparse_regression    synthetic   [41, 21]        PASS
mnist_icl            real        [41, 785]       PASS
glue_sst2            benchmark   [1, 128]        PASS
----------------------------------------------------
4 datasets built. 0 failures. Configs in run/conf/dataset/.
```

## When to Use

### Scenarios for This Skill

1. **After project scaffold** -- directory structure exists, need to fill `src/data_module/dataset/`
2. **Adding a new dataset mid-project** -- need a new synthetic or real dataset for an ablation
3. **Updating dataset parameters** -- changing noise scale, dimensionality, or split sizes after initial results
4. **Debugging data issues** -- the `validate()` method helps diagnose shape mismatches, leakage, or distribution problems

### Typical Workflow

```
experiment-design -> project-scaffold -> [experiment-data-builder] -> model-setup / experiment-runner
                           OR
user describes dataset -> [experiment-data-builder] -> training loop
```

**Output Files:**
- `src/data_module/dataset/{task_name}.py` for each dataset
- `run/conf/dataset/{task_name}.yaml` for each dataset
- Console validation report

## Integration with Other Systems

### Complete Pipeline

```
experiment-plan.md
    |
project-scaffold (Create project structure)
    |
experiment-data-builder (Fill src/data_module/)  <-- THIS SKILL
    |
    ├── model-setup (Fill src/model_module/)
    ├── measurement-implementation (Fill src/metrics/)
    └── experiment-runner (Run experiments with data + model + metrics)
```

### Data Flow

- **Depends on**: `project-scaffold` (writes into its directory structure), `experiment-design` output (`experiment-plan.md`)
- **Feeds into**: `experiment-runner` (provides data for each run), `setup-validation` (data integrity checks)
- **References**: `architecture-design` for `@register_dataset` pattern and Factory/Registry wiring
- **Hook activation**: Context-aware keyword trigger in `skill-forced-eval.js` for "data generator", "synthetic data", "dataset", "data construction", "build data"
- **New command**: `/build-data` -- generate all dataset classes and configs from experiment plan

### Key Configuration

- **Factory/Registry**: All datasets register via `@register_dataset` from `src/data_module/dataset/__init__.py`
- **Config system**: Hydra + OmegaConf (per CLAUDE.md)
- **Reproducibility**: Per-episode `torch.Generator` seeding, dataset version pinning, hash-based split verification
- **File size**: 200-400 lines per file (per `coding-style.md` rule)
- **Validation**: Automatic probe-batch validation on construction

## Additional Resources

### Reference Files

Detailed patterns and code templates, loaded on demand:

- **`references/synthetic-data-patterns.md`** -- Synthetic Data Patterns
  - Regression tasks: linear, ridge, polynomial, sinusoidal, sparse
  - Classification tasks: linear boundary, XOR, concentric circles, multi-class
  - ICL episode formatting and sequence construction
  - Distribution sampling utilities
  - Common data bugs and how to avoid them

- **`references/data-loading-patterns.md`** -- Data Loading Patterns
  - HuggingFace `datasets` loading with version pinning
  - Local file loading (CSV, JSON, Parquet) with type inference
  - Benchmark wrapper pattern with standard metrics
  - Dataset versioning and fingerprinting

### Example Files

Complete working examples:

- **`examples/example-icl-dataset.py`** -- ICL Linear Regression Dataset Example
  - Complete `@register_dataset` class for linear regression ICL
  - Fresh weight vector per episode, Gaussian inputs, additive noise
  - `validate()` method with shape and value checks
  - Proper type hints and docstring
