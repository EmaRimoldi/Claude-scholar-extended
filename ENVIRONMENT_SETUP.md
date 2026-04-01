# Environment Setup

This repository is the **Claude Scholar** plugin and workflow bundle. There is **no** root `pyproject.toml`; scaffolded research projects live under `projects/<slug>/` with their own Python environment after `/scaffold`.

## Prerequisites

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for the full checklist (Claude Code CLI, Python 3.10+, uv, Git, optional Zotero, SLURM, LaTeX).

## Verify from the repo root

```bash
python3 --version    # 3.10+
uv --version
node --version       # optional; for npm-based tooling
python3 scripts/pipeline_state.py steps | head
```

## Python environment for bundled scripts

Pipeline helpers in `scripts/` use mostly the stdlib; some scripts need `pandas`, `numpy`, `scipy`, `statsmodels`, and/or `matplotlib` ([scripts/README.md](scripts/README.md)). Create a venv at the repo root if you run those scripts often:

```bash
cd /path/to/Claude-scholar-extended
uv venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install pandas numpy scipy statsmodels matplotlib
```

Research code under `projects/<slug>/` should use that project’s own `uv sync` after scaffolding.

## Credentials

Copy `settings.json.template` to `.claude/settings.local.json` and configure keys as in [docs/QUICKSTART.md](docs/QUICKSTART.md#credential-setup).

## Cluster jobs (optional)

If you use SLURM, see `scripts/run_on_cluster.sh` and `scripts/slurm/`. Partitions and GPU types are site-specific; regenerate or edit profiles with `scripts/slurm/cluster_profile.py` for your cluster.
