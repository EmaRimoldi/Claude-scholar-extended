# Pipeline Diagnostic Report

**Date**: 2026-03-28
**Topic**: RAG for Scientific Literature Synthesis
**Mode**: Manual sequential (auto diagnostic)

---

## 1. Summary Table

| # | Step | Status | Notes |
|---|---|---|---|
| 1 | `/research-init` | ⚠️ Completed w/ warnings | Zotero MCP unavailable, used WebSearch fallback |
| 2 | `/check-competition` | -- Skipped | Covered during research-init |
| 3 | `/design-experiments` | ✅ Completed | experiment-plan.md + experiment-state.json |
| 4 | `/scaffold` | ✅ Completed | Full project structure with pyproject.toml, registry, Hydra config |
| 5 | `/build-data` | ✅ Completed | Semantic Scholar API benchmark builder |
| 6 | `/setup-model` | ✅ Completed | BM25/Dense/Hybrid retrievers + LLM synthesizer |
| 7 | `/implement-metrics` | ✅ Completed | Citation, faithfulness, text quality, bias metrics |
| 8 | `/validate-setup` | ⚠️ Completed w/ warnings | 12/23 checks pass — Python 3.6.8 + missing packages |
| 9 | `/plan-compute` | ✅ Completed | Resource estimates + SLURM template |
| 10 | `/run-experiment` | ❌ Failed | No Python 3.10+ or GPU |
| 11 | `/collect-results` | ❌ Failed | No outputs to collect |
| 12 | `/analyze-results` | ⚠️ Completed w/ warnings | Template with placeholders only |
| 13 | `/map-claims` | ✅ Completed | Claim-evidence mapping |
| 14 | `/position` | ✅ Completed | Differentiation matrix + contribution statement |
| 15 | `/story` | ✅ Completed | Paper blueprint + figure plan |
| 16 | `/produce-manuscript` | ⚠️ Completed w/ warnings | LaTeX skeleton — results sections are placeholders |
| 17 | `/rebuttal` | -- Skipped | No reviews received |

**Pipeline Health Score: 13/17 steps completed (2 failed, 2 skipped)**

---

## 2. Issues Found

### 🔴 Blockers (step cannot complete)

| Issue | Step | Impact | Details |
|---|---|---|---|
| **System Python 3.6.8** | 10, 11 | Cannot run experiments | Project requires Python >= 3.10 for type hints, transformers, torch |
| **No ML packages installed** | 10, 11 | Cannot run experiments | torch, transformers, sentence-transformers, faiss, rank_bm25, hydra all missing |
| **No GPU on login node** | 10 | Cannot run model inference | LLaMA-3.1-8B requires ≥16GB VRAM |

### 🟡 Warnings (step completes but with issues)

| Issue | Step | Impact | Details |
|---|---|---|---|
| **Zotero MCP not installed** | 1 | No automated paper management | `zotero-mcp` binary not found; fell back to WebSearch |
| **No BibTeX references.bib** | 1 | Manual citation management | Requires Zotero API for BibTeX export |
| **No Obsidian knowledge base** | 1 | No persistent project memory | registry.yaml not found; `/obsidian-init` not run |
| **Analysis report is template** | 12 | No actual statistical analysis | Depends on experiment data from step 10 |
| **Manuscript has placeholders** | 16 | Results sections empty | Depends on analysis-report.md being populated |

### 🟢 Suggestions (improvements)

| Suggestion | Benefit |
|---|---|
| Install `zotero-mcp` via npm | Full Zotero integration for literature management |
| Run `/obsidian-init` to bootstrap knowledge base | Persistent project memory across sessions |
| Add `__pycache__/` to `.gitignore` | Prevent Python cache from being tracked |
| Add Python version check to pipeline_state.py | Fail fast with clear message |
| Create a `requirements.txt` alongside `pyproject.toml` | Fallback for systems without uv/hatch |

---

## 3. Missing Dependencies

### System-level
| Dependency | Required By | How to Install |
|---|---|---|
| Python 3.10+ | All ML code | `conda create -n rag python=3.10` or `pyenv install 3.10` |
| CUDA toolkit | GPU inference | `module load cuda/12.1` (cluster) or install locally |

### Python packages (install via `uv sync` in Python 3.10+ venv)
| Package | Required By | Version |
|---|---|---|
| torch | Model inference | >= 2.0 |
| transformers | LLM loading | >= 4.40 |
| sentence-transformers | Dense retrieval | >= 3.0 |
| faiss-cpu | Vector indexing | >= 1.7 |
| rank-bm25 | Sparse retrieval | >= 0.2.2 |
| hydra-core | Config management | >= 1.3 |
| rouge-score | ROUGE metric | >= 0.1.2 |
| bert-score | BERTScore metric | >= 0.3.13 |
| scipy | Statistical tests | >= 1.11 |
| numpy | Array operations | >= 1.24 |

