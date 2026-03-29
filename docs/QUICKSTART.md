# Claude Scholar --- Researcher Quickstart

A step-by-step guide to running a full research experiment pipeline, from
initial idea to camera-ready submission.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Claude Code CLI** | Core runtime. Install via `npm i -g @anthropic-ai/claude-code` or follow official docs. |
| **Python 3.10+** | Required for experiment code. |
| **uv** | Modern Python package manager (`curl -LsSf https://astral.sh/uv/install.sh \| sh`). Used by all scaffolded projects. |
| **Git** | Version control. Claude Scholar enforces Conventional Commits and a branching strategy automatically. |
| **Zotero** (optional) | Desktop app + Zotero MCP server for automated paper import, full-text reading, and citation export. Not required but strongly recommended for Phase 1. |
| **SLURM cluster access** (optional) | Needed for Phase 4 if you run experiments on a cluster (e.g., MIT Engaging). Local execution works without it. |
| **LaTeX distribution** (optional) | For `make build-pdf` in the manuscript phase. TeX Live or TinyTeX recommended. |

### Initial setup

1. **Clone or create your research repository.**

2. **Enter the project directory** and launch Claude Code:
   ```bash
   cd my-research-project
   claude
   ```

3. **Create a project directory.** All research outputs live inside a
   dedicated project folder. Run:
   ```
   /new-project "Your Research Topic"
   ```
   This creates `projects/<topic-slug>/` with the standard layout
   (`docs/`, `configs/`, `src/`, `data/`, `results/`, `manuscript/`,
   `logs/`, `notebooks/`) and initializes `pipeline-state.json` with the
   `project_dir` field pointing to it.

