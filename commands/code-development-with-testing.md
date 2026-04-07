---
name: code-development-with-testing
description: Automatic test-driven code development for experiments. Writes code (datasets, models, metrics), automatically runs validation tests, diagnoses failures with Opus extended thinking, fixes code, and retests in a loop until all tests pass.
tags: [Development, Testing, TDD, Automation]
---

# Code Development with Testing Command

Automates: **write code → test → diagnose failures with Opus → fix → retest → loop until passing**.

Eliminates manual iteration by running all tests on CPU and using Opus extended thinking to automatically diagnose and fix failures.

## Goal

Activates `code-development-with-testing` skill to:

1. **Write code** for all experiment components (datasets, models, metrics)
2. **Run tests**: pre-flight (10-15s) + CPU smoke (1-5min)
3. **If tests fail**: Diagnose with Opus extended thinking → propose fix → apply → retest
4. **Loop** until passing (max 5 iterations per component)
5. **Report**: Ready-to-train codebase or failure diagnostics

## Usage

```bash
/code-development-with-testing                    # uses experiment-plan.md in cwd
/code-development-with-testing path/to/plan.md   # explicit plan file
```

## Workflow

Write → Test (pre-flight + cpu-smoke) → PASS?
```
YES → Next component (data → model → metrics)
 NO → [OPUS Extended Thinking]
      ├─ Diagnose root cause
      ├─ Propose fix
      └─ Retest (loop 5x max)
```

All three components must pass before returning success.

## Automatic Diagnosis with Opus

When tests fail, uses **Opus with extended thinking** to:

- **Analyze error**: Root cause (ImportError, shape mismatch, NaN, etc.)
- **Trace execution**: Code path from error to source
- **Propose fix**: Specific code changes with explanation
- **Rate confidence**: HIGH / MEDIUM / LOW likelihood of success
- **Provide rationale**: Why this fix addresses root cause

## Three-Component Code Generation

In order (dependencies matter):

1. **Data Builder** — Dataset loaders, validation methods
2. **Model Setup** — Model classes, forward/backward
3. **Metrics** — Metric functions, various input shapes

Each component:
- Generates Python classes + Hydra config YAML
- Runs pre-flight validation (30s timeout)
- Runs CPU smoke test (10min timeout, max 5 iterations)
- Moves to next on success, aborts on 5 failed iterations

## Output

**Success**:
```
✅ All components tested and passing
Ready to train: python scripts/run_experiment_autonomously.py --phase 2
```

**Failure** (after 5 iterations):
```
❌ Code generation failed (component X, iteration 5)
Attempted fixes: [list of 5 fixes tried]
Recommendation: Review experiment-plan.md specification
Diagnostics: logs/code_dev_failed_iteration_5.log
```

## Key Benefits

✅ No manual debugging on GPU (all tests on CPU)
✅ Automatic error recovery (Opus fixes common issues)
✅ Complete audit trail (all iterations logged)
✅ Validated codebase (no untested code to GPU)
✅ Faster iteration (minutes, not hours/days)

## Integration

- **Prerequisite**: `experiment-plan.md` (completed)
- **Prerequisite**: `project-scaffold` output (directory structure)
- **Feeds into**: `experiment-runner` (GPU training pipeline)
- **Model**: Always Opus with extended thinking (complex debugging)

