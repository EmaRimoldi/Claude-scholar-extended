"""Interpretability evaluation: ERASER + faithfulness + plausibility.

Loads the best checkpoint for each condition (averaged over seeds via ensemble),
runs evaluation on the test set, and writes:
  results/tables/eraser_results.csv   — per-condition AOPC scores
  results/tables/plausibility.csv     — token-level F1 vs human rationale
  results/tables/faithfulness.csv     — H4 adversarial swap delta
  results/tables/interpretability_summary.csv — all metrics, one row per condition

Usage:
    python scripts/eval_interpretability.py [--device cuda|cpu] [--max-examples N]

Expects to be run from the project directory:
    cd projects/sparse-rationale-constrained-attention-hate-speech
    python scripts/eval_interpretability.py
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path

import torch

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")

PROJECT_DIR = Path(".")
CHECKPOINT_DIR = PROJECT_DIR / "checkpoints"
RESULTS_DIR = PROJECT_DIR / "results" / "tables"
DATA_DIR = PROJECT_DIR / "data" / "hatexplain"

CONDITIONS = ["C1", "C2", "C3", "C4", "C5"]
SEEDS = [42, 43, 44, 45, 46]


def load_best_model(condition: str, seed: int, device: torch.device):
    """Load best checkpoint for a given condition and seed."""
    from src.model_module.bert_classifier import BertHateSpeechClassifier, ClassifierConfig

    ckpt_path = CHECKPOINT_DIR / condition / f"seed_{seed}" / f"cond_{condition}_seed_{seed}" / "best_model.pt"
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg_dict = ckpt["config"]

    # Reconstruct ClassifierConfig from saved dict
    model_cfg = cfg_dict.get("model", {})
    clf_cfg = ClassifierConfig(
        model_name=model_cfg.get("model_name", "bert-base-uncased"),
        use_sparsemax=model_cfg.get("use_sparsemax", False),
        supervised_heads=model_cfg.get("supervised_heads"),
        alpha=model_cfg.get("alpha", 0.0),
        use_kl_loss=model_cfg.get("use_kl_loss", False),
        num_labels=model_cfg.get("num_labels", 3),
        dropout=model_cfg.get("dropout", 0.1),
    )

    model = BertHateSpeechClassifier(clf_cfg)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()
    return model


def build_test_dataloader(batch_size: int = 16, max_examples: int = None):
    """Build test DataLoader from cached JSONL."""
    from transformers import AutoTokenizer
    from src.data_module.loader import load_jsonl
    from src.data_module.dataset import HateXplainDataset

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    test_path = DATA_DIR / "test.jsonl"
    if not test_path.exists():
        test_path = DATA_DIR / "validation.jsonl"
        logger.warning(f"test.jsonl not found, using validation.jsonl")

    # load_jsonl returns HateXplainExample objects directly — do NOT pass through
    # load_hatexplain_examples again (that expects raw dicts, not HateXplainExample)
    examples = load_jsonl(str(test_path))
    if max_examples:
        examples = examples[:max_examples]

    dataset = HateXplainDataset(examples, tokenizer, max_length=128)

    from torch.utils.data import DataLoader
    return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)


def compute_eraser_scores(model, loader, device, n_steps: int = 10) -> dict:
    """Compute ERASER comprehensiveness and sufficiency AOPC."""
    from src.metrics_module.eraser import compute_comprehensiveness_aopc, compute_sufficiency_aopc

    all_input_ids, all_masks, all_cls_attn = [], [], []

    with torch.no_grad():
        for batch in loader:
            iids = batch["input_ids"].to(device)
            amask = batch["attention_mask"].to(device)
            ttype = batch["token_type_ids"].to(device)
            out = model(input_ids=iids, attention_mask=amask, token_type_ids=ttype)
            cls_attn = out.get("cls_attention")
            if cls_attn is None:
                # No supervised heads: use average attention from all heads
                # We need output_attentions=True; model already sets this
                # Fallback: skip ERASER for this condition
                return {"comprehensiveness_aopc": None, "sufficiency_aopc": None}
            all_input_ids.append(iids.cpu())
            all_masks.append(amask.cpu())
            all_cls_attn.append(cls_attn.cpu())

    input_ids = torch.cat(all_input_ids)
    attention_mask = torch.cat(all_masks)
    cls_attention = torch.cat(all_cls_attn)

    def model_fn(ids, mask):
        with torch.no_grad():
            out = model(input_ids=ids.to(device), attention_mask=mask.to(device))
        return out["logits"].cpu()

    comp = compute_comprehensiveness_aopc(model_fn, input_ids, attention_mask, cls_attention, n_steps=n_steps)
    suff = compute_sufficiency_aopc(model_fn, input_ids, attention_mask, cls_attention, n_steps=n_steps)
    return {"comprehensiveness_aopc": comp, "sufficiency_aopc": suff}


def compute_plausibility(model, loader, device) -> dict:
    """Compute token-level F1 between model top-k attention and human rationale."""
    from src.metrics_module.eraser import compute_plausibility_metrics

    all_input_ids, all_masks, all_cls_attn, all_rationale_binary = [], [], [], []

    with torch.no_grad():
        for batch in loader:
            iids = batch["input_ids"].to(device)
            amask = batch["attention_mask"].to(device)
            ttype = batch["token_type_ids"].to(device)
            rationale_bin = batch["rationale_binary"]
            out = model(input_ids=iids, attention_mask=amask, token_type_ids=ttype)
            cls_attn = out.get("cls_attention")
            if cls_attn is None:
                return {"plausibility_f1": None, "plausibility_iou": None}
            all_input_ids.append(iids.cpu())
            all_masks.append(amask.cpu())
            all_cls_attn.append(cls_attn.cpu())
            all_rationale_binary.append(rationale_bin)

    cls_attention = torch.cat(all_cls_attn)
    rationale_binary = torch.cat(all_rationale_binary)

    metrics = compute_plausibility_metrics(cls_attention, rationale_binary)
    return metrics


def compute_faithfulness(model, loader, device) -> dict:
    """H4 adversarial swap: replace CLS attention with uniform, measure KL(P_swap||P_orig)."""
    from src.metrics_module.faithfulness import compute_adversarial_swap_kl, aggregate_swap_kl_statistics

    all_kl_values = []

    with torch.no_grad():
        for batch in loader:
            iids = batch["input_ids"].to(device)
            amask = batch["attention_mask"].to(device)
            ttype = batch["token_type_ids"].to(device)
            result = compute_adversarial_swap_kl(model, iids, amask, token_type_ids=ttype)
            kl = result.get("kl_divergence")
            if kl is None:
                return {"adversarial_swap_delta": None}
            all_kl_values.append(kl.cpu())

    if not all_kl_values:
        return {"adversarial_swap_delta": None}

    all_kl = torch.cat(all_kl_values)
    stats = aggregate_swap_kl_statistics(all_kl)
    return {
        "adversarial_swap_delta": round(stats.get("mean_kl", 0.0), 6),
        "adversarial_swap_kl_mean": round(stats.get("mean_kl", 0.0), 6),
        "adversarial_swap_kl_std": round(stats.get("std_kl", 0.0), 6),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-examples", type=int, default=None,
                        help="Limit test examples (default: all). Use 200 for quick smoke test.")
    parser.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    parser.add_argument("--conditions", nargs="+", default=CONDITIONS)
    args = parser.parse_args()

    device = torch.device(args.device)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Device: {device} | Max examples: {args.max_examples or 'all'}")
    loader = build_test_dataloader(batch_size=16, max_examples=args.max_examples)
    logger.info(f"Test batches: {len(loader)}")

    all_rows = []  # per-seed rows
    summary_rows = []  # per-condition aggregated

    for condition in args.conditions:
        logger.info(f"\n{'='*50}\nCondition: {condition}\n{'='*50}")
        cond_eraser, cond_plaus, cond_faith = [], [], []

        for seed in args.seeds:
            logger.info(f"  Loading {condition} seed={seed}")
            try:
                model = load_best_model(condition, seed, device)
            except FileNotFoundError as e:
                logger.warning(f"  SKIP: {e}")
                continue

            eraser = compute_eraser_scores(model, loader, device)
            plaus = compute_plausibility(model, loader, device)
            faith = compute_faithfulness(model, loader, device)

            row = {
                "condition": condition,
                "seed": seed,
                **{f"eraser_{k}": v for k, v in eraser.items()},
                **plaus,
                **faith,
            }
            all_rows.append(row)
            logger.info(f"  {condition} s={seed}: {eraser} | {plaus} | {faith}")

            if eraser["comprehensiveness_aopc"] is not None:
                cond_eraser.append(eraser)
            if plaus.get("plausibility_f1") is not None:
                cond_plaus.append(plaus)
            if faith.get("adversarial_swap_delta") is not None:
                cond_faith.append(faith)

        # Aggregate over seeds
        def mean_or_none(lst, key):
            vals = [x[key] for x in lst if x.get(key) is not None]
            return round(sum(vals) / len(vals), 6) if vals else None

        import statistics as _stats
        def std_or_none(lst, key):
            vals = [x[key] for x in lst if x.get(key) is not None]
            return round(_stats.stdev(vals), 6) if len(vals) > 1 else None

        summary_rows.append({
            "condition": condition,
            "n_seeds": len([r for r in all_rows if r["condition"] == condition]),
            "comprehensiveness_aopc_mean": mean_or_none(cond_eraser, "comprehensiveness_aopc"),
            "comprehensiveness_aopc_std": std_or_none(cond_eraser, "comprehensiveness_aopc"),
            "sufficiency_aopc_mean": mean_or_none(cond_eraser, "sufficiency_aopc"),
            "sufficiency_aopc_std": std_or_none(cond_eraser, "sufficiency_aopc"),
            "plausibility_f1_mean": mean_or_none(cond_plaus, "plausibility_f1"),
            "plausibility_f1_std": std_or_none(cond_plaus, "plausibility_f1"),
            "adversarial_swap_delta_mean": mean_or_none(cond_faith, "adversarial_swap_delta"),
            "adversarial_swap_delta_std": std_or_none(cond_faith, "adversarial_swap_delta"),
        })

    # Write CSVs
    if all_rows:
        with open(RESULTS_DIR / "interpretability_per_seed.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            w.writeheader(); w.writerows(all_rows)
        logger.info(f"Written: {RESULTS_DIR}/interpretability_per_seed.csv")

    if summary_rows:
        with open(RESULTS_DIR / "interpretability_summary.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
            w.writeheader(); w.writerows(summary_rows)
        logger.info(f"Written: {RESULTS_DIR}/interpretability_summary.csv")

    # Also write JSON for downstream analysis
    with open(RESULTS_DIR / "interpretability_summary.json", "w") as f:
        json.dump(summary_rows, f, indent=2)

    logger.info("\n=== DONE ===")
    for row in summary_rows:
        logger.info(
            f"  {row['condition']}: "
            f"comp={row['comprehensiveness_aopc_mean']}  "
            f"suff={row['sufficiency_aopc_mean']}  "
            f"swap_delta={row['adversarial_swap_delta_mean']}"
        )


if __name__ == "__main__":
    main()
