---
name: design-novelty-check
description: Gate N2. After experiment design, verify that the experimental design actually tests the novelty claim. Checks baseline correctness, evaluation metric alignment with the field, and ablation coverage of the novelty dimensions. Can loop back to design-experiments.
args:
  - name: strict
    description: "Strict mode: block on any MAJOR issue (default false — blocks only on CRITICAL)"
    required: false
    default: "false"
tags: [Research, Novelty, Gate, Pipeline, Phase2]
---

# /design-novelty-check — Design-Novelty Alignment Gate (Gate N2)

## Purpose

Gate N2 asks one question: **does the experimental design actually test the novelty claim?**

This is a lighter check than Gate N1. It does not re-evaluate whether the contribution is novel — Gate N1 already answered that. Gate N2 asks whether the *experiments* are set up to *demonstrate* that novelty convincingly.

A common failure: the novelty claim is about property X, but the experiments only measure property Y. Or the closest prior work identified in Pass 2 is not included as a baseline.

## Project Directory

Read `pipeline-state.json` → `project_dir`.

**Required inputs:**
- `$PROJECT_DIR/experiment-plan.md`
- `$PROJECT_DIR/hypotheses.md`
- `$PROJECT_DIR/novelty-assessment.md` (Gate N1 output)
- `$PROJECT_DIR/claim-overlap-report.md`

**Output:**
- `$PROJECT_DIR/design-novelty-check.md`
- Update `$PROJECT_DIR/pipeline-state.json` → gate N2 status

---

## Execution

### Check 1: Novelty Claim → Experiment Alignment

Extract the primary novelty claim from `novelty-assessment.md`. This is the claim that Gate N1 approved.

For each dimension where novelty was claimed (from the contribution decomposition):

| Novelty Dimension | Claimed in Gate N1 | Experiment That Tests It | Present in Design? |
|------------------|-------------------|------------------------|-------------------|
| Method novelty | Y/N | [which experiment] | Y/N |
| Empirical novelty | Y/N | [which experiment] | Y/N |
| Application novelty | Y/N | [which experiment] | Y/N |
[...etc...]

**CRITICAL issue:** Any dimension where novelty is claimed but no experiment tests it.

### Check 2: Baseline Completeness

Pull the closest prior work list from `claim-overlap-report.md`. For every paper with overlap level HIGH:

- Is it included as a baseline in `experiment-plan.md`?
- If not: is there a documented justification (e.g., code not available, different task formulation)?

**CRITICAL issue:** A HIGH-overlap paper that is not a baseline and has no justification for its absence. A reviewer will ask "why didn't you compare against [closest prior work]?" — we must have an answer, and that answer must be "we did."

Also check:
- Is there a plain vanilla baseline (no proposed modification)?
- Is there the most widely-used method in the field as a baseline?
- For each component of the proposed method, is there an ablation that removes just that component?

### Check 3: Evaluation Metric Alignment

Check whether the evaluation metrics in `experiment-plan.md` match how the field measures the type of progress being claimed.

Reference: the standard benchmarks identified in the research landscape clusters.

**MAJOR issue:** Using a non-standard metric without justification.
**MAJOR issue:** Using a metric the field has deprecated or critiqued.
**CRITICAL issue:** The novelty claim is about metric X (e.g., "faster") but the experiment plan only measures metric Y (e.g., accuracy), with no measurement of X.

### Check 4: Ablation Coverage of Novelty

If the novelty is a combination of components (combination novelty), or relies on a specific mechanism (method novelty with a stated mechanism), the ablation design must isolate that mechanism.

For each component claimed to be necessary:
- Is there an ablation that removes or varies only that component?
- Is the ablation design sufficient to attribute a performance difference specifically to that component (no confounds)?

**MAJOR issue:** A claimed mechanism with no isolating ablation.

### Check 5: Power Analysis

Are the planned sample sizes / run counts sufficient to detect the claimed effect?

- If the improvement claim is small (< 5% relative improvement), are there enough seeds and evaluation instances to detect it statistically?
- Is the variance of the primary metric known from prior work? If so, is the planned run count sufficient for 80%+ statistical power?

**MAJOR issue:** A small claimed improvement with only 1–2 seeds planned.

---

## Decision Logic

```python
if any(check == 'CRITICAL'):
    decision = 'BLOCK'
    route_to = 'design-experiments'
elif strict and any(check == 'MAJOR'):
    decision = 'BLOCK'
    route_to = 'design-experiments'
elif count(check == 'MAJOR') >= 3:
    decision = 'BLOCK'
    route_to = 'design-experiments'
elif count(check == 'MAJOR') in [1, 2]:
    decision = 'REVISE'
    route_to = 'design-experiments'  # targeted fix only
else:
    decision = 'PASS'
```

**BLOCK:** Route back to `/design-experiments` with the checklist report as input. Specify exactly which checks failed and what the experiment plan must add.

**REVISE:** Route back to `/design-experiments` with targeted instructions. Only the failing checks need to be addressed — do not re-do the full experiment design.

**PASS:** Proceed to Phase 3 (implementation). Log Gate N2 as passed in `pipeline-state.json`.

**Loop termination:** Maximum 2 loops back to `/design-experiments` from Gate N2. On the third failure:
- CRITICAL issues → escalate to human researcher
- MAJOR issues only → document as known limitations, log in `pipeline-state.json`, proceed

---

## Output: `design-novelty-check.md`

```markdown
# Design-Novelty Gate Check (Gate N2)

**Date:** YYYY-MM-DD
**Decision:** PASS / REVISE / BLOCK
**Cycle:** N / 2

## Check 1: Novelty Claim → Experiment Alignment

| Novelty Dimension | Claimed | Tested By | Status |
|------------------|---------|-----------|--------|
[...]

## Check 2: Baseline Completeness

| Prior Work (HIGH overlap) | As Baseline? | Justification if Absent | Status |
|--------------------------|-------------|------------------------|--------|
[...]

**Missing baselines:** [list]

## Check 3: Evaluation Metric Alignment

| Metric | Standard? | Tests Novelty Claim? | Status |
|--------|-----------|---------------------|--------|
[...]

## Check 4: Ablation Coverage

| Component | Isolating Ablation Present? | Status |
|-----------|---------------------------|--------|
[...]

## Check 5: Power Analysis

| Metric | Claimed Effect Size | Seeds Planned | Sufficient Power? | Status |
|--------|--------------------|--------------|--------------------|--------|
[...]

## Issue Summary

| ID | Severity | Description | Required Fix |
|----|----------|-------------|-------------|
[...]

## Decision

**Decision:** PASS / REVISE / BLOCK
**Route to:** [step] (if REVISE or BLOCK)
**Specific instructions for fix:** [what must change in experiment-plan.md]
```

---

## Gate Criteria

Before marking complete:

- [ ] All 5 checks executed
- [ ] Decision recorded in `design-novelty-check.md`
- [ ] `pipeline-state.json` updated with Gate N2 status
- [ ] If BLOCK/REVISE: specific fix instructions written and passed to `/design-experiments`

---

## Integration

- **Follows:** `/design-experiments`
- **Loops back to:** `/design-experiments` (max 2 iterations)
- **Feeds into:** `/scaffold` (Phase 3 starts only after PASS)
- **Relevant to:** Paper Quality Verifier Dimension 2 (Methodological Rigor), criterion M1 (baseline completeness) and M5 (ablations)
- **Agent:** `experiment-design` skill + `scope-agent` (sonnet)
