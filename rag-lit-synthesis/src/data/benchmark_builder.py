"""Benchmark dataset builder for RAG literature synthesis evaluation.

Downloads papers from Semantic Scholar API for 5 NLP/ML topics.
Each topic has 30-50 candidate papers and 1 survey as ground truth.
"""

import json
import time
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
PAPER_FIELDS = "paperId,title,authors,year,venue,abstract,citationCount,url"

# 5 well-defined NLP/ML topics with known high-citation surveys
SEED_TOPICS = [
    {
        "topic_id": "attention_mechanisms",
        "topic_name": "Attention Mechanisms in Neural Networks",
        "search_query": "attention mechanism transformer neural network",
        "survey_query": "survey attention mechanism transformer",
    },
    {
        "topic_id": "prompt_engineering",
        "topic_name": "Prompt Engineering for Large Language Models",
        "search_query": "prompt engineering large language models",
        "survey_query": "survey prompt engineering LLM",
    },
    {
        "topic_id": "rlhf",
        "topic_name": "Reinforcement Learning from Human Feedback",
        "search_query": "reinforcement learning human feedback RLHF alignment",
        "survey_query": "survey reinforcement learning human feedback",
    },
    {
        "topic_id": "diffusion_models",
        "topic_name": "Diffusion Models for Generative AI",
        "search_query": "diffusion models denoising generative",
        "survey_query": "survey diffusion models generative",
    },
    {
        "topic_id": "in_context_learning",
        "topic_name": "In-Context Learning in Large Language Models",
        "search_query": "in-context learning few-shot large language models",
        "survey_query": "survey in-context learning",
    },
]


@dataclass
class Paper:
    """A paper in the benchmark."""
    paper_id: str
    title: str
    authors: list[str]
    year: int
    venue: str = ""
    abstract: str = ""
    citation_count: int = 0
    url: str = ""
    is_expert_cited: bool = False


@dataclass
class BenchmarkTopic:
    """A benchmark topic with survey ground truth and candidate corpus."""
    topic_id: str
    topic_name: str
    survey: Optional[Paper] = None
    survey_cited_ids: list[str] = field(default_factory=list)
    corpus: list[Paper] = field(default_factory=list)


