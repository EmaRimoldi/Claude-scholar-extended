# GPU Memory Estimation Guide

Reference for estimating GPU memory requirements for transformer model training and inference. All formulas assume a single GPU unless stated otherwise.

## Memory Components

GPU memory during training is consumed by four main components:

```
Peak GPU Memory = Model Parameters + Optimizer States + Activations + Buffer
```

### 1. Model Parameters

The memory for storing model weights depends on the number of parameters and the precision:

| Precision | Bytes/Param | Example: 124M params | Example: 1.3B params |
|-----------|-------------|----------------------|----------------------|
| fp32 | 4 | 496 MB | 5.2 GB |
| fp16 / bf16 | 2 | 248 MB | 2.6 GB |
| int8 | 1 | 124 MB | 1.3 GB |
| int4 | 0.5 | 62 MB | 650 MB |

**Formula**:
```
model_memory = num_params x bytes_per_param
```

### 2. Optimizer States

Different optimizers require different amounts of additional memory:

| Optimizer | Additional Memory | Notes |
|-----------|-------------------|-------|
| SGD | 0 | Only gradients (same size as model) |
| SGD + momentum | 1x model size | Momentum buffer |
| Adam / AdamW (fp32) | 2x model size | First moment (m) + second moment (v) |
| Adam + mixed precision | 2x model size + master weights | fp32 master weights + fp32 m + fp32 v |

**Adam (fp32 training)**:
```
optimizer_memory = num_params x 4 bytes x 2   (m and v, both fp32)
gradient_memory  = num_params x 4 bytes        (gradients in fp32)
total_optimizer  = num_params x 4 bytes x 3    (gradients + m + v)
```

**Adam (mixed precision training)**:
```
# Weights stored in fp16 for forward/backward, fp32 master copy for updates
model_memory     = num_params x 2 bytes        (fp16 weights)
master_weights   = num_params x 4 bytes        (fp32 master copy)
gradient_memory  = num_params x 2 bytes        (fp16 gradients)
optimizer_memory = num_params x 4 bytes x 2    (fp32 m and v)
total            = num_params x (2 + 4 + 2 + 8) = num_params x 16 bytes
```

### 3. Activation Memory

Activations are the intermediate tensors stored during the forward pass for use in the backward pass.

**Transformer activation memory estimate**:
```
activation_memory = batch_size x seq_len x hidden_dim x num_layers x bytes_per_activation x factor
```

Where `factor` accounts for:
- Attention scores: `batch_size x num_heads x seq_len x seq_len x bytes` per layer
- MLP intermediates: typically 4x hidden_dim
- Layer norm buffers
- Residual connections

**Simplified estimate** (practical rule of thumb):
```
activation_memory ~= 2 x model_memory x (batch_size / reference_batch_size)
```

For a more precise estimate per transformer layer:
```
per_layer_activation = batch_size x seq_len x hidden_dim x (
    10 +                              # attention: Q, K, V, scores, output, etc.
    (24 x hidden_dim / seq_len)       # MLP: intermediate activations
) x bytes_per_activation
```

**Gradient checkpointing** reduces activation memory at the cost of recomputation:
```
checkpointed_activation_memory ~= activation_memory / sqrt(num_layers)
```

Typically saves 60-70% of activation memory with ~33% increase in compute time.

### 4. Buffer and Overhead

Additional memory consumers:

- **CUDA context**: ~300-800 MB (allocated on first CUDA call)
- **NCCL buffers** (multi-GPU): ~200-400 MB per GPU
- **Memory fragmentation**: 5-15% overhead due to CUDA memory allocator
- **Temporary buffers**: Workspace for cuBLAS, cuDNN operations

**Practical buffer rule**: Add 15-20% to the sum of the three components above.

## Peak Memory Formula

### Training (fp32, Adam)

```
peak_memory = (num_params x 4)          # model weights
            + (num_params x 4 x 3)      # gradients + Adam m + Adam v
            + activation_memory          # forward pass activations
            + buffer                     # CUDA context + fragmentation

            = num_params x 16 + activations + buffer
```

