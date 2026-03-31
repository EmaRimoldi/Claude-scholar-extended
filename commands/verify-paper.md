---
name: verify-paper
description: 7-dimensional paper quality verifier. Replaces /quality-review. Evaluates the manuscript across independent dimensions (Novelty, Methodological Rigor, Claim-Evidence Alignment, Argument Structure, Cross-Section Coherence, Presentation Quality, Reproducibility). Each dimension can independently block. Produces structured PASS/REVISE/BLOCK decision with routed remediation. 46 individual criteria total.
args:
  - name: dimensions
    description: "Comma-separated list of dimensions to run (1–7). Default: all. Example: '2,3' to re-run only Methodological Rigor and Claim-Evidence after a targeted fix."
    required: false
    default: "1,2,3,4,5,6,7"
  - name: cycle
    description: "Revision cycle number (1–3). Tracked in pipeline-state.json."
    required: false
    default: ""
tags: [Quality, Review, Pipeline, Manuscript, Gate]
---

# /verify-paper — 7-Dimensional Paper Quality Verifier

## Purpose

This command is the **final arbiter** of paper quality before submission. It replaces `/quality-review`. Unlike a single gate with a composite score, this verifier evaluates the paper across 7 independent dimensions, each with its own criteria, scoring, and blocking authority. A paper must pass ALL dimensions to proceed to submission.

The verifier asks one question: **would this paper survive peer review at a top venue?**

## Project Directory

Read `pipeline-state.json` → `project_dir`.

**Required inputs:**
- `$PROJECT_DIR/manuscript/` — LaTeX source
- `$PROJECT_DIR/analysis-report.md`
- `$PROJECT_DIR/claim-alignment-report.md` (from Step 26 `/claim-source-align`)
- `$PROJECT_DIR/cross-section-report.md` (from Step 32 `/cross-section-consistency`)
- `$PROJECT_DIR/claim-overlap-report.md` (from Pass 2)
- `$PROJECT_DIR/adversarial-novelty-report.md` (from Pass 6)
- `$PROJECT_DIR/concurrent-work-report.md` (from recency sweeps)
- `$PROJECT_DIR/.epistemic/confidence_tracker.json`
- `$PROJECT_DIR/experiment-state.json`
- Target venue formatting guidelines (read from `pipeline-state.json` → `target_venue`)

**Output:**
- `$PROJECT_DIR/manuscript/paper-quality-report.md`
- Updated `pipeline-state.json` → `verify_paper_cycle`, `verify_paper_decision`

---

## Pre-Check: Load Automated Analysis

Before scoring, run the mechanical extraction:

```bash
python scripts/quality_review.py \
    --manuscript-dir $PROJECT_DIR/manuscript/ \
    --results $PROJECT_DIR/analysis-input/results.csv \
    --output $PROJECT_DIR/manuscript/quality-review-data.json
```

Also load outputs from deterministic checks already run:
- `cross-section-report.md` → feeds Dimension 5 directly
- `claim-alignment-report.md` → feeds Dimension 3 directly
- `method-reconciliation-report.md` → feeds Dimension 2 (criterion M8)

These checks have already been run — do NOT re-run the same logic. Consume their outputs.

---

## Dimension 1: Novelty & Contribution

**Run only if `1` is in `$dimensions`.**

**Inputs:** Manuscript text, `claim-overlap-report.md`, `adversarial-novelty-report.md`, `concurrent-work-report.md`, `novelty-assessment.md` or `novelty-reassessment.md`

Score each criterion 0–10:

| ID | Criterion |
|----|-----------|
| N1 | The paper makes an explicit, falsifiable contribution statement |
| N2 | The claimed contribution is not fully anticipated by any cited paper |
| N3 | No uncited paper in `claim-overlap-report.md` with overlap HIGH exists |
| N4 | The novelty differential vs. closest prior work is explicitly articulated |
| N5 | The significance of the contribution is argued, not just asserted |
| N6 | Related work covers all major threads from `research-landscape.md` |
| N7 | Prior art is credited honestly and proportionally: the paper acknowledges what it borrows (method, framing, experimental setup); overlapping prior work is discussed in sufficient detail, not dismissed in a clause; language does not minimize overlap (e.g., "unlike X" when difference is minor) |

