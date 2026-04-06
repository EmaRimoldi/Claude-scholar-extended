"""Phase 0: data analysis — rationale sparsity and annotator agreement.

Run: python scripts/phase0_data_analysis.py
Gate G0: median rationale coverage < 0.50
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    from transformers import AutoTokenizer
    from src.data.dataset import HateXplainDataset
    from src.analysis.rationale_sparsity import compute_sparsity_stats
    from src.analysis.annotator_agreement import compute_annotator_agreement

    output_dir = Path("outputs/phase0")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    logger.info("Loading HateXplain train split...")
    train_dataset = HateXplainDataset(
        "train", tokenizer, max_length=128, include_rationale=True
    )

    logger.info("Computing rationale sparsity stats (Gate G0)...")
    sparsity_stats = compute_sparsity_stats(
        train_dataset, output_path=output_dir / "rationale_sparsity.json"
    )

    logger.info("Computing annotator agreement...")
    agreement_stats = compute_annotator_agreement(
        output_path=output_dir / "annotator_agreement.json"
    )

    # Gate G0 check
    gate_pass = sparsity_stats["gate_g0_pass"]
    logger.info(f"\n{'='*60}")
    logger.info(f"GATE G0: {'PASS' if gate_pass else 'FAIL'}")
    logger.info(f"  Median coverage: {sparsity_stats['median_coverage']:.3f}")
    logger.info(f"  Criterion: < 0.50")
    logger.info(f"  Annotator κ: {agreement_stats['label_kappa']:.3f}")
    logger.info(f"{'='*60}")

    summary = {
        "gate_g0": "PASS" if gate_pass else "FAIL",
        "sparsity": sparsity_stats,
        "agreement": agreement_stats,
    }
    with open(output_dir / "phase0_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    if not gate_pass:
        logger.error("Gate G0 FAILED. Rationale coverage is not sparse enough.")
        sys.exit(1)
    logger.info("Gate G0 PASSED. Proceed to Phase 1.")


if __name__ == "__main__":
    main()
