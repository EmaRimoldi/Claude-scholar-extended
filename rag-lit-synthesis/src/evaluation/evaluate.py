"""Evaluation metrics for RAG literature synthesis.

Computes:
  - Citation precision: % of cited papers that are in the corpus
  - Citation recall: % of corpus papers that were cited
  - ROUGE-L: against survey ground truth abstract
  - BERTScore: semantic similarity with survey ground truth
  - Retrieval quality: Precision@10 and NDCG@10 vs survey-cited papers
"""

import logging
import math
from dataclasses import dataclass, asdict

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """All metrics for a single (topic, condition) run."""
    topic_id: str
    condition: str
    citation_precision: float
    citation_recall: float
    rouge_l: float
    bertscore_f1: float
    retrieval_precision_at_10: float
    retrieval_ndcg_at_10: float
    num_cited: int
    num_corpus: int
    generation_method: str
    model_name: str


def citation_precision(cited_ids: list[str], corpus_ids: set[str]) -> float:
    """Fraction of cited papers that exist in the corpus."""
    if not cited_ids:
        return 0.0
    return sum(1 for cid in cited_ids if cid in corpus_ids) / len(cited_ids)


def citation_recall(cited_ids: list[str], corpus_ids: set[str]) -> float:
    """Fraction of corpus papers that were cited in the summary."""
    if not corpus_ids:
        return 0.0
    return sum(1 for cid in corpus_ids if cid in set(cited_ids)) / len(corpus_ids)


def compute_rouge_l(generated: str, reference: str) -> float:
    """Compute ROUGE-L F1 score."""
    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference, generated)
        return scores["rougeL"].fmeasure
    except Exception as e:
        logger.warning(f"ROUGE-L computation failed: {e}")
        return 0.0


def compute_bertscore(generated: str, reference: str) -> float:
    """Compute BERTScore F1. Uses a lighter model for speed."""
    try:
        from bert_score import score as bert_score_fn
        P, R, F1 = bert_score_fn(
            [generated], [reference],
            model_type="microsoft/deberta-base-mnli",
            verbose=False,
            device="cuda",
        )
        return F1[0].item()
    except Exception as e:
        logger.warning(f"BERTScore computation failed: {e}, trying CPU...")
        try:
            from bert_score import score as bert_score_fn
            P, R, F1 = bert_score_fn(
                [generated], [reference],
                model_type="microsoft/deberta-base-mnli",
                verbose=False,
                device="cpu",
            )
            return F1[0].item()
        except Exception as e2:
            logger.warning(f"BERTScore CPU also failed: {e2}")
            return 0.0


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 10) -> float:
    """Precision@k: fraction of top-k retrieved that are relevant."""
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    return sum(1 for rid in top_k if rid in relevant_ids) / len(top_k)


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 10) -> float:
    """NDCG@k: normalized discounted cumulative gain."""
    top_k = retrieved_ids[:k]
    if not top_k or not relevant_ids:
        return 0.0

    # DCG
    dcg = 0.0
    for i, rid in enumerate(top_k):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because log2(1) = 0

    # Ideal DCG
    n_relevant = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(n_relevant))

    return dcg / idcg if idcg > 0 else 0.0


def evaluate_run(topic_id: str, condition: str,
                 generated_text: str,
                 cited_paper_ids: list[str],
                 corpus_paper_ids: set[str],
                 survey_abstract: str,
                 retrieved_paper_ids: list[str],
                 survey_cited_ids: set[str],
                 generation_method: str = "",
                 model_name: str = "",
                 compute_bert: bool = True) -> EvalResult:
    """Compute all metrics for a single run."""
    cit_prec = citation_precision(cited_paper_ids, corpus_paper_ids)
    cit_rec = citation_recall(cited_paper_ids, corpus_paper_ids)
    rouge = compute_rouge_l(generated_text, survey_abstract)

    bert_f1 = 0.0
    if compute_bert and survey_abstract:
        bert_f1 = compute_bertscore(generated_text, survey_abstract)

    # Retrieval quality (only for retrieval conditions)
    ret_p10 = 0.0
    ret_ndcg10 = 0.0
    if retrieved_paper_ids and survey_cited_ids:
        ret_p10 = precision_at_k(retrieved_paper_ids, survey_cited_ids, k=10)
        ret_ndcg10 = ndcg_at_k(retrieved_paper_ids, survey_cited_ids, k=10)

    return EvalResult(
        topic_id=topic_id,
        condition=condition,
        citation_precision=round(cit_prec, 4),
        citation_recall=round(cit_rec, 4),
        rouge_l=round(rouge, 4),
        bertscore_f1=round(bert_f1, 4),
        retrieval_precision_at_10=round(ret_p10, 4),
        retrieval_ndcg_at_10=round(ret_ndcg10, 4),
        num_cited=len(cited_paper_ids),
        num_corpus=len(corpus_paper_ids),
        generation_method=generation_method,
        model_name=model_name,
    )


def results_to_dict(results: list[EvalResult]) -> list[dict]:
    """Convert results to serializable dicts."""
    return [asdict(r) for r in results]
