"""HateXplain dataset loader and collation utilities.

Loads directly from the raw JSON files downloaded from the HateXplain GitHub repository
(punyajoy/HateXplain). This avoids dependency on the HuggingFace loading script which
requires trust_remote_code and has network/version compatibility issues.

Expected files:
    data/hatexplain/dataset.json          — all 20,148 examples
    data/hatexplain/post_id_divisions.json — train/val/test split IDs
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from torch import Tensor
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase


LABEL_MAP = {"hatespeech": 0, "offensive": 1, "normal": 2}
LABEL_NAMES = ["hatespeech", "offensive", "normal"]

# Default paths (relative to project root, or override via DATA_DIR env var)
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "hatexplain"


@dataclass
class HateXplainExample:
    """Single HateXplain example after preprocessing."""

    post_id: str
    input_ids: list[int]
    attention_mask: list[int]
    token_type_ids: list[int]
    label: int
    rationale_mask: Optional[list[float]]  # sum-normalised or None for M0
    word_tokens: list[str]  # original words for word-level evaluation


class HateXplainDataset(Dataset):
    """PyTorch Dataset for HateXplain loaded from local JSON files.

    Majority-vote label; rationale mask is per-word annotation aggregated
    across annotators (fraction of annotators who marked each word), then
    aligned to WordPiece sub-tokens via preprocessing.py.

    Args:
        split: One of "train", "validation", "test".
        tokenizer: HuggingFace tokenizer for BERT.
        max_length: Maximum token sequence length.
        include_rationale: Whether to include rationale masks (set False for M0).
        rationale_mode: "binary" (threshold at 0.5) or "soft" (use raw fractions).
        data_dir: Path to directory containing dataset.json and post_id_divisions.json.
            Defaults to data/hatexplain/ relative to project root.
    """

    def __init__(
        self,
        split: str,
        tokenizer: PreTrainedTokenizerBase,
        max_length: int = 128,
        include_rationale: bool = True,
        rationale_mode: str = "soft",
        data_dir: Optional[Path | str] = None,
    ) -> None:
        self.split = split
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.include_rationale = include_rationale
        self.rationale_mode = rationale_mode

        data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        all_data = json.loads((data_dir / "dataset.json").read_text())
        divisions = json.loads((data_dir / "post_id_divisions.json").read_text())

        # Normalise split name: HateXplain uses "val" not "validation"
        split_key = "val" if split == "validation" else split
        split_ids = set(divisions[split_key])

        raw_examples = [v for k, v in all_data.items() if k in split_ids]
        self.examples = [self._process(ex) for ex in raw_examples]

    def _process(self, raw: dict) -> HateXplainExample:
        from .preprocessing import tokenize_with_rationale_alignment

        post_id = raw["post_id"]
        tokens = raw["post_tokens"]  # list of str
        label = self._majority_label(raw["annotators"])

        if self.include_rationale:
            rationale_scores = self._aggregate_rationale(
                raw["rationales"], n_tokens=len(tokens)
            )
            if self.rationale_mode == "binary":
                rationale_scores = [1.0 if s >= 0.5 else 0.0 for s in rationale_scores]
        else:
            rationale_scores = None

        encoding, aligned_rationale = tokenize_with_rationale_alignment(
            tokens=tokens,
            rationale_scores=rationale_scores,
            tokenizer=self.tokenizer,
            max_length=self.max_length,
        )

        return HateXplainExample(
            post_id=post_id,
            input_ids=encoding["input_ids"],
            attention_mask=encoding["attention_mask"],
            token_type_ids=encoding.get("token_type_ids", [0] * len(encoding["input_ids"])),
            label=label,
            rationale_mask=aligned_rationale,
            word_tokens=tokens,
        )

    @staticmethod
    def _majority_label(annotators: list[dict]) -> int:
        """Determine majority vote label from list of annotator dicts."""
        label_counts: dict[str, int] = {}
        for ann in annotators:
            lbl = ann["label"]
            label_name = lbl if isinstance(lbl, str) else LABEL_NAMES[int(lbl)]
            label_counts[label_name] = label_counts.get(label_name, 0) + 1
        majority = max(label_counts, key=lambda k: label_counts[k])
        return LABEL_MAP[majority]

    @staticmethod
    def _aggregate_rationale(rationales: list[list[int]], n_tokens: int) -> list[float]:
        """Average binary rationale masks across annotators."""
        if not rationales:
            return [0.0] * n_tokens
        valid = [r for r in rationales if len(r) == n_tokens]
        if not valid:
            return [0.0] * n_tokens
        scores = [sum(r[i] for r in valid) / len(valid) for i in range(n_tokens)]
        return scores

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        ex = self.examples[idx]
        item = {
            "input_ids": torch.tensor(ex.input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(ex.attention_mask, dtype=torch.long),
            "token_type_ids": torch.tensor(ex.token_type_ids, dtype=torch.long),
            "labels": torch.tensor(ex.label, dtype=torch.long),
            "post_id": ex.post_id,
        }
        if ex.rationale_mask is not None:
            item["rationale_mask"] = torch.tensor(ex.rationale_mask, dtype=torch.float)
        return item


def collate_fn(batch: list[dict]) -> dict:
    """Pad a batch of HateXplain examples to the same length."""
    keys = [k for k in batch[0].keys() if k != "post_id"]
    result: dict = {}

    for key in keys:
        tensors = [item[key] for item in batch]
        if tensors[0].dim() == 0:
            result[key] = torch.stack(tensors)
        else:
            max_len = max(t.size(0) for t in tensors)
            padded = []
            for t in tensors:
                pad_size = max_len - t.size(0)
                if pad_size > 0:
                    padded.append(torch.cat([t, torch.full((pad_size,), 0, dtype=t.dtype)]))
                else:
                    padded.append(t)
            result[key] = torch.stack(padded)

    result["post_ids"] = [item["post_id"] for item in batch]
    return result
