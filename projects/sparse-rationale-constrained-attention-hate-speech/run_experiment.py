"""Hydra entry point for sparse-hate-explain experiments.

Usage:
    python run_experiment.py +experiment=m4b_sel_sparsemax_mse_k6 seed=42
    python run_experiment.py +experiment=m0_baseline_softmax seed=0
"""
from __future__ import annotations

import logging

import hydra
from omegaconf import DictConfig, OmegaConf

from src.trainer.train import ExperimentConfig, run_training

logger = logging.getLogger(__name__)


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig) -> None:
    """Run one training job from a Hydra config."""
    logger.info(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    # Merge experiment sub-config with globals
    exp_cfg = OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)

    # Flatten: merge experiment keys into top-level
    if "experiment" in exp_cfg:
        exp_cfg.update(exp_cfg.pop("experiment"))

    experiment_config = ExperimentConfig(**{
        k: v for k, v in exp_cfg.items()
        if k in ExperimentConfig.__dataclass_fields__
    })

    run_training(experiment_config)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()
