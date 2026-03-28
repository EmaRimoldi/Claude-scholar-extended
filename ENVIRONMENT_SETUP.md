# Environment Setup

## Quick Start

```bash
# 1. Activate the project venv (Python 3.12, managed by uv)
cd rag-lit-synthesis
source .venv/bin/activate

# 2. Verify
python --version   # Should show 3.12.x
python -c "import torch; print(torch.__version__)"
```

## First-Time Setup

If the `.venv` directory doesn't exist yet:

```bash
cd rag-lit-synthesis
uv venv --python 3.12 .venv
source .venv/bin/activate
uv sync
```

## System Requirements

| Requirement | This System | Status |
|---|---|---|
| Python 3.10+ | 3.12.13 (via uv) | Installed |
| uv | 0.10.11 | Installed |
| Node.js | v24.14.1 (via nvm) | Installed |
| npm | 11.11.0 | Installed |
| CUDA | 12.4.0 / 12.9.1 / 13.0.1 / 13.1.0 (modules) | Available |
| GPU | Login node: none. Compute nodes: check with `sinfo` | Available on compute |

## Loading CUDA (for GPU compute nodes)

```bash
module load cuda/12.4.0    # or cuda/13.0.1 for torch 2.11
module load cudnn/9.8.0.87-cuda12
```

## Key Paths

| Component | Path |
|---|---|
| Project root | `/home/erimoldi/projects/Claude-scholar-extended` |
| Python venv | `rag-lit-synthesis/.venv/` |
| uv binary | `~/.local/bin/uv` |
| Node.js | `~/.nvm/versions/node/v24.14.1/bin/node` |
| zotero-mcp | `~/.nvm/versions/node/v24.14.1/lib/node_modules/zotero-mcp/build/index.js` |

## Git Authentication

Git is configured with credential store (`~/.git-credentials`). Push works without
manual token entry:

```bash
git push origin main   # Just works
```

To update the stored token, edit `~/.git-credentials`.

## Installed Python Packages (Key)

| Package | Version | Purpose |
|---|---|---|
| torch | 2.11.0+cu130 | Model inference |
| transformers | 5.4.0 | LLM loading |
| sentence-transformers | 5.3.0 | Dense retrieval |
| faiss-cpu | 1.13.2 | Vector indexing |
| hydra-core | 1.3.2 | Config management |
| rouge-score | 0.1.2 | ROUGE metric |
| bert-score | 0.3.13 | BERTScore metric |
| scipy | 1.17.1 | Statistical tests |
| rank-bm25 | 0.2.2 | Sparse retrieval |
