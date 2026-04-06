"""WordPiece tokenization with rationale mask alignment for HateXplain."""
from __future__ import annotations

from typing import Optional

from transformers import PreTrainedTokenizerBase


def tokenize_with_rationale_alignment(
    tokens: list[str],
    rationale_scores: Optional[list[float]],
    tokenizer: PreTrainedTokenizerBase,
    max_length: int = 128,
) -> tuple[dict, Optional[list[float]]]:
    """Tokenize a list of words and align rationale scores to sub-tokens.

    Alignment strategy: each sub-token inherits the rationale score of its
    originating word (first-subtoken propagation). The [CLS] and [SEP] tokens
    receive score 0.

    Args:
        tokens: List of whitespace-separated words from HateXplain.
        rationale_scores: Per-word rationale scores (floats in [0, 1]).
            If None, no rationale alignment is performed.
        tokenizer: BERT-compatible tokenizer.
        max_length: Maximum total sequence length (includes [CLS] and [SEP]).

    Returns:
        Tuple of (encoding_dict, aligned_rationale).
        encoding_dict contains input_ids, attention_mask, token_type_ids.
        aligned_rationale is a list of floats aligned to sub-tokens, or None.
    """
    # Tokenize each word separately to get word-to-subtoken mapping
    word_encodings = [tokenizer.tokenize(w) for w in tokens]

    # Build flat sub-token list and word indices
    flat_subtokens: list[str] = []
    word_index_per_subtoken: list[int] = []
    for word_idx, subtokens in enumerate(word_encodings):
        for st in subtokens:
            flat_subtokens.append(st)
            word_index_per_subtoken.append(word_idx)

    # Truncate to fit max_length (reserve 2 for [CLS] and [SEP])
    max_subtokens = max_length - 2
    flat_subtokens = flat_subtokens[:max_subtokens]
    word_index_per_subtoken = word_index_per_subtoken[:max_subtokens]

    # Build full token sequence with special tokens
    full_tokens = [tokenizer.cls_token] + flat_subtokens + [tokenizer.sep_token]
    input_ids = tokenizer.convert_tokens_to_ids(full_tokens)

    seq_len = len(input_ids)
    attention_mask = [1] * seq_len
    token_type_ids = [0] * seq_len

    # Pad to max_length
    pad_len = max_length - seq_len
    if pad_len > 0:
        input_ids += [tokenizer.pad_token_id] * pad_len
        attention_mask += [0] * pad_len
        token_type_ids += [0] * pad_len

    encoding = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "token_type_ids": token_type_ids,
    }

    if rationale_scores is None:
        return encoding, None

    # Align rationale scores: [CLS]=0, each sub-token gets its word's score, [SEP]=0
    aligned: list[float] = [0.0]  # [CLS]
    for word_idx in word_index_per_subtoken:
        if word_idx < len(rationale_scores):
            aligned.append(rationale_scores[word_idx])
        else:
            aligned.append(0.0)
    aligned.append(0.0)  # [SEP]

    # Pad rationale to max_length with zeros
    aligned += [0.0] * (max_length - len(aligned))
    assert len(aligned) == max_length, f"Rationale length mismatch: {len(aligned)} vs {max_length}"

    return encoding, aligned


def normalize_rationale(rationale: list[float], eps: float = 1e-8) -> list[float]:
    """Normalize a rationale mask to sum to 1 (for distribution alignment loss).

    If the rationale is all zeros (no annotated rationale), returns uniform over
    all non-padding tokens. This avoids NaN in the alignment loss while preserving
    the all-zero signal for gradient purposes (gradient is 0 when target is 0 everywhere).

    Args:
        rationale: List of non-negative floats.
        eps: Small constant for numerical stability.

    Returns:
        Normalized list summing to 1 (or uniform if sum is zero).
    """
    total = sum(rationale)
    if total < eps:
        n = max(sum(1 for r in rationale if r >= 0), 1)
        return [1.0 / n for _ in rationale]
    return [r / total for r in rationale]
