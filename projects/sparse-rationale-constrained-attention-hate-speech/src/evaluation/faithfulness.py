"""Faithfulness metrics: comprehensiveness and sufficiency (ERASER benchmark).

Reference:
    DeYoung et al. "ERASER: A Benchmark to Evaluate Rationalized NLP Models."
    ACL 2020.

Comprehensiveness: Performance drop when rationale tokens are masked from input.
Sufficiency: Performance when only rationale tokens are kept.
"""
from __future__ import annotations

import logging
from typing import Optional

import torch
import torch.nn as nn
from torch import Tensor
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


def mask_tokens(
    input_ids: Tensor,
    attention_mask: Tensor,
    rationale_mask: Tensor,
    mask_token_id: int,
    mode: str = "mask_rationale",
) -> tuple[Tensor, Tensor]:
    """Apply token masking for comprehensiveness/sufficiency evaluation.

    Args:
        input_ids: Token ids, shape (B, L).
        attention_mask: Padding mask, shape (B, L).
        rationale_mask: Binary rationale positions, shape (B, L).
        mask_token_id: ID of [MASK] token to substitute.
        mode: "mask_rationale" (comprehensiveness) — replace rationale tokens with [MASK].
              "keep_rationale" (sufficiency) — mask all non-rationale tokens.

    Returns:
        Tuple of (modified_input_ids, modified_attention_mask).
    """
    modified = input_ids.clone()
    rat = rationale_mask.bool()

    if mode == "mask_rationale":
        # Replace rationale tokens with [MASK]
        modified[rat] = mask_token_id
    elif mode == "keep_rationale":
        # Replace non-rationale tokens with [MASK] (excluding [CLS] and [SEP])
        non_rat = ~rat & attention_mask.bool()
        # Keep [CLS] (position 0) and last non-padding token ([SEP])
        non_rat[:, 0] = False
        # Find [SEP] positions and keep them
        seq_lens = attention_mask.sum(dim=-1) - 1  # index of last real token
        for b in range(input_ids.size(0)):
            non_rat[b, seq_lens[b]] = False
        modified[non_rat] = mask_token_id
    else:
        raise ValueError(f"Unknown mode '{mode}'. Choose 'mask_rationale' or 'keep_rationale'.")

    return modified, attention_mask


@torch.no_grad()
def compute_faithfulness_metrics(
    model: nn.Module,
    dataloader: DataLoader,
    rationale_extractor,
    mask_token_id: int,
    device: str = "cuda",
) -> dict[str, float]:
    """Compute comprehensiveness and sufficiency over a dataset split.

    Args:
        model: Trained SparseBertForSequenceClassification.
        dataloader: DataLoader for the evaluation split.
        rationale_extractor: Callable(model, batch) → binary_rationale_mask (B, L).
        mask_token_id: HuggingFace tokenizer [MASK] token id.
        device: Compute device.

    Returns:
        Dict with "comprehensiveness" and "sufficiency" scores.
    """
    model.eval()
    model = model.to(device)

    orig_probs_list = []
    comp_probs_list = []
    suff_probs_list = []
    labels_list = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        token_type_ids = batch.get("token_type_ids", None)
        if token_type_ids is not None:
            token_type_ids = token_type_ids.to(device)
        labels = batch["labels"].to(device)

        # Original probabilities
        out_orig = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        orig_probs = torch.softmax(out_orig.logits, dim=-1)

        # Extract binary rationale mask
        rat_mask = rationale_extractor(model, batch, device)  # (B, L), binary float

        # Comprehensiveness: mask rationale tokens
        comp_ids, comp_amask = mask_tokens(
            input_ids, attention_mask, rat_mask, mask_token_id, mode="mask_rationale"
        )
        out_comp = model(
            input_ids=comp_ids,
            attention_mask=comp_amask,
            token_type_ids=token_type_ids,
        )
        comp_probs = torch.softmax(out_comp.logits, dim=-1)

        # Sufficiency: keep only rationale tokens
        suff_ids, suff_amask = mask_tokens(
            input_ids, attention_mask, rat_mask, mask_token_id, mode="keep_rationale"
        )
        out_suff = model(
            input_ids=suff_ids,
            attention_mask=suff_amask,
            token_type_ids=token_type_ids,
        )
        suff_probs = torch.softmax(out_suff.logits, dim=-1)

        orig_probs_list.append(orig_probs.cpu())
        comp_probs_list.append(comp_probs.cpu())
        suff_probs_list.append(suff_probs.cpu())
        labels_list.append(labels.cpu())

    orig_probs = torch.cat(orig_probs_list)  # (N, C)
    comp_probs = torch.cat(comp_probs_list)
    suff_probs = torch.cat(suff_probs_list)
    labels = torch.cat(labels_list)  # (N,)

    # Predicted class probabilities
    predicted_labels = orig_probs.argmax(dim=-1)
    orig_pred_probs = orig_probs.gather(1, predicted_labels.unsqueeze(1)).squeeze(1)
    comp_pred_probs = comp_probs.gather(1, predicted_labels.unsqueeze(1)).squeeze(1)
    suff_pred_probs = suff_probs.gather(1, predicted_labels.unsqueeze(1)).squeeze(1)

    # Comprehensiveness = mean(p_orig - p_comp): how much does removing rationale hurt?
    comprehensiveness = (orig_pred_probs - comp_pred_probs).mean().item()

    # Sufficiency = mean(p_orig - p_suff): how much does keeping only rationale lose?
    sufficiency = (orig_pred_probs - suff_pred_probs).mean().item()

    return {
        "comprehensiveness": comprehensiveness,
        "sufficiency": sufficiency,
    }
