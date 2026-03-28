#!/usr/bin/env python3
"""Run faithfulness and plausibility evaluation on ALL trained models.

Scans results/ for subdirectories containing best_model.pt, loads each
checkpoint, runs the full evaluation suite (classification from existing
results.json, plus faithfulness, plausibility, and attention property
metrics on the test set), and aggregates everything into a CSV.

Usage:
    python scripts/run_full_evaluation.py
    python scripts/run_full_evaluation.py --results-dir results --cache-dir data/cache
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

# ---------------------------------------------------------------------------
# Project imports — resolve project root so we can import src.*
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.hatexplain import HateXplainDataset, collate_fn
from src.models.bert_sparse import BertSparseForClassification, BertSparseOutput
from src.models.head_importance import select_top_k_heads

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

LABEL_NAMES = ["hatespeech", "offensive", "normal"]
EVAL_BATCH_SIZE = 32


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def _resolve_supervised_heads(
    model_cfg: Dict[str, Any],
) -> Any:
    """Resolve supervised_heads from the saved config dict."""
    supervised_heads = model_cfg.get("supervised_heads", "all")
    if isinstance(supervised_heads, str) and supervised_heads not in ("all",):
        # topk or similar — load from head importance file
        hi_path = Path(model_cfg.get(
            "head_importance_path",
            str(PROJECT_ROOT / "results" / "head_importance" / "head_importance.json"),
        ))
        if hi_path.exists():
            with open(hi_path) as f:
                hi_data = json.load(f)
            importance: Dict[Tuple[int, int], float] = {}
            for layer_idx, row in enumerate(hi_data["head_importance"]):
                for head_idx, score in enumerate(row):
                    importance[(layer_idx, head_idx)] = score
            top_k = model_cfg.get("top_k", 24)
            supervised_heads = select_top_k_heads(importance, top_k)
            logger.info("Resolved top-%d heads from %s", top_k, hi_path)
        else:
            logger.warning(
                "Head importance file not found at %s, falling back to 'all'",
                hi_path,
            )
            supervised_heads = "all"
    return supervised_heads


def load_model(
    result_dir: Path,
    device: torch.device,
) -> Tuple[BertSparseForClassification, Dict[str, Any]]:
    """Load model from checkpoint and its saved config."""
    results_json = result_dir / "results.json"
    checkpoint_path = result_dir / "best_model.pt"

    with open(results_json) as f:
        results_data = json.load(f)
    model_cfg = results_data.get("config", {}).get("model", {})

    supervised_heads = _resolve_supervised_heads(model_cfg)

    model = BertSparseForClassification(
        model_name=model_cfg.get("model_name", "bert-base-uncased"),
        num_labels=model_cfg.get("num_labels", 3),
        supervised_heads=supervised_heads,
        attention_transform=model_cfg.get("attention_transform", "softmax"),
        lambda_attn=model_cfg.get("lambda_attn", 0.0),
    )

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, results_data


# ---------------------------------------------------------------------------
# Metric computation helpers
# ---------------------------------------------------------------------------

@torch.no_grad()
def _get_confidence(
    model: BertSparseForClassification,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return (probs [B, C], preds [B])."""
    out: BertSparseOutput = model(
        input_ids=input_ids, attention_mask=attention_mask,
    )
    probs = F.softmax(out.logits, dim=-1)
    preds = probs.argmax(dim=-1)
    return probs, preds


@torch.no_grad()
def compute_faithfulness_batch(
    model: BertSparseForClassification,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    rationale_mask: torch.Tensor,
    rationale_threshold: float = 0.5,
) -> Dict[str, List[float]]:
    """Compute per-sample sufficiency and comprehensiveness for one batch."""
    device = input_ids.device

    # Full-input confidence
    full_probs, full_preds = _get_confidence(model, input_ids, attention_mask)

    binary_rat = (rationale_mask >= rationale_threshold).long().to(device)

    # --- Sufficiency: keep only rationale tokens + CLS + SEP ---
    suff_mask = binary_rat * attention_mask.long()
    suff_mask[:, 0] = attention_mask[:, 0]  # CLS
    seq_lengths = attention_mask.sum(dim=1).long()
    for j in range(suff_mask.size(0)):
        sep_idx = seq_lengths[j] - 1
        suff_mask[j, sep_idx] = 1
    suff_ids = input_ids * suff_mask
    suff_probs, _ = _get_confidence(model, suff_ids, suff_mask)

    # --- Comprehensiveness: remove rationale tokens ---
    comp_mask = (1 - binary_rat) * attention_mask.long()
    comp_mask[:, 0] = attention_mask[:, 0]
    for j in range(comp_mask.size(0)):
        sep_idx = seq_lengths[j] - 1
        comp_mask[j, sep_idx] = 1
    comp_ids = input_ids * comp_mask
    comp_probs, _ = _get_confidence(model, comp_ids, comp_mask)

    sufficiency_scores: List[float] = []
    comprehensiveness_scores: List[float] = []
    for i in range(input_ids.size(0)):
        pred_cls = int(full_preds[i])
        full_conf = float(full_probs[i, pred_cls])
        rat_conf = float(suff_probs[i, pred_cls])
        mask_conf = float(comp_probs[i, pred_cls])

        if full_conf > 0:
            sufficiency_scores.append(rat_conf / full_conf)
        comprehensiveness_scores.append(full_conf - mask_conf)

    return {
        "sufficiency": sufficiency_scores,
        "comprehensiveness": comprehensiveness_scores,
    }


