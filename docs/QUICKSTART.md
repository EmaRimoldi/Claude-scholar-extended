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
Phase 1                    Phase 2           Phase 3           Phase 4
Research & Novelty    -->  Experiment   -->  Implementation -> Execution
Assessment (Day 1-5)       Design            (Day 6-10)        (Day 10-19)
8 steps, 4 search passes   (Day 5-6)
Gate N1                    Gate N2

                         Phase 5A                  Phase 5B               Phase 6
                    -->  Analysis & Epistemic  -->  Writing Cycle     -->  Publication
                         Grounding (Day 19-23)      (Day 23-29)            (Day 29-38)
                         Gate N3                    Revision cycle (×3)    Gates N4
```

| Phase | Focus | Estimated Time |
|---|---|---|
| 1. Research & Novelty Assessment | 6 search passes, N1 novelty gate | 1--5 days |
| 2. Experiment Design | Baselines, ablations, sample size, Gate N2 | 1--2 days |
| 3. Implementation | Scaffold code, data, model, metrics, validation | 4--5 days |
| 4. Execution | SLURM submission, monitoring, phase gates | 1--2 weeks |
| 5A. Analysis & Epistemic Grounding | Statistics, figures, Gate N3 | 4--5 days |
| 5B. Claim Architecture & Writing Cycle | Map claims, write, verify (7 dims) | 6--7 days |
| 6. Pre-Submission & Publication | Adversarial review, Gate N4, compile | 1 week |

Time estimates assume a single focused project. Phases overlap in practice.

---

## Step-by-Step Guide

### Phase 1: Research & Novelty Assessment (Day 1--5)

**Goal:** Map the research territory, decompose the contribution into verifiable
claims, and confirm novelty before committing to experiments. Phase 1 runs
**6 search passes** across 8 steps and ends at **Novelty Gate N1**.

#### 1.1 Broad territory mapping (Pass 1)

```
/research-landscape
```

Runs a broad search collecting 50--100 papers, builds a cluster analysis
(4--8 themes), identifies research gaps, and initializes the **Citation
Provenance Ledger** (`$PROJECT_DIR/.epistemic/citation_ledger.json`).

**Output:** `$PROJECT_DIR/docs/research-landscape.md`

#### 1.2 Check for competing work (Pass 4)

```
/check-competition
```

Cross-field search for concurrent or closely prior work. Paste search results
and the `competitive-check` skill analyzes overlap and identifies threat papers.

#### 1.3 Formulate hypotheses

```
/research-init
```

Activates the `hypothesis-generator` agent (opus + extended thinking) to
convert research gaps into falsifiable hypotheses with explicit success/failure
criteria.

**Output:** `$PROJECT_DIR/docs/hypotheses.md`

#### 1.4 Claim-level decomposition (Pass 2)

```
/claim-search
```

Decomposes the primary hypothesis into 7 atomic components (Method, Task,
Result, Mechanism, and combinations). Each component is searched independently.
Papers with ≥2 overlapping components are flagged as HIGH threat.

**Output:** `$PROJECT_DIR/docs/claim-overlap-report.md`

#### 1.5 Citation graph traversal (Pass 3)

```
/citation-traversal
```

Forward and backward citation traversal from the top seed papers via the
Semantic Scholar API. Discovers papers that cite and are cited by the most
relevant prior work.

#### 1.6 Adversarial novelty attack (Pass 6)

```
/adversarial-search
```

5 attack types (Survey, "Already Done", Closest-Prior-Work, Incremental
Variation, Cross-Field Anticipation). If no rebuttal can be written, the step
emits a kill signal.

**Output:** `$PROJECT_DIR/docs/adversarial-novelty-report.md`

#### 1.7 Novelty Gate N1 (hard gate)

```
/novelty-gate gate=N1
```

Synthesizes all search passes into a 7-dimension novelty evaluation using the
`adversarial-attacker` and `skeptic` agents (opus + extended thinking).

**Decision:** PROCEED / REPOSITION / PIVOT / KILL

- **PROCEED** → move to Phase 2.
- **REPOSITION** → loop back to Step 3 (max 2 iterations, then KILL).
- **PIVOT** → loop back to Step 1 (max 1 iteration, then KILL).
- **KILL** → pipeline terminates; use `python scripts/kill_decision.py --override-kill` to proceed anyway.

#### 1.8 First recency sweep (Pass 5)

```
/recency-sweep sweep_id=1
```

Searches arXiv, OpenReview, Semantic Scholar, and lab blogs for papers published
in the last 90 days that overlap with the hypothesis.

**Expected outputs at end of Phase 1:**
- `$PROJECT_DIR/docs/research-landscape.md`
- `$PROJECT_DIR/docs/hypotheses.md`
- `$PROJECT_DIR/docs/claim-overlap-report.md`
- `$PROJECT_DIR/docs/adversarial-novelty-report.md`
- `$PROJECT_DIR/.epistemic/citation_ledger.json`
- Gate N1 decision recorded in `pipeline-state.json`

---

### Phase 2: Experiment Design (Day 5--6)

**Goal:** Translate hypotheses into a concrete, reproducible experiment plan
and verify the design tests the actual novelty claim (Gate N2).

#### 2.1 Design experiments

```
/design-experiments
```

The `experiment-design` skill produces a comprehensive plan covering:

- **Baselines** --- Which existing methods to compare against (must include all HIGH-overlap papers from Phase 1).
- **Ablations** --- Which components to isolate and test.
- **Sample size / power analysis** --- How many runs, seeds, and data points.
- **Resource estimation** --- Approximate GPU hours and memory.
- **Success criteria** --- Quantitative thresholds tied to each hypothesis.

`$PROJECT_DIR/docs/experiment-plan.md` is the **source of truth** for all downstream phases.

#### 2.2 Novelty Gate N2 (hard gate)

```
/design-novelty-check
```

Verifies that the experiment design actually tests the novelty claim identified
in Phase 1. Checks:

1. Every claimed novelty dimension has at least one experiment testing it.
2. All HIGH-overlap papers are included as baselines.
3. Evaluation metrics are aligned with the claimed novelty.
4. Ablations isolate claimed mechanisms.
5. Power analysis covers small claimed improvements.

**BLOCK** → loop back to `/design-experiments` (max 2 iterations).

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

#### 5.4 Paper Quality Verifier (7-dimension gate)

```
/verify-paper
```

The Paper Quality Verifier (PQV) is the peer-review gate before submission.
It evaluates the manuscript across **7 dimensions with 41 criteria**:

| # | Dimension | Criteria |
|---|-----------|---------|
| 1 | Novelty & Contribution | N1–N6: incremental test, dimension coverage, uncited threats |
| 2 | Methodological Rigor | M1–M8: baselines, ablations, power, method-code alignment |
| 3 | Claim-Evidence Alignment | C1–C6: claim trace, confidence, cherry-picking |
| 4 | Argument Structure | A1–A6: narrative, causation, negative results |
| 5 | Cross-Section Coherence | X1–X6: abstract/intro/conclusion/related agreement |
| 6 | Presentation Quality | P1–P7: figures, tables, clarity |
| 7 | Reproducibility | R1–R6: seeds, configs, checkpoints |

**Gate rules:** CRITICAL issue → BLOCK; 3+ MAJOR from one dimension → BLOCK;
any dimension < 5 → BLOCK; average < 7 → REVISE. Re-run targeted dimensions
with `--dimensions N,M`. Outputs acceptance probability: HIGH / MEDIUM / LOW.

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

The orchestrator runs the 38 pipeline steps in canonical order across 6 phases:

```
Phase 1: Research & Novelty Assessment (Steps 1–8)
 1. /research-landscape    5. /citation-traversal
 2. /check-competition     6. /adversarial-search
 3. /research-init         7. /novelty-gate N1      (gate)
 4. /claim-search          8. /recency-sweep 1