### MCP servers (optional but recommended)
| Server | Required By | How to Install |
|---|---|---|
| zotero-mcp | Literature management | `npm install -g zotero-mcp` (check npm registry) |

---

## 4. Credential Issues

| Credential | Status | Issue |
|---|---|---|
| ZOTERO_API_KEY | ✅ Configured | Key in settings.local.json, but zotero-mcp binary missing |
| ZOTERO_LIBRARY_ID | ✅ Configured | — |
| UNPAYWALL_EMAIL | ✅ Configured | — |
| GITHUB_PERSONAL_ACCESS_TOKEN | ✅ Configured | — |
| Semantic Scholar API | ✅ No key needed | Public API, rate-limited (100 req/5min) |
| CrossRef API | ✅ No key needed | Public API |
| arXiv API | ✅ No key needed | Public API |

**All credentials are properly configured.** The only connectivity issue is the missing `zotero-mcp` binary which prevents the MCP server from starting.

---

## 5. Fix Suggestions

### Priority 1: Enable experiment execution

```bash
# Set up Python 3.10+ environment
conda create -n rag-lit python=3.10 -y
conda activate rag-lit

# Install project dependencies
cd rag-lit-synthesis
pip install -e ".[dev]"

# Or with uv:
uv venv --python 3.10
source .venv/bin/activate
uv sync
```

### Priority 2: Enable Zotero integration

```bash
# Install Zotero MCP server (check exact package name)
npm install -g @anthropic/zotero-mcp
# Or: pip install zotero-mcp
```

### Priority 3: Bootstrap Obsidian knowledge base

```
# In Claude Code session:
/obsidian-init
```

### Priority 4: Fix pipeline orchestrator for auto mode

The `/run-pipeline` command works as a prompt-based orchestrator that Claude interprets. For true unattended execution, consider adding a shell script wrapper:

```bash
# scripts/run-pipeline.sh
#!/bin/bash
set -e
for step in research-init design-experiments scaffold build-data ...; do
    echo "Running: $step"
    python3 scripts/pipeline_state.py start "$step"
    # ... invoke claude with the slash command ...
    python3 scripts/pipeline_state.py complete "$step"
done
```

Note: True end-to-end automation requires Claude Code's headless mode or API, since each step is a Claude-interpreted prompt.

---

## 6. Files Generated During This Run

### Research artifacts
| File | Content |
|---|---|
| `literature-review.md` | Literature survey from WebSearch |
| `hypotheses.md` | 4 falsifiable hypotheses (H1-H4) |
| `experiment-plan.md` | Full experiment matrix, metrics, gates |
| `experiment-state.json` | Iteration tracking state |
| `validation-report.md` | Pre-flight checklist results |
| `compute-plan.md` | Resource estimates + SLURM template |
| `analysis-report.md` | Template with placeholders |
| `claim-evidence-map.md` | Claims mapped to evidence |
| `contribution-positioning.md` | Differentiation matrix |
| `paper-blueprint.md` | Narrative arc + figure plan |

### Code artifacts
| File | Content |
|---|---|
| `rag-lit-synthesis/pyproject.toml` | Project config with all dependencies |
| `rag-lit-synthesis/configs/config.yaml` | Hydra experiment config |
| `rag-lit-synthesis/Makefile` | Standard build targets |
| `rag-lit-synthesis/src/registry.py` | Component registry |
| `rag-lit-synthesis/src/main.py` | Hydra entry point |
| `rag-lit-synthesis/src/data/benchmark_builder.py` | Semantic Scholar dataset builder |
| `rag-lit-synthesis/src/retrieval/retrievers.py` | BM25, Dense, Hybrid retrievers |
| `rag-lit-synthesis/src/generation/synthesizer.py` | LLM + NoRetrieval generators |
| `rag-lit-synthesis/src/metrics/citation_metrics.py` | Citation P/R/F1, hallucination count |
| `rag-lit-synthesis/src/metrics/faithfulness.py` | Claim-level faithfulness scoring |
| `rag-lit-synthesis/src/metrics/text_quality.py` | ROUGE + BERTScore |
| `rag-lit-synthesis/src/metrics/bias_analysis.py` | Recency + popularity bias |
| `rag-lit-synthesis/manuscript/main.tex` | LaTeX manuscript skeleton |

### Pipeline state
| File | Content |
|---|---|
| `pipeline-state.json` | 13/17 completed, 2 failed, 2 skipped |
| `logs/pipeline-2026-03-28/run.log` | Step-by-step execution log |
| `logs/diagnostic-report.md` | This report |
