---
name: experiment-design
description: This skill should be used when the user asks to "design experiments", "plan experiments", "how many runs do I need", "which baselines should I use", "plan ablations", "power analysis", "how many seeds", or after hypothesis formulation and before running any experiments. Pre-experiment planning with baselines, ablations, sample size, resource estimation, and execution ordering.
version: 0.1.0
tags: [Research, Experimental Design, Statistics, Planning]
---

# Experiment Design

Pre-experiment planning that translates hypotheses into a concrete, executable experiment plan with baselines, ablations, sample size, resource estimation, and execution ordering.

## Core Features

### 1. Baseline Selection

Select and justify comparison baselines:

- **Trivial baseline**: Random chance, majority class, or simplest heuristic
- **Standard baseline**: Most common method in the field
- **SOTA baseline**: Best published result on the benchmark
- **Ablation baseline**: Proposed method minus the key component
- **Fairness checklist**: Same preprocessing, splits, hyperparameter budget

### 2. Ablation Planning

Design ablation studies to isolate component contributions:

- **Component identification**: Which parts of the method are novel?
- **Ablation ordering**: Which components to remove first (most to least important)
- **Expected impact**: Predicted effect of each ablation (for hypothesis validation)
- **Interaction effects**: Which components might interact?

### 3. Sample Size & Seeds

Determine the number of runs needed:

- **Convention-based**: Community standard for the benchmark (e.g., "5 seeds is standard for BCI-IV-2a")
- **Power analysis** (optional, see caveat below): When prior effect size and variance are available
- **Cross-validation strategy**: k-fold, leave-one-out, stratified
- **Quick validation first**: Small-scale run before committing to full sweep

### 4. Resource Estimation

Estimate compute, storage, and time:

- **GPU-hours per run**: Based on model size, dataset size, training epochs
- **Total GPU-hours**: Runs x methods x seeds x folds
- **Storage**: Checkpoints, logs, embeddings
- **Wall time**: With available hardware

### 5. Execution Ordering

Prioritize experiments for efficient resource use:

- **Quick validation first**: 1 seed, subset of data -- stop-or-go gate
- **Core experiments second**: Full sweep on primary hypothesis
- **Ablations third**: Component analysis after main result confirmed
- **Extended experiments last**: Secondary hypotheses, additional datasets

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Hypotheses** -- from `hypothesis-formulation` output (`hypotheses.md`)
2. **Available resources** -- GPU hours, datasets, time constraints
3. **Target venue** (optional) -- for calibrating experiment thoroughness

### Mode B: Standalone (manual)

1. **Research goal** -- user describes what they want to test in free text
2. **Method description** -- user describes their approach
3. **Available resources** -- user specifies compute, data, time constraints
4. The skill reconstructs implicit hypotheses from the description before designing experiments, and notes: "No hypotheses.md found. I've inferred the following testable hypotheses from your description -- please confirm before proceeding."

When running in Mode B, state: "No hypotheses.md found. I've inferred the following testable hypotheses from your description -- please confirm before proceeding."

## Outputs

- `experiment-plan.md` containing:
  - **Baselines**: Selected baselines with justification for each
  - **Ablations**: Components to ablate, with justification for each
  - **Datasets & splits**: Which datasets, how to split, cross-validation strategy
  - **Metrics**: Primary metric, secondary metrics, with justification
  - **Sample size / runs**: Number of seeds, subjects, folds
  - **Power analysis** (optional, see caveat below)
  - **Resource estimate**: Estimated GPU hours, storage, wall time
  - **Execution order**: Which experiments to run first (quick validation before full sweep)
  - **Checkpoints**: Decision points (stop-or-go after each experiment block)
- Initial `experiment-state.json` (see Iteration Loop State section)

## Power Analysis: Optional with Explicit Caveat

Power analysis is included **only when the user provides or the skill can estimate**:
- Expected effect size (from prior work or pilot data)
- Variance estimate (from prior work or pilot data)
- Desired significance level and power

**When parameters are available**: Compute the recommended sample size and include the calculation.

**When parameters are NOT available** (the common case):
1. State: "Power analysis skipped -- no prior effect size or variance estimates available."
2. Use a **convention-based default** instead (e.g., "5 seeds is standard for this benchmark; 3 seeds minimum for a quick validation pass").
3. Flag this as a limitation: "Sample size is based on community convention, not statistical power. If the effect is small, more runs may be needed."

