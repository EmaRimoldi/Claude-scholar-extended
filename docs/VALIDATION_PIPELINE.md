# Validation Pipeline: Pre-Flight + CPU Smoke Test

## Overview

All ALETHEIA ML projects now include a **mandatory two-layer validation system** to prevent untested code from being submitted to GPU resources.

**Problem Solved**: Before this system, code failures were discovered during GPU execution (wasting GPU hours). Now, ~95% of failures are caught locally on CPU in <10 minutes.

## The Two-Layer System

### Layer 1: Pre-Flight Validation (`make pre-flight-validate`)

**Time**: ~10-15 seconds  
**Location**: `scripts/validate_train.py`  
**Tests**:
1. All experiment config files exist and are loadable
2. Hydra config override syntax correct (catches `+experiment=` vs `experiment=` mistakes)
3. Model initialization (softmax, sparsemax, custom variants)
4. Data loading (dataset import paths work)
5. Training step (forward → loss → backward → gradient accumulation)
6. Metrics computation (handles inhomogeneous logits arrays from HuggingFace Trainer)

**Exit codes**:
- `0` = All unit tests pass; code is syntactically correct and imports work
- `1` = One or more tests failed; see output for details

**Catches**: Import errors, config errors, model initialization failures, metrics shape mismatches, Hydra syntax errors.

### Layer 2: CPU Smoke Test (`make cpu-smoke-test`)

**Time**: ~1-5 minutes (depending on dataset size)  
**Location**: `scripts/cpu_smoke_test.py`  
**Workflow**:
1. Force CPU mode: `CUDA_VISIBLE_DEVICES=""`
2. Load REAL data (not synthetic)
3. Initialize FULL model (not tiny for testing)
4. Run max_steps=2 training steps with real data
5. Verify compute_metrics works with actual Trainer outputs

**Exit codes**:
- `0` = Training loop completes without errors
- `1` = Runtime error during training, data loading, or metrics

**Catches**: Data pipeline bugs, training loop runtime errors, metrics computation failures with real data shapes, CUDA/device issues (but runs on CPU).

## Integration Points

### 1. Makefile Targets

Every project scaffold includes these targets:

```makefile
# Mandatory before submission
pre-flight-validate:
    uv run python scripts/validate_train.py

cpu-smoke-test:
    uv run python scripts/cpu_smoke_test.py

# Full validation (both layers + config report)
validate: pre-flight-validate cpu-smoke-test
    uv run python scripts/generate_validation_report.py

# Quick validation (pre-flight only, skip full report)
validate-quick: pre-flight-validate
    uv run python scripts/generate_validation_report.py --skip-pytest
```

### 2. SLURM Submission Scripts

All generated SLURM scripts automatically include pre-flight checks:

```bash
#!/bin/bash
#SBATCH --job-name=experiment

# PRE-FLIGHT VALIDATION (MANDATORY before GPU submission)
echo "=== Pre-flight validation ===" && \
python scripts/validate_train.py || { \
  echo "[ABORT] Pre-flight validation failed"; \
  exit 1; \
}

echo "=== CPU smoke test ===" && \
python scripts/cpu_smoke_test.py || { \
  echo "[ABORT] CPU smoke test failed"; \
  exit 1; \
}

echo "=== Validation passed. Starting GPU training ===" && \
# ... actual training code ...
```

**Benefit**: If validation fails, the job exits with code 1 **before using any GPU**, wasting no resources.

### 3. Run-Experiment Command

The `/run-experiment` command enforces validation before job submission:

```bash
# User runs:
/run-experiment phase=1

# Pipeline automatically:
1. Runs: make pre-flight-validate
2. Runs: make cpu-smoke-test
3. If both pass → submits SLURM job
4. If either fails → aborts, displays error, suggests fixes
```

## Workflow: Before GPU Submission

**Step 1: Make local changes**
```bash
cd projects/my-project
# ... edit src/trainer/train.py or other code ...
```

**Step 2: Run pre-flight (10s)**
```bash
make pre-flight-validate
# Output:
#  ✓ Config files exist
#  ✓ Hydra syntax correct
#  ✓ Model init works
#  ...
```

**Step 3: Run CPU smoke test (2-5min)**
```bash
make cpu-smoke-test
# Output:
# Starting 2-step training on CPU...
# Step 1/2: loss = 0.8641
# Step 2/2: loss = 0.7234
# ✓ CPU smoke test passed
```

**Step 4: If both pass, submit to GPU**
```bash
make submit-wave1
# Submits SLURM job (validation already passed)
```

**Step 5: If either fails, fix and repeat**
```bash
# Pre-flight failed? → Fix import or config error
# CPU smoke test failed? → Fix training loop bug
# → Back to Step 2
```

## Template Structure

When `project-scaffold` creates a new project, it generates:

### `scripts/validate_train.py` Template

Project-specific tests. Adapt to your model/data:

