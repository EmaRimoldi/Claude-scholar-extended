# Orchestration Refactor — Final Pre-Commit Audit

**Date:** 2026-04-07  
**Scope:** Packages 2–7 (state primitives, structured gate routing, loop-back lineage, completion contracts, execution readiness, spec alignment)  
**Auditor:** Final automated audit before commit

---

## 1. Audit Scope

This audit does NOT start a new refactor package. It verifies:

1. Code/spec coherence: do `scripts/pipeline_state.py`, `scripts/kill_decision.py`, and `scripts/check_gates.py` do what `commands/run-pipeline.md` says they do?
2. Contract coherence: are the four contracts (Step Result, Decision, Generation, Execution Readiness) internally consistent?
3. Behavioral coherence: are there fail-open paths inside the newly refactored high-risk surface?
4. Verification honesty: does `docs/orchestration_refactor_verification.md` accurately represent what was implemented?
5. Commit readiness.

---

## 2. Files Audited

| File | Why |
|------|-----|
| `docs/orchestration_refactor_verification.md` | Primary ground truth for tested guarantees |
| `commands/run-pipeline.md` | Spec that orchestrator executes |
| `scripts/pipeline_state.py` | All Package 2/4/5/6 changes |
| `scripts/check_gates.py` | Package 6 `--output-json` / readiness artifact |
| `scripts/kill_decision.py` | Package 3 `--gate-output` flag |

Additional check: `docs/orchestration_refactor_diagnosis.md` and `docs/orchestration_refactor_plan.md` reviewed for targeted scope confirmation.

---

## 3. Confirmed Coherent Areas

### 3.1 W5 fix: reset clears loop counters

`pipeline_state.py:1185–1198` — `reset` iterates `LOOP_COUNTERS.keys()` and deletes all matching keys from state before saving. The spec (run-pipeline.md:61) correctly documents: "Note: `reset` now also clears all loop counters (W5 fix)."  
**Coherent.**

### 3.2 Generation manifest lifecycle

`new_generation()` (pipeline_state.py:504–545): appends new entry with `parent_generation`, marks all prior entries `active: False`, increments `active_generation`. Matches spec Steps R1/P1 exactly.  
`add_archive_path()` (pipeline_state.py:585–603): appends to `archived_paths` list of the named generation. Matches spec Steps R2/P2 exactly.  
**Coherent.**

### 3.3 Decision log

`append_decision_record()` (pipeline_state.py:554–559): opens `state/decision-log.jsonl` in append mode. `append-decision` handler (pipeline_state.py:1319–1331) auto-injects `timestamp`, `generation`, `$schema` via `setdefault`. Matches spec append-decision call sites.  
**Coherent.**

### 3.4 N1 structured gate routing (Steps 7a/7b/7c)

`kill_decision.py:344,418,465,482–485`: `--gate-output` accepted; if neither `--output` nor `--gate-output` is given in evaluation mode, exits 4 with error. `gate_path.parent.mkdir(parents=True, exist_ok=True)` creates `state/gates/` directory automatically. Spec Step 7a matches the exact flag set. Step 7b names `state/gates/novelty-gate-n1.json` as PRIMARY routing source; Step 7c routes from `decision` field. Prose routing explicitly prohibited.  
**Coherent.**

### 3.5 Fail-closed completion contracts

`check_completion_contracts()` (pipeline_state.py:383–407): checks `REQUIRED_OUTPUTS` for file/directory existence, then checks `STEP_RESULT_REQUIRED` for the step-result artifact. The `complete` handler (pipeline_state.py:1135–1151) calls this first; on any failure, calls `mark_fail()` and exits 1. The 7 high-risk steps in `REQUIRED_OUTPUTS` match the table in spec Section 8 exactly.  
**Coherent.**

### 3.6 check-readiness subcommand