**CRITICAL auto-BLOCK:**
- A HIGH-overlap paper from `claim-overlap-report.md` is not cited or discussed
- The contribution statement is absent
- `adversarial-novelty-report.md` flagged INSUFFICIENT and this was not addressed

**Route_to on block:** `/formulate-hypotheses` (contribution reframing), `/position` (related work), `/story` (narrative)

---

## Dimension 2: Methodological Rigor

**Run only if `2` is in `$dimensions`.**

**Inputs:** Manuscript text, `experiment-state.json`, config files, `analysis-report.md`, `method-reconciliation-report.md`

| ID | Criterion |
|----|-----------|
| M1 | All baselines include the current SOTA and closest prior work from `claim-overlap-report.md` |
| M2 | Evaluation metrics are standard for the field or justified if non-standard |
| M3 | Statistical methodology is appropriate: significance tests, CIs, effect sizes |
| M4 | Sample sizes / dataset sizes sufficient to support the claims |
| M5 | Ablation studies isolate each proposed component |
| M6 | Hyperparameter sensitivity addressed or acknowledged |
| M7 | Experimental setup described in enough detail for reproduction |
| M8 | Method section matches actual code/configs (from `method-reconciliation-report.md`) |

**CRITICAL auto-BLOCK:**
- SOTA claim with no comparison to actual current SOTA
- Statistical claim without any significance testing
- Method section contradicts actual experimental configuration

**Route_to on block:** `/design-experiments` (missing baselines/ablations — new experiments needed), `/analyze-results` (statistics), `/produce-manuscript` (writing misrepresents method)

---

## Dimension 3: Claim-Evidence Alignment

**Run only if `3` is in `$dimensions`.**

**Inputs:** `claim-alignment-report.md`, `analysis-report.md`, manuscript text, `.epistemic/confidence_tracker.json`

| ID | Criterion |
|----|-----------|
| C1 | Every factual claim traceable to a specific result or citation (from `claim-alignment-report.md`) |
| C2 | No claim is stronger than evidence warrants (no overclaiming) |
| C3 | Hedge language calibrated correctly — not too uncertain, not overconfident |
| C4 | Limitations honestly acknowledged, not buried |
| C5 | Abstract claims ⊆ conclusion claims ⊆ evidence |
| C6 | Causal claims supported by causal evidence |

**CRITICAL auto-BLOCK:**
- Abstract claim with no corresponding evidence in results
- Causal claim ("X causes Y") from only correlational evidence
- Claimed improvement within reported confidence interval of baseline

**Route_to on block:** `/map-claims` (claim mapping), `/produce-manuscript` (prose overclaims), `/analyze-results` (additional analysis needed)

---

## Dimension 4: Argument Structure & Logical Flow

**Run only if `4` is in `$dimensions`.**

**Inputs:** Manuscript text, `paper-blueprint.md`

| ID | Criterion |
|----|-----------|
| A1 | Introduction motivates a clear, precise research question |
| A2 | Research question answered by experiments |
| A3 | Results presented in order that builds the argument |
| A4 | Discussion interprets results; does not restate them |
| A5 | Conclusion follows from evidence, no new claims |
| A6 | Sections flow logically — each motivates the next |

**CRITICAL auto-BLOCK:**
- Research question never directly answered in results or discussion
- Conclusion makes a claim not supported anywhere in the paper

