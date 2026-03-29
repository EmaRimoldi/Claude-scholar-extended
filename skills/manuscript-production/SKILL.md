---
name: manuscript-production
description: This skill should be used when the user asks to "produce the manuscript", "generate figures", "compile the paper", "assemble submission", "camera ready", "write the paper draft", "build the LaTeX", "create figure manifest", or when transitioning from analysis and story construction into a complete submission package. Produces publication-quality figures, full manuscript prose, and assembled LaTeX submission packages.
version: 0.1.0
tags: [Research, Writing, Figures, LaTeX, Submission, Manuscript Production]
dependencies: [matplotlib, seaborn, numpy]
---

# Manuscript Production

Produce the complete submission package: publication-quality figures, full manuscript prose, LaTeX source, and supplementary materials. This skill takes upstream deliverables (paper blueprint, analysis report, contribution positioning) and turns them into a camera-ready submission.

## Relationship to ml-paper-writing

This skill **extends** `ml-paper-writing` -- it does NOT replace it.

- **ml-paper-writing** provides writing methodology: section-by-section guidance, philosophy, citation workflows, reviewer heuristics, and operating modes.
- **manuscript-production** produces the actual deliverables: rendered figures, drafted prose, compiled LaTeX, and assembled supplementary material.

When writing prose, always consult `ml-paper-writing` for guidance on tone, structure, and section-specific conventions. This skill orchestrates the production; that skill provides the craft.

## Default operating order

1. Collect inputs: `paper-blueprint.md`, `analysis-report.md`, `contribution-positioning.md`, experiment data, figure plan.
2. Produce figures (Feature 1) -- figures before prose, because prose references them.
3. Draft manuscript prose (Feature 2) -- section by section, following the blueprint.
4. Assemble submission package (Feature 3) -- LaTeX compilation, supplementary, checklists.
5. Apply venue-specific formatting (Feature 4) -- final compliance pass.

## Core Features

### 1. Figure Production

Generate publication-quality figures for the target venue.

#### 1.1 Unified Style Sheet

Set matplotlib rcParams before any figure generation. See `references/figure-style-guide.md` for full specification.

- **NeurIPS**: single column = 5.5 in, double column = 11 in, font size 8-10 pt, serif (Times)
- **ICML**: single column = 3.25 in, double column = 6.75 in, font size 8-10 pt, serif (Times)
- **ICLR**: single column = 5.5 in, double column = 11 in, font size 8-10 pt, serif (Times)
- **ACL**: single column = 3.3 in, double column = 6.8 in, font size 8-10 pt, serif (Times)

Always apply the style sheet at the start of figure generation:

```python
import matplotlib.pyplot as plt
from manuscript_figures import apply_venue_style
apply_venue_style("neurips", column="single")
```

See `examples/example-rcparams.py` for a complete working example.

#### 1.2 Schematic Figures

Architecture diagrams and pipeline illustrations:

- Use matplotlib patches, arrows, and annotations for simple schematics
- Use TikZ for complex diagrams that benefit from precise positioning
- Keep schematics minimal: boxes, arrows, labels -- no decorative elements
- Use consistent color coding: same color for the same concept across all figures
- Label every component; avoid abbreviations not defined in the caption

#### 1.3 Result Figures

Generate from analysis data per the figure plan in the paper blueprint:

- **Bar charts**: grouped bars with hatching for grayscale compatibility, error bars showing 95% CI or standard deviation (always state which), baseline reference lines
- **Line plots**: distinct markers per method, line styles vary for grayscale, shading for confidence intervals, axis labels with units
- **Heatmaps**: annotated cell values, appropriate color normalization (linear vs. log), colorbar with label and units, aspect ratio 1:1 unless data dictates otherwise
- **Statistical annotations**: significance brackets, effect sizes, sample sizes in captions

#### 1.4 Colorblind-Safe Palettes

Use colorblind-safe palettes by default. See `references/figure-style-guide.md` for hex codes.

- **Qualitative** (up to 6 categories): Wong palette or Tol bright
- **Sequential**: viridis, inferno, or cividis
- **Diverging**: coolwarm with desaturated extremes

Never rely on color alone to distinguish categories. Always pair with markers, hatching, or line styles.

