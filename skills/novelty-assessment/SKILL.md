---
name: novelty-assessment
description: This skill should be used when the user asks to "assess novelty", "compare my contribution against prior work", "check if this is incremental", "validate research novelty", or after completing a literature review and before committing to experiments. Compares proposed contributions against closest prior works and flags incremental contributions.
version: 0.1.0
tags: [Research, Validation, Novelty, Literature]
---

# Novelty Assessment

Compares a proposed research contribution against the closest prior works to assess novelty level, identify overlap, and suggest differentiation strategies.

## Core Features

### 1. Related Work Identification

Identify the 3-5 closest prior works:

- **From literature review**: Extract closest works from `literature-review.md` if available
- **Via WebSearch**: Search for closely related works when no literature review exists
- **User-provided**: Accept user's list of related papers (titles, abstracts, URLs)

### 2. Contribution Comparison Matrix

For each related work, create a structured comparison:

- **What they do**: Core methodology and contributions
- **What you add**: The delta between their work and the proposal
- **Overlap assessment**: None / Low / Medium / High
- **Delta type**: Method variant / Complementary / Architecture extension / Direct overlap

### 3. Novelty Classification

Classify the proposed contribution:

- **Novel method**: Fundamentally new approach
- **Novel application**: Known method applied to new domain
- **Novel analysis**: New theoretical or empirical insight about existing methods
- **Scale improvement**: Known approach at significantly larger scale
- **Incremental**: Small delta over existing work

### 4. Venue Calibration

Assess whether the contribution meets the novelty bar for the target venue:

- **Top venues** (NeurIPS, ICML, ICLR): Require novel method/analysis or surprising empirical findings
- **Second-tier venues**: Accept novel applications and significant engineering contributions
- **Workshops**: Accept incremental work with interesting preliminary results

### 5. Differentiation Suggestions

When novelty is weak, suggest concrete strategies:

- Add a theoretical contribution
- Target a harder or different evaluation setting
- Demonstrate surprising scaling behavior
- Combine with a complementary direction

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Literature review output** -- from `research-ideation` or `literature-reviewer` agent (`literature-review.md`)
2. **Proposed contribution statement** -- what the researcher claims to contribute
3. **Target venue** (optional) -- for calibrating novelty expectations

### Mode B: Standalone (manual)

1. **Proposed contribution statement** -- user describes their contribution in free text
2. **Related works** -- user provides a list of 3-10 related papers (titles, abstracts, or URLs), OR the skill runs a WebSearch to find the closest related works
3. **Target venue** (optional)

When running in Mode B, state: "No literature review file found. Using user-provided related works and supplementing with WebSearch."

## Outputs

- `novelty-assessment.md` containing:
  - Top 5 closest related works with structured comparison
  - Contribution comparison matrix (what each related work does vs. what proposal adds)
  - Novelty classification: novel method / novel application / novel analysis / scale improvement / incremental
  - Venue calibration: is the delta sufficient for the target venue?
  - Differentiation suggestions if novelty is weak

## When to Use

### Scenarios for This Skill

1. **After literature review** -- have a clear picture of the field, need to validate contribution novelty
2. **Before committing to experiments** -- want to ensure the research direction is worth pursuing
3. **During paper writing** -- need to sharpen the contribution statement against related work
4. **After competitive check** -- found overlapping work, need to reassess novelty

### Typical Workflow

```
research-ideation -> [novelty-assessment] -> hypothesis-formulation -> experiment-design
                        OR
user describes contribution -> [novelty-assessment] -> next steps
```

**Output Files:**
- `novelty-assessment.md` -- Structured novelty evaluation

## Integration with Other Systems

### Complete Research Workflow

```
research-ideation (Research initiation)
    |
novelty-assessment (Validate contribution)  <-- THIS SKILL
    |
hypothesis-formulation (Testable predictions)
    |
experiment-design (Plan experiments)
    |
Experiment execution (completed by user)
```

### Data Flow

- **Depends on**: `research-ideation` (Mode A) OR user-provided context (Mode B)
- **Feeds into**: `hypothesis-formulation` (validated contribution guides hypothesis design)
- **Hook activation**: Keyword trigger in `skill-forced-eval.js`
- **No new command**: Triggered as part of `/research-init` extended workflow or manually

### Key Configuration

- **Comparison matrix**: Structured markdown table
- **Output format**: Markdown for easy editing and version control
- **WebSearch**: Used in Mode B to find related works if user doesn't provide them

## Additional Resources

### Reference Files

- **`references/comparison-methodology.md`** -- Comparison Methodology Guide
  - How to identify the closest related works
  - Structured comparison framework
  - Venue-specific novelty bars
  - Common novelty pitfalls (method combination ≠ novelty, benchmarking ≠ contribution)

### Example Files

- **`examples/example-novelty-assessment.md`** -- Novelty Assessment Example
  - Demonstrates complete assessment with comparison matrix
  - Shows venue calibration and differentiation suggestions