### Training (mixed precision, Adam)

```
peak_memory = (num_params x 2)          # fp16 model weights
            + (num_params x 4)          # fp32 master weights
            + (num_params x 2)          # fp16 gradients
            + (num_params x 4 x 2)      # fp32 Adam m + v
            + activation_memory          # activations (fp16)
            + buffer

            = num_params x 16 + activations + buffer
```

Note: Mixed precision does NOT save total memory for Adam training (master weights offset the fp16 savings). The benefit is faster compute, not less memory. Activation memory is reduced because activations are in fp16.

### Inference Only

```
peak_memory = (num_params x bytes_per_param) + activation_memory + buffer
```

Much smaller than training because no optimizer states or gradients.

## Practical Examples

### GPT-2 124M on A100 80GB

```
Model params: 124M
Precision: fp32
Optimizer: Adam

Model weights:       124M x 4B  =   496 MB
Optimizer states:    124M x 12B =  1,488 MB
Activations (bs=8):              ~  2,000 MB  (estimate)
Buffer:                          ~    500 MB
                                 ──────────
Peak estimate:                   ~  4,484 MB  (~4.4 GB)
A100 headroom:                      75.6 GB remaining

Concurrent jobs on one A100:        ~16 (conservative)
```

### GPT-2 350M on A100 80GB

```
Model params: 350M
Precision: fp32
Optimizer: Adam

Model weights:       350M x 4B  =  1,400 MB
Optimizer states:    350M x 12B =  4,200 MB
Activations (bs=8):              ~  5,000 MB  (estimate)
Buffer:                          ~    800 MB
                                 ──────────
Peak estimate:                   ~ 11,400 MB  (~11.1 GB)
A100 headroom:                      68.9 GB remaining

Concurrent jobs on one A100:        ~6 (conservative)
```

### GPT-2 1.3B on A100 80GB

```
Model params: 1.3B
Precision: mixed (fp16 forward, fp32 optimizer)
Optimizer: Adam

fp16 weights:        1.3B x 2B  =  2,600 MB
fp32 master weights: 1.3B x 4B  =  5,200 MB
fp16 gradients:      1.3B x 2B  =  2,600 MB
fp32 Adam m + v:     1.3B x 8B  = 10,400 MB
Activations (bs=4):              ~ 10,000 MB  (fp16, estimate)
Buffer:                          ~  1,500 MB
                                 ──────────
Peak estimate:                   ~ 32,300 MB  (~31.5 GB)
A100 headroom:                      48.5 GB remaining

Concurrent jobs on one A100:        2 (tight)
```

## Memory Profiling Tools

### PyTorch Memory Stats

```python
import torch

# Peak memory allocated
print(f"Peak: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")

# Current memory allocated
print(f"Current: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

# Memory reserved by caching allocator
print(f"Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

# Reset peak stats
torch.cuda.reset_peak_memory_stats()
```

### NVIDIA SMI (from SLURM job)

```bash
# Snapshot GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Continuous monitoring (every 5 seconds)
nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv -l 5
```

### Memory Summary

```python
# Detailed memory summary
print(torch.cuda.memory_summary())
```

## Quick Estimation Cheat Sheet

| Model Size | fp32 Training (Adam) | Mixed Precision Training | Inference (fp16) |
|-----------|----------------------|--------------------------|-------------------|
| 100M | ~3 GB | ~3 GB | ~0.5 GB |
| 350M | ~11 GB | ~10 GB | ~1.5 GB |
| 1.3B | ~35 GB | ~32 GB | ~4 GB |
| 7B | ~180 GB (multi-GPU) | ~120 GB (multi-GPU) | ~15 GB |
| 13B | ~340 GB (multi-GPU) | ~220 GB (multi-GPU) | ~27 GB |

Notes:
- Estimates include activation memory for batch_size=4, seq_len=1024
- Actual memory varies significantly with batch size and sequence length
- Gradient checkpointing can reduce activation memory by ~60%
- These are rough estimates -- always validate with a smoke test
