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

## Integration

- **Primary skill**: `manuscript-production`
- **Extends**: `ml-paper-writing` (uses its section-by-section writing methodology)
- **Prerequisite**: `story-construction` output (paper-blueprint.md), analysis data
- **Final output**: Submission-ready PDF
