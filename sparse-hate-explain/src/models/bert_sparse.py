"""BERT with configurable sparse attention and attention supervision.

Wraps ``transformers.BertModel`` and adds:
* Configurable attention normalization (softmax or sparsemax targets).
* An attention supervision loss that aligns selected heads with a
  rationale mask via KL divergence.
* fp16 / mixed-precision compatibility throughout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from transformers import BertModel, BertConfig

from .sparsemax import sparsemax


@dataclass
class BertSparseOutput:
    """Structured output container for ``BertSparseForClassification``."""

    loss: Tensor
    ce_loss: Tensor
    attn_loss: Tensor
    logits: Tensor
    attentions: tuple[Tensor, ...]


class BertSparseForClassification(nn.Module):
    """BERT classifier with attention supervision on selected heads.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier (e.g. ``"bert-base-uncased"``).
    num_labels : int
        Number of classification labels.
    supervised_heads : list[tuple[int, int]] | str
        Specific ``(layer, head)`` pairs to supervise, or ``"all"`` for every
        head in every layer.
    attention_transform : str
        How to create target distributions from rationale masks:
        ``"softmax"`` or ``"sparsemax"``.
    lambda_attn : float
        Weight multiplying the attention supervision loss.
    """

    def __init__(
        self,
        model_name: str = "bert-base-uncased",
        num_labels: int = 2,
        supervised_heads: Sequence[tuple[int, int]] | str = "all",
        attention_transform: str = "softmax",
        lambda_attn: float = 1.0,
    ) -> None:
        super().__init__()

        self.config: BertConfig = BertConfig.from_pretrained(model_name)
        self.bert = BertModel.from_pretrained(
            model_name, config=self.config, attn_implementation="eager"
        )
        self.num_labels = num_labels
        self.lambda_attn = lambda_attn

        if attention_transform not in ("softmax", "sparsemax"):
            raise ValueError(
                f"attention_transform must be 'softmax' or 'sparsemax', "
                f"got '{attention_transform}'"
            )
        self.attention_transform = attention_transform

        # Resolve supervised head indices.
        n_layers = self.config.num_hidden_layers
        n_heads = self.config.num_attention_heads
        if supervised_heads == "all":
            self.supervised_heads: list[tuple[int, int]] = [
                (layer, head)
                for layer in range(n_layers)
                for head in range(n_heads)
            ]
        else:
            self.supervised_heads = list(supervised_heads)

        # Classification head on [CLS].
        hidden_size = self.config.hidden_size
        self.dropout = nn.Dropout(self.config.hidden_dropout_prob)
        self.classifier = nn.Linear(hidden_size, num_labels)

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        labels: Optional[Tensor] = None,
        rationale_mask: Optional[Tensor] = None,
    ) -> BertSparseOutput:
        """Run the full forward pass.

        Parameters
        ----------
        input_ids : Tensor[B, L]
            Token ids.
        attention_mask : Tensor[B, L]
            1 for real tokens, 0 for padding.
        labels : Tensor[B], optional
            Ground-truth class labels (required for loss computation).
        rationale_mask : Tensor[B, L], optional
            Binary mask (1 = rationale token) used to create target attention
            distributions.  Required when ``lambda_attn > 0``.

        Returns
        -------
        BertSparseOutput
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=True,
        )

        # attentions: tuple of (B, H, L, L) tensors, one per layer.
        attentions: tuple[Tensor, ...] = outputs.attentions
        cls_hidden = outputs.last_hidden_state[:, 0]  # [CLS]
        logits: Tensor = self.classifier(self.dropout(cls_hidden))

        # Classification loss.
        if labels is not None:
            ce_loss = F.cross_entropy(logits, labels)
        else:
            ce_loss = torch.tensor(0.0, device=logits.device, dtype=logits.dtype)

        # Attention supervision loss.
        if rationale_mask is not None and self.lambda_attn > 0.0:
            attn_loss = self.compute_attention_loss(
                attentions, rationale_mask, attention_mask
            )
        else:
            attn_loss = torch.tensor(0.0, device=logits.device, dtype=logits.dtype)

        total_loss = ce_loss + self.lambda_attn * attn_loss

        return BertSparseOutput(
            loss=total_loss,
            ce_loss=ce_loss,
            attn_loss=attn_loss,
            logits=logits,
            attentions=attentions,
        )

    # ------------------------------------------------------------------
    # Attention supervision
    # ------------------------------------------------------------------

    def compute_attention_loss(
        self,
        attentions: tuple[Tensor, ...],
        rationale_mask: Tensor,
        attention_mask: Tensor,
    ) -> Tensor:
        """KL-divergence loss between supervised heads and rationale targets.

        Parameters
        ----------
        attentions : tuple[Tensor]
            Per-layer attention weights, each of shape ``(B, H, L, L)``.
        rationale_mask : Tensor[B, L]
            Binary rationale indicator (1 = rationale token).
        attention_mask : Tensor[B, L]
            Padding mask (1 = real token).

        Returns
        -------
        Tensor
            Scalar attention supervision loss.
        """
        # Build target distribution from rationale_mask (B, L).
        # We want a distribution over *key* positions for every query, so the
        # target is the same for every query position.
        target_scores = rationale_mask.float()

        # Mask out padding in the target.
        target_scores = target_scores * attention_mask.float()

        # Apply configured transform to create a valid distribution.
        if self.attention_transform == "sparsemax":
            target_dist = sparsemax(target_scores, dim=-1)
        else:
            # Softmax: use large negative for masked positions.
            neg_inf = torch.finfo(target_scores.dtype).min
            masked_scores = target_scores.masked_fill(
                attention_mask == 0, neg_inf
            )
            target_dist = F.softmax(masked_scores, dim=-1)

        # Ensure valid distribution even when rationale is all-zero for a sample.
        # Fall back to uniform over non-padding tokens.
        all_zero = target_dist.sum(dim=-1, keepdim=True) < 1e-8
        if all_zero.any():
            uniform = attention_mask.float()
            uniform = uniform / uniform.sum(dim=-1, keepdim=True).clamp(min=1.0)
            target_dist = torch.where(all_zero, uniform, target_dist)

        # target_dist: (B, L) -- broadcast to (B, 1, 1, L) for heads.
        target_dist = target_dist.unsqueeze(1).unsqueeze(1)  # (B, 1, 1, L)

        loss_accum = torch.tensor(0.0, device=rationale_mask.device, dtype=torch.float32)
        n_heads = 0

        for layer_idx, head_idx in self.supervised_heads:
            # attn_weights: (B, H, L, L) -> select head -> (B, L, L)
            head_attn = attentions[layer_idx][:, head_idx]  # (B, L, L)

            # Clamp for numerical stability in log.
            head_attn_clamped = head_attn.clamp(min=1e-12).float()
            target_expanded = target_dist[:, 0, 0, :].unsqueeze(1).expand_as(head_attn)  # (B, L, L)
            target_expanded = target_expanded.clamp(min=1e-12).float()

            # KL(target || head_attn) = sum target * log(target / head_attn)
            kl = target_expanded * (target_expanded.log() - head_attn_clamped.log())

            # Mask padding query positions: only compute loss for real tokens.
            query_mask = attention_mask.float().unsqueeze(-1)  # (B, L, 1)
            kl = kl * query_mask

            # Also mask padding key positions.
            key_mask = attention_mask.float().unsqueeze(1)  # (B, 1, L)
            kl = kl * key_mask

            # Mean over non-padding entries.
            n_valid = (query_mask * key_mask).sum().clamp(min=1.0)
            loss_accum = loss_accum + kl.sum() / n_valid
            n_heads += 1

        if n_heads > 0:
            loss_accum = loss_accum / n_heads

        return loss_accum

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def get_head_attentions(
        self,
        attentions: tuple[Tensor, ...],
        layer: int,
        head: int,
    ) -> Tensor:
        """Extract attention weights for a single head.

        Parameters
        ----------
        attentions : tuple[Tensor]
            Output of BERT with ``output_attentions=True``.
        layer : int
            Transformer layer index (0-based).
        head : int
            Attention head index (0-based).

        Returns
        -------
        Tensor[B, L, L]
            Attention weights for the specified head.
        """
        return attentions[layer][:, head]
