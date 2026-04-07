---
name: run-pipeline
description: Run the full research pipeline end-to-end with human-in-the-loop checkpoints. Supports --auto mode, --resume from last checkpoint, and --from to start at a specific step. v3 pipeline — 38 steps across 6 phases with 4 feedback loops, 4 novelty gates, and epistemic infrastructure.
args:
  - name: flags
    description: "Flags: --auto (no confirmations), --resume (continue from last checkpoint), --from <step> (start at specific step), --status (show progress), --reset (reset all steps), --skip-online (skip online steps)"
    required: false
    default: ""
tags: [Pipeline, Orchestration, Research, Workflow]
---

# /run-pipeline - End-to-End Research Pipeline Orchestrator

You are now the pipeline orchestrator. Your job is to run each research pipeline step in sequence, tracking state and giving the user control between steps.

## Flag Parsing

Parse the flags from "$flags":

- `--auto` → Set mode to **auto** (run all steps without asking for confirmation)
- `--resume` → Resume from the last incomplete step in `pipeline-state.json`
- `--from <step_id>` → Start execution from the named step (e.g., `--from scaffold`)
- `--status` → Only show current pipeline status, then stop
- `--reset` → Reset all step statuses to pending, then stop
- `--skip-online` → Skip steps that require online access (research-init, check-competition)

If no flags are given, default to **interactive** mode starting from step 1 (or resuming if state exists).

## Initialization

1. Check if `pipeline-state.json` exists in the project root.
   - If it exists and `--resume` or no flags: load it and find the next pending/failed step.
   - If it exists and `--from <step>`: load it and set the starting point to that step.
   - If it does not exist: prefer the human-editable proposal **`RESEARCH_PROPOSAL.md`** (repo root). Run:
     - `python scripts/pipeline_state.py init --inputs RESEARCH_PROPOSAL.md`
     This infers `--project` (slug) and `--topic` from `RESEARCH_PROPOSAL.md`, creates `projects/<slug>/`, and writes `pipeline-state.json`.
     If the template is missing, fall back to `python scripts/pipeline_state.py init --project <topic-slug> --topic "Your research question"` (derive `<topic-slug>` from the topic). The topic string is stored as `research_topic` in `pipeline-state.json` and is the **canonical source** for Step 1 `/research-landscape` when using `/run-pipeline --auto` (no separate chat turn).

2. **Resolve PROJECT_DIR**: Read `project_dir` from `pipeline-state.json`. This is the base directory for ALL research outputs. If `project_dir` is null (legacy state), ask the user for a project slug and run `python scripts/pipeline_state.py init --force --project <slug>` to set it.

2a. **Load generation state**: Read the active generation from the generation manifest:
    ```bash
    GENERATION=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation 2>/dev/null || echo 1)
    ```
    Log: `[INIT] Active generation: $GENERATION`. If the generation manifest is absent
    (`init` was run before Package 2), it will be created with generation 1 on the next `init`.

3. **Create project folder structure** (if not already present):
   ```bash
   mkdir -p $PROJECT_DIR/{docs,configs,src,data,results/tables,results/figures,manuscript,logs,notebooks}
   mkdir -p $PROJECT_DIR/state/step-results $PROJECT_DIR/state/gates $PROJECT_DIR/state/handoffs
   ```

4. If `--status` was passed:
   - Run `python scripts/pipeline_state.py status` and display the output.
   - Also print active generation: `python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation`.
   - Stop here.

5. If `--reset` was passed:
   - Run `python scripts/pipeline_state.py reset`.
   - **Note:** `reset` now also clears all loop counters (W5 fix). Generation manifest and decision log are preserved — use `new-generation` explicitly when intentionally starting a new generation context after reset.
   - Stop here.

6. Create the logs directory for this run:
   ```bash
   mkdir -p $PROJECT_DIR/logs/pipeline-$(date +%Y-%m-%d)
   ```

**CRITICAL**: For every step below, all output files MUST be written inside `$PROJECT_DIR`. Pass the project directory to each step command. Never write research documents to the repository root.

## Pipeline Steps

Execute the following steps **in this exact order**. This is the canonical v3 sequence (38 steps).

**Phase 1: Research & Novelty Assessment (Days 1–5)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 1 | research-landscape | `/research-landscape` | Pass 1: Broad territory mapping, 50–100 papers, cluster analysis, initialize Citation Ledger | — | Yes |
| 2 | cross-field-search | `/cross-field-search` | Pass 4: Abstract problem to domain-agnostic terms, identify 3–5 adjacent fields, search with field-specific terminology, produce cross-field-report.md | research-landscape.md | Yes |
| 3 | formulate-hypotheses | `/research-init` | Hypothesis generation from gaps (hypothesis-generator agent, opus) | research-landscape.md | No |
| 4 | claim-search | `/claim-search` | Pass 2: Decompose hypothesis into atomic claims, search each independently | hypotheses.md | Yes |
| 5 | citation-traversal | `/citation-traversal` | Pass 3: Citation graph from top seed papers | research-landscape.md | Yes |
| 6 | adversarial-search | `/adversarial-search` | Pass 6: Actively attempt to kill novelty claim | claim-overlap-report.md | Yes |
| 7 | novelty-gate-n1 | `/novelty-gate gate=N1` | Gate N1: Full novelty evaluation. PROCEED/REPOSITION/PIVOT/KILL | adversarial-novelty-report.md, **cross-field-report.md** | No |
| 8 | recency-sweep-1 | `/recency-sweep sweep_id=1` | Pass 5: First recency check for concurrent work | hypotheses.md | Yes |

**Phase 2: Experiment Design (Days 5–6)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 9 | design-experiments | `/design-experiments` | Full experiment plan with baselines, ablations, power analysis | hypotheses.md, novelty-assessment.md | No |
| 10 | design-novelty-check | `/design-novelty-check` | Gate N2: Does design test the novelty claim? Baselines correct? | experiment-plan.md, claim-overlap-report.md | No |

**Phase 3: Implementation (Days 6–10)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 11 | scaffold | `/scaffold` | Generate project structure | experiment-plan.md | No |
| 12 | build-data | `/build-data` | Dataset generators and loaders | experiment-plan.md | No |
| 13 | setup-model | `/setup-model` | Load and configure models | experiment-plan.md | No |
| 14 | implement-metrics | `/implement-metrics` | Metrics and statistical tests | experiment-plan.md | No |
| 15 | validate-setup | `/validate-setup` | Pre-flight validation checklist (hard block) | — | No |

