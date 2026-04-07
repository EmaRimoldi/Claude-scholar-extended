# Orchestration Refactor Verification

**Package:** 7 (Final)
**Date:** 2026-04-07
**Refactor scope:** Packages 2–6 (state/generation primitives, structured gate routing, loop-back lineage, completion contracts, execution readiness)

---

## Summary

| # | Guarantee | Result | Caveat |
|---|-----------|--------|--------|
| G1 | Generation state is durable | PASS | — |
| G2 | Decision logging is durable | PASS | — |
| G3 | N1 gate routes from structured artifact | PASS | Other gates still prose-routed |
| G4 | Loop-back has explicit machine actions | PASS | Only N1; N2–N5 deferred |
| G5 | High-risk completion contracts are fail-closed | PASS | 7 steps covered; remainder deferred |
| G6 | Execution readiness is durable | PASS | — |
| G7 | Execution → analysis boundary enforced | PASS | — |
| G8 | Spec reflects implemented behavior | PASS (substantial) | [P]-tagged gaps documented in spec |

---

## G1 — Generation state is durable

**Test:**
```bash
python scripts/pipeline_state.py --dir /tmp/t init
python scripts/pipeline_state.py --dir /tmp/t get-generation          # → 1
python scripts/pipeline_state.py --dir /tmp/t new-generation \
  --trigger-reason "N1 REPOSITION #1" --rerun-from formulate-hypotheses --rerun-to novelty-gate-n1
python scripts/pipeline_state.py --dir /tmp/t get-generation          # → 2
cat /tmp/t/state/generation-manifest.json
```

**Expected:** `state/generation-manifest.json` persists across calls; new-generation appends an entry with `parent_generation`, `trigger_reason`, `rerun_range`; prior entry marked `active: false`.

**Observed:**
- `state/generation-manifest.json` created by `init` with generation 1
- `new-generation` incremented to generation 2 with `parent_generation: 1`, `trigger_reason: "N1 REPOSITION #1"`, `rerun_range: {from_step: "formulate-hypotheses", to_step: "novelty-gate-n1"}`
- Generation 1 entry correctly set `active: false`
- `get-generation` returned `2`

**Result:** PASS

---

## G2 — Decision logging is durable

**Test:**
```bash
python scripts/pipeline_state.py --dir /tmp/t append-decision \
  '{"step_id":"novelty-gate-n1","decision_type":"routing","decision":"PROCEED","reason":"no kill criteria","validator_used":"kill_decision.py","effect":"continue"}'
python scripts/pipeline_state.py --dir /tmp/t append-decision \
  '{"step_id":"gap-detection","decision_type":"loop_increment","decision":"LOOP","reason":"critical gaps","validator_used":"prose","effect":"rerun_range"}'
cat state/decision-log.jsonl | wc -l    # → 2
```

**Expected:** `state/decision-log.jsonl` accumulates one JSON line per `append-decision` call; each record has `timestamp` and `generation` auto-injected.

**Observed:**
- Two records written; file persists as append-only JSONL
- Auto-injected fields: `timestamp`, `generation`, `$schema`
- Records queryable as JSON objects

**Result:** PASS

---

## G3 — N1 gate routes from structured artifact

**Test:**
```bash
python scripts/kill_decision.py \
    --claim-overlap  /tmp/claim-overlap-report.md \
    --adversarial    /tmp/adversarial-novelty-report.md \
    --concurrent     /tmp/concurrent-work-report.md \
    --gate-output    /tmp/state/gates/novelty-gate-n1.json \
    --gate-id        novelty-gate-n1 \
    --generation     2
```

**Expected:** `state/gates/novelty-gate-n1.json` written with `$schema: gate-decision-v1` and all required fields: `decision_type`, `decision`, `generation`, `trigger_step`, `reason`, `inputs_used`, `validator_used`, `created_at`.

