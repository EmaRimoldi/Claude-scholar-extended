---
name: story
description: Define narrative arc, triage results, create figure plan, and produce section outline for the paper. Outputs paper-blueprint.md.
tags: [Research, Writing, Narrative]
---

# Story Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- `paper-blueprint.md` → `$PROJECT_DIR/docs/paper-blueprint.md`

Never write paper blueprints to the repository root.

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

## Devil's Advocate Review

After constructing the narrative, generate the top 5 objections a hostile reviewer would raise. For each objection, verify the paper has data or discussion addressing it.

### Standard objections to check

1. **"Why not compare with [obvious alternative method]?"** — Verify the baselines include the most natural competitor. If not, flag as a required addition or explain the omission.
2. **"Only one dataset — how do we know this generalizes?"** — Verify multi-dataset evaluation or explicitly scope the generalization claims.
3. **"Effect sizes are tiny — is this practically significant?"** — Verify practical significance is discussed alongside statistical significance.
4. **"You claim X but don't measure X directly"** — Verify every core claim has a metric that directly measures the claimed phenomenon.
5. **"Correlation ≠ causation — where's the causal evidence?"** — Verify causal language is only used when supported by causal methodology (interventions, ablations, controls).

### Resolution rule

If any objection cannot be addressed with existing results, flag it as either:
- A **required addition** (new experiment, baseline, or analysis before submission), or
- An **explicit limitation** that must appear in the paper's discussion/limitations section.

## Integration

- **Primary skill**: `story-construction`
- **Prerequisite**: `claim-evidence-bridge` output, `contribution-positioning` output, `results-analysis` output
- **Feeds into**: `manuscript-production` (blueprint drives figures and prose)
