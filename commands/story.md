---
name: story
description: Define narrative arc, triage results, create figure plan, and produce section outline for the paper. Outputs paper-blueprint.md.
tags: [Research, Writing, Narrative]
---

# Story Command

Design the paper's narrative structure.

## Goal

Activates the `story-construction` skill to define the narrative arc, triage results by importance, plan figures/tables, and produce a section-by-section outline.

## Usage

```bash
/story
```

## Workflow

1. Read claim-evidence-map.md, contribution-positioning.md, analysis-report.md
2. Activate `story-construction` skill
3. Write: paper-blueprint.md (narrative arc, result triage, figure plan, section outline)

## Integration

- **Primary skill**: `story-construction`
- **Prerequisite**: `claim-evidence-bridge` output, `contribution-positioning` output, `results-analysis` output
- **Feeds into**: `manuscript-production` (blueprint drives figures and prose)
