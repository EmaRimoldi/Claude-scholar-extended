---
name: quality-review
description: Simulate peer review of the generated paper. Checks claim-evidence alignment, statistical rigor, baseline completeness, generalizability, mechanistic validation, error analysis, presentation accuracy, and reproducibility. Blocks submission if any score < 5.
tags: [Quality, Review, Pipeline, Manuscript]
---

# /quality-review — Paper Quality Review Gate

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Quality review report → `$PROJECT_DIR/docs/`

Never write quality reports to the repository root.

You are now a simulated peer reviewer. Your job is to critically evaluate the generated paper against 8 quality dimensions before it can proceed to submission.

## Input Collection

1. Locate the manuscript: find `main.tex` in `manuscript/`, `sparse-*/manuscript/`, or project root
2. Locate the results: find `results/summary.csv`, `results/all_results.csv`, or individual `results/*/results.json`
3. Locate the hypotheses: `hypotheses.md`
4. Locate the experiment plan: `experiment-plan.md`
5. Locate the claims map: look for `claims_evidence.md` or similar

## Automated Pre-Check

Before scoring, run the mechanical extraction script:

```bash
python scripts/quality_review.py \
    --manuscript-dir $PROJECT_DIR/manuscript/ \
    --results $PROJECT_DIR/analysis-input/results.csv \
    --output $PROJECT_DIR/manuscript/quality-review-data.json
```

This extracts: title words, abstract sentences, figure/table labels, scope counts (models/datasets/methods), banned/restricted word flags, efficiency claim detection, statistical reporting counts, and reproducibility markers. Use the extracted JSON to inform scoring below.

## Review Dimensions

Score each dimension 1-10 and provide specific findings.

### D1: Claim-Evidence Alignment (weight: critical)

- Extract every factual claim from the abstract and introduction
- For each claim, find the supporting evidence in results tables/figures
- Check: Does every keyword in the title correspond to a measured metric?
- Check: Are there claims without corresponding data? (score ≤ 3 if yes)
- Check: Are negative results honestly reported?
- **Auto-fail (score=1)**: Title contains a keyword (e.g., "faithfulness") with no corresponding metric

### D2: Statistical Rigor (weight: critical)

