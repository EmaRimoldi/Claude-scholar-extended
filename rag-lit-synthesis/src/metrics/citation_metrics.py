"""Citation accuracy and coverage metrics."""

import re
from dataclasses import dataclass
from typing import Optional

from ..registry import register


@dataclass
class CitationMetrics:
    """Results of citation evaluation."""
    precision: float  # correct citations / total citations
    recall: float     # cited relevant / total relevant
    f1: float
    hallucinated_count: int  # citations to non-existent papers
    attribution_errors: int  # correct paper, wrong claim
    total_citations: int


def extract_citations(text: str) -> list[str]:
    """Extract [Author, Year] citations from generated text."""
    pattern = r'\[([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?(?:,\s*\d{4}))\]'
    return re.findall(pattern, text)


def extract_citation_paper_ids(text: str, paper_lookup: dict[str, str]) -> list[str]:
    """Map extracted citations to paper IDs using a lookup table.

    paper_lookup: {author_year_string: paper_id}
    """
    citations = extract_citations(text)
    return [paper_lookup[c] for c in citations if c in paper_lookup]


@register("metric", "citation_precision")
def citation_precision(cited_ids: list[str], relevant_ids: set[str],
                       existing_ids: set[str]) -> float:
    """Fraction of citations that are both real and relevant."""
    if not cited_ids:
        return 0.0
    correct = sum(1 for cid in cited_ids if cid in relevant_ids and cid in existing_ids)
    return correct / len(cited_ids)


@register("metric", "citation_recall")
def citation_recall(cited_ids: list[str], relevant_ids: set[str]) -> float:
    """Fraction of relevant papers that were cited."""
    if not relevant_ids:
        return 0.0
    found = sum(1 for rid in relevant_ids if rid in set(cited_ids))
    return found / len(relevant_ids)


@register("metric", "hallucination_count")
def hallucination_count(cited_ids: list[str], existing_ids: set[str]) -> int:
    """Count citations to non-existent papers."""
    return sum(1 for cid in cited_ids if cid not in existing_ids)


@register("metric", "key_paper_recall")
def key_paper_recall(cited_ids: list[str], expert_cited_ids: set[str]) -> float:
    """Fraction of expert-cited key papers that appear in generated review."""
    if not expert_cited_ids:
        return 0.0
    found = sum(1 for eid in expert_cited_ids if eid in set(cited_ids))
    return found / len(expert_cited_ids)


def compute_citation_metrics(cited_ids: list[str], relevant_ids: set[str],
                              existing_ids: set[str]) -> CitationMetrics:
    """Compute all citation metrics."""
    prec = citation_precision(cited_ids, relevant_ids, existing_ids)
    rec = citation_recall(cited_ids, relevant_ids)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    hall = hallucination_count(cited_ids, existing_ids)
    attr_err = sum(1 for cid in cited_ids if cid in existing_ids and cid not in relevant_ids)

    return CitationMetrics(
        precision=prec,
        recall=rec,
        f1=f1,
        hallucinated_count=hall,
        attribution_errors=attr_err,
        total_citations=len(cited_ids),
    )
