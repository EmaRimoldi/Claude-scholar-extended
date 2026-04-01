"""BERT with sparsemax attention in selected heads for rationale-constrained classification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
from torch import Tensor
from transformers import BertModel, BertPreTrainedModel
from transformers.modeling_outputs import SequenceClassifierOutput

from .sparsemax import Sparsemax


@dataclass
class SparseBertConfig:
    """Configuration for SparseBertForSequenceClassification.

    Args:
        pretrained_model_name: HuggingFace model identifier.
        num_labels: Number of output classes (3 for HateXplain).
        supervised_heads: List of (layer_idx, head_idx) tuples to apply sparsemax.
            Pass [] to use standard softmax everywhere (M0/M1 baseline mode).
        alignment_loss_weight: Lambda weighting the alignment loss term.
        dropout: Classifier dropout rate.
    """

    pretrained_model_name: str = "bert-base-uncased"
    num_labels: int = 3
    supervised_heads: list[tuple[int, int]] = None  # type: ignore[assignment]
    alignment_loss_weight: float = 0.1
    dropout: float = 0.1

    def __post_init__(self) -> None:
        if self.supervised_heads is None:
            self.supervised_heads = []


class SparseBertForSequenceClassification(BertPreTrainedModel):
    """BERT sequence classifier with optional sparsemax in selected CLS attention heads.

    Architecture:
    - BERT-base-uncased backbone (12 layers, 12 heads)
    - In each supervised head (layer l, head h): replace softmax with sparsemax
    - CLS token's attention weights for supervised heads are collected as model rationales
    - Classification head: dropout → linear(768 → num_labels)
    - Loss: CrossEntropy(logits, labels) + λ * AlignmentLoss(attention_weights, rationale_mask)

    The alignment loss is applied only over supervised heads. If no supervised heads are
    configured (baseline M0), the model reduces to standard BERT classification.
    """

    def __init__(self, bert_config, model_cfg: SparseBertConfig) -> None:
        # Force eager attention so output_attentions=True works at inference time.
        # SDPA (the default in transformers>=4.36) does not support attention output.
        bert_config._attn_implementation = "eager"
        super().__init__(bert_config)
        self.model_cfg = model_cfg
        self.num_labels = model_cfg.num_labels

        self.bert = BertModel(bert_config, add_pooling_layer=True)
        self.dropout = nn.Dropout(model_cfg.dropout)
        self.classifier = nn.Linear(bert_config.hidden_size, model_cfg.num_labels)

        # Patch supervised heads: replace softmax with sparsemax
        self._sparsemax = Sparsemax(dim=-1)
        self._patch_supervised_heads()

        self.post_init()

    # ------------------------------------------------------------------
    # Head patching
    # ------------------------------------------------------------------

    def _patch_supervised_heads(self) -> None:
        """Replace softmax with sparsemax in configured attention heads.

        BERT attention computes: softmax(QK^T / sqrt(d_k)) · V.
        We intercept per-head attention scores after QK^T / sqrt(d_k)
        and before the value aggregation using forward hooks.
        """
        self._hooks: list = []
        supervised_set = set(map(tuple, self.model_cfg.supervised_heads))
        if not supervised_set:
            return

        for layer_idx, layer in enumerate(self.bert.encoder.layer):
            for head_idx in range(layer.attention.self.num_attention_heads):
                if (layer_idx, head_idx) in supervised_set:
                    hook = _SparsemaxHeadHook(head_idx, self._sparsemax)
                    handle = layer.attention.self.register_forward_hook(
                        hook.make_hook(head_idx)
                    )
                    self._hooks.append(handle)

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Optional[Tensor] = None,
        token_type_ids: Optional[Tensor] = None,
        rationale_mask: Optional[Tensor] = None,
        labels: Optional[Tensor] = None,
        alignment_loss_fn: Optional[nn.Module] = None,
        return_attention: bool = False,
        output_attentions: Optional[bool] = None,  # accepted for HF API compatibility; always True internally
    ) -> SequenceClassifierOutput | dict:
        """Forward pass.

        Args:
            input_ids: Token ids, shape (B, L).
            attention_mask: Padding mask, shape (B, L).
            token_type_ids: Segment ids, shape (B, L).
            rationale_mask: Binary rationale annotation, shape (B, L).
                Required when alignment_loss_fn is provided.
            labels: Class indices, shape (B,). Required for loss computation.
            alignment_loss_fn: Callable (attention_weights, rationale_mask) → scalar.
                If None, no alignment loss is added.
            return_attention: Whether to return supervised head attention weights.

        Returns:
            HuggingFace SequenceClassifierOutput (or dict with extra 'attention' key).
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            output_attentions=True,
        )

        pooled_output = outputs.pooler_output  # (B, H)
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)  # (B, num_labels)

        loss = None
        if labels is not None:
            ce_loss = nn.CrossEntropyLoss()(logits, labels)
            loss = ce_loss

            if alignment_loss_fn is not None and rationale_mask is not None:
                supervised_attn = self._extract_supervised_attention(
                    outputs.attentions, attention_mask
                )  # (B, k, L)
                align_loss = alignment_loss_fn(supervised_attn, rationale_mask)
                loss = ce_loss + self.model_cfg.alignment_loss_weight * align_loss

        result = SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )

        if return_attention:
            supervised_attn = self._extract_supervised_attention(
                outputs.attentions, attention_mask
            )
            return {"output": result, "attention": supervised_attn}

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_supervised_attention(
        self,
        all_attentions: tuple[Tensor, ...],
        attention_mask: Optional[Tensor],
    ) -> Tensor:
        """Extract CLS-token attention weights for supervised heads.

        BERT output.attentions is a tuple of length num_layers, each tensor
        shape (B, num_heads, L, L). We select row 0 (CLS query) for each
        supervised (layer, head), applying the padding mask.

        Returns:
            Tensor of shape (B, k, L) where k = len(supervised_heads).
        """
        supervised = self.model_cfg.supervised_heads
        if not supervised:
            raise ValueError("No supervised heads configured.")

        extracted = []
        for layer_idx, head_idx in supervised:
            # shape: (B, L)  — CLS query attends to all tokens
            attn = all_attentions[layer_idx][:, head_idx, 0, :]
            if attention_mask is not None:
                # Zero out padding positions (they should already be ~0 after masking
                # but ensure consistency with the padding mask)
                pad_mask = attention_mask.float()
                attn = attn * pad_mask
            extracted.append(attn)

        return torch.stack(extracted, dim=1)  # (B, k, L)


