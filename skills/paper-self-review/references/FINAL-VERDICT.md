# Final Verdict

## Verdict buckets

Assign exactly one verdict:

- **`ready with minor edits`**: All section checks pass. No blocking issues. Only cosmetic or minor wording improvements needed. Paper can be submitted after a quick polish pass.
- **`needs moderate revision`**: Most section checks pass but 1-3 substantive issues remain (e.g., a claim lacks sufficient evidence, a limitation is not discussed, a figure is misleading). Requires targeted work but not a full rewrite.
- **`not ready for submission`**: Multiple blocking issues. Core claims are unsupported, major sections are incomplete, or the narrative is incoherent. Requires significant revision before submission.

## Always report

### Top 3 blocking issues
Issues that would likely cause rejection if not fixed. Examples:
- "Claim 2 (cross-domain generalization) has no supporting evidence in the results"
- "Discussion section is a 3-bullet list, not a substantive analysis"
- "No significance testing reported for any comparison"
- "claim-evidence-map.md shows 2 primary claims rated 'Unsupported'"

### Top 3 polish issues
Issues that reduce quality but are not fatal. Examples:
- "Figure 3 caption does not specify what error bars represent"
- "Introduction contribution bullet 3 is vague ('extensive experiments')"
- "Related work paragraph on [X] is missing the most recent 2024 paper"

### Missing evidence or missing citations
- List any `[CITATION NEEDED]` placeholders remaining in the draft
- List any claims that reference experiments not present in the analysis bundle
- Note if claim-evidence-map.md was unavailable (Claim-Conclusion Audit skipped)

### Figure/table risks
- Figures that are illegible at print size (text < 6pt)
- Tables missing uncertainty or sample size
- Figures that rely on color alone without markers/hatching
- Figures referenced in text but not present in `paper/figures/`

## Claim-Conclusion Audit summary

If `claim-evidence-map.md` was available, report:
- Number of claims checked: N
- Claims matching evidence strength: N
- Claims stated more strongly than evidence warrants: N (list them)
- Claims missing from the map: N (list them)
- Negative results mentioned in Discussion: yes/no

If `claim-evidence-map.md` was NOT available:
- State: "Claim-Conclusion Audit was skipped — claim-evidence-map.md not found. Run /map-claims to enable this check."
