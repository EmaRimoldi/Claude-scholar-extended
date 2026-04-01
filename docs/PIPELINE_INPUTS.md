# What you need to run the pipeline (and `/run-experiment`)

This document answers: **what artifacts must exist before the orchestrator or `/run-experiment` can run**, and **what the slash command arguments mean**.

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
