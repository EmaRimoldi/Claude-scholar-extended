# What you need to run the pipeline (and `/run-experiment`)

This document answers: **what artifacts must exist before the orchestrator or `/run-experiment` can run**, and **what the slash command arguments mean**.

---

## 0. From scratch: new paper → `/run-pipeline --auto`

**`--auto` only removes confirmation prompts** — it does **not** invent a research question. Something must supply the topic for Step 1 (`/research-landscape`), which requires a `topic` argument.

**Recommended flow (moment 0):**

1. **Clone + install** this repo; run `bash scripts/setup.sh` so Claude Code has commands/skills.
2. **Create the project folder and state** (pick a short **slug** and a clear **research question**):
   ```bash
   python scripts/pipeline_state.py init --project my-paper-slug \
     --topic "Does selective-head sparsemax supervision improve faithfulness on HateXplain without hurting F1?"
   ```
   This creates `projects/my-paper-slug/` and **`pipeline-state.json`** with:
   - `project_dir` → `projects/my-paper-slug`
   - **`research_topic`** → your question (used when the orchestrator runs `/research-landscape`).
   Alternatively use **`/new-project "Title"`** in chat, then set `research_topic` by re-running init with `--force` and `--topic`, or **edit `pipeline-state.json`** and add the `"research_topic": "..."` field manually.
3. **Run the orchestrator** in Claude Code:
   ```text
   /run-pipeline --auto
   ```
   Step 1 should pass **`research_topic`** from `pipeline-state.json` into `/research-landscape`.
4. **Later**, `docs/hypotheses.md` is **produced** at step 3 (`/research-init`). You can edit it afterward; it is not the seed for step 1.

**Without `research_topic`:** the model may fall back to the project **README** title or must **ask you** — so for unattended `--auto`, always set `--topic` at init.

---

## 1. Starting the full pipeline: `/run-pipeline`

**Install** the bundle (`bash scripts/setup.sh`) so `~/.claude` has commands, skills, and rules.

**Repository / project root**

- Open a **git clone** of this repo (or your fork) in Claude Code, **or** a research repo that already copies these commands into `~/.claude`.

**Per-research project directory** (required)

- Run **`/new-project "Your paper title"`** (or `python scripts/pipeline_state.py init --project <kebab-slug>`).
- This sets **`pipeline-state.json`** → `project_dir` = `projects/<slug>/`.
- **All** pipeline outputs (docs, code, results, manuscript) go under that folder — not under the plugin repo root.

**Optional but typical**

- **`.claude/settings.local.json`** — Zotero / API keys if you use online steps.
- **Obsidian** binding via **`/obsidian-init`** if you use the vault workflow.

**Nothing to put in quotes** for `/run-pipeline`: flags are `--auto`, `--resume`, `--from <step_id>`, `--status`, `--reset`, `--skip-online` (see `commands/run-pipeline.md`).

### Where the research question lives (what you edit)

- **First anchor**: the string you pass to **`/new-project "…"`** — becomes the project title and folder `projects/<slug>/`; it is *not* a separate file by itself.
- **After literature / formulation (step 3 in v3)**: the pipeline expects a written hypothesis document. The command **`/research-init`** (used as `formulate-hypotheses` in the pipeline) writes:
  - **`$PROJECT_DIR/docs/hypotheses.md`** — main place for **research question + hypotheses** (you can edit this file directly).
  - Optionally **`$PROJECT_DIR/docs/research-proposal.md`** and **`$PROJECT_DIR/docs/literature-review.md`** from the same step.
- **Some** later commands refer to `hypotheses.md` at the project root in examples; keep a **single canonical copy** under **`docs/hypotheses.md`** unless you standardize otherwise. Downstream steps (`/claim-search`, `/design-experiments`, gates) read the hypothesis content from there.

**Yes — creating a project always targets `projects/<slug>/`** (slug from the name you give `/new-project`). That directory is the only place pipeline artifacts for that paper should live.

---

## 2. `/run-experiment` — what goes after the command?

