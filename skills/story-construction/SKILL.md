---
name: story-construction
description: This skill should be used when the user asks to "plan the paper story", "build a narrative", "figure plan", "paper blueprint", "section outline", "what story does this paper tell", "how to structure the paper", or after claim-evidence mapping and before manuscript production. Transforms analysis results into a publication narrative with arc, result triage, figure plan, and section outline.
version: 0.1.0
tags: [Research, Writing, Narrative, Figures, Structure]
---

# Story Construction

Transforms analysis results and claim-evidence mappings into a publication narrative. Defines the paper's story arc, triages results by narrative role, designs the figure plan, and produces a section-by-section outline that serves as the structural input to manuscript production.

This skill does **not** duplicate `claim-evidence-bridge`. That skill determines evidence *strength* and *scope*; this skill consumes those ratings and adds narrative *role*, *figure design*, and *structural placement*.

## Core Features

### 1. Narrative Arc Definition

Define the paper's story using a 4-part structure:

- **Setup**: Known context and the gap (sourced from literature review and related work). What the field knows, what it can do, and where current approaches fall short.
- **Question**: What this paper asks (sourced from the hypothesis). The specific question the reader should hold in mind while reading the method and results.
- **Evidence**: Which results answer the question (sourced from analysis). The logical chain of experiments that resolves the question.
- **Implication**: What this means for the field. Why the answer matters beyond this specific experiment -- new understanding, new capability, or changed practice.

Each part maps to paper sections:

| Arc Part | Primary Section(s) | Supporting Section(s) |
|----------|-------------------|----------------------|
| Setup | Introduction (paragraphs 1-3) | Related Work |
| Question | Introduction (final paragraph), Abstract | -- |
| Evidence | Results, Method | Appendix |
| Implication | Discussion, Abstract (final sentence) | Conclusion |

The arc must pass the "one thing" test: can you state the paper's story in a single sentence of the form "This paper shows that [finding] by [method/evidence], which means [implication]"? If not, narrow the scope or split. See `references/narrative-arc-guide.md` for examples and common mistakes.

Arc construction order:
1. Start with the **Question** -- what is the single question this paper answers?
2. Then **Evidence** -- which results answer that question? (prune everything else)
3. Then **Setup** -- what context does the reader need to understand the question?
4. Finally **Implication** -- given the answer, what changes for the field?

### 2. Result Triage

Assign each result from the analysis bundle to one of 4 narrative categories. This extends the claim-evidence map: `claim-evidence-bridge` provides evidence strength ratings; this skill determines where each result lives in the paper.

| Category | Paper Placement | Figure/Table? | Abstract Mention? | Criteria |
|----------|----------------|---------------|-------------------|----------|
| **Primary** | Main results section | Dedicated figure or table | Yes | Directly answers the paper's question; strong evidence |
| **Supporting** | Main results section | May share a figure; row in a table | Brief or no | Strengthens primary result; strong or moderate evidence |
| **Diagnostic** | Methods or appendix | Appendix table at most | No | Confirms a design choice (e.g., "hyperparameter sensitivity was confirmed"); any evidence strength |
| **Null/Negative** | Discussion or appendix | Appendix if at all | No | Honestly reported; informs limitations or future work |

**Relationship to claim-evidence-bridge**: A result with "strong" evidence strength may still be triaged as "supporting" if it does not directly answer the paper's question. A result with "moderate" evidence strength may be triaged as "primary" if it is the central finding (with appropriately hedged language from the claim map).

Triage decision process:
1. Identify the paper's question (from the narrative arc)
2. For each result: does it directly answer the question? If yes -> Primary candidate
3. For each remaining result: does it strengthen a primary result? If yes -> Supporting
4. For each remaining result: does it confirm a design choice or validate a method detail? If yes -> Diagnostic
5. Everything else -> Null/Negative (report honestly)

### 3. Figure Plan

For each primary result and selected supporting results, design the figure or table:

- **Figure type**: Bar chart, line plot, heatmap, scatter plot, table, schematic/diagram, confusion matrix
- **Panel layout**: Single panel, 2-panel (side-by-side or stacked), multi-panel grid (rows x columns)
- **Axes and encoding**:
  - X-axis: variable and units
  - Y-axis: variable and units
  - Color coding: what color represents and the palette choice
  - Marker/line style: meaning of different markers or line styles
