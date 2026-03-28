# Ablation Patterns Reference

Detailed guide to ablation methods for testing component necessity in neural networks. Each method removes or replaces a component's contribution to measure its causal effect on model behavior.

## A. Zero Ablation

Zero ablation sets a component's output to zero, completely removing its contribution to downstream computation.

```python
import torch
import torch.nn as nn
from typing import Optional


def zero_ablation_hook(head_index: Optional[int] = None, num_heads: Optional[int] = None):
    """Create a hook that zeros out a specific attention head or the entire layer output.

    Args:
        head_index: If provided, zero only this head. If None, zero the entire output.
        num_heads: Required when head_index is provided, to compute head_dim.

    Returns:
        Hook function compatible with register_forward_hook.
    """
    def hook_fn(module, input, output):
        # Handle tuple outputs (some attention modules return (output, attention_weights))
        if isinstance(output, tuple):
            hidden_states = output[0]
        else:
            hidden_states = output

        if head_index is not None and num_heads is not None:
            head_dim = hidden_states.shape[-1] // num_heads
            start = head_index * head_dim
            end = start + head_dim
            modified = hidden_states.clone()
            modified[:, :, start:end] = 0.0
        else:
            modified = torch.zeros_like(hidden_states)

        if isinstance(output, tuple):
            return (modified,) + output[1:]
        return modified

    return hook_fn
```

**When to use**: As a quick first test. Zero ablation is the simplest method and gives a clear signal, but it introduces an out-of-distribution input to downstream layers (they never saw zeros during training), which can cause cascading effects that overstate the component's importance.

## B. Mean Ablation

Mean ablation replaces a component's output with its average output across a reference dataset. This preserves the expected scale and distribution, giving a more accurate measure of the component's unique contribution.

```python
import torch
import torch.nn as nn
from typing import Dict, List


def compute_mean_activations(
    model: nn.Module,
    layer_names: List[str],
    dataloader,
    device: str = "cuda",
) -> Dict[str, torch.Tensor]:
    """Compute mean activation for each specified layer across a reference dataset.

    Returns:
        Dict mapping layer name to mean activation tensor.
    """
    sums: Dict[str, torch.Tensor] = {}
    counts: Dict[str, int] = {}
    hooks = []
    module_dict = dict(model.named_modules())

    def make_accumulator(name):
        def hook_fn(module, input, output):
            tensor = output[0] if isinstance(output, tuple) else output
            if name not in sums:
                sums[name] = torch.zeros_like(tensor).sum(dim=0)  # Sum over batch
                counts[name] = 0
            sums[name] += tensor.detach().sum(dim=0)
            counts[name] += tensor.shape[0]
        return hook_fn

    for name in layer_names:
        hook = module_dict[name].register_forward_hook(make_accumulator(name))
        hooks.append(hook)

    model.eval()
    with torch.no_grad():
        for batch in dataloader:
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            model(**batch)

    for h in hooks:
        h.remove()

    return {name: sums[name] / counts[name] for name in layer_names}


def mean_ablation_hook(mean_activation: torch.Tensor):
    """Create a hook that replaces output with a precomputed mean activation.

    Args:
        mean_activation: The mean activation tensor (seq_len, hidden_dim) or (hidden_dim,).
    """
    def hook_fn(module, input, output):
        if isinstance(output, tuple):
            hidden_states = output[0]
        else:
            hidden_states = output

        # Broadcast mean to match batch size
        replacement = mean_activation.to(hidden_states.device).unsqueeze(0).expand_as(hidden_states)

        if isinstance(output, tuple):
            return (replacement,) + output[1:]
        return replacement

    return hook_fn
```

**When to use**: When you want a more faithful estimate of component importance. Mean ablation keeps downstream layers in-distribution, avoiding the cascading artifacts of zero ablation. Requires a reference dataset pass first.

## C. Activation Patching

Activation patching replaces a component's output on one input (the corrupted or counterfactual input) with the output from a different input (the clean or factual input). This measures the causal effect of that component on the difference between the two inputs.

```python
import torch
import torch.nn as nn
from typing import Dict


def collect_activations(
    model: nn.Module,
    layer_name: str,
    input_kwargs: dict,
) -> torch.Tensor:
    """Run a forward pass and collect the activation at the specified layer."""
    module_dict = dict(model.named_modules())
    cached = {}

    def cache_hook(module, input, output):
        tensor = output[0] if isinstance(output, tuple) else output
        cached["activation"] = tensor.detach()

    handle = module_dict[layer_name].register_forward_hook(cache_hook)
    model.eval()
    with torch.no_grad():
        model(**input_kwargs)
    handle.remove()

    return cached["activation"]


def activation_patching_hook(clean_activation: torch.Tensor):
    """Create a hook that patches in a clean activation during a corrupted forward pass.

    Args:
        clean_activation: Activation tensor from the clean input at this layer.
    """
    def hook_fn(module, input, output):
        if isinstance(output, tuple):
            return (clean_activation.to(output[0].device),) + output[1:]
        return clean_activation.to(output.device)

    return hook_fn


def run_activation_patching(
    model: nn.Module,
    layer_name: str,
    clean_input: dict,
    corrupted_input: dict,
) -> Dict[str, torch.Tensor]:
    """Run activation patching: replace corrupted activation with clean activation.

    Returns:
        Dict with keys: "clean_output", "corrupted_output", "patched_output"
    """
    model.eval()
    with torch.no_grad():
        clean_output = model(**clean_input)
        corrupted_output = model(**corrupted_input)

    clean_activation = collect_activations(model, layer_name, clean_input)

    module_dict = dict(model.named_modules())
    handle = module_dict[layer_name].register_forward_hook(
        activation_patching_hook(clean_activation)
    )
    with torch.no_grad():
        patched_output = model(**corrupted_input)
    handle.remove()

    return {
        "clean_output": clean_output,
        "corrupted_output": corrupted_output,
        "patched_output": patched_output,
    }
```

