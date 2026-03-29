---
name: paper-self-review
description: This skill should be used when the user asks to "review paper quality", "check paper completeness", "validate paper structure", "self-review before submission", or mentions systematic paper quality checking. Provides comprehensive quality assurance checklist for academic papers.
version: 0.1.0
---

# Paper Self-Review

A systematic paper quality checking tool that helps researchers conduct comprehensive self-review before submission.

## Core Features

### 1. Structure Review

Check whether all sections of the paper are complete and conform to academic standards:
- Does the Abstract include problem, method, results, and contributions?
- Does the Introduction clearly articulate research motivation and background?
- Is the Method detailed enough to be reproducible?
- Do the Results sufficiently support the conclusions?
- Does the Discussion address limitations and future work?

### 2. Logic Consistency Check

Verify the logical coherence of the paper:
- Do research questions match the methodology?
- Does the experimental design support the research hypotheses?
- Are result interpretations reasonable?
- Are conclusions supported by evidence?

#### 2a. Overclaiming Audit

- Every adjective in the title must be experimentally justified.
- BANNED title words unless justified across ≥3 model families AND ≥5 datasets: "universal", "general", "always", "any", "all".
- Every factual abstract sentence must map to a specific table or figure.
- No claim may have broader scope than the experimental design supports.
- Category-level claims require ≥2 datasets per category.

#### 2b. Limitation-Claim Consistency

For every limitation acknowledged in the paper:
- Does it affect any stated claim?
- If yes: is the claim reduced in scope or addressed by an additional experiment?
- If neither: the claim must be weakened or removed.
- Acknowledging a limitation without adjusting claims is a reviewer red flag.

#### 2c. Motivation-Measurement Alignment

If the paper motivates with efficiency claims, verify that wall-clock time, GPU memory, and throughput are measured — not just parameter counts.

### 3. Citation Completeness

Check the completeness and accuracy of citations:
- Are all citations present in the references?
- Is the reference format consistent?
- Are key related works cited?
- Do citations accurately reflect the original content?

### 4. Figure/Table Quality

Evaluate the quality and effectiveness of figures and tables:
- Do all figures/tables have clear titles and captions?
- Do figures/tables support the text narrative?
- Are figures/tables clear and readable?
- Do formats comply with journal/conference requirements?

### 5. Writing Clarity

Check writing clarity and readability:
- Is the language concise and clear?
- Is technical terminology used appropriately?
- Are sentence structures clear?
- Is paragraph organization logical?

## Quality Checklist

Use this checklist for systematic paper self-review:

```
Paper Quality Checklist:
- [ ] Abstract includes problem, method, results, contributions
- [ ] Introduction clearly states research motivation
- [ ] Method is reproducible
- [ ] Results support conclusions
- [ ] Discussion addresses limitations
- [ ] All figures/tables have captions
- [ ] Citations are complete and accurate
```

## When to Use

Use this skill in the following scenarios:

- **Pre-submission check** - Final review before submitting to a journal or conference
- **After first draft** - Systematic review after completing the first draft
- **Before advisor review** - Self-check before requesting advisor feedback to improve quality
- **Post-revision verification** - After revising based on reviewer comments, verify all issues are addressed
- **Collaborator review** - Quality check before sending to collaborators

## Review Process

Follow these steps for systematic paper review:

### Step 1: Structure Review
Start with the overall structure, checking if all sections are complete and logically coherent.

### Step 2: Content Review
Dive into each section, checking content accuracy and completeness.

### Step 3: Citation Check
Verify the completeness and accuracy of all citations.

### Step 4: Figure/Table Review
Check the quality and captions of all figures and tables.

### Step 5: Writing Quality
Review language expression and writing clarity.

### Step 6: Final Checklist
Use the quality checklist for final verification.

## Best Practices

### Review Timing
- **Spaced review** - Wait 1-2 days after completing the draft before reviewing to maintain objectivity
- **Multiple rounds** - Conduct multiple review rounds, focusing on different aspects each time
- **Print review** - Print a hard copy for review; issues are easier to spot on paper

### Review Techniques
- **Reverse reading** - Read from conclusion backwards to check logical coherence
- **Read aloud** - Reading the paper aloud helps identify language issues
- **Reviewer perspective** - Assume you are a reviewer and read critically

### Common Issues
- Abstract too brief or too verbose
- Introduction lacks clear research question statement
- Method lacks sufficient detail for reproduction
- Results lack statistical significance tests
- Discussion doesn't address research limitations
- Figures/tables lack clear titles and captions
- Inconsistent citation formatting

## Integration with Other Systems

### Pre-Submission Pipeline

```
manuscript-production (Complete paper draft)
    |
paper-self-review (Systematic quality check)  <-- THIS SKILL
    |
    ├── ready with minor edits → post-acceptance
    └── needs revision → iterate with manuscript-production
```

### Data Flow

- **Depends on**: `manuscript-production` (completed paper draft in `paper/` directory)
- **Also requires**: `claim-evidence-bridge` output (`claim-evidence-map.md`) for claim-conclusion audit
- **Also uses**: `results-analysis` output (`analysis-report.md`, `stats-appendix.md`) for verifying claims against evidence
- **Feeds into**: `post-acceptance` (if ready), or revision loop back to `manuscript-production`
- **Hook activation**: Keyword trigger in `skill-forced-eval.js` — "self-review", "review paper", "check paper quality"
- **No dedicated command**: Triggered manually or as part of the manuscript production workflow

### Upstream Input Requirements

| Input | Source | Required |
|-------|--------|----------|
| Paper draft (`paper/main.tex` or equivalent) | manuscript-production | Yes |
| `claim-evidence-map.md` | claim-evidence-bridge | Required for Claim-Conclusion Audit |
| `analysis-report.md` | results-analysis | Recommended for evidence verification |
| `stats-appendix.md` | results-analysis | Recommended for statistical claim checking |

If `claim-evidence-map.md` is missing, the Claim-Conclusion Audit section of the checklist cannot be completed. State: "claim-evidence-map.md not found. Claim-Conclusion Audit will be skipped. Run `/map-claims` to enable this check."

## Reference Files

Load only what is needed:
- `references/SECTION-CHECKLIST.md` - section-by-section review questions and claim-conclusion audit
- `references/FINAL-VERDICT.md` - how to summarize submission readiness and blocking issues
- `examples/example-self-review.md` - example review output
