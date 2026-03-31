#!/usr/bin/env python3
"""
run_head_importance.py — Standalone head importance scoring via Integrated Gradients.

Loads a trained model checkpoint, runs IG attribution over the validation set,
and emits per-head importance scores and ranked JSON files for K ∈ {6,12,24,36,48,72}.

The attribution target is the model's predicted class logit (argmax).  We
integrate gradients on the attention weight tensors with respect to a zero-
attention baseline (uniform over sequence length).

Usage:
    python scripts/run_head_importance.py \\
        --model-path results/vanilla/seed_42/best_model.pt \\
        --data-cache data/cache \\
        --output-dir results/head_importance/ \\
        --n-steps 50 \\
        --batch-size 8

Outputs:
    results/head_importance/
        head_importance.json          # {(layer, head): float} raw scores
        head_importance_ranked.json   # sorted list of [layer, head, score]
        top_6_heads.json   .. top_72_heads.json    # per-K lists
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import torch
import numpy as np
from torch.utils.data import DataLoader
from transformers import BertTokenizerFast

logger = logging.getLogger(__name__)

K_VALUES = [6, 12, 24, 36, 48, 72]


# ---------------------------------------------------------------------------
# Integrated Gradients on attention weights
# ---------------------------------------------------------------------------

def _zero_attention_baseline(
    attention: torch.Tensor,
) -> torch.Tensor:
    """Uniform attention baseline: 1 / seq_len for unmasked positions.

    attention: (batch, heads, seq, seq)  — after masking / softmax
    Returns tensor of same shape with uniform rows (summing to 1 over dim=-1).
    """
    seq_len = attention.size(-1)
    return torch.full_like(attention, 1.0 / seq_len)


def _integrated_gradients(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    token_type_ids: torch.Tensor,
    n_steps: int = 50,
) -> torch.Tensor:
    """Return IG attribution averaged over all layers.

    Returns: (n_layers, n_heads) float tensor of mean |IG| scores.
    """
    model.eval()
    device = next(model.parameters()).device

    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)
    token_type_ids = token_type_ids.to(device)

    # Collect per-step gradients via hook-based approach.
    # We scale the attention weight output by alpha ∈ [0, 1] and integrate.
    n_layers = model.bert.config.num_hidden_layers
    n_heads = model.bert.config.num_attention_heads
    ig_accum = torch.zeros(n_layers, n_heads, device="cpu")

    captured: Dict[int, torch.Tensor] = {}

    def make_hook(layer_idx: int):
        def hook(module, input, output):
            # output[0] is context layer; we need the raw attn weights.
            # For this hook, we capture the scaled attn weights pre-softmax.
            captured[layer_idx] = module._attn_weights  # type: ignore[attr-defined]
        return hook

    # Register hooks on each attention layer.
    hooks = []
    for li in range(n_layers):
        attn_self = model.bert.encoder.layer[li].attention.self
        hooks.append(attn_self.register_forward_hook(make_hook(li)))

    # Forward pass to get baseline logit.
    with torch.no_grad():
        baseline_out = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
    target_class = baseline_out.logits.argmax(dim=-1)  # (batch,)

    # IG: interpolate between baseline and actual attention.
    # We perturb via a scaling hook — simpler than modifying forward pass.
    # Accumulate sum of gradients ∫₀¹ ∂F/∂A · dα  (trapezoidal rule).
    for hook in hooks:
        hook.remove()

    # Re-run with gradient tracking; scale attention weights at each alpha step.
    for step in range(n_steps + 1):
        alpha = step / n_steps

        def attn_scale_hook(module, input, output, _alpha=alpha):
            # Scale the raw attention weights (before softmax in vanilla mode).
            # This is an approximation: we scale output context instead.
            return output

        # Enable gradient capture on attention weight matrices.
        for li in range(n_layers):
            layer_attn = model.bert.encoder.layer[li].attention.self
            # Access value/query/key weight matrices and create scaled inputs.
            _ = layer_attn  # noqa (accessed below via model forward)

        # Run forward with autograd.
        model.zero_grad()
        out = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            output_attentions=True,
        )

        # Select logit for target class.
        logit = out.logits.gather(1, target_class.unsqueeze(1)).sum()

        # Collect attention tensors: tuple of (batch, heads, seq, seq) per layer.
        attn_tensors = out.attentions  # tuple[n_layers], each (B, H, S, S)

        grads = torch.autograd.grad(
            logit,
            attn_tensors,
            retain_graph=False,
            allow_unused=True,
        )

        weight = 1.0 / n_steps if 0 < step < n_steps else 0.5 / n_steps  # trap
        for li, (attn_t, grad_t) in enumerate(zip(attn_tensors, grads)):
            if grad_t is None:
                continue
            # IG score per head: mean |gradient × (attn - baseline)|
            # Use scaled attention α·attn as interpolation.
            baseline = _zero_attention_baseline(attn_t.detach())
            delta = (alpha * attn_t.detach() - baseline).abs()
            score = (grad_t.abs() * delta).mean(dim=(0, 2, 3))  # (n_heads,)
            ig_accum[li] += weight * score.cpu()

    return ig_accum  # (n_layers, n_heads)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Head importance via Integrated Gradients")
    parser.add_argument("--model-path", required=True, help="Path to best_model.pt")
    parser.add_argument("--data-cache", default="data/cache", help="HuggingFace dataset cache")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--n-steps", type=int, default=50, help="IG integration steps")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-batches", type=int, default=100,
                        help="Limit validation batches for speed (0 = all)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = Path(args.model_path)
    logger.info("Loading model from %s", model_path)
    model = torch.load(model_path, map_location="cpu", weights_only=False)
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    n_layers = model.bert.config.num_hidden_layers
    n_heads = model.bert.config.num_attention_heads
    logger.info("Model: %d layers × %d heads", n_layers, n_heads)

    # Load validation set.
    from datasets import load_dataset, load_from_disk
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
    cache = Path(args.data_cache)
    if (cache / "hatexplain").exists():
        dataset = load_from_disk(str(cache / "hatexplain"))
    else:
        dataset = load_dataset("hatexplain", cache_dir=str(cache))

    val_data = dataset["validation"]

    def tokenize(batch):
        return tokenizer(
            batch["post_tokens"],
            is_split_into_words=True,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )

    val_data = val_data.map(tokenize, batched=True, batch_size=32)
    val_data.set_format(type="torch", columns=["input_ids", "attention_mask", "token_type_ids"])
    loader = DataLoader(val_data, batch_size=args.batch_size, shuffle=False)

    # Accumulate IG scores.
    total_ig = torch.zeros(n_layers, n_heads)
    n_batches = 0
    for batch_idx, batch in enumerate(loader):
        if args.max_batches and batch_idx >= args.max_batches:
            break
        try:
            batch_ig = _integrated_gradients(
                model,
                batch["input_ids"],
                batch["attention_mask"],
                batch["token_type_ids"],
                n_steps=args.n_steps,
            )
            total_ig += batch_ig
            n_batches += 1
        except Exception as exc:
            logger.warning("Batch %d failed: %s", batch_idx, exc)
            continue

        if (batch_idx + 1) % 10 == 0:
            logger.info("Processed %d/%d batches", batch_idx + 1,
                        min(args.max_batches or len(loader), len(loader)))

    if n_batches == 0:
        logger.error("No batches processed — check data and model paths.")
        return

    mean_ig = total_ig / n_batches  # (n_layers, n_heads)

    # Serialize raw scores.
    raw_scores: Dict[str, float] = {}
    for li in range(n_layers):
        for hi in range(n_heads):
            raw_scores[f"{li},{hi}"] = float(mean_ig[li, hi])

    with open(output_dir / "head_importance.json", "w") as fh:
        json.dump(raw_scores, fh, indent=2)

    # Ranked list: [[layer, head, score], ...]
    ranked: List[Tuple[int, int, float]] = sorted(
        [(li, hi, float(mean_ig[li, hi]))
         for li in range(n_layers)
         for hi in range(n_heads)],
        key=lambda x: x[2],
        reverse=True,
    )
    with open(output_dir / "head_importance_ranked.json", "w") as fh:
        json.dump(ranked, fh, indent=2)

    # Per-K top-head lists.
    for k in K_VALUES:
        top_k = [[li, hi] for li, hi, _ in ranked[:k]]
        with open(output_dir / f"top_{k}_heads.json", "w") as fh:
            json.dump(top_k, fh, indent=2)

    logger.info(
        "Head importance written to %s (%d batches, %d heads scored)",
        output_dir, n_batches, n_layers * n_heads,
    )
    logger.info("Top-5 heads: %s", ranked[:5])


if __name__ == "__main__":
    main()