- Check: How many seeds per condition? (< 5 → score ≤ 4, < 3 → score ≤ 2)
- Check: Are formal statistical tests reported? (no p-values/CI → score ≤ 3)
- Check: Are effect sizes reported? (no Cohen's d → score ≤ 5)
- Check: Do confidence intervals overlap for claimed improvements? (overlap → score ≤ 4)
- Check: Is power analysis discussed for small effects?
- **Auto-fail (score=1)**: Claims "significant improvement" without any statistical test

### D3: Baseline Completeness (weight: high)

- Check: Is there a vanilla/no-intervention baseline?
- Check: For explanation methods, are gradient-based alternatives (IG, SHAP) compared?
- Check: For each component of the method, is there an ablation?
- Check: Are there "obvious alternatives" a reviewer would ask about?
- **Auto-fail (score=2)**: No alternative explanation method compared when claiming explanation quality

### D4: Generalizability (weight: medium)

- Check: How many datasets? (1 → score ≤ 5, 2+ → score ≥ 6)
- Check: How many model architectures? (1 → score ≤ 5)
- Check: Is limited generalizability discussed as a limitation?
- Acceptable if limitation is honestly discussed (score 5-6 even with 1 dataset)

### D5: Mechanistic Validation (weight: high)

- Check: If claiming causal relationships, are causal tests included?
- Check: If using attention as explanation, is adversarial attention test done? (Jain & Wallace 2019)
- Check: Are ablation studies sufficient to isolate the mechanism?
- **Auto-fail (score=2)**: Claims attention is "faithful" without any causal/adversarial test

### D6: Error Analysis (weight: medium)

- Check: Are results stratified by class/category?
- Check: Are failure cases analyzed?
- Check: Is performance broken down by relevant dimensions (difficulty, length, agreement)?
- Score ≤ 4 if only aggregate metrics with no stratification

### D7: Presentation Accuracy (weight: critical)

- Check: Does the abstract match the actual results?
- Check: Are numbers in text consistent with tables?
- Check: Are contributions accurately described (not overclaimed)?
- Check: Are limitations discussed?
- **Auto-fail (score=1)**: Abstract contains claims contradicted by results

#### D7a: Title and Abstract Overclaiming Audit

- Check: Every adjective in the title is supported by evidence.
- BANNED title words unless justified across ≥3 model families AND ≥5 datasets: "universal", "general", "always", "any", "all".
- RESTRICTED title words (require ≥2 model families OR ≥3 datasets): "robust", "consistent", "reliable", "task-agnostic".
- Check: Every factual sentence in the abstract maps to a specific table or figure.
- Check: No abstract sentence claims broader scope than the experimental design supports.
- Check: If experiments use 1 model on N datasets, the abstract says "on [model] across [N] [domain] benchmarks" — not "for language models" or "across tasks" generically.
- Check: Category-level claims (e.g., "syntactic tasks") are backed by ≥2 datasets per category; if only 1 dataset per category, dataset names are used instead of category labels.
- **Scope-evidence count**: List number of models, datasets, and domains tested. Map each claim to its evidence scope. Any claim exceeding evidence scope → score ≤ 3.

#### D7b: Limitation-Claim Consistency Check

For every limitation acknowledged in the paper:
1. Does this limitation affect any stated claim? If yes:
   a. Is the claim REDUCED in scope to match? (e.g., "X holds on BERT" instead of "X holds generally")
   b. OR is the limitation addressed by an additional experiment or analysis?
   c. If NEITHER a nor b: the claim must be weakened or removed. Acknowledging a limitation without adjusting claims is a reviewer red flag.
2. **Auto-fail (score=1)**: Paper acknowledges a confound or limitation that directly undermines a primary claim, but the claim is stated without qualification.

Limitation resolution table (mandatory in quality review report):

| Limitation | Affected claims | Resolution | Claim adjusted? |
|-----------|----------------|------------|----------------|
| [limitation] | [claims] | [experiment/rewrite/none] | [YES/NO → action] |

### D8: Reproducibility (weight: medium)

- Check: Are hyperparameters fully specified?
- Check: Are random seeds reported?
- Check: Is code availability mentioned?
- Check: Are hardware/compute details provided?

### D9: Motivation-Measurement Alignment (weight: high)

If the introduction or motivation mentions ANY efficiency benefit ("faster", "cheaper", "less compute", "parameter efficient", "memory efficient"):
- Check: Are wall-clock training times reported (not just parameter counts)?
- Check: Is peak GPU memory usage measured?
- Check: Is throughput (examples/second) reported?
- Parameter count alone is NOT an efficiency metric. Score ≤ 4 if efficiency is claimed but only parameter counts are provided.
- **Auto-fail (score=1)**: Paper title or abstract contains efficiency claims but no efficiency measurements appear in the results.

## Output

Generate a structured review:

```markdown
# Quality Review Report

## Summary
[2-3 sentence overview]

## Scores

| Dimension | Score | Status |
|-----------|-------|--------|
| D1: Claim-Evidence | X/10 | PASS/FAIL |
| D2: Statistical Rigor | X/10 | PASS/FAIL |
| D3: Baselines | X/10 | PASS/FAIL |
| D4: Generalizability | X/10 | PASS/FAIL |
| D5: Mechanistic Validation | X/10 | PASS/FAIL |
| D6: Error Analysis | X/10 | PASS/FAIL |
| D7: Presentation | X/10 | PASS/FAIL |
| D8: Reproducibility | X/10 | PASS/FAIL |
| D9: Motivation-Measurement | X/10 | PASS/FAIL |
| **Overall** | **X/10** | **PASS/FAIL** |

## Detailed Findings
[For each dimension, specific issues found]

## Required Fixes (if any FAIL)
[Numbered list of required changes, ordered by severity]

## Recommendations (for PASS items that could improve)
[Optional improvements]
```

## Gate Rules

- **PASS threshold**: All dimensions must score ≥ 5/10
- **Critical dimensions** (D1, D2, D7, D9): Must score ≥ 6/10
- If ANY dimension scores < 5: **BLOCK submission** and list required fixes
- If ANY critical dimension scores < 6: **BLOCK submission**
- Save the review to `manuscript/quality-review.md`

## After Review

If the review PASSES:
- Print: "Quality review PASSED. Paper is ready for submission."
- Proceed to next pipeline step

If the review FAILS:
- Print: "Quality review FAILED. Required fixes listed below."
- List all required fixes
- In auto mode: attempt to fix issues by re-running relevant pipeline steps
- In interactive mode: ask user which fixes to apply