The skill must NEVER silently assume effect size parameters and present a power analysis as if it were well-grounded. Assumed parameters must be explicitly marked: "ASSUMED: effect size d=0.5 (medium, no prior data). This power analysis is illustrative only."

## Iteration Loop State

### `experiment-state.json`

On first run, create `experiment-state.json` in the project root:

```jsonc
{
  "$schema": "experiment-state-v1",
  "project": "<project-name>",
  "created": "<ISO-8601 timestamp>",
  "updated": "<ISO-8601 timestamp>",
  "iteration": 0,
  "max_iterations": 3,
  "active_hypothesis": {
    "id": "H1",
    "summary": "<one-line hypothesis summary>",
    "source_file": "hypotheses.md"
  },
  "status": "planned",
  "latest_analysis": null,
  "history": [],
  "resource_budget": {
    "total_gpu_hours": null,
    "used_gpu_hours": 0,
    "remaining_gpu_hours": null
  },
  "deadline": null
}
```

**Valid statuses**: `"planned"` | `"running"` | `"analyzing"` | `"diagnosing"` | `"revising"` | `"confirmed"` | `"abandoned"`

**File lifecycle**:
- **Created by**: `experiment-design` (on first run)
- **Updated by**: Each skill in the iteration loop updates `status`, `iteration`, and `active_hypothesis`
- **Read by**: `session-start.js` hook, all iteration loop skills
- **Archived when**: Status reaches `confirmed` or `abandoned` -- file is moved to `experiment-state.{timestamp}.json`

## When to Use

### Scenarios for This Skill

1. **After hypothesis formulation** -- have testable hypotheses, need a concrete experiment plan
2. **Before running experiments** -- want to estimate cost and prioritize runs
3. **Mid-project iteration** -- after hypothesis revision, need updated experiment plan
4. **Resource-constrained** -- need to maximize information from limited GPU budget

### Typical Workflow

```
hypothesis-formulation -> [experiment-design] -> execution -> results-analysis
                OR
user describes goal -> [experiment-design] -> execution -> results-analysis
```

**Output Files:**
- `experiment-plan.md` -- Full experiment plan
- `experiment-state.json` -- Iteration loop state file

## Integration with Other Systems

### Complete Research Workflow

```
research-ideation (Research initiation)
    |
novelty-assessment (Validate contribution)
    |
hypothesis-formulation (Testable predictions)
    |
experiment-design (Plan experiments)  <-- THIS SKILL
    |
Experiment execution (completed by user)
    |
results-analysis (Analyze results)
    |
failure-diagnosis / claim-evidence-bridge (Iterate or write)
```

### Data Flow

- **Depends on**: `hypothesis-formulation` (Mode A) OR user description (Mode B)
- **Feeds into**: Experiment execution, `obsidian-experiment-log` (log plan into Obsidian)
- **Hook activation**: Context-aware keyword trigger in `skill-forced-eval.js`
- **New command**: `/design-experiments` -- generate a full experiment plan from hypotheses
- **Obsidian integration**: If bound, writes `Experiments/{experiment-line}.md` with planned status
- **State file**: Creates `experiment-state.json` on first run

### Key Configuration

- **Quick validation gate**: Always plan a small-scale run before full sweep
- **Output format**: Markdown for easy editing and version control
- **Power analysis**: Optional, explicit caveat when parameters are assumed
- **Resource tracking**: GPU hours, storage, wall time estimated

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/power-analysis-guide.md`** -- Power Analysis Guide
  - When power analysis is appropriate
  - Required parameters and how to estimate them
  - Convention-based defaults by domain
  - Tools and formulas
  - Common mistakes

- **`references/baseline-selection.md`** -- Baseline Selection Guide
  - Baseline categories and when to use each
  - Fairness checklist
  - Finding published baselines
  - Handling missing baselines

- **`references/ablation-planning.md`** -- Ablation Study Planning Guide
  - Component identification
  - Ablation ordering strategies
  - Interaction effect detection
  - Reporting ablation results

### Example Files

Complete working examples:

- **`examples/example-experiment-plan.md`** -- Experiment Plan Example
  - Demonstrates complete experiment plan structure
  - Includes baselines, ablations, resource estimation, and execution order