**Phase 4: Execution (Days 10–19, SLURM)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 16 | download-data | `/download-data` | Download datasets/models to cluster cache | experiment-plan.md | Yes |
| 17 | plan-compute | `/plan-compute` | GPU estimation, SLURM scripts | experiment-plan.md | No |
| 18 | run-experiment | `/run-experiment` | Submit experiment matrix, monitor, recover | — | No |
| 19 | collect-results | `/collect-results` | Aggregate outputs into structured tables | — | No |

**Phase 5A: Analysis & Epistemic Grounding (Days 19–23)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 20 | analyze-results | `/analyze-results` | Statistical analysis, figures, hypothesis outcomes | results-tables/ | No |
| 21 | gap-detection | — | Gap Detection: missing ablations/baselines → may loop back to step 9 | analysis-report.md | No |
| 22 | post-results-novelty | `/novelty-gate gate=N3` | Gate N3: Re-evaluate novelty given actual results, write novelty-reassessment.md | analysis-report.md, hypothesis-outcomes.md | No |
| 23 | recency-sweep-2 | `/recency-sweep sweep_id=2` | Pass 5 again: concurrent work during execution | novelty-reassessment.md | Yes |
| 24 | literature-rescan | — | Results-contextualized literature re-scan | analysis-report.md, novelty-reassessment.md | Yes |
| 25 | method-code-reconciliation | — | Method-Code consistency check (hard block on discrepancy) | experiment-state.json, configs/ | No |

**Phase 5B: Claim Architecture & Writing Cycle (Days 23–29)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 26 | map-claims | `/map-claims` | Claim-evidence architecture, populate Claim Dependency Graph, Skeptic Agent | analysis-report.md | No |
| 27 | position | `/position` | Contribution positioning using novelty-reassessment.md as primary input | novelty-reassessment.md, claim-ledger.md | No |
| 28 | story | `/story` | Narrative arc, paper blueprint, figure plan | positioning.md | No |
| 29 | narrative-gap-detect | — | Narrative Gap Detector: may loop back to step 20 or step 9 | paper-blueprint.md, claim_graph.json | No |
| 30 | argument-figure-align | — | Figure-argument alignment; redesign figures that don't serve their claim | figure-plan.md | No |
| 31 | produce-manuscript | `/produce-manuscript` | Full prose + Citation Audit sub-step | paper-blueprint.md, confidence_tracker.json | No |
| 32 | cross-section-consistency | — | 5-check cross-section consistency (hard block on failure) | manuscript/ | No |
| 33 | claim-source-align | — | Claim-Source Alignment Verifier (hard block on untraced claims) | manuscript/, claim_graph.json | No |
| 34 | verify-paper | `/verify-paper` | 7-dimensional quality verifier; replaces /quality-review | claim-alignment-report.md, cross-section-report.md | No |

**Phase 6: Pre-Submission & Publication (Days 29–38)**

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 35 | adversarial-review | — | Pre-submission adversarial review: 3 hostile simulated reviewers, routes upstream | manuscript/, paper-quality-report.md | No |
| 36 | recency-sweep-final | `/recency-sweep sweep_id=final` | Pass 5 final: last concurrent work check within 48h of submission | novelty-reassessment.md | Yes |
| 37 | novelty-gate-n4 | `/novelty-gate gate=N4` | Gate N4: Final novelty confirmation before compilation | concurrent-work-report.md | No |
| 38 | compile-manuscript | `/compile-manuscript` | Compile LaTeX to PDF, Overleaf ZIP, chktex | manuscript/ | No |

**Post-submission (not part of main pipeline):**
- `/presentation` — slide deck
- `/poster` — academic poster
- `/announce` — promotion content
- `/rebuttal` — actual reviewer response (after reviews received)

## Execution Loop

For each step from the starting point to the end:

### 1. Check if already done

Read the step status from `pipeline-state.json`:
- If `completed` or `skipped` → print `[OK] Step N: <command> — already done` and move to the next step.
- If `pending`, `failed`, or `running` → proceed.

### 2. Check prerequisites

For each file listed in the step's `prerequisite_files`:
- Check if the file exists inside `$PROJECT_DIR` (paths are relative to project_dir, e.g. `docs/hypotheses.md` → `$PROJECT_DIR/docs/hypotheses.md`).
- If missing: warn the user. In interactive mode, ask if they want to continue anyway or abort. In auto mode, log a warning and proceed.

### 3. Check online requirement

If the step has `needs_online: true` and `--skip-online` was passed:
- Run `python scripts/pipeline_state.py skip <step_id>`.
- Print `[--] Step N: <command> — skipped (online step, --skip-online active)`.
- Continue to next step.

### 4. Show step info (interactive mode only)

If mode is **interactive** (not `--auto`), display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step N/38: <command>
  <description>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then ask the user with three options:
- **Continue** — run this step now
- **Skip** — skip this step and move to the next
- **Abort** — stop the pipeline here (state is saved, resume later with `--resume`)

Use the AskUserQuestion tool for this confirmation.

### 5. Execute the step

**Pre-execution: context budget check**

Before marking a step as running, check whether its prerequisite files exceed the
context budget threshold:

```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR check-budget <step_id> \
  > /tmp/budget-<step_id>.json
BUDGET_EXIT=$?
```

- **Exit 0 (OK):** Load prerequisite files as full documents. Proceed normally.
- **Exit 2 (HIGH — >100K chars):** Print `[BUDGET] Step <step_id>: prereqs exceed 100K chars — loading handoffs where available.`
  - For each prerequisite step that has a handoff at `state/handoffs/<dep_step_id>.json`:
    - Load the handoff JSON and pass its `summary` + `critical_context` as inline context.
    - Log: `[HANDOFF] Loaded state/handoffs/<dep_step_id>.json (token_estimate: N) instead of full doc.`
  - For prerequisites with no handoff file: load the full Markdown as normal, with a note.
  - Available handoffs are listed in the `handoff_alternatives` field of the JSON output.

The budget check is **advisory in interactive mode** and **enforced in auto mode**
(auto mode must load handoffs rather than full docs when budget is HIGH).

1. Mark the step as running:
   ```bash
   python scripts/pipeline_state.py start <step_id>
   ```

2. Log the start:
   ```
   [>>] Step N: <command> — starting at <timestamp>
   ```

3. **Invoke the slash command** by running the corresponding skill/command. For example, if the step command is `/scaffold`, invoke the `scaffold` skill using the Skill tool.

   **Important**: Pass the default arguments as defined in the step. Do not invent arguments. Let each command use its defaults.

