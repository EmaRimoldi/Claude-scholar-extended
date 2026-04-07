"""Load HateXplain from preprocessed JSONL files (produced by scripts/download_data.py)."""
import json
import logging
import os
from typing import Optional

from .dataset import HateXplainExample, build_majority_vote_rationale, LABEL2ID

logger = logging.getLogger(__name__)


def load_jsonl(path: str) -> list[HateXplainExample]:
    """Load HateXplain examples from a JSONL split file.

    Args:
        path: Path to .jsonl file (train.jsonl / validation.jsonl / test.jsonl).

    Returns:
        List of HateXplainExample objects.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset file not found: {path}\n"
            "Run: python scripts/download_data.py --output-dir data/hatexplain"
        )

    examples: list[HateXplainExample] = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line.strip())
            label_str = rec.get("label", "normal")
            label = LABEL2ID.get(label_str, 0)

            rationale_binary: Optional[list[int]] = None
            rationale_normalized: Optional[list[float]] = None

            raw_rationales = rec.get("rationales", [])
            if raw_rationales:
                rationale_binary, rationale_normalized = build_majority_vote_rationale(
                    raw_rationales
                )

            examples.append(
                HateXplainExample(
                    post_id=str(rec.get("id", "")),
                    text=rec.get("text", " ".join(rec.get("post_tokens", []))),
                    label=label,
                    rationale_binary=rationale_binary,
                    rationale_normalized=rationale_normalized,
                )
            )

    logger.info(f"Loaded {len(examples)} examples from {path}")
    return examples
