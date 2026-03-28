# Architecture Discovery Reference

Detailed guide to programmatically inspecting model architecture, enumerating modules, identifying transformer components, and generating structured architecture reports.

## A. Using `named_modules()` and `named_parameters()`

### Enumerating All Modules

```python
for name, module in model.named_modules():
    print(f"{name}: {type(module).__name__}")
```

This traverses the entire module tree depth-first. Each entry includes:
- `name`: Dot-separated path (e.g., `transformer.h.0.attn.c_attn`)
- `module`: The `nn.Module` instance

### Distinguishing Container vs. Leaf Modules

Container modules (Sequential, ModuleList, ModuleDict) hold other modules but have no learnable parameters of their own. Leaf modules (Linear, Conv2d, LayerNorm) perform computation.

```python
def is_leaf_module(module: nn.Module) -> bool:
    """A leaf module has no child modules."""
    return len(list(module.children())) == 0
```

### Counting Parameters Per Module

```python
def module_param_count(module: nn.Module) -> int:
    """Count parameters owned directly by this module (not children)."""
    return sum(p.numel() for p in module.parameters(recurse=False))

def total_param_count(model: nn.Module) -> int:
    """Count all parameters in the model."""
    return sum(p.numel() for p in model.parameters())
```

### Listing Parameters with Shapes

```python
for name, param in model.named_parameters():
    print(f"{name}: {param.shape}, dtype={param.dtype}, requires_grad={param.requires_grad}")
```

## B. Identifying Transformer Components by Type

### Standard Component Types

Map PyTorch and HuggingFace module types to semantic roles:

```python
ATTENTION_TYPES = (
    "Attention", "MultiheadAttention", "SelfAttention",
    "GPT2Attention", "LlamaAttention", "BertSelfAttention",
    "MistralAttention", "GemmaAttention",
)

MLP_TYPES = (
    "MLP", "GPT2MLP", "LlamaMLP", "BertIntermediate",
    "BertOutput", "MistralMLP", "GemmaMLP",
)

NORM_TYPES = (
    "LayerNorm", "RMSNorm", "LlamaRMSNorm", "BatchNorm1d",
    "GroupNorm",
)

EMBEDDING_TYPES = (
    "Embedding", "GPT2Embedding",
)


def classify_module(module: nn.Module) -> str:
    """Classify a module by its semantic role in a transformer."""
    type_name = type(module).__name__
    if any(t in type_name for t in ATTENTION_TYPES):
        return "attention"
    elif any(t in type_name for t in MLP_TYPES):
        return "mlp"
    elif any(t in type_name for t in NORM_TYPES):
        return "normalization"
    elif any(t in type_name for t in EMBEDDING_TYPES):
        return "embedding"
    elif isinstance(module, nn.Linear):
        return "linear"
    else:
        return "other"
```

### Extracting Transformer Hyperparameters

For HuggingFace models, read directly from the config:

```python
from transformers import AutoConfig

config = AutoConfig.from_pretrained(model_name)

num_layers = getattr(config, "num_hidden_layers", getattr(config, "n_layer", None))
num_heads = getattr(config, "num_attention_heads", getattr(config, "n_head", None))
hidden_dim = getattr(config, "hidden_size", getattr(config, "n_embd", None))
head_dim = hidden_dim // num_heads if (hidden_dim and num_heads) else None
vocab_size = getattr(config, "vocab_size", None)
max_seq_len = getattr(config, "max_position_embeddings", getattr(config, "n_positions", None))
```

For custom models, infer from module shapes:

```python
def infer_transformer_params(model: nn.Module) -> dict:
    """Infer transformer hyperparameters from module shapes."""
    info = {"num_layers": 0, "num_heads": None, "hidden_dim": None, "head_dim": None}

    for name, module in model.named_modules():
        role = classify_module(module)
        if role == "attention":
            info["num_layers"] += 1
        if role == "linear" and info["hidden_dim"] is None:
            # First linear layer's input features is likely the hidden dimension
            if hasattr(module, "in_features"):
                info["hidden_dim"] = module.in_features

    return info
```

## C. Handling Different Transformer Implementations

### HuggingFace GPT-2

```
GPT2Model
  transformer
    wte (Embedding)                         # Token embeddings
    wpe (Embedding)                         # Position embeddings
    h (ModuleList)
      0 (GPT2Block)
        ln_1 (LayerNorm)                    # Pre-attention norm
        attn (GPT2Attention)
          c_attn (Conv1D)                   # Q, K, V projection (fused)
          c_proj (Conv1D)                   # Output projection
        ln_2 (LayerNorm)                    # Pre-MLP norm
        mlp (GPT2MLP)
          c_fc (Conv1D)                     # Up projection
          c_proj (Conv1D)                   # Down projection
      1 (GPT2Block) ...
    ln_f (LayerNorm)                        # Final norm
```