Phase 2: Experiment Design (Steps 9–10)
 9. /design-experiments   10. /design-novelty-check  (gate N2)

Phase 3: Implementation (Steps 11–15)
11. /scaffold             14. /implement-metrics
12. /build-data           15. /validate-setup        (gate)
13. /setup-model

Phase 4: Execution (Steps 16–19)
16. /download-data        18. /run-experiment
17. /plan-compute         19. /collect-results

Phase 5A: Analysis & Epistemic Grounding (Steps 20–25)
20. /analyze-results      23. /recency-sweep 2
21. gap-detection         24. literature-rescan
22. /novelty-gate N3      25. method-code-reconciliation

Phase 5B: Claim Architecture & Writing Cycle (Steps 26–34)
26. /map-claims           31. /produce-manuscript
27. /position             32. cross-section-consistency
28. /story                33. claim-source-align
29. narrative-gap-detect  34. /verify-paper          (gate, 7 dims)
30. argument-figure-align

Phase 6: Pre-Submission & Publication (Steps 35–38)
35. adversarial-review    37. /novelty-gate N4       (gate)
36. /recency-sweep final  38. /compile-manuscript
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
🔄 Pipeline: 7/38 completed, 1 skipped
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
| `/research-landscape` | Pass 1: broad territory mapping, 50–100 papers, cluster analysis | Phase 1, Step 1 |
| `/check-competition` | Pass 4: search for competing/concurrent work | Phase 1, Step 2 |
| `/research-init` | Formulate hypotheses from gaps (opus + extended thinking) | Phase 1, Step 3 |
| `/claim-search` | Pass 2: decompose into atomic claims, per-component search | Phase 1, Step 4 |
| `/citation-traversal` | Pass 3: citation graph traversal from seed papers | Phase 1, Step 5 |
| `/adversarial-search` | Pass 6: 5 attacks to kill novelty claim | Phase 1, Step 6 |
| `/novelty-gate` | Gate N1/N3/N4: PROCEED/REPOSITION/PIVOT/KILL | Phase 1 Step 7, Phase 5A/6 |
| `/recency-sweep` | Pass 5: concurrent work detection (sweep 1, 2, or final) | Phase 1 Step 8, Phase 5A/6 |
| `/design-experiments` | Generate full experiment plan | After novelty confirmed |
| `/design-novelty-check` | Gate N2: verify design tests the novelty claim | After experiment design |
| `/zotero-review` | Synthesize papers from Zotero into literature review | After collecting papers in Zotero |
| `/zotero-notes` | Batch-create Obsidian paper notes from Zotero | After `/zotero-review` |
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
| `/verify-paper` | 7-dimension PQV (41 criteria), acceptance probability estimate | After produce-manuscript |
| `/compile-manuscript` | Compile LaTeX to PDF, create Overleaf ZIP | After verify-paper passes |
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