4. After the command completes:
   - If it succeeded (no errors, user is satisfied):

     **For high-risk steps** (see Section 8), you MUST write a step-result artifact
     BEFORE calling `complete`, or `complete` will fail closed and mark the step as
     failed:
     ```bash
     python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result <step_id> \
       '{"status":"completed","required_outputs":[...],"produced_outputs":[...],"validators_run":[...],"validator_status":"pass|not_run","decision":null,"notes":""}'
     ```
     Then:
     ```bash
     python scripts/pipeline_state.py --dir $PROJECT_DIR complete <step_id>
     ```
     If required output files or the step-result artifact are missing, `complete`
     will exit 1, mark the step `failed`, and print the missing items.

   - For non-high-risk steps, `complete` with no step-result is still accepted:
     ```bash
     python scripts/pipeline_state.py complete <step_id>
     ```

   - If it failed:
     ```bash
     python scripts/pipeline_state.py fail <step_id> --reason "<brief reason>"
     ```
     In interactive mode, ask the user: **Retry**, **Skip**, or **Abort**.
     In auto mode, log the failure and continue to the next step.

5. Log the step output to the log directory:
   - Log file: `logs/pipeline-YYYY-MM-DD/step-NN-<step_id>.log`
   - Content: timestamp, command, status, any error messages

### 6. Post-step summary

After each step completes, display a brief status line:

```
[OK] Step N/38: <command> — completed
     Next: <next_command> — <next_description>
```

**Optional handoff write** (strongly recommended for steps that produce large documents):

If the completed step produced a document >50K chars, write a handoff immediately after
`complete` succeeds. This allows downstream steps to load a compressed summary instead
of the full document when the context budget is HIGH.

```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-handoff <step_id> \
  '{"key_outputs":   {"<field>": "<1-2 sentence value>", ...},
    "summary":        "<1-3 sentence prose summary of what this step produced>",
    "critical_context": ["<fact 1>", "<fact 2>", ...],
    "token_estimate": <int — rough token count of the full output document>}'
```

**Steps that most benefit from handoffs** (write after every run):

| Step | Key fields to include in `key_outputs` |
|------|---------------------------------------|
| `research-landscape` | `total_papers`, `clusters`, `top_gaps`, `tier1_papers` |
| `cross-field-search` | `adjacent_fields`, `cross_field_gaps`, `key_papers` |
| `formulate-hypotheses` | `hypotheses` (one line each), `primary_hypothesis` |
| `design-experiments` | `conditions`, `baselines`, `metrics`, `total_runs` |
| `analyze-results` | `primary_result`, `hypothesis_verdicts`, `key_numbers` |
| `map-claims` | `claims` (one line each), `weakest_claim`, `evidence_gaps` |
| `produce-manuscript` | `sections_written`, `manuscript_path`, `claim_coverage` |

### 8. Completion Contracts for High-Risk Steps

The following steps have **completion contracts**: required output files and a required
step-result artifact. `pipeline_state.py complete` will fail closed (exit 1, mark step
`failed`) if any contract is not met.

The contracts are enforced automatically by `complete`. The orchestrator's responsibility
is to (a) ensure the skill actually produced the outputs, and (b) write a step-result
artifact before calling `complete`.

| Step ID | Required Outputs | Validator Evidence | Step-Result Required |
|---|---|---|---|
| `formulate-hypotheses` | `docs/hypotheses.md` | none (structural) | Yes |
| `novelty-gate-n1` | `docs/novelty-assessment.md`, `state/gates/novelty-gate-n1.json` | `kill_decision.py` → gate artifact | Yes |
| `design-experiments` | `docs/experiment-plan.md` | none (structural) | Yes |
| `analyze-results` | `state/execution-readiness.json` (ready_for_analysis=true), `docs/analysis-report.md`, `docs/hypothesis-outcomes.md` | `check_gates.py` → readiness artifact | Yes |
| `map-claims` | `docs/claim-ledger.md` | none (structural) | Yes |
| `produce-manuscript` | `manuscript/` (non-empty directory) | cross-section and claim-source validators run as separate inline steps | Yes |
| `verify-paper` | `docs/paper-quality-report.md` | `/verify-paper` skill produces the report | Yes |

#### Step-result templates for high-risk steps

**`formulate-hypotheses`:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result formulate-hypotheses \
  '{"status":"completed","required_outputs":["docs/hypotheses.md"],"produced_outputs":["docs/hypotheses.md"],"validators_run":[],"validator_status":"not_run","decision":null,"notes":""}'
```

**`novelty-gate-n1`** (read `decision` from the gate artifact before writing):
```bash
GATE_DECISION=$(python3 -c "import json; print(json.load(open('$PROJECT_DIR/state/gates/novelty-gate-n1.json'))['decision'])")

python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result novelty-gate-n1 \
  "{\"status\":\"completed\",\"required_outputs\":[\"docs/novelty-assessment.md\",\"state/gates/novelty-gate-n1.json\"],\"produced_outputs\":[\"docs/novelty-assessment.md\",\"docs/kill-decision.json\",\"state/gates/novelty-gate-n1.json\"],\"validators_run\":[\"kill_decision.py\"],\"validator_status\":\"pass\",\"decision\":\"$GATE_DECISION\",\"notes\":\"\"}"
```

**`design-experiments`:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result design-experiments \
  '{"status":"completed","required_outputs":["docs/experiment-plan.md"],"produced_outputs":["docs/experiment-plan.md"],"validators_run":[],"validator_status":"not_run","decision":null,"notes":""}'
```

**`analyze-results`:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result analyze-results \
  '{"status":"completed","required_outputs":["docs/analysis-report.md","docs/hypothesis-outcomes.md"],"produced_outputs":["docs/analysis-report.md","docs/hypothesis-outcomes.md"],"validators_run":[],"validator_status":"not_run","decision":null,"notes":""}'
```

**`map-claims`:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result map-claims \
  '{"status":"completed","required_outputs":["docs/claim-ledger.md"],"produced_outputs":["docs/claim-ledger.md"],"validators_run":[],"validator_status":"not_run","decision":null,"notes":""}'
```

**`produce-manuscript`:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result produce-manuscript \
  '{"status":"completed","required_outputs":["manuscript/"],"produced_outputs":["manuscript/"],"validators_run":[],"validator_status":"not_run","decision":null,"notes":"Validators (cross-section, claim-source) run as subsequent inline steps."}'
```

**`verify-paper`** (read decision from paper-quality-report.md before writing):
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result verify-paper \
  '{"status":"completed","required_outputs":["docs/paper-quality-report.md"],"produced_outputs":["docs/paper-quality-report.md"],"validators_run":["/verify-paper"],"validator_status":"pass","decision":"<PASS|REVISE — paste Overall Decision from paper-quality-report.md>","notes":""}'
```

**Fail-closed behavior:** If `complete` is called without the step-result artifact or with a
missing required output, it will:
1. Exit 1
2. Mark the step as `failed` in `pipeline-state.json` with an explicit reason string
3. Print `[FAIL-CLOSED]` with the list of missing items

To diagnose: `python scripts/pipeline_state.py status` will show the step as `[!!]` with the failure reason.

