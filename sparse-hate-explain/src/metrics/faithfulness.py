"""Faithfulness metrics: attention-IG correlation, sufficiency, comprehensiveness."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import torch
from captum.attr import LayerIntegratedGradients
from scipy.stats import spearmanr
from torch.utils.data import DataLoader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_attention_weights(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> torch.Tensor:
    """Return last-layer CLS attention weights averaged over heads.

    Returns:
        Tensor of shape (batch, seq_len) with attention weights.
    """
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
    )
    # last layer attention: (batch, heads, seq, seq)
    last_attn = outputs.attentions[-1]
    # CLS row averaged across heads: (batch, seq)
    cls_attn = last_attn[:, :, 0, :].mean(dim=1)
    return cls_attn


def _get_model_confidence(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return predicted class probabilities and predicted class indices.

    Returns:
        probs: (batch, num_classes) softmax probabilities.
        preds: (batch,) predicted class indices.
    """
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    logits = outputs.logits  # (batch, num_classes)
    probs = torch.softmax(logits, dim=-1)
    preds = probs.argmax(dim=-1)
    return probs, preds


# ---------------------------------------------------------------------------
# Attention-IG Correlation
# ---------------------------------------------------------------------------

def compute_attention_ig_correlation(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    n_steps: int = 50,
) -> Dict[str, float]:
    """Compute Spearman correlation between attention weights and IG attributions.

    For each sample the correlation is computed over the non-padding tokens.
    The function returns the mean and std of per-sample correlations.

    Args:
        model: Transformer model with ``output_attentions`` support.
        dataloader: Test dataloader yielding dicts with input_ids,
            attention_mask, labels.
        device: Torch device.
        n_steps: Number of interpolation steps for Integrated Gradients.

    Returns:
        Dict with ``mean_correlation`` and ``std_correlation``.
    """
    model.eval()

    # Build IG on the embedding layer.
    embedding_layer = model.bert.embeddings
    lig = LayerIntegratedGradients(
        lambda inp_ids, attn_mask: model.bert(
            inputs_embeds=inp_ids, attention_mask=attn_mask
        ).last_hidden_state[:, 0] @ model.classifier.weight.T + model.classifier.bias,
        embedding_layer,
    )

    correlations: list[float] = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)

        # Attention weights --------------------------------------------------
        attn_weights = _get_attention_weights(model, input_ids, attention_mask)

        # Predicted class for IG target --------------------------------------
        with torch.no_grad():
            logits = model(
                input_ids=input_ids, attention_mask=attention_mask
            ).logits
        pred_classes = logits.argmax(dim=-1)

        # IG attributions per sample (captum expects one target at a time) ----
        with torch.no_grad():
            input_embeds = embedding_layer(input_ids)
        input_embeds = input_embeds.detach().requires_grad_(True)
        baseline = torch.zeros_like(input_embeds)

        for i in range(input_ids.size(0)):
            attr = lig.attribute(
                input_embeds[i].unsqueeze(0),
                baselines=baseline[i].unsqueeze(0),
                target=int(pred_classes[i]),
                additional_forward_args=(attention_mask[i].unsqueeze(0),),
                n_steps=n_steps,
            )
            # Summarise per-token: L2 norm over embedding dim
            ig_scores = attr.squeeze(0).norm(dim=-1)  # (seq,)

            mask = attention_mask[i].bool().cpu().numpy()
            a = attn_weights[i].detach().cpu().numpy()[mask]
            g = ig_scores.detach().cpu().numpy()[mask]

            if len(a) < 3:
                continue
            rho, _ = spearmanr(a, g)
            if not np.isnan(rho):
                correlations.append(float(rho))

    mean_corr = float(np.mean(correlations)) if correlations else 0.0
    std_corr = float(np.std(correlations)) if correlations else 0.0
    return {"mean_correlation": mean_corr, "std_correlation": std_corr}


# ---------------------------------------------------------------------------
# Sufficiency
# ---------------------------------------------------------------------------