# ------------------------------------------------------------------
# Hook utility: applied when sparsemax head injection is needed
# ------------------------------------------------------------------


class _SparsemaxHeadHook:
    """Forward hook factory for replacing softmax with sparsemax in a specific head.

    Note: BERT's BertSelfAttention.forward() computes all-head attention scores
    jointly and applies a single softmax. To intercept per-head, we use a
    post-forward hook and re-compute that head's output via sparsemax, then
    patch the module's cached attention_probs tensor.

    This is a lightweight approach that avoids subclassing BertSelfAttention,
    which would require deep transformers internals changes.

    LIMITATION: This hook modifies attention_probs AFTER the forward pass,
    meaning the hook only affects the stored attention weights (used for alignment
    loss computation), NOT the value aggregation (which already used softmax).

    For full sparsemax in value aggregation, use SparseBertSelfAttention (below),
    which overrides BertSelfAttention entirely. The hook approach is kept here
    for experimental comparison purposes.
    """

    def __init__(self, head_idx: int, sparsemax: Sparsemax) -> None:
        self.head_idx = head_idx
        self.sparsemax = sparsemax

    def make_hook(self, head_idx: int):
        sparsemax = self.sparsemax

        def hook(module, input, output):
            # output is (context_layer, attention_probs) when output_attentions=True
            if isinstance(output, tuple) and len(output) == 2:
                context_layer, attention_probs = output
                # attention_probs: (B, num_heads, L, L)
                probs = attention_probs.clone()
                probs[:, head_idx, :, :] = sparsemax(
                    attention_probs[:, head_idx, :, :]
                )
                return (context_layer, probs)
            return output

        return hook