---

### 7. Gate Decision Reading and Loop Counter Management

**This section defines how to handle all 7 feedback loops.** After every gate step, read the gate's structured output and route accordingly. Do not rely solely on exit codes — also read the recommendation field from the output file.

**Counter management pattern** (same for all loops):
```bash
# Before routing backward, increment the counter:
python scripts/pipeline_state.py increment-counter <field> --max <N>
# Exit 0: counter incremented, still within limit → route backward
# Exit 1: counter has reached max → do NOT route backward, escalate instead
```

---

#### Loop 0: Gate N1 REPOSITION (Step 7 → Step 3)

After Step 7 (`/novelty-gate gate=N1`) completes:

**Step 7a: Produce the authoritative gate artifact.**

Read the active generation number, then invoke `kill_decision.py` explicitly to produce the structured gate artifact. This call is NOT optional — routing depends on it.

```bash
GENERATION=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation)

python scripts/kill_decision.py \
    --claim-overlap  $PROJECT_DIR/docs/claim-overlap-report.md \
    --adversarial    $PROJECT_DIR/docs/adversarial-novelty-report.md \
    --concurrent     $PROJECT_DIR/docs/concurrent-work-report.md \
    --pipeline-state $PROJECT_DIR/pipeline-state.json \
    --output         $PROJECT_DIR/docs/kill-decision.json \
    --gate-output    $PROJECT_DIR/state/gates/novelty-gate-n1.json \
    --gate-id        novelty-gate-n1 \
    --generation     $GENERATION
```

The exit code is informational only. **Do not route from the exit code alone.**

**Step 7b: Read the structured gate artifact (PRIMARY routing source).**

Read `$PROJECT_DIR/state/gates/novelty-gate-n1.json` and parse the `decision` field.

**If `state/gates/novelty-gate-n1.json` is absent or unparseable:**
```
[ERROR] Gate N1: state/gates/novelty-gate-n1.json is missing or malformed.
        Do NOT proceed. Do NOT fall back to novelty-assessment.md prose matching.
        Diagnose why kill_decision.py failed to write the gate artifact, then re-run Step 7a.
```
Halt in both interactive and auto modes.

`docs/novelty-assessment.md` is preserved for **human inspection only**. It is not a routing source.

**Step 7c: Route from `decision` field.**

Valid values: `PROCEED`, `PROCEED_WITH_CAUTION`, `REPOSITION`, `PIVOT`, `KILL`.
Any other value → treat as a malformed artifact: fail loud (same as absent artifact above).

**If PROCEED or PROCEED_WITH_CAUTION:**

```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
  '{"step_id":"novelty-gate-n1","decision_type":"routing","decision":"PROCEED","reason":"No kill criteria triggered","inputs_used":["docs/claim-overlap-report.md","docs/adversarial-novelty-report.md","docs/concurrent-work-report.md"],"validator_used":"kill_decision.py","effect":"continue"}'
```
Continue to Step 8.

**If REPOSITION:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR increment-counter reposition_count --max 2
```

- **Exit 0** (counter within limit — loop allowed):

  **Step R1: Create a new generation (generation transition).**
  ```bash
  OLD_GEN=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation)

  python scripts/pipeline_state.py --dir $PROJECT_DIR new-generation \
    --trigger-reason "N1 REPOSITION #<current reposition_count value>" \
    --rerun-from formulate-hypotheses \
    --rerun-to   novelty-gate-n1

  NEW_GEN=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation)
  ```
  Log: `[GEN] Generation $OLD_GEN → $NEW_GEN (N1 REPOSITION).`

  **Step R2: Archive superseded docs from generation $OLD_GEN.**
  Copy the docs produced in Steps 3–7 of generation $OLD_GEN to `archive/gen-$OLD_GEN/`.
  Nothing is deleted; originals remain in place.
  ```bash
  ARCHIVE_DIR=$PROJECT_DIR/archive/gen-$OLD_GEN
  mkdir -p $ARCHIVE_DIR/docs $ARCHIVE_DIR/state/gates

  for f in hypotheses.md claim-overlap-report.md adversarial-novelty-report.md \
            concurrent-work-report.md cross-field-report.md novelty-assessment.md \
            kill-decision.json; do
    [ -f "$PROJECT_DIR/docs/$f" ] && cp "$PROJECT_DIR/docs/$f" "$ARCHIVE_DIR/docs/$f"
  done
  [ -f "$PROJECT_DIR/state/gates/novelty-gate-n1.json" ] && \
    cp "$PROJECT_DIR/state/gates/novelty-gate-n1.json" "$ARCHIVE_DIR/state/gates/novelty-gate-n1.json"

  python scripts/pipeline_state.py --dir $PROJECT_DIR add-archive-path \
    --generation $OLD_GEN "archive/gen-$OLD_GEN"
  ```
  Log: `[ARCHIVE] Generation $OLD_GEN docs archived to archive/gen-$OLD_GEN.`

  **Step R3: Reset the rerun step range.**
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR reset-range \
    formulate-hypotheses novelty-gate-n1
  ```
  This marks Steps 3–7 as `pending` so `find_next_step()` will schedule them next.
  Loop counters are NOT reset (generation handles lineage).

  **Step R4: Log the loop decision with full lineage.**
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
    "{\"step_id\":\"novelty-gate-n1\",\"decision_type\":\"loop_increment\",\"decision\":\"REPOSITION\",\"generation\":$NEW_GEN,\"parent_generation\":$OLD_GEN,\"reason\":\"<paste reason from state/gates/novelty-gate-n1.json>\",\"inputs_used\":[\"docs/claim-overlap-report.md\",\"docs/adversarial-novelty-report.md\"],\"validator_used\":\"kill_decision.py\",\"effect\":{\"type\":\"rerun_range\",\"from_step\":\"formulate-hypotheses\",\"to_step\":\"novelty-gate-n1\",\"new_generation\":$NEW_GEN,\"archived\":\"archive/gen-$OLD_GEN\"}}"
  ```
  Log: `[LOOP] Novelty gate N1: REPOSITION — generation $OLD_GEN → $NEW_GEN, routing to formulate-hypotheses.`

  Resume the pipeline loop. The next `find_next_step()` call will return `formulate-hypotheses`.

- **Exit 1** (counter reached max = 2): Do NOT loop again. Run:
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
    '{"step_id":"novelty-gate-n1","decision_type":"kill","decision":"KILL","reason":"Gate N1 failed after 2 repositioning attempts","validator_used":"kill_decision.py","effect":"terminate"}'

  python scripts/kill_decision.py --log-kill --criterion failed_reposition \
    --project $PROJECT_DIR \
    --reason "Gate N1 failed after 2 repositioning attempts. No viable novel angle found."
  ```
  Log: `[KILL] Novelty gate N1: failed after 2 repositioning attempts.`
  Pipeline terminates.

