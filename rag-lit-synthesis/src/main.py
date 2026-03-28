"""Main entry point for the RAG literature synthesis experiment."""

import hydra
from omegaconf import DictConfig


@hydra.main(config_path="../configs", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Run the experiment pipeline."""
    import json
    from pathlib import Path

    print(f"Project: {cfg.project.name}")
    print(f"Seed: {cfg.project.seed}")
    print(f"Retrieval: {cfg.retrieval.method}, top_k={cfg.retrieval.top_k}")
    print(f"Generator: {cfg.generation.model}")

    # Ensure output directory
    output_dir = Path(cfg.project.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Log config
    config_log = output_dir / "config.json"
    from omegaconf import OmegaConf
    config_log.write_text(json.dumps(OmegaConf.to_container(cfg), indent=2))

    print(f"Config saved to {config_log}")
    print("Pipeline ready. Run individual stages via CLI or experiment-runner.")


if __name__ == "__main__":
    main()
