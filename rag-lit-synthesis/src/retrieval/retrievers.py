"""Retrieval components: BM25 (sparse) and Dense (sentence-transformers).

Each retriever indexes paper abstracts and retrieves top-k for a query.
"""

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RetrievedPaper:
    """A retrieved paper with relevance score."""
    paper_id: str
    title: str
    abstract: str
    score: float


class BM25Retriever:
    """Sparse retrieval using BM25 over paper abstracts."""

    def __init__(self, papers: list[dict]):
        """
        Args:
            papers: list of dicts with keys: paper_id, title, abstract
        """
        from rank_bm25 import BM25Okapi

        self.papers = [p for p in papers if p.get("abstract")]
        tokenized = [p["abstract"].lower().split() for p in self.papers]
        self.bm25 = BM25Okapi(tokenized)
        logger.info(f"BM25 index: {len(self.papers)} papers")

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedPaper]:
        scores = self.bm25.get_scores(query.lower().split())
        top_idx = np.argsort(scores)[::-1][:top_k]
        results = []
        for i in top_idx:
            if scores[i] > 0:
                p = self.papers[i]
                results.append(RetrievedPaper(
                    paper_id=p["paper_id"],
                    title=p["title"],
                    abstract=p["abstract"],
                    score=float(scores[i]),
                ))
        return results


class DenseRetriever:
    """Dense retrieval using sentence-transformers + cosine similarity."""

    def __init__(self, papers: list[dict], model_name: str = "all-MiniLM-L6-v2"):
        """
        Args:
            papers: list of dicts with keys: paper_id, title, abstract
            model_name: sentence-transformers model name
        """
        from sentence_transformers import SentenceTransformer

        self.papers = [p for p in papers if p.get("abstract")]
        self.model = SentenceTransformer(model_name)

        texts = [f"{p['title']}. {p['abstract']}" for p in self.papers]
        logger.info(f"Encoding {len(texts)} papers with {model_name}...")
        self.embeddings = self.model.encode(
            texts, show_progress_bar=True, normalize_embeddings=True,
            batch_size=32,
        )
        logger.info(f"Dense index: {len(self.papers)} papers, dim={self.embeddings.shape[1]}")

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedPaper]:
        q_emb = self.model.encode([query], normalize_embeddings=True)
        # Cosine similarity (embeddings are normalized)
        scores = (self.embeddings @ q_emb.T).flatten()
        top_idx = np.argsort(scores)[::-1][:top_k]
        results = []
        for i in top_idx:
            p = self.papers[i]
            results.append(RetrievedPaper(
                paper_id=p["paper_id"],
                title=p["title"],
                abstract=p["abstract"],
                score=float(scores[i]),
            ))
        return results
