# Orchestration Refactor Plan

**Package:** 1  
**Input:** `docs/orchestration_refactor_diagnosis.md`  
**Date:** 2026-04-07  
**Scope:** Minimal refactor. No full rewrite. Four explicit contracts defined below.

---

## 1. What Must Be Solved Now vs. Deferred

### Solve in packages 2–7 (in order)

| Priority | Problem (from diagnosis) | Why now |
|---|---|---|
| P1 | W5: `reset` silently preserves loop counters | Silent data corruption; trivial fix, high blast radius |
| P1 | W2: No generation concept | Loop-backs are the highest-risk correctness gap; all other fixes build on this |
| P1 | W1: No per-step completion evidence | Gates and hard blocks are currently decorative |
| P2 | W3: Prose-fragile gate routing (loops 1–4) | Can silently skip loops on malformed docs |
| P2 | W4: Analysis proceeds on partial execution | `check_gates.py` output must become durable |
| P3 | W7: Dual-source N1 routing can diverge | Now that `kill-decision.json` exists, consume it |
| P3 | W8: No decision log | Required for lineage-safe rerun/reset |
| P4 | W6: `check_gates.py` ephemeral | Blocked on execution readiness contract |

### Defer

- Refactoring individual step skills (e.g., `/novelty-gate`, `/verify-paper`) — not needed for contracts.
- Full rewrite of `run-pipeline.md` — update incrementally in Package 7.
- Any change requiring SLURM job management — out of scope for this refactor.

---

## 2. Four Explicit Contracts

### Contract A — Step Result

A step-result artifact is written **after every step completes**, before `pipeline_state.py complete <step_id>` is called.

**Location:** `state/step-results/<step_id>.json` (inside `$PROJECT_DIR/`)

**Schema:**

```json
{
  "step_id": "<step_id>",
  "generation": 1,
  "status": "completed",
  "required_outputs": ["docs/hypotheses.md"],
  "produced_outputs": ["docs/hypotheses.md"],
  "validators_run": [],
  "validator_status": "pass | fail | not_run",
  "decision": null,
  "created_at": "2026-04-07T12:00:00Z",
  "notes": ""
}
```

**Rules:**
- `required_outputs` comes from the step's `prerequisite_files` of the NEXT step that depends on this one, OR from an explicit `required_outputs` map (added to `pipeline_state.py`).
- If any `required_outputs` file is absent, `validator_status` is `fail` and the orchestrator must not mark the step `completed` — it must mark it `failed` with reason `"required outputs missing"`.
- `generation` is the active generation at time of completion (see Contract C).
- `decision` is null unless the step is a gate (see Contract B).

**Who writes it:** The orchestrator (LLM executing `run-pipeline.md`) writes this artifact inline, before calling `pipeline_state.py complete`.  
**Who reads it:** Downstream steps check parent step's result; Package 5 enforces it for high-risk steps.

---

### Contract B — Decision

A decision record is appended to the decision log **whenever a gate produces a routing outcome** or a loop counter is incremented.

**Location:** `state/decision-log.jsonl` (inside `$PROJECT_DIR/`, append-only JSONL)

**Schema:**

```json
{
  "timestamp": "2026-04-07T12:05:00Z",
  "generation": 1,
  "step_id": "novelty-gate-n1",
  "decision_type": "routing | kill | loop_increment | override",
  "decision": "REPOSITION | PIVOT | KILL | PROCEED | PASS | REVISE | BLOCK",
  "reason": "<human-readable explanation>",
  "inputs_used": ["docs/claim-overlap-report.md", "docs/adversarial-novelty-report.md"],
  "validator_used": "kill_decision.py | prose | lm-judgment",
  "effect": "rerun_range: formulate-hypotheses -> novelty-gate-n1 | terminate | continue"
}
```

**Rules:**
- Every loop counter increment (via `increment-counter`) must produce a Decision record with `decision_type: loop_increment`.
- Every gate KILL, REPOSITION, PIVOT, PROCEED must produce a Decision record.
- `validator_used` must identify the authoritative source: `kill_decision.py`, `gap_detector.py`, `prose`, or `lm-judgment`. The last two signal fragility.
- The orchestrator writes this by appending a JSON line to `state/decision-log.jsonl`.

**Who writes it:** The orchestrator, immediately after reading a gate output.  
**Who reads it:** Package 4 (lineage), Package 7 (verification).

---

### Contract C — Generation

A generation manifest is created at pipeline init and updated whenever a loop-back routes backward past the current generation's first step.

**Location:** `state/generation-manifest.json` (inside `$PROJECT_DIR/`)

**Schema:**

```json
{
  "active_generation": 1,
  "generations": [
    {
      "generation_id": 1,
      "parent_generation": null,
      "trigger_reason": "initial run",
      "created_at": "2026-04-07T10:00:00Z",
      "active": true,
      "rerun_range": null,
      "archived_paths": []
    }
  ]
}
```

