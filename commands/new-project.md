---
name: new-project
description: Create a new research project with standardized folder structure. Initializes project directory, pipeline state, and placeholder files.
args:
  - name: name
    description: Project name or research topic (will be converted to kebab-case slug)
    required: true
tags: [Project, Scaffold, Pipeline, Research]
---

# /new-project - Create New Research Project

Initialize a standardized project directory for a new research topic.

## Usage

```bash
/new-project "Sparse Rationale Attention for Hate Speech"
/new-project my-experiment-name
```

## Workflow

### 1. Derive project slug

Convert "$name" to a kebab-case slug:
- Lowercase all characters
- Replace spaces and underscores with hyphens
- Remove special characters
- Truncate to 50 characters max
- Example: "Sparse Rationale Attention for Hate Speech" → `sparse-rationale-attention-for-hate-speech`

### 2. Create project directory structure

Create the following structure under `projects/<slug>/`:

```
projects/<slug>/
├── docs/
│   └── README.md          # "Research documents for <name>"
├── configs/
│   └── README.md          # "Hydra/OmegaConf configuration files"
├── src/
│   └── README.md          # "Source code"
├── data/
│   └── .gitkeep
├── results/
│   ├── tables/
│   │   └── .gitkeep
│   └── figures/
│       └── .gitkeep
├── manuscript/
│   └── README.md          # "LaTeX source and submission packages"
├── logs/
│   └── .gitkeep
├── notebooks/
│   └── .gitkeep
└── README.md              # Project overview with name, date, status
```

### 3. Initialize pipeline state

Run:
```bash
python scripts/pipeline_state.py init --project <slug> --topic "Your full research question in one sentence"
```

This creates `pipeline-state.json` in the repo root with `project_dir` set to `projects/<slug>` and optional **`research_topic`** for `/run-pipeline` (especially `--auto` step 1). Omit `--topic` only if you will set `research_topic` manually or rely on the project README.

If `pipeline-state.json` already exists, warn the user and ask if they want to reinitialize with `--force`.

### 4. Create project README

Write `projects/<slug>/README.md` with:

```markdown
# <Original Name>

**Created**: YYYY-MM-DD
**Status**: Planning
**Pipeline state**: See `../../pipeline-state.json`

## Structure

- `docs/` — Research documents (literature review, hypotheses, experiment plan, etc.)
- `configs/` — Hydra/OmegaConf configuration files
- `src/` — Source code (models, data loaders, metrics)
- `data/` — Datasets (gitignored for large files)
- `results/` — Experiment outputs, tables, and figures
- `manuscript/` — LaTeX source and submission packages
- `logs/` — Experiment and pipeline logs
- `notebooks/` — Jupyter notebooks for exploration
```

### 5. Confirmation

Display:

```
Project created: projects/<slug>/
Pipeline state: pipeline-state.json (project_dir = projects/<slug>)

Next steps:
  1. /research-init "<topic>" — Start literature review
  2. /run-pipeline — Run the full research pipeline
```

## Notes

- Only one project can be active in `pipeline-state.json` at a time
- To switch projects, reinitialize with `/new-project --force`
- The project directory is the single source of truth for all research outputs
