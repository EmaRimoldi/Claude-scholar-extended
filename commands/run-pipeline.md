---
name: run-pipeline
description: Run the full research pipeline end-to-end with human-in-the-loop checkpoints. Supports --auto mode, --resume from last checkpoint, and --from to start at a specific step.
args:
  - name: flags
    description: "Flags: --auto (no confirmations), --resume (continue from last checkpoint), --from <step> (start at specific step), --status (show progress), --reset (reset all steps)"
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
   - If it does not exist: run `python scripts/pipeline_state.py init` to create it.

2. If `--status` was passed:
   - Run `python scripts/pipeline_state.py status` and display the output.
   - Stop here.

3. If `--reset` was passed:
   - Run `python scripts/pipeline_state.py reset`.
   - Stop here.

4. Create the logs directory for this run:
   ```bash
   mkdir -p logs/pipeline-$(date +%Y-%m-%d)
   ```

## Pipeline Steps

Execute the following steps **in this exact order**. This is the canonical sequence:

| # | Step ID | Command | Description | Prerequisite Files | Online? |
|---|---------|---------|-------------|-------------------|---------|
| 1 | research-init | `/research-init` | Literature review, gap analysis, hypotheses | — | Yes |
| 2 | check-competition | `/check-competition` | Competitive landscape check | — | Yes |
| 3 | design-experiments | `/design-experiments` | Experiment plan from hypotheses | hypotheses.md | No |
| 4 | scaffold | `/scaffold` | Generate project structure | experiment-plan.md | No |
| 5 | build-data | `/build-data` | Dataset generators and loaders | experiment-plan.md | No |
| 6 | setup-model | `/setup-model` | Load and configure models | experiment-plan.md | No |
| 7 | implement-metrics | `/implement-metrics` | Metrics and statistical tests | experiment-plan.md | No |
| 8 | validate-setup | `/validate-setup` | Pre-flight validation checklist | — | No |
| 9 | plan-compute | `/plan-compute` | GPU estimation, SLURM scripts | experiment-plan.md | No |
| 10 | run-experiment | `/run-experiment` | Submit experiment matrix | — | No |
| 11 | collect-results | `/collect-results` | Aggregate outputs into tables | — | No |
| 12 | analyze-results | `/analyze-results` | Statistical analysis, figures | — | No |
| 13 | map-claims | `/map-claims` | Claims to evidence mapping | — | No |
| 14 | position | `/position` | Contribution positioning | — | No |
| 15 | story | `/story` | Narrative arc, paper blueprint | — | No |
| 16 | produce-manuscript | `/produce-manuscript` | Figures, prose, LaTeX, package | — | No |
| 17 | rebuttal | `/rebuttal` | Reviewer response document | — | No |

## Execution Loop

For each step from the starting point to the end:

### 1. Check if already done

Read the step status from `pipeline-state.json`:
- If `completed` or `skipped` → print `[OK] Step N: <command> — already done` and move to the next step.
- If `pending`, `failed`, or `running` → proceed.

### 2. Check prerequisites

For each file listed in the step's `prerequisite_files`:
- Check if the file exists in the project directory.
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
  Step N/17: <command>
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
[OK] Step N/17: <command> — completed
     Next: <next_command> — <next_description>
```

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
5. **The rebuttal step is optional** — in interactive mode, suggest skipping it if no reviews have been received yet.

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
- Experiment iteration state: `experiment-state.json` (managed by `/run-experiment`)