#### 1.5 Export Standards

- Format: vector PDF (not rasterized PNG)
- Resolution: 300 DPI minimum for any rasterized elements (e.g., heatmap cells)
- Whitespace: use `bbox_inches='tight'` and `pad_inches=0.02`
- Font embedding: ensure all fonts are embedded (use `pdf.fonttype: 42`)
- File naming: `fig{N}-{short-description}.pdf` (e.g., `fig1-pipeline-overview.pdf`)

#### 1.6 Figure Manifest

After generating all figures, produce `figures/figure-manifest.md`:

```markdown
| Filename | Paper Location | Type | Caption Summary |
|----------|---------------|------|-----------------|
| fig1-pipeline.pdf | Figure 1 (Introduction) | Schematic | Method pipeline overview |
| fig2-main-results.pdf | Figure 2 (Results 4.1) | Bar chart | Main comparison table |
```

See `examples/example-figure-manifest.md` for a complete example.

### 2. Prose Generation

Write the full manuscript, section by section, following the paper blueprint.

#### 2.1 General Prose Principles

- Consult `ml-paper-writing` for section-specific writing guidance before drafting each section.
- Write in active voice where possible. Passive voice is acceptable for methods.
- One idea per paragraph. Topic sentence first.
- Define all notation in the Method section before using it elsewhere.
- Forward-reference figures and tables: "as shown in Figure 2" not "as shown below."
- Maintain consistent terminology: choose one term per concept and use it throughout.

#### 2.2 Overclaiming Prevention (mandatory)

Before drafting the title and abstract, run these checks:

**Title audit:**
- Every adjective in the title must be supported by evidence.
- BANNED words unless experimentally justified across ≥3 model families AND ≥5 datasets: "universal", "general", "always", "any", "all".
- RESTRICTED words (require ≥2 model families OR ≥3 datasets): "robust", "consistent", "reliable", "task-agnostic".
- The title must be literally true — not aspirational. If experiments use one model on three tasks, the title must name the model and scope.

**Abstract audit:**
- Every factual sentence in the abstract must map to a specific table or figure.
- No sentence may claim broader scope than the experimental design supports.
- If experiments use 1 model on N datasets, the abstract must say "on [model] across [N] [domain] benchmarks" — not "for language models" or "across tasks" generically.

**Scope-evidence alignment check:**
1. Count: number of models tested, number of datasets tested, number of domains tested.
2. Map each claim to its scope: "works on BERT-base" vs. "works on transformers" vs. "works on language models".
3. Any claim whose scope exceeds evidence scope → REJECT and rewrite with narrower scope.
4. Category-level claims (e.g., "syntactic tasks") require ≥2 datasets per category; if only 1 dataset per category, use dataset names, not category labels.

#### 2.3 Abstract

Follow the 5-sentence formula from `ml-paper-writing`:

1. **Context**: One sentence on the problem domain and why it matters.
2. **Gap**: One sentence on what current methods lack.
3. **Approach**: One sentence on what this paper does.
4. **Results**: One-two sentences on key quantitative findings.
5. **Implication**: One sentence on broader significance.

Target length: 150-250 words depending on venue.

#### 2.3 Introduction

Structure:

1. **Opening paragraph**: Motivate the problem. Why should the reader care?
2. **Background paragraph**: Brief context on the state of the field.
3. **Gap paragraph**: What is missing? What fails? Use the gap analysis from the paper blueprint.
4. **Approach paragraph**: What does this paper do? High-level method description.
5. **Contribution statement**: Numbered list of contributions from `contribution-positioning`. Be precise and falsifiable.
6. **Roadmap** (optional): "The remainder of this paper is organized as follows..." Only if the paper structure is non-standard.

#### 2.4 Related Work

- Organize by theme, not chronologically.
- Use the differentiation matrix from `contribution-positioning` to position against each group.
- For each group: summarize the approach, state the limitation, explain how this work differs.
- End with a summary paragraph: "In contrast to prior work, our approach..."
- Be generous to related work. Acknowledge contributions fairly.

#### 2.5 Method

- Clear enough for reproduction by a competent researcher.
- Start with problem formulation: define input, output, notation.
- Present the method top-down: overview first, then details.
- Use algorithm blocks for procedures with steps.
- Every equation must be referenced in the text.
- State all assumptions explicitly.
- Provide computational complexity analysis where relevant.

