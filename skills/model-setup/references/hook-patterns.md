# Hook Patterns Reference

Detailed guide to PyTorch forward hooks for extracting and modifying intermediate representations during model inference and training.

## A. Forward Hook API

### Registration

```python
handle = module.register_forward_hook(hook_fn)
```

### Hook Signature

```python
def hook_fn(module: nn.Module, input: tuple, output: Any) -> Optional[Any]:
    """
    Args:
        module: The module this hook is attached to.
        input: Tuple of inputs to the module's forward().
        output: The output of the module's forward().

    Returns:
        None to leave the output unchanged, or a modified tensor/tuple
        to replace the output (used for ablation).
    """
    pass
```

### Removal

```python
handle.remove()
```

The handle returned by `register_forward_hook` is a `RemovableHook`. Call `.remove()` to detach the hook. After removal, the hook no longer fires on subsequent forward passes.

### Pre-hooks vs. Post-hooks

- `register_forward_pre_hook(fn)`: fires before the module's `forward()`, receives only `input`. Return a modified input tuple to change what the module sees.
- `register_forward_hook(fn)`: fires after the module's `forward()`, receives both `input` and `output`. Return a modified output to change what downstream modules see.

Use pre-hooks for input modification, post-hooks for output extraction or modification.

## B. Context Manager Pattern for Hooks

The `ActivationCache` class provides automatic hook lifecycle management. Hooks are registered on entry and guaranteed to be removed on exit, even if an exception occurs.

```python
import torch
import torch.nn as nn
from typing import Dict, List, Optional


class ActivationCache:
    """Context manager for extracting intermediate activations via forward hooks.

    Usage:
        with ActivationCache(model, ["transformer.h.0.attn", "transformer.h.1.attn"]) as cache:
            output = model(input_ids)
            activations = cache.cache  # dict mapping layer name -> tensor
    """

    def __init__(self, model: nn.Module, layer_names: List[str]):
        self.model = model
        self.layer_names = layer_names
        self.cache: Dict[str, torch.Tensor] = {}
        self.hooks: List[torch.utils.hooks.RemovableHook] = []

    def _make_hook(self, name: str):
        def hook_fn(module, input, output):
            # Detach from computation graph and move to CPU to save GPU memory
            if isinstance(output, tuple):
                self.cache[name] = tuple(o.detach().cpu() if isinstance(o, torch.Tensor) else o for o in output)
            else:
                self.cache[name] = output.detach().cpu()
        return hook_fn

    def __enter__(self):
        module_dict = dict(self.model.named_modules())
        for name in self.layer_names:
            if name not in module_dict:
                raise KeyError(f"Module '{name}' not found. Available: {list(module_dict.keys())[:10]}...")
            layer = module_dict[name]
            hook = layer.register_forward_hook(self._make_hook(name))
            self.hooks.append(hook)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for h in self.hooks:
            h.remove()
        self.hooks.clear()
        return False  # Do not suppress exceptions


class BatchActivationCache(ActivationCache):
    """Extended cache that accumulates activations across multiple batches."""

    def __init__(self, model: nn.Module, layer_names: List[str]):
        super().__init__(model, layer_names)
        self.batch_cache: Dict[str, List[torch.Tensor]] = {name: [] for name in layer_names}

    def _make_hook(self, name: str):
        def hook_fn(module, input, output):
            if isinstance(output, tuple):
                tensor = output[0]
            else:
                tensor = output
            self.batch_cache[name].append(tensor.detach().cpu())
        return hook_fn

    def concatenate(self) -> Dict[str, torch.Tensor]:
        """Concatenate accumulated batches along dim 0."""
        return {name: torch.cat(tensors, dim=0) for name, tensors in self.batch_cache.items()}
```

## C. Memory Management

### When to Detach

Always call `.detach()` on cached tensors. Without detaching, the entire computation graph is retained in memory, causing GPU OOM on large models.

```python
# WRONG: retains computation graph
self.cache[name] = output

# CORRECT: breaks the graph link
self.cache[name] = output.detach()
```

### When to Move to CPU

Move to CPU when:
- The extraction job will cache many layers or many batches
- GPU memory is tight (e.g., large model already occupies most of GPU)
- The cached activations will be analyzed after the forward pass completes

Keep on GPU when:
- The cached activations will be used immediately in a GPU computation (e.g., activation patching in the same forward pass)

```python
# For offline analysis
self.cache[name] = output.detach().cpu()

# For same-pass patching (keep on GPU)
self.cache[name] = output.detach()
```

### Batch Accumulation Patterns

For large datasets, accumulate per-batch results and concatenate once at the end:

