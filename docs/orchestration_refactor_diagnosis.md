# Orchestration Refactor Diagnosis

**Package:** 0  
**Date:** 2026-04-07  
**Source files inspected:** `commands/run-pipeline.md`, `scripts/pipeline_state.py`, `scripts/kill_decision.py`, `scripts/check_gates.py`, `scripts/update_experiment_state.py`

---

## 1. Entrypoint Model

**Confirmed from code**

The pipeline has a two-layer entrypoint:

1. **Skill entrypoint**: `commands/run-pipeline.md` is a Markdown skill file loaded and executed by the LLM via the `Skill` tool. The LLM is the orchestrator; there is no Python runner script for the top-level loop.
2. **State entrypoint**: `python scripts/pipeline_state.py init --inputs RESEARCH_PROPOSAL.md` is called by the LLM-orchestrator at startup to produce `pipeline-state.json` if it doesn't exist.

Flags parsed (`--auto`, `--resume`, `--from`, `--status`, `--reset`, `--skip-online`) are interpreted by the LLM — not by a shell script. The LLM reads `pipeline-state.json` to reconstruct context at the start of each session.

**Consequence:** The "orchestrator" is a stateless LLM prompt with a side-channel to `pipeline-state.json`. It has no persistent process, no signal handling, and no crash recovery beyond what the JSON file records.

---

## 2. Step Selection Model

**Confirmed from code**

Step selection is performed by `find_next_step()` in `pipeline_state.py` (lines 554–559):

```python
def find_next_step(state: dict) -> Optional[str]:
    order = get_step_order()
    for step_id in order:
        step = state["steps"].get(step_id, {})
        if step.get("status") in ("pending", "failed"):
            return step_id
    return None
```

The step order is the static canonical list `PIPELINE_STEPS` (lines 43–317). There is no dynamic reordering mechanism.

**Loop-back mechanism**: When a gate triggers a loop-back (e.g., N1 REPOSITION → Step 3), the orchestrator re-marks prior steps as `pending` or re-executes them by invoking their skills directly — overwriting the `completed` status. This is done without a generation boundary. The state file's `updated_at` timestamp is the only trace.

**Confirmed weakness**: Loop-backs are semantically invisible to the state machine. Step 3's `completed` record from generation 1 is silently overwritten by generation 2's execution. No history, no archiving.

---

## 3. Durable State Model

**Confirmed from code**

Two distinct state files:

### `pipeline-state.json` (root or `--dir`)
Managed by `pipeline_state.py`. Contains:

```
version                   int         Always 2
created_at / updated_at   ISO strings
mode                      str         "interactive" | "auto"
project_dir               str | null  relative path to project directory
research_topic            str | null
steps                     dict        keyed by step_id, each with:
  status                  str         "pending" | "running" | "completed" | "skipped" | "failed"
  command                 str
  description             str
  prerequisite_files      list[str]
  needs_online            bool
  started_at              ISO | null
  completed_at            ISO | null
  skipped                 bool
  failure_reason          str | null
  slurm_job_id            int | null
<loop_counter_fields>     int         top-level flat fields (reposition_count, pivot_count, etc.)
```

Loop counters (`reposition_count`, `pivot_count`, `design_novelty_loops`, etc.) are top-level flat fields written by `increment-counter`. They are NOT inside the `steps` dict.

**Critical gap**: `reset` (lines 786–794) resets all `steps` entries but does NOT reset loop counter fields. A reset pipeline can silently inherit exhausted loop counters from a previous run.

### `experiment-state.json` (inside `$PROJECT_DIR/`)
Managed by `update_experiment_state.py`. Contains:

```
$schema          "experiment-state-v1"
project          str
iteration        int
status           str    "planned" | "running" | "collecting" | "analyzing" | "confirmed" | ...
active_hypothesis dict  {id, summary}
total_runs       int
jobs             dict   per-job statuses
phases           dict
failures         list
history          list
```

This file represents experiment execution state, separate from pipeline orchestration state. It is NOT updated by `pipeline_state.py`. The two files have no shared version or generation key.

**No step-result artifacts**: There is no `state/step-results/` directory, no per-step JSON completion record, no decision log, no generation manifest.

---

## 4. Validator Map

**Confirmed from code**

