# Paper Scope Decision Guide

## The Scope Decision Matrix

| Evidence Strength | In Paper? | Where? |
|---|---|---|
| Strong | Yes | Main contributions, abstract, introduction |
| Moderate | Yes, hedged | Results section with qualified language |
| Weak | Maybe | Supplementary material, or dropped |
| Unsupported | No | Future work at most |

## One Paper or Two?

**Signals you should split into two papers**:
- You have two independent strong results that tell different stories
- The paper exceeds page limits even with tight writing
- Reviewers consistently say "too much going on"
- One result is ready now but the other needs more experiments

**Signals you should keep as one paper**:
- The results build on each other (result B only makes sense with result A)
- Neither result alone meets the venue's contribution bar
- The combined story is stronger than either part alone
- Splitting would require duplicating the methodology section

## Venue-Specific Scope Calibration

### NeurIPS / ICML / ICLR
- **Expected scope**: One clear contribution with thorough experiments
- **Typical claims**: 1 primary + 2-3 supporting
- **Common mistake**: Trying to claim too many things -> each feels shallow
- **Page budget**: 8-9 pages of content

### Nature / Science (short format)
- **Expected scope**: One striking finding with broad implications
- **Typical claims**: 1 primary with extensive validation
- **Common mistake**: Too many technical details -> unclear what the finding is
- **Page budget**: ~4 pages + methods + supplementary

### Workshop Papers
- **Expected scope**: One interesting observation or preliminary result
- **Typical claims**: 1 primary, minimal supporting evidence acceptable
- **Good for**: Testing whether the community finds the direction interesting

## The Supplementary Material Decision

Move to supplementary when:
- The result supports the main narrative but is not essential to understand it
- It is a robustness check or sensitivity analysis
- It provides implementation details that support reproducibility
- It is an ablation that confirms a design choice but does not change the story

Keep in the main paper when:
- Removing it would leave a gap in the argument
- Reviewers are likely to ask about it
- It is a primary contribution
