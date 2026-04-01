# Scripts Reference

Deterministic scripts that automate procedural parts of the research pipeline. These scripts reduce token consumption and variance — the LLM delegates mechanical work to them and focuses on judgment.

## Research Pipeline Scripts

### `pipeline_state.py` — Pipeline orchestration state machine

Manages `pipeline-state.json` for the **v3** research pipeline (**38 steps** across six phases). Step IDs and order match [`commands/run-pipeline.md`](../commands/run-pipeline.md).

```bash
python scripts/pipeline_state.py init --project <slug>
python scripts/pipeline_state.py status
python scripts/pipeline_state.py start <step_id>
python scripts/pipeline_state.py complete <step_id>
python scripts/pipeline_state.py fail <step_id> --reason "<msg>"
python scripts/pipeline_state.py skip <step_id>
python scripts/pipeline_state.py reset
```

### `collect_results.py` — Result collection pipeline

Scans experiment outputs, extracts metrics, assembles canonical tables, detects gaps. Replaces procedural sections of the `result-collector` skill.

```bash
python scripts/collect_results.py \
    --results-dir results/ \
    --experiment-plan docs/experiment-plan.md \
    --output-dir analysis-input/
```

**Outputs**: `results.csv`, `summary.csv`, `run-manifest.json`, `gap-report.md`, `figures/`

### `run_statistics.py` — Statistical analysis with automatic test selection

Encodes the statistical decision tree (normality → test selection → post-hoc → effect sizes). Replaces the need to load `statistical-methods.md` (~560 lines).

```bash
python scripts/run_statistics.py \
    --results analysis-input/results.csv \
    --metric primary_metric \
    --groupby strategy,task \
    --output-dir analysis-output/
```

**Outputs**: `stats-appendix.md`, `stats-raw.json`

### `generate_figures.py` — Publication-quality figure generation

Generates bar charts, violin plots, interaction plots, and heatmaps with colorblind-safe palettes (Okabe-Ito) and publication styling.

```bash
python scripts/generate_figures.py \
    --results analysis-input/results.csv \
    --metric primary_metric \
    --groupby strategy,task \
    --output-dir analysis-output/figures/ \
    --format pdf
```

### `check_gates.py` — Phase gate evaluation

Evaluates completion, baseline sanity, variance, and crash gates for experiment phases. Referenced by project Makefiles (`make check-gates`).

```bash
python scripts/check_gates.py \
    --experiment-state experiment-state.json \
    --results-dir results/
```

Exit code 0 = all gates pass, 1 = gate failed.

### `compute_budget_check.py` — Validate seeds / GPUs per job (ALETHEIA defaults)

Enforces default **5 seeds per condition** and **1 GPU per SLURM job** before you lock a compute plan. Fails if seeds or `gpus-per-job` violate policy unless `--allow-extra-seeds` / `--allow-multi-gpu`.

```bash
python scripts/compute_budget_check.py --seeds 5 --conditions 9 --gpus-per-job 1
```

Reads optional numeric overrides from `config/compute_defaults.yaml`.

### `update_experiment_state.py` — Experiment state lifecycle

Manages `experiment-state.json` transitions (planned → running → collecting → analyzing → confirmed).

```bash
python scripts/update_experiment_state.py status
python scripts/update_experiment_state.py update --status running
python scripts/update_experiment_state.py update --job-id cola 12345
python scripts/update_experiment_state.py update --job-status cola completed
python scripts/update_experiment_state.py increment-iteration
```

## Manuscript Scripts

### `compile_manuscript.py` — LaTeX compilation + Overleaf ZIP

Tries compilers in order (tectonic → pdflatex → xelatex), creates Overleaf-ready ZIP.

```bash
python scripts/compile_manuscript.py --project-dir .
python scripts/compile_manuscript.py --no-compile  # ZIP only
```

### `quality_review.py` — Mechanical checks for `/verify-paper`

Extracts programmatically checkable facts from a LaTeX manuscript: title word audit, scope-evidence counts, statistical reporting scan, efficiency claim detection. Invoked as a pre-check from [`commands/verify-paper.md`](../commands/verify-paper.md) (legacy [`commands/quality-review.md`](../commands/quality-review.md) may reuse the same script).

```bash
python scripts/quality_review.py \
    --manuscript-dir manuscript/ \
    --results analysis-input/results.csv \
    --output manuscript/quality-review-data.json
```

## SLURM / Cluster Scripts

### `slurm/submit.py` — SLURM job submission

### `slurm/job_builder.py` — SLURM script generation

### `slurm/cluster_profile.py` — Cluster configuration and partition selection

### `run_on_cluster.sh` — Cluster job launcher wrapper

## Utility Scripts

### `setup.sh` — Environment setup and installation

### `sync_obsidian_to_windows.sh` — Obsidian vault sync to Windows

## Dependencies

Most scripts use only Python stdlib. Exceptions:
- `run_statistics.py`: requires `pandas`, `numpy`, `scipy`, `statsmodels`
- `generate_figures.py`: requires `matplotlib`, `numpy`
- `collect_results.py`: optionally uses `scipy.stats` for CI computation

All dependencies are available in the project's `.venv` (managed by `uv`).

## Integration with Skills

Scripts replace procedural SKILL.md sections. The LLM runs the script first, then applies judgment to the output:

| Script | Replaces procedural parts of | Token savings |
|--------|------------------------------|---------------|
| `collect_results.py` | `result-collector` SKILL.md | ~130 lines |
| `run_statistics.py` | `results-analysis` SKILL.md + `statistical-methods.md` ref | ~660 lines |
| `generate_figures.py` | `results-analysis` SKILL.md + `visualization-best-practices.md` ref | ~100 lines |
| `compile_manuscript.py` | `compile-manuscript.md` command | ~100 lines |
| `quality_review.py` | `verify-paper.md` command (mechanical layer); legacy `quality-review.md` | ~60 lines |
| `check_gates.py` | `experiment-runner` SKILL.md | ~40 lines |
| `update_experiment_state.py` | `experiment-runner` SKILL.md | ~30 lines |