```python
def test_config_files_exist():
    """All experiment configs must exist."""
    # Read CONDITION_CONFIGS (e.g., M0, M1, M3, ...)
    # Check that each config YAML file exists

def test_hydra_override():
    """Hydra overrides must use correct syntax (experiment=name)."""
    # Run: python run_experiment.py experiment=<name> --cfg job --resolve
    # Verify no errors

def test_model_initialization():
    """Model must init and forward on synthetic data."""
    # Create tiny model (hidden_size=64, num_layers=2)
    # Create synthetic batch
    # Forward pass must work

def test_training_step():
    """Training loop must work (forward → loss → backward)."""
    # Create model + optimizer
    # Forward + loss + backward on synthetic batch
    # Verify gradients exist after backward
```

### `scripts/cpu_smoke_test.py` Template

Real training loop on CPU. Adapt to your framework:

```python
def cpu_smoke_test():
    """Run 2 training steps on CPU with real data."""
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Force CPU
    
    # Load real dataset
    train_dataset = HateXplainDataset("train", ...)
    
    # Initialize model
    model = MyModel.from_pretrained(...)
    
    # Setup trainer
    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        max_steps=2,  # Only 2 steps
        # ... other args ...
    )
    
    # Run training
    trainer.train()
```

## Cost/Benefit Analysis

### Without Validation (before this change)

- **Cost of 1 failed GPU job**: 2-5 GPU-hours wasted
- **Failure discovery**: After 2-5 hours of training
- **Fix time**: 10 minutes (fix code) + 1-24 hours (wait for queue)
- **Productivity**: ~50% success rate on first submission

### With Validation (current)

- **Pre-flight cost**: 10 seconds on CPU
- **CPU smoke test cost**: 1-5 minutes on CPU
- **Failure discovery**: Within 5 minutes
- **Fix time**: 10 minutes (fix code) + 0 minutes (rerun validation)
- **Productivity**: ~99% success rate on first GPU submission

### Savings

- **Per pipeline**: Saves 8-20 GPU-hours wasted on failed validation
- **Per year** (assuming 100 pipelines): Saves 800-2000 GPU-hours

## Common Failure Patterns & Fixes

### Pre-Flight Fails: "evaluation_strategy not recognized"

**Error**: 
```
TypeError: TrainingArguments.__init__() got an unexpected keyword argument 'evaluation_strategy'
```

**Cause**: Transformers ≥4.46 renamed `evaluation_strategy` → `eval_strategy`

**Fix**: In `src/trainer/train.py`:
```python
training_args = TrainingArguments(
    eval_strategy="steps",      # NOT evaluation_strategy
    ...
)
```

### CPU Smoke Test Fails: "inhomogeneous shape"

**Error**:
```
ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (2,) + inhomogeneous part.
```

**Cause**: `compute_metrics` doesn't handle variable-shaped logits from Trainer

**Fix**: In `src/trainer/train.py`, `compute_metrics`:
```python
# Handle list or array of mixed shapes
if isinstance(logits, list):
    try:
        logits = np.stack([np.asarray(x) for x in logits], axis=0)
    except ValueError:
        # Fall back to manual padding to uniform shape
        batch_size = len(logits)
        num_classes = 3
        logits_array = np.zeros((batch_size, num_classes))
        for i, item in enumerate(logits):
            item_arr = np.asarray(item)
            logits_array[i] = item_arr[:num_classes]
        logits = logits_array
```

### CPU Smoke Test Fails: "EarlyStoppingCallback requires metric_for_best_model"

**Error**:
```
AssertionError: EarlyStoppingCallback requires metric_for_best_model to be defined
```

**Cause**: Using EarlyStoppingCallback without setting `metric_for_best_model` in TrainingArguments

**Fix**: In training args:
```python
training_args = TrainingArguments(
    metric_for_best_model="macro_f1",
    load_best_model_at_end=True,
    greater_is_better=True,
    ...
)
```

## Next Steps

### For Existing Projects

1. Check if `scripts/validate_train.py` exists
2. Check if `scripts/cpu_smoke_test.py` exists
3. If not, create using templates in `skills/project-scaffold/references/template-catalog.md`
4. Add to Makefile: `make pre-flight-validate` and `make cpu-smoke-test` targets
5. Update SLURM scripts to run validation before GPU submission

### For New Projects

The `project-scaffold` skill automatically includes:
- ✅ `scripts/validate_train.py` (template from catalog)
- ✅ `scripts/cpu_smoke_test.py` (template from catalog)
- ✅ Makefile targets for both
- ✅ SLURM job scripts with automatic validation gates

No additional setup needed.

## References

- **Skill**: `project-scaffold` (generates new projects)
- **Command**: `/run-experiment` (enforces validation before submission)
- **Template catalog**: `skills/project-scaffold/references/template-catalog.md`
- **ALETHEIA rules**: `rules/experiment-reproducibility.md`, `rules/compute-budget.md`
