"""BERT-based hate speech classifier with optional sparsemax attention.

Implements Conditions C1-C5 from the experiment plan:
  C1: softmax, no supervision
  C2: softmax, KL alignment loss (SRA replication)
  C3: sparsemax, no supervision
  C4: sparsemax, MSE alignment loss (all 12 heads) — primary contribution
  C5: sparsemax, MSE alignment loss (top-6 heads by gradient importance)

Architecture: BERT-base-uncased, replace final-layer attention with
sparsemax in conditions C3-C5. CLS token representation → linear head.
"""
import logging
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
from torch import Tensor
from transformers import BertConfig, BertModel, BertPreTrainedModel
from transformers.modeling_outputs import BaseModelOutputWithPoolingAndCrossAttentions

from .sparsemax import sparsemax

logger = logging.getLogger(__name__)

LABEL2ID = {"normal": 0, "offensive": 1, "hatespeech": 2}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
NUM_LABELS = 3


@dataclass
class ClassifierConfig:
    """Configuration for BertHateSpeechClassifier.

    Args:
        model_name: HuggingFace model identifier.
        use_sparsemax: Replace final-layer softmax with sparsemax.
        supervised_heads: List of head indices (0-indexed) to supervise.
            None means no supervision; empty list means no supervision.
            [0..11] means all 12 heads; pass top-6 indices for H3.
        alpha: Alignment loss weight. 0 means no alignment loss.
        use_kl_loss: Use KL loss instead of MSE (for SRA replication, C2).
        num_labels: Number of output classes.
        dropout: Classifier dropout.
    """

    model_name: str = "bert-base-uncased"
    use_sparsemax: bool = False
    supervised_heads: Optional[list[int]] = None
    alpha: float = 0.3
    use_kl_loss: bool = False
    num_labels: int = NUM_LABELS
    dropout: float = 0.1


class SparsemaxBertSelfAttention(nn.Module):
    """BERT self-attention with sparsemax replacing softmax in specified heads.

    Wraps an existing BertSelfAttention layer. Intercepts the attention score
    computation and routes specified heads through sparsemax instead of softmax.

    Args:
        original_attn: Original BertSelfAttention module from BERT.
        sparsemax_heads: Set of head indices (0-indexed) to use sparsemax.
    """

    def __init__(
        self,
        original_attn: nn.Module,
        sparsemax_heads: set[int],
    ) -> None:
        super().__init__()
        self.original_attn = original_attn
        self.sparsemax_heads = sparsemax_heads
        # Mirror attributes accessed by Transformers internals
        self.num_heads = original_attn.num_attention_heads
        self.head_dim = original_attn.attention_head_size
        # Expose query/key/value and dropout for any caller that accesses them directly
        self.query = original_attn.query
        self.key = original_attn.key
        self.value = original_attn.value
        self.dropout = original_attn.dropout
        self.scaling = getattr(original_attn, "scaling", self.head_dim ** -0.5)

    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Optional[Tensor] = None,
        past_key_values: object = None,
        **kwargs: object,
    ) -> tuple[Tensor, ...]:
        """Forward with per-head sparsemax injection (Transformers 5.x API).

        Matches BertSelfAttention.forward signature in transformers>=5.0:
          (hidden_states, attention_mask, past_key_values, **kwargs)
        Returns (attn_output, attn_weights).
        """
        input_shape = hidden_states.shape[:-1]   # (B, T)
        hidden_shape = (*input_shape, -1, self.head_dim)  # (B, T, H, d)

        # QKV: (B, T, H*d) -> (B, H, T, d)
        query = self.query(hidden_states).view(*hidden_shape).transpose(1, 2)
        key = self.key(hidden_states).view(*hidden_shape).transpose(1, 2)
        value = self.value(hidden_states).view(*hidden_shape).transpose(1, 2)

        # Attention scores: (B, H, T, T)
        scores = torch.matmul(query, key.transpose(2, 3)) * self.scaling

        if attention_mask is not None:
            scores = scores + attention_mask

        # Per-head activation: sparsemax for supervised heads, softmax for the rest
        # NUMERICAL SAFETY: BERT uses torch.finfo().min (~-3.4e38) as the additive
        # attention mask for padding positions. Summing many such values in sparsemax's
        # cumsum overflows float32 to -inf, which corrupts the support computation.
        # Clamp to -1e4: sufficient to exclude padding (real scores are in ~[-50, +50]),
        # and safe for float32 cumsum (max overflow threshold ~3.4e38).
        scores_safe = scores.clamp(min=-1e4)
        weights_list = []
        for h in range(self.num_heads):
            s_h = scores_safe[:, h, :, :]  # (B, T_q, T_k)
            if h in self.sparsemax_heads:
                # Apply sparsemax over the key dimension for each query position
                w_h = sparsemax(s_h)
            else:
                w_h = torch.softmax(s_h, dim=-1)
            weights_list.append(w_h.unsqueeze(1))  # (B, 1, T, T)
        weights = torch.cat(weights_list, dim=1)  # (B, H, T, T)

        # Dropout on attention weights
        dropout_p = 0.0 if not self.training else self.dropout.p
        if dropout_p > 0.0:
            weights = torch.nn.functional.dropout(weights, p=dropout_p, training=True)

        # Context: (B, H, T, d) -> (B, T, H*d)
        attn_output = torch.matmul(weights, value)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(*input_shape, -1)

        return attn_output, weights