- **Reader takeaway**: One sentence stating what the reader should conclude from this figure (e.g., "This figure shows that contrastive pre-training consistently outperforms training from scratch across all 9 subjects.")
- **Statistical annotations**: Significance brackets, error bars (specify: std, SEM, or 95% CI), effect size annotations, baseline reference lines
- **Caption requirements**: Key information the caption must contain (method names, dataset, metric, sample sizes)

Figures are numbered sequentially and referenced from the section outline.

Figure numbering convention:
- **Figure 1**: Method schematic (almost always -- this is what the reader sees first)
- **Figures 2-N**: Primary results in narrative order (one figure per primary result)
- **Tables**: Numbered separately; use tables when exact numbers matter more than visual patterns
- **Appendix figures**: Prefixed with "A" (Figure A1, Table A1)

Each figure entry in the blueprint must include all fields above. Incomplete figure specs (e.g., missing reader takeaway) are flagged during the quality gate.

### 4. Section Outline

Section-by-section skeleton with claim-evidence links:

**Abstract** (structured as 4 sentences mapping to the arc):
1. Setup: one sentence on context and gap
2. Question: one sentence on what this paper does
3. Evidence: one sentence on the key result with numbers
4. Implication: one sentence on significance

**Introduction**:
- Paragraph plan: broad context, narrow to problem, gap, contribution statement
- Contribution statement: sourced from contribution-positioning or constructed here
- Forward references to key figures and results

**Related Work**:
- Paragraph order and grouping (by approach family, not chronologically)
- For each paragraph: topic sentence, how prior work relates, gap this paper fills

**Method**:
- Ordered by what the reader needs to understand the experiments
- Identify which method details are essential for the main paper vs. appendix
- Notation consistency plan

**Results**:
- One subsection per primary result
- Each subsection: setup sentence, figure/table reference, key numbers, interpretation
- Supporting results placed where they strengthen the primary narrative

**Discussion**:
- Implications (from arc part 4)
- Limitations (honest, specific)
- Future work (sourced from null/negative results and claim-evidence map removals)

**Appendix**:
- Diagnostic results with brief descriptions
- Supporting details moved from methods
- Full statistical tables from stats-appendix.md
- Null/negative results with honest interpretation

Each section entry in the outline links back to:
- The narrative arc part it serves
- The specific results (by triage ID) it presents
- The figures/tables it references

### 5. Venue Calibration

Adjust the blueprint for the target venue:

| Venue Type | Page Limit | Figures | Depth | Reader Expectation |
|-----------|-----------|---------|-------|-------------------|
| NeurIPS/ICML/ICLR | 8-9 pages | 4-6 | Thorough experiments, clear method | Technical ML audience |
| Nature/Science | ~4 pages + methods | 3-4 | Broad significance, clean story | Interdisciplinary |
| ACL/EMNLP | 8 pages | 4-5 | Strong baselines, error analysis | NLP specialist |
| Workshop | 4 pages | 2-3 | One clear point, preliminary OK | Niche audience |
| Journal (JMLR/TMLR) | No strict limit | 6-10 | Exhaustive, reproducible | Deep technical review |

Calibration adjustments:
- **Short-format venues**: Tighten the arc, move supporting results to appendix, fewer figures
- **Journal venues**: Expand method section, include all diagnostic results, add reproducibility details
- **Interdisciplinary venues**: Lead with implication, minimize jargon, schematic figure of method

When the venue is unknown, default to NeurIPS conventions (8-page main body, 4-6 figures, technical ML audience).

## Quality Gate

Do not finalize the blueprint until all are true:

- [ ] The narrative arc passes the "one thing" test (single-sentence summary exists)
- [ ] Every result from the analysis bundle is triaged (none are unassigned)
- [ ] Every primary result has a complete figure/table spec (all fields filled)
- [ ] Every figure has a reader takeaway sentence
- [ ] The section outline references all primary and supporting results
- [ ] Null/negative results are placed in discussion or appendix (not silently dropped)
- [ ] The figure count fits the target venue
- [ ] The claim-evidence map entries are referenced (not duplicated) in the triage table

## Input Modes

### Mode A: Pipeline (from predecessors)

1. **Claim-evidence map** -- from `claim-evidence-bridge` output (`claim-evidence-map.md`)
2. **Contribution positioning** -- from `contribution-positioning` output (optional, provides contribution statement and positioning angle)
3. **Analysis bundle** -- from `results-analysis` output (`analysis-report.md`, `figure-catalog.md`)
4. **Target venue** (optional) -- for calibrating scope and depth

