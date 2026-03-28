"""Example: Extract per-head attention patterns from GPT-2 using forward hooks.

Loads GPT-2 from HuggingFace, attaches hooks to all attention layers,
runs a single forward pass, and prints the shapes of the extracted
attention weight tensors.

Requirements:
    pip install torch transformers
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    # Load model and tokenizer
    model_name = "gpt2"
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.eval()

    # Identify all attention layer names
    attn_layer_names = [
        name for name, module in model.named_modules()
        if type(module).__name__ == "GPT2Attention"
    ]
    print(f"Found {len(attn_layer_names)} attention layers: {attn_layer_names[:3]}...")

    # Set up hooks to capture attention weights
    attention_cache = {}
    hooks = []
    module_dict = dict(model.named_modules())

    for layer_name in attn_layer_names:
        def make_hook(name):
            def hook_fn(module, input, output):
                # GPT2Attention returns (hidden_states, present, attn_weights)
                # when output_attentions=True; otherwise (hidden_states, present)
                # We extract the attention weights via the model's output_attentions flag
                attention_cache[name] = output
            return hook_fn
        hook = module_dict[layer_name].register_forward_hook(make_hook(layer_name))
        hooks.append(hook)

    # Tokenize a sample input
    text = "The cat sat on the mat and then the cat"
    inputs = tokenizer(text, return_tensors="pt")
    seq_len = inputs["input_ids"].shape[1]
    print(f"Input: '{text}' -> {seq_len} tokens")

    # Forward pass with attention output enabled
    with torch.no_grad():
        outputs = model(**inputs, output_attentions=True)

    # Extract per-head attention patterns from model outputs
    # outputs.attentions is a tuple of (batch, num_heads, seq_len, seq_len) per layer
    print(f"\nAttention patterns from model outputs:")
    for i, attn_weights in enumerate(outputs.attentions):
        print(f"  Layer {i}: {attn_weights.shape}")
        # Shape: (1, 12, seq_len, seq_len) for GPT-2 with 12 heads

    # Also show what the hooks captured (raw layer outputs)
    print(f"\nRaw hook outputs:")
    for layer_name in attn_layer_names[:3]:
        cached = attention_cache[layer_name]
        if isinstance(cached, tuple):
            for j, item in enumerate(cached):
                if isinstance(item, torch.Tensor):
                    print(f"  {layer_name}[{j}]: {item.shape}")
        else:
            print(f"  {layer_name}: {cached.shape}")

    # Clean up hooks
    for h in hooks:
        h.remove()
    print(f"\nRemoved {len(hooks)} hooks. Remaining hooks: "
          f"{sum(len(dict(m._forward_hooks)) for _, m in model.named_modules())}")


if __name__ == "__main__":
    main()
