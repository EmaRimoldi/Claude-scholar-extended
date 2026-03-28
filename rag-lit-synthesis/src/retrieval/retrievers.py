"""Retrieval components: BM25, Dense, and Hybrid retrievers."""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..registry import register


@dataclass
class RetrievedPassage:
    """A retrieved passage with score."""
    paper_id: str
    text: str
    score: float
    title: str = ""
    chunk_idx: int = 0


@register("retriever", "bm25")
class BM25Retriever:
    """Sparse retrieval using BM25."""

    def __init__(self, corpus: list[dict], chunk_size: int = 512):
        from rank_bm25 import BM25Okapi
        self.corpus = corpus
        self.chunk_size = chunk_size
        self.chunks, self.chunk_meta = self._build_chunks()
        tokenized = [c.split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    def _build_chunks(self):
        chunks, meta = [], []
        for doc in self.corpus:
            text = doc.get("abstract", "") or doc.get("text", "")
            words = text.split()
            for i in range(0, max(1, len(words)), self.chunk_size):
                chunk = " ".join(words[i : i + self.chunk_size])
                chunks.append(chunk)
                meta.append({"paper_id": doc["paper_id"], "title": doc.get("title", ""), "chunk_idx": i})
        return chunks, meta

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedPassage]:
        scores = self.bm25.get_scores(query.split())
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            RetrievedPassage(
                paper_id=self.chunk_meta[i]["paper_id"],
                text=self.chunks[i],
                score=float(scores[i]),
                title=self.chunk_meta[i]["title"],
                chunk_idx=self.chunk_meta[i]["chunk_idx"],
            )
            for i in top_indices
            if scores[i] > 0
        ]


@register("retriever", "dense")
class DenseRetriever:
    """Dense passage retrieval using sentence-transformers + FAISS."""

    def __init__(self, corpus: list[dict], model_name: str = "BAAI/bge-base-en-v1.5", chunk_size: int = 512):
        from sentence_transformers import SentenceTransformer
        import faiss

        self.corpus = corpus
        self.chunk_size = chunk_size
        self.model = SentenceTransformer(model_name)

        self.chunks, self.chunk_meta = self._build_chunks()
        embeddings = self.model.encode(self.chunks, show_progress_bar=True, normalize_embeddings=True)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))

    def _build_chunks(self):
        chunks, meta = [], []
        for doc in self.corpus:
            text = doc.get("abstract", "") or doc.get("text", "")
            words = text.split()
            for i in range(0, max(1, len(words)), self.chunk_size):
                chunk = " ".join(words[i : i + self.chunk_size])
                chunks.append(chunk)
                meta.append({"paper_id": doc["paper_id"], "title": doc.get("title", ""), "chunk_idx": i})
        return chunks, meta

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedPassage]:
        q_emb = self.model.encode([query], normalize_embeddings=True).astype(np.float32)
        scores, indices = self.index.search(q_emb, top_k)
        return [
            RetrievedPassage(
                paper_id=self.chunk_meta[idx]["paper_id"],
                text=self.chunks[idx],
                score=float(scores[0][j]),
                title=self.chunk_meta[idx]["title"],
                chunk_idx=self.chunk_meta[idx]["chunk_idx"],
            )
            for j, idx in enumerate(indices[0])
            if idx >= 0
        ]


@register("retriever", "hybrid")
class HybridRetriever:
    """Hybrid retrieval: BM25 candidates re-ranked by dense model."""

    def __init__(self, corpus: list[dict], model_name: str = "BAAI/bge-base-en-v1.5", chunk_size: int = 512):
        self.bm25 = BM25Retriever(corpus, chunk_size)
        self.dense = DenseRetriever(corpus, model_name, chunk_size)

    def retrieve(self, query: str, top_k: int = 10, bm25_candidates: int = 50) -> list[RetrievedPassage]:
        bm25_results = self.bm25.retrieve(query, top_k=bm25_candidates)
        dense_results = self.dense.retrieve(query, top_k=top_k)

        # Reciprocal rank fusion
        scores: dict[str, float] = {}
        paper_map: dict[str, RetrievedPassage] = {}
        k = 60  # RRF constant

        for rank, r in enumerate(bm25_results):
            key = f"{r.paper_id}_{r.chunk_idx}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            paper_map[key] = r

        for rank, r in enumerate(dense_results):
            key = f"{r.paper_id}_{r.chunk_idx}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            if key not in paper_map:
                paper_map[key] = r

        sorted_keys = sorted(scores, key=scores.get, reverse=True)[:top_k]
        return [
            RetrievedPassage(
                paper_id=paper_map[key].paper_id,
                text=paper_map[key].text,
                score=scores[key],
                title=paper_map[key].title,
                chunk_idx=paper_map[key].chunk_idx,
            )
            for key in sorted_keys
        ]