**If PIVOT:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR increment-counter pivot_count --max 1
```

- **Exit 0** (first pivot — loop allowed):

  **Step P1: Create a new generation (generation transition).**
  ```bash
  OLD_GEN=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation)

  python scripts/pipeline_state.py --dir $PROJECT_DIR new-generation \
    --trigger-reason "N1 PIVOT #1" \
    --rerun-from research-landscape \
    --rerun-to   novelty-gate-n1

  NEW_GEN=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation)
  ```
  Log: `[GEN] Generation $OLD_GEN → $NEW_GEN (N1 PIVOT).`

  **Step P2: Archive superseded docs from generation $OLD_GEN.**
  A pivot covers all of Phase 1 (Steps 1–7), so archive the full Phase 1 output:
  ```bash
  ARCHIVE_DIR=$PROJECT_DIR/archive/gen-$OLD_GEN
  mkdir -p $ARCHIVE_DIR/docs $ARCHIVE_DIR/state/gates

  for f in research-landscape.md cross-field-report.md hypotheses.md \
            claim-overlap-report.md adversarial-novelty-report.md \
            concurrent-work-report.md novelty-assessment.md kill-decision.json; do
    [ -f "$PROJECT_DIR/docs/$f" ] && cp "$PROJECT_DIR/docs/$f" "$ARCHIVE_DIR/docs/$f"
  done
  [ -f "$PROJECT_DIR/state/gates/novelty-gate-n1.json" ] && \
    cp "$PROJECT_DIR/state/gates/novelty-gate-n1.json" "$ARCHIVE_DIR/state/gates/novelty-gate-n1.json"

  python scripts/pipeline_state.py --dir $PROJECT_DIR add-archive-path \
    --generation $OLD_GEN "archive/gen-$OLD_GEN"
  ```
  Log: `[ARCHIVE] Generation $OLD_GEN docs archived to archive/gen-$OLD_GEN.`

  **Step P3: Reset the rerun step range.**
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR reset-range \
    research-landscape novelty-gate-n1
  ```

  **Step P4: Log the loop decision with full lineage.**
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
    "{\"step_id\":\"novelty-gate-n1\",\"decision_type\":\"loop_increment\",\"decision\":\"PIVOT\",\"generation\":$NEW_GEN,\"parent_generation\":$OLD_GEN,\"reason\":\"<paste reason from state/gates/novelty-gate-n1.json>\",\"inputs_used\":[\"docs/claim-overlap-report.md\",\"docs/adversarial-novelty-report.md\"],\"validator_used\":\"kill_decision.py\",\"effect\":{\"type\":\"rerun_range\",\"from_step\":\"research-landscape\",\"to_step\":\"novelty-gate-n1\",\"new_generation\":$NEW_GEN,\"archived\":\"archive/gen-$OLD_GEN\"}}"
  ```
  Log: `[LOOP] Novelty gate N1: PIVOT — generation $OLD_GEN → $NEW_GEN, routing to research-landscape.`

  Resume the pipeline loop. The next `find_next_step()` call will return `research-landscape`.

- **Exit 1** (already pivoted once): Run:
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
    '{"step_id":"novelty-gate-n1","decision_type":"kill","decision":"KILL","reason":"Pivot limit reached after 1 pivot attempt","validator_used":"kill_decision.py","effect":"terminate"}'

  python scripts/kill_decision.py --log-kill --criterion failed_reposition \
    --project $PROJECT_DIR \
    --reason "Gate N1 pivot limit reached. No viable novel angle after full pivot."
  ```
  Pipeline terminates.

**If KILL:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
  '{"step_id":"novelty-gate-n1","decision_type":"kill","decision":"KILL","reason":"<paste reason from gate artifact>","inputs_used":["docs/kill-decision.json"],"validator_used":"kill_decision.py","effect":"terminate"}'

python scripts/kill_decision.py --log-kill \
    --project $PROJECT_DIR \
    --reason "<paste reason from state/gates/novelty-gate-n1.json reason field>"
```
Pipeline terminates immediately.

---

#### Loop 0c: Gate N2 Design-Novelty (Step 10 → Step 9)

After Step 10 (`/design-novelty-check`) completes:

1. Read `$PROJECT_DIR/docs/design-novelty-check.md` → look for `Decision:` field (PASS / REVISE / BLOCK).

**If PASS:** Continue to Step 11.

**If REVISE or BLOCK:**
```bash
python scripts/pipeline_state.py increment-counter design_novelty_loops --max 2
```
- Exit 0: Route back to Step 9. Re-execute Steps 9–10. Log: `[LOOP] Gate N2: REVISE #N — routing to design-experiments.`
- Exit 1: Do NOT loop. In interactive mode: halt and require human review. In auto mode: log `[BLOCK] Gate N2 failed after 2 attempts. Human review required.` and stop.

---

#### Execution Readiness Boundary (Step 19 → Step 20)

This is a hard gate — not a loop. It prevents `analyze-results` from starting unless
all execution runs completed cleanly. The boundary has two parts: produce the readiness
artifact at the end of Step 19, then check it before Step 20 begins.

**At the end of Step 19 (`collect-results`):**

After the `/collect-results` skill completes, run the execution gate checker and emit the
durable readiness artifact:

```bash
GENERATION=$(python scripts/pipeline_state.py --dir $PROJECT_DIR get-generation)

python scripts/check_gates.py \
    --experiment-state  $PROJECT_DIR/experiment-state.json \
    --results-dir       $PROJECT_DIR/results/ \
    --output-json       $PROJECT_DIR/state/execution-readiness.json \
    --generation        $GENERATION
# Exit code is informational. The readiness artifact is the authoritative source.
```

Then write the step-result and mark Step 19 complete normally:
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-step-result collect-results \
  '{"status":"completed","required_outputs":[],"produced_outputs":["state/execution-readiness.json"],"validators_run":["check_gates.py"],"validator_status":"pass","decision":null,"notes":""}'

