"""Faithfulness and factual consistency metrics."""

import re
from dataclasses import dataclass

from ..registry import register


@dataclass
class FaithfulnessResult:
    """Faithfulness evaluation result."""
    score: float           # fraction of claims supported
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    hallucination_rate: float


def split_into_claims(text: str) -> list[str]:
    """Split generated text into individual claims (sentences)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    claims = [s.strip() for s in sentences if len(s.strip()) > 20]
    return claims


def claim_is_supported(claim: str, passages: list[str], threshold: float = 0.3) -> bool:
    """Check if a claim is supported by any retrieved passage.

    Uses simple token overlap as a lightweight proxy.
    For production, use NLI model or LLM-as-judge.
    """
    claim_tokens = set(claim.lower().split())
    for passage in passages:
        passage_tokens = set(passage.lower().split())
        if not claim_tokens:
            return True
        overlap = len(claim_tokens & passage_tokens) / len(claim_tokens)
        if overlap >= threshold:
            return True
    return False


@register("metric", "faithfulness")
def compute_faithfulness(generated_text: str, retrieved_passages: list[str],
                          threshold: float = 0.3) -> FaithfulnessResult:
    """Compute faithfulness score for generated text against retrieved passages."""
    claims = split_into_claims(generated_text)
    if not claims:
        return FaithfulnessResult(score=1.0, total_claims=0, supported_claims=0,
                                   unsupported_claims=0, hallucination_rate=0.0)

    supported = sum(1 for c in claims if claim_is_supported(c, retrieved_passages, threshold))
    unsupported = len(claims) - supported

    return FaithfulnessResult(
        score=supported / len(claims),
        total_claims=len(claims),
        supported_claims=supported,
        unsupported_claims=unsupported,
        hallucination_rate=unsupported / len(claims),
    )
