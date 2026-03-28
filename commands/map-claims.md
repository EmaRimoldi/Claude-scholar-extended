---
name: map-claims
description: Generate a claim-evidence map before writing. Maps planned paper claims to experimental evidence and manages paper scope.
args:
  - name: contributions
    description: Planned contributions (reads from analysis bundle if available, or prompts interactively)
    required: false
  - name: analysis_dir
    description: Path to analysis output directory (defaults to analysis-output/ in project root)
    required: false
    default: analysis-output
tags: [Research, Writing, Evidence]
---

# Map Claims Command

Generate a claim-evidence map that verifies every planned paper claim is supported by experimental evidence.

## Goal

This command activates the `claim-evidence-bridge` skill to produce a structured claim-evidence map covering:

1. **Claim extraction**: All claims the paper intends to make
2. **Evidence mapping**: Specific evidence supporting each claim
3. **Strength assessment**: Strong / Moderate / Weak / Unsupported
4. **Language recommendations**: How to phrase each claim
5. **Scope decisions**: What to include, hedge, remove, or move to supplementary

## Usage

### Basic (reads from analysis bundle)

```bash
/map-claims
```

### With explicit analysis directory

```bash
/map-claims analysis-output/iter-02
```

## Workflow

1. **Locate evidence**: Read `analysis-report.md`, `stats-appendix.md`, `figure-catalog.md` from analysis directory
2. **Prompt for claims**: Ask user to list planned contributions, or infer from analysis
3. **Activate `claim-evidence-bridge` skill**: Generate the map
4. **Write outputs**:
   - `claim-evidence-map.md` in project root
   - If Obsidian-bound: `Writing/claim-evidence-map.md`

## Claim-Evidence Consistency Gate

Before finalizing the claim-evidence map, apply these mandatory consistency checks:

- **Dual-sided evidence listing**: For each claim, explicitly list BOTH supporting AND contradicting evidence from results. Never present only the favorable side.
- **Ambiguity flag**: Flag claims where evidence is ambiguous or contradictory — these must be reframed honestly before proceeding.
- **Statistical significance downgrade**: If a claim says "method X improves Y" but the evidence shows no statistically significant improvement, the claim MUST be downgraded to "method X maintains Y" or "method X does not significantly degrade Y".
- **Title keyword audit**: Extract every substantive keyword from the planned title, verify each has at least one metric and one significant result supporting it. If any keyword lacks evidence, flag for title revision.
- **Hard block**: BLOCK manuscript generation if any core claim has zero supporting evidence. The map must be revised and all core claims must have at least one piece of supporting evidence before downstream steps proceed.

## Integration

- **Primary skill**: `claim-evidence-bridge`
- **Prerequisite**: `results-analysis` output (recommended) or user description
- **Feeds into**: `ml-paper-writing` (the map becomes a writing checklist)