python scripts/pipeline_state.py --dir $PROJECT_DIR complete collect-results
```

**Before Step 20 (`analyze-results`) starts:**

Check readiness before invoking `/analyze-results`. This is a hard block in both
interactive and auto modes:

```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR check-readiness
```

- **Exit 0** (`[READY]`): Proceed to invoke `/analyze-results`.
- **Exit 1** (`[BLOCK]`): Do NOT start Step 20.
  - The artifact at `$PROJECT_DIR/state/execution-readiness.json` contains the exact
    blocking reason and counts.
  - In **interactive** mode: display the blocking reason and ask the user:
    **Retry collection**, **Force-proceed** (exceptional override), or **Abort**.
    Force-proceed requires explicit user confirmation and logs a warning.
  - In **auto** mode: log `[BLOCK] analyze-results blocked — execution not ready.
    See state/execution-readiness.json.` and stop the pipeline.
  - **Do NOT fall back to running analysis on partial results.**

If `state/execution-readiness.json` is absent entirely (e.g., `check_gates.py` was not
called at the end of Step 19), `check-readiness` will also exit 1 with a clear message.
This satisfies the `REQUIRED_OUTPUTS` contract for `analyze-results` (the artifact must
exist for `complete` to succeed anyway).

---

#### Loop 1: Gap Detection (Step 21 → Step 9)

> **Status [P] — prose routing, generation lineage deferred.** This loop routes from a Markdown
> field (`critical_gaps_found: true` in `gap-detection-report.md`). It does not yet create a new
> generation or archive superseded state when looping back. Upgrade to structured lineage is deferred.

Step 21 is an inline orchestrator sub-task. After running it:

1. Check `$PROJECT_DIR/docs/gap-detection-report.md` for `critical_gaps_found: true` or presence of any CRITICAL severity gap entries.

**If no critical gaps:** Continue to Step 22.

**If critical gaps found:**
```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR increment-counter gap_detection_loops --max 2
```
- Exit 0: Log the loop decision:
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
    '{"step_id":"gap-detection","decision_type":"loop_increment","decision":"LOOP","reason":"Critical gaps found","validator_used":"prose","effect":"rerun_range: design-experiments -> gap-detection"}'
  ```
  Route back to Step 9. Reset the range and re-execute Steps 9–21:
  ```bash
  python scripts/pipeline_state.py --dir $PROJECT_DIR reset-range design-experiments gap-detection
  ```
  Log: `[LOOP] Gap detection: critical gaps found, loop #N — routing to design-experiments.`
- Exit 1: Do NOT loop. Continue forward with gaps noted as limitations. Log: `[WARN] Gap detection triggered 2 loops. Proceeding with current evidence; remaining gaps documented as limitations.`

---

#### Loop 2: Narrative Gap Detection (Step 29 → Step 20 or Step 9)

Step 29 is an inline orchestrator sub-task. After running it:

1. Check `$PROJECT_DIR/narrative-gap-report.md` for any gap with `severity: Critical` and `type: Evidence missing`.

**If no critical evidence-missing gaps:** Continue to Step 30.

**If critical evidence-missing gaps:**
```bash
python scripts/pipeline_state.py increment-counter narrative_gap_loops --max 2
```
- Exit 0: Determine routing:
  - If gap's `route_to` field is `experiments` (requires new data): Route to Step 9. Re-execute Steps 9–29. Log: `[LOOP] Narrative gap: missing evidence requires new experiments, loop #N — routing to design-experiments.`
  - If gap's `route_to` is `analysis` (can be derived from existing results): Route to Step 20. Re-execute Steps 20–29. Log: `[LOOP] Narrative gap: missing evidence requires re-analysis, loop #N — routing to analyze-results.`
- Exit 1: Do NOT loop. Document remaining critical gaps as Limitations. Log: `[WARN] Narrative gap loops exhausted. Proceeding with gaps documented as limitations.`

---

#### Loop 3: Phase 5B Revision Cycle (Step 34 → Steps 26–33)

This loop is already correctly implemented by `/verify-paper`. The `verify_paper_cycle` counter is written by the command itself. The orchestrator should:

1. After Step 34 completes, read `$PROJECT_DIR/manuscript/paper-quality-report.md` for `Overall Decision:`.
2. Also read `pipeline-state.json` → `verify_paper_decision` and `verify_paper_cycle`.

**If PASS:** Continue to Step 35.

**If REVISE or BLOCK:**
```bash
python scripts/pipeline_state.py get-field verify_paper_cycle
```
- Value < 3: Route to the upstream step indicated in the report's `route_to` field. Re-run affected steps. Re-run `/verify-paper --dimensions X,Y` on affected dimensions only.
- Value >= 3: CRITICAL remaining → halt and escalate to human. MAJOR only → document in cover letter and continue.

---

#### Loop 4: Adversarial Review (Step 35 → varies)

Step 35 is an inline orchestrator sub-task. After running it:

1. Check `$PROJECT_DIR/adversarial-review-report.md` for findings with `severity: Critical` or `severity: Major`.

**If no Critical/Major findings:** Continue to Step 36.

**If Critical/Major findings:**
```bash
python scripts/pipeline_state.py increment-counter adversarial_review_cycles --max 2
```
- Exit 0: Find the earliest `route_to` step among Critical findings. Route there. Re-execute forward through Step 35. Log: `[LOOP] Adversarial review: critical finding, cycle #N — routing to step N.`
- Exit 1: Do NOT loop. Continue to Step 36. Log critical/major findings in `adversarial-review-report.md` as known weaknesses for cover letter.

---

**Kill decision (any gate, any loop):**

For the N1 gate, the kill is signalled by `decision: "KILL"` in `state/gates/novelty-gate-n1.json`
(the authoritative source — see Section 7 Loop 0). For other gates that have not yet been
upgraded to structured routing, a `kill_decision.py` exit 1 serves as the signal.

When a KILL is reached:
1. Append a kill decision record to the decision log:
   ```bash
   python scripts/pipeline_state.py --dir $PROJECT_DIR append-decision \
     '{"step_id":"<gate_step>","decision_type":"kill","decision":"KILL","reason":"<reason>","validator_used":"kill_decision.py","effect":"terminate"}'
   ```
2. Print: `[KILL] Project terminated at step N. Reason: <reason>. Artifacts preserved in $PROJECT_DIR.`
3. Run `python scripts/pipeline_state.py status` and display.
4. Print: `Human override: python scripts/kill_decision.py --override-kill --human-override --project $PROJECT_DIR --justification "..."`
5. Stop pipeline execution.

## Feedback Loop Routing Reference

Summary table for quick reference. For full logic, see "Gate Decision Reading" section above.

**Upgrade status:**
- **[S]** = Structured routing: routes from `state/gates/<gate>.json` (Package 3); loop-back creates new generation, archives superseded docs, calls `reset-range` (Package 4); decision logged (Package 2).
- **[P]** = Prose routing: routes from LLM-interpreted Markdown. Fragility risk. Upgrade deferred.

