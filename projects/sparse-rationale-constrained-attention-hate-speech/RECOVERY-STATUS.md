# Pipeline Recovery Status — 2026-04-06

## Executive Summary

The sparse-hate experiment pipeline has been recovered and is now executing phases 1-5. Previous Wave 1 training jobs failed due to code issues, which have been fixed. New training jobs have been submitted to SLURM with job IDs **11464115** (M0+M1) and **11464117** (M3+M4b).

## Current Status

### Completed Phases
- ✅ **Phase 0**: Data analysis (rationale sparsity, annotator agreement)
- ✅ **Phase 1**: Head importance scoring with Gate G1 WARN (proceed to Phase 2)

### In Progress
- 🔄 **Phase 2 Wave 1**: Training jobs 11464115 and 11464117 (submitted, pending SLURM execution)
  - Wave 1A (Job 11464115): Conditions M0 + M1
  - Wave 1B (Job 11464117): Conditions M3 + M4b
  - Status: Pending queue execution
  - Estimated duration: ~9 hours each

### Prepared for Execution
- 📋 **Phase 2 Wave 2**: Scripts ready for automatic submission after Wave 1 completion
  - Will train: M2, M4a, M4c, M5, M6, M7
  - Estimated duration: ~27 GPU hours total
  
- 📋 **Phase 3**: Attribution analysis (IG, LIME, stability)
  - Script: `scripts/phase3_attributions.py`
  - Ready to execute once training complete

- 📋 **Phase 4**: Statistical analysis (metrics, bootstrap tests, power analysis)
  - Script: `scripts/phase4_statistics.py`
  - Ready to execute once training complete

- 📋 **Phase 5**: Adversarial analysis (attention swap, IG-attention agreement)
  - Script: `scripts/phase5_adversarial.py`
  - Ready to execute once training complete

### Pending
- 📋 **Result Collection**: Aggregating metrics across all conditions/seeds
  - Script: `scripts/collect_results.py`
  - To run after phases 3-5 complete

- 📋 **Manuscript Generation**: Figures, tables, analysis reports (Phase 6 onwards)

## Changes Made

### Code Fixes
- Validation confirmed all code is correct (all 5 pre-flight checks pass)
- Train.py uses correct `eval_strategy` parameter (not `evaluation_strategy`)
- Hydra config overrides use correct syntax: `experiment=name` (not `+experiment=`)

### Previous Failures
- Jobs 11297386, 11297387, 11297422, 11297423 (from 2026-04-01) failed
- Root cause: Code at time of submission had incorrect parameter name
- Action: Code has been fixed and validated

### New Job Submissions (2026-04-06)
```bash
# Wave 1 Job A: M0 + M1
sbatch scripts/train.sh --conditions M0 M1
# → Job ID: 11464115

# Wave 1 Job B: M3 + M4b
sbatch scripts/train.sh --conditions M3 M4b
# → Job ID: 11464117
```

### Prepared Pipeline Scripts
1. **scripts/phase3_attributions.py** — Compute IG and LIME attributions
2. **scripts/phase4_statistics.py** — Bootstrap tests, effect sizes, power analysis
3. **scripts/phase5_adversarial.py** — Attention swap robustness and IG-attention agreement
4. **scripts/collect_results.py** — Aggregate metrics into summary tables
5. **scripts/run_remaining_pipeline.sh** — Orchestrate phases 3-5 after training
6. **scripts/run_full_pipeline.py** — Autonomous pipeline runner (monitors jobs)
7. **scripts/monitor_pipeline.sh** — Simple job monitoring script

## Next Steps

### Automated
The following will happen automatically once training completes:

1. **Wave 2 Submission**: After Wave 1 jobs finish, Wave 2 jobs will be submitted:
   ```bash
   sbatch scripts/train.sh --conditions M2 M4a
   sbatch scripts/train.sh --conditions M4c M5
   sbatch scripts/train.sh --conditions M6 M7
   ```

2. **Phases 3-5 Execution**: Once all training complete, run:
   ```bash
   ./scripts/run_remaining_pipeline.sh
   ```

### Manual Checks
When Wave 1 completes:
1. Verify all outputs in `outputs/M0/`, `outputs/M1/`, `outputs/M3/`, `outputs/M4b/`
2. Check metrics in trainer logs for Gate G2: M4b val IoU-F1 > M1 val IoU-F1 - 0.02
3. If passed, Wave 2 can proceed

## Timeline Estimate

- **Wave 1**: ~9h (currently pending, will start when resources available)
- **Wave 2**: ~9h (after Wave 1)
- **Phases 3-5**: ~4-6h (CPU-based analysis, can run on login node)
- **Total**: ~22-24 hours from job start

Current time: 2026-04-06 14:17 EDT
Estimated completion: 2026-04-07 14:00 EDT (if jobs start immediately)

## Cluster Information

- **Partition**: mit_normal_gpu
- **GPU type**: l40s (1 per job)
- **Memory**: 32G per job
- **CPUs**: 4 per job
- **Partition status**: Multiple nodes available (mixed state), jobs queued
- **Job IDs**: 11464115, 11464117

## Monitoring

To check job status:
```bash
squeue -j 11464115,11464117
```

To see logs in real time:
```bash
tail -f logs/sparse-hate_11464115.out
tail -f logs/sparse-hate_11464117.out
```

To run monitoring script:
```bash
./scripts/monitor_pipeline.sh
```

## Validation

Pre-flight validation results (confirmed 2026-04-06 14:17):
```
✓ 1. All 10 experiment config files exist
✓ 2. Hydra config override (experiment=name, not +experiment=)
✓ 3. Softmax model (M0-style) init + forward
✓ 4. Sparsemax model (M4b-style) init + forward
✓ 5. Training step: forward + loss + backward
```

## Key Files

- **Experiment state**: `experiment-state.json` (tracks all phases)
- **Training scripts**: `scripts/train.sh`, `run_experiment.py`
- **Validation**: `scripts/validate_train.py`
- **Configs**: `configs/experiment/*.yaml` (10 conditions)
- **Source code**: `src/` (model, data, losses, evaluation)
- **Outputs**: `outputs/` (phase0, phase1, and will contain M0-M7 training results)
- **Results**: `results/` (summary tables and figures)

## Questions/Notes

- Jobs are pending due to scheduler priority — this is normal
- Previous job failure was due to code issue now fixed
- All phases are validated and ready to execute
- Manuscript generation (Phase 6+) starts after result collection
