"""Basic tests for evaluation metrics."""

from src.metrics.citation_metrics import (
    citation_precision,
    citation_recall,
    hallucination_count,
    key_paper_recall,
    compute_citation_metrics,
    extract_citations,
)
from src.metrics.faithfulness import compute_faithfulness, split_into_claims


class TestCitationMetrics:
    def test_precision_all_correct(self):
        assert citation_precision(["a", "b"], {"a", "b"}, {"a", "b"}) == 1.0

    def test_precision_none_correct(self):
        assert citation_precision(["a", "b"], {"c", "d"}, {"a", "b"}) == 0.0

    def test_precision_partial(self):
        assert citation_precision(["a", "b", "c"], {"a", "b"}, {"a", "b", "c"}) == 2 / 3

    def test_precision_empty(self):
        assert citation_precision([], {"a"}, {"a"}) == 0.0

    def test_recall_all_found(self):
        assert citation_recall(["a", "b"], {"a", "b"}) == 1.0

    def test_recall_none_found(self):
        assert citation_recall(["c"], {"a", "b"}) == 0.0

    def test_recall_empty_relevant(self):
        assert citation_recall(["a"], set()) == 0.0

    def test_hallucination_count(self):
        assert hallucination_count(["a", "b", "c"], {"a", "b"}) == 1
        assert hallucination_count(["a", "b"], {"a", "b"}) == 0

    def test_key_paper_recall(self):
        assert key_paper_recall(["a", "b"], {"a", "b", "c"}) == 2 / 3

    def test_compute_citation_metrics(self):
        result = compute_citation_metrics(["a", "b", "x"], {"a", "b", "c"}, {"a", "b", "c"})
        assert result.precision == 2 / 3
        assert result.recall == 2 / 3
        assert result.hallucinated_count == 1
        assert result.total_citations == 3

    def test_extract_citations(self):
        text = "As shown by [Vaswani, 2017] and [Lewis et al., 2020], RAG works well."
        cites = extract_citations(text)
        assert "Vaswani, 2017" in cites
        assert "Lewis et al., 2020" in cites


class TestFaithfulness:
    def test_fully_supported(self):
        text = "Retrieval augmented generation combines retrieval with generation for better results."
        passages = ["Retrieval augmented generation combines retrieval with generation for better results."]
        result = compute_faithfulness(text, passages)
        assert result.score == 1.0

    def test_no_passages(self):
        text = "This is a sufficiently long claim that should not be supported by empty passages at all."
        result = compute_faithfulness(text, [])
        assert result.hallucination_rate == 1.0

    def test_split_into_claims(self):
        text = "This is the first claim about something important. This is the second claim with details."
        claims = split_into_claims(text)
        assert len(claims) == 2