4. **Configure credentials** (see [Credential Setup](#credential-setup) below).

5. **Bootstrap the Obsidian knowledge base** (recommended). If your repo does
   not yet have a `.claude/project-memory/registry.yaml`, Claude Scholar will
   offer to create one automatically, or you can run:
   ```
   /obsidian-init
   ```
   This binds the repo to a structured knowledge base that tracks literature,
   experiments, results, and writing across sessions.

6. **Verify the session-start hook fires.** When Claude Code starts, a hook
   displays Git status, open TODOs, available commands, pipeline progress,
   and the bound Obsidian project status. If you see this summary, the
   system is ready.

### Credential Setup

Claude Scholar accesses several external services. Credentials are stored in
`.claude/settings.local.json` (gitignored --- never committed).

Copy the template and fill in your values:

```bash
cp settings.json.template .claude/settings.local.json
```

Then edit `.claude/settings.local.json` and replace the placeholders:

| Credential | Where to get it | Required? |
|---|---|---|
| **ZOTERO_API_KEY** | [zotero.org/settings/keys](https://www.zotero.org/settings/keys) --- create a new key with read/write access | Required for Phase 1 (literature review) |
| **ZOTERO_LIBRARY_ID** | Same page --- your numeric "User ID" shown at the top | Required with above |
| **ZOTERO_LIBRARY_TYPE** | `user` for personal libraries, `group` for shared | Default: `user` |
| **UNPAYWALL_EMAIL** | Any valid email address | Optional --- enables open-access PDF auto-attachment |
| **GITHUB_PERSONAL_ACCESS_TOKEN** | [github.com/settings/tokens](https://github.com/settings/tokens) | Optional --- for GitHub plugin operations |

**APIs that do NOT require keys** (public access):
- Semantic Scholar (100 req/5 min)
- CrossRef (50 req/min)
- arXiv (20 req/min recommended)

**Optional: Chrome browser automation.** The `daily-paper-generator` skill can
use a Chrome MCP server at `http://127.0.0.1:12306/mcp` for browser-based
arXiv navigation. Uncomment the `streamable-mcp-server` block in settings if
you need this.

**Verify your setup:**

```bash
# In a Claude Code session, test Zotero connection:
# Ask Claude to run: mcp__zotero__get_collections
# If it returns your library collections, credentials are working.
```

---

## Pipeline Overview

Claude Scholar organizes a research project into six phases that mirror the
natural research lifecycle. Each phase has dedicated skills, commands, and
outputs.

```
Phase 1          Phase 2            Phase 3           Phase 4
Ideation    -->  Experiment    -->  Implementation -> Execution
(Day 1-3)        Design (Day 3-4)   (Day 4-7)        (Day 7-14+)

                                          Phase 5              Phase 6
                                     -->  Analysis &      -->  Review &
                                          Writing (Day 14-21)  Submit (Day 21-28)
```

| Phase | Focus | Estimated Time |
|---|---|---|
| 1. Research Ideation | Literature, gaps, hypotheses, novelty check | 1--3 days |
| 2. Experiment Design | Baselines, ablations, sample size, resource plan | 1--2 days |
| 3. Implementation | Scaffold code, data, model, metrics, validation | 3--4 days |
| 4. Execution | SLURM submission, monitoring, phase gates, iteration | 1--2 weeks |
| 5. Analysis & Writing | Statistics, figures, narrative, manuscript | 1 week |
| 6. Review & Submit | Self-review, rebuttal, post-acceptance materials | 1 week |

Time estimates assume a single focused project. Phases overlap in practice.

---

## Step-by-Step Guide

### Phase 1: Research Ideation (Day 1--3)

**Goal:** Identify a promising research direction, review the literature, and
formulate testable hypotheses.

#### 1.1 Start the ideation workflow

```
/research-init
```

This command activates the `research-ideation` skill and (if Zotero MCP is
configured) the `literature-reviewer` agent. It walks you through:

- **5W1H framework** --- Who, What, Where, When, Why, How for your research
  question.
- **Literature review** --- Automated Zotero collection creation, paper import,
  and full-text analysis. Without Zotero, provide papers manually or use
  `/zotero-review` later.
- **Gap analysis** --- Identifies under-explored areas in the literature.
- **Research question formulation** --- Produces a focused, falsifiable research
  question.

**What it produces:**
- `$PROJECT_DIR/docs/literature-review.md` --- Synthesized literature survey.
- `$PROJECT_DIR/docs/hypotheses.md` --- Testable hypotheses.
- Obsidian paper notes (if knowledge base is active).

#### 1.2 Check for competing work

```
/check-competition
```

This generates structured search queries for arXiv, Semantic Scholar, and Google
Scholar. Paste the search results back and the `competitive-check` skill will
analyze them for concurrent or prior work that overlaps with your idea.

#### 1.3 Assess novelty and formulate hypotheses

The `novelty-assessment` skill compares your proposed contribution against the
closest prior works and flags incremental contributions. If novelty is
confirmed, the `hypothesis-formulation` skill converts research gaps into
falsifiable hypotheses with explicit success and failure criteria.

**Expected outputs at end of Phase 1:**
- `$PROJECT_DIR/docs/hypotheses.md` --- Testable hypotheses with success/failure criteria.
- Novelty assessment (inline or as separate document).
- Literature notes in Obsidian (if active).

**Decision point:** If novelty is insufficient, iterate on the idea or pivot
before investing in experiments.

---

### Phase 2: Experiment Design (Day 3--4)

**Goal:** Translate hypotheses into a concrete, reproducible experiment plan.

```
/design-experiments
```

The `experiment-design` skill produces a comprehensive plan covering:

- **Baselines** --- Which existing methods to compare against.
- **Ablations** --- Which components to isolate and test.
- **Sample size / power analysis** --- How many runs, seeds, and data points.
- **Resource estimation** --- Approximate GPU hours and memory.
- **Success criteria** --- Quantitative thresholds tied to each hypothesis.

**What `$PROJECT_DIR/docs/experiment-plan.md` contains:**
- Full experiment matrix (conditions x seeds x metrics).
- Baseline specifications with expected performance ranges.
- Ablation schedule.
- Resource budget.
- Phase gate criteria (what must pass before proceeding to analysis).

**How to review the plan:**
- Check that every hypothesis maps to at least one experiment condition.
- Verify baselines are fair and well-known.
- Confirm the ablation schedule isolates the right variables.
- Adjust seed count or sample size if compute budget is limited.

`$PROJECT_DIR/docs/experiment-plan.md` is the **source of truth** for all
downstream phases. Every subsequent command reads from it.

---

### Phase 3: Implementation (Day 4--7)

**Goal:** Generate runnable code from the experiment plan and validate it before
the full sweep.

#### 3.1 Scaffold the project

```
/scaffold
```

The `project-scaffold` skill generates a complete, runnable ML project inside
`$PROJECT_DIR/`:

- `$PROJECT_DIR/pyproject.toml` with uv dependency management.
- `$PROJECT_DIR/src/` directory with Factory and Registry patterns.
- `$PROJECT_DIR/configs/` Hydra configuration files.
- Entry point script.
- `Makefile` with standard targets.

#### 3.2 Build data, model, and metrics

Run these commands in sequence (each builds on the previous):

```
/build-data
```
Translates dataset specs from the experiment plan into working
generators/loaders (synthetic data, HuggingFace datasets, benchmarks).

```
/setup-model
```
Loads, introspects, and configures models. Supports HuggingFace models,
activation hooks, architecture discovery, and model surgery (ablation).

```
/implement-metrics
```
Implements metrics, analytical references (OLS, GD, ridge, Bayes-optimal), and
statistical tests as registrable components.

#### 3.3 Validate the setup

```
/validate-setup
```

The `setup-validation` skill runs a pre-flight checklist:

- **Data integrity** --- Shapes, types, distributions.
- **Model loading** --- Weights load, forward pass runs.
- **Measurement correctness** --- Metrics compute on toy data.
- **Ablation sanity** --- Ablated models produce different outputs.
- **Baseline replication** --- Baseline numbers match expected ranges.
- **Smoke test** --- One full train-evaluate cycle completes without error.

**What to check before proceeding:**
- All validation checks pass (green).
- Smoke test loss curves look reasonable.
- No OOM errors on a single-GPU test run.

---

### Phase 4: Execution (Day 7--14+)

**Goal:** Run the full experiment matrix, monitor progress, and handle failures.

#### 4.1 Download data and models

```
/download-data
```

Downloads all datasets and pretrained model weights to local cache so SLURM GPU
jobs do not need internet access. Reads the experiment plan to identify required
assets, downloads them via HuggingFace or direct URLs, and validates offline
loading. **This step must complete before submitting GPU jobs.**

#### 4.2 Plan compute resources

```
/plan-compute
```

Estimates GPU hours, memory requirements, and generates SLURM scripts tailored
to your cluster (MIT Engaging partitions by default). Outputs a scheduling
strategy for job dependencies and priorities.

#### 4.3 Submit experiments

```
/run-experiment
```

The `experiment-runner` skill submits the experiment matrix via SLURM with:

- **Phased gates** --- Experiments proceed in phases; each phase must pass
  gates before the next begins.
- **Failure recovery** --- Automatic resubmission of failed jobs with
  diagnostic logging.
- **Progress tracking** --- Real-time status via `experiment-state.json`.

#### 4.4 After jobs complete

```
/collect-results
```

Or use the Makefile shortcut:

```bash
make refresh
```

This aggregates per-run outputs (logs, metrics, checkpoints) into structured
tables ready for analysis.

#### 4.5 Evaluate phase gates

```bash
make check-gates
```

Compares collected results against the success criteria defined in
`experiment-plan.md`. If gates pass, proceed to Phase 5.

#### 4.6 What happens on gate failure

When experiments fail or gates do not pass, Claude Scholar enters the
**iteration loop** (see dedicated section below). The system will:

1. Run `failure-diagnosis` to identify root causes.
2. Trigger `hypothesis-revision` for pivot/persevere/abandon decisions.
3. Update `$PROJECT_DIR/experiment-state.json` with the iteration record.
4. Loop back to experiment design or implementation as needed.

**How `$PROJECT_DIR/experiment-state.json` tracks progress:**
- Current phase and iteration number.
- Per-condition status (passed / failed / pending).
- Gate evaluation history.
- Failure diagnoses and revision decisions.

---

### Phase 5: Analysis & Writing (Day 14--21)

**Goal:** Analyze results rigorously, then construct and produce the manuscript.

#### 5.1 Analyze results

```
/analyze-results
```

The `results-analysis` skill performs:

- Rigorous statistical tests (significance, confidence intervals, effect sizes).
- Scientific figure generation (with publication-quality defaults).
- Ablation analysis and decomposition.
- Comparison tables.

#### 5.2 Pre-writing preparation

Three commands bridge results to the manuscript:

```
/map-claims
```
Maps each paper claim to supporting experimental evidence. Identifies
unsupported claims and manages paper scope.

```
/position
```
Builds a differentiation matrix against prior work, crafts contribution
statements, and anticipates reviewer objections.

```
/story
```
Defines the narrative arc, triages results by importance, creates a figure plan,
and produces `paper-blueprint.md` (section outline for the full paper).

#### 5.3 Produce the manuscript

```
/produce-manuscript
```

Generates publication-quality figures, full prose for every section, LaTeX
source, and a submission-ready package. All outputs go to
`$PROJECT_DIR/manuscript/`.

#### 5.4 Quality review (gate)

```
/quality-review
```

The quality review step acts as a peer-review gate before submission. It scores
the manuscript across 8 dimensions (claim-evidence alignment, statistical
rigor, baseline completeness, generalizability, mechanistic validation, error
analysis, presentation accuracy, reproducibility). Each dimension is scored
1--10. **Gate rules:** all dimensions must score >= 5, and critical dimensions
(claim-evidence, statistical rigor, presentation accuracy) must score >= 6.
If the gate fails, the report includes specific fixes before you proceed.

#### 5.5 Compile the manuscript

```
/compile-manuscript
```

Compiles `$PROJECT_DIR/manuscript/main.tex` to PDF and creates an
Overleaf-ready ZIP package. Tries compilers in order: tectonic, pdflatex,
xelatex. The ZIP is always created as a fallback even if PDF compilation
fails.

**Deterministic scripts that save time:**
- `make refresh` --- Re-collect and update result tables without agent
  involvement.
- `make tables` --- Regenerate LaTeX tables from structured data.
- These handle mechanical tasks so agent time is focused on reasoning.

---

### Phase 6: Review & Submit (Day 21--28)

**Goal:** Quality-check the paper, prepare for submission, and handle
post-acceptance tasks.

#### 6.1 Self-review

The `paper-self-review` skill triggers automatically (or on demand) and runs a
6-item quality checklist covering clarity, completeness, reproducibility,
figures, related work, and contribution framing.

#### 6.2 Respond to reviewers

After receiving reviews:

```
/rebuttal
```

The `review-response` skill and `rebuttal-writer` agent produce a systematic
rebuttal document. The workflow:

1. Parses and categorizes each reviewer comment.
2. Maps comments to paper sections and evidence.
3. Drafts point-by-point responses with professional tone.
4. Suggests paper revisions where appropriate.

#### 6.3 Post-acceptance

```
/presentation
```
Generates a conference presentation outline with speaker notes.

```
/poster
```
Produces an academic poster layout.

```
/promote
```
Creates promotion content for Twitter, LinkedIn, and blog posts.

---

## Key Makefile Targets

After `/scaffold` generates your project, the following `make` targets are
available:

| Target | When to Use | What It Does |
|---|---|---|
| `make validate` | Phase 3, before full sweep | Runs setup-validation pre-flight checklist |
| `make refresh` | Phase 4, after jobs finish | Collects and aggregates all run outputs |
| `make check-gates` | Phase 4, after refresh | Evaluates phase gate criteria |
| `make tables` | Phase 5, during writing | Regenerates LaTeX tables from result data |
| `make build-pdf` | Phase 5, after manuscript | Compiles LaTeX source into PDF (or use `/compile-manuscript` for PDF + Overleaf ZIP) |
| `make clean` | Any time | Removes temporary and generated files |

---

## The Iteration Loop

Research rarely succeeds on the first attempt. Claude Scholar includes a
structured iteration loop for when experiments fail or gates do not pass.

### How it works

```
Gate failure
  |
  v
failure-diagnosis  -->  Root cause identified
  |
  v
hypothesis-revision  -->  Decision: PIVOT / PERSEVERE / ABANDON
  |
  v
  +-- PERSEVERE --> Adjust parameters, re-run same experiments
  +-- PIVOT -----> Revise hypothesis, return to Phase 2
  +-- ABANDON ---> Document findings, move to a different direction
```

### What each step does

1. **`failure-diagnosis`** --- Systematic diagnosis of research-level experiment
   failures (not code bugs). Examines whether the failure is due to
   insufficient data, wrong architecture, flawed metrics, or a genuinely
   falsified hypothesis.

2. **`hypothesis-revision`** --- Evaluates the diagnosis and recommends one of
   three actions:
   - **Persevere**: Minor adjustments (hyperparameters, data augmentation).
   - **Pivot**: Substantial change to the hypothesis or method.
   - **Abandon**: The direction is exhausted; archive results and move on.

3. **`$PROJECT_DIR/experiment-state.json`** tracks every iteration:
   - Iteration count and history.
   - Diagnosis summaries.
   - Revision decisions with rationale.
   - Updated experiment plan references.

### When to stop iterating

- The experiment plan defines **max iterations** (typically 3--5).
- If you hit the limit without passing gates, the system recommends pivoting or
  abandoning with a structured retrospective written to the Obsidian knowledge
  base.

---

## Tips for Efficient Use

1. **Use `make refresh` instead of manual result collection.** Deterministic
   scripts are faster and more reliable than asking the agent to parse log
   files.

2. **Let deterministic scripts handle tables, gates, and state.** Reserve agent
   time for reasoning-heavy tasks: analysis, writing, positioning.

3. **Keep `$PROJECT_DIR/docs/experiment-plan.md` as the single source of
   truth.** All downstream commands read from it. If you change the plan,
   re-run `/design-experiments` to keep everything consistent.

4. **Use the Obsidian knowledge base.** It persists context across sessions.
   Daily notes, experiment logs, and literature reviews accumulate into a
   searchable project memory.

5. **Run `/validate-setup` before every full sweep.** A five-minute smoke test
   can save days of wasted compute on broken pipelines.

6. **Leverage Zotero integration for Phase 1.** Automated paper import and
   full-text reading dramatically accelerate literature review. Use
   `/zotero-review` and `/zotero-notes` to batch-process collections.

7. **Commit frequently using `/commit`.** Claude Scholar enforces Conventional
   Commits, which keeps the project history clean and makes it easy to trace
   when and why each change was made.

8. **Use `/obsidian-sync` when switching between long sessions.** This forces a
   full sync between the repo, project memory, and Obsidian vault.

---

## Pipeline Orchestrator

Instead of running each phase command individually, you can use the
`/run-pipeline` command to execute the full research pipeline with built-in
state tracking and checkpoints.

### Basic usage

```bash
# Interactive mode (default) --- asks before each step
/run-pipeline

# Full auto --- runs all steps without confirmation
/run-pipeline --auto

# Resume from where you left off (after closing a session)
/run-pipeline --resume

# Start from a specific step
/run-pipeline --from scaffold

# Check current pipeline progress
/run-pipeline --status

# Reset all steps to pending
/run-pipeline --reset

# Skip steps that need internet (offline mode)
/run-pipeline --skip-online
```

### How it works

The orchestrator runs the 20 pipeline steps in canonical order:

```
 1. /research-init         11. /run-experiment
 2. /check-competition     12. /collect-results
 3. /design-experiments    13. /analyze-results
 4. /scaffold              14. /map-claims
 5. /build-data            15. /position
 6. /setup-model           16. /story
 7. /implement-metrics     17. /produce-manuscript
 8. /validate-setup        18. /quality-review      (gate)
 9. /download-data         19. /compile-manuscript
10. /plan-compute          20. /rebuttal
```

**In interactive mode** (default), between each step the orchestrator:

1. Shows what completed and what is coming next.
2. Asks: **Continue**, **Skip**, or **Abort**.
3. Checks that prerequisite files exist before running a step.
4. Saves progress to `pipeline-state.json` so you can resume later.

**In auto mode** (`--auto`), all steps run sequentially without prompts. Failed
steps are logged and skipped.

### State tracking

Pipeline progress persists in `pipeline-state.json` (v2, gitignored) at the
repo root. It records:

- **`project_dir`** --- The active project directory (e.g.,
  `projects/sparse-hate-explain`). All research outputs are written here.
- Per-step status: `pending`, `running`, `completed`, `skipped`, `failed`
- Timestamps for start and completion
- Failure reason (if applicable)
- SLURM job IDs (if applicable)

You can also check state directly:

```bash
python3 scripts/pipeline_state.py status
python3 scripts/pipeline_state.py next
```

### Project directory enforcement

All pipeline commands write outputs inside `$PROJECT_DIR` (resolved from
`pipeline-state.json` -> `project_dir`). Research documents never go to the
repository root. A PostToolUse hook (`research-doc-guard.js`) warns if a
research document is accidentally written to the root.

**Project directory layout:**

```
projects/<slug>/
├── docs/          # literature-review, hypotheses, experiment-plan, etc.
├── configs/       # Hydra/OmegaConf configs
├── src/           # Source code
├── data/          # Datasets (gitignored for large files)
├── results/       # Experiment outputs
│   ├── tables/
│   └── figures/
├── manuscript/    # LaTeX source, PDF, Overleaf ZIP
├── logs/          # Experiment and pipeline logs
├── notebooks/     # Jupyter notebooks
└── experiment-state.json
```

### Logs

Each step logs output to `$PROJECT_DIR/logs/pipeline-YYYY-MM-DD/step-NN-<name>.log`.

### Session-start integration

When `pipeline-state.json` exists, the session-start hook automatically shows
pipeline progress and suggests the next step:

```
🔄 Pipeline: 7/20 completed, 1 skipped
  → Next: /plan-compute — GPU estimation and SLURM script generation
  → Run /run-pipeline --resume to continue
```

The hook also scans the repo root for misplaced research documents and warns
if any are found outside the project directory.

---

## Common Commands Quick Reference

### Research Workflow

| Command | What It Does | When to Use |
|---|---|---|
| `/new-project` | Create project directory structure + pipeline state | Very first step for any new project |
| `/research-init` | Start research ideation with 5W1H + literature review | Beginning of a new project |
| `/zotero-review` | Synthesize papers from Zotero into literature review | After collecting papers in Zotero |
| `/zotero-notes` | Batch-create Obsidian paper notes from Zotero | After `/zotero-review` |
| `/check-competition` | Search for competing/concurrent work | After formulating your idea |
| `/design-experiments` | Generate full experiment plan | After hypotheses are ready |
| `/scaffold` | Generate runnable project structure | Start of implementation |
| `/build-data` | Create dataset generators/loaders | After scaffolding |
| `/setup-model` | Load and configure models | After data is ready |
| `/implement-metrics` | Implement metrics and statistical tests | After model setup |
| `/validate-setup` | Pre-flight validation checklist | Before full experiment sweep |
| `/download-data` | Download datasets and models to local cache | Before submitting GPU jobs |
| `/plan-compute` | Estimate resources, generate SLURM scripts | Before submitting jobs |
| `/run-experiment` | Submit experiment matrix to SLURM | When ready to run |
| `/collect-results` | Aggregate outputs into structured tables | After jobs complete |
| `/analyze-results` | Statistical analysis and figure generation | After collecting results |
| `/map-claims` | Map claims to experimental evidence | Before writing |
| `/position` | Position contribution against prior work | Before writing |
| `/story` | Build narrative arc and paper blueprint | Before writing |
| `/produce-manuscript` | Generate figures, prose, LaTeX, submission package | Writing phase |
| `/quality-review` | 8-dimension quality gate (blocks if critical dims fail) | Before submission |
| `/compile-manuscript` | Compile LaTeX to PDF, create Overleaf ZIP | After quality review passes |
| `/rebuttal` | Write systematic reviewer responses | After receiving reviews |
| `/presentation` | Create conference presentation | Post-acceptance |
| `/poster` | Generate academic poster | Post-acceptance |
| `/promote` | Create promotion content | Post-acceptance |

### Development Workflow

| Command | What It Does | When to Use |
|---|---|---|
| `/commit` | Create a Conventional Commits-style commit | After meaningful changes |
| `/update-github` | Commit and push to remote | When ready to share |
| `/plan` | Create an implementation plan | Before complex tasks |
| `/code-review` | Run code review | Before merging |
| `/tdd` | Start test-driven development workflow | When writing tests first |
| `/verify` | Verify recent changes | Before committing |
| `/build-fix` | Fix build errors | When builds fail |

### Knowledge Base

| Command | What It Does | When to Use |
|---|---|---|
| `/obsidian-init` | Bootstrap project knowledge base | Once per project |
| `/obsidian-sync` | Force sync repo and Obsidian | Between long sessions |
| `/obsidian-review` | Generate literature synthesis from paper notes | During literature review |
| `/obsidian-notes` | Normalize and connect paper notes | After adding papers |
| `/obsidian-link` | Repair wikilinks across notes | When links break |
| `/obsidian-project` | Archive, detach, or purge a project KB | Project lifecycle changes |