| Loop | Counter field | Trigger step | Target | Max | Termination on exceed | Status |
|------|--------------|-------------|--------|-----|----------------------|--------|
| N1 REPOSITION | `reposition_count` | Step 7 | Step 3 | 2 | `kill_decision.py --criterion failed_reposition` | **[S]** |
| N1 PIVOT | `pivot_count` | Step 7 | Step 1 | 1 | `kill_decision.py --criterion failed_reposition` | **[S]** |
| N2 Design-Novelty | `design_novelty_loops` | Step 10 | Step 9 | 2 | Halt, human review required | **[P]** deferred |
| Gap Detection | `gap_detection_loops` | Step 21 | Step 9 | 2 | Continue with gaps as limitations | **[P]** deferred |
| Narrative Gap | `narrative_gap_loops` | Step 29 | Step 20 or 9 | 2 | Continue with gaps as limitations | **[P]** deferred |
| Phase 5B Revision | `verify_paper_cycle` | Step 34 | Steps 26–33 | 3 | CRITICAL→escalate; MAJOR→cover letter | **[P]** deferred |
| Adversarial Review | `adversarial_review_cycles` | Step 35 | varies | 2 | Continue with weaknesses documented | **[P]** deferred |

**Kill decision:** See "Kill decision" section above. N1 kill is routed from `state/gates/novelty-gate-n1.json`; other gate kills are routed from `kill_decision.py` exit codes until upgraded.

## Pipeline Completion

When all steps are done (or the user aborts), display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pipeline Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then run `python scripts/pipeline_state.py status` and display the result.

If aborted, remind the user: `Resume later with: /run-pipeline --resume`

## Inline Step Invocations and Output Templates

These are the execution instructions for the inline steps (steps with `—` in the Command column). Steps that have a deterministic Python script **must** invoke the script — do not LLM-generate the output. Steps without a script use the output template as the generation format.

All output paths are in `$PROJECT_DIR/` (project root). No `docs/` prefix.

---

### Step 21: gap-detection-report.md (deterministic script)

**REQUIRED: Run the script. Do not generate this output manually.**

```bash
python scripts/gap_detector.py \
  --experiment-plan $PROJECT_DIR/experiment-plan.md \
  --analysis-report $PROJECT_DIR/analysis-report.md \
  --hypotheses      $PROJECT_DIR/hypotheses.md \
  --landscape       $PROJECT_DIR/competitive-landscape.md \
  --output          $PROJECT_DIR/gap-detection-report.md
```

Exit codes:
- `0` → No critical gaps. Continue to Step 22.
- `1` → Critical gaps found. Read `gap-detection-report.md` → run Loop 1 counter logic (see Loop 1 section).
- `2` → Input file error. Check prerequisite files before retrying.

---

### Step 24: literature-rescan.md

```markdown
# Literature Re-scan Report (Step 24)

**Date:** YYYY-MM-DD
**Scope:** Papers published since [Step 1 date] relevant to actual findings
**Databases searched:** [list]

## New Papers Found

### [Author et al., YYYY] — [Title]
- **URL / arXiv ID:** ...
- **Why now relevant:** [connection to actual results, not original hypothesis]
- **Overlap with contribution:** [direct competition / complementary / cites differently]
- **Action required:** [cite and differentiate / add to related work / no action]
- **cite_key:** [added to citation_ledger.json as: key]

## Updated Positioning
[How the related work section will change given new papers]

## Related Work Delta
[Diff from what the related work section would have said after Step 1]

## Gate Status
- Databases searched: ≥ 2 ✓/✗
- Time window covers post-Step-1 papers ✓/✗
- At least one query derived from actual findings ✓/✗
- New papers added to citation_ledger.json ✓/✗ (N added)
```

---

### Step 25: method-reconciliation-report.md (deterministic script)

**REQUIRED: Run the script. Hard block on any CRITICAL discrepancy.**

```bash
python scripts/method_reconcile.py \
  --experiment-plan   $PROJECT_DIR/experiment-plan.md \
  --configs           $PROJECT_DIR/configs/ \
  --runs              $PROJECT_DIR/runs/ \
  --experiment-state  $PROJECT_DIR/experiment-state.json \
  --output            $PROJECT_DIR/method-reconciliation-report.md
```

Exit codes:
- `0` → No discrepancies. Continue to Step 26.
- `1` → CRITICAL discrepancy found (manuscript says X, config/log says Y). **Hard block.** Resolve all discrepancies before proceeding — either update the config or update the planned manuscript description. Rerun until exit 0.
- `2` → Input file error.

---

### Step 29: narrative-gap-report.md (deterministic script)

**REQUIRED: Run the script. Do not generate this output manually.**

```bash
python scripts/narrative_gap_detector.py \
  --blueprint         $PROJECT_DIR/paper-blueprint.md \
  --figure-plan       $PROJECT_DIR/figure-plan.md \
  --claim-graph       $PROJECT_DIR/.epistemic/claim_graph.json \
  --evidence-registry $PROJECT_DIR/.epistemic/evidence_registry.json \
  --figures-dir       $PROJECT_DIR/figures/ \
  --output            $PROJECT_DIR/narrative-gap-report.md
```

Exit codes:
- `0` → No critical evidence-missing gaps. Continue to Step 30.
- `1` → Critical evidence-missing gaps found. Read `narrative-gap-report.md` → run Loop 2 counter logic (see Loop 2 section).
- `2` → Input file error.

---

### Step 30: figure-alignment-report.md

```markdown
# Figure-Argument Alignment Report (Step 30)

**Date:** YYYY-MM-DD
**Figures evaluated:** N

## Figure Inventory

| Figure | Assigned Claim | Takeaway Message | Alignment | Action |
|--------|---------------|-----------------|-----------|--------|
| fig_1.pdf | C3: method outperforms baselines | Bar chart shows +4.2% | aligned | none |
| fig_2.pdf | C5: ablation isolates component X | Table hard to read | misaligned | redesign |

## Misaligned Figures (redesign required)

### [Figure filename]
- **Assigned claim:** [claim from paper-blueprint.md]
- **Current takeaway:** [what the figure currently communicates]
- **Required takeaway:** [what it should communicate to support the claim]
- **Redesign instruction:** [specific change: rotate axes / highlight bar / add CI / change color]
- **Status after redesign:** [pending / complete]

## Gate Status
- All figures rated aligned ✓/✗
- Redesigned figures written to figures/ ✓/✗ (N redesigned)
- figure-plan.md updated ✓/✗
```

---

### Step 32: cross-section-report.md (deterministic script)

**REQUIRED: Run the script. Hard block if any of the 5 sub-checks fail.**

```bash
python scripts/cross_section_check.py \
  --manuscript $PROJECT_DIR/manuscript/ \
  --output     $PROJECT_DIR/cross-section-report.md
```

Exit codes:
- `0` → All 5 sub-checks pass. Continue to Step 33.
- `1` → One or more sub-checks FAIL. **Hard block.** Read `cross-section-report.md` for specific failure locations. Fix in manuscript and rerun until exit 0.
- `2` → No `.tex` files found in manuscript directory.