class BertHateSpeechClassifier(nn.Module):
    """BERT hate speech classifier supporting softmax and sparsemax conditions.

    For conditions with supervised_heads, the model returns CLS attention
    weights from the final encoder layer (averaged over supervised heads)
    alongside logits, enabling the joint alignment loss in the training loop.

    Implements Proposition 1: for tokens with zero sparsemax weight, their
    contribution to h_CLS is exactly zero, guaranteeing maximal comprehensiveness.
    """

    def __init__(self, cfg: ClassifierConfig) -> None:
        super().__init__()
        self.cfg = cfg

        bert_config = BertConfig.from_pretrained(
            cfg.model_name,
            num_labels=cfg.num_labels,
            output_attentions=True,
        )
        self.bert: BertModel = BertModel.from_pretrained(
            cfg.model_name,
            config=bert_config,
            ignore_mismatched_sizes=False,
        )

        hidden_size = self.bert.config.hidden_size
        self.dropout = nn.Dropout(cfg.dropout)
        self.classifier = nn.Linear(hidden_size, cfg.num_labels)

        # Inject sparsemax into final encoder layer if requested
        if cfg.use_sparsemax:
            self._inject_sparsemax(cfg.supervised_heads)

        # Store which heads to return for alignment loss
        self._supervised_heads: set[int] = (
            set(cfg.supervised_heads) if cfg.supervised_heads else set()
        )

        logger.info(
            f"BertHateSpeechClassifier: sparsemax={cfg.use_sparsemax}, "
            f"supervised_heads={cfg.supervised_heads}, alpha={cfg.alpha}"
        )

    def _inject_sparsemax(self, supervised_heads: Optional[list[int]]) -> None:
        """Replace softmax with sparsemax in final encoder layer.

        Only the final layer (index 11 in bert-base) is modified.
        All earlier layers retain standard softmax attention.
        """
        final_layer = self.bert.encoder.layer[-1]
        original_self_attn = final_layer.attention.self

        if supervised_heads is None:
            # Unsupervised sparsemax: all heads use sparsemax, no supervision
            sparsemax_heads_set = set(range(self.bert.config.num_attention_heads))
        else:
            sparsemax_heads_set = set(supervised_heads)

        final_layer.attention.self = SparsemaxBertSelfAttention(
            original_self_attn,
            sparsemax_heads=sparsemax_heads_set,
        )
        logger.info(f"Injected sparsemax into final layer, heads: {sparsemax_heads_set}")

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        token_type_ids: Optional[Tensor] = None,
        rationale_mask: Optional[Tensor] = None,
    ) -> dict[str, Tensor]:
        """Forward pass.

        Args:
            input_ids: Token ids, shape (B, T).
            attention_mask: Padding mask (1=real, 0=pad), shape (B, T).
            token_type_ids: Segment ids, shape (B, T).
            rationale_mask: Binary rationale annotation mask (B, T). Optional;
                used externally for loss computation — not consumed here.

        Returns:
            Dict with keys:
              'logits': shape (B, num_labels)
              'cls_attention': shape (B, T) — averaged over supervised heads;
                  None if no supervised heads.
              'all_attentions': all layer attention weights (optional).
        """
        outputs: BaseModelOutputWithPoolingAndCrossAttentions = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            output_attentions=True,
        )

        # CLS classification
        cls_repr = outputs.last_hidden_state[:, 0, :]  # (B, hidden)
        cls_repr = self.dropout(cls_repr)
        logits = self.classifier(cls_repr)

        # Extract CLS attention from final layer over supervised heads
        cls_attention = None
        if self._supervised_heads and outputs.attentions is not None:
            final_attn = outputs.attentions[-1]  # (B, H, T, T)
            # CLS query attends to all tokens: take row 0 of Q dimension
            cls_rows = final_attn[:, :, 0, :]  # (B, H, T) — CLS attends to all tokens
            # Average over supervised heads only
            head_indices = sorted(self._supervised_heads)
            supervised_attn = cls_rows[:, head_indices, :]  # (B, k, T)
            cls_attention = supervised_attn.mean(dim=1)  # (B, T)

        return {
            "logits": logits,
            "cls_attention": cls_attention,
        }