@torch.no_grad()
def compute_attention_properties_batch(
    attentions: Tuple[torch.Tensor, ...],
    attention_mask: torch.Tensor,
) -> Dict[str, List[float]]:
    """Compute attention entropy and sparsity for one batch.

    Uses last-layer CLS attention averaged over heads.
    """
    last_attn = attentions[-1]  # (B, H, L, L)
    cls_attn = last_attn[:, :, 0, :].mean(dim=1)  # (B, L)
    cls_attn_np = cls_attn.cpu().numpy().astype(np.float64)
    mask_np = attention_mask.cpu().numpy().astype(bool)

    entropies: List[float] = []
    sparsity_ratios: List[float] = []

    for i in range(cls_attn_np.shape[0]):
        w = cls_attn_np[i][mask_np[i]]
        # Entropy
        w_sum = w.sum()
        if w_sum > 0:
            p = w / w_sum
        else:
            p = np.ones_like(w) / max(len(w), 1)
        p = np.clip(p, 1e-12, None)
        entropy = -float(np.sum(p * np.log(p)))
        entropies.append(entropy)

        # Sparsity: fraction of exact zeros
        sparsity = float((w == 0.0).sum() / max(len(w), 1))
        sparsity_ratios.append(sparsity)

    return {"entropy": entropies, "sparsity": sparsity_ratios}


@torch.no_grad()
def compute_plausibility_batch(
    cls_attn: np.ndarray,
    rationale_mask: np.ndarray,
    attention_mask: np.ndarray,
) -> Dict[str, Any]:
    """Compute token F1 and collect scores/labels for AUPRC (batch level).

    Token F1 uses mean-attention threshold per sample.
    """
    from sklearn.metrics import f1_score as sk_f1

    token_f1_scores: List[float] = []
    all_scores: List[np.ndarray] = []
    all_labels: List[np.ndarray] = []

    for i in range(cls_attn.shape[0]):
        mask_i = attention_mask[i].astype(bool)
        w = cls_attn[i][mask_i]
        rat = rationale_mask[i][mask_i]

        # Token F1: threshold at mean attention
        threshold = float(w.mean()) if len(w) > 0 else 0.5
        pred_bin = (w >= threshold).astype(int)
        gt_bin = rat.astype(int)
        f1 = float(sk_f1(gt_bin, pred_bin, zero_division=0.0))
        token_f1_scores.append(f1)

        all_scores.append(w)
        all_labels.append(rat)

    return {
        "token_f1": token_f1_scores,
        "flat_scores": all_scores,
        "flat_labels": all_labels,
    }


# ---------------------------------------------------------------------------
# Full evaluation for one model
# ---------------------------------------------------------------------------

