# Orchestration Refactor Workplan

A phased, low-context execution plan designed for multiple prompts without saturating the model.

Use this document as the master execution plan for a repo-aware AI model.

The work is intentionally split into prompt-sized packages. Each package has a narrow goal, a bounded file set, required outputs, stop conditions, and handoff notes for the next prompt.

## How to use this document

- Run exactly one package per prompt unless the model finishes early and still has ample context budget.
- Do not ask the model to redesign the whole system at once. Make it produce the required artifact for each package before moving on.
- Each package should begin by reloading only the minimum files listed for that package.
- If the model discovers something that invalidates the current package assumptions, it should update the package artifact and stop, rather than improvising a broad redesign.

## Global operating rules

- Always distinguish: Confirmed from code / Strong inference / Still unclear.
- Do not read the whole repository indiscriminately; keep context calibrated to the current question.
- Preserve deterministic validators and preserve useful human-readable Markdown outputs.
- Introduce structured machine-readable sidecars where orchestration needs authoritative contracts.
- Do not mark a problem fixed unless repository behavior changed and the change was verified.

## Package map

| Package | Purpose | Primary Files | Required Output | Move On When |
|---|---|---|---|---|
| 0 | Create diagnosis artifacts and bound the problem | run-pipeline.md; pipeline_state.py | orchestration_refactor_diagnosis.md | Diagnosis covers entrypoints, registry, validators, execution, state boundaries |
| 1 | Design minimal contracts and refactor plan | diagnosis file + targeted source files | orchestration_refactor_plan.md | All new contracts are explicitly defined |
| 2 | Implement state, generation, and decision primitives | pipeline_state.py + new state helpers | machine-readable state extensions | Active generation, decision log, and step-result support exist |
| 3 | Refactor gate outputs to structured routing | run-pipeline.md; kill_decision.py; gate files | authoritative gate JSON sidecars | At least one critical route uses structured decisions |
| 4 | Make loop-back explicit and lineage-safe | pipeline_state.py; run-pipeline.md | rerun/reset + archive behavior | A loop can create a new generation and archive superseded state |
| 5 | Strengthen completion contracts for high-risk steps | pipeline_state.py; validators; run-pipeline.md | completion evidence enforcement | High-risk steps fail closed without required evidence |
| 6 | Strengthen execution readiness and analysis boundary | run_experiment_autonomously.py; check_gates.py | execution-readiness contract | Analysis readiness becomes machine-checkable |
| 7 | Update orchestration spec and verify behavior | run-pipeline.md + verification docs | verification report | Structured routing/completion/rerun behavior is documented and tested |

## Package 0 — Diagnosis

### Operations

- Answer only the narrow diagnosis questions. Do not refactor yet.
- Read first: `commands/run-pipeline.md`, `scripts/pipeline_state.py`.
- Then read only the minimum extra files needed for validator coverage and execution monitoring.
- Create `docs/orchestration_refactor_diagnosis.md` with: entrypoint model, dependency model, validator map, execution monitoring model, state boundary model, confirmed weaknesses, uncertain points, exact file-change candidates.

### Questions this package must answer

- What actually starts the pipeline?
- How is the current step selected?
- Where does durable state live?
- Which validators are authoritative?
- Can analysis proceed on partial execution?
- Where do routing decisions live today?

### Stop conditions

- Do not change code in this package.
- Do not read unrelated files.
- Stop immediately after the diagnosis file is complete.

### Handoff to the next prompt

- If the diagnosis reveals a materially different architecture than expected, update the diagnosis and flag the divergence for Package 1.

## Package 1 — Minimal Refactor Design

### Operations

- Use the diagnosis file as the input contract.
- Create `docs/orchestration_refactor_plan.md`.
- Define four contracts explicitly: Step Result, Decision, Generation, Execution Readiness.
- List exact files to modify, exact files to add, implementation order, compatibility notes, and risks.

### Questions this package must answer

- What must be solved now versus deferred?
- Which state should live in `pipeline_state.py`?
- Which outputs need JSON sidecars?
- Which highest-risk steps need completion contracts first?

### Stop conditions

- Do not start coding until the plan file exists.
- Do not propose a full rewrite unless strictly necessary.

### Handoff to the next prompt

- Package 2 should implement the shared primitives first, not gate-specific behavior.

## Package 2 — State, Generation, and Decision Primitives

### Operations

- Extend `scripts/pipeline_state.py` to support richer orchestration state.
- Add machine-readable support for: active generation, generation history, structured decision references, and step-result metadata.
- Add a decision log (for example JSONL) and a generation manifest.

### Questions this package must answer

- Can the repo now represent an active generation?
- Can it record the last decision structurally?
- Can it store richer step execution metadata?

### Stop conditions

- Do not yet refactor the whole routing flow.
- Do not yet touch every step; build primitives first.

### Handoff to the next prompt

- Package 3 should consume these primitives in the critical gate path.

## Package 3 — Structured Gate Outputs

### Operations

- Keep the human-readable Markdown gate reports.
- Add authoritative machine-readable gate outputs for the highest-risk gates first: novelty gate, then design or verify-paper if feasible.
- Make routing consume structured outputs instead of prose matching where possible.
- Reduce regex fragility in `kill_decision.py` or validate the interface explicitly.

### Questions this package must answer