There is **no** string in `'` `'` that you must pass. The command is defined in `commands/run-experiment.md` with **one optional argument**:

| Invocation | Meaning |
|------------|---------|
| `/run-experiment` | Run the **next pending phase** according to `$PROJECT_DIR/experiment-state.json`. |
| `/run-experiment phase=2` | Run **phase 2** explicitly (numeric phase id used by your `experiment-state.json` / `run-manifest`). |

So: **`phase=<number>`**, not a file path. If your project uses string phase keys (`phase_1`, `phase_2`), the implementation in Claude should map that to the same numbering (convention: phase 1 = quick validation, etc.) — align with `experiment-plan.md` and `experiment-state.json`.

**Prerequisites before `/run-experiment` can do anything useful** (pipeline steps 9–17 completed in order):

| Step | Command | Produces (under `$PROJECT_DIR`) |
|------|---------|----------------------------------|
| 9 | `/design-experiments` | `docs/experiment-plan.md` (matrix, seeds, phases) |
| 11–15 | `/scaffold` … `/validate-setup` | `src/`, `configs/`, working code |
| 16 | `/download-data` | Data/cache ready on cluster |
| 17 | `/plan-compute` | `docs/compute-plan.md`, SLURM scripts (e.g. `cluster/` or `scripts/` as in your plan) |

**Runner state**

- **`experiment-state.json`** — tracks phases, job IDs, gates. Often created/updated by `experiment-design` / runner; if missing, the agent should initialize from `experiment-plan.md`.

**Pre-flight** (from `commands/run-experiment.md`): data offline check, dry-run, `sinfo`, venv in sbatch, commit hash recorded.

---

## 3. Minimal example layout (works with v3 + compute budget)

Below is a **minimal** `projects/<slug>/` tree that matches the pipeline and `run-experiment` expectations:

```
projects/my-paper/
├── pipeline-state.json          # symlink or note: root pipeline-state.json points here
├── experiment-state.json        # phases, jobs, gates (runner)
├── docs/
│   ├── experiment-plan.md       # matrix: conditions × seeds (default 5 seeds), phases
│   └── compute-plan.md          # from /plan-compute; GPU/time, array strategy
├── cluster/                     # or scripts/ — your sbatch + launchers from plan-compute
│   ├── run_phase1.sh
│   └── ...
├── src/
│   └── main.py                  # entry (Hydra optional)
├── configs/
│   └── config.yaml
├── results/
└── logs/
```

**`docs/experiment-plan.md` (excerpt)** — defines *what* to run:

```markdown
## Run matrix
- Conditions: A (baseline), B (proposed)
- Seeds per condition: 5 (1, 2, 3, 4, 5)
- Phases:
  - Phase 1: condition A only, 1 seed — smoke
  - Phase 2: A and B × 5 seeds — main comparison

## Primary metric
Macro-F1 on validation set.
```

**Compute validation** (before locking SLURM):

```bash
python scripts/compute_budget_check.py --seeds 5 --conditions 2 --gpus-per-job 1
```

**`/run-experiment`** then:

1. Reads `compute-plan.md` + scripts in `cluster/`.
2. Submits jobs (prefer **1 GPU per job**, **array** for seeds — see `rules/compute-budget.md`).
3. Updates `experiment-state.json` and `results/`.

---

## 4. Relationship to `pipeline-state.json` (root)

- **`pipeline-state.json`** (repo root): which **pipeline step** is next (`research-landscape`, `run-experiment`, …).
- **`experiment-state.json`** (`$PROJECT_DIR`): **experiment execution** only (phases, SLURM jobs, gates).

Do not confuse the two.

---

## See also

- [`commands/run-pipeline.md`](../commands/run-pipeline.md) — full 38 steps
- [`commands/run-experiment.md`](../commands/run-experiment.md) — pre-flight, batching, paths
- [`docs/PROJECT_LAYOUT.md`](PROJECT_LAYOUT.md) — where `projects/<slug>/` comes from
- [`rules/compute-budget.md`](../rules/compute-budget.md) — 5 seeds, 1 GPU/job, arrays
