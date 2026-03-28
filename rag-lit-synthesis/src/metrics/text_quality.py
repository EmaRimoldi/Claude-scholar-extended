"""Text quality metrics: ROUGE, BERTScore."""

from dataclasses import dataclass

from ..registry import register


@dataclass
class TextQualityResult:
    """Text quality scores."""
    rouge1: float
    rouge2: float
    rougeL: float
    bertscore_precision: float
    bertscore_recall: float
    bertscore_f1: float


@register("metric", "rouge")
def compute_rouge(generated: str, reference: str) -> dict[str, float]:
    """Compute ROUGE scores."""
    from rouge_score import rouge_scorer
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, generated)
    return {
        "rouge1": scores["rouge1"].fmeasure,
        "rouge2": scores["rouge2"].fmeasure,
        "rougeL": scores["rougeL"].fmeasure,
    }


@register("metric", "bertscore")
def compute_bertscore(generated: str, reference: str,
                       model_type: str = "microsoft/deberta-xlarge-mnli") -> dict[str, float]:
    """Compute BERTScore."""
    from bert_score import score
    P, R, F1 = score([generated], [reference], model_type=model_type, verbose=False)
    return {
        "bertscore_precision": P[0].item(),
        "bertscore_recall": R[0].item(),
        "bertscore_f1": F1[0].item(),
    }