**Observed:**
- Artifact written to `state/gates/novelty-gate-n1.json`
- All 8 required fields present
- `decision: PROCEED`, `generation: 2`, `validator_used: kill_decision.py`, `$schema: gate-decision-v1`
- Run-pipeline spec Loop 0 consumes this artifact as PRIMARY routing source; prose matching on `novelty-assessment.md` is explicitly prohibited for routing (Section 7, Step 7b)

**Result:** PASS

**Caveat:** Other gates (N2, N3, N4, Gap Detection, Narrative Gap, Adversarial Review) still use prose-based routing. They are tagged `[P] deferred` in the Feedback Loop Reference table.

---

## G4 — Loop-back has explicit machine actions

**Test (simulating N1 REPOSITION):**
```bash
OLD_GEN=2
python scripts/pipeline_state.py --dir /tmp/t increment-counter reposition_count --max 2
python scripts/pipeline_state.py --dir /tmp/t new-generation \
  --trigger-reason "N1 REPOSITION #1" --rerun-from formulate-hypotheses --rerun-to novelty-gate-n1
NEW_GEN=$(python scripts/pipeline_state.py --dir /tmp/t get-generation)   # → 3
mkdir -p /tmp/t/archive/gen-$OLD_GEN/docs
cp docs/hypotheses.md /tmp/t/archive/gen-$OLD_GEN/docs/
python scripts/pipeline_state.py --dir /tmp/t add-archive-path \
  --generation $OLD_GEN "archive/gen-$OLD_GEN"
python scripts/pipeline_state.py --dir /tmp/t reset-range \
  formulate-hypotheses novelty-gate-n1
python scripts/pipeline_state.py --dir /tmp/t append-decision \
  '{"decision_type":"loop_increment","decision":"REPOSITION","generation":3,"parent_generation":2,...}'
```

**Expected:** New generation created with parent linkage; archive path recorded in gen 2 manifest entry; steps 3–7 reset to pending; decision log contains the loop event with `parent_generation`, `effect.new_generation`, `effect.archived`.

**Observed:**
- `active_generation: 3`, gen 2 entry: `active: false`, `archived_paths: ["archive/gen-2"]`, `rerun_range: {"from_step":"research-landscape","to_step":"novelty-gate-n1"}`
- Gen 3 entry: `active: true`, `parent_generation: 2`, `trigger_reason: "N1 REPOSITION #1"`
- Steps 3–7 reset to pending (5 steps: formulate-hypotheses → novelty-gate-n1)
- Decision log: `REPOSITION gen=3 parent=2 archived=archive/gen-2`
- Archive directory created with superseded docs

**Result:** PASS

**Caveat:** N2, Gap Detection, Narrative Gap, and Adversarial Review loops do NOT yet create new generations or archive superseded state. They use `reset-range` (where explicitly noted in spec) but lack full Package 4 treatment.

---

## G5 — High-risk completion contracts are fail-closed

**Test A — missing everything:**
```bash
python scripts/pipeline_state.py complete formulate-hypotheses
# → Exit 1, step marked FAILED, error lists both missing items
```

**Test B — output present, step-result missing:**
```bash
echo "# Hypotheses" > docs/hypotheses.md
python scripts/pipeline_state.py complete formulate-hypotheses
# → Exit 1, step marked FAILED, error lists missing step-result
```

**Test C — both present:**
```bash
python scripts/pipeline_state.py write-step-result formulate-hypotheses '{"status":"completed",...}'
python scripts/pipeline_state.py complete formulate-hypotheses
# → Exit 0, Completed: formulate-hypotheses
```

**Expected:** `complete` fails closed at every partial state; step is marked `failed` in `pipeline-state.json`; only succeeds when both required outputs AND step-result artifact exist.

**Observed:** All three test scenarios behaved exactly as expected.

**High-risk steps covered:**

