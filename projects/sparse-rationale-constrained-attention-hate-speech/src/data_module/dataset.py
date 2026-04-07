"""HateXplain dataset loader with rationale annotation processing.

Reference: Mathew et al., "HateXplain: A Benchmark Dataset for Explainable
Hate Speech Detection", AAAI 2021. https://arxiv.org/abs/2012.10289

Dataset structure (from HuggingFace datasets):
  - text: post string
  - label: majority vote label (hatespeech / offensive / normal)
  - rationale: per-annotator token-level binary rationale masks
  - post_id: unique identifier

Rationale construction: majority-vote across 3 annotators per token.
"""
import logging
from dataclasses import dataclass
from typing import Optional

import torch
from torch import Tensor
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)

LABEL2ID = {"normal": 0, "offensive": 1, "hatespeech": 2}
MAX_RATIONALE_ANNOTATORS = 3
MAJORITY_THRESHOLD = 2  # out of 3 annotators


@dataclass
class HateXplainExample:
    """Single processed HateXplain example."""

    post_id: str
    text: str
    label: int
    # Token-level majority-vote rationale mask (1 = highlighted by majority)
    rationale_binary: Optional[list[int]] = None
    # Normalized rationale mask for alignment loss target (sums to 1)
    rationale_normalized: Optional[list[float]] = None


class HateXplainDataset(Dataset):
    """PyTorch Dataset for HateXplain.

    Args:
        examples: List of HateXplainExample objects.
        tokenizer: HuggingFace tokenizer for BERT.
        max_length: Maximum token sequence length.
    """

    def __init__(
        self,
        examples: list[HateXplainExample],
        tokenizer: PreTrainedTokenizerBase,
        max_length: int = 128,
    ) -> None:
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, Tensor]:
        """Tokenize and return a single example.

        Returns dict with:
          input_ids, attention_mask, token_type_ids: standard BERT inputs
          labels: integer class label
          rationale_mask: normalized rationale target (zeros if unavailable)
          rationale_binary: binary mask (zeros if unavailable)
        """
        ex = self.examples[idx]

        encoding = self.tokenizer(
            ex.text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        T = self.max_length

        # Build rationale targets — align word-level mask to token-level
        rationale_normalized = torch.zeros(T, dtype=torch.float)
        rationale_binary = torch.zeros(T, dtype=torch.float)

        if ex.rationale_normalized is not None:
            # Map original word-level rationale to token positions
            # Use character-to-token alignment from tokenizer
            word_ids = encoding.word_ids(batch_index=0)
            # word_ids[i] = word index for token i (None for special tokens)
            word_to_rationale = _build_word_to_rationale(
                ex.rationale_binary, ex.rationale_normalized
            )
            for tok_idx, word_idx in enumerate(word_ids):
                if word_idx is not None and word_idx < len(word_to_rationale):
                    rationale_binary[tok_idx] = word_to_rationale[word_idx][0]
                    rationale_normalized[tok_idx] = word_to_rationale[word_idx][1]

            # Re-normalize after truncation (sum may change due to truncated tokens)
            norm_sum = rationale_normalized.sum()
            if norm_sum > 0:
                rationale_normalized = rationale_normalized / norm_sum

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "token_type_ids": encoding["token_type_ids"].squeeze(0),
            "labels": torch.tensor(ex.label, dtype=torch.long),
            "rationale_mask": rationale_normalized,
            "rationale_binary": rationale_binary,
        }


def _build_word_to_rationale(
    binary: Optional[list[int]],
    normalized: Optional[list[float]],
) -> list[tuple[float, float]]:
    """Map word index to (binary, normalized) rationale values.

    Args:
        binary: Word-level binary rationale mask.
        normalized: Word-level normalized rationale mask.

    Returns:
        List of (binary_val, normalized_val) tuples per word.
    """
    if binary is None or normalized is None:
        return []
    return list(zip([float(b) for b in binary], normalized))


def build_majority_vote_rationale(
    annotator_rationales: list[list[int]],
) -> tuple[list[int], list[float]]:
    """Construct majority-vote rationale from multiple annotator masks.

    Args:
        annotator_rationales: List of per-annotator binary masks (same length).
            Each inner list has 1 per highlighted token, 0 otherwise.

    Returns:
        Tuple of (binary_mask, normalized_mask):
          binary_mask: 1 if majority of annotators highlighted the token.
          normalized_mask: binary_mask / sum(binary_mask) for simplex target.
    """
    if not annotator_rationales:
        return [], []

    n_tokens = len(annotator_rationales[0])
    n_annotators = len(annotator_rationales)

    binary = [
        1 if sum(r[t] for r in annotator_rationales) >= MAJORITY_THRESHOLD else 0
        for t in range(n_tokens)
    ]

    total = sum(binary)
    if total == 0:
        # No majority rationale — uniform fallback (edge case)
        normalized: list[float] = [1.0 / n_tokens] * n_tokens
        logger.warning("No majority-vote rationale tokens; using uniform fallback.")
    else:
        normalized = [b / total for b in binary]

    return binary, normalized


def load_hatexplain_examples(
    split_data: list[dict],
    include_rationales: bool = True,
) -> list[HateXplainExample]:
    """Convert raw HateXplain split data to HateXplainExample objects.

    Args:
        split_data: List of raw dataset records from HuggingFace datasets.
        include_rationales: Whether to process rationale annotations.

    Returns:
        List of HateXplainExample ready for HateXplainDataset.
    """
    examples = []
    skipped = 0

    for record in split_data:
        label_str = record.get("label", "normal")
        if label_str not in LABEL2ID:
            skipped += 1
            continue
        label = LABEL2ID[label_str]

        rationale_binary = None
        rationale_normalized = None

        if include_rationales and "rationales" in record:
            raw_rationales = record["rationales"]
            if raw_rationales:
                binary, normalized = build_majority_vote_rationale(raw_rationales)
                rationale_binary = binary
                rationale_normalized = normalized

        examples.append(
            HateXplainExample(
                post_id=str(record.get("id", "")),
                text=record["post_tokens"] if isinstance(record.get("post_tokens"), str)
                else " ".join(record.get("post_tokens", [])),
                label=label,
                rationale_binary=rationale_binary,
                rationale_normalized=rationale_normalized,
            )
        )

    if skipped:
        logger.warning(f"Skipped {skipped} records with unknown labels.")
    logger.info(f"Loaded {len(examples)} examples from HateXplain split.")
    return examples