| Script | Inputs (markdown prose) | Output | Authoritative? |
|---|---|---|---|
| `kill_decision.py` | `claim-overlap-report.md`, `adversarial-novelty-report.md`, `concurrent-work-report.md` | `kill-decision.json` + exit code | **Yes** for KILL; partially for REPOSITION |
| `check_gates.py` | `experiment-state.json`, `results/` dir | Console report only — **no JSON sidecar** | **No** — ephemeral |
| `gap_detector.py` | `experiment-plan.md`, `analysis-report.md`, `hypotheses.md`, `competitive-landscape.md` | `gap-detection-report.md` | Deterministic script; markdown output only |
| `narrative_gap_detector.py` | `paper-blueprint.md`, `claim_graph.json`, `evidence_registry.json` | `narrative-gap-report.md` | Deterministic script; markdown output only |
| `method_reconcile.py` | `experiment-plan.md`, `configs/`, `runs/`, `experiment-state.json` | `method-reconciliation-report.md` | Deterministic; hard block on exit 1 |
| `cross_section_check.py` | `manuscript/` `.tex` files | `cross-section-report.md` | Deterministic; hard block on exit 1 |
| `check_registry_freshness.py` | `$PROJECT_DIR/.epistemic/` | Console + auto-fix | Deterministic; hard block if still exit 1 after fix |
| `consistency_oracle.py` | `manuscript/`, `.epistemic/` | `consistency_ledger.json`, `consistency-report.md` | Deterministic; hard block on exit 1 |

**Confirmed weakness**: `check_gates.py` — the only execution completeness validator — produces no durable artifact. Its verdict cannot be verified by downstream steps. The analysis phase can start without any machine-checkable evidence that `check_gates.py` passed.

---

## 5. Execution Monitoring Model

**Confirmed from code / strong inference**

Execution monitoring is split between:

- `experiment-state.json`: tracks `total_runs`, `jobs` dict (per-job status), `status` (lifecycle state), `failures` list.
- `check_gates.py`: reads `experiment-state.json` + `results/*.json` files to evaluate Completion / Baseline sanity / Variance / No-crash gates.

The pipeline step `collect-results` (Step 19) has no prerequisite files and no specified completion contract. It's a skill invocation whose outputs are unspecified in `pipeline-state.json`.

`analyze-results` (Step 20) has `prerequisite_files: []` (confirmed at line 186 of `pipeline_state.py`). This means the orchestrator will warn but not block analysis if no results exist.

**Strong inference**: There is no hard block between execution and analysis. The orchestrator in auto mode will log a warning if prerequisite files are missing but will proceed. Analysis readiness is not machine-checkable.

---

## 6. Routing Decision Model

**Confirmed from code**

Gate routing uses a **dual-source** mechanism for N1 and a **prose-only** mechanism for all other loops:

### N1 Novelty Gate (Step 7) — dual-source
1. **Prose match**: LLM reads `novelty-assessment.md` looking for the string `Decision: REPOSITION/PIVOT/KILL/PROCEED`.
2. **Exit code**: `kill_decision.py` exits 0 (PROCEED) / 1 (KILL) / 2 (REPOSITION) / 3 (PIVOT).

`kill_decision.py` also produces `kill-decision.json` (confirmed from its `--output` argument), but the orchestrator spec in `run-pipeline.md` does NOT reference this file for routing. It reads exit codes and prose separately.

The two sources can diverge if:
- The LLM-generated `novelty-assessment.md` says PROCEED but `kill_decision.py` parses the underlying reports differently.
- The outputs of `kill_decision.py` are absent (no `--output` specified in the orchestrator call path shown in `run-pipeline.md`).

### Other loop gates — prose-only
- **Loop 1 (Gap Detection)**: LLM checks `gap-detection-report.md` for `critical_gaps_found: true` — a YAML-like field in a Markdown document.
- **Loop 2 (Narrative Gap)**: LLM checks `narrative-gap-report.md` for `severity: Critical` and `type: Evidence missing` strings.
- **Loop 3 (Phase 5B)**: LLM reads `paper-quality-report.md` for `Overall Decision:` string AND `pipeline-state.json`'s `verify_paper_decision` field.
- **Loop 4 (Adversarial Review)**: LLM checks `adversarial-review-report.md` for `severity: Critical` or `severity: Major` strings.