---

### Step 35: adversarial-review-report.md (with 3 reviewer profiles)

```markdown
# Adversarial Review Report (Step 35)

**Date:** YYYY-MM-DD
**Reviewer profiles:** Novelty Skeptic, Methods Pedant, Clarity Judge
**Revision cycle:** N

## Reviewer 1: Novelty Skeptic

**Profile:** Hostile reviewer who questions contribution novelty; cites obscure prior work.

### Major Objections

#### [OBJ-1] [Short title of objection]
- **Severity:** Critical / Major / Minor
- **Objection:** "[Verbatim simulated reviewer text — write as hostile peer reviewer]"
- **Basis:** [Which prior work or observation supports this objection]
- **Route to:** [step number — e.g., Step 3 (hypotheses), Step 27 (position)]
- **Recommended response:** [Specific manuscript change that addresses this objection]
- **Status:** Unresolved / Resolved (see [section/file])

---

## Reviewer 2: Methods Pedant

**Profile:** Demands methodological rigor; flags every statistical weakness.

### Major Objections

#### [OBJ-2] [Short title]
- **Severity:** Critical / Major / Minor
- **Objection:** "..."
- **Basis:** ...
- **Route to:** [e.g., Step 9 (design), Step 20 (re-analysis)]
- **Recommended response:** ...
- **Status:** Unresolved / Resolved

---

## Reviewer 3: Clarity Judge

**Profile:** Evaluates whether a reader unfamiliar with the subfield can follow the paper.

### Major Objections

#### [OBJ-3] [Short title]
- **Severity:** Critical / Major / Minor
- **Objection:** "..."
- **Basis:** ...
- **Route to:** [e.g., Step 31 (manuscript revision)]
- **Recommended response:** ...
- **Status:** Unresolved / Resolved

---

## Aggregated Critical Items

| ID | Reviewer | Severity | Route to | Status |
|----|----------|----------|----------|--------|
| OBJ-1 | Novelty Skeptic | Critical | Step 27 | Unresolved |
| OBJ-2 | Methods Pedant | Major | Step 9 | Unresolved |

## Loop Routing

```bash
python scripts/pipeline_state.py increment-counter adversarial_review_cycles --max 2
# Exit 0: route to earliest Critical item's route_to step
# Exit 1: document remaining weaknesses and continue to Step 36
```

## Known Weaknesses for Cover Letter
[Critical/Major items that could not be resolved — document here for cover letter]
```

---

## Deterministic Guards

These three checks are not pipeline steps — they are mandatory guards that run at specific transition points. They do not appear in the step table but must be executed at the indicated points.

---

### Guard G1: Epistemic Registry Freshness — run before Step 26 (map-claims)

Step 26 reads all four `.epistemic/` files heavily. Run this guard after Step 25 completes and before starting Step 26.

```bash
python scripts/check_registry_freshness.py --project $PROJECT_DIR
```

- **Exit 0** → `.epistemic/` files are consistent. Proceed to Step 26.
- **Exit 1** → Stale or inconsistent entries found. First attempt auto-repair:
  ```bash
  python scripts/check_registry_freshness.py --project $PROJECT_DIR --fix
  ```
  Re-run the check. If still exit 1, halt and investigate manually — do not proceed to Step 26 with a corrupt epistemic layer.
- **Exit 2** → `.epistemic/` directory missing. Re-run from Step 1 or initialize manually.

---

### Guard G2: Consistency Oracle Sweep — run after Step 31 (produce-manuscript)

After the manuscript is generated, verify that all claim confidence levels are reflected correctly in the prose.

```bash
python scripts/consistency_oracle.py sweep \
  --project    $PROJECT_DIR \
  --manuscript $PROJECT_DIR/manuscript/ \
  --output     $PROJECT_DIR/.epistemic/consistency_ledger.json \
  --report     $PROJECT_DIR/consistency-report.md
```

- **Exit 0** → No critical confidence-hedging mismatches. Proceed to Step 32.
- **Exit 1** → Critical mismatches found (assertive prose for low-confidence claims). Read `consistency-report.md` for specific sentences. Route back to Step 31 for targeted rewrite of the flagged sentences. Rerun until exit 0.

---

### Guard G3: Consistency Oracle Sweep (refresh) — run before Step 35 (adversarial-review)

After the Phase 5B revision cycle, re-sweep to ensure no consistency regressions were introduced during manuscript edits.

```bash
python scripts/consistency_oracle.py sweep \
  --project    $PROJECT_DIR \
  --manuscript $PROJECT_DIR/manuscript/ \
  --output     $PROJECT_DIR/.epistemic/consistency_ledger.json \
  --report     $PROJECT_DIR/consistency-report.md
```

- **Exit 0** → Consistent. Proceed to Step 35.
- **Exit 1** → Regressions found. Route back to the earliest step indicated in `consistency-report.md`. Fix and re-sweep before running adversarial review.

---

## Important Rules

1. **Never duplicate command logic.** Always invoke the actual slash command via the Skill tool. The orchestrator only manages sequencing and state.
2. **Always update pipeline-state.json** before and after each step.
3. **Always create log files** for each step.
4. **Respect the user's choice** in interactive mode. If they say abort, stop immediately.
5. **Steps marked with `—` in the Command column** (gap-detection, narrative-gap-detect, literature-rescan, method-code-reconciliation, argument-figure-align, cross-section-consistency, claim-source-align, adversarial-review) are invoked inline by the orchestrator — they do not have separate slash commands. For steps with a deterministic script, invoke the script as specified in "Inline Step Invocations and Output Templates". For LLM-generated steps, use the output template as the generation format.
6. **Epistemic infrastructure** (`$PROJECT_DIR/.epistemic/`) is initialized at Step 1 and updated throughout. Check that `evidence_registry.json`, `citation_ledger.json`, `claim_graph.json`, and `confidence_tracker.json` are being updated at each evidence-producing step.

## Examples

```bash
# Interactive mode (default) — asks before each step
/run-pipeline

# Full auto — runs everything without confirmation
/run-pipeline --auto

# Resume from where you left off
/run-pipeline --resume

# Start from a specific step
/run-pipeline --from scaffold

# Just check status
/run-pipeline --status

# Reset and start fresh
/run-pipeline --reset

# Skip online steps (offline mode)
/run-pipeline --skip-online
```

## Related Commands

- Individual step commands: `/research-init`, `/design-experiments`, `/scaffold`, etc.
- State script: `python scripts/pipeline_state.py status`
- Experiment iteration state: `$PROJECT_DIR/experiment-state.json` (managed by `/run-experiment`)
- Project directory: All research outputs live in `$PROJECT_DIR` (stored as `project_dir` in `pipeline-state.json`)
