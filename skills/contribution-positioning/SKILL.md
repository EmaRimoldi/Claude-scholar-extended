---
name: contribution-positioning
description: This skill should be used when the user asks to "position my contribution", "differentiate from prior work", "write related work", "anticipate reviewer objections", "how is this different from X", "articulate novelty", or after novelty assessment confirms sufficient novelty and before paper writing. Produces a differentiation matrix, contribution statement, reviewer objection anticipation, and related work paragraph drafts.
version: 0.1.0
tags: [Research, Writing, Positioning, Differentiation, Reviewer Objection]
---

# Contribution Positioning

Articulates how a research contribution advances beyond specific prior works. Produces a differentiation matrix, publication-ready contribution statement, anticipated reviewer objections with prepared responses, and related work paragraph drafts. Extends novelty-assessment output without duplicating it: novelty-assessment asks "is this novel enough?"; contribution-positioning asks "how do I articulate this novelty to reviewers?"

## Core Features

### 1. Closest Work Selection

Select the 3-5 most similar papers for detailed positioning:

- **Mode A (pipeline)**: Start from the novelty-assessment.md comparison matrix. Refine the selection by:
  - Keeping all papers with Medium or High overlap
  - Adding any papers the user identifies as "the paper reviewers will compare us to"
  - Removing papers with Low overlap that are not positioning-critical
- **Mode B (standalone)**: Use WebSearch + user input to identify the closest works
  - Ask the user: "Which 3-5 papers are you most worried reviewers will compare your work to?"
  - Supplement with WebSearch if fewer than 3 papers are provided
- **Selection criteria**: Prioritize papers that (a) share the most method overlap, (b) are published at the target venue, (c) are recent (last 2-3 years), (d) come from prolific groups whose reviewers are likely in the pool

### 2. Differentiation Matrix

For each closest work, produce a structured comparison along 5 dimensions:

| Dimension | Description |
|---|---|
| **Research Question** | What question does each paper ask? Where do the questions diverge? |
| **Method** | What is the core technical approach? What specific component differs? |
| **Models / Data** | What models, datasets, or domains are used? Where is coverage different? |
| **Key Findings** | What are the main results? What does each paper show that the other does not? |
| **Limitation Addressed** | What acknowledged limitation of the prior work does our contribution address? |

Go beyond novelty-assessment's binary comparison (what they do / what you add) to articulate *how* and *why* the contribution advances beyond each specific paper. For each dimension, write a 1-2 sentence comparative statement, not just labels.

### 3. Contribution Statement

Draft a 3-4 sentence contribution statement suitable for the end of the introduction:

- **Formula**: "While [prior work] showed [X], our work [Y], revealing [Z]."
- **"So what?" test**: A reader who knows the field should understand what the community gains from this work after reading the statement
- **Avoid**: Listing method components without connecting them to outcomes ("We propose A, B, and C" is not a contribution statement)
- **Include**: The key delta over the closest work, the main finding, and why it matters
- **Draft multiple variants**: Provide 2-3 candidate statements with different emphasis (method-first, finding-first, problem-first) so the user can choose

### 4. Reviewer Objection Anticipation

For each differentiator in the matrix, identify the most likely reviewer objection and prepare a response:

**Common objection patterns**:

| Objection | Trigger | Response Strategy |
|---|---|---|
| "Incremental over [X]" | Small method delta | Emphasize the qualitative difference in findings, not just method |
| "Limited evaluation" | Few datasets or metrics | Justify dataset choice, discuss generalization evidence |
| "Unclear novelty vs. [Y]" | Overlapping contribution | Produce a precise side-by-side table showing the delta |
| "Missing comparison with [Z]" | Absent baseline | Either add the baseline or explain why the comparison is not applicable |
| "Concurrent work" | arXiv overlap | Articulate independent development, complementary findings |
| "Engineering trick, not contribution" | Method perceived as simple | Reframe around the insight or finding the trick enables |
| "Overclaiming" | Strong language, moderate evidence | Propose language calibration (see claim-evidence-bridge) |

For each objection-response pair, draft a 2-3 sentence rebuttal paragraph that can be directly used in a reviewer response.

### 5. Related Work Paragraph Drafts

For each closest work, draft a 2-3 sentence paragraph suitable for the related work section:

- **Structure**: What the paper does -> How our work relates -> What our work adds or changes
- **Tone**: Respectful, precise, factual. Never disparage prior work; frame limitations as "opportunities" or "complementary perspectives"
- **Positioning language**: Use positioning verbs (extends, generalizes, complements, addresses, builds upon) rather than competitive verbs (outperforms, surpasses, beats)
- **Citation style**: Use placeholder citations `[Author et al., YEAR]` for the user to fill in

