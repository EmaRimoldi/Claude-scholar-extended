---
name: novelty-gate
description: Novelty evaluation gate. Handles Gates N1 (post-hypothesis), N3 (post-results), and N4 (pre-submission). Reads all search pass outputs, runs contribution decomposition and per-dimension assessment, produces a structured PROCEED/REPOSITION/PIVOT/KILL recommendation.
args:
  - name: gate
    description: "Which gate to run: N1, N3, or N4"
    required: true
  - name: project_dir
    description: Project directory path (reads from pipeline-state.json if not set)
    required: false
    default: ""
tags: [Research, Novelty, Gate, Pipeline]
---

# /novelty-gate — Structured Novelty Evaluation

## Purpose

This command is the **kill-or-continue decision point** for the research project. It synthesizes all search pass outputs, evaluates novelty across multiple dimensions, and produces a structured machine-readable recommendation. It is not a soft suggestion — a KILL recommendation terminates the project.

Gates:
- **N1 (post-hypothesis):** Full evaluation using all 6 search passes. Primary gate. Hard block before experiment design.
- **N3 (post-results):** Re-evaluation given actual results. Feeds positioning and narrative.
- **N4 (pre-submission):** Final confirmation including the latest recency sweep. Last gate before compilation.

## Project Directory

Read `pipeline-state.json` → `project_dir`.

---

## Input Requirements by Gate

| Input | N1 | N3 | N4 |
|-------|----|----|-----|
| `hypotheses.md` | required | required | required |
| `novelty-initial.md` (from Step 3) | required | — | — |
| `claim-overlap-report.md` (Pass 2+3) | required | required | required |
| `adversarial-novelty-report.md` (Pass 6) | required | re-run if shifted | required |
| `concurrent-work-report.md` (Pass 5) | required (sweep 1) | required (sweep 2) | required (sweep final) |
| `cross-field-report.md` (Pass 4) | required | — | — |
| `analysis-report.md` | — | required | required |
| `hypothesis-outcomes.md` | — | required | required |
| `novelty-reassessment.md` | — | written here | required |

---

## Execution

### Phase 1: Contribution Decomposition

Read `hypotheses.md` (for N1) or `analysis-report.md` + `hypothesis-outcomes.md` (for N3/N4) to identify the actual contribution.

Decompose into 7 novelty dimensions:

| Dimension | Applicable? | Evidence |
|-----------|------------|---------|
| Method novelty | Y/N | [source] |
| Application novelty | Y/N | [source] |
| Combination novelty | Y/N | [source] |
| Empirical novelty | Y/N | [source] |
| Theoretical novelty | Y/N | [source] |
| Scale novelty | Y/N | [source] |
| Negative result novelty | Y/N | [source] |

Mark which dimensions carry the **primary** novelty claim (must have at least one).

### Phase 2: Per-Dimension Prior Art Assessment

For each dimension marked applicable, assess the novelty status using the search pass outputs:

- **CLEAR novelty:** No prior work covers this dimension. Confidence: high if search was thorough (all 6 passes run).
- **PARTIAL novelty:** Prior work exists but differs meaningfully. Differential statement written and defensible.
- **NO novelty:** Prior work fully anticipates this dimension.

Reference documents for each dimension:
- Method novelty → `claim-overlap-report.md` (method component)
- Application novelty → `claim-overlap-report.md` (task/domain component) + `cross-field-report.md`
- Empirical novelty → `adversarial-novelty-report.md` + `claim-overlap-report.md` (result component)
- All dimensions → `concurrent-work-report.md` (for currency)

### Phase 3: Differential Articulation

For every prior paper with overlap level HIGH or MEDIUM, write (or verify) the differential statement:

> "[Prior work] does A but not B. Our work does B. The specific technical difference is [X]. This leads to [outcome difference Y]."

If this statement cannot be written for any HIGH-overlap paper → immediate KILL signal.

### Phase 4: Significance Assessment

**Problem significance:** Is the problem important? Evidence: has it been acknowledged as open in surveys or position papers? Are there downstream applications?
Rating: HIGH / MEDIUM / LOW