**Rules:**
- Generation 1 is created at `pipeline_state.py init` time (or on first execution if not yet present).
- A new generation is created when ANY loop-back routes backward. The new entry records the `trigger_reason` (e.g., "N1 REPOSITION #1"), the `rerun_range` (first_step → gate_step), and a pointer to archived paths.
- Before re-executing steps in the rerun range, the orchestrator archives superseded docs to `archive/gen-<N>/` (relative to `$PROJECT_DIR`). At minimum: `docs/hypotheses.md`, `docs/novelty-assessment.md`, `docs/.epistemic/` where applicable.
- `pipeline_state.py` must expose `set-generation` and `get-generation` subcommands that read/write `active_generation` in this file.
- All Step Result artifacts (Contract A) must embed the `generation` value at write time.

**Who writes it:** `pipeline_state.py init` (initial entry) and the orchestrator on loop-back (new entry).  
**Who reads it:** Orchestrator at session start, Package 4 (rerun/reset).

---

### Contract D — Execution Readiness

An execution readiness artifact is produced **at the end of `collect-results` (Step 19)** and consumed as a hard prerequisite before `analyze-results` (Step 20) starts.

**Location:** `state/execution-readiness.json` (inside `$PROJECT_DIR/`)

**Schema:**

```json
{
  "generated_at": "2026-04-07T14:00:00Z",
  "generation": 1,
  "expected_runs": 20,
  "observed_runs": 18,
  "failed_runs": 2,
  "completion_ratio": 0.9,
  "ready_for_analysis": false,
  "blocking_reason": "2 expected runs missing; completion threshold not met.",
  "check_gates_verdict": "FAIL | PASS",
  "gates_checked": ["completion", "baseline_sanity", "variance", "no_crashes"]
}
```

**Rules:**
- `check_gates.py` must be extended to write this JSON sidecar (new `--output-json` flag).
- `ready_for_analysis` is `true` only if `check_gates_verdict == "PASS"` AND `completion_ratio >= threshold` (default 1.0, configurable).
- If `ready_for_analysis == false`, the orchestrator must block Step 20 with a hard error in both interactive and auto modes.
- This file must be present and `ready_for_analysis == true` to proceed to Step 20. Its absence is treated as `ready_for_analysis == false`.
- The `analyze-results` step in `pipeline_state.py` must have `state/execution-readiness.json` added to `prerequisite_files`.

**Who writes it:** `check_gates.py --output-json` invoked by the orchestrator at the end of Step 19.  
**Who reads it:** Orchestrator before Step 20; Package 6 (execution readiness enforcement).

---

## 3. Files to Modify (in Implementation Order)

### Phase A — Primitives (Package 2)

**1. `scripts/pipeline_state.py`**

Changes:
- `reset` subcommand must also clear all loop counter fields (any key in `LOOP_COUNTERS`).
- New subcommand: `set-generation <N>` — writes `active_generation` to `state/generation-manifest.json`.
- New subcommand: `get-generation` — reads and prints `active_generation`.
- New subcommand: `write-step-result <step_id> <json_inline_or_file>` — writes/overwrites `state/step-results/<step_id>.json`.
- New subcommand: `append-decision <json_inline_or_file>` — appends one JSON line to `state/decision-log.jsonl`.
- `init` subcommand: create `state/` directory and write initial `state/generation-manifest.json` with generation 1.

No other changes to existing logic.

**Files to add (new):**
- `state/` directory structure (created by `pipeline_state.py init`).
- `state/generation-manifest.json` — written by `init`.

### Phase B — Gate Outputs (Package 3)

**2. `scripts/check_gates.py`**

Changes:
- Add `--output-json <path>` flag.
- When flag is provided, write the execution readiness JSON (Contract D schema) to that path after computing all gate verdicts.
- No change to existing console output.

**3. `commands/run-pipeline.md`**

Changes (targeted, not full rewrite):
- Step 19 (`collect-results`) execution section: add `check_gates.py --output-json $PROJECT_DIR/state/execution-readiness.json` call.
- Step 20 (`analyze-results`) prerequisite check: hard block if `state/execution-readiness.json` is absent or `ready_for_analysis == false`.
- N1 gate routing: consume `kill-decision.json` as primary source (Contract B); prose match becomes secondary confirmation only.
- All gate routing sections: add `append-decision` call after each routing decision.

### Phase C — Loop and Lineage (Package 4)

**4. `commands/run-pipeline.md`** (continued)

Changes:
- All loop-back sections: before re-executing, call `set-generation` to increment generation, write new generation-manifest entry, archive superseded docs.
- Loop-back steps: reset only the step statuses for the rerun range, not the full state.
- Add explicit rerun-range semantics: `python scripts/pipeline_state.py reset-range <from_step> <to_step>` (new subcommand).

**5. `scripts/pipeline_state.py`** (continued)

New subcommand: `reset-range <from_step_id> <to_step_id>` — resets step statuses for the specified inclusive range only. Does NOT reset loop counters (generation handles lineage).

### Phase D — Completion Contracts (Package 5)

**6. `scripts/pipeline_state.py`** (continued)

- Add `required_outputs` map: a dict keyed by step_id specifying which output files must exist for that step to be considered complete.
- The `complete` subcommand: check required outputs before writing `completed` status. On missing outputs: write `failed` with reason.

**7. `commands/run-pipeline.md`** (continued)