## Input Modes

### Mode A: Pipeline (from novelty-assessment)

1. **Novelty assessment output** -- from `novelty-assessment` skill (`novelty-assessment.md` comparison matrix, novelty classification, differentiation suggestions)
2. **Analysis report** (optional) -- from `results-analysis` output (`analysis-report.md`) to ground the contribution statement in actual results
3. **Target venue** (optional) -- for calibrating positioning language and reviewer expectations

State: "Using novelty-assessment.md as starting point for positioning."

When `analysis-report.md` is also available, ground the contribution statement in actual experimental findings rather than planned contributions.

### Mode B: Standalone (manual)

1. **Contribution description** -- user describes their contribution in free text
2. **Related papers** -- user provides 3-5 most similar papers (titles, abstracts, URLs, or PDFs)
3. **Target venue** (optional)
4. If fewer than 3 papers are provided, supplement with WebSearch

State: "No novelty-assessment.md found. Building positioning from user-provided contribution and related works."

## Outputs

- `contribution-positioning.md` containing:
  - **Closest works summary**: 3-5 papers selected for positioning, with justification for each
  - **Differentiation matrix**: 5-dimension comparison table for each closest work
  - **Contribution statement**: 2-3 candidate statements (method-first, finding-first, problem-first variants)
  - **Reviewer objection anticipation**: For each differentiator, the most likely objection and a prepared 2-3 sentence response
  - **Related work paragraph drafts**: 2-3 sentence paragraphs for each closest work, ready for the related work section

## When to Use

### Scenarios for This Skill

1. **After novelty assessment** -- novelty is confirmed sufficient, now need to articulate it for the paper
2. **Before paper writing** -- need contribution statement, related work drafts, and anticipated objections
3. **During paper writing** -- struggling to write the "our contributions" or related work section
4. **Before submission** -- final check that positioning is clear and objections are anticipated
5. **After receiving reviews** -- reviewer says "unclear novelty" or "incremental" -- need to sharpen positioning

### Typical Workflow

```
novelty-assessment -> [contribution-positioning] -> ml-paper-writing
                        OR
user describes contribution + related works -> [contribution-positioning] -> writing
```

**Output Files:**
- `contribution-positioning.md` -- Differentiation matrix, contribution statements, objections, related work drafts

## Integration with Other Systems

### Pre-Writing Pipeline

```
novelty-assessment (Is this novel enough?)
    |
contribution-positioning (How to articulate novelty)  <-- THIS SKILL
    |
    +---> story-construction (Contribution statement informs narrative arc)
    |
    +---> ml-paper-writing (Related work paragraphs, introduction contribution statement)
```

### Data Flow

- **Depends on**: `novelty-assessment` (Mode A input) -- comparison matrix, novelty classification, differentiation suggestions
- **Optionally uses**: `results-analysis` (Mode A) -- to ground contribution statements in actual results
- **Feeds into**: `story-construction` (contribution statement informs narrative), `ml-paper-writing` (related work paragraphs, introduction)
- **Does NOT duplicate novelty-assessment**: novelty-assessment evaluates whether the contribution is novel enough; contribution-positioning articulates how to communicate that novelty to reviewers
- **Hook activation**: Keyword trigger in `skill-forced-eval.js` -- "contribution", "differentiation", "positioning", "reviewer objection"
- **Command**: `/position` -- generate the positioning document from novelty assessment or user input
- **Obsidian integration**: If bound, creates/updates `Writing/contribution-positioning.md`

### Key Configuration

- **Differentiation matrix**: 5-dimension structured markdown table
- **Contribution statement**: Multiple variants for user selection
- **Objection-response pairs**: Directly usable in rebuttal
- **Related work paragraphs**: Publication-ready drafts
- **Output format**: Markdown for easy editing and version control

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/differentiation-template.md`** -- Differentiation Framework Guide
  - The 5-dimension comparison framework (question, method, data, findings, limitation addressed)
  - Template table for differentiation matrix
  - Contribution statement formula and examples
  - Common reviewer objection patterns and response strategies
  - How to handle concurrent work, incremental-seeming contributions, and negative results as contributions

### Example Files

Complete working examples:

- **`examples/example-positioning.md`** -- Contribution Positioning Example
  - Complete positioning for a contrastive EEG pre-training paper against 4 closest works
  - Filled differentiation matrix, contribution statement variants, reviewer objections with responses, and related work paragraph drafts