**Route_to on block:** `/story` (narrative restructuring), `/produce-manuscript` (writing doesn't follow arc)

---

## Dimension 5: Cross-Section Coherence

**Run only if `5` is in `$dimensions`.**

**Inputs:** `cross-section-report.md` (already computed — consume it, do not re-run), manuscript text

| ID | Criterion |
|----|-----------|
| X1 | Abstract claims ⊆ conclusion claims ⊆ evidence (subset relationship holds) |
| X2 | Terminology consistent throughout |
| X3 | All figure/table references exist; all figures/tables referenced in text |
| X4 | Numbers consistent across sections |
| X5 | Method in main text consistent with appendix/supplementary |
| X6 | Paper does not contradict itself |

**CRITICAL auto-BLOCK:**
- Numerical discrepancy between sections
- Figure or table referenced but does not exist
- Direct self-contradiction between sections

**Note:** If `cross-section-report.md` already shows all 5 sub-checks passed, Dimension 5 auto-passes. If any sub-check failed, the failure details are imported directly — do not re-evaluate.

**Route_to on block:** `/produce-manuscript` (writing inconsistency), `/analyze-results` (numbers need re-verification)

---

## Dimension 6: Presentation Quality

**Run only if `6` is in `$dimensions`.**

**Inputs:** Manuscript text, compiled PDF (if available), target venue guidelines from `pipeline-state.json`

| ID | Criterion |
|----|-----------|
| P1 | Writing clear and concise; jargon defined at first use |
| P2 | Figures readable, labeled, informative captions |
| P3 | Each figure makes exactly one clear point |
| P4 | Tables well-formatted with appropriate precision |
| P5 | Paper respects venue formatting requirements |
| P6 | Grammar and spelling correct |
| P7 | Paper is the right length |

**CRITICAL auto-BLOCK:**
- Paper exceeds page limit
- Figures unreadable at print resolution

**Route_to on block:** `/produce-manuscript` (writing/figures), `/compile-manuscript` (formatting)

---

## Dimension 7: Reproducibility & Transparency

**Run only if `7` is in `$dimensions`.**

**Inputs:** Manuscript text, `experiment-state.json`, config files, code repository

| ID | Criterion |
|----|-----------|
| R1 | All hyperparameters reported |
| R2 | Dataset described in sufficient detail |
| R3 | Computational cost reported |
| R4 | Code availability stated |
| R5 | Random seeds and variance reported (≥ 3 seeds for primary results) |
| R6 | Negative results or failed approaches acknowledged |

**CRITICAL auto-BLOCK:**
- Results from single run with no variance estimate
- Critical hyperparameters missing

**Route_to on block:** `/produce-manuscript` (add details), `/analyze-results` (additional runs needed)

---

## Scoring and Decision Logic

For each dimension run, compute:
- Dimension score: mean of criterion scores (0–10)
- Issue counts by severity: CRITICAL / MAJOR / MINOR
- Per-dimension decision: PASS / REVISE / BLOCK

**Global blocking rules:**
```
if any CRITICAL issue from any dimension:
    decision = BLOCK
elif any dimension score < 5:
    decision = BLOCK
elif count(MAJOR issues from single dimension) >= 3:
    decision = BLOCK
elif count(MAJOR issues total) >= 5:
    decision = BLOCK
elif average score < 7.0:
    decision = REVISE
else:
    decision = PASS
```

**Revision routing:** Each issue includes a `route_to` field. REVISE triggers a targeted loop — only the relevant steps re-execute, then the verifier re-runs on the affected dimensions only (use `$dimensions` argument for partial re-runs).

**Revision cycle termination:**
- Maximum 3 revision cycles (tracked in `pipeline-state.json` → `verify_paper_cycle`)
- After cycle 3: if still BLOCK → escalate to human researcher
- After cycle 3: if REVISE → document remaining MAJOR issues as known limitations in cover letter, proceed

---

## Output: `paper-quality-report.md`

```markdown
# Paper Quality Verification Report

**Date:** YYYY-MM-DD
**Revision Cycle:** N / 3
**Overall Decision:** PASS / REVISE / BLOCK
**Overall Score:** X.X / 10.0

## Dimension Scores

| # | Dimension | Score | Decision |
|---|-----------|-------|----------|
| 1 | Novelty & Contribution | X/10 | PASS/REVISE/BLOCK |
| 2 | Methodological Rigor | X/10 | PASS/REVISE/BLOCK |
| 3 | Claim-Evidence Alignment | X/10 | PASS/REVISE/BLOCK |
| 4 | Argument Structure | X/10 | PASS/REVISE/BLOCK |
| 5 | Cross-Section Coherence | X/10 | PASS/REVISE/BLOCK |
| 6 | Presentation Quality | X/10 | PASS/REVISE/BLOCK |
| 7 | Reproducibility | X/10 | PASS/REVISE/BLOCK |

**Total issues:** CRITICAL: N, MAJOR: N, MINOR: N

## Issues (ordered by severity)

| ID | Severity | Dimension | Location | Description | Route_to | Remediation |
|----|----------|-----------|----------|-------------|----------|-------------|
[...]

## Acceptance Probability Estimate

**Estimate:** HIGH / MEDIUM / LOW
- HIGH (60–80%): all dimensions ≥ 8, no MAJOR issues
- MEDIUM (30–50%): all dimensions ≥ 6, ≤ 2 MAJOR issues
- LOW (< 30%): any dimension < 6, or 3+ MAJOR issues

**Justification:** [2–3 sentences]

## Revision Instructions

[If BLOCK: list issues that must be fixed first, in priority order, with route_to for each]
[If REVISE: which dimensions to re-run (/verify-paper --dimensions X,Y), which steps to re-run first]
[If PASS: optional improvements that would increase acceptance probability]

## Previous Cycles
[If cycle > 1: score history and changes from previous cycle]
```

---

## Self-Calibration Log

After each revision cycle, record the predicted acceptance probability and the actual outcome of that cycle's review. This allows the verifier to track whether its estimates are systematically optimistic or pessimistic over time.

Append one entry to `$PROJECT_DIR/.epistemic/verifier_calibration_log.json` after writing `paper-quality-report.md`:

```json
{
  "cycle": 1,
  "date": "YYYY-MM-DD",
  "predicted_probability": "MEDIUM",
  "decision": "REVISE",
  "critical_issues": 2,
  "major_issues": 4,
  "resolved_in_next_cycle": null,
  "actual_outcome": null
}
```

Fields `resolved_in_next_cycle` and `actual_outcome` are filled in on subsequent cycles:
- `resolved_in_next_cycle`: set to `true`/`false` at the start of the next cycle's run, based on whether the issues flagged in this cycle were fixed.
- `actual_outcome`: filled in after submission — accepted/rejected/withdrawn (never filled by the pipeline; requires human update).

If the log shows a systematic pattern (e.g., PASS predictions consistently followed by REVISE outcomes), flag this to the user as: `[CALIBRATION WARNING] Verifier has over-predicted PASS N consecutive times. Apply additional scrutiny.`

---

## Gate Criteria

Before marking complete:

- [ ] All requested dimensions scored
- [ ] All CRITICAL issues documented with route_to and remediation
- [ ] Global decision computed and written
- [ ] `paper-quality-report.md` written to `$PROJECT_DIR/manuscript/`
- [ ] `pipeline-state.json` updated with cycle count and decision
- [ ] If BLOCK: specific re-run instructions provided
- [ ] Self-calibration log entry appended to `.epistemic/verifier_calibration_log.json`

---

## Integration

**Position in pipeline (Phase 5B revision cycle):**
1. `/produce-manuscript` (Step 31)
2. `/cross-section-consistency` (Step 32 — its output feeds Dimension 5)
3. `/claim-source-align` (Step 33 — its output feeds Dimension 3)
4. **`/verify-paper`** (Step 34, replaces old `/multi-dimensional-review`)
5. If PASS → `/adversarial-review` (Step 35)
6. If REVISE/BLOCK → route to specific upstream step → re-run affected dimensions only

**Callable independently:** `/verify-paper --dimensions 2,3` re-runs only Dimensions 2 and 3 after a targeted fix.

**Agents:** Four LLM invocations in parallel (one per high-weight dimension: Novelty, Methodology, Claim-Evidence, Argument). Dimensions 5 and 7 consume pre-computed outputs. Dimension 6 runs independently.