| Step | Required outputs | Step-result required |
|------|-----------------|---------------------|
| `formulate-hypotheses` | `docs/hypotheses.md` | Yes |
| `novelty-gate-n1` | `docs/novelty-assessment.md`, `state/gates/novelty-gate-n1.json` | Yes |
| `design-experiments` | `docs/experiment-plan.md` | Yes |
| `analyze-results` | `state/execution-readiness.json`, `docs/analysis-report.md`, `docs/hypothesis-outcomes.md` | Yes |
| `map-claims` | `docs/claim-ledger.md` | Yes |
| `produce-manuscript` | `manuscript/` (non-empty dir) | Yes |
| `verify-paper` | `docs/paper-quality-report.md` | Yes |

**Result:** PASS

**Caveat:** 31 remaining steps have no required-outputs contract. Completion for those steps is accepted without evidence.

---

## G6 — Execution readiness is durable

**Test (9/10 runs complete):**
```bash
python scripts/check_gates.py \
  --experiment-state experiment-state.json \
  --results-dir results/ \
  --output-json state/execution-readiness.json \
  --generation 3
```

**Expected:** `state/execution-readiness.json` written with `$schema: execution-readiness-v1` and fields: `expected_runs`, `observed_runs`, `failed_runs`, `completion_ratio`, `ready_for_analysis`, `blocking_reason`, `check_gates_verdict`, `gates_checked`, `generation`.

**Observed:**
```json
{
  "expected_runs": 10,
  "observed_runs": 9,
  "failed_runs": 1,
  "completion_ratio": 0.9,
  "ready_for_analysis": false,
  "blocking_reason": "1 expected run(s) missing; completion 90.0% < threshold 100.0%; ...",
  "check_gates_verdict": "FAIL",
  "gates_checked": ["completion", "variance", "no_crashes"],
  "generation": 3
}
```

Also verified: when `experiment-state.json` is absent, a blocked artifact (`ready_for_analysis: false`) is still written — the failure is durable, not only console output.

**Result:** PASS

---

## G7 — Execution → analysis boundary enforced

**Test A — partial execution blocks:**
```bash
# state/execution-readiness.json exists with ready_for_analysis: false
python scripts/pipeline_state.py --dir /tmp/t check-readiness
# → Exit 1, [BLOCK] message with counts
```

**Test B — complete execution passes:**
```bash
# All 10 runs present, check_gates re-run → ready_for_analysis: true
python scripts/pipeline_state.py --dir /tmp/t check-readiness
# → Exit 0, [READY] message
```

**Test C — absent artifact blocks:**
```bash
# state/execution-readiness.json deleted
python scripts/pipeline_state.py --dir /tmp/t check-readiness
# → Exit 1, [BLOCK] "not found" message
```

**Expected:** `check-readiness` exits 1 in all non-ready states; exits 0 only when `ready_for_analysis == true`.

**Observed:** All three tests passed. Additionally:
- `REQUIRED_OUTPUTS["analyze-results"]` includes `state/execution-readiness.json`, so `complete analyze-results` also fails closed without the artifact (second enforcement layer)
- The spec's "Execution Readiness Boundary" section (Section 7) mandates `check-readiness` before `/analyze-results` is invoked, in both interactive and auto modes

**Result:** PASS

---

## G8 — Spec reflects implemented behavior

**Spot-checks on `commands/run-pipeline.md`:**

| Check | Expected | Observed |
|-------|----------|---------|
| `state/gates/novelty-gate-n1.json` appears as routing source | ≥1 reference | 16 references |
| `new-generation` subcommand in spec | ≥1 reference | 3 references |
| `reset-range` subcommand in spec | ≥1 reference | 4 references |
| `append-decision` in spec | ≥1 reference | 8 references |
| `check-readiness` in spec | ≥1 reference | 2 references |
| `write-step-result` in spec | ≥1 reference | 9 references |
| Section 8 "Completion Contracts for High-Risk Steps" | Present | Present |
| `[P] deferred` tags on un-upgraded loops | Present | 7 occurrences |
| Old prose-routing line `look for 'Decision: REPOSITION'` in N1 section | Removed | Confirmed absent |

