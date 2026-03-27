---
name: claim-evidence-bridge
description: This skill should be used when the user asks to "map claims to evidence", "check if my claims are supported", "what can I claim in the paper", "scope the paper", "what to include in the paper", "over-claiming", or after experiment analysis and before starting paper writing. Maps paper claims to experimental evidence, manages paper scope.
version: 0.1.0
tags: [Research, Writing, Evidence, Claims, Scope]
---

# Claim-Evidence Bridge

Creates an explicit mapping between every claim a paper will make and the experimental evidence supporting it. Flags unsupported or over-claimed results, manages paper scope, and produces a writing checklist for `ml-paper-writing`.

## Core Features

### 1. Claim Extraction

Identify all claims the paper intends to make:

- **Primary contributions**: Main claims about method, results, or insights
- **Secondary claims**: Supporting claims about components, ablations, analysis
- **Implicit claims**: Claims implied by language but not explicitly stated (e.g., "state-of-the-art" implies comparison against all relevant methods)

### 2. Evidence Mapping

For each claim, identify:

- **Supporting evidence**: Specific table, figure, or statistic
- **Evidence strength**: Strong / Moderate / Weak / Unsupported
- **Alternative interpretations**: Confounds or alternative explanations
- **Missing evidence**: What additional data would strengthen the claim

### 3. Evidence Strength Criteria

- **Strong**: Statistically significant, replicated across seeds/folds, no obvious confounds, consistent with secondary metrics
- **Moderate**: Significant but small effect, OR significant but only on one dataset, OR missing important control
- **Weak**: Not statistically significant, OR contradicted by some metrics, OR based on a single run
- **Unsupported**: No experimental evidence provided, OR evidence contradicts the claim

### 4. Claim Language Recommendations

For each claim, recommend the appropriate language:

- **Strong evidence**: Claim as stated ("We show that...", "Our method achieves...")
- **Moderate evidence**: Hedge ("Our results suggest...", "We observe that...", "competitive with...")
- **Weak evidence**: Qualify heavily or move to supplementary ("Preliminary results indicate...")
- **Unsupported**: Remove from main claims, mention as future work if relevant

### 5. Scope Decision (addresses Gap 8)

Based on the claim-evidence map, decide paper scope:

- **Include**: Claims with strong evidence (primary contributions)
- **Hedge**: Claims with moderate evidence (adjust language)
- **Remove**: Claims with weak/no evidence (move to future work)
- **Supplementary**: Claims with moderate evidence that support but don't drive the narrative
- **Venue-fit assessment**: Is the overall contribution correctly sized for the target venue?

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Planned contributions** -- what the paper intends to claim
2. **Analysis bundle** -- from `results-analysis` output (`analysis-report.md`, `stats-appendix.md`, `figure-catalog.md`)
3. **Hypothesis evolution** -- from `hypothesis-revision` output (optional, shows what was learned)
4. **Target venue** (optional) -- for calibrating claim strength

### Mode B: Standalone (manual)

1. **Planned contributions** -- user lists the claims they want to make in free text
2. **Evidence description** -- user describes their experimental results (metrics, tables, figures) or points to result files
3. **Target venue** (optional)
4. The skill structures the claim-evidence mapping from the user's description

When running in Mode B, state: "No analysis bundle found. Mapping claims against user-provided evidence descriptions."

## Outputs

- `claim-evidence-map.md` containing:
  - For each claim:
    - Supporting evidence (table/figure/statistic reference)
    - Evidence strength (strong/moderate/weak/unsupported)
    - Alternative interpretations or confounds
    - Recommended claim language (strong/hedged/removed)
  - **Scope decision section**:
    - Claims to include (strong evidence)
    - Claims to hedge (moderate evidence)
    - Claims to remove (weak/no evidence)
    - Supplementary material candidates
    - Venue-fit assessment

## When to Use

### Scenarios for This Skill

1. **Before writing** -- have results, need to determine what to claim
2. **During writing** -- need to verify a specific claim is supported
3. **During self-review** -- checking if all claims have evidence
4. **After reviewer feedback** -- reviewer says "over-claimed" -- need to recalibrate

### Typical Workflow

```
results-analysis + hypothesis-evolution -> [claim-evidence-bridge] -> ml-paper-writing
                        OR
user lists claims + evidence -> [claim-evidence-bridge] -> writing
```

**Output Files:**
- `claim-evidence-map.md` -- Claim-evidence mapping with scope decisions

## Integration with Other Systems

### Pre-Writing Pipeline

```
results-analysis (Analysis bundle)
    |
hypothesis-evolution (What was learned) [optional]
    |
claim-evidence-bridge (Map claims to evidence)  <-- THIS SKILL
    |
ml-paper-writing (Write with verified claims)
```

### Data Flow

- **Depends on**: `results-analysis` (Mode A) OR user description (Mode B)
- **Feeds into**: `ml-paper-writing` (the map becomes a writing checklist)
- **Hook activation**: Keyword trigger in `skill-forced-eval.js`
- **New command**: `/map-claims` -- generate the claim-evidence map before writing
- **Obsidian integration**: If bound, creates/updates `Writing/claim-evidence-map.md`

### Key Configuration

- **Evidence strength**: 4-level scale (strong/moderate/weak/unsupported)
- **Scope decisions**: Include/hedge/remove/supplementary
- **Output format**: Markdown table for easy review and editing
- **Writing checklist**: Every claim in the paper must trace back to an entry in the map

## Additional Resources

### Reference Files

- **`references/evidence-strength-criteria.md`** -- Evidence Strength Assessment
  - Detailed criteria for each strength level
  - Common patterns that inflate perceived strength
  - Statistical significance vs. practical significance

- **`references/scope-decision-guide.md`** -- Paper Scope Decision Guide
  - How to decide what goes in the paper vs. supplement vs. future work
  - Venue-specific scope calibration
  - The "one-paper vs. two-papers" decision

### Example Files

- **`examples/example-claim-map.md`** -- Claim-Evidence Map Example
  - Demonstrates complete mapping with scope decisions
  - Shows language recommendations at each evidence level
