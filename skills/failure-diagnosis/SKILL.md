---
name: failure-diagnosis
description: This skill should be used when the user says "my experiment failed", "results are worse than expected", "model isn't learning", "why didn't this work", "underperforming", or when results-analysis shows the hypothesis was not confirmed. Systematic diagnosis of research-level experiment failures (not code bugs). Disambiguated from bug-detective by project context.
version: 0.1.0
tags: [Research, Diagnosis, Iteration, Experiment]
---

# Failure Diagnosis

Systematically diagnoses research-level experiment failures — why results are bad, not why code crashed. Produces ranked failure mode analysis with evidence for/against each cause and targeted diagnostic experiments.

## Disambiguation from `bug-detective`

This skill handles **research-level failures**: wrong hypothesis, bad hyperparameters, data issues, metric mismatch, unexpectedly strong baselines. `bug-detective` handles **code-level bugs**: tracebacks, exceptions, broken builds. The hook uses project context (existence of `hypotheses.md`, `experiment-plan.md`, or `experiment-state.json`) to route correctly.

## Core Features

### 1. Expected vs. Observed Gap Analysis

Structure the failure clearly:

- **What was predicted**: From the hypothesis (effect size, metric, threshold)
- **What was observed**: Actual results with confidence intervals
- **Gap characterization**: How far off? Is it directionally wrong or just smaller than expected?

### 2. Systematic Failure Mode Checklist

For every diagnosis, work through these modes in order:

1. **Hypothesis wrong**: The fundamental approach does not work
2. **Implementation bug**: The code does not do what was intended
3. **Hyperparameter issue**: The approach works but needs tuning
4. **Data issue**: Data quality, distribution shift, insufficient size, label noise
5. **Metric issue**: The metric does not capture what we care about
6. **Baseline stronger than expected**: The bar was higher than anticipated

### 3. Evidence Assessment

For each failure mode:

- **Evidence for**: What observations support this being the cause?
- **Evidence against**: What observations argue against it?
- **Likelihood**: LIKELY / POSSIBLE / UNLIKELY
- **Cost to verify**: How expensive is the diagnostic experiment?

### 4. Diagnostic Experiments

Propose small, targeted tests to isolate the cause:

- Each test should take <10% of the original experiment compute
- Prioritize by: (likelihood of cause) x (1 / cost to verify)
- Include expected outcomes for each diagnostic

### 5. State Update

Update `experiment-state.json` status to `"diagnosing"` and record the latest analysis reference.

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Experiment results** -- from `results-analysis` output (`analysis-report.md`)
2. **Original hypothesis** -- from `hypotheses.md`
3. **Experiment plan** -- from `experiment-plan.md`
4. **Code and configs** -- for implementation verification

### Mode B: Standalone (manual)

1. **What you expected** -- user describes expected outcome
2. **What you observed** -- user describes actual outcome (metrics, behaviors)
3. **What you tried** -- user describes the method and setup
4. The skill structures the diagnosis around the expected/observed gap without requiring formal hypothesis documents

When running in Mode B, state: "No hypotheses.md found. Working from your description of expected vs. observed outcomes."

## Outputs

- `failure-diagnosis.md` containing:
  - Observed vs. expected results
  - Systematic failure mode analysis (ranked by likelihood)
  - Evidence for/against each failure mode
  - Proposed diagnostic experiments (small, targeted tests)
  - Recommended next steps (priority order)
- Updates `experiment-state.json` status to `"diagnosing"`

## When to Use

### Scenarios for This Skill

1. **After experiment analysis** -- results do not confirm the hypothesis
2. **During training** -- model is not learning as expected (loss plateau, divergence)
3. **After baseline comparison** -- proposed method underperforms or ties with baseline
4. **Mid-iteration** -- previous fix did not fully resolve the issue

### Typical Workflow

```
results-analysis -> [failure-diagnosis] -> hypothesis-revision -> experiment-design (loop)
                OR
user describes failure -> [failure-diagnosis] -> next steps
```

**Output Files:**
- `failure-diagnosis.md` -- Ranked failure mode analysis with diagnostic experiments

## Integration with Other Systems

### Complete Iteration Loop

```
results-analysis (Results don't confirm hypothesis)
    |
failure-diagnosis (Why did it fail?)  <-- THIS SKILL
    |
hypothesis-revision (What to do next)
    |
experiment-design (Updated plan)
    |
[execution by researcher] (Loop back)
```

### Data Flow

- **Depends on**: `results-analysis` (Mode A) OR user description (Mode B)
- **Feeds into**: `hypothesis-revision` (diagnosis informs revision strategy)
- **Hook activation**: Context-aware conditional trigger in `skill-forced-eval.js` (requires research project files)
- **No new command**: Activated via skill trigger or manually
- **State update**: Sets `experiment-state.json` status to `"diagnosing"`

### Key Configuration

- **Failure modes**: Fixed 6-item checklist (hypothesis, implementation, hyperparameters, data, metric, baseline)
- **Diagnostic experiments**: Must be <10% of original compute cost
- **Output format**: Markdown for easy review and discussion

## Additional Resources

### Reference Files

- **`references/failure-taxonomy.md`** -- Failure Taxonomy
  - Detailed description of each failure mode
  - Diagnostic signals for each mode
  - Common patterns and red flags

- **`references/diagnostic-experiments.md`** -- Diagnostic Experiment Design
  - How to design minimal diagnostic experiments
  - Cost-benefit prioritization
  - Sanity checks and control experiments

### Example Files

- **`examples/example-failure-diagnosis.md`** -- Failure Diagnosis Example
  - Demonstrates complete diagnosis workflow
  - Shows evidence assessment and diagnostic experiment proposals
