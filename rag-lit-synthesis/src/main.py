"""End-to-end RAG literature synthesis experiment.

Usage:
    python -m src.main                # full run (GPU required for LLM/BERTScore)
    python -m src.main --dry-run      # structure check only (no GPU needed)
    python -m src.main --build-data   # only download benchmark data
    python -m src.main --no-bert      # skip BERTScore (faster, CPU-friendly)
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Project root = rag-lit-synthesis/
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "benchmark"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"

CONDITIONS = ["bm25", "dense", "no_retrieval"]


def setup_logging(log_dir: Path | None = None):
    """Configure logging to console and optionally to file."""
    handlers = [logging.StreamHandler()]
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_dir / "experiment.log"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def dry_run():
    """Verify project structure without running anything expensive."""
    print("=== DRY RUN: Structure Check ===\n")

    checks = []

    # Check source files exist
    for path in [
        "src/data/benchmark_builder.py",
        "src/retrieval/retrievers.py",
        "src/generation/synthesizer.py",
        "src/evaluation/evaluate.py",
    ]:
        exists = (PROJECT_ROOT / path).exists()
        checks.append((path, exists))
        print(f"  {'OK' if exists else 'MISSING'}: {path}")

    # Check imports work
    print("\nImport checks:")
    import_checks = [
        ("src.data.benchmark_builder", "benchmark_builder"),
        ("src.retrieval.retrievers", "retrievers"),
        ("src.generation.synthesizer", "synthesizer"),
        ("src.evaluation.evaluate", "evaluate"),
    ]
    for module, name in import_checks:
        try:
            __import__(module)
            print(f"  OK: {name}")
            checks.append((name, True))
        except Exception as e:
            print(f"  FAIL: {name} — {e}")
            checks.append((name, False))

    # Check key libraries
    print("\nLibrary checks:")
    libs = ["torch", "transformers", "sentence_transformers", "rank_bm25",
            "rouge_score", "bert_score", "matplotlib", "pandas", "numpy"]
    for lib in libs:
        try:
            __import__(lib)
            print(f"  OK: {lib}")
        except ImportError:
            print(f"  MISSING: {lib}")
            checks.append((lib, False))

    # Check GPU
    print("\nGPU check:")
    try:
        import torch
        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            print(f"  GPU: {gpu} ({vram:.1f} GB)")
        else:
            print("  No GPU (will use template fallback for generation)")
    except Exception as e:
        print(f"  GPU check failed: {e}")

    # Check data
    print("\nData check:")
    if DATA_DIR.exists() and (DATA_DIR / "manifest.json").exists():
        manifest = json.loads((DATA_DIR / "manifest.json").read_text())
        print(f"  Benchmark: {manifest['num_topics']} topics")
        for t in manifest["topics"]:
            print(f"    - {t['topic_id']}: {t['num_corpus']} papers")
    else:
        print("  No benchmark data yet (run with --build-data first)")

    # Output dirs
    print("\nOutput directories:")
    for d in [OUTPUT_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  OK: {d.relative_to(PROJECT_ROOT)}")

    n_pass = sum(1 for _, ok in checks if ok)
    n_total = len(checks)
    print(f"\n=== {n_pass}/{n_total} checks passed ===")
    return all(ok for _, ok in checks)


def build_data():
    """Download benchmark data from Semantic Scholar API."""
    from src.data.benchmark_builder import build_benchmark
    logger.info("Building benchmark dataset...")
    topics = build_benchmark(str(DATA_DIR))
    logger.info(f"Benchmark ready: {len(topics)} topics")
    for t in topics:
        logger.info(f"  {t.topic_id}: {len(t.corpus)} papers, survey={t.survey.title if t.survey else 'None'}")
    return topics


def run_experiment(no_bert: bool = False):
    """Run the full 3 conditions × 5 topics experiment."""
    from src.data.benchmark_builder import load_benchmark
    from src.retrieval.retrievers import BM25Retriever, DenseRetriever
    from src.generation.synthesizer import (
        template_synthesis, llm_synthesis, _try_load_llm,
    )
    from src.evaluation.evaluate import evaluate_run, results_to_dict

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Load benchmark
    logger.info("Loading benchmark data...")
    topics = load_benchmark(str(DATA_DIR))
    logger.info(f"Loaded {len(topics)} topics")

    # Try to load LLM once (reuse across all runs)
    model_bundle = _try_load_llm()
    use_llm = model_bundle is not None
    logger.info(f"Generation mode: {'LLM' if use_llm else 'template'}")

    all_results = []
    all_generations = []

    for topic in topics:
        logger.info(f"\n{'='*60}")
        logger.info(f"Topic: {topic.topic_name} ({len(topic.corpus)} papers)")
        logger.info(f"{'='*60}")

        # Prepare corpus as dicts for retrievers
        corpus_dicts = [asdict(p) for p in topic.corpus]
        corpus_ids = {p.paper_id for p in topic.corpus}
        survey_cited_set = set(topic.survey_cited_ids)
        survey_abstract = topic.survey.abstract if topic.survey else ""

        # Build retrievers
        logger.info("Building BM25 index...")
        bm25 = BM25Retriever(corpus_dicts)
        logger.info("Building Dense index...")
        dense = DenseRetriever(corpus_dicts, model_name="all-MiniLM-L6-v2")

        query = topic.topic_name

        for condition in CONDITIONS:
            logger.info(f"\n--- Condition: {condition} ---")

            retrieved_papers = []
            retrieved_ids = []

            if condition == "bm25":
                results = bm25.retrieve(query, top_k=10)
                retrieved_papers = [
                    {"paper_id": r.paper_id, "title": r.title,
                     "abstract": r.abstract, "authors": [], "year": 0}
                    for r in results
                ]
                # Enrich with full paper data
                paper_lookup = {p.paper_id: p for p in topic.corpus}
                for rp in retrieved_papers:
                    full = paper_lookup.get(rp["paper_id"])
                    if full:
                        rp["authors"] = full.authors
                        rp["year"] = full.year
                retrieved_ids = [r.paper_id for r in results]

            elif condition == "dense":
                results = dense.retrieve(query, top_k=10)
                retrieved_papers = [
                    {"paper_id": r.paper_id, "title": r.title,
                     "abstract": r.abstract, "authors": [], "year": 0}
                    for r in results
                ]
                paper_lookup = {p.paper_id: p for p in topic.corpus}
                for rp in retrieved_papers:
                    full = paper_lookup.get(rp["paper_id"])
                    if full:
                        rp["authors"] = full.authors
                        rp["year"] = full.year
                retrieved_ids = [r.paper_id for r in results]

            # Generate synthesis
            if use_llm:
                synthesis = llm_synthesis(
                    topic.topic_name, retrieved_papers, condition,
                    model_bundle=model_bundle,
                )
            else:
                synthesis = template_synthesis(
                    topic.topic_name, retrieved_papers, condition,
                )

            logger.info(f"  Generated {len(synthesis.text)} chars, "
                        f"cited {len(synthesis.cited_paper_ids)} papers, "
                        f"method={synthesis.method}")

            # Evaluate
            eval_result = evaluate_run(
                topic_id=topic.topic_id,
                condition=condition,
                generated_text=synthesis.text,
                cited_paper_ids=synthesis.cited_paper_ids,
                corpus_paper_ids=corpus_ids,
                survey_abstract=survey_abstract,
                retrieved_paper_ids=retrieved_ids,
                survey_cited_ids=survey_cited_set,
                generation_method=synthesis.method,
                model_name=synthesis.model_name,
                compute_bert=not no_bert,
            )
            all_results.append(eval_result)

            # Store generation for inspection
            all_generations.append({
                "topic_id": topic.topic_id,
                "condition": condition,
                "text": synthesis.text,
                "cited_paper_ids": synthesis.cited_paper_ids,
                "retrieved_paper_ids": retrieved_ids,
                "method": synthesis.method,
                "model_name": synthesis.model_name,
            })

            logger.info(f"  Metrics: cit_P={eval_result.citation_precision:.3f}, "
                        f"cit_R={eval_result.citation_recall:.4f}, "
                        f"ROUGE-L={eval_result.rouge_l:.3f}, "
                        f"BERTScore={eval_result.bertscore_f1:.3f}, "
                        f"ret_P@10={eval_result.retrieval_precision_at_10:.3f}, "
                        f"ret_NDCG@10={eval_result.retrieval_ndcg_at_10:.3f}")

    # Save results
    results_dicts = results_to_dict(all_results)
    results_file = OUTPUT_DIR / "results.json"
    results_file.write_text(json.dumps(results_dicts, indent=2))
    logger.info(f"\nResults saved to {results_file}")

    # Save generations
    gen_file = OUTPUT_DIR / "generations.json"
    gen_file.write_text(json.dumps(all_generations, indent=2))
    logger.info(f"Generations saved to {gen_file}")

    # Save CSV table
    save_results_csv(results_dicts)

    # Generate figures
    generate_figures(results_dicts)

    return all_results


def save_results_csv(results: list[dict]):
    """Save results as a CSV table."""
    import pandas as pd
    df = pd.DataFrame(results)
    csv_path = OUTPUT_DIR / "results_table.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Results table saved to {csv_path}")

    # Print summary table
    print("\n=== Results Summary ===\n")
    summary = df.groupby("condition").agg({
        "citation_precision": "mean",
        "citation_recall": "mean",
        "rouge_l": "mean",
        "bertscore_f1": "mean",
        "retrieval_precision_at_10": "mean",
        "retrieval_ndcg_at_10": "mean",
    }).round(4)
    print(summary.to_string())
    print()


def generate_figures(results: list[dict]):
    """Generate analysis figures."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)

    # Color palette
    colors = {"bm25": "#2196F3", "dense": "#4CAF50", "no_retrieval": "#FF9800"}
    condition_labels = {"bm25": "BM25", "dense": "Dense", "no_retrieval": "No Retrieval"}

    # --- Figure 1: Bar chart of metrics by condition ---
    metrics = ["citation_precision", "citation_recall", "rouge_l", "bertscore_f1"]
    metric_labels = ["Citation\nPrecision", "Citation\nRecall", "ROUGE-L", "BERTScore\nF1"]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(metrics))
    width = 0.25

    for i, cond in enumerate(CONDITIONS):
        means = [df[df.condition == cond][m].mean() for m in metrics]
        stds = [df[df.condition == cond][m].std() for m in metrics]
        ax.bar(x + i * width, means, width, yerr=stds,
               label=condition_labels[cond], color=colors[cond],
               capsize=3, alpha=0.85)

    ax.set_ylabel("Score")
    ax.set_title("RAG Literature Synthesis: Metrics by Retrieval Condition")
    ax.set_xticks(x + width)
    ax.set_xticklabels(metric_labels)
    ax.legend()
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "metrics_by_condition.png", dpi=150)
    fig.savefig(FIGURES_DIR / "metrics_by_condition.pdf")
    plt.close()
    logger.info("Figure: metrics_by_condition.png")

    # --- Figure 2: Heatmap topic × condition for ROUGE-L ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, metric, title in zip(axes, ["rouge_l", "citation_precision"],
                                  ["ROUGE-L", "Citation Precision"]):
        pivot = df.pivot_table(values=metric, index="topic_id",
                               columns="condition", aggfunc="mean")
        pivot = pivot.reindex(columns=CONDITIONS)
        pivot.columns = [condition_labels[c] for c in CONDITIONS]

        im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto", vmin=0)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=8)
        ax.set_title(title)

        # Annotate cells
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                        fontsize=8, color="black" if val < 0.5 else "white")

        plt.colorbar(im, ax=ax, shrink=0.8)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "heatmap_topic_condition.png", dpi=150)
    fig.savefig(FIGURES_DIR / "heatmap_topic_condition.pdf")
    plt.close()
    logger.info("Figure: heatmap_topic_condition.png")

    # --- Figure 3: Retrieval quality ---
    ret_df = df[df.condition != "no_retrieval"]
    if not ret_df.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ret_metrics = ["retrieval_precision_at_10", "retrieval_ndcg_at_10"]
        ret_labels = ["P@10", "NDCG@10"]
        x = np.arange(len(ret_metrics))
        width = 0.3

        for i, cond in enumerate(["bm25", "dense"]):
            cond_df = ret_df[ret_df.condition == cond]
            means = [cond_df[m].mean() for m in ret_metrics]
            stds = [cond_df[m].std() for m in ret_metrics]
            ax.bar(x + i * width, means, width, yerr=stds,
                   label=condition_labels[cond], color=colors[cond],
                   capsize=3, alpha=0.85)

        ax.set_ylabel("Score")
        ax.set_title("Retrieval Quality: BM25 vs Dense")
        ax.set_xticks(x + width / 2)
        ax.set_xticklabels(ret_labels)
        ax.legend()
        ax.set_ylim(0, 1.0)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        fig.savefig(FIGURES_DIR / "retrieval_quality.png", dpi=150)
        fig.savefig(FIGURES_DIR / "retrieval_quality.pdf")
        plt.close()
        logger.info("Figure: retrieval_quality.png")

    logger.info(f"\nAll figures saved to {FIGURES_DIR}")


def main():
    parser = argparse.ArgumentParser(
        description="RAG Literature Synthesis Experiment"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Check structure without running experiment")
    parser.add_argument("--build-data", action="store_true",
                        help="Only download benchmark data")
    parser.add_argument("--no-bert", action="store_true",
                        help="Skip BERTScore computation (faster)")
    parser.add_argument("--log-dir", type=str, default=None,
                        help="Log directory path")
    args = parser.parse_args()

    log_dir = Path(args.log_dir) if args.log_dir else None
    setup_logging(log_dir)

    if args.dry_run:
        ok = dry_run()
        sys.exit(0 if ok else 1)

    if args.build_data:
        build_data()
        sys.exit(0)

    # Full experiment
    start = time.time()
    logger.info("Starting RAG literature synthesis experiment")

    # Ensure data exists
    if not (DATA_DIR / "manifest.json").exists():
        logger.info("No benchmark data found, building...")
        build_data()

    results = run_experiment(no_bert=args.no_bert)
    elapsed = time.time() - start
    logger.info(f"\nExperiment complete in {elapsed/60:.1f} minutes")
    logger.info(f"Total runs: {len(results)}")


if __name__ == "__main__":
    main()
