---
name: validate-setup
description: Run pre-flight validation checklist before committing to full experiment sweep. Checks data, model, metrics, ablations, baselines, and runs end-to-end smoke test.
tags: [Research, Validation, Testing]
---

# Validate Setup Command

Verify the experiment pipeline before committing GPU hours.

## Goal

Activates the `setup-validation` skill to run a structured pre-flight checklist (6 categories, ~20 checks) and produce a validation report with pass/fail status and smoke test timing.

## Usage

```bash
/validate-setup
```

## Workflow

1. Activate `setup-validation` skill
2. Run checks: data integrity, model loading, measurement correctness, ablation verification, baseline replication, end-to-end smoke test
3. Write: validation-report.md with pass/fail per check and timing data
4. Report overall verdict: READY or NOT READY with blocking issues

## Integration

- **Primary skill**: `setup-validation`
- **Prerequisite**: `project-scaffold`, `experiment-data-builder`, `model-setup`, `measurement-implementation`
- **Feeds into**: `compute-planner` (uses smoke test timing), `experiment-runner` (green light)