def compute_sufficiency(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    rationale_threshold: float = 0.5,
) -> Dict[str, float]:
    """Compute sufficiency: how well the rationale alone preserves prediction.

    Sufficiency = confidence_rationale_only / confidence_full.
    Higher is better (rationale tokens are sufficient).

    Args:
        model: Transformer model.
        dataloader: Dataloader yielding dicts with input_ids,
            attention_mask, labels, rationale_mask.
        device: Torch device.
        rationale_threshold: Threshold to binarise rationale_mask.

    Returns:
        Dict with ``mean_sufficiency``.
    """
    model.eval()
    scores: list[float] = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        rationale_mask = batch["rationale_mask"].to(device)

        # Full-input confidence
        full_probs, full_preds = _get_model_confidence(
            model, input_ids, attention_mask
        )

        # Rationale-only mask: keep CLS/SEP plus rationale tokens
        binary_rationale = (rationale_mask >= rationale_threshold).long()
        # Always keep special tokens (positions where attention_mask=1 but
        # the token is CLS=101 or SEP=102 for BERT). Simpler: keep first and
        # last valid position regardless.
        rationale_attn = binary_rationale * attention_mask
        # Ensure CLS and the first SEP are always kept
        rationale_attn[:, 0] = attention_mask[:, 0]
        seq_lengths = attention_mask.sum(dim=1).long()
        for j in range(rationale_attn.size(0)):
            sep_idx = seq_lengths[j] - 1
            rationale_attn[j, sep_idx] = 1

        # Mask input_ids: replace non-rationale with pad (0)
        masked_ids = input_ids * rationale_attn.long()

        rationale_probs, _ = _get_model_confidence(
            model, masked_ids, rationale_attn
        )

        for i in range(input_ids.size(0)):
            pred_cls = int(full_preds[i])
            full_conf = float(full_probs[i, pred_cls])
            rat_conf = float(rationale_probs[i, pred_cls])
            if full_conf > 0:
                scores.append(rat_conf / full_conf)

    mean_suff = float(np.mean(scores)) if scores else 0.0
    return {"mean_sufficiency": mean_suff}


# ---------------------------------------------------------------------------
# Comprehensiveness
# ---------------------------------------------------------------------------

def compute_comprehensiveness(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    rationale_threshold: float = 0.5,
) -> Dict[str, float]:
    """Compute comprehensiveness: confidence drop when rationale tokens removed.

    Comprehensiveness = confidence_full - confidence_without_rationale.
    Higher is better (rationale tokens are important).

    Args:
        model: Transformer model.
        dataloader: Dataloader yielding dicts with input_ids,
            attention_mask, labels, rationale_mask.
        device: Torch device.
        rationale_threshold: Threshold to binarise rationale_mask.

    Returns:
        Dict with ``mean_comprehensiveness``.
    """
    model.eval()
    scores: list[float] = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        rationale_mask = batch["rationale_mask"].to(device)

        # Full-input confidence
        full_probs, full_preds = _get_model_confidence(
            model, input_ids, attention_mask
        )

        # Remove rationale tokens: keep everything *except* rationale
        binary_rationale = (rationale_mask >= rationale_threshold).long()
        non_rationale = (1 - binary_rationale) * attention_mask
        # Always keep CLS and SEP
        non_rationale[:, 0] = attention_mask[:, 0]
        seq_lengths = attention_mask.sum(dim=1).long()
        for j in range(non_rationale.size(0)):
            sep_idx = seq_lengths[j] - 1
            non_rationale[j, sep_idx] = 1

        masked_ids = input_ids * non_rationale.long()

        masked_probs, _ = _get_model_confidence(
            model, masked_ids, non_rationale
        )

        for i in range(input_ids.size(0)):
            pred_cls = int(full_preds[i])
            full_conf = float(full_probs[i, pred_cls])
            mask_conf = float(masked_probs[i, pred_cls])
            scores.append(full_conf - mask_conf)

    mean_comp = float(np.mean(scores)) if scores else 0.0
    return {"mean_comprehensiveness": mean_comp}
