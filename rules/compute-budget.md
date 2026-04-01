# Compute Budget (Cluster GPU / Seeds)

ALETHEIA defaults avoid **over-allocating GPUs** and **excessive seed counts** when generating SLURM scripts and experiment plans.

## Defaults (must follow unless user explicitly overrides)

1. **Seeds per experimental condition**: **5** (not 10). Use **3** for quick validation, **5** for paper-quality variance; use **more than 5** only with a written power-analysis or venue-specific requirement and **`--allow-extra-seeds`** when running checks.
2. **GPUs per training job**: **1** (`#SBATCH --gres=gpu:<type>:1`). Multi-GPU is only for documented model/data parallel setups, not for “running seeds in parallel on one fat job.”
3. **Seed sweeps**: implement with **SLURM job arrays** (`#SBATCH --array=0-4` for 5 seeds), one array **task** = one seed, **each task uses 1 GPU**. Do **not** request `N_experiments × N_seeds` GPUs in a **single** job (e.g. never `--gres=gpu:90`).
4. **Concurrency**: total **simultaneous** single-GPU jobs is bounded by the partition and fair share (often **~8** on shared queues); submit in **waves** or use array tasks so the scheduler maps many runs without one job owning 90 GPUs.

## Relationship to pipeline steps

- **`/design-experiments`** — seed count and statistical power should align with these defaults.
- **`/plan-compute`** — must apply these rules when generating `compute-plan.md` and `sbatch` scripts.
- **`/run-experiment`** — submission must match the plan (arrays, 1 GPU per task).

## Validation

Run before committing a compute plan to the repo or before bulk submission:

```bash
python scripts/compute_budget_check.py --seeds 5 --conditions 9 --gpus-per-job 1
```

See `config/compute_defaults.yaml` for tunable numbers.