class SparseBertSelfAttention(nn.Module):
    """Drop-in replacement for BertSelfAttention with per-head activation choice.

    Implements the full sparsemax path including value aggregation, unlike the
    hook approach. Used when model_cfg.supervised_heads requires true sparse
    value weighting (not just sparse stored weights).

    Usage: inject into model via monkey-patching before the first forward pass.
    See `inject_sparsemax_attention()` factory function.
    """

    def __init__(self, original: nn.Module, supervised_heads: set[int], sparsemax: Sparsemax) -> None:
        super().__init__()
        # Copy all parameters from original BertSelfAttention
        self.__dict__.update(original.__dict__)
        self._supervised_heads = supervised_heads
        self._sparsemax = sparsemax

    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Optional[Tensor] = None,
        head_mask: Optional[Tensor] = None,
        encoder_hidden_states: Optional[Tensor] = None,
        encoder_attention_mask: Optional[Tensor] = None,
        past_key_value=None,
        output_attentions: bool = False,
    ):
        """Forward matching BertSelfAttention signature."""
        import math

        B, L, _ = hidden_states.shape
        num_heads = self.num_attention_heads
        head_dim = self.attention_head_size

        def transpose_for_scores(x: Tensor) -> Tensor:
            # (B, L, H*d) → (B, H, L, d)
            new_shape = x.size()[:-1] + (num_heads, head_dim)
            x = x.view(new_shape)
            return x.permute(0, 2, 1, 3)

        q = transpose_for_scores(self.query(hidden_states))
        k_src = encoder_hidden_states if encoder_hidden_states is not None else hidden_states
        k = transpose_for_scores(self.key(k_src))
        v = transpose_for_scores(self.value(k_src))

        # Scaled dot-product attention scores: (B, H, L, L)
        scores = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(head_dim)
        if attention_mask is not None:
            scores = scores + attention_mask

        # Apply per-head activation
        probs_list = []
        for h in range(num_heads):
            if h in self._supervised_heads:
                probs_list.append(self._sparsemax(scores[:, h, :, :]))
            else:
                probs_list.append(torch.softmax(scores[:, h, :, :], dim=-1))
        attention_probs = torch.stack(probs_list, dim=1)  # (B, H, L, L)

        if head_mask is not None:
            attention_probs = attention_probs * head_mask

        attention_probs = self.dropout(attention_probs)
        context = torch.matmul(attention_probs, v)  # (B, H, L, d)
        context = context.permute(0, 2, 1, 3).contiguous()
        context = context.view(B, L, num_heads * head_dim)

        outputs = (context, attention_probs) if output_attentions else (context,)
        return outputs


def inject_sparsemax_attention(
    model: SparseBertForSequenceClassification,
    supervised_heads: list[tuple[int, int]],
) -> SparseBertForSequenceClassification:
    """Replace BertSelfAttention with SparseBertSelfAttention in supervised layers.

    This provides TRUE sparsemax value aggregation (not just stored weight patching).
    Call this after model construction, before training.

    Args:
        model: SparseBertForSequenceClassification instance.
        supervised_heads: List of (layer_idx, head_idx) pairs.

    Returns:
        Model with injected SparseBertSelfAttention modules.
    """
    from collections import defaultdict

    head_map: dict[int, set[int]] = defaultdict(set)
    for layer_idx, head_idx in supervised_heads:
        head_map[layer_idx].add(head_idx)

    sparsemax = Sparsemax(dim=-1)
    for layer_idx, head_set in head_map.items():
        orig = model.bert.encoder.layer[layer_idx].attention.self
        replacement = SparseBertSelfAttention(orig, head_set, sparsemax)
        model.bert.encoder.layer[layer_idx].attention.self = replacement

    return model
