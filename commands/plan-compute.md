---
name: plan-compute
description: Estimate GPU resources, select cluster partitions, design scheduling strategy, and generate SLURM scripts for MIT Engaging or other HPC clusters.
args:
  - name: plan_file
    description: Path to experiment plan (defaults to experiment-plan.md)
    required: false
    default: experiment-plan.md
tags: [Research, HPC, SLURM, Cluster]
---

# Plan Compute Command

Estimate resources and generate cluster submission scripts.

## Goal

Activates the `compute-planner` skill to estimate GPU memory/time/storage, select partitions, design scheduling strategy, and generate SLURM sbatch scripts.

## Usage

```bash
/plan-compute                      # reads experiment-plan.md + validation-report.md
/plan-compute path/to/plan.md      # explicit plan file
```

## Workflow

1. Parse run matrix from experiment-plan.md
2. Read timing data from validation-report.md (smoke test)
3. Activate `compute-planner` skill
4. Write: compute-plan.md, cluster/ directory with sbatch scripts, launch.sh, monitor.sh

## Integration

- **Primary skill**: `compute-planner`
- **Prerequisite**: `experiment-plan.md`, `validation-report.md` (smoke test timing)
- **Feeds into**: `experiment-runner` (provides SLURM scripts)