**Result:** PASS (substantial alignment; remaining gaps explicitly tagged in spec)

---

## Remaining Limitations (Honest)

These items were diagnosed, designed, and partially or fully solved in this refactor. The following are **still open or only partially solved**:

### High priority (directly affect correctness)

1. **N2, Gap Detection, Narrative Gap, Phase 5B, Adversarial Review loops** — still use prose-based routing (`[P]` in the loop table). They do not create new generations or archive superseded state when looping back. Loop counter reset on `reset` was fixed (W5), but generation lineage was not added for these loops. Risk: loop-back overwrites prior-generation state without lineage record.

2. **Lower-risk step completion contracts** — 31 of 38 steps have no `REQUIRED_OUTPUTS` contract. Completion for those steps is accepted on status alone. Evidence of execution is not required.

3. **N3/N4 novelty gates** — `/novelty-gate gate=N3` and `/novelty-gate gate=N4` do not yet use `kill_decision.py --gate-output`. Their routing remains prose-based.

### Medium priority

4. **`check_gates.py` called but not explicitly shown in older execution guidance** — Step 19 now has an explicit `check_gates.py --output-json` call in the spec (Section 7, "Execution Readiness Boundary"). However, Step 19's own `REQUIRED_OUTPUTS` contract is empty (it is not in `STEP_RESULT_REQUIRED`). This means `collect-results` itself can be marked complete without evidence.

5. **`verify_paper_decision` field** — `run-pipeline.md` still reads `verify_paper_decision` from `pipeline-state.json` for Phase 5B loop routing (diagnosis item U4). This field is not part of the structured step-result system. Alignment deferred.

6. **No separate orchestrator runtime** — The orchestrator remains a stateless LLM prompt consuming `pipeline-state.json` as its side-channel. There is no process-level crash recovery, signal handling, or atomic state transition. This is an architectural limitation outside the scope of this refactor.

### Low priority (cosmetic / deferred)

7. **Archive contents** — `archived_paths` in the generation manifest is a pointer list, not a copy-verified set. The archive copy itself is done by bash `cp` in the orchestrator loop body; if the orchestrator crashes during archiving, the path may be recorded but incomplete.

8. **`--completion-threshold` not surfaced per-project** — Currently defaults to 1.0. A research project with SLURM variance may want a lower threshold. Configurable via `--config gate_spec.json` but not exposed in `RESEARCH_PROPOSAL.md` frontmatter.

---

## Final Assessment

**The refactor is materially complete for its targeted scope.**

The four primary weaknesses from the diagnosis that were targeted (W1–W3, W5) are all addressed:

| Weakness | Target | Status |
|---------|--------|--------|
| W1 — No per-step completion evidence | High-risk steps | Addressed (7 steps, fail-closed) |
| W2 — No generation concept | N1 loop-back | Addressed (generation manifest + archive + lineage log) |
| W3 — Prose-fragile gate routing | N1 novelty gate | Addressed (structured `state/gates/novelty-gate-n1.json`) |
| W4 — Analysis on partial execution | Step 19→20 boundary | Addressed (`check-readiness` hard block, readiness artifact) |
| W5 — `reset` preserves loop counters | `pipeline_state.py reset` | Fixed |
| W6 — `check_gates.py` ephemeral | `--output-json` flag | Fixed |
| W7 — Dual-source N1 routing divergence | `state/gates/novelty-gate-n1.json` as primary source | Fixed |
| W8 — No decision log | `state/decision-log.jsonl` | Fixed |

Weaknesses W3 (partial — other gates still prose), W2 (partial — only N1 loop has full lineage), and W1 (partial — 7 of 38 steps) are addressed for the highest-risk paths. Full coverage is deferred.

---

*Verification performed on: 2026-04-07 using Python 3.11, in `/home/erimoldi/projects/Claude-scholar-extended`.*
