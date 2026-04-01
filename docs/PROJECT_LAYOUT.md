# Where research artifacts live

This repository is an **ALETHEIA / Claude Code workflow bundle**. Outputs for a **research line or paper** are **not** scattered at the repo root: they go under a dedicated project folder.

## Canonical path: `projects/<slug>/`

When you run **`/new-project "Title of your paper or topic"`**, the command creates:

```
projects/<slug>/
├── docs/           # literature, hypotheses, experiment-plan.md, compute-plan.md, …
├── configs/        # Hydra / OmegaConf
├── src/            # experiment code after /scaffold
├── data/
├── results/
├── manuscript/
├── logs/
├── notebooks/
└── .epistemic/     # created during v3 pipeline (citation ledger, claim graph, …)
```

The slug is **kebab-case** derived from the title (e.g. `sparse-attention-hatexplain`).

**`pipeline-state.json`** at the **repository root** stores `project_dir` (e.g. `projects/<slug>`). Commands such as **`/run-pipeline`**, **`/plan-compute`**, and **`/produce-manuscript`** must resolve **`$PROJECT_DIR`** from that file and write **only** under that directory.

So: **new “paper” work for this workflow = one folder under `projects/<name>/`**, not a new top-level repo unless you intentionally split repositories.

## Zotero and PDFs

- **Bibliographic records and PDFs** live in **Zotero** (local or synced library), not automatically under `projects/`.
- The pipeline produces **Markdown reports** (e.g. literature notes, claim maps) under **`$PROJECT_DIR/docs/`** (or your Obsidian vault if you use **`/obsidian-init`** — see [OBSIDIAN_SETUP.md](../OBSIDIAN_SETUP.md)).

## Obsidian (optional)

If you bind a vault via **`.claude/project-memory/registry.yaml`**, durable notes may mirror into  
`Vault/Research/<slug>/Papers/`, `…/Writing/`, etc., while the **code and numeric results** remain in **`projects/<slug>/`** in the git repo.

## Switching between papers

Only one active **`project_dir`** is tracked in root **`pipeline-state.json`**. To work on another paper, re-run **`/new-project`** for the other slug (or re-init **`pipeline_state.py`** with the other project) so the active `project_dir` matches the worktree you are editing.
