---
name: download-data
description: Download all datasets and pretrained models to local cache before GPU jobs. Must run on login node BEFORE /run-experiment.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to docs/experiment-plan.md in project dir)
    required: false
    default: docs/experiment-plan.md
tags: [Pipeline, Data, Setup]
---

# Download Data Command

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` -> `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Download logs -> `$PROJECT_DIR/logs/`
- Cached data -> `$PROJECT_DIR/data/` or `~/.cache/huggingface/`

Never write data files to the repository root.

## Purpose

Ensure all datasets and model weights are cached locally so SLURM GPU jobs do NOT need internet access.

## Instructions

1. Read `$PROJECT_DIR/docs/experiment-plan.md` to identify ALL datasets and models needed
2. For each dataset: download via HuggingFace `datasets` library or direct URL
3. For each model: download via `transformers` AutoModel.from_pretrained()
4. Save everything to the HuggingFace cache (~/.cache/huggingface/) or $PROJECT_DIR/data/
5. Verify each download succeeded
6. Print a summary: "Downloaded N datasets, M models, total size X GB"

## Validation

Run a quick import test for each dataset and model to confirm they load from cache without network access:

```python
import os
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
# Try loading each dataset and model — must succeed
```

If any download fails, log the error and try alternative sources. Do NOT proceed to /run-experiment until all downloads succeed.

## Usage

```bash
/download-data                              # reads experiment-plan.md from project dir
/download-data path/to/custom-plan.md       # explicit plan file
```

## Workflow

1. Read experiment-plan.md to identify datasets and models
2. Download each dataset and model to local cache
3. Run offline validation to confirm all assets load without network
4. Write download manifest to `$PROJECT_DIR/docs/download-manifest.md`

## Integration

- **Prerequisite**: `validate-setup` output (validated pipeline)
- **Feeds into**: `plan-compute`, `run-experiment` (ensures GPU jobs have cached data)
