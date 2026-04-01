# Pipeline input specification (formal)

This document defines the **pre-execution input contract** for the v3 research pipeline (`/run-pipeline` in [`commands/run-pipeline.md`](../commands/run-pipeline.md)). It complements **runtime state** in `pipeline-state.json` (step status, feedback-loop counters).

**Important:** this file is a **specification**, not a template you edit for your project. The **human-editable “start here” template** is **`PIPELINE_INPUTS.json`** at the repository root (edit it), and the **canonical** value the orchestrator reads for Step 1 is `research_topic` in **`pipeline-state.json`** (created via `python scripts/pipeline_state.py init --inputs PIPELINE_INPUTS.json`).

---

## 1. Goals

| Goal | Meaning |
|------|---------|
| **Determinism** | Given the same inputs and repo, the orchestrator can resolve `PROJECT_DIR`, pass a topic into Step 1, and apply consistent defaults for online steps and compute — without guessing from chat context. |
| **Separation** | **Inputs** (intent, fixed at init) vs **artifacts** (files produced by steps) vs **state** (which step is done, loop counts). |
| **Traceability** | Every input field maps to at least one step or guard; no unused fields. |

---

## 2. Reverse-engineered dependency summary

### 2.1 What each phase consumes (implicit from prior work)

| Phase | Steps (ids) | Primary upstream dependencies |
|-------|-------------|------------------------------|
| **P1** Research | `research-landscape` … `recency-sweep-1` | **research_topic** (input); then `docs/research-landscape.md`, `docs/hypotheses.md`, claim/citation reports |
| **P2** Design | `design-experiments`, `design-novelty-check` | `docs/hypotheses.md`, `docs/novelty-assessment.md`, `docs/claim-overlap-report.md` |
| **P3** Build | `scaffold` … `validate-setup` | `docs/experiment-plan.md` |
| **P4** Execute | `download-data` … `collect-results` | `docs/experiment-plan.md`, code under `src/`, `experiment-state.json` |
| **P5** Analysis & writing | `analyze-results` … `verify-paper` | Results tables, `docs/analysis-report.md`, `.epistemic/*`, manuscript tree |
| **P6** Submit | `adversarial-review` … `compile-manuscript` | `docs/concurrent-work-report.md`, `manuscript/` |

**Epistemic layer** (`.epistemic/`) is initialized in early literature steps and **must** stay consistent through map-claims, manuscript, and guards — see `run-pipeline.md` (Guards G1–G3).

### 2.2 Where ambiguity existed (underspecification)

| Issue | Before | Resolution |
|-------|--------|------------|
| Step 1 topic | Relied on chat or README title | **research_topic** required in `pipeline-state.json` via `pipeline_state.py init --topic "..."` |
| Project root | Mixed repo root vs `projects/<slug>/` | **`project_dir`** in state points at `projects/<slug>/`; all artifacts go there |
| Online steps | Unclear when network is allowed | **`execution_defaults.skip_online`** + CLI `--skip-online` |
| Compute policy | Scattered across docs | **`compute_defaults`** align with [`rules/compute-budget.md`](../rules/compute-budget.md); overridden by `docs/experiment-plan.md` once written |
| Venue / format | Implicit in manuscript step | **`constraints.target_venue`** informs `/story`, `/produce-manuscript`, `/compile-manuscript` |

---

## 3. Minimal deterministic inputs

To run **`/run-pipeline --auto`** without ad hoc clarification, these must be known **before Step 1**:

1. **`project.slug`** — filesystem anchor (`projects/<slug>/`).
2. **`research.topic`** — single canonical string for `/research-landscape` and scoped search (stored as `research_topic` in `pipeline-state.json`).

All other fields in the JSON Schema are **optional** but remove remaining degrees of freedom when set.

---

## 4. Machine-readable schema

- **JSON Schema:** [`docs/schemas/pipeline-inputs.schema.json`](schemas/pipeline-inputs.schema.json)
- **Example:** [`examples/pipeline-inputs.min.json`](../examples/pipeline-inputs.min.json)

Validate locally (optional):

```bash
# pip install check-jsonschema
check-jsonschema --schemafile docs/schemas/pipeline-inputs.schema.json examples/pipeline-inputs.min.json
```

---

## 5. Field reference → pipeline steps

Each field must appear in at least one downstream consumer. Unused fields are schema violations.

