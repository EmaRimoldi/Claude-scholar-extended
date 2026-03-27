---
name: hypothesis-revision
description: This skill should be used when the user asks to "revise my hypothesis", "should I pivot or continue", "update the research direction", "what should I try next after this experiment", or after failure diagnosis when a decision about the research direction is needed. Iterative hypothesis refinement with pivot/persevere/abandon decisions and hypothesis evolution tracking.
version: 0.1.0
tags: [Research, Iteration, Hypothesis, Decision]
---

# Hypothesis Revision

Based on failure diagnosis, revises hypotheses, updates the experimental plan, and decides whether to pivot, persevere, or abandon. Tracks the evolution of hypotheses across iterations.

## Core Features

### 1. Decision Framework

For each iteration, make one of three decisions:

- **Persevere**: Same hypothesis, adjusted execution (tuning, more data, different implementation)
  - When: Diagnosis points to fixable issues (hyperparameters, data, implementation)
  - Action: Update experiment plan, keep hypothesis, iterate
- **Pivot**: New or revised hypothesis based on what was learned
  - When: Original hypothesis partially supported but needs refinement
  - Action: Formulate H1' or H2, update experiment plan, iterate
- **Abandon**: Stop pursuing this research line
  - When: Multiple iterations failed, evidence strongly against the approach, resources exhausted
  - Action: Archive state, consider new direction via novelty-assessment

### 2. Hypothesis Evolution Tracking

Maintain an append-only log of all iterations:

- **Chain format**: H1 -> evidence -> decision -> H1' -> evidence -> decision -> H2 -> ...
- **Cumulative learning**: What has been learned across all iterations
- **Decision rationale**: Why each decision was made
- **Resource accounting**: GPU-hours spent, remaining budget

### 3. Revised Hypothesis Construction

When pivoting, construct the revised hypothesis:

- **What changed**: Specific difference from the previous hypothesis
- **Why**: What evidence from the diagnosis supports this change
- **New prediction**: Updated effect size and success threshold
- **New experiment**: What needs to be tested differently

### 4. Termination Criteria

Define when the loop should stop:

- **Max iterations reached**: Default 3, configurable in `experiment-state.json`
- **Resource exhaustion**: GPU budget or deadline reached
- **Hypothesis confirmed**: Evidence supports the claim at the success threshold
- **Stable negative result**: Failure itself is interesting (negative result paper)

### 5. State Updates

- Update `experiment-state.json`: increment iteration, update active hypothesis, set status to `"revising"`
- Update `hypotheses.md` with revised hypotheses
- Append to `hypothesis-evolution.md` (create if not exists)

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Failure diagnosis** -- from `failure-diagnosis` output (`failure-diagnosis.md`)
2. **Hypothesis history** -- accumulated `hypotheses.md` + `hypothesis-evolution.md`
3. **Resource constraints** -- remaining GPU budget, time to deadline
4. **`experiment-state.json`** -- current iteration context

### Mode B: Standalone (manual)

1. **What you tried** -- user describes the experiment and method
2. **What happened** -- user describes the results and any diagnosis
3. **What you're considering** -- user describes possible next directions
4. **Constraints** -- remaining time, compute, or other limitations
5. The skill structures a pivot/persevere/abandon recommendation from the description

When running in Mode B, state: "No failure-diagnosis.md found. Working from your description of results and possible directions."

## Outputs

- Updated `hypotheses.md` with:
  - Revised hypotheses (H1', H2, etc.)
  - Decision record: pivot / persevere / abandon with justification
  - What evidence led to the revision
  - Updated experiment plan pointer
- `hypothesis-evolution.md` (append-only log):
  - Chain: H1 -> evidence -> decision -> H1' -> evidence -> decision -> H2 -> ...
  - Cumulative "what we've learned" summary
- Updated `experiment-state.json` (increments iteration, updates active hypothesis, sets status to `"revising"`)

## Obsidian Write-Back (when bound)

When the current repo is bound to an Obsidian project knowledge base:

1. **`Results/Reports/`**: Create or update a decision report
2. **`Experiments/{experiment-line}.md`**: Update canonical experiment note with new iteration section
3. **`Daily/YYYY-MM-DD.md`**: Append trace entry
4. **`.claude/project-memory/<project_id>.md`**: Update with current direction
5. **`00-Hub.md`**: Update ONLY if decision changes top-level project direction

When NOT bound: write outputs to local project directory only. State: "No Obsidian binding detected. Outputs written locally."

## When to Use

### Scenarios for This Skill

1. **After failure diagnosis** -- have a diagnosis, need to decide next steps
2. **After partial success** -- results are positive but below target
3. **Resource check** -- running low on compute or time, need to prioritize
4. **Advisor discussion** -- preparing a pivot/persevere recommendation

### Typical Workflow

```
failure-diagnosis -> [hypothesis-revision] -> experiment-design -> execution (loop)
                OR
user describes situation -> [hypothesis-revision] -> next steps
```

**Output Files:**
- Updated `hypotheses.md` -- Revised hypotheses with decision record
- `hypothesis-evolution.md` -- Append-only iteration log

## Integration with Other Systems

### The Iteration Loop

```
results-analysis (Hypothesis not confirmed)
    |
failure-diagnosis (Why did it fail?)
    |
hypothesis-revision (What to do next?)  <-- THIS SKILL
    |
    |-- pivot/persevere --> experiment-design (Updated plan, LOOP BACK)
    |
    |-- abandon --> novelty-assessment (New direction)
```

### Data Flow

- **Depends on**: `failure-diagnosis` (Mode A) OR user description (Mode B)
- **Feeds into**: `experiment-design` (new hypotheses need new experiments) -- THIS CREATES THE LOOP
- **Hook activation**: Context-aware conditional trigger (requires research project files)
- **No new command**: Part of the iteration loop
- **State update**: Increments iteration in `experiment-state.json`, sets status to `"revising"`

### Key Configuration

- **Decision types**: Pivot / Persevere / Abandon (exactly one per iteration)
- **Evolution log**: Append-only, never edited retroactively
- **Max iterations**: Default 3, configurable per project
- **Output format**: Markdown for easy review and version control

## Additional Resources

### Reference Files

- **`references/decision-framework.md`** -- Decision Framework Guide
  - When to pivot vs. persevere vs. abandon
  - Resource-aware decision-making
  - Sunk cost avoidance strategies
  - Common decision mistakes in research iteration

### Example Files

- **`examples/example-hypothesis-evolution.md`** -- Hypothesis Evolution Example
  - Demonstrates 3-iteration evolution chain
  - Shows pivot, persevere, and abandon scenarios
