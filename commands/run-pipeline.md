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
   - If it does not exist: run `python scripts/pipeline_state.py init --project <topic-slug>` to create it. Derive `<topic-slug>` from the research topic (kebab-case, e.g. `sparse-hate-explain`).

2. **Resolve PROJECT_DIR**: Read `project_dir` from `pipeline-state.json`. This is the base directory for ALL research outputs. If `project_dir` is null (legacy state), ask the user for a project slug and run `python scripts/pipeline_state.py init --force --project <slug>` to set it.

3. **Create project folder structure** (if not already present):
   ```bash
   mkdir -p $PROJECT_DIR/{docs,configs,src,data,results/tables,results/figures,manuscript,logs,notebooks}
   ```

4. If `--status` was passed:
   - Run `python scripts/pipeline_state.py status` and display the output.
   - Stop here.

5. If `--reset` was passed:
   - Run `python scripts/pipeline_state.py reset`.
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

1. Read `$PROJECT_DIR/docs/novelty-assessment.md` → look for `Decision: REPOSITION` or `Decision: PIVOT` or `Decision: KILL` or `Decision: PROCEED`.
2. Also check the exit code of `scripts/kill_decision.py` (called inside `/novelty-gate`):
   - Exit 0 → PROCEED
   - Exit 1 → KILL (see Kill Decision below)
   - Exit 2 → REPOSITION
   - Exit 3 → PIVOT

**If PROCEED:** Continue to Step 8.

**If REPOSITION:**
```bash
python scripts/pipeline_state.py increment-counter reposition_count --max 2
```
- Exit 0 (counter now 1 or 2, still within limit): Route back to Step 3. Re-execute Steps 3–7. Log: `[LOOP] Novelty gate N1: REPOSITION #N — routing to formulate-hypotheses.`
- Exit 1 (counter reached max = 2): Do NOT loop again. Run:
  ```bash
  python scripts/kill_decision.py --log-kill --criterion failed_reposition \
    --project $PROJECT_DIR \
    --reason "Gate N1 failed after 2 repositioning attempts. No viable novel angle found."
  ```
  Pipeline terminates (exit 1 from kill_decision.py). Log: `[KILL] Novelty gate N1: failed after 2 repositioning attempts.`

**If PIVOT:**
```bash
python scripts/pipeline_state.py increment-counter pivot_count --max 1
```
- Exit 0 (first pivot): Route back to Step 1. Re-execute Steps 1–7. Log: `[LOOP] Novelty gate N1: PIVOT #1 — routing to research-landscape.`
- Exit 1 (already pivoted once): Run `--log-kill --criterion failed_reposition`. Pipeline terminates.

**If KILL:** Run `kill_decision.py --log-kill` and terminate immediately.

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

#### Loop 1: Gap Detection (Step 21 → Step 9)

Step 21 is an inline orchestrator sub-task. After running it:

1. Check `$PROJECT_DIR/docs/gap-detection-report.md` for `critical_gaps_found: true` or presence of any CRITICAL severity gap entries.

**If no critical gaps:** Continue to Step 22.

**If critical gaps found:**
```bash
python scripts/pipeline_state.py increment-counter gap_detection_loops --max 2
```
- Exit 0: Route back to Step 9. Re-execute Steps 9–21. Log: `[LOOP] Gap detection: critical gaps found, loop #N — routing to design-experiments.`
- Exit 1: Do NOT loop. Continue forward with gaps noted as limitations. Log: `[WARN] Gap detection triggered 2 loops. Proceeding with current evidence; remaining gaps documented as limitations.`

---

#### Loop 2: Narrative Gap Detection (Step 29 → Step 20 or Step 9)

Step 29 is an inline orchestrator sub-task. After running it:

1. Check `$PROJECT_DIR/docs/narrative-gap-report.md` for any gap with `severity: Critical` and `type: Evidence missing`.

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

**Kill decision (any gate, any loop):** If `kill_decision.py` exits 1 (KILL) at any point:
1. Print: `[KILL] Project terminated at step N. Reason: <reason>. Artifacts preserved in $PROJECT_DIR.`
2. Run `python scripts/pipeline_state.py status` and display.
3. Print: `Human override: python scripts/kill_decision.py --override-kill --human-override --project $PROJECT_DIR --justification "..."`
4. Stop pipeline execution.

## Feedback Loop Routing Reference

Summary table for quick reference. For full logic, see "Gate Decision Reading" section above.

| Loop | Counter field | Trigger step | Target | Max | Termination on exceed |
|------|--------------|-------------|--------|-----|----------------------|
| N1 REPOSITION | `reposition_count` | Step 7 | Step 3 | 2 | `kill_decision.py --criterion failed_reposition` |
| N1 PIVOT | `pivot_count` | Step 7 | Step 1 | 1 | `kill_decision.py --criterion failed_reposition` |
| N2 Design-Novelty | `design_novelty_loops` | Step 10 | Step 9 | 2 | Halt, human review required |
| Gap Detection | `gap_detection_loops` | Step 21 | Step 9 | 2 | Continue with gaps as limitations |
| Narrative Gap | `narrative_gap_loops` | Step 29 | Step 20 or 9 | 2 | Continue with gaps as limitations |
| Phase 5B Revision | `verify_paper_cycle` | Step 34 | Steps 26–33 | 3 | CRITICAL→escalate; MAJOR→cover letter |
| Adversarial Review | `adversarial_review_cycles` | Step 35 | varies | 2 | Continue with weaknesses documented |

**Kill decision:** If `kill_decision.py` exits 1 (KILL) at any point, the pipeline terminates. Human override: `python scripts/kill_decision.py --override-kill --human-override --project $PROJECT_DIR --justification "..."`

## Pipeline Completion

When all steps are done (or the user aborts), display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pipeline Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then run `python scripts/pipeline_state.py status` and display the result.

If aborted, remind the user: `Resume later with: /run-pipeline --resume`

## Inline Step Output Templates

These are the required output formats for the inline steps (steps with `—` in the Command column). The orchestrator must produce these files before reading gate decisions.

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

## Important Rules

1. **Never duplicate command logic.** Always invoke the actual slash command via the Skill tool. The orchestrator only manages sequencing and state.
2. **Always update pipeline-state.json** before and after each step.
3. **Always create log files** for each step.
4. **Respect the user's choice** in interactive mode. If they say abort, stop immediately.
5. **Steps marked with `—` in the Command column** (gap-detection, narrative-gap-detect, literature-rescan, method-code-reconciliation, argument-figure-align, cross-section-consistency, claim-source-align, adversarial-review) are invoked inline by the orchestrator — they do not have separate slash commands. Run them as structured sub-tasks using the output templates defined in "Inline Step Output Templates" above.
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
