"""Head importance scoring via Integrated Gradients.

Uses Captum's ``IntegratedGradients`` to attribute the model's predicted-class
logit to each attention head, then aggregates importance scores across the
dataset.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import torch
from torch import Tensor
from torch.utils.data import DataLoader

from captum.attr import IntegratedGradients


def _build_head_forward(
    model: torch.nn.Module,
    layer: int,
    head: int,
) -> torch.nn.Module:
    """Build a wrapper that takes ``input_ids`` + ``attention_mask`` and returns
    the predicted-class logit, while registering a hook on the requested
    attention head so we can attribute through it.

    This is intentionally lightweight: we attribute w.r.t. the *embedding*
    layer and then project the attribution onto per-head attention norms.
    """
    # We use a simpler gradient-based approach: compute the gradient of the
    # predicted logit w.r.t. each attention head's output, then aggregate.
    pass  # see compute_head_importance for the actual implementation.


def compute_head_importance(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device | str = "cpu",
    n_steps: int = 20,
) -> Dict[Tuple[int, int], float]:
    """Compute per-head importance scores using Integrated Gradients.

    For each batch the function:
    1. Runs the model and gets the predicted class.
    2. Uses IG (attributing w.r.t. token embeddings) to get per-token
       attributions for the predicted class.
    3. Collects attention weights per head and weights them by the token-level
       IG attributions to produce a per-head importance score.

    Parameters
    ----------
    model : torch.nn.Module
        A ``BertSparseForClassification`` (or compatible) model.
    dataloader : DataLoader
        Yields dicts with ``input_ids``, ``attention_mask``, and optionally
        ``labels``.
    device : torch.device | str
        Target device.
    n_steps : int
        Number of interpolation steps for Integrated Gradients.

    Returns
    -------
    dict[(int, int), float]
        Mapping ``(layer_idx, head_idx) -> importance_score``.
    """
    model.eval()
    model.to(device)

    bert = model.bert  # type: ignore[attr-defined]
    n_layers: int = bert.config.num_hidden_layers
    n_heads: int = bert.config.num_attention_heads
    head_dim: int = bert.config.hidden_size // n_heads

    # Accumulator: (n_layers, n_heads).
    importance_acc = torch.zeros(n_layers, n_heads, device=device)
    total_samples = 0

    # IG wrapper: takes embeddings and attention_mask, returns predicted logit.
    embedding_layer = bert.embeddings

    class _EmbeddingForward(torch.nn.Module):
        """Wraps model to accept raw embeddings instead of input_ids."""

        def __init__(self, outer_model: torch.nn.Module) -> None:
            super().__init__()
            self.outer = outer_model

        def forward(self, embeddings: Tensor, attention_mask: Tensor) -> Tensor:
            # Run BERT from embeddings.
            bert_out = bert(
                inputs_embeds=embeddings,
                attention_mask=attention_mask,
                output_attentions=True,
            )
            cls_hidden = bert_out.last_hidden_state[:, 0]
            logits = self.outer.classifier(self.outer.dropout(cls_hidden))  # type: ignore[attr-defined]
            return logits

    embed_model = _EmbeddingForward(model)
    ig = IntegratedGradients(
        lambda embeds, mask: embed_model(embeds, mask),
    )

    with torch.no_grad():
        pass  # We need gradients for IG, handled below.

    for batch in dataloader:
        input_ids: Tensor = batch["input_ids"].to(device)
        attention_mask: Tensor = batch["attention_mask"].to(device)
        batch_size = input_ids.size(0)

        # Get embeddings.
        with torch.no_grad():
            embeddings = embedding_layer(input_ids)

        embeddings = embeddings.detach().requires_grad_(True)

        # Get predicted class.
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attention_mask)
            predicted = out.logits.argmax(dim=-1)  # (B,)

        # Compute IG attributions w.r.t. embeddings for each sample.
        # baseline: zero embeddings.
        baseline = torch.zeros_like(embeddings)

        # IG returns attributions of shape (B, L, hidden_size).
        attributions = ig.attribute(
            embeddings,
            baselines=baseline,
            additional_forward_args=(attention_mask,),
            target=predicted,
            n_steps=n_steps,
        )

        # Per-token importance: L2 norm over hidden dim -> (B, L).
        token_importance = attributions.norm(dim=-1)  # (B, L)

        # Get attention weights for head-level scoring.
        with torch.no_grad():
            bert_out = bert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=True,
            )
            layer_attns = bert_out.attentions  # tuple of (B, H, L, L)

        # Score each head: mean of (attention_weight * token_importance) over
        # query and key positions.
        for layer_idx in range(n_layers):
            attn = layer_attns[layer_idx]  # (B, H, L, L)
            # Weight each key position by its IG importance.
            # attn: (B, H, L_q, L_k), token_importance: (B, L_k)
            weighted = attn * token_importance.unsqueeze(1).unsqueeze(2)  # (B, H, L_q, L_k)

            # Mask padding.
            pad_mask = attention_mask.float().unsqueeze(1).unsqueeze(2)  # (B, 1, 1, L)
            weighted = weighted * pad_mask

            # Mean absolute score per head.
            head_scores = weighted.abs().sum(dim=(2, 3))  # (B, H)
            n_tokens = attention_mask.sum(dim=-1, keepdim=True).float().clamp(min=1.0)
            head_scores = head_scores / (n_tokens ** 2)  # normalize by seq_len^2

            importance_acc[:n_layers, :n_heads] = importance_acc[:n_layers, :n_heads]  # no-op shape guard
            importance_acc[layer_idx] += head_scores.sum(dim=0)

        total_samples += batch_size

    # Average over dataset.
    if total_samples > 0:
        importance_acc /= total_samples

    # Build result dict.
    result: Dict[Tuple[int, int], float] = {}
    for layer_idx in range(n_layers):
        for head_idx in range(n_heads):
            result[(layer_idx, head_idx)] = importance_acc[layer_idx, head_idx].item()

    return result


def select_top_k_heads(
    importance_scores: Dict[Tuple[int, int], float],
    k: int,
) -> List[Tuple[int, int]]:
    """Return the *k* most important ``(layer, head)`` tuples.

    Parameters
    ----------
    importance_scores : dict[(int, int), float]
        Output of :func:`compute_head_importance`.
    k : int
        Number of heads to select.

    Returns
    -------
    list[tuple[int, int]]
        Top-k heads sorted by descending importance.
    """
    sorted_heads = sorted(
        importance_scores.items(), key=lambda x: x[1], reverse=True
    )
    return [head for head, _score in sorted_heads[:k]]


def select_top_k_per_layer(
    importance_scores: Dict[Tuple[int, int], float],
    k_per_layer: int,
) -> List[Tuple[int, int]]:
    """Return the top-*k_per_layer* heads within each transformer layer.

    Parameters
    ----------
    importance_scores : dict[(int, int), float]
        Output of :func:`compute_head_importance`.
    k_per_layer : int
        Number of heads to keep per layer.

    Returns
    -------
    list[tuple[int, int]]
        Selected heads sorted by ``(layer, head)`` index.
    """
    # Group by layer.
    per_layer: Dict[int, List[Tuple[int, float]]] = {}
    for (layer_idx, head_idx), score in importance_scores.items():
        per_layer.setdefault(layer_idx, []).append((head_idx, score))

    result: List[Tuple[int, int]] = []
    for layer_idx in sorted(per_layer.keys()):
        heads_sorted = sorted(per_layer[layer_idx], key=lambda x: x[1], reverse=True)
        for head_idx, _score in heads_sorted[:k_per_layer]:
            result.append((layer_idx, head_idx))

    return sorted(result)