#### 2.6 Results

- One subsection per primary result, matching the figure plan.
- Each subsection follows: setup sentence, result statement, figure/table reference, interpretation.
- Report exact numbers: "achieves 73.2% accuracy (CI: 71.8-74.6)" not "significantly outperforms."
- Ablation results: present in the order that builds understanding, not necessarily the order of the ablation plan.
- Compare against baselines explicitly: "improves over [baseline] by X.X points."

#### 2.7 Discussion

Structure the Discussion as argument, not decoration. Each item below is a paragraph or paragraph group, not a bullet in a list.

1. **Key insight paragraph**: State the main takeaway and what it changes for the field. Connect back to the narrative arc's "Implication" from the paper blueprint.
2. **Limitations paragraph(s)** (minimum 1 substantive paragraph, not a bullet list):
   - For each major limitation: state it, explain how it could affect the conclusions, and describe what experiment would resolve the concern.
   - Do not enumerate limitations as a list — discuss each one with reasoning about its impact on the claims.
3. **Alternative explanations paragraph**: For each primary result, state at least one plausible alternative explanation. Explain why the proposed interpretation is preferred, or acknowledge that the evidence does not distinguish between explanations.
4. **What would make this conclusion false?** (MANDATORY paragraph): Explicitly state what evidence, result, or experimental outcome would falsify the main claim. This paragraph forces intellectual honesty and demonstrates scientific maturity to reviewers.
5. **Empirical vs. causal claims**: If the paper demonstrates correlation or association, do not use causal language ("causes", "leads to", "results in") in the Discussion or Conclusion unless a causal mechanism is experimentally demonstrated. Use observational language ("is associated with", "co-occurs with", "predicts") and state the limitation explicitly.
6. **Future work**: Concrete experiments that would address the limitations above — not vague gestures like "future work could explore..." but specific experimental designs.

#### 2.8 Notation Consistency

Before finalizing prose:

1. Collect all mathematical symbols used in the paper.
2. Verify each is defined before first use (in Method section).
3. Verify consistent usage: the same symbol always means the same thing.
4. Create `\newcommand` macros for frequently used notation.

### 3. Submission Assembly

Compile the complete submission package.

#### 3.1 LaTeX Source

- Use the target venue's official template from `ml-paper-writing/templates/`.
- Follow `references/latex-patterns.md` for document structure, figure inclusion, and table formatting.
- All figures in `figures/` subdirectory, referenced by relative path.
- All bibliography entries in a single `.bib` file.
- Use `\input{}` for long sections to keep the main file navigable.

**Tables**: When the project was scaffolded with `project-scaffold`, use the deterministic CSV-to-LaTeX generator instead of writing tables by hand:

```bash
make tables                                              # default spec
python scripts/csv_to_latex_tables.py --config scripts/table_spec.json  # custom spec
```

This reads `experiments/results_summary.csv` and emits `.tex` files into `manuscript/tables/`. Include them in the manuscript with `\input{tables/tab_<name>}`. After `make refresh`, tables update automatically on the next `make build-pdf`. See `project-scaffold/references/template-catalog.md` section M for the full script source and table specification format.

**Use agent-generated tables only when**: the table requires non-standard formatting (multi-row cells, merged headers, custom highlighting), or when data comes from sources other than `results_summary.csv`.

#### 3.2 Supplementary Material

- Appendix sections for proofs, extended derivations, additional analysis.
- Extended tables: full results that do not fit in the main paper.
- Additional figures: ablation visualizations, qualitative examples.
- Structure: `supplementary/` directory with its own LaTeX file if the venue requires a separate PDF.

#### 3.3 Reproducibility Checklist

If the venue requires a reproducibility checklist (NeurIPS, ICML):

- Answer every question. Do not leave items blank.
- Reference specific sections, figures, or appendices for each "Yes" answer.
- Be honest about "No" answers -- explain why and what you did instead.
- Common items: random seeds reported, error bars included, hyperparameter search described, compute budget stated.

#### 3.4 Code and Data Availability