### Mode B: Standalone (manual)

1. **Results description** -- user describes their key findings in free text
2. **Paper goal** -- user describes what story the paper should tell
3. **Target venue** (optional)
4. The skill constructs the narrative arc and figure plan from the user's description

When running in Mode B, state: "No claim-evidence-map.md found. Constructing narrative arc from user-provided results description. Evidence strength ratings will be approximate."

## Outputs

- `paper-blueprint.md` containing:
  - **Narrative arc**: Setup, Question, Evidence, Implication (one sentence each + expanded paragraph)
  - **One-sentence story**: The paper's story in a single sentence
  - **Result triage table**: Every result categorized as primary/supporting/diagnostic/null-negative, with evidence strength from claim-evidence-bridge and narrative role from this skill
  - **Figure plan**: For each figure/table -- type, layout, axes, reader takeaway, annotations, caption requirements
  - **Section outline**: Section-by-section skeleton with claim-evidence links and figure references
  - **Venue calibration notes**: Adjustments for target venue (page budget, figure count, depth)
  - **Quality gate checklist**: Confirmation that all checks passed

## When to Use

### Scenarios for This Skill

1. **Before writing** -- have claim-evidence map, need to plan the paper structure
2. **After analysis** -- have results, need to decide the story and figure plan
3. **During revision** -- reviewer says "the story is unclear" or "restructure the paper"
4. **Venue change** -- retargeting a paper to a different venue, need to recalibrate scope
5. **Figure planning** -- need to design figures before producing them

### When NOT to Use This Skill

- To determine whether a claim is supported by evidence -> use `claim-evidence-bridge`
- To run statistical analysis on raw results -> use `results-analysis`
- To write actual prose -> use `ml-paper-writing` (after this skill produces the blueprint)
- To generate the figures themselves -> use `results-analysis` or manual plotting (this skill designs specs only)

### Typical Workflow

```
claim-evidence-bridge + contribution-positioning -> [story-construction] -> manuscript-production
                        OR
user describes results + story -> [story-construction] -> writing
```

**Output Files:**
- `paper-blueprint.md` -- Complete structural blueprint for manuscript production

## Integration with Other Systems

### Pre-Writing Pipeline

```
results-analysis (Analysis bundle)
    |
claim-evidence-bridge (Map claims to evidence)
    |
contribution-positioning (Contribution statement) [optional]
    |
story-construction (Narrative arc + blueprint)  <-- THIS SKILL
    |
manuscript-production (Write prose from blueprint)
```

### Data Flow

- **Depends on**: `claim-evidence-bridge` (evidence strength ratings), `contribution-positioning` (contribution statement), `results-analysis` (analysis bundle)
- **Feeds into**: `manuscript-production` (blueprint drives figure generation and prose), `ml-paper-writing` (structural input)
- **Does NOT duplicate**: `claim-evidence-bridge` -- uses its strength ratings but adds narrative role, figure design, and section structure
- **Hook activation**: Keyword trigger in `skill-forced-eval.js` -- "narrative", "story", "figure plan", "paper blueprint", "section outline"
- **New command**: `/story` -- generate the paper blueprint before writing
- **Obsidian integration**: If bound, creates/updates `Writing/paper-blueprint.md`

### Key Configuration

- **Narrative arc**: 4-part structure (setup, question, evidence, implication)
- **Result triage**: 4-level categorization (primary, supporting, diagnostic, null/negative)
- **Figure plan**: Complete design spec per figure
- **Output format**: Markdown for easy editing and version control
- **Venue calibration**: Adjusts scope, figure count, and depth for target venue

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/narrative-arc-guide.md`** -- Narrative Arc Guide
  - The 4-part narrative arc with published paper examples
  - How to identify the "one thing" the paper is about
  - Common narrative mistakes and how to fix them
  - Adapting arc for different paper types

- **`references/figure-planning.md`** -- Figure Planning Guide
  - Choosing figure type based on data
  - Multi-panel layout conventions for ML papers
  - Statistical annotation conventions
  - Figure-to-text ratio guidelines by venue

### Example Files

Complete working examples:

- **`examples/example-paper-blueprint.md`** -- Paper Blueprint Example
  - Demonstrates complete blueprint for an ICL circuit-algorithm bridge paper
  - Includes narrative arc, result triage, figure plan, and section outline
