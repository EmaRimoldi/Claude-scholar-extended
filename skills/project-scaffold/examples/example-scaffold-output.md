# Example: Scaffold Output

## Context

**Source**: `experiment-plan.md` from an interpretability study
**Research question**: Do in-context learning (ICL) task vectors in GPT-2 converge to a shared subspace across different synthetic tasks?
**Models**: GPT-2 Small, GPT-2 Medium (HuggingFace)
**Datasets**: Synthetic ICL tasks (linear regression, majority vote, parity)
**Metrics**: Cosine similarity, subspace overlap (Grassmann distance)

---

## Generated File Tree

```
icl-task-vectors/
├── pyproject.toml
├── Makefile
├── .gitignore
├── run_experiment.py
├── run/
│   └── conf/
│       ├── config.yaml
│       ├── dataset/               # (empty -- filled by experiment-data-builder)
│       ├── model/                 # (empty -- filled by model-setup)
│       └── experiment/
│           └── default.yaml
├── src/
│   ├── data_module/
│   │   ├── __init__.py
│   │   └── dataset/
│   │       └── __init__.py        # DatasetFactory + register_dataset
│   ├── model_module/
│   │   ├── __init__.py
│   │   └── model/
│   │       └── __init__.py        # ModelFactory + register_model
│   ├── metrics/
│   │   └── __init__.py            # MetricFactory + register_metric
│   └── utils/
│       ├── __init__.py
│       ├── seed.py
│       ├── environment.py
│       └── registry.py
└── tests/
    ├── __init__.py
    └── test_smoke.py
```

## Key File Contents

### pyproject.toml

HuggingFace group promoted to core dependencies because every experiment uses GPT-2 from `transformers`.

```toml
[project]
name = "icl-task-vectors"
version = "0.1.0"
description = "Investigating shared subspace convergence of ICL task vectors in GPT-2"
requires-python = ">=3.10"
dependencies = [
    "torch>=2.0",
    "numpy>=1.24",
    "hydra-core>=1.3",
    "omegaconf>=2.3",
    "matplotlib>=3.7",
    "pandas>=2.0",
    "scipy>=1.10",
    "transformers>=4.36",
    "accelerate>=0.25",
    "datasets>=2.16",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "ruff>=0.1",
    "mypy>=1.7",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4",
    "ruff>=0.1",
    "mypy>=1.7",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### src/data_module/dataset/__init__.py

```python
"""Dataset Factory and Registry."""
import os
import importlib
from typing import Dict, Type
from torch.utils.data import Dataset

DATASET_FACTORY: Dict[str, Type[Dataset]] = {}


def register_dataset(name: str):
    """Register a dataset class."""
    def decorator(cls):
        DATASET_FACTORY[name] = cls
        return cls
    return decorator


def DatasetFactory(name: str) -> Type[Dataset]:
    """Get dataset class by name."""
    dataset = DATASET_FACTORY.get(name)
    if dataset is None:
        raise ValueError(
            f"Dataset '{name}' not registered. "
            f"Available: {list(DATASET_FACTORY.keys())}"
        )
    return dataset


def import_modules(modules_dir: str, package: str) -> None:
    """Auto-import all Python modules in a directory."""
    for filename in os.listdir(modules_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            importlib.import_module(f"{package}.{module_name}")


_dir = os.path.dirname(__file__)
import_modules(_dir, __name__)
```

### run_experiment.py

```python
"""Main experiment entry point (Hydra-driven)."""
import logging

import hydra
from omegaconf import DictConfig, OmegaConf

from src.utils.seed import set_seed
from src.utils.environment import log_environment

logger = logging.getLogger(__name__)


@hydra.main(config_path="run/conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Run an experiment from a Hydra configuration."""
    set_seed(cfg.experiment.seed)
    env_info = log_environment()
    logger.info("Resolved config:\n%s", OmegaConf.to_yaml(cfg))

    # Placeholder: experiment logic goes here
    logger.info("Experiment finished.")


if __name__ == "__main__":
    main()
```

## Notes

- The `hf` optional group was merged into core `dependencies` because the experiment plan lists GPT-2 Small and GPT-2 Medium as required models, both loaded via HuggingFace `transformers`.
- `run/conf/dataset/` and `run/conf/model/` are intentionally empty. `experiment-data-builder` will create configs like `dataset/icl_linear_regression.yaml`; `model-setup` will create configs like `model/gpt2_small.yaml`.
- `src/metrics/` factory is wired but contains no concrete metrics yet. `measurement-implementation` will add files like `cosine_similarity.py` decorated with `@register_metric("cosine_similarity")`.