- Can at least one critical gate route from JSON rather than Markdown prose?
- Does malformed gate output fail loudly instead of silently defaulting benignly?

### Stop conditions

- Do not broaden the change to every possible gate if context gets tight.
- Prioritize the most fragile and highest-impact routing boundary.

### Handoff to the next prompt

- Package 4 should focus on loop semantics now that structured decisions exist.

## Package 4 — Explicit Rerun/Reset and Lineage

### Operations

- Implement explicit rerun/reset semantics for loop-back.
- A loop instruction such as re-execute steps X–Y must become a real mechanism.
- Archive superseded docs and epistemic state when a new generation is created.
- Record loop causes structurally in the decision log and generation manifest.

### Questions this package must answer

- Can a loop create a new generation?
- Can the repo archive superseded state?
- Can the intended step range actually rerun rather than being skipped?

### Stop conditions

- Do not leave loop semantics implicit inside model judgment.
- Do not overwrite critical state without lineage.

### Handoff to the next prompt

- Package 5 should use the new generation-aware state to enforce completion contracts.

## Package 5 — Completion Contracts

### Operations

- Define required outputs for the highest-risk steps first.
- For validated steps, completion must incorporate validator results.
- For non-validated steps, require at least expected outputs plus a structured step result.
- Fail closed if required completion evidence is missing.

### Questions this package must answer

- Which steps are highest-risk?
- What evidence is minimally sufficient to mark them complete?
- Which validators can become completion authorities?

### Stop conditions

- Do not try to perfect every low-risk step in one prompt.
- Prioritize hypothesis generation, claim search, design, execution boundary, analysis, map-claims, manuscript, novelty gate, verify-paper.

### Handoff to the next prompt

- Package 6 should address execution readiness and downstream safety.

## Package 6 — Execution Readiness and Analysis Boundary

### Operations

- Clarify the relationship between `pipeline-state.json` and `experiment-state.json`.
- Add a structured execution-readiness artifact.
- Make analysis readiness machine-checkable.
- Surface partial failure durably rather than implicitly.

### Questions this package must answer

- Can the repo now state expected runs, observed runs, failed runs, completion ratio, and readiness for analysis?
- Can downstream steps detect incomplete execution mechanically?

### Stop conditions

- Do not assume SLURM submission equals successful execution.
- Do not allow silent progression on partial results.

### Handoff to the next prompt

- Package 7 should align `run-pipeline.md` and then verify the refactor mechanically.

## Package 7 — Spec Alignment and Verification

### Operations

- Update `commands/run-pipeline.md` so it reflects the new contracts.
- Ensure it uses structured routing artifacts, explicit completion evidence, rerun/reset behavior, generation-aware semantics, and execution readiness checks.
- Create `docs/orchestration_refactor_verification.md` and test the new behavior mechanically.

### Questions this package must answer

- Can a high-risk step be blocked if required evidence is missing?
- Can a gate route from a structured artifact?
- Can a rerun create a new generation and archive state?
- Can execution readiness block analysis?

### Stop conditions

- Do not finish with docs only; verify real behavior changes.
- Do not declare success without a verification artifact.

### Handoff to the next prompt

- After this package, produce a concise summary of remaining limitations and next highest-leverage redesign.

## Structured artifact templates

### Step result artifact

```json
{
  "step_id": "research-init",
  "generation": 2,
  "status": "completed",
  "required_outputs": ["docs/hypotheses.md"],
  "produced_outputs": ["docs/hypotheses.md", "state/step-results/research-init.json"],
  "validators_run": ["basic-output-contract"],
  "validator_status": "pass",
  "decision": null,
  "created_at": "2026-04-07T12:00:00Z",
  "notes": "Completed with required outputs present."
}
```

### Decision log record

```json
{
  "timestamp": "2026-04-07T12:05:00Z",
  "generation": 2,
  "step_id": "novelty-gate",
  "decision_type": "routing",
  "decision": "REPOSITION",
  "reason": "High overlap with prior work and weak rebuttal.",
  "inputs_used": ["docs/claim-overlap-report.md", "docs/adversarial-novelty-report.md"],
  "validator_used": "kill_decision.py",
  "effect": "rerun_range: research-init -> novelty-gate"
}
```

### Generation manifest entry

```json
{
  "active_generation": 2,
  "generations": [
    {
      "generation_id": 1,
      "parent_generation": null,
      "trigger_reason": "initial run",
      "created_at": "2026-04-07T10:00:00Z",
      "active": false,
      "archived_paths": ["archive/gen-1/docs", "archive/gen-1/.epistemic"]
    }
  ]
}
```

### Execution readiness artifact

```json
{
  "expected_runs": 20,
  "observed_runs": 18,
  "failed_runs": 2,
  "completion_ratio": 0.9,
  "ready_for_analysis": false,
  "blocking_reason": "2 expected runs missing; completion threshold not met."
}
```

## Final acceptance checklist

- At least one critical gate now emits an authoritative machine-readable decision artifact.
- Loop-back has explicit rerun/reset semantics.
- Generation or iteration is tracked and superseded state is archived.
- At least the highest-risk steps have stronger completion contracts.
- Execution readiness is checked before analysis proceeds.
- Machine-readable decision state exists.
- `commands/run-pipeline.md` reflects the new orchestration behavior.
- Deterministic validators remain part of the control flow.
- A verification document records what was tested and what remains unresolved.
