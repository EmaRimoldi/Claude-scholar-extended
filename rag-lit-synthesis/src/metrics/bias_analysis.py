"""Bias analysis: recency bias and popularity bias in citations."""

from dataclasses import dataclass

import numpy as np
from scipy import stats

from ..registry import register


@dataclass
class BiasResult:
    """Bias analysis result."""
    recency_correlation: float   # Spearman rho: year vs inclusion
    recency_pvalue: float
    popularity_correlation: float  # Spearman rho: citation_count vs inclusion
    popularity_pvalue: float
    mean_year_cited: float
    mean_year_uncited: float
    mean_citations_cited: float
    mean_citations_uncited: float


@register("metric", "bias_analysis")
def compute_bias(papers: list[dict], cited_ids: set[str]) -> BiasResult:
    """Analyze recency and popularity bias in RAG citations.

    papers: list of dicts with keys: paper_id, year, citation_count
    cited_ids: set of paper_ids that were cited in the generated review
    """
    years = np.array([p["year"] for p in papers if p["year"]])
    cit_counts = np.array([p["citation_count"] for p in papers if p["year"]])
    included = np.array([1 if p["paper_id"] in cited_ids else 0 for p in papers if p["year"]])

    if len(years) < 5:
        return BiasResult(0, 1, 0, 1, 0, 0, 0, 0)

    rec_rho, rec_p = stats.spearmanr(years, included)
    pop_rho, pop_p = stats.spearmanr(cit_counts, included)

    cited_mask = included == 1
    uncited_mask = included == 0

    return BiasResult(
        recency_correlation=float(rec_rho),
        recency_pvalue=float(rec_p),
        popularity_correlation=float(pop_rho),
        popularity_pvalue=float(pop_p),
        mean_year_cited=float(years[cited_mask].mean()) if cited_mask.any() else 0,
        mean_year_uncited=float(years[uncited_mask].mean()) if uncited_mask.any() else 0,
        mean_citations_cited=float(cit_counts[cited_mask].mean()) if cited_mask.any() else 0,
        mean_citations_uncited=float(cit_counts[uncited_mask].mean()) if uncited_mask.any() else 0,
    )
