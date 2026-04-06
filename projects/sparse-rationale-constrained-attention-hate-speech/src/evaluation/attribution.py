"""Attribution methods: Integrated Gradients (Captum) and LIME for explanation evaluation.

IG is the primary faithfulness evaluator (hypothesis H4). LIME is used as secondary
for comparability with SRA (Eilertsen et al. 2025) and for the LIME stability test (H4a).
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import torch
from torch import Tensor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Integrated Gradients (Captum)
# ---------------------------------------------------------------------------


def compute_ig_attributions(
    model,
    input_ids: Tensor,
    attention_mask: Tensor,
    token_type_ids: Optional[Tensor],
    target_class: int,
    n_steps: int = 50,
    baseline_type: str = "pad",
    pad_token_id: int = 0,
) -> Tensor:
    """Compute Integrated Gradients attributions for a single example.

    Uses Captum's IntegratedGradients on the embedding layer inputs.
    Attributions are L2-normalized per token.

    Args:
        model: SparseBertForSequenceClassification.
        input_ids: Token ids, shape (1, L).
        attention_mask: Padding mask, shape (1, L).
        token_type_ids: Segment ids, shape (1, L) or None.
        target_class: Class index to compute attributions for.
        n_steps: Number of integration steps.
        baseline_type: "pad" uses [PAD] token as baseline; "zero" uses zero embedding.
        pad_token_id: Token ID for padding (used with baseline_type="pad").

    Returns:
        Attribution tensor, shape (L,). Higher = more attributed to target class.
    """
    from captum.attr import IntegratedGradients

    model.eval()

    def forward_fn(inputs_embeds):
        outputs = model.bert(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
        )
        pooled = outputs.pooler_output
        pooled = model.dropout(pooled)
        logits = model.classifier(pooled)
        return torch.softmax(logits, dim=-1)

    embeddings = model.bert.embeddings.word_embeddings(input_ids)  # (1, L, D)

    if baseline_type == "pad":
        baseline_ids = torch.full_like(input_ids, pad_token_id)
        baseline = model.bert.embeddings.word_embeddings(baseline_ids)
    else:
        baseline = torch.zeros_like(embeddings)

    ig = IntegratedGradients(forward_fn)
    attributions, _ = ig.attribute(
        embeddings,
        baselines=baseline,
        target=target_class,
        n_steps=n_steps,
        return_convergence_delta=True,
    )

    # Aggregate over embedding dimension: L2 norm per token
    token_attrs = attributions.squeeze(0).norm(dim=-1)  # (L,)
    return token_attrs.detach().cpu()


def compute_ig_batch(
    model,
    dataloader,
    device: str = "cuda",
    n_steps: int = 50,
) -> list[dict]:
    """Compute IG attributions for all examples in a dataloader.

    Returns:
        List of dicts with keys: "post_id", "attributions" (np.ndarray), "label".
    """
    model.eval()
    model = model.to(device)
    results = []

    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        token_type_ids = batch.get("token_type_ids", None)
        if token_type_ids is not None:
            token_type_ids = token_type_ids.to(device)
        labels = batch["labels"]
        post_ids = batch.get("post_ids", [None] * input_ids.size(0))

        for i in range(input_ids.size(0)):
            attrs = compute_ig_attributions(
                model=model,
                input_ids=input_ids[i:i+1],
                attention_mask=attention_mask[i:i+1],
                token_type_ids=token_type_ids[i:i+1] if token_type_ids is not None else None,
                target_class=int(labels[i].item()),
                n_steps=n_steps,
            )
            results.append({
                "post_id": post_ids[i],
                "attributions": attrs.numpy(),
                "label": int(labels[i].item()),
            })

        if batch_idx % 10 == 0:
            logger.info(f"IG attributions: processed {batch_idx + 1} batches")

    return results


# ---------------------------------------------------------------------------
# LIME
# ---------------------------------------------------------------------------


def compute_lime_attributions(
    model,
    text_tokens: list[str],
    tokenizer,
    target_class: int,
    num_samples: int = 1000,
    device: str = "cuda",
) -> np.ndarray:
    """Compute LIME attributions for a single example.

    Args:
        model: SparseBertForSequenceClassification.
        text_tokens: List of space-separated word tokens.
        tokenizer: BERT tokenizer.
        target_class: Class to explain.
        num_samples: Number of LIME perturbation samples.
        device: Compute device.

    Returns:
        LIME feature importance array, shape (len(text_tokens),).
    """
    from lime.lime_text import LimeTextExplainer

    model.eval()
    model = model.to(device)

    def predict_fn(texts: list[str]) -> np.ndarray:
        """Predict probabilities for LIME perturbations."""
        encoding = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        encoding = {k: v.to(device) for k, v in encoding.items()}
        with torch.no_grad():
            outputs = model(**encoding)
        probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
        return probs

    explainer = LimeTextExplainer(class_names=["hate", "offensive", "normal"])
    text = " ".join(text_tokens)
    explanation = explainer.explain_instance(
        text,
        predict_fn,
        num_features=len(text_tokens),
        num_samples=num_samples,
        labels=[target_class],
    )

    # Map LIME word attributions back to word indices
    word_attrs = np.zeros(len(text_tokens))
    for word, weight in explanation.as_list(label=target_class):
        # Find word in token list (case-insensitive)
        for i, token in enumerate(text_tokens):
            if token.lower() == word.lower():
                word_attrs[i] = weight
                break

    return word_attrs


def compute_lime_stability(
    model,
    text_tokens: list[str],
    tokenizer,
    target_class: int,
    n_runs: int = 10,
    num_samples: int = 1000,
    device: str = "cuda",
) -> dict:
    """Compute LIME stability: run LIME n_runs times and measure consistency.

    H4a hypothesis: LIME has low stability (Kendall's τ < 0.8) on short texts.

    Args:
        model: Trained model.
        text_tokens: Word tokens.
        tokenizer: BERT tokenizer.
        target_class: Class to explain.
        n_runs: Number of LIME runs for stability estimation.
        num_samples: Samples per LIME run.
        device: Compute device.

    Returns:
        Dict with "mean_kendall_tau", "std_kendall_tau", "all_attributions".
    """
    from scipy.stats import kendalltau

    all_attrs = []
    for run in range(n_runs):
        attrs = compute_lime_attributions(
            model, text_tokens, tokenizer, target_class, num_samples=num_samples, device=device
        )
        all_attrs.append(attrs)

    # Compute pairwise Kendall's τ between all run pairs
    tau_values = []
    for i in range(n_runs):
        for j in range(i + 1, n_runs):
            tau, _ = kendalltau(all_attrs[i], all_attrs[j])
            tau_values.append(tau)

    return {
        "mean_kendall_tau": float(np.mean(tau_values)),
        "std_kendall_tau": float(np.std(tau_values)),
        "all_attributions": all_attrs,
    }


def compute_ig_lime_agreement(
    ig_attrs: np.ndarray,
    lime_attrs: np.ndarray,
) -> float:
    """Compute Spearman correlation between IG and LIME attributions.

    H4b: IG and LIME agree on high-importance tokens despite mechanistic differences.

    Args:
        ig_attrs: IG attribution scores per token.
        lime_attrs: LIME attribution scores per token (same length).

    Returns:
        Spearman ρ in [-1, 1].
    """
    from scipy.stats import spearmanr

    rho, _ = spearmanr(ig_attrs, lime_attrs)
    return float(rho)