**When to use**: When you want to measure the causal effect of a specific component on a specific behavior difference. Activation patching is the gold standard for causal interpretability (used in circuit analysis, IOI, and related work).

## D. Reversible Ablation Context Manager

A context manager that applies an ablation and guarantees restoration of the original model state on exit.

```python
import torch
import torch.nn as nn
from typing import Callable, Optional
from contextlib import contextmanager


class ReversibleAblation:
    """Context manager that applies an ablation hook and removes it on exit.

    Usage:
        with ReversibleAblation(model, "transformer.h.0.attn", zero_ablation_hook(head_index=3, num_heads=12)):
            output = model(input_ids)  # Head 3 of layer 0 is ablated
        output = model(input_ids)  # Head 3 is restored
    """

    def __init__(self, model: nn.Module, layer_name: str, hook_fn: Callable):
        self.model = model
        self.layer_name = layer_name
        self.hook_fn = hook_fn
        self.handle = None

    def __enter__(self):
        module_dict = dict(self.model.named_modules())
        if self.layer_name not in module_dict:
            raise KeyError(f"Module '{self.layer_name}' not found in model.")
        layer = module_dict[self.layer_name]
        self.handle = layer.register_forward_hook(self.hook_fn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.remove()
            self.handle = None
        return False


class ReversibleWeightAblation:
    """Context manager that modifies model weights and restores them on exit.

    Use when ablation requires changing weights directly (e.g., setting a head's
    output projection to zero) rather than using hooks.
    """

    def __init__(self, model: nn.Module, param_name: str, new_value: torch.Tensor):
        self.model = model
        self.param_name = param_name
        self.new_value = new_value
        self.original_value = None

    def __enter__(self):
        parts = self.param_name.split(".")
        module = self.model
        for part in parts[:-1]:
            module = getattr(module, part)
        param = getattr(module, parts[-1])
        self.original_value = param.data.clone()
        param.data.copy_(self.new_value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_value is not None:
            parts = self.param_name.split(".")
            module = self.model
            for part in parts[:-1]:
                module = getattr(module, part)
            param = getattr(module, parts[-1])
            param.data.copy_(self.original_value)
        return False
```

## E. When to Use Which Ablation Method

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Zero ablation** | Quick importance screening | Simple, fast, no reference data needed | Out-of-distribution; overstates importance |
| **Mean ablation** | Faithful importance measurement | In-distribution; avoids cascading artifacts | Requires reference dataset pass |
| **Activation patching** | Causal analysis of specific behaviors | Gold standard for causal claims | Requires clean/corrupted input pair |
| **Weight zeroing** | Permanent removal | Persists across forward passes | Destructive without context manager |
| **Surgical fine-tuning** | Testing if a component can learn a task | Isolates component capacity | Expensive (requires training) |

**Decision guide**:
1. Start with **zero ablation** for a quick scan of which components matter.
2. Follow up with **mean ablation** for components that show large effects, to check whether the effect persists with in-distribution replacement.
3. Use **activation patching** when you have a specific hypothesis about what information a component carries (e.g., "head 9.1 moves the subject token's identity to the final position").

## F. Verifying Ablation Correctness

After applying an ablation, verify that it had the expected effect:

### 1. Output Should Change

```python
model.eval()
with torch.no_grad():
    original_output = model(**inputs)

with ReversibleAblation(model, layer_name, ablation_hook):
    with torch.no_grad():
        ablated_output = model(**inputs)

# Verify the output actually changed
diff = (original_output.logits - ablated_output.logits).abs().max().item()
assert diff > 1e-6, f"Ablation had no effect (max diff: {diff})"
```

### 2. Restoration Should Be Exact

```python
with torch.no_grad():
    restored_output = model(**inputs)

# Verify restoration is exact (within floating-point tolerance)
restoration_diff = (original_output.logits - restored_output.logits).abs().max().item()
assert restoration_diff < 1e-6, f"Restoration failed (max diff: {restoration_diff})"
```

### 3. Direction of Change Should Match Expectation

For interpretability experiments, check that ablating a component degrades performance on the relevant task and not on unrelated tasks:

```python
# If we ablated an "induction head", copying accuracy should drop
original_accuracy = compute_copying_accuracy(original_output)
ablated_accuracy = compute_copying_accuracy(ablated_output)
assert ablated_accuracy < original_accuracy, "Ablating induction head should reduce copying accuracy"
```