Key: GPT-2 uses `Conv1D` (not `Linear`) for projections. `c_attn` fuses Q, K, V into one matrix.

### HuggingFace LLaMA

```
LlamaModel
  model
    embed_tokens (Embedding)
    layers (ModuleList)
      0 (LlamaDecoderLayer)
        self_attn (LlamaAttention)
          q_proj (Linear)
          k_proj (Linear)
          v_proj (Linear)
          o_proj (Linear)
        mlp (LlamaMLP)
          gate_proj (Linear)
          up_proj (Linear)
          down_proj (Linear)
        input_layernorm (LlamaRMSNorm)
        post_attention_layernorm (LlamaRMSNorm)
      1 (LlamaDecoderLayer) ...
    norm (LlamaRMSNorm)
```

Key: LLaMA uses separate Q, K, V projections and RMSNorm instead of LayerNorm. MLP uses a gated architecture (SwiGLU).

### HuggingFace BERT

```
BertModel
  embeddings (BertEmbeddings)
    word_embeddings (Embedding)
    position_embeddings (Embedding)
    token_type_embeddings (Embedding)
    LayerNorm (LayerNorm)
  encoder
    layer (ModuleList)
      0 (BertLayer)
        attention (BertAttention)
          self (BertSelfAttention)
            query (Linear)
            key (Linear)
            value (Linear)
          output (BertSelfOutput)
            dense (Linear)
            LayerNorm (LayerNorm)
        intermediate (BertIntermediate)
          dense (Linear)
        output (BertOutput)
          dense (Linear)
          LayerNorm (LayerNorm)
      1 (BertLayer) ...
  pooler (BertPooler)
```

Key: BERT uses post-norm (LayerNorm after residual), separate Q, K, V projections, and a pooler layer for classification.

## D. Generating `model-architecture.json`

### Schema

```json
{
  "model_class": "GPT2LMHeadModel",
  "total_parameters": 124439808,
  "dtype": "float32",
  "source": "gpt2",
  "summary": {
    "num_attention_layers": 12,
    "num_mlp_layers": 12,
    "num_norm_layers": 25,
    "num_embedding_layers": 2,
    "hidden_dim": 768,
    "num_heads": 12,
    "head_dim": 64,
    "vocab_size": 50257,
    "max_seq_len": 1024
  },
  "layers": [
    {
      "index": 0,
      "name": "transformer.wte",
      "type": "Embedding",
      "role": "embedding",
      "shape": [50257, 768],
      "parameters": 38597376
    },
    {
      "index": 1,
      "name": "transformer.h.0.attn",
      "type": "GPT2Attention",
      "role": "attention",
      "parameters": 2362368
    }
  ]
}
```

### Generation Code

```python
import json
import torch.nn as nn


def generate_architecture_report(model: nn.Module, model_name: str, output_path: str = "model-architecture.json"):
    """Generate a structured architecture report for a model."""
    layers = []
    role_counts = {"attention": 0, "mlp": 0, "normalization": 0, "embedding": 0, "linear": 0, "other": 0}

    for idx, (name, module) in enumerate(model.named_modules()):
        if not is_leaf_module(module) and not classify_module(module) in ("attention", "mlp"):
            continue  # Skip pure containers, but keep semantic containers like Attention

        role = classify_module(module)
        role_counts[role] = role_counts.get(role, 0) + 1

        entry = {
            "index": idx,
            "name": name,
            "type": type(module).__name__,
            "role": role,
            "parameters": module_param_count(module),
        }

        # Add shape info for leaf modules with weight
        if hasattr(module, "weight") and module.weight is not None:
            entry["shape"] = list(module.weight.shape)

        layers.append(entry)

    report = {
        "model_class": type(model).__name__,
        "total_parameters": total_param_count(model),
        "dtype": str(next(model.parameters()).dtype),
        "source": model_name,
        "summary": {
            "num_attention_layers": role_counts.get("attention", 0),
            "num_mlp_layers": role_counts.get("mlp", 0),
            "num_norm_layers": role_counts.get("normalization", 0),
            "num_embedding_layers": role_counts.get("embedding", 0),
        },
        "layers": layers,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return report
```