- Draft a code/data availability statement.
- If code will be released: "Code is available at [URL]" or "Code will be released upon acceptance."
- If data is proprietary: explain access limitations clearly.
- Anonymous GitHub repos for double-blind review (if venue allows).

#### 3.5 Reference Completeness

Before submission, verify:

- Every `\cite{}` key has a corresponding `.bib` entry.
- No orphaned `.bib` entries (entries not cited in the paper).
- Run `bibtex` or `biber` and check for warnings.
- Verify author names, years, and venues match actual papers.
- Use the citation verification workflow from `ml-paper-writing` for any uncertain references.

#### 3.6 Pre-Submission Formatting Checklist

See `references/venue-formatting.md` for the complete 10-item checklist. Summary:

1. Page limit compliance (main body, excluding references)
2. Anonymous (no author names, no institution, no self-citation giveaways)
3. Figures legible at print size (text in figures >= 6pt)
4. Tables use booktabs (no vertical rules)
5. References complete and consistently formatted
6. Supplementary correctly linked or bundled
7. Reproducibility checklist complete (if required)
8. No TODO/FIXME/PLACEHOLDER markers remain
9. Abstract within word limit
10. PDF file size within venue limit (typically < 50 MB)

### 4. Venue-Specific Formatting

Adapt the submission to the target venue's requirements.

#### 4.1 NeurIPS

- **Page limit**: 9 pages main body + unlimited references + unlimited appendix
- **Template**: `neurips.sty` from `ml-paper-writing/templates/neurips2025/`
- **Anonymization**: Required for review. No author info, no acknowledgments, no identifying URLs.
- **Checklist**: Paper checklist is mandatory. Include as the last section before references.
- **Supplementary**: Appendix in the same PDF, after references. No separate supplementary PDF.
- **Broader impact**: Not required as a separate section but checklist asks about it.

#### 4.2 ICML

- **Page limit**: 8 pages main body + unlimited references + unlimited appendix
- **Template**: `icml2026.sty` from `ml-paper-writing/templates/icml2026/`
- **Anonymization**: Required for review. Similar rules to NeurIPS.
- **Broader impact**: Optional but recommended.
- **Supplementary**: Appendix after references in the same PDF.
- **Style notes**: Two-column format. Use `figure*` for full-width figures.

#### 4.3 ICLR

- **Page limit**: 10 pages main body + unlimited references + unlimited appendix
- **Template**: `iclr2026_conference.sty` from `ml-paper-writing/templates/iclr2026/`
- **Submission**: Via OpenReview. Upload PDF directly.
- **Anonymization**: Required for review.
- **Supplementary**: Appendix in same PDF or as separate upload on OpenReview.
- **Style notes**: Single-column format. More generous page limit allows deeper method sections.

#### 4.4 ACL

- **Page limit**: 8 pages main body + unlimited references
- **Template**: `acl.sty` from `ml-paper-writing/templates/acl/`
- **Limitations section**: Required. Must discuss limitations of the work.
- **Ethics statement**: Required if applicable. Discuss ethical considerations.
- **Supplementary**: Separate supplementary PDF, up to 100 MB.
- **Style notes**: Two-column format. Strict formatting requirements.

## Input Requirements

This skill expects the following inputs to be available:

| Input | Source | Required |
|-------|--------|----------|
| `paper-blueprint.md` | story-construction skill | Yes |
| `analysis-report.md` | results-analysis skill | Yes |
| `contribution-positioning.md` | contribution-positioning skill | Yes |
| Experiment data (CSV, JSON, logs) | analysis-input/ directory | Yes |
| Figure plan | Embedded in paper-blueprint.md | Yes |
| Target venue | User-specified or from blueprint | Yes |
| `experiment-state.json` | experiment-runner skill | Recommended |

If any required input is missing, state the gap explicitly and ask the user to provide it or run the upstream skill.

### Experiment Completion Verification

Before producing manuscript content, check whether experiments actually completed:

