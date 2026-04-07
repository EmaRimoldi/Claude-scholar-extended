"""Download and cache HateXplain dataset.

HateXplain is hosted on GitHub (Mathew et al., AAAI 2021).
This script downloads and preprocesses the raw JSON into a split-ready format.

Dataset source: https://github.com/punyajoy/HateXplain
License: CC BY 4.0

Usage:
    python scripts/download_data.py --output-dir data/hatexplain
"""
import argparse
import json
import logging
import os
import random
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

HATEXPLAIN_DATASET_URL = (
    "https://raw.githubusercontent.com/punyajoy/HateXplain/master/Data/dataset.json"
)
HATEXPLAIN_SPLIT_URL = (
    "https://raw.githubusercontent.com/punyajoy/HateXplain/master/Data/post_id_divisions.json"
)

LABEL_MAP = {"hatespeech": 2, "offensive": 1, "normal": 0}


def download_json(url: str, cache_path: str) -> dict:
    """Download JSON file from URL, caching locally.

    Args:
        url: URL to fetch.
        cache_path: Local path to cache the download.

    Returns:
        Parsed JSON dict.
    """
    if os.path.exists(cache_path):
        logger.info(f"Using cached file: {cache_path}")
        with open(cache_path) as f:
            return json.load(f)

    import urllib.request
    logger.info(f"Downloading: {url}")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    urllib.request.urlretrieve(url, cache_path)
    with open(cache_path) as f:
        return json.load(f)


def get_majority_label(labels: list[str]) -> str:
    """Compute majority-vote label from list of annotator labels.

    Args:
        labels: List of label strings from 3 annotators.

    Returns:
        Majority label string.
    """
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return max(counts, key=lambda k: counts[k])


def process_record(post_id: str, record: dict[str, Any]) -> dict[str, Any]:
    """Convert raw HateXplain record to processed format.

    Args:
        post_id: Post identifier string.
        record: Raw record dict from dataset.json.

    Returns:
        Processed dict with post_id, text, label, rationales.
    """
    post_tokens = record.get("post_tokens", [])
    text = " ".join(post_tokens)

    # Majority-vote label
    annotations = record.get("annotators", [])
    label_strs = [ann.get("label", "normal") for ann in annotations]
    label_str = get_majority_label(label_strs)
    label = LABEL_MAP.get(label_str, 0)

    # Per-annotator rationale masks
    rationales = []
    for ann in annotations:
        rat = ann.get("rationale", [])
        if len(rat) == len(post_tokens):
            rationales.append([int(r) for r in rat])
        else:
            # Pad or truncate to match token count
            rat_padded = (rat + [0] * len(post_tokens))[: len(post_tokens)]
            rationales.append([int(r) for r in rat_padded])

    return {
        "id": post_id,
        "post_tokens": post_tokens,
        "text": text,
        "label": label_str,
        "label_id": label,
        "rationales": rationales,
    }


def save_split(
    records: list[dict[str, Any]], output_path: str
) -> None:
    """Save processed records to JSONL file.

    Args:
        records: List of processed record dicts.
        output_path: Path to output JSONL file.
    """
    with open(output_path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    logger.info(f"Saved {len(records)} records to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download HateXplain dataset")
    parser.add_argument("--output-dir", default="data/hatexplain", help="Output directory")
    parser.add_argument("--cache-dir", default="data/.cache", help="Download cache directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Download raw data
    dataset_cache = os.path.join(args.cache_dir, "dataset.json")
    splits_cache = os.path.join(args.cache_dir, "post_id_divisions.json")

    dataset = download_json(HATEXPLAIN_DATASET_URL, dataset_cache)
    splits = download_json(HATEXPLAIN_SPLIT_URL, splits_cache)

    logger.info(f"Total posts: {len(dataset)}")

    # Process all records
    processed = {
        post_id: process_record(post_id, record)
        for post_id, record in dataset.items()
    }

    # Use official train/val/test splits
    for split_name in ["train", "val", "test"]:
        post_ids = splits.get(split_name, [])
        records = [processed[pid] for pid in post_ids if pid in processed]
        output_name = "validation" if split_name == "val" else split_name
        output_path = os.path.join(args.output_dir, f"{output_name}.jsonl")
        save_split(records, output_path)

    # Print statistics
    for split_name in ["train", "validation", "test"]:
        path = os.path.join(args.output_dir, f"{split_name}.jsonl")
        if os.path.exists(path):
            with open(path) as f:
                records = [json.loads(line) for line in f]
            label_counts: dict[str, int] = {}
            for r in records:
                label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1
            logger.info(f"{split_name}: {len(records)} posts, labels={label_counts}")

    logger.info("HateXplain download complete.")


if __name__ == "__main__":
    main()