- Highest-risk steps (Step 3, 6, 7, 9, 20, 26, 31, 34): explicitly list required outputs in the step's execution block.
- After each high-risk step skill invocation: write Step Result artifact (Contract A) before calling `pipeline_state.py complete`.

### Phase E — Spec and Verification (Package 7)

**8. `commands/run-pipeline.md`** (final update)

- Replace all remaining prose-based routing with structured artifact reads where possible.
- Document generation semantics in the Initialization section.
- Add references to all four contracts.

---

## 4. Files to Add

| File | Created by | Package |
|---|---|---|
| `state/generation-manifest.json` | `pipeline_state.py init` | 2 |
| `state/decision-log.jsonl` | orchestrator `append-decision` | 2 |
| `state/step-results/<step_id>.json` | orchestrator per step | 2 |
| `state/execution-readiness.json` | `check_gates.py --output-json` | 3 |
| `archive/gen-<N>/` tree | orchestrator on loop-back | 4 |
| `docs/orchestration_refactor_verification.md` | Package 7 | 7 |

---

## 5. Implementation Order

```
Package 2: pipeline_state.py primitives
  ├─ Fix reset to clear loop counters
  ├─ Add set/get-generation + generation-manifest init
  ├─ Add write-step-result + append-decision subcommands
  └─ Add reset-range subcommand

Package 3: gate outputs
  ├─ check_gates.py --output-json
  ├─ run-pipeline.md: Step 19 → execution readiness
  ├─ run-pipeline.md: Step 20 hard block on execution-readiness.json
  └─ run-pipeline.md: N1 gate → consume kill-decision.json as primary

Package 4: loop and lineage
  ├─ run-pipeline.md: all loop-backs create new generation
  ├─ run-pipeline.md: archive superseded docs before loop-back
  └─ run-pipeline.md: use reset-range instead of full reset

Package 5: completion contracts
  ├─ pipeline_state.py: required_outputs map + complete-time check
  └─ run-pipeline.md: Step Result artifact for high-risk steps

Package 6: execution readiness enforcement
  └─ Verify execution-readiness.json gates analysis readiness end-to-end

Package 7: spec alignment + verification
  └─ run-pipeline.md: final update + verification doc
```

---

## 6. Compatibility Notes

- **`pipeline-state.json` version**: No schema version bump required for primitives. Loop counter bug fix (W5) is behavioral — existing files will simply have counters cleared on next `reset`. Add a note to status output: `Counters reset: yes/no`.
- **`experiment-state.json`**: Not modified in this refactor. The execution readiness contract reads it via `check_gates.py` — no direct change.
- **Existing skills**: No skill file is modified. All changes are in orchestration glue (`run-pipeline.md`) and the state manager (`pipeline_state.py`).
- **Archive paths**: `archive/gen-<N>/` is created relative to `$PROJECT_DIR`. Nothing is deleted — only copied. Superseded files remain in their original locations until the archived copy is verified.

---

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Generation-manifest diverges from actual step statuses if orchestrator crashes mid-loop | Medium | `get-generation` always re-reads from file; orchestrator checks consistency at session start |
| `check_gates.py` JSON output added but not consumed by orchestrator | Medium | Package 3 updates `run-pipeline.md` atomically with the script change |
| Archive copies of superseded docs consume significant disk | Low | Docs are typically small (<100 KB); archive only `docs/` and `.epistemic/`, not `data/` or `results/` |
| `reset` counter fix breaks an existing run that relies on counters surviving reset | Low | Counter survival across reset was always a bug; document the breaking change in Package 2 output |
| `write-step-result` in `pipeline_state.py` adds coupling between orchestrator and file format | Low | Contract A schema is versioned and stable; format changes are backwards-compatible additions only |

---

## 8. Highest-Risk Steps Requiring Completion Contracts First (Package 5 Priority)

Based on diagnosis (W1 + downstream impact):

1. **Step 3 (`formulate-hypotheses`)** — all downstream claims depend on `hypotheses.md`.
2. **Step 7 (`novelty-gate-n1`)** — gate decision controls the most expensive loops.
3. **Step 9 (`design-experiments`)** — `experiment-plan.md` is prerequisite for 6 steps.
4. **Step 20 (`analyze-results`)** — gates the entire writing phase; partial execution risk is highest here.
5. **Step 26 (`map-claims`)** — populates `claim_graph.json`; downstream hard blocks depend on it.
6. **Step 31 (`produce-manuscript`)** — three hard-blocking guards run immediately after.
7. **Step 34 (`verify-paper`)** — controls the Phase 5B revision cycle (up to 3 iterations).

---

## 9. Exact Contracts Summary (Machine Reference)

```
Contract A (Step Result):    state/step-results/<step_id>.json
Contract B (Decision):       state/decision-log.jsonl         (append-only JSONL)
Contract C (Generation):     state/generation-manifest.json
Contract D (Exec Readiness): state/execution-readiness.json
```

All paths relative to `$PROJECT_DIR`.  
All timestamps in ISO 8601 UTC (`Z` suffix).  
All JSON schemas versioned by the `$schema` field (to be added in Package 2 implementation).
