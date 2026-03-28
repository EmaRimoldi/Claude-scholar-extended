# Compute Plan: RAG Literature Synthesis

## Resource Requirements

### Phase 1: Data Construction (CPU only)
- Semantic Scholar API calls: ~15 topics × ~3 requests each = ~45 API calls
- Time: ~20 minutes (rate-limited)
- Resources: Any machine with internet

### Phase 2: Retrieval Index Building
| Component | Resource | Time | Memory |
|---|---|---|---|
| BM25 index | CPU | ~5 min / topic | 2 GB RAM |
| Dense embeddings (BGE-base) | 1× GPU (any) | ~15 min / topic | 4 GB VRAM |
| FAISS index | CPU | ~2 min / topic | 2 GB RAM |

### Phase 3: Generation
| Model | VRAM | Time per topic | Total (15 topics × 3 seeds) |
|---|---|---|---|
| LLaMA-3.1-8B | 16 GB (fp16) | ~10 min | ~7.5 h |
| Mistral-7B-v0.3 | 14 GB (fp16) | ~8 min | ~6 h |
| GPT-4o (API) | N/A | ~2 min | ~1.5 h + $cost |

### Phase 4: Evaluation
| Metric | Resource | Time |
|---|---|---|
| ROUGE, citation metrics | CPU | ~1 min total |
| BERTScore | 1× GPU | ~30 min total |
| Bias analysis | CPU | ~1 min total |

## Total Estimate

| Resource | Estimate |
|---|---|
| GPU hours (local models) | ~15 h (1× A100 or 2× RTX 3090) |
| API cost (GPT-4o) | ~$5–10 |
| Wall clock time | ~2 days with 1 GPU |
| Storage | ~5 GB (corpus + outputs) |

## SLURM Configuration (if cluster available)

```bash
#!/bin/bash
#SBATCH --job-name=rag-lit-synth
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=logs/slurm-%j.out

module load python/3.10 cuda/12.1
source .venv/bin/activate
python -m src.main retrieval.method=$1 generation.model=$2 project.seed=$3
```

## Scheduling Strategy

1. **Day 1**: Data construction + BM25 baseline (CPU only)
2. **Day 2**: Dense retrieval + LLaMA generation (GPU)
3. **Day 3**: Mistral generation + GPT-4o API calls + evaluation
