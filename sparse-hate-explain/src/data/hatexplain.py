"""HateXplain dataset loader with rationale-aligned WordPiece tokenization.

Loads from the original JSON files (dataset.json + post_id_divisions.json)
from the hate-alert/HateXplain GitHub repository.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, PreTrainedTokenizerFast

LABEL_MAP: Dict[str, int] = {"hatespeech": 0, "offensive": 1, "normal": 2}
GITHUB_BASE = "https://raw.githubusercontent.com/hate-alert/HateXplain/master/Data"


def _download_if_missing(cache_dir: str) -> Tuple[str, str]:
    cache = Path(cache_dir) / "hatexplain"
    cache.mkdir(parents=True, exist_ok=True)
    dataset_path = cache / "dataset.json"
    splits_path = cache / "post_id_divisions.json"

    if not dataset_path.exists():
        r = requests.get(f"{GITHUB_BASE}/dataset.json")
        r.raise_for_status()
        dataset_path.write_bytes(r.content)

    if not splits_path.exists():
        r = requests.get(f"{GITHUB_BASE}/post_id_divisions.json")
        r.raise_for_status()
        splits_path.write_bytes(r.content)

    return str(dataset_path), str(splits_path)


def _majority_vote_label(annotators: List[Dict[str, Any]]) -> int:
    counts: Dict[str, int] = {}
    for ann in annotators:
        label = ann["label"]
        counts[label] = counts.get(label, 0) + 1
    return LABEL_MAP[max(counts, key=lambda k: counts[k])]


def _majority_vote_rationale(rationales: List[List[int]], n_tokens: int) -> List[int]:
    if not rationales:
        return [0] * n_tokens
    result = []
    for i in range(n_tokens):
        votes = sum(r[i] for r in rationales if i < len(r))
        result.append(1 if votes >= 2 else 0)
    return result


def _align_rationale_to_subwords(
    tokens: List[str],
    rationale: List[int],
    tokenizer: PreTrainedTokenizerFast,
    max_length: int,
) -> List[int]:
    encoding = tokenizer(
        tokens, is_split_into_words=True,
        max_length=max_length, padding="max_length", truncation=True,
    )
    word_ids = encoding.word_ids()
    return [
        rationale[wid] if wid is not None and wid < len(rationale) else 0
        for wid in word_ids
    ]


class HateXplainDataset(Dataset):
    def __init__(
        self,
        split: str,
        tokenizer: PreTrainedTokenizerFast,
        max_length: int = 128,
        cache_dir: str = "data/cache",
    ) -> None:
        dataset_path, splits_path = _download_if_missing(cache_dir)

        with open(dataset_path) as f:
            all_data = json.load(f)
        with open(splits_path) as f:
            split_ids = json.load(f)

        split_key = "val" if split == "validation" else split
        ids = split_ids[split_key]

        self.samples: List[Dict[str, Any]] = []
        for post_id in ids:
            if post_id in all_data:
                entry = all_data[post_id]
                tokens = entry["post_tokens"]
                label = _majority_vote_label(entry["annotators"])
                rationale = _majority_vote_rationale(entry.get("rationales", []), len(tokens))
                self.samples.append({
                    "tokens": tokens,
                    "label": label,
                    "rationale": rationale,
                })

        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]
        tokens = sample["tokens"]
        encoding = self.tokenizer(
            tokens, is_split_into_words=True,
            max_length=self.max_length, padding="max_length", truncation=True,
            return_tensors="pt",
        )
        aligned_rationale = _align_rationale_to_subwords(
            tokens, sample["rationale"], self.tokenizer, self.max_length,
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(sample["label"], dtype=torch.long),
            "rationale_mask": torch.tensor(aligned_rationale, dtype=torch.float),
        }


def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "rationale_mask": torch.stack([b["rationale_mask"] for b in batch]),
    }


def build_dataloaders(cfg: Any) -> Tuple[DataLoader, DataLoader, DataLoader]:
    max_length: int = getattr(cfg.data, "max_length", 128)
    batch_size: int = getattr(cfg.data, "batch_size", 16)
    num_workers: int = getattr(cfg.data, "num_workers", 4)
    model_name: str = getattr(cfg.data, "model_name", "bert-base-uncased")
    cache_dir: str = getattr(cfg.data, "cache_dir", None) or "data/cache"

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    train_ds = HateXplainDataset("train", tokenizer, max_length, cache_dir)
    val_ds = HateXplainDataset("validation", tokenizer, max_length, cache_dir)
    test_ds = HateXplainDataset("test", tokenizer, max_length, cache_dir)

    shared = {"collate_fn": collate_fn, "num_workers": num_workers, "pin_memory": True}

    return (
        DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True, **shared),
        DataLoader(val_ds, batch_size=batch_size, shuffle=False, **shared),
        DataLoader(test_ds, batch_size=batch_size, shuffle=False, **shared),
    )
