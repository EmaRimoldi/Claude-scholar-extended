#!/bin/bash
#SBATCH --job-name=sprattn_C1
#SBATCH --output=logs/slurm_%x_%A_%a.out
#SBATCH --error=logs/slurm_%x_%A_%a.err
#SBATCH --array=0-4
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=mit_normal_gpu

set -e
PROJECT_DIR=/home/erimoldi/projects/Claude-scholar-extended/projects/sparse-rationale-constrained-attention-hate-speech
VENV=/home/erimoldi/projects/Claude-scholar-extended/.venv/bin/python
cd $PROJECT_DIR

SEED=$((42 + SLURM_ARRAY_TASK_ID))
echo "Starting C1 seed=$SEED on $(hostname)"
mkdir -p logs checkpoints/C1/seed_$SEED

$VENV train.py \
    model=bert_softmax_baseline \
    seed=$SEED \
    condition=C1 \
    training.output_dir=checkpoints/C1/seed_$SEED \
    training.device=cuda \
    +training.run_id=C1_seed${SEED}

echo "C1 seed=$SEED complete"