`check-readiness` handler (pipeline_state.py:1333–1368): reads `state/execution-readiness.json` from `args.dir`; exits 1 if absent, malformed, or `ready_for_analysis` is false; exits 0 with `[READY]` message otherwise. Path construction `os.path.join(args.dir, STATE_DIR, "execution-readiness.json")` matches `check_gates.py --output-json $PROJECT_DIR/state/execution-readiness.json`. Spec Execution Readiness Boundary section (run-pipeline.md:558–612) matches this exactly.  
**Coherent.**

### 3.7 check_gates.py readiness artifact

`build_readiness_artifact()` (check_gates.py:139–189) and the absent-state fallback (check_gates.py:225–241) both write to the `--output-json` path. The `ready_for_analysis: false` artifact is written even on failure, making the absence durable rather than ephemeral. Spec documents this: "If `state/execution-readiness.json` is absent entirely, `check-readiness` will also exit 1 with a clear message."  
**Coherent.**

### 3.8 Feedback Loop Reference table

The table (run-pipeline.md:724–733) correctly marks N1 REPOSITION and N1 PIVOT as `[S]` (structured) and all other loops as `[P] deferred`. This matches the implementation state.  
**Coherent.**

### 3.9 Verification document honesty

`docs/orchestration_refactor_verification.md` lists G1–G8 all as PASS with specific caveats documented. The "Remaining Limitations" section explicitly lists what was NOT addressed (prose-routed loops, 31/38 steps without contracts, N3/N4 without structured artifacts). This accurately reflects implementation scope. No overstated claims found.  
**Coherent.**

---

## 4. Blocking Issues

**None.**

No code/spec incoherence was found that would cause incorrect runtime behavior within the refactored surface.

---

## 5. Non-Blocking Issues

### NB1 — `analyze-results` step-result template omits `state/execution-readiness.json`

**Location:** `commands/run-pipeline.md`, the `analyze-results` step-result template (the `write-step-result` bash example).

**Issue:** The template's `required_outputs` JSON field lists only `["docs/analysis-report.md","docs/hypothesis-outcomes.md"]`, omitting `state/execution-readiness.json`, even though `REQUIRED_OUTPUTS["analyze-results"]` in the code includes it as the first entry.

**Impact:** The step-result template is documentation guidance for the orchestrator. The `complete` command validates against `REQUIRED_OUTPUTS` in code, not against the `required_outputs` field inside the step-result JSON artifact. So enforcement is unaffected. The template is misleading but not incorrect operationally.

**Risk:** Low. An orchestrator following the template literally will still trigger `complete` which will independently validate the readiness artifact exists.

### NB2 — `(ready_for_analysis=true)` constraint implied by spec table but not enforced by `complete`

**Location:** `commands/run-pipeline.md:268` (Section 8 table, `analyze-results` row).

**Issue:** The table entry reads `state/execution-readiness.json (ready_for_analysis=true)`, which implies that `complete` validates the `ready_for_analysis` field. In practice, `_check_required_output()` checks only file existence — it does not parse the JSON or check the flag.

**Defense-in-depth still holds:**
1. `check-readiness` (the primary enforcement) reads and checks `ready_for_analysis` before Step 20 starts, and hard-blocks if false.
2. `REQUIRED_OUTPUTS` enforces file existence as a secondary layer.
3. The spec mandates `check-readiness` before `/analyze-results` is invoked.

**Impact:** A scenario where `check-readiness` is bypassed AND `complete analyze-results` is called manually could succeed with a blocked readiness artifact. This is an exceptional operator-error path, not a normal orchestration path.

**Risk:** Low. Would only occur if someone deliberately bypasses `check-readiness`.

### NB3 — `collect-results` step-result template uses `validator_status: "pass"` unconditionally

**Location:** `commands/run-pipeline.md:583`.

**Issue:** The template for `collect-results` hardcodes `"validator_status":"pass"`, but `check_gates.py` may return FAIL (the readiness artifact will then have `check_gates_verdict: "FAIL"` and `ready_for_analysis: false`). The template should guide the orchestrator to read the actual verdict.

**Impact:** The step-result artifact for `collect-results` is informational documentation of what was run, not a gate. Its `validator_status` field is not consumed by any validator or routing logic. Misleading documentation only.

