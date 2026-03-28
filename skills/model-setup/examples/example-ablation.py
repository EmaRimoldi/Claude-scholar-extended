"""Example: Zero-ablate a specific attention head using a reversible context manager.

Loads GPT-2, identifies a specific attention head, ablates it, and verifies
that (a) the output changes during ablation and (b) the output matches the
original after the context manager exits.

Requirements:
    pip install torch transformers
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class ReversibleAblation:
    """Context manager that applies a hook-based ablation and removes it on exit."""

    def __init__(self, model, layer_name, hook_fn):
        self.model = model
        self.layer_name = layer_name
        self.hook_fn = hook_fn
        self.handle = None

    def __enter__(self):
        module_dict = dict(self.model.named_modules())
        layer = module_dict[self.layer_name]
        self.handle = layer.register_forward_hook(self.hook_fn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.remove()
            self.handle = None
        return False


def zero_head_hook(head_index, num_heads):
    """Create a hook that zeros the output of a specific attention head."""
    def hook_fn(module, input, output):
        hidden_states = output[0] if isinstance(output, tuple) else output
        head_dim = hidden_states.shape[-1] // num_heads
        start = head_index * head_dim
        end = start + head_dim
        modified = hidden_states.clone()
        modified[:, :, start:end] = 0.0
        if isinstance(output, tuple):
            return (modified,) + output[1:]
        return modified
    return hook_fn


def main():
    model_name = "gpt2"
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.eval()

    num_heads = model.config.n_head  # 12 for GPT-2
    target_layer = "transformer.h.0.attn"
    target_head = 3

    text = "The capital of France is"
    inputs = tokenizer(text, return_tensors="pt")

    # Step 1: Get original output
    with torch.no_grad():
        original_logits = model(**inputs).logits.clone()

    # Step 2: Ablate head 3 in layer 0 using the reversible context manager
    hook = zero_head_hook(head_index=target_head, num_heads=num_heads)
    with ReversibleAblation(model, target_layer, hook):
        with torch.no_grad():
            ablated_logits = model(**inputs).logits.clone()

    # Step 3: Verify output changed during ablation
    diff = (original_logits - ablated_logits).abs().max().item()
    print(f"Max logit difference during ablation: {diff:.6f}")
    assert diff > 1e-6, "Ablation had no effect -- something is wrong."
    print("PASS: Ablation changed the output.")

    # Step 4: Verify restoration after context manager exit
    with torch.no_grad():
        restored_logits = model(**inputs).logits.clone()

    restoration_diff = (original_logits - restored_logits).abs().max().item()
    print(f"Max logit difference after restoration: {restoration_diff:.6e}")
    assert restoration_diff < 1e-6, "Restoration failed -- hooks were not cleaned up."
    print("PASS: Output matches original after restoration.")


if __name__ == "__main__":
    main()
