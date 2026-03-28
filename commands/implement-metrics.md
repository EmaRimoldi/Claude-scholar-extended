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

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Metric implementations → `$PROJECT_DIR/src/`
- Test files → `$PROJECT_DIR/tests/`

Never write metric files to the repository root.

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

## Metric Coverage Validation

Before finalizing metric implementations, cross-reference every key term in the research question (from `hypotheses.md`) with the implemented metrics. **BLOCK and warn** if any research question keyword has zero corresponding metric.

### Keyword-to-Metric Requirements

| Research Question Keyword | Required Metrics |
|---------------------------|-----------------|
| **faithfulness** | comprehensiveness (confidence drop when rationale removed), sufficiency (confidence using only rationale), attention-IG correlation |
| **plausibility** | token-level F1 vs human rationales, AUPRC |
| **accuracy** | macro-F1, per-class F1, accuracy |
| **sparsity** | attention entropy, sparsity ratio (% zero weights) |

### Procedure

1. Load `hypotheses.md` and extract all research questions
2. Tokenize each research question into key terms
3. For each key term, look up the keyword-to-metric table above
4. Verify that every required metric has a corresponding `@register_metric` implementation in `src/metrics/`
5. If any required metric is missing, **BLOCK** the workflow and emit a clear warning listing the missing metrics and the research question keyword that triggered them
6. Produce a coverage matrix showing: keyword → required metrics → implemented (yes/no)

### Faithfulness Metrics in the Catalog

The following faithfulness metrics are part of the known metric catalog and must be available for registration:

- **Comprehensiveness**: Measures the drop in model confidence when the rationale is removed from the input. Higher drop = more faithful rationale.
- **Sufficiency**: Measures model confidence when only the rationale is provided as input. Higher confidence = rationale is sufficient to reproduce the prediction.
- **AOPC (Area Over the Perturbation Curve)**: Aggregates comprehensiveness over incremental token removals, providing a curve-level faithfulness score.

## Integration

- **Primary skill**: `measurement-implementation`
- **Prerequisite**: `project-scaffold`, `hypothesis-formulation` (mathematical framework section)
- **Feeds into**: `setup-validation` (measurement correctness checks), `experiment-runner`, `result-collector`
