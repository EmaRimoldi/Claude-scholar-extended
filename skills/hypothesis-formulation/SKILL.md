---
name: hypothesis-formulation
description: This skill should be used when the user asks to "formulate hypotheses", "define success criteria", "what should I test", "make this testable", "falsifiable", or after completing novelty assessment and before designing experiments. Converts research gaps into falsifiable hypotheses with success/failure criteria.
version: 0.1.0
tags: [Research, Hypothesis, Experimental Design, Validation]
---

# Hypothesis Formulation

Converts research questions and gaps into falsifiable, testable hypotheses with explicit success/failure criteria, null hypotheses, and fallback strategies.

## Core Features

### 1. Hypothesis Construction

Transform vague research ideas into structured, testable hypotheses:

- **Primary hypothesis (H1)**: The core prediction with expected effect size, metric, baseline, and thresholds
- **Secondary hypotheses (H2, H3)**: Supporting predictions that strengthen the contribution
- **Null hypothesis (H0)**: Explicitly stated for each testable hypothesis
- **Falsifiability check**: Every hypothesis must have a concrete way to be disproven

### Minimum Count & Scoring Format

Generate minimum 5 hypotheses per invocation. If fewer than 5 novel hypotheses can be identified, state why and document what was considered and rejected.

Score each hypothesis on 5 dimensions with mandatory justification:
- Novelty: [X/5] — [one sentence explaining this score]
- Feasibility: [X/5] — [one sentence explaining this score]
- Impact: [X/5] — [one sentence explaining this score]
- Testability: [X/5] — [one sentence explaining this score]
- Specificity: [X/5] — [one sentence explaining this score]

### 2. Success/Failure Criteria

Define quantitative thresholds for each hypothesis:

- **Success threshold**: Minimum effect size + statistical significance level
- **Failure threshold**: Below what result do we reject?
- **Ambiguous zone**: What constitutes an inconclusive result?
- **Metric selection**: Primary metric with justification, secondary metrics

### 3. Competing Explanations

For each hypothesis, document:

**Competing explanations**: List known alternative hypotheses or explanations from the literature that could account for the same observations. Note which papers propose them. This surfaces known controversies and alternative interpretations early.

### 4. Risk Assessment & Fallback Strategy

For each primary hypothesis:

- **Fallback hypotheses**: What to test if H1 fails (H1', H1'')
- **Abandon criteria**: When to stop pursuing this direction entirely
- **Resource estimate**: Rough compute/time cost to test each hypothesis
- **Prior evidence**: What existing work supports the prediction?

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Research questions** -- from `research-ideation` output (`research-proposal.md`)
2. **Novelty assessment** -- from `novelty-assessment` output (optional but recommended)
3. **Domain context** -- the research field and available resources

### Mode B: Standalone (manual)

1. **Research idea** -- user describes their research idea or question in free text
2. **Domain context** -- user provides: field, available datasets, available compute, target venue
3. The skill asks clarifying questions if the idea is too vague to formulate testable hypotheses

When running in Mode B, state: "No research-proposal.md or novelty-assessment.md found. Formulating hypotheses from user-provided description."

## Outputs

### Output Files

1. `$PROJECT_DIR/docs/hypotheses.md` — Full hypothesis log with all details
2. `$PROJECT_DIR/docs/ranked-hypotheses.md` — Top-5 hypotheses ranked by combined score (Novelty + Feasibility + Impact + Testability + Specificity), with one-line summary each. This serves as a quick reference for experiment prioritization.

### hypotheses.md content

- `hypotheses.md` containing:
  - Primary hypothesis (H1) with: prediction, expected effect size, metric, comparison baseline, success threshold
  - Secondary hypotheses (H2, H3) if applicable
  - Null hypotheses (H0) explicitly stated
  - Success/failure criteria for each hypothesis
  - Minimum experiment specification to test each hypothesis
  - Risk assessment: what if H1 fails? (fallback hypotheses)
  - **Mathematical framework** section: what analytical formulas, derivations, or reference algorithms are needed to compute the predictions. If the hypothesis compares model behavior to a known algorithm (e.g., gradient descent, Bayes-optimal, kernel regression), identify the formula here. If the hypothesis is purely empirical (method A vs. method B), note "no analytical reference needed." This section feeds directly into the `measurement-implementation` skill.

## When to Use

### Scenarios for This Skill

1. **After research ideation** -- have research questions but no testable hypotheses yet
2. **After novelty assessment** -- validated contribution needs concrete predictions
3. **Before experiment design** -- need structured hypotheses to design experiments for
4. **Mid-project pivot** -- need to reformulate hypotheses after initial results

### Typical Workflow

```
research-ideation -> novelty-assessment -> [hypothesis-formulation] -> experiment-design
                        OR
user describes idea -> [hypothesis-formulation] -> experiment-design
```

**Output Files:**
- `hypotheses.md` -- Structured testable hypotheses with criteria

## Integration with Other Systems

### Complete Research Workflow

```
research-ideation (Research initiation)
    |
novelty-assessment (Validate contribution)
    |
hypothesis-formulation (Testable predictions)  <-- THIS SKILL
    |
experiment-design (Plan experiments)
    |
Experiment execution (completed by user)
    |
results-analysis (Analyze results)
    |
failure-diagnosis / claim-evidence-bridge (Iterate or write)
```

### Data Flow

- **Depends on**: `research-ideation` (Mode A) OR user description (Mode B)
- **Feeds into**: `experiment-design` (hypotheses define what experiments to run)
- **Hook activation**: Context-aware keyword trigger in `skill-forced-eval.js`
- **No new command**: Part of the extended ideation-to-design pipeline

### Key Configuration

- **Hypothesis format**: Structured markdown with explicit fields
- **Output format**: Markdown for easy editing and version control
- **Null hypothesis**: Always explicitly stated
- **Fallback strategy**: Required for every primary hypothesis

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/hypothesis-construction.md`** -- Hypothesis Construction Guide
  - SMART hypothesis framework
  - From research question to testable prediction
  - Effect size estimation strategies
  - Metric selection methodology
  - Common pitfalls in hypothesis formulation

- **`references/success-criteria-guide.md`** -- Success Criteria Definition Guide
  - Setting quantitative thresholds
  - Statistical significance requirements
  - Baseline selection for comparisons
  - Handling ambiguous results
  - Abandon criteria design

### Example Files

Complete working examples:

- **`examples/example-hypotheses.md`** -- Hypothesis Formulation Example
  - Demonstrates complete hypothesis structure
  - Includes primary, secondary, and null hypotheses
  - Shows success/failure criteria and fallback strategy
