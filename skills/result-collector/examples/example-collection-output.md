# Example Collection Output

Demonstrates the output of `result-collector` for a small experiment:
3 models x 2 datasets x 3 seeds = 18 expected runs.

## results.csv

```csv
model,dataset,seed,method,ablation,primary_metric,accuracy,f1_score,loss,wall_time_seconds,gpu_memory_peak_mb
transformer,cifar10,42,proposed,none,0.9234,0.9234,0.9218,0.2871,3842.5,11234.0
transformer,cifar10,123,proposed,none,0.9251,0.9251,0.9240,0.2803,3901.2,11198.0
transformer,cifar10,456,proposed,none,0.9219,0.9219,0.9201,0.2912,3877.8,11245.0
transformer,imagenet,42,proposed,none,0.7812,0.7812,0.7645,0.8934,14523.1,23456.0
transformer,imagenet,123,proposed,none,0.7798,0.7798,0.7631,0.9012,14612.7,23501.0
transformer,imagenet,456,proposed,none,0.7825,0.7825,0.7660,0.8887,14498.3,23478.0
resnet50,cifar10,42,baseline,none,0.9112,0.9112,0.9098,0.3201,1245.3,4512.0
resnet50,cifar10,123,baseline,none,0.9098,0.9098,0.9081,0.3245,1232.1,4498.0
resnet50,cifar10,456,baseline,none,0.9125,0.9125,0.9110,0.3178,1251.7,4521.0
resnet50,imagenet,42,baseline,none,0.7623,0.7623,0.7456,0.9523,8901.4,12345.0
resnet50,imagenet,123,baseline,none,0.7601,0.7601,0.7434,0.9601,8945.2,12312.0
resnet50,imagenet,456,baseline,none,0.7634,0.7634,0.7468,0.9489,8878.9,12356.0
mlp_mixer,cifar10,42,baseline,none,0.8945,0.8945,0.8912,0.3567,987.3,3201.0
mlp_mixer,cifar10,123,baseline,none,0.8923,0.8923,0.8890,0.3612,992.1,3198.0
mlp_mixer,cifar10,456,baseline,none,0.8958,0.8958,0.8928,0.3534,981.5,3205.0
mlp_mixer,imagenet,42,baseline,none,0.7234,0.7234,0.7012,1.0823,7234.5,11023.0
```

Note: 16 of 18 expected runs shown. The 2 missing runs are reported in the gap report below.

## summary.csv

```csv
model,dataset,method,ablation,metric_mean,metric_std,metric_ci_lower,metric_ci_upper,n_seeds
transformer,cifar10,proposed,none,0.9235,0.0016,0.9195,0.9274,3
transformer,imagenet,proposed,none,0.7812,0.0014,0.7777,0.7846,3
resnet50,cifar10,baseline,none,0.9112,0.0014,0.9078,0.9145,3
resnet50,imagenet,baseline,none,0.7619,0.0017,0.7578,0.7661,3
mlp_mixer,cifar10,baseline,none,0.8942,0.0018,0.8898,0.8986,3
mlp_mixer,imagenet,baseline,none,0.7234,,,1
```

Note: `mlp_mixer` on `imagenet` has only 1 completed seed, so confidence intervals are not computed.

## gap-report.md

```markdown
# Gap Report

Generated: 2026-03-27T14:32:00Z
Expected runs: 18
Completed: 16
Missing/Failed/Incomplete: 2

## Missing Runs

| Model | Dataset | Seed | Method | Ablation | Status | Reason |
|-------|---------|------|--------|----------|--------|--------|
| mlp_mixer | imagenet | 123 | baseline | none | failed | CUDA out of memory |
| mlp_mixer | imagenet | 456 | baseline | none | incomplete | Wall-time limit exceeded |

## Failure Details

### mlp_mixer_imagenet_123_baseline_none
- **Status**: failed
- **Output directory**: outputs/mlp_mixer/imagenet/seed_123/
- **Last error**: RuntimeError: CUDA out of memory. Tried to allocate 2.34 GiB
- **Log tail**:
  Epoch 45/100, batch 312/625
  Loss: 1.0912
  RuntimeError: CUDA out of memory. Tried to allocate 2.34 GiB (GPU 0; 24.00 GiB total)
  Training terminated.

### mlp_mixer_imagenet_456_baseline_none
- **Status**: incomplete
- **Output directory**: outputs/mlp_mixer/imagenet/seed_456/
- **Last error**: Process killed after exceeding 8h wall-time limit
- **Log tail**:
  Epoch 72/100, batch 501/625
  Loss: 1.0534
  [SLURM] Job exceeded wall-time limit
  [SLURM] Sending SIGTERM

## Recommended Actions

- Re-run mlp_mixer/imagenet/seed_123 with reduced batch size (current: 256, try: 128) or enable gradient checkpointing
- Re-run mlp_mixer/imagenet/seed_456 with increased wall-time limit (current: 8h, try: 12h)
```
