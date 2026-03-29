---
name: setup-validation
description: This skill should be used when the user asks to "validate the setup", "run sanity checks", "check if the pipeline works", "replicate baseline", "smoke test", or before committing to a full experiment sweep. Structured pre-flight checklist verifying data, model, measurements, ablations, baselines, and end-to-end correctness.
version: 0.1.0
tags: [Research, Validation, Testing, Experiment]
---

# Setup Validation

Structured pre-flight checklist that verifies the entire experiment pipeline produces correct results before committing to the full sweep. Catches data bugs, model loading errors, measurement mistakes, ablation failures, and baseline mismatches — all cheaper to fix now than after 200 GPU-hours.

## Core Features

### 1. Data Integrity Checks

Verify each dataset produces correct output:

- **Shape check**: output tensors have expected dimensions (batch, sequence_length, features)
- **Distribution check**: sample statistics match specification (mean, variance, range)
- **Label check**: manually verify 3-5 samples against hand computation
- **Sequence format check**: ICL episodes are correctly interleaved [x1,y1,...,xk,yk,x_query]
- **Reproducibility check**: same seed produces identical data across two runs
- **No data leakage**: training and evaluation splits share no sequences

### 2. Model Loading Verification

Verify models load correctly and produce expected behavior:

- **Output check**: model produces non-trivial output on a known input (not all zeros, not NaN)
- **Shape check**: output shape matches expected (batch, vocab_size or output_dim)
- **Published check**: if model card provides example output, verify match within tolerance
- **Hook check**: attached hooks extract tensors of expected shape
- **Device check**: model and data are on the same device (no silent CPU/GPU mismatch)
- **Dtype check**: model precision matches expectation (fp32, fp16, bf16)

### 3. Measurement Correctness

Verify core metrics produce known-correct results on trivial cases:

- **Identity check**: similarity between identical vectors = 1.0
- **Orthogonal check**: similarity between orthogonal vectors = 0.0
- **Known-answer check**: analytical reference on a problem with known solution matches implementation
- **Scale check**: metric is invariant to input scale (if it should be)
- **Numerical stability**: metric handles edge cases (zero vectors, very large values, near-singular matrices)

### 4. Ablation Verification

Verify ablation operations work correctly:

- **Effect check**: ablated component's contribution is confirmed to be zero (output of that component is zero-tensor)
- **Impact check**: model output changes after ablation (ablation has an effect)
- **Restoration check**: after reversible ablation, output matches pre-ablation output exactly (bitwise)
- **Specificity check**: ablating component A does not accidentally ablate component B

### 5. Baseline Replication

If the experiment extends prior work, verify the pipeline reproduces published results:

- **Published value**: record the number from the paper
- **Reproduced value**: run the pipeline on the same configuration
- **Tolerance**: define acceptable deviation (typically ±1% for classification, ±0.05 for similarity metrics)
- **Pass/fail**: within tolerance = pass; outside = investigate before proceeding
- If no published baseline to replicate, run a trivial baseline (random, majority class) and verify it produces the expected floor

### 6. Compute Environment Check

Before running the smoke test, verify the execution environment provides GPU access:

- **GPU availability**: Run `torch.cuda.is_available()`. If `False`:
  - "BLOCKING: No GPU detected. You are likely on a login node. Smoke test timing on CPU is invalid for GPU wall-time estimation. Run validation from a GPU-equipped session: `salloc --gres=gpu:1 --time=01:00:00 --partition=<partition>`"
  - Do NOT proceed with timing-dependent checks until GPU is available.
- **GPU model**: Record `torch.cuda.get_device_name(0)` in the validation report. This is needed by `compute-planner` to match wall-time estimates to hardware.
- **CUDA version**: Record `torch.version.cuda` for reproducibility.
- **Device consistency**: Verify model and data are placed on the same device (catch silent CPU fallback).

If the user explicitly requests a CPU-only validation (e.g., for testing pipeline logic without GPU), allow it but mark timing data as: "CPU-only — not valid for GPU wall-time estimation" in the validation report.

### 7. ML-Specific Validation (mandatory)

