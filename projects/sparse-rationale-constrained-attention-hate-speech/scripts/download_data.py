"""Download HateXplain dataset and bert-base-uncased model to HuggingFace cache.

Run on cluster before submitting SLURM jobs:
    python scripts/download_data.py [--cache_dir /path/to/cache]

This ensures all workers use cached files and do not trigger concurrent downloads.
"""
from __future__ import annotations

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache_dir", default=None, help="HuggingFace cache directory.")
    args = parser.parse_args()

    kwargs = {}
    if args.cache_dir:
        import os
        os.environ["HF_HOME"] = args.cache_dir

    logger.info("Downloading HateXplain dataset (all splits)...")
    from datasets import load_dataset
    for split in ["train", "validation", "test"]:
        ds = load_dataset("Hate-speech-CNERG/hatexplain", split=split, trust_remote_code=True, **kwargs)
        logger.info(f"  {split}: {len(ds)} examples")

    logger.info("Downloading bert-base-uncased tokenizer and model weights...")
    from transformers import AutoConfig, AutoTokenizer, BertModel
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    config = AutoConfig.from_pretrained("bert-base-uncased")
    model = BertModel.from_pretrained("bert-base-uncased")
    logger.info(f"  BERT params: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")

    logger.info("All downloads complete. Ready for cluster jobs.")


if __name__ == "__main__":
    main()
