"""Benchmark dataset builder for literature synthesis evaluation.

Constructs a benchmark of ML/NLP topics with:
- Expert-written survey papers as ground truth
- Corpus of candidate papers per topic for retrieval
- Annotation guidelines for error classification
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import requests

from ..registry import register


@dataclass
class Paper:
    """Represents a paper in the benchmark."""
    paper_id: str
    title: str
    authors: list[str]
    year: int
    venue: str = ""
    abstract: str = ""
    citation_count: int = 0
    is_expert_cited: bool = False
    url: str = ""


@dataclass
class BenchmarkTopic:
    """A single benchmark topic with expert review and candidate corpus."""
    topic_id: str
    topic_name: str
    expert_survey: Optional[Paper] = None
    expert_cited_papers: list[Paper] = field(default_factory=list)
    corpus_papers: list[Paper] = field(default_factory=list)


@register("dataset", "literature_benchmark")
class LiteratureBenchmarkBuilder:
    """Build benchmark dataset from Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    FIELDS = "paperId,title,authors,year,venue,abstract,citationCount,externalIds,url"
    RATE_LIMIT_DELAY = 1.1  # seconds between requests

    # Curated list of ML/NLP survey topics with known expert surveys
    SEED_SURVEYS = [
        {"topic": "Transformer Architectures", "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776"},
        {"topic": "Retrieval-Augmented Generation", "paper_id": "46f9f7b8f88f72e12cbdb21e3311f995eb6e65c5"},
        {"topic": "Prompt Engineering", "paper_id": "f2cd4440e0ef78a6db9b56a04d6e37ef38c14e0a"},
        {"topic": "LLM Hallucination", "paper_id": "d2764e5df46ded096b33e3f3d67fbc5e66e3dae5"},
        {"topic": "In-Context Learning", "paper_id": "38d2d3023e7ac002a53d32cd8faa691c67ee1c6d"},
        {"topic": "Knowledge Graphs and LLMs", "paper_id": "26ce5a81d458b0492bdc5a9011ff01b7a5ff1a3e"},
        {"topic": "Text Summarization", "paper_id": "a27c0fc8f02ed3e14e10d14d58fbc399afa1d5a0"},
        {"topic": "Question Answering", "paper_id": "3a57a19571d416ceff75d82b7be5e20d41acc7b8"},
        {"topic": "Machine Translation", "paper_id": "bb1ee1a279c0e26b0b2ed0a0b75e7aa600e0f5d0"},
        {"topic": "Instruction Tuning", "paper_id": "d18a72751a30ba57e8d7b5a9d0e0b31c0b4a3e5e"},
        {"topic": "Evaluation of LLMs", "paper_id": "9a0b7b2da7b58e36d7f0cdd1e5eece7ef6c3fbb3"},
        {"topic": "Multimodal LLMs", "paper_id": "a93e39a2f1795914efcf27b0d8aa6d4e3c3c1f22"},
        {"topic": "LLM Alignment", "paper_id": "a7f0b2b55ae22f2c7c0de67af2ddfe15ad15fb70"},
        {"topic": "Code Generation with LLMs", "paper_id": "d7e5b45afc5e4d4cd3ff7df83c5d1f67c97a8f9e"},
        {"topic": "Efficient LLM Inference", "paper_id": "e63aa2a91e92b22e5cf2bdc9e5c35a0b7d65d9c2"},
    ]

    def __init__(self, output_dir: str = "data/benchmark"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _api_get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make rate-limited API request."""
        time.sleep(self.RATE_LIMIT_DELAY)
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            resp = requests.get(url, params=params or {}, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                print(f"  Rate limited, waiting 5s...")
                time.sleep(5)
                return self._api_get(endpoint, params)
            else:
                print(f"  API error {resp.status_code}: {endpoint}")
                return None
        except requests.RequestException as e:
            print(f"  Request failed: {e}")
            return None

    def fetch_paper(self, paper_id: str) -> Optional[Paper]:
        """Fetch a single paper's metadata."""
        data = self._api_get(f"paper/{paper_id}", {"fields": self.FIELDS})
        if not data:
            return None
        return Paper(
            paper_id=data.get("paperId", ""),
            title=data.get("title", ""),
            authors=[a.get("name", "") for a in (data.get("authors") or [])],
            year=data.get("year") or 0,
            venue=data.get("venue", ""),
            abstract=data.get("abstract", ""),
            citation_count=data.get("citationCount", 0),
            url=data.get("url", ""),
        )

    def fetch_citations(self, paper_id: str, limit: int = 200) -> list[Paper]:
        """Fetch papers cited by a given paper (its references)."""
        data = self._api_get(
            f"paper/{paper_id}/references",
            {"fields": self.FIELDS, "limit": limit},
        )
        if not data or "data" not in data:
            return []
        papers = []
        for item in data["data"]:
            cited = item.get("citedPaper", {})
            if cited and cited.get("title"):
                papers.append(Paper(
                    paper_id=cited.get("paperId", ""),
                    title=cited.get("title", ""),
                    authors=[a.get("name", "") for a in (cited.get("authors") or [])],
                    year=cited.get("year") or 0,
                    venue=cited.get("venue", ""),
                    abstract=cited.get("abstract", ""),
                    citation_count=cited.get("citationCount", 0),
                    is_expert_cited=True,
                    url=cited.get("url", ""),
                ))
        return papers

    def search_corpus(self, query: str, limit: int = 200) -> list[Paper]:
        """Search for papers on a topic to build retrieval corpus."""
        data = self._api_get(
            "paper/search",
            {"query": query, "fields": self.FIELDS, "limit": limit},
        )
        if not data or "data" not in data:
            return []
        return [
            Paper(
                paper_id=p.get("paperId", ""),
                title=p.get("title", ""),
                authors=[a.get("name", "") for a in (p.get("authors") or [])],
                year=p.get("year") or 0,
                venue=p.get("venue", ""),
                abstract=p.get("abstract", ""),
                citation_count=p.get("citationCount", 0),
            )
            for p in data["data"]
            if p.get("title")
        ]

    def build_topic(self, topic_name: str, survey_id: str) -> BenchmarkTopic:
        """Build a single benchmark topic."""
        print(f"Building topic: {topic_name}")

        # Fetch expert survey
        survey = self.fetch_paper(survey_id)
        if not survey:
            print(f"  WARNING: Could not fetch survey paper {survey_id}")
            return BenchmarkTopic(topic_id=survey_id, topic_name=topic_name)

        # Fetch papers cited by the survey
        expert_cited = self.fetch_citations(survey_id)
        print(f"  Expert survey cites {len(expert_cited)} papers")

        # Build broader corpus via search
        corpus = self.search_corpus(topic_name, limit=200)
        print(f"  Corpus search returned {len(corpus)} papers")

        # Mark corpus papers that are also expert-cited
        expert_ids = {p.paper_id for p in expert_cited}
        for p in corpus:
            if p.paper_id in expert_ids:
                p.is_expert_cited = True

        return BenchmarkTopic(
            topic_id=survey_id,
            topic_name=topic_name,
            expert_survey=survey,
            expert_cited_papers=expert_cited,
            corpus_papers=corpus,
        )

    def build_all(self, max_topics: int = 15) -> list[BenchmarkTopic]:
        """Build the full benchmark dataset."""
        topics = []
        for entry in self.SEED_SURVEYS[:max_topics]:
            topic = self.build_topic(entry["topic"], entry["paper_id"])
            topics.append(topic)

            # Save incrementally
            topic_file = self.output_dir / f"{topic.topic_id}.json"
            topic_file.write_text(json.dumps(asdict(topic), indent=2, default=str))

        # Save manifest
        manifest = {
            "num_topics": len(topics),
            "topics": [
                {
                    "topic_id": t.topic_id,
                    "topic_name": t.topic_name,
                    "num_expert_cited": len(t.expert_cited_papers),
                    "num_corpus": len(t.corpus_papers),
                }
                for t in topics
            ],
        }
        (self.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"\nBenchmark built: {len(topics)} topics")
        return topics


if __name__ == "__main__":
    builder = LiteratureBenchmarkBuilder()
    builder.build_all(max_topics=3)  # Start with 3 for testing