def evaluate_model(
    model: BertSparseForClassification,
    test_loader: DataLoader,
    device: torch.device,
    results_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Run full evaluation suite on a single model."""
    from sklearn.metrics import average_precision_score

    model.eval()

    # Collect existing classification metrics from results.json
    test_metrics = results_data.get("test_metrics", {})
    classification = {
        "macro_f1": test_metrics.get("macro_f1", 0.0),
        "per_class_f1": test_metrics.get("per_class_f1", []),
        "accuracy": test_metrics.get("accuracy", 0.0),
    }

    # Accumulators
    all_sufficiency: List[float] = []
    all_comprehensiveness: List[float] = []
    all_entropy: List[float] = []
    all_sparsity: List[float] = []
    all_token_f1: List[float] = []
    all_plaus_scores: List[np.ndarray] = []
    all_plaus_labels: List[np.ndarray] = []

    for batch in test_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        rationale_mask = batch["rationale_mask"]  # keep on CPU for numpy ops

        # Forward pass to get attentions
        with torch.no_grad():
            outputs: BertSparseOutput = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
        attentions = outputs.attentions

        # Faithfulness
        faith = compute_faithfulness_batch(
            model, input_ids, attention_mask,
            rationale_mask.to(device),
        )
        all_sufficiency.extend(faith["sufficiency"])
        all_comprehensiveness.extend(faith["comprehensiveness"])

        # Attention properties
        attn_props = compute_attention_properties_batch(attentions, attention_mask)
        all_entropy.extend(attn_props["entropy"])
        all_sparsity.extend(attn_props["sparsity"])

        # Plausibility: use last-layer CLS attention averaged over heads
        last_attn = attentions[-1]
        cls_attn = last_attn[:, :, 0, :].mean(dim=1).cpu().numpy().astype(np.float64)
        rat_np = rationale_mask.numpy().astype(np.float64)
        mask_np = attention_mask.cpu().numpy().astype(np.float64)

        plaus = compute_plausibility_batch(cls_attn, rat_np, mask_np)
        all_token_f1.extend(plaus["token_f1"])
        all_plaus_scores.extend(plaus["flat_scores"])
        all_plaus_labels.extend(plaus["flat_labels"])

    # Aggregate plausibility AUPRC
    flat_scores = np.concatenate(all_plaus_scores)
    flat_labels = np.concatenate(all_plaus_labels)
    if flat_labels.sum() > 0:
        auprc = float(average_precision_score(flat_labels.astype(int), flat_scores))
    else:
        auprc = 0.0

    return {
        "classification": classification,
        "faithfulness": {
            "sufficiency": float(np.mean(all_sufficiency)) if all_sufficiency else 0.0,
            "comprehensiveness": float(np.mean(all_comprehensiveness)) if all_comprehensiveness else 0.0,
        },
        "plausibility": {
            "token_f1": float(np.mean(all_token_f1)) if all_token_f1 else 0.0,
            "auprc": auprc,
        },
        "attention_properties": {
            "entropy": float(np.mean(all_entropy)) if all_entropy else 0.0,
            "sparsity_ratio": float(np.mean(all_sparsity)) if all_sparsity else 0.0,
        },
    }


# ---------------------------------------------------------------------------
# Aggregation to CSV
# ---------------------------------------------------------------------------

def flatten_eval(name: str, eval_result: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten nested eval_full.json into a single row dict."""
    m = re.match(r"^(.+?)_s(\d+)$", name)
    condition = m.group(1) if m else name
    seed = int(m.group(2)) if m else 0

    cls = eval_result.get("classification", {})
    faith = eval_result.get("faithfulness", {})
    plaus = eval_result.get("plausibility", {})
    attn = eval_result.get("attention_properties", {})
    per_class = cls.get("per_class_f1", [None, None, None])

    return {
        "condition": condition,
        "seed": seed,
        "macro_f1": cls.get("macro_f1"),
        "accuracy": cls.get("accuracy"),
        "per_class_f1_0": per_class[0] if len(per_class) > 0 else None,
        "per_class_f1_1": per_class[1] if len(per_class) > 1 else None,
        "per_class_f1_2": per_class[2] if len(per_class) > 2 else None,
        "sufficiency": faith.get("sufficiency"),
        "comprehensiveness": faith.get("comprehensiveness"),
        "token_f1": plaus.get("token_f1"),
        "auprc": plaus.get("auprc"),
        "entropy": attn.get("entropy"),
        "sparsity_ratio": attn.get("sparsity_ratio"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full evaluation on all trained models.",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=str(PROJECT_ROOT / "results"),
        help="Directory containing per-model result subdirectories.",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "cache"),
        help="Directory for cached dataset downloads.",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    cache_dir = args.cache_dir
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    # Build test dataloader once (shared across all models)
    model_name = "bert-base-uncased"
    max_length = 128
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    test_ds = HateXplainDataset("test", tokenizer, max_length, cache_dir)
    test_loader = DataLoader(
        test_ds,
        batch_size=EVAL_BATCH_SIZE,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=4,
        pin_memory=True,
    )
    logger.info("Test set: %d samples", len(test_ds))

    # Discover all model directories
    model_dirs = sorted([
        d for d in results_dir.iterdir()
        if d.is_dir()
        and (d / "best_model.pt").exists()
        and (d / "results.json").exists()
    ])
    logger.info("Found %d model directories with checkpoints.", len(model_dirs))

    if not model_dirs:
        logger.error("No model directories found in %s", results_dir)
        sys.exit(1)

    # Evaluate each model
    import pandas as pd

    all_rows: List[Dict[str, Any]] = []
    for i, model_dir in enumerate(model_dirs):
        name = model_dir.name
        logger.info("[%d/%d] Evaluating %s ...", i + 1, len(model_dirs), name)

        try:
            model, results_data = load_model(model_dir, device)
            eval_result = evaluate_model(model, test_loader, device, results_data)

            # Save per-model results
            eval_path = model_dir / "eval_full.json"
            with open(eval_path, "w") as f:
                json.dump(eval_result, f, indent=2)
            logger.info("  Saved %s", eval_path)

            # Flatten for CSV
            row = flatten_eval(name, eval_result)
            all_rows.append(row)

            # Free GPU memory
            del model
            torch.cuda.empty_cache()

        except Exception as e:
            logger.error("  Failed to evaluate %s: %s", name, e)
            continue

    # Aggregate to CSV
    if all_rows:
        df = pd.DataFrame(all_rows)
        csv_path = results_dir / "full_evaluation.csv"
        df.to_csv(csv_path, index=False)
        logger.info("Aggregated results saved to %s", csv_path)
        print("\n=== Full Evaluation Summary ===")
        print(df.to_string(index=False, float_format="%.4f"))
    else:
        logger.error("No models were successfully evaluated.")
        sys.exit(1)


if __name__ == "__main__":
    main()