**Confirmed weakness**: Except for the N1 gate's exit code, all routing decisions are made by the LLM interpreting prose fields in Markdown documents. There is no authoritative machine-readable gate output for loops 1, 2, 3, or 4. A malformed document silently defaults to no-loop (benign failure).

---

## 7. Confirmed Weaknesses

**W1 — No per-step completion evidence**  
`pipeline-state.json` records `status: completed` and a timestamp, but not what was produced. A step can be marked complete with no required outputs present. There are no completion contracts.

**W2 — No generation concept**  
When a gate routes backward, prior step statuses are silently overwritten. No generation ID, no archiving of superseded epistemic state (`hypotheses.md`, `novelty-assessment.md`, etc.). The state machine cannot distinguish generation-1 outputs from generation-2 outputs.

**W3 — Prose-fragile gate routing (loops 1–4)**  
Four of seven feedback loops route exclusively from LLM interpretation of prose fields. Malformed or missing documents default silently to no-loop (false negative).

**W4 — Analysis can proceed on partial execution**  
`analyze-results` (Step 20) has zero prerequisite files. `check_gates.py` produces no durable artifact. There is no hard block between execution and analysis.

**W5 — `reset` does not clear loop counters**  
`pipeline_state.py reset` (lines 786–794) resets all `steps` fields but leaves top-level counter fields (`reposition_count`, etc.) intact. A reset pipeline inherits exhausted counters from the previous run, causing immediate loop termination on the first gate trigger.

**W6 — `check_gates.py` output is ephemeral**  
The execution gate checker prints to console only. Its pass/fail verdict is not persisted anywhere. Downstream steps (Step 20+) cannot verify it was run or passed.

**W7 — Dual-source N1 routing can diverge**  
The N1 gate reads both prose from `novelty-assessment.md` and exit codes from `kill_decision.py`. These are independent evaluations. Divergence is possible and undetected. The `kill-decision.json` artifact is produced by `kill_decision.py` but is not consumed by the orchestrator's routing logic.

**W8 — No decision log**  
Individual loop decisions are not recorded structurally. Only kill events write `kill-justification.md`. No audit trail for "why did we loop back to Step 3 on generation 2."

---

## 8. Uncertain Points

**U1 — How the N1 novelty gate skill generates `novelty-assessment.md`**  
The orchestrator references this file for prose matching, but the `/novelty-gate` skill file was not inspected. It is unclear whether `kill_decision.py` is actually invoked by the skill or separately by the orchestrator.

**U2 — Whether `pipeline-state.json` is in the repo root or `$PROJECT_DIR`**  
`pipeline_state.py` writes to `--dir` (default: cwd or `$PROJECT_DIR` env var). The orchestrator refers to "pipeline-state.json in the project root" (repo root), but `$PROJECT_DIR` is the project subdirectory. Path collision risk is unclear from these two files alone.

**U3 — `run_experiment_autonomously.py` scope**  
This script exists but was not inspected. It may have its own state management that interacts with `experiment-state.json` in ways not captured here.

**U4 — Whether `verify_paper_decision` field is written to `pipeline-state.json` by `/verify-paper` or by the orchestrator**  
`run-pipeline.md` reads this field, but whether the `/verify-paper` skill writes it was not confirmed.

---

## 9. File Change Candidates

| File | Likelihood | Reason |
|---|---|---|
| `scripts/pipeline_state.py` | **High** | Must add: generation tracking, decision log, step-result metadata, counter reset on `reset` |
| `commands/run-pipeline.md` | **High** | Must add: structured gate consumption, completion evidence checks, generation semantics |
| `scripts/check_gates.py` | **Medium** | Should emit a JSON sidecar for durable execution readiness verdict |
| `scripts/kill_decision.py` | **Low** | Already produces `kill-decision.json`; orchestrator needs to consume it |
| New: `state/step-results/*.json` | **High** | Per-step completion evidence artifacts |
| New: `state/decision-log.jsonl` | **High** | Structured audit trail for routing decisions |
| New: `state/generation-manifest.json` | **High** | Generation tracking and archive pointers |
| New: `state/execution-readiness.json` | **Medium** | Durable execution readiness artifact from `check_gates.py` |