- [ ] **Gradient check**: Run numerical gradient verification on 1 batch — relative error < 1e-5
- [ ] **Numerical stability**: Test with edge-case inputs (all zeros, very large values, empty sequences) — no NaN/Inf
- [ ] **Fair baseline enforcement**: Verify all conditions use same hyperparameter budget, same data splits, same preprocessing
- [ ] **Minimum test count**: At least 10 unit tests covering: data loading, model forward pass, metric computation, freezing/modification logic, training step
- [ ] **Single-step training test**: Initialize Trainer with ALL arguments, run 1 forward + 1 backward pass, run 1 eval step — must complete without error
- [ ] **Determinism check**: Run 2 training steps with same seed — outputs must be identical

### 8. End-to-End Smoke Test

Run the complete pipeline on a single configuration:

- 1 model, 1 dataset, 1 seed, no ablations
- Verify: data loads → model runs → metric computes → result saves → output has expected format
- Time this run — it provides the per-run estimate for `compute-planner` (only valid if Section 6 GPU check passed)
- Verify output directory structure matches what `result-collector` expects

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Scaffolded project** -- from `project-scaffold`
2. **Implemented data** -- from `experiment-data-builder`
3. **Configured model** -- from `model-setup`
4. **Implemented metrics** -- from `measurement-implementation`
5. **Experiment plan** -- from `experiment-plan.md` (for baseline expectations)

### Mode B: Standalone (manual)

1. **Project directory** -- user points to an existing experiment project
2. The skill runs the validation checklist against whatever code exists

When running in Mode B, state: "Running validation against existing project. Checks will be skipped for unimplemented components."

## Outputs

- `validation-report.md` containing:
  - Pass/fail status for each check (7 categories, ~23 individual checks)
  - For failures: error message, expected vs. observed, suggested fix
  - Smoke test timing (used by `compute-planner` for per-run estimates)
  - Overall verdict: READY / NOT READY with blocking issues listed
- Timing data for `compute-planner`

## When to Use

### Scenarios for This Skill

1. **Before full sweep** -- all code is written, need to verify correctness before committing GPU hours
2. **After modifying pipeline** -- changed data, model, or metric code and need to re-verify
3. **After hypothesis revision** -- new iteration may have changed components
4. **Debugging failures** -- experiment produced unexpected results, need to identify where the pipeline broke

### Typical Workflow

```
project-scaffold + data-builder + model-setup + measurement-implementation
    |
[setup-validation]  <-- THIS SKILL
    |
    ├── all checks pass → compute-planner → experiment-runner
    └── any check fails → fix → re-validate
```

**Output Files:**
- `validation-report.md` -- Structured pass/fail checklist with timing data

## Integration with Other Systems

### Pipeline Position

```
experiment-data-builder ──┐
model-setup ──────────────┤
measurement-implementation┘
         |
   setup-validation  <-- THIS SKILL
         |
   compute-planner (uses smoke test timing)
         |
   experiment-runner
```

### Data Flow

- **Depends on**: `project-scaffold`, `experiment-data-builder`, `model-setup`, `measurement-implementation` (all must be complete)
- **Feeds into**: `compute-planner` (provides per-run timing estimate), `experiment-runner` (green light to proceed)
- **Hook activation**: Keyword trigger in `skill-forced-eval.js`
- **New command**: `/validate-setup`

### Key Configuration

- **Checks**: 7 categories, ~23 individual checks
- **Baseline tolerance**: configurable per metric (default ±1% for accuracy, ±0.05 for similarity)
- **Smoke test**: always runs 1 full configuration as the final check
- **Output format**: Markdown checklist for human review

## Additional Resources

### Reference Files

- **`references/validation-protocol.md`** -- Validation Protocol
  - Complete checklist with pass/fail criteria for each check
  - How to interpret failures and debug common issues
  - When to skip checks (e.g., no published baseline to replicate)
  - Timing measurement methodology for compute planning

### Example Files

- **`examples/example-validation-report.md`** -- Validation Report Example
  - Shows a complete validation report with mixed pass/fail results
  - Demonstrates failure reporting with suggested fixes
  - Includes smoke test timing data
