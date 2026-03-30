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
| 2 | check-competition | `/check-competition` | Competitive landscape + Pass 4 cross-field search | research-landscape.md | Yes |
| 3 | formulate-hypotheses | `/research-init` | Hypothesis generation from gaps (hypothesis-generator agent, opus) | research-landscape.md | No |
| 4 | claim-search | `/claim-search` | Pass 2: Decompose hypothesis into atomic claims, search each independently | hypotheses.md | Yes |
| 5 | citation-traversal | `/citation-traversal` | Pass 3: Citation graph from top seed papers | research-landscape.md | Yes |
| 6 | adversarial-search | `/adversarial-search` | Pass 6: Actively attempt to kill novelty claim | claim-overlap-report.md | Yes |
| 7 | novelty-gate-n1 | `/novelty-gate gate=N1` | Gate N1: Full novelty evaluation. PROCEED/REPOSITION/PIVOT/KILL | adversarial-novelty-report.md | No |
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
| 35 | adversarial-review | — | Pre-submission adversarial review: 3 hostile simulated reviewers, routes upstream | manuscript/, review-battery-report.md | No |
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

## Feedback Loop Routing

The following steps may route backward. When a step triggers a loop:

1. Log the loop in `pipeline-state.json` under the appropriate counter.
2. Re-run the routing target step.
3. Re-run all steps from the target to the triggering step.
4. Check the termination condition before looping again.

| Loop | Trigger | Target | Max Iterations | Termination |
|------|---------|--------|---------------|-------------|
| Gap Detection | Step 21 (critical gap found) | Step 9 (design-experiments) | 2 | No critical gaps remain |
| Narrative Gap | Step 29 (evidence missing) | Step 20 or Step 9 | 1 per direction | No evidence-missing critical gaps |
| Revision Cycle | Step 34 (any dimension < 7) | Step 26–33 (targeted) | 3 | All dimensions ≥ 7 |
| Adversarial Review | Step 35 (critical item found) | Step 9/20/27/31 (routed) | 2 | No critical items unaddressed |
| Novelty Gate N1 | Step 7 (REPOSITION) | Step 3 (formulate-hypotheses) | 2 | Gate N1 passes |
| Novelty Gate N1 | Step 7 (PIVOT) | Step 1 (research-landscape) | 1 | Gate N1 passes |
| Design Novelty | Step 10 (REVISE/BLOCK) | Step 9 (design-experiments) | 2 | Gate N2 passes |

**Kill decision:** If `/novelty-gate` returns KILL at any point, the pipeline terminates. All artifacts are preserved. Human can override with `python scripts/kill_decision.py --override-kill`.

## Pipeline Completion

When all steps are done (or the user aborts), display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pipeline Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then run `python scripts/pipeline_state.py status` and display the result.

If aborted, remind the user: `Resume later with: /run-pipeline --resume`

## Important Rules

1. **Never duplicate command logic.** Always invoke the actual slash command via the Skill tool. The orchestrator only manages sequencing and state.
2. **Always update pipeline-state.json** before and after each step.
3. **Always create log files** for each step.
4. **Respect the user's choice** in interactive mode. If they say abort, stop immediately.
5. **Steps marked with `—` in the Command column** (gap-detection, narrative-gap-detect, literature-rescan, method-code-reconciliation, argument-figure-align, cross-section-consistency, claim-source-align, adversarial-review) are invoked inline by the orchestrator — they do not have separate slash commands. Run them as structured sub-tasks.
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
