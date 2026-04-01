---
name: run-pipeline
description: Use when the user runs /run-pipeline, asks to run the full ALETHEIA v3 research pipeline, resume the pipeline (--resume), run in --auto mode, or when the client reports "Unknown skill" for run-pipeline. Orchestrates 38 steps; canonical spec is commands/run-pipeline.md (also installed as ~/.claude/commands/run-pipeline.md).
version: 0.1.0
tags: [Pipeline, Orchestration, Research, Workflow, ALETHEIA]
---

# Run pipeline (orchestrator)

You are the **v3 research pipeline orchestrator**. Some Claude Code builds route `/run-pipeline` through the **Skill** tool; this skill ensures `run-pipeline` always resolves. Behavior is **identical** to the slash command.

## What to do

1. **Locate the full specification** (same content everywhere):
   - **Project checkout:** `commands/run-pipeline.md` at the repository root (preferred if the cwd is this repo).
   - **Global install:** `~/.claude/commands/run-pipeline.md` after `bash scripts/setup.sh`.

2. **Read that file** and follow it exactly: flag parsing (`--auto`, `--resume`, `--from`, `--status`, `--reset`, `--skip-online`), initialization from `RESEARCH_PROPOSAL.md` / `pipeline-state.json`, step order, and guards.

3. **Parse flags** from the user message (e.g. `--resume` on `/run-pipeline --resume`).

4. **Do not** stop with "unknown skill"; execute the orchestrator workflow from the markdown file.

## If the user still sees command issues

Ask them to run `bash scripts/setup.sh` from the repo, then **fully quit and restart** the Claude Code CLI so commands and skills reload.