```python
all_activations = []
with ActivationCache(model, layers) as cache:
    for batch in dataloader:
        model(batch)
        all_activations.append(cache.cache["target_layer"].clone())
        cache.cache.clear()  # Free memory before next batch

stacked = torch.cat(all_activations, dim=0)
```

### Gradient Checkpointing Interaction

When `torch.utils.checkpoint` is enabled, intermediate activations are recomputed during the backward pass. Hooks still fire during the forward pass, but be aware:
- Hooks fire once during the initial forward pass
- During backward recomputation, hooks fire again -- guard against double-counting by checking `torch.is_grad_enabled()`

```python
def hook_fn(module, input, output):
    if not torch.is_grad_enabled():  # Only cache during eval or initial forward
        self.cache[name] = output.detach().cpu()
```

## D. Multi-Head Attention Extraction

### Extracting Per-Head Outputs

Most HuggingFace attention modules return a fused output of shape `(batch, seq_len, num_heads * head_dim)`. To get per-head outputs, reshape:

```python
def extract_per_head(fused_output, num_heads):
    """Reshape fused multi-head output to per-head tensors.

    Args:
        fused_output: (batch, seq_len, num_heads * head_dim)
        num_heads: number of attention heads

    Returns:
        (batch, num_heads, seq_len, head_dim)
    """
    batch, seq_len, hidden = fused_output.shape
    head_dim = hidden // num_heads
    return fused_output.view(batch, seq_len, num_heads, head_dim).transpose(1, 2)
```

### Extracting Q, K, V Matrices

Hook onto the attention module and access intermediate projections. For HuggingFace GPT-2:

```python
# GPT-2 computes Q, K, V via a single linear projection c_attn
# Output of c_attn: (batch, seq_len, 3 * hidden_dim)
def extract_qkv(attn_module_output, num_heads):
    # attn_module.c_attn produces concatenated Q, K, V
    qkv = attn_module_output  # (batch, seq_len, 3 * hidden)
    hidden = qkv.shape[-1] // 3
    q, k, v = qkv.split(hidden, dim=-1)
    head_dim = hidden // num_heads
    # Reshape to (batch, num_heads, seq_len, head_dim)
    q = q.view(-1, q.size(1), num_heads, head_dim).transpose(1, 2)
    k = k.view(-1, k.size(1), num_heads, head_dim).transpose(1, 2)
    v = v.view(-1, v.size(1), num_heads, head_dim).transpose(1, 2)
    return q, k, v
```

### Extracting Attention Weights

For HuggingFace models, pass `output_attentions=True` to the forward call:

```python
outputs = model(input_ids, output_attentions=True)
attention_weights = outputs.attentions  # tuple of (batch, num_heads, seq_len, seq_len) per layer
```

Alternatively, hook onto the attention softmax output for models that do not expose attention weights.

## E. Common Hook Pitfalls

### 1. Hooking on Wrong Module

Container modules (e.g., `nn.Sequential`, `nn.ModuleList`) do not have a meaningful `forward()` of their own. Hooking on them captures the aggregated output, not individual layer outputs.

**Fix**: Hook on leaf modules (e.g., `nn.Linear`, `nn.LayerNorm`, or the specific attention class).

```python
# WRONG: hooks on the ModuleList container
model.transformer.h.register_forward_hook(hook_fn)

# CORRECT: hooks on a specific transformer block
model.transformer.h[0].attn.register_forward_hook(hook_fn)
```

### 2. Hooks Surviving Model Copy

`copy.deepcopy(model)` duplicates the model but does NOT duplicate hook handles. The original hooks still reference the original model's modules. The copied model has no hooks.

**Fix**: Re-register hooks on the copied model if needed.

### 3. Memory Leaks from Unclosed Hooks

If hooks are registered but never removed, they persist for the lifetime of the model. Each forward pass accumulates more cached data.

**Fix**: Always use the context manager pattern, or explicitly remove hooks in a `finally` block.

```python
hooks = []
try:
    for name, module in model.named_modules():
        hooks.append(module.register_forward_hook(hook_fn))
    # ... do work ...
finally:
    for h in hooks:
        h.remove()
```

### 4. Hooks Modifying Output Unexpectedly

If a hook returns a value (instead of `None`), that value replaces the module's output. This is intentional for ablation but can cause bugs if a hook accidentally returns something.

**Fix**: For extraction-only hooks, always return `None` (or simply omit the return statement).

### 5. Hooks on Modules with Multiple Outputs

Some modules return tuples (e.g., LSTM returns `(output, (h_n, c_n))`). The hook receives the entire tuple as `output`. Indexing incorrectly causes shape errors downstream.

**Fix**: Check the module's return type in the documentation and handle tuple outputs explicitly.