**Improvement magnitude:** Is the claimed improvement over prior work substantial?
- For quantitative claims: is the improvement > noise? Is effect size large (Cohen's d > 0.8)?
- For qualitative claims: is the new capability meaningfully different?
Rating: LARGE / MODERATE / MARGINAL / WITHIN NOISE

**Generalizability:** Does the contribution apply beyond a narrow special case?
Rating: BROAD / MODERATE / NARROW

**Insight value:** Does this teach something about the problem, or is it purely mechanical?
Rating: HIGH / MEDIUM / LOW

### Phase 5: Gate N3 Special Logic — Contribution Shift Detection and Venue Fit

*Only for Gate N3.*

Compare the actual results (`analysis-report.md`) against the hypothesized contribution:

1. Is the real contribution the same as what was hypothesized?
2. If not: what is the *actual* contribution revealed by the results?
3. Is the actual contribution still novel? Re-run Phase 2 targeting the actual contribution.
4. Is the actual contribution more or less significant than the hypothesized one?

If the actual contribution has shifted from the hypothesis:
- Re-run Pass 2 (claim-level search) with the actual contribution framing
- Re-run Pass 6 (adversarial search) with `mode: targeted`
- Update the novelty assessment

Write `novelty-reassessment.md` with the updated contribution framing.

### Phase 5b: Venue Appropriateness Check (N3 only)

After assessing novelty, evaluate venue fit based on the final contribution shape:

**Trigger conditions (ALL must be true to emit the warning):**
1. `target_venue` in `pipeline-state.json` is a top-tier ML venue (NeurIPS, ICML, ICLR)
2. The primary novelty dimension is empirical (not theoretical) — i.e., no formal proposition with proof is present
3. The evaluation covers a single dataset in a single task domain

**If triggered, emit this warning in `novelty-reassessment.md`:**

```
[VENUE WARNING] Single-dataset empirical NLP contribution submitted to [venue].
NeurIPS/ICML/ICLR reviewers typically expect either:
  (a) a theoretical contribution that generalizes across domains, or
  (b) evaluation on multiple datasets and/or modalities.
The current contribution may be better suited for ACL / EMNLP / NAACL, where
single-dataset NLP results are an accepted community norm.
Recommendation: Either (1) strengthen the theoretical contribution so it is
the primary vehicle for novelty, or (2) add a second dataset, or (3) redirect
to ACL/EMNLP.
This is a WARNING, not a BLOCK. The venue decision belongs to the researcher.
```

This warning is propagated into the adversarial review (Step 35) so the adversarial reviewer considers the venue fit as a potential weakness.

### Phase 6: Kill Criteria Evaluation

Run the deterministic kill check:

```bash
python scripts/kill_decision.py \
  --claim-overlap $PROJECT_DIR/claim-overlap-report.md \
  --adversarial $PROJECT_DIR/adversarial-novelty-report.md \
  --concurrent $PROJECT_DIR/concurrent-work-report.md \
  --output $PROJECT_DIR/kill-decision.json
```

Kill criteria (auto-KILL if any is true):
1. `full_anticipation`: A prior paper proposes same method + same task + comparable results
2. `marginal_differentiation`: Closest prior work differs only in minor details (hyperparameters, dataset variant) AND results are not surprisingly large
3. `failed_reposition_count >= 2`: Project has been repositioned twice and still cannot find clearly novel angle
4. `significance_collapse`: Contribution is technically novel but no evidence anyone cares
5. `concurrent_scoop`: A paper appeared during execution that fully anticipates the contribution (1 emergency reposition attempt allowed)

### Phase 7: Gate Decision

```
NOVELTY ASSESSMENT
==================
Gate: N1 / N3 / N4
Primary contribution: [which dimension(s)]
Novelty level: CLEAR / PARTIAL / INSUFFICIENT
Closest prior work: [paper reference]
Differential: [explicit statement]
Significance: HIGH / MEDIUM / LOW
Problem significance: HIGH / MEDIUM / LOW
Improvement magnitude: LARGE / MODERATE / MARGINAL / WITHIN NOISE
Generalizability: BROAD / MODERATE / NARROW
Insight value: HIGH / MEDIUM / LOW
Kill signals triggered: N
Recommendation: PROCEED / REPOSITION / PIVOT / KILL
Confidence: HIGH / MEDIUM / LOW
Evidence: [list of passes and reports contributing to this verdict]
```

### Phase 6b: Theoretical Claim Heuristic (N1 only)

*Run during reposition instruction generation whenever the gate is N1.*

Scan the contribution statement and hypotheses for keywords related to attention mechanism theory:

**Trigger keywords:** "attention faithfulness", "attention explanation", "decision boundary", "information flow", "causal role of attention", "attention swap", "attention invariance", "value subspace", "functional equivalence under attention", "attention does not affect"

**If any trigger keyword is present:**
1. Flag that the Jain & Wallace (2019) / Wiegreffe & Pinter (2019) debate (attention-is-not-explanation) is established and well-covered ground
2. Add to the REPOSITION instructions:
   - "The theoretical claim about attention mechanisms must be explicitly differentiated from Jain & Wallace (2019) adversarial swap and Wiegreffe & Pinter (2019) counter-argument. Simply showing that attention distributions can be exchanged without affecting predictions restates a known result."
   - "For the theoretical contribution to count at a venue like NeurIPS, it must be formalized as a proposition with a proof sketch, not stated as an empirical observation. State the sufficient condition precisely, prove it analytically, then validate empirically."
   - "Add this differentiation requirement to the contribution statement revision."
3. Include this in the reposition routing instructions sent back to Step 3 (`formulate-hypotheses`)

This heuristic prevents a wasted adversarial review cycle (Step 35) by surfacing the attention-theory differentiation requirement at the earliest opportunity.

---

**Decision rules:**
- **PROCEED:** CLEAR novelty on primary dimension + at least MEDIUM significance on ≥ 2 significance dimensions. No kill signals.
- **REPOSITION:** PARTIAL novelty but framing can be adjusted to emphasize a different genuinely novel dimension. Return to `/formulate-hypotheses` (N1) or `/position` (N3/N4) with specific guidance. Max 2 reposition loops.
- **PIVOT:** Insufficient novelty on the proposed contribution, but an adjacent open problem exists. Return to `/research-landscape` (N1) with specific pivot direction. Max 1 pivot.
- **KILL:** Insufficient novelty AND no viable reposition/pivot. OR any kill criterion triggered. Log and terminate.

**Loop termination:**
- N1 REPOSITION: max 2 loops back to `/formulate-hypotheses`. Third failure → KILL.
- N1 PIVOT: max 1 loop back to `/research-landscape`. No second pivot.
- N3 REPOSITION: max 1 redirect to `/position`. If still insufficient → document as limitation, proceed with reduced claims.
- N4 REPOSITION: max 1 targeted fix to `/position` + related work update. No new experiments.

---

## Output Files

### `novelty-assessment.md` (Gate N1) or `novelty-reassessment.md` (Gate N3)

```markdown
# Novelty Assessment — Gate [N1/N3/N4]

**Date:** YYYY-MM-DD
**Gate:** N1 / N3 / N4
**Decision:** PROCEED / REPOSITION / PIVOT / KILL

## Contribution Statement

[Canonical form: method → result → task → mechanism, based on actual results for N3/N4]

## Novelty Dimension Analysis

| Dimension | Applicable | Status | Evidence |
|-----------|-----------|--------|---------|
| Method | Y | CLEAR/PARTIAL/NO | [source] |
[...]

## Prior Art Differentials

### [Most threatening prior paper]
- What they do: ...
- What we do differently: [precise technical statement]
- Why our difference matters: ...

[repeat for each HIGH/MEDIUM paper]

## Significance Assessment

| Dimension | Rating | Justification |
|-----------|--------|--------------|
| Problem significance | HIGH/MEDIUM/LOW | ... |
| Improvement magnitude | LARGE/MODERATE/MARGINAL | ... |
| Generalizability | BROAD/MODERATE/NARROW | ... |
| Insight value | HIGH/MEDIUM/LOW | ... |

## Kill Criteria Check

| Criterion | Triggered | Notes |
|-----------|---------|-------|
| Full anticipation | Y/N | ... |
| Marginal differentiation | Y/N | ... |
| Failed reposition count | N / 2 | |
| Significance collapse | Y/N | ... |
| Concurrent scoop | Y/N | ... |

## Gate Decision

```
PROCEED / REPOSITION / PIVOT / KILL
```

[If REPOSITION: specific repositioning guidance]
[If PIVOT: specific pivot direction]
[If KILL: full justification + artifacts preserved]
```

---

## Kill Action

If the decision is KILL:

1. Write `$PROJECT_DIR/kill-justification.md` with full reasoning
2. Run: `python scripts/kill_decision.py --log-kill --project $PROJECT_DIR --reason "..."`
3. Preserve all artifacts: `research-landscape.md`, `claim-overlap-report.md`, all search pass outputs
4. Update `pipeline-state.json` → `status: killed`
5. Print: "Project terminated at Gate [N]. All artifacts preserved in $PROJECT_DIR. Justification: $PROJECT_DIR/kill-justification.md"

**Kill decisions are reversible.** A human can override with:
```bash
python scripts/kill_decision.py --override-kill --project $PROJECT_DIR --justification "..."
```
This sets `pipeline-state.json` → `status: kill_overridden` and logs the justification.

---

## Gate Criteria

Before marking complete:

- [ ] All input documents present for the specified gate
- [ ] Contribution decomposition completed (7 dimensions assessed)
- [ ] Per-dimension prior art assessment completed
- [ ] Differential statement written for all HIGH/MEDIUM overlap papers
- [ ] Significance assessed on all 4 dimensions
- [ ] Kill criteria evaluation run (script or manual)
- [ ] Gate decision written in structured format
- [ ] `pipeline-state.json` updated with gate N1/N3/N4 status and decision

---

## Integration

- **N1:** Follows `/recency-sweep sweep_id=1`. Blocks `/design-experiments` until PASS. REPOSITION loops to `/formulate-hypotheses`. PIVOT loops to `/research-landscape`.
- **N3:** Follows `/recency-sweep sweep_id=2`. Writes `novelty-reassessment.md`. Feeds `/position` and `/story`.
- **N4:** Follows `/recency-sweep sweep_id=final`. Blocks `/compile-manuscript` until PASS (or human override).
- **Paper Quality Verifier:** `novelty-assessment.md` is a primary input to Dimension 1.
- **Agent:** `hypothesis-generator` (opus, extended thinking) + `novelty-assessment` skill + `skeptic-agent` (opus)