def _api_get(endpoint: str, params: dict | None = None,
             max_retries: int = 5) -> Optional[dict]:
    """Rate-limited Semantic Scholar API request with exponential backoff."""
    url = f"{SEMANTIC_SCHOLAR_API}/{endpoint}"
    for attempt in range(max_retries):
        try:
            time.sleep(1.2)  # rate limit: ~1 req/sec for public API
            resp = requests.get(url, params=params or {}, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                logger.warning(f"API {resp.status_code} for {endpoint}")
                if resp.status_code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                return None
        except requests.RequestException as e:
            logger.warning(f"Request error: {e}, retrying...")
            time.sleep(2 ** attempt)
    logger.error(f"Failed after {max_retries} retries: {endpoint}")
    return None


def fetch_paper(paper_id: str) -> Optional[Paper]:
    """Fetch a single paper by ID."""
    data = _api_get(f"paper/{paper_id}", {"fields": PAPER_FIELDS})
    if not data or not data.get("title"):
        return None
    return Paper(
        paper_id=data.get("paperId", ""),
        title=data.get("title", ""),
        authors=[a.get("name", "") for a in (data.get("authors") or [])],
        year=data.get("year") or 0,
        venue=data.get("venue", ""),
        abstract=data.get("abstract", "") or "",
        citation_count=data.get("citationCount", 0),
        url=data.get("url", ""),
    )


def search_papers(query: str, limit: int = 50, year_range: str = "2019-2026") -> list[Paper]:
    """Search Semantic Scholar for papers matching a query."""
    data = _api_get("paper/search", {
        "query": query,
        "fields": PAPER_FIELDS,
        "limit": min(limit, 100),
        "year": year_range,
    })
    if not data or "data" not in data:
        return []
    papers = []
    for p in data["data"]:
        if p.get("title") and p.get("abstract"):
            papers.append(Paper(
                paper_id=p.get("paperId", ""),
                title=p.get("title", ""),
                authors=[a.get("name", "") for a in (p.get("authors") or [])],
                year=p.get("year") or 0,
                venue=p.get("venue", ""),
                abstract=p.get("abstract", "") or "",
                citation_count=p.get("citationCount", 0),
                url=p.get("url", ""),
            ))
    return papers


def find_best_survey(query: str) -> Optional[Paper]:
    """Find the most-cited survey paper for a topic."""
    papers = search_papers(query, limit=20, year_range="2020-2026")
    if not papers:
        return None
    # Pick the most cited one
    papers.sort(key=lambda p: p.citation_count, reverse=True)
    return papers[0]


def fetch_survey_references(paper_id: str, limit: int = 200) -> list[str]:
    """Get paper IDs cited by the survey."""
    data = _api_get(f"paper/{paper_id}/references", {
        "fields": "paperId",
        "limit": limit,
    })
    if not data or "data" not in data:
        return []
    ids = []
    for item in data["data"]:
        cited = item.get("citedPaper", {})
        if cited and cited.get("paperId"):
            ids.append(cited["paperId"])
    return ids


def build_topic(seed: dict, min_papers: int = 30) -> BenchmarkTopic:
    """Build a single benchmark topic."""
    topic_id = seed["topic_id"]
    topic_name = seed["topic_name"]
    logger.info(f"Building topic: {topic_name}")

    # Find best survey
    survey = find_best_survey(seed["survey_query"])
    if not survey:
        logger.warning(f"No survey found for {topic_name}, using search fallback")
        survey = find_best_survey(seed["search_query"])

    survey_cited_ids = []
    if survey:
        logger.info(f"  Survey: {survey.title} (citations: {survey.citation_count})")
        survey_cited_ids = fetch_survey_references(survey.paper_id)
        logger.info(f"  Survey cites {len(survey_cited_ids)} papers")

    # Build corpus
    corpus = search_papers(seed["search_query"], limit=50)
    logger.info(f"  Corpus: {len(corpus)} papers")

    # Mark papers cited by the survey
    cited_set = set(survey_cited_ids)
    for p in corpus:
        if p.paper_id in cited_set:
            p.is_expert_cited = True

    # If too few papers, try a broader search
    if len(corpus) < min_papers:
        extra = search_papers(topic_name, limit=30)
        existing_ids = {p.paper_id for p in corpus}
        for p in extra:
            if p.paper_id not in existing_ids:
                if p.paper_id in cited_set:
                    p.is_expert_cited = True
                corpus.append(p)

    return BenchmarkTopic(
        topic_id=topic_id,
        topic_name=topic_name,
        survey=survey,
        survey_cited_ids=survey_cited_ids,
        corpus=corpus,
    )


def build_benchmark(output_dir: str = "data/benchmark") -> list[BenchmarkTopic]:
    """Build the full 5-topic benchmark."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    topics = []
    for seed in SEED_TOPICS:
        topic = build_topic(seed)
        topics.append(topic)

        # Save incrementally
        topic_file = out / f"{topic.topic_id}.json"
        topic_file.write_text(json.dumps(asdict(topic), indent=2, default=str))
        logger.info(f"  Saved {topic_file}")

    # Save manifest
    manifest = {
        "num_topics": len(topics),
        "topics": [
            {
                "topic_id": t.topic_id,
                "topic_name": t.topic_name,
                "num_corpus": len(t.corpus),
                "num_survey_cited": len(t.survey_cited_ids),
                "survey_title": t.survey.title if t.survey else None,
            }
            for t in topics
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    logger.info(f"Benchmark complete: {len(topics)} topics")
    return topics


def load_benchmark(benchmark_dir: str = "data/benchmark") -> list[BenchmarkTopic]:
    """Load a previously built benchmark from disk."""
    bdir = Path(benchmark_dir)
    manifest_file = bdir / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"No benchmark at {bdir}. Run build_benchmark() first.")

    manifest = json.loads(manifest_file.read_text())
    topics = []
    for entry in manifest["topics"]:
        topic_file = bdir / f"{entry['topic_id']}.json"
        data = json.loads(topic_file.read_text())

        survey = None
        if data.get("survey"):
            s = data["survey"]
            survey = Paper(**{k: v for k, v in s.items() if k in Paper.__dataclass_fields__})

        corpus = []
        for p in data.get("corpus", []):
            corpus.append(Paper(**{k: v for k, v in p.items() if k in Paper.__dataclass_fields__}))

        topics.append(BenchmarkTopic(
            topic_id=data["topic_id"],
            topic_name=data["topic_name"],
            survey=survey,
            survey_cited_ids=data.get("survey_cited_ids", []),
            corpus=corpus,
        ))
    return topics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    build_benchmark()
