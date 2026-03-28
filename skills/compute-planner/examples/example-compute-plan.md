# Compute Plan: ICL Circuit-Algorithm Bridge

**Project**: In-Context Learning Circuit-Algorithm Bridge
**Date**: 2026-03-27
**Cluster**: MIT Engaging
**Primary Partition**: pi_tpoggio (8x A100 80GB)

## Experiment Matrix Summary

From `experiment-plan.md`:
- **Models**: GPT-2 124M, GPT-2 350M, GPT-2 1.3B (3 models)
- **Tasks**: Linear Regression, Sparse Parity, Decision Tree, Mixture-of-Gaussians (4 tasks)
- **Methods**: Full model, attention-ablated, MLP-ablated, head-ablated (4 methods)
- **Seeds**: 5 per configuration
- **Total runs**: 3 models x 4 tasks x 4 methods x 5 seeds = 240 runs

## Resource Estimates

### Per-Run Estimates

| Model | GPU Memory | Wall Time (est.) | Storage/Run |
|-------|-----------|-------------------|-------------|
| GPT-2 124M (fp32, Adam) | ~4.5 GB | ~1.5 h | ~500 MB |
| GPT-2 350M (fp32, Adam) | ~11 GB | ~3.0 h | ~1.2 GB |
| GPT-2 1.3B (mixed prec.) | ~32 GB | ~6.0 h | ~4.0 GB |

Wall time source: smoke test timing from `validation-report.md` (GPT-2 124M, linear regression, 1 seed = 1.2h actual, scaled with 20% margin).

### Aggregate Estimates by Phase

| Phase | Runs | GPUs/Run | Avg Hours/Run | Total GPU-h | Storage |
|-------|------|----------|---------------|-------------|---------|
| 1. Validation | 1 | 1 | 1.5 | 1.5 | 0.5 GB |
| 2. Core (3x4x4, 1 seed) | 48 | 1 | 3.0 | 144.0 | 48 GB |
| 3. Ablations (3x4x3, 1 seed) | 36 | 1 | 3.0 | 108.0 | 36 GB |
| 4. Seeds (48 cells x 4 more seeds) | 192 | 1 | 3.0 | 576.0 | 192 GB |
| **Total** | **277** | | | **829.5** | **276.5 GB** |

Note: Phase 3 ablations overlap with Phase 2 for ablated methods. The 36 runs here represent additional ablation-only configurations not already in Phase 2.

## Partition Assignments

| Phase | Partition | Justification |
|-------|-----------|---------------|
| Phase 1 (validation) | `ou_bcs_high` | Quick turnaround (< 2h), high priority scheduling |
| Phase 2 (core) | `pi_tpoggio` | Long runs (GPT-2 1.3B needs ~6h), 7-day limit provides safety |
| Phase 3 (ablations) | `pi_tpoggio` + `ou_bcs_normal` overflow | Same rationale; spill to BCS if queue > 2h |
| Phase 4 (seeds) | `ou_bcs_low` + `pi_tpoggio` for 1.3B | Bulk parallelism on low priority; 1.3B seeds on pi_tpoggio (need longer wall time margin) |

### Concurrency Plan

- `pi_tpoggio`: 8 concurrent single-GPU jobs (124M and 350M fit 1 GPU each, 1.3B needs 1 A100)
- Phase 2 core experiments: 48 runs / 8 concurrent = 6 batches x ~3h = ~18h wall time
- Phase 4 seed sweeps: 192 runs, split across `ou_bcs_low` (up to 16 concurrent) and `pi_tpoggio` (8 concurrent)

## Scheduling Diagram

```
Phase 1 (validation):  [==]                                          ~1.5h
                            |
Phase 2 (core):             [===============]                        ~18h (8 concurrent)
                                             |
Phase 3 (ablation):                          [===========]           ~14h (8 concurrent)
                                                          |
Phase 4 (seeds):                                          [========] ~24h (24 concurrent across partitions)
                       ──────────────────────────────────────────────
Estimated wall time:   ~57.5 hours (~2.4 days)
```

Gate points:
- After Phase 1: manual check -- does the pipeline produce sensible output?
- After Phase 2: automated check -- are core results consistent? Proceed to ablations?
- After Phase 3: manual check -- do ablation results support the hypothesis? Proceed to full sweep?

## Filesystem Layout

```
/home/<user>/icl-bridge/
    code/                   # Git repo
    configs/                # Hydra configs
    results/                # Final results (copied from scratch)
    cluster/
        launch.sh           # Master launch script
        monitor.sh          # Monitoring script
        job-manifest.txt    # Submitted job IDs
        jobs/               # sbatch scripts
        logs/               # SLURM stdout/stderr

/scratch/<user>/icl-bridge/
    data/                   # Active datasets
    checkpoints/            # Training checkpoints
    outputs/                # Raw experiment outputs

/pool001/tpoggio/shared/
    models/                 # Pretrained GPT-2 weights (shared)
```

## Risk Factors

| Risk | Severity | Mitigation |
|------|----------|------------|
| `ou_bcs_low` preemption during Phase 4 | Medium | Checkpoint every 500 steps; `--requeue` flag; 1.3B runs on `pi_tpoggio` instead |
| GPT-2 1.3B OOM with large batch | Low | Smoke test confirmed batch_size=4 fits in 32 GB; gradient checkpointing available as fallback |
| Scratch purge before results copy | Low | rsync in sbatch epilogue; manual copy after each phase |
| Queue congestion on `pi_tpoggio` | Medium | Fall back to `ou_bcs_normal` for runs < 24h; submit during off-peak hours |
| Wall time exceeded for 1.3B training | Low | 6h estimate with 20% margin = 7.2h; pi_tpoggio limit is 7 days |

## Total Budget

- **Total GPU-hours**: ~830 GPU-hours
- **Estimated wall time**: ~2.4 days (with 8-24 concurrent jobs)
- **Storage**: ~277 GB on scratch (peak), ~50 GB final results on home
- **Partition split**: ~70% pi_tpoggio, ~20% ou_bcs_low, ~10% ou_bcs_normal/high
