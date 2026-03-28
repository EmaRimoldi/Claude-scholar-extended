---
name: produce-manuscript
description: Produce publication-quality figures, full paper prose, LaTeX source, and submission package from paper-blueprint.md.
args:
  - name: venue
    description: Target venue (neurips, icml, iclr, acl)
    required: false
    default: neurips
tags: [Research, Writing, LaTeX, Figures]
---

# Produce Manuscript Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- LaTeX source → `$PROJECT_DIR/manuscript/`
- Figures → `$PROJECT_DIR/figures/`
- Submission package → `$PROJECT_DIR/manuscript/`

Never write manuscript files to the repository root.

Generate the complete submission package.

## Goal

Activates the `manuscript-production` skill to produce figures (publication-quality matplotlib/TikZ), full prose (using ml-paper-writing guidance), LaTeX source, supplementary materials, and formatted PDF.

## Usage

```bash
/produce-manuscript                # defaults to NeurIPS format
/produce-manuscript venue=icml     # ICML format
```

## Workflow

1. Read paper-blueprint.md, analysis-report.md, contribution-positioning.md
2. Activate `manuscript-production` skill
3. Generate figures per figure plan → paper/figures/
4. Write prose per section outline → paper/main.tex
5. Compile LaTeX, organize supplementary, check formatting
6. Write: paper/ directory with complete submission package

## Pre-Generation Verification Gates

Before generating any manuscript content, run these mandatory audits. BLOCK generation if any audit fails — list the failures and require fixes before proceeding.

- **Abstract audit**: Every factual claim in the abstract must correspond to a specific number in the results. No claim without data. If the abstract says "achieves 95% accuracy", the results must contain that exact number.
- **Title audit**: Every keyword in the title must correspond to a metric that was measured AND showed a result. If the title says "improves faithfulness" there must be a faithfulness metric showing improvement. Flag unsupported title keywords for revision.
- **Contribution audit**: Each numbered contribution must have at least one table or figure directly supporting it. If a contribution is contradicted by results, it must be reframed or removed — not spun.
- **Negative results**: If any hypothesis was NOT supported, the paper MUST honestly report this. Spinning contradicted hypotheses as positive results is forbidden. Negative results should appear in the results section with honest discussion of implications.

### Enforcement

Generation proceeds only after all four audits pass. If any audit fails, output a structured failure report listing each violation and the specific fix required before re-running.

## Integration

- **Primary skill**: `manuscript-production`
- **Extends**: `ml-paper-writing` (uses its section-by-section writing methodology)
- **Prerequisite**: `story-construction` output (paper-blueprint.md), analysis data
- **Final output**: Submission-ready PDF
