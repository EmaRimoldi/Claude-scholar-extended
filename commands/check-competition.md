---
name: check-competition
description: Generate structured search queries for competitive landscape check. Two-turn interaction: first generates queries, then analyzes pasted results.
args:
  - name: contribution_statement
    description: Your contribution statement (reads from novelty-assessment.md if available, or prompts interactively)
    required: false
tags: [Research, Competitive Analysis]
---

# Check Competition Command

## MANDATORY: Online Competitive Check

You MUST use WebSearch to check for competing/recent work. Search for:
1. The exact research question or close variants
2. Key method names + "2024 2025 2026"
3. Related workshop papers, preprints, blog posts

Do NOT skip this step. Do NOT claim offline. If no competing work is found after genuine search, state that explicitly with the queries you tried.

Generate structured search queries to check if competing work has been published.

## Goal

This command activates the `competitive-check` skill in a two-turn interaction:

**Turn 1**: Generate platform-specific search queries for Semantic Scholar, arXiv, and Google Scholar.

**Turn 2**: Analyze pasted search results and produce a competitive alert report.

## Usage

### Basic (reads from novelty-assessment.md or prompts interactively)

```bash
/check-competition
```

### With explicit contribution statement

```bash
/check-competition "Cross-subject EEG transfer using contrastive pre-training"
```

## Workflow

1. **Locate contribution**: Read `novelty-assessment.md` or prompt user for contribution statement
2. **Activate `competitive-check` skill (Turn 1)**: Generate search queries
3. **Wait for user**: User runs queries and pastes results
4. **Activate `competitive-check` skill (Turn 2)**: Analyze results
5. **Write outputs**:
   - `competitive-queries.md` (Turn 1)
   - `competitive-alert.md` (Turn 2)

## Novelty Gate Enforcement

After competitive analysis, each contribution must be classified as:

- **NOVEL**: No prior work does this. Record the searched queries that returned nothing relevant.
- **INCREMENTAL**: Prior work exists but this version differs in [specific way]. Must explicitly state the delta.
- **NOT NOVEL**: Prior work already demonstrated this. REMOVE from contribution list.

**Gate rules:**
- The pipeline MUST NOT proceed to experiment design if ALL contributions are classified as NOT NOVEL.
- If the primary contribution is INCREMENTAL, the paper must explicitly acknowledge prior work and frame the contribution as an extension, not a discovery.
- Include the novelty classification in `competitive-alert.md`.

## Integration

- **Primary skill**: `competitive-check`
- **Prerequisite**: Contribution statement (from `novelty-assessment.md` or user input)
- **Feeds into**: Researcher decision-making