1. **If `experiment-state.json` exists**: Read its `status` field.
   - `"analyzing"` or `"confirmed"`: Experiments complete. Proceed normally.
   - `"running"`: "WARNING: experiment-state.json shows status 'running'. Experiments may still be in progress. Any claims based on current data may be invalidated by pending results. Proceed only if the user explicitly confirms the current data is sufficient."
   - `"diagnosing"` or `"revising"`: "WARNING: experiment-state.json shows status '{status}'. The research is in an iteration loop — experiments did not confirm the hypothesis. Proceed with extreme caution and ensure all claims use appropriately hedged language."
   - `"planned"`: "BLOCKING: experiment-state.json shows status 'planned'. No experiments have been executed. Cannot produce a manuscript without experimental evidence."
2. **If `experiment-state.json` does not exist**: Check whether `analysis-input/results.csv` or `analysis-input/run-manifest.json` exist and contain data. If both are missing or empty, warn: "No experiment state file or collected results found. Verify that experiments have been executed and results collected before manuscript production."
3. **If `analysis-input/gap-report.md` exists**: Check for missing runs. If more than 20% of expected runs are missing or failed, warn: "Gap report shows {N}% of expected runs are missing or failed. The manuscript will be based on incomplete data — flag this in the Limitations section."

## Output

This skill produces the following directory structure:

```
paper/
  main.tex                    # Main LaTeX source
  sections/                   # Individual section .tex files
    abstract.tex
    introduction.tex
    related-work.tex
    method.tex
    results.tex
    discussion.tex
    appendix.tex
  figures/
    figure-manifest.md        # Figure-to-location mapping
    fig1-*.pdf                # Individual figure PDFs
    fig2-*.pdf
    ...
  supplementary/
    supplementary.tex         # Extended results, proofs, additional figures
  references.bib              # Complete bibliography
  Makefile                    # Build commands (pdflatex + bibtex)
```

## Integration

- **Depends on**: `story-construction` (paper blueprint and figure plan), `contribution-positioning` (contribution statement and differentiation matrix), `results-analysis` (analysis report and experiment data), `claim-evidence-bridge` (claim verification and scoping)
- **Extends**: `ml-paper-writing` (uses its section-by-section writing guidance, citation workflow, and LaTeX templates)
- **Does NOT replace**: `ml-paper-writing` -- that skill provides writing methodology; this skill produces the actual deliverables
- **Feeds into**: `paper-self-review` (self-review of the completed manuscript), `post-acceptance` (camera-ready revisions)

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/figure-style-guide.md`** -- Figure Style Guide
  - Venue-specific figure dimensions and font sizes
  - Colorblind-safe palettes with hex codes
  - Export standards (DPI, font embedding, whitespace)
  - Unified rcParams for matplotlib

- **`references/latex-patterns.md`** -- LaTeX Patterns
  - Document structure and section organization
  - Figure and table inclusion patterns
  - Algorithm and equation formatting
  - Common LaTeX pitfalls and fixes

- **`references/venue-formatting.md`** -- Venue Formatting Reference
  - Pre-submission 10-item formatting checklist
  - Page limits, anonymization rules, supplementary requirements per venue
  - Common formatting errors that cause desk rejection

### Example Files

Complete working examples:

- **`examples/example-figure-manifest.md`** -- Figure Manifest Example
  - Demonstrates figure-to-location mapping table

- **`examples/example-rcparams.py`** -- Matplotlib rcParams Example
  - Complete working venue-specific style configuration

## Trigger Conditions

Activate this skill when the user mentions:
- "figures", "generate figures", "publication figures"
- "LaTeX", "compile paper", "build the paper"
- "submission", "submit the paper", "submission package"
- "manuscript", "write the manuscript", "draft the paper"
- "camera ready", "camera-ready version"
- "produce manuscript", "assemble submission"

## Command

`/produce-manuscript` -- Run the full manuscript production pipeline.

When invoked without arguments, the command:
1. Scans for upstream deliverables (blueprint, analysis report, contribution positioning).
2. Reports what is available and what is missing.
3. If all inputs are present, proceeds through the default operating order.
4. If inputs are missing, prompts the user to run the upstream skill or provide the file.

Optional flags:
- `--venue <name>`: Override the target venue (neurips, icml, iclr, acl)
- `--figures-only`: Only produce figures, skip prose and assembly
- `--prose-only`: Only draft prose, skip figures and assembly
- `--assemble-only`: Only assemble LaTeX package from existing prose and figures
- `--check`: Run pre-submission formatting checklist without producing new content