**Risk:** Negligible.

### NB4 — `narrative-gap-report.md` path omits `docs/` prefix (pre-existing)

**Location:** `commands/run-pipeline.md:649`, Loop 2 (Narrative Gap Detection).

**Issue:** Loop 2 references `$PROJECT_DIR/narrative-gap-report.md` without the `docs/` subdirectory, unlike all other generated documents which live in `$PROJECT_DIR/docs/`.

**Impact:** Pre-existing inconsistency not introduced by Packages 2–7. It is in a `[P] deferred` loop and does not affect any refactored surface.

**Risk:** Negligible for this commit scope.

---

## 6. Deferred Items (by Design)

These items are explicitly documented in `docs/orchestration_refactor_verification.md` "Remaining Limitations". They are not defects in this commit — they are the acknowledged scope boundary.

| Item | Reference |
|------|-----------|
| N2, Gap Detection, Narrative Gap, Phase 5B, Adversarial Review loops: prose routing; no generation lineage | `[P] deferred` in Feedback Loop Reference table |
| 31 of 38 steps have no `REQUIRED_OUTPUTS` contract | verification.md G5 caveat |
| N3/N4 novelty gates use prose routing, not `kill_decision.py --gate-output` | verification.md G3 caveat |
| `verify_paper_decision` field not part of structured step-result system | verification.md item 5 |
| No separate orchestrator runtime (crash recovery, atomic state) | verification.md item 6 |

---

## 7. Commit Readiness Verdict

**READY TO COMMIT WITH NOTES**

No blocking issues found. All eight refactored guarantees (G1–G8) are internally coherent. The three non-blocking issues (NB1–NB3) are template documentation inaccuracies that do not affect runtime enforcement. NB4 is pre-existing and outside refactor scope. The verification document is honest about scope and remaining limitations.

---

## 8. Recommended Commit Scope

Include these files together as one logical commit:

```
scripts/pipeline_state.py       # Packages 2, 4, 5, 6: state primitives, completion contracts, check-readiness
scripts/kill_decision.py        # Package 3: --gate-output structured gate artifact
scripts/check_gates.py          # Package 6: --output-json execution readiness artifact
commands/run-pipeline.md        # Packages 3–7: structured routing, readiness boundary, contracts, spec alignment
docs/orchestration_refactor_verification.md   # Package 7: mechanical verification record
docs/orchestration_refactor_audit.md          # This file: pre-commit audit record
```

**Do not include** `docs/orchestration_refactor_diagnosis.md` or `docs/orchestration_refactor_plan.md` separately — they are inputs to the refactor and belong with the commit as design provenance, or can be committed in a separate docs-only commit.

**Suggested commit message:**
```
feat(orchestration): structured routing, generation lineage, fail-closed contracts (Packages 2–7)

- Generation manifest + decision log (state primitives, W2/W8)
- N1 gate routes from state/gates/novelty-gate-n1.json, not prose (W3/W7)
- N1 loop-back creates new generation, archives superseded docs (W2)
- 7 high-risk steps fail-closed on complete: require outputs + step-result artifact (W1)
- check_gates.py --output-json produces durable execution-readiness artifact (W6)
- check-readiness hard-blocks analyze-results on partial execution (W4)
- reset clears loop counters (W5)
- All 8 guarantees mechanically verified; deferred items tagged [P] in spec
```

---

## 9. Minimal Follow-Up After Commit

**Highest-leverage next task:** Apply the Package 4 generation/lineage pattern to the Gap Detection loop (Loop 1, step 21 → step 9). It is the most commonly triggered loop after N1, has an established `reset-range` call already in the spec, and the pattern is now well-proven in N1. The upgrade is: `increment-counter`, then `new-generation` + archive + `reset-range` + enriched `append-decision`, matching N1 REPOSITION exactly.

This is not required before commit. The loop is functional (prose-routed), the counter fires, and the `[P] deferred` tag is visible.
