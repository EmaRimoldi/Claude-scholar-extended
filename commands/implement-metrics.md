---
name: implement-metrics
description: Implement core metrics, analytical references, comparison functions, and statistical tests from experiment-plan.md and hypotheses.md.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to experiment-plan.md)
    required: false
    default: experiment-plan.md
tags: [Development, Metrics, Statistics, ML]
---

# Implement Metrics Command

Implement the measurements that test the hypothesis.

## Goal

Activates the `measurement-implementation` skill to produce metric functions, analytical reference implementations, comparison code, and statistical tests.

## Usage

```bash
/implement-metrics                    # reads experiment-plan.md + hypotheses.md
/implement-metrics path/to/plan.md    # explicit plan file
```

## Workflow

1. Parse metrics section from experiment-plan.md and mathematical framework from hypotheses.md
2. Activate `measurement-implementation` skill
3. Write: src/metrics/{metric}.py with @register_metric classes
4. Implement analytical references if needed (OLS, GD, ridge, etc.)
5. Implement statistical tests appropriate for the experimental design

## Integration

- **Primary skill**: `measurement-implementation`
- **Prerequisite**: `project-scaffold`, `hypothesis-formulation` (mathematical framework section)
- **Feeds into**: `setup-validation` (measurement correctness checks), `experiment-runner`, `result-collector`
