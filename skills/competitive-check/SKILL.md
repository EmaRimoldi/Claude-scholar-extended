---
name: competitive-check
description: This skill should be used when the user asks to "check for competing work", "has anyone published something similar", "check for scooping", "concurrent work", "generate search queries for competing work", or wants to verify their contribution is still novel. Generates structured search queries for competitive landscape checks and analyzes user-provided results.
version: 0.1.0
tags: [Research, Competitive Analysis, arXiv, Literature]
---

# Competitive Check

On-demand competitive landscape check. Generates structured search queries optimized for Semantic Scholar, arXiv, and Google Scholar, then analyzes user-provided results for overlap with the research project.

## Design Philosophy

This is a **competitive check template**, not an automatic monitor. It generates queries the user runs manually on search platforms. The user then pastes results back for analysis. This avoids dependency on automated search APIs and keeps the researcher in control of the search step.

## Core Features

### 1. Query Generation (Turn 1)

Generate structured search queries optimized for each platform:

- **Semantic Scholar**: Phrase-based queries with year filters
- **arXiv**: URL-formatted queries sorted by date
- **Google Scholar**: Operator-based queries with date filters
- **Query rationale**: Why each query was constructed this way

### 2. Results Analysis (Turn 2)

Analyze user-pasted search results:

- **Overlap assessment**: None / Low / Medium / High for each found paper
- **Threat classification**: For high-overlap papers, assess threat level
- **Differentiation**: How does your work differ from the competing paper?
- **Recommendations**: Actions to take based on the competitive landscape

### 3. Alert Status

Overall assessment:

- **CLEAR**: No significant overlap found
- **CAUTION**: Some overlap detected, differentiation needed
- **URGENT**: Direct competitor found, immediate action needed

## Workflow (Two-Turn Interaction)

**Turn 1 -- Query Generation**: User provides contribution statement. Skill produces search queries.

**Turn 2 -- Results Analysis**: User pastes search results. Skill analyzes overlap and produces alert.

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Novelty assessment** -- from `novelty-assessment` output (provides contribution statement and closest works)
2. **Time window** (optional) -- how far back to check (default: 3 months)

### Mode B: Standalone (manual)

1. **Contribution statement** -- user describes what their project contributes in free text
2. **Key differentiators** -- user lists 2-3 things that make their approach unique
3. **Time window** (optional)

## Outputs

### Turn 1: `competitive-queries.md`
- 3-5 search queries per platform (Semantic Scholar, arXiv, Google Scholar)
- Query construction rationale
- Instructions for the user on how to run each query
- Date range filter recommendations

### Turn 2: `competitive-alert.md`
- Papers found with overlap assessment (none/low/medium/high)
- For high-overlap papers: what they do, how they differ, threat level
- Differentiation recommendations if overlap is high
- Status: CLEAR / CAUTION / URGENT

## When to Use

### Scenarios for This Skill

1. **Before committing to experiments** -- verify no one has published the same idea
2. **Mid-project check** -- months into the project, check for concurrent work
3. **Pre-submission** -- final check before submitting the paper
4. **After rejection** -- check if the competitive landscape has changed since last submission

### Typical Workflow

```
User provides contribution statement -> [competitive-check Turn 1] -> user searches
-> user pastes results -> [competitive-check Turn 2] -> alert report
```

**Output Files:**
- `competitive-queries.md` -- Search queries for the user to run (Turn 1)
- `competitive-alert.md` -- Overlap analysis and alert status (Turn 2)

## Integration with Other Systems

### Research Workflow

This skill runs **on-demand**, not in the main pipeline. The user decides when to run it.

- **Depends on**: `novelty-assessment` (Mode A) OR user contribution statement (Mode B)
- **Feeds into**: Researcher decision-making (may trigger hypothesis revision or scope change)
- **Hook activation**: Keyword trigger in `skill-forced-eval.js`
- **New command**: `/check-competition`
- **No loop integration**: Manual, on-demand check

### Key Configuration

- **Platforms**: Semantic Scholar, arXiv, Google Scholar
- **Default time window**: 3 months
- **Alert levels**: CLEAR / CAUTION / URGENT
- **Output format**: Markdown for easy sharing with collaborators

## Additional Resources

### Reference Files

- **`references/search-strategies.md`** -- Search Strategy Guide
  - Query construction for each platform
  - Boolean operators and filters
  - How to interpret search results
  - Common false positives and how to filter them

### Example Files

- **`examples/example-competitive-alert.md`** -- Competitive Alert Example
  - Demonstrates both turns of the interaction
  - Shows query generation and results analysis
