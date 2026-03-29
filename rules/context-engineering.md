# Context Engineering Rules

## What Stays in Active Context

Always loaded, kept minimal:
- `CLAUDE.md` (lean version, <200 lines, ~1500 tokens)
- Current pipeline step's command file (~100-200 lines)
- Current project's `experiment-plan.md` and `hypotheses.md` (when executing experiment steps)

## What Is Loaded on Demand

Retrieved only when the current task needs it:
- Full skill documents (loaded via Skill tool when activated)
- Full reference docs (`docs/CLAUDE_REFERENCE.md`)
- Past research outputs (`literature-review.md`, `analysis-report.md`)
- Code files (only when editing or reviewing)
- Agent system prompts (only the currently-invoked agent)

## Summarization Strategies

When context approaches limits, compress loaded research artifacts:
- **Literature review** → "N papers reviewed, key finding: X, main gap: Y"
- **Experiment results** → metrics table only, drop raw outputs and per-epoch logs
- **Code files** → function signatures + docstrings, drop implementations
- **Analysis reports** → hypothesis verdict table + key statistics, drop verbose discussion

## Token Budget Guidelines

Target steady-state overhead for system/pipeline context:

| Component | Budget |
|-----------|--------|
| CLAUDE.md | <200 lines (~1500 tokens) |
| Per-step command | ~100-200 lines (~1000 tokens) |
| Active skill | ~200-400 lines (~2000 tokens) |
| Research context | ~500 lines (~3000 tokens) |
| **Total overhead** | **<10K tokens** |

## Context Thresholds

| Threshold | Action |
|-----------|--------|
| 75% context | Summarize loaded research documents to compressed form |
| 85% context | Checkpoint current progress, offload completed step outputs to files |
| 95% context | Block new tool invocations, save state to `pipeline-state.json`, suggest session restart |