| JSON path | Role | Step ids (or scope) |
|-----------|------|---------------------|
| `schema_version` | Contract version for tooling | All (validation) |
| `project.slug` | `project_dir` → `projects/<slug>/` | All (paths) |
| `project.display_title` | Title line for README / manuscript front matter | `produce-manuscript`, `compile-manuscript`; optional elsewhere |
| `research.topic` | Pass to `/research-landscape`; scope for searches | `research-landscape`, `cross-field-search`, `formulate-hypotheses`, `claim-search`, `recency-sweep-1` |
| `research.domain_hints` | Query disambiguation | `research-landscape`, `cross-field-search`, `claim-search`, `literature-rescan`, `recency-sweep-*` |
| `constraints.target_venue` | Page limits, class, anonymization | `story`, `produce-manuscript`, `compile-manuscript` |
| `execution_defaults.skip_online` | Default for network-dependent steps | Steps with `needs_online: true` in `pipeline_state.py` when orchestrator applies skip policy |
| `compute_defaults.seeds_per_condition` | Default experiment matrix density | `design-experiments`, `plan-compute`, `run-experiment` |
| `compute_defaults.gpus_per_job` | SLURM resource shape | `plan-compute`, `run-experiment` |

**Not in this schema** (by design): `steps`, loop counters (`reposition_count`, …), SLURM job ids — they belong to **`pipeline-state.json`** as **runtime state**.

---

## 6. Mapping: schema → `pipeline-state.json`

At initialization, the orchestrator **should** set:

| State field | Source |
|-------------|--------|
| `project_dir` | `"projects/" + project.slug` |
| `research_topic` | `research.topic` |
| `mode` | From `/run-pipeline` flags (`--auto` → orchestrator behavior; may still store `"interactive"` unless you standardize persistence) |

Optional: copy `compute_defaults` and `constraints.target_venue` into state or into `projects/<slug>/docs/pipeline-inputs.resolved.json` for agents to read — not required if agents read the example YAML/JSON from the project root.

---

## 7. Moment zero → `/run-pipeline --auto`

1. Install the bundle: `bash scripts/setup.sh`
2. Initialize state with topic (required for deterministic Step 1):

   ```bash
   python scripts/pipeline_state.py init --project my-paper-slug \
     --topic "Your full research question here?"
   ```

3. Optionally add a validated **`examples/pipeline-inputs.min.json`** copy at the repo root or under `projects/<slug>/` and align fields with the schema.
4. In Claude Code: `/run-pipeline --auto`

`--auto` only removes confirmation prompts; it does **not** infer a missing **`research_topic`**.

---

## 8. `/run-experiment` (Phase 4)

No string argument is passed to the slash command; see [`commands/run-experiment.md`](../commands/run-experiment.md). Prerequisites:

| Prerequisite | Produced by (typical) |
|--------------|------------------------|
| `docs/experiment-plan.md` | `design-experiments` |
| `src/`, `configs/` | `scaffold` … `implement-metrics` |
| `experiment-state.json` | Runner / `run-experiment` |
| `docs/compute-plan.md` | `plan-compute` |

`compute_defaults` in the input schema **seed** `/design-experiments` and `/plan-compute` until `experiment-plan.md` overrides them.

---

## 9. Diagrams

| Diagram | Shows |
|---------|--------|
| [`docs/assets/aletheia-workflow.svg`](assets/aletheia-workflow.svg) | Phase **sequence**, scripts vs LLM |
| [`docs/assets/aletheia-pipeline-dependencies.svg`](assets/aletheia-pipeline-dependencies.svg) | **Artifact and control dependencies** (gates, loops) |

---

## 10. Related files

| File | Role |
|------|------|
| [`commands/run-pipeline.md`](../commands/run-pipeline.md) | Full 38-step list, guards, inline scripts |
| [`scripts/pipeline_state.py`](../scripts/pipeline_state.py) | Step definitions, `init --topic`, counters |
| [`rules/compute-budget.md`](../rules/compute-budget.md) | Seeds, GPU/job policy |
| [`docs/PROJECT_LAYOUT.md`](PROJECT_LAYOUT.md) | Directory layout |

---

## Document history

- **v1 (schema_version 1):** Formal schema file, field→step matrix, dependency diagram reference, split inputs vs runtime state.
