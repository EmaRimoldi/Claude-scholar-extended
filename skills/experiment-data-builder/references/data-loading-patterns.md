# Data Loading Patterns

Reference for loading real-world datasets, wrapping standard benchmarks, and ensuring reproducibility through version pinning and fingerprinting.

---

## A. HuggingFace Datasets

### Basic Loading with Version Pinning

Always pin the dataset version to ensure reproducibility across machines and time:

```python
from datasets import load_dataset

# Pin by revision (commit hash on HuggingFace Hub)
dataset = load_dataset(
    "glue",
    "sst2",
    revision="fd8e832271b85e7f2e0ea3548e9407aa38b0e22b",
    trust_remote_code=False,
)

# Pin by specifying the exact version tag if available
dataset = load_dataset(
    "cais/mmlu",
    "all",
    revision="v1.0",
)
```

### Split Specification

Map experiment-plan.md split definitions to HuggingFace split syntax:

```python
# Standard splits
train_data = dataset["train"]
val_data = dataset["validation"]
test_data = dataset["test"]

# Percentage-based splits (when the dataset has no predefined val split)
split_dataset = load_dataset("my_dataset", split={
    "train": "train[:80%]",
    "val": "train[80%:90%]",
    "test": "train[90%:]",
})

# Cross-validation fold (e.g., fold 3 of 5)
n_folds = 5
fold = 3
train_split = f"train[:{fold * 20}%]+train[{(fold + 1) * 20}%:]"
val_split = f"train[{fold * 20}%:{(fold + 1) * 20}%]"
```

### Preprocessing Pipeline

Apply tokenization, normalization, and formatting in a reproducible `map()` call:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

def preprocess_fn(examples: dict) -> dict:
    """Tokenize text and format labels."""
    encoded = tokenizer(
        examples["sentence"],
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )
    encoded["labels"] = examples["label"]
    return encoded

processed = dataset.map(
    preprocess_fn,
    batched=True,
    remove_columns=dataset["train"].column_names,
    desc="Tokenizing",
)
processed.set_format("torch")
```

### Prompt Template Formatting for Few-Shot Evaluation

When evaluating language models with few-shot prompts:

```python
def format_few_shot_prompt(
    examples: list[dict],
    query: dict,
    template: str = "Input: {input}\nOutput: {output}",
    query_template: str = "Input: {input}\nOutput:",
) -> str:
    """Build a few-shot prompt from examples and a query.

    Args:
        examples: List of dicts with 'input' and 'output' keys.
        query: Dict with 'input' key.
        template: Template for each in-context example.
        query_template: Template for the query (no output).

    Returns:
        Formatted prompt string.
    """
    parts = [template.format(**ex) for ex in examples]
    parts.append(query_template.format(**query))
    return "\n\n".join(parts)
```

### Caching Processed Data

Save processed data to `data/processed/` with a fingerprint for cache invalidation:

```python
import hashlib
import json
from pathlib import Path

def save_processed_dataset(dataset, cache_dir: str, config: dict) -> Path:
    """Save processed dataset with config-based fingerprint.

    Args:
        dataset: HuggingFace Dataset object.
        cache_dir: Directory to save processed data.
        config: Dict of preprocessing parameters (for fingerprinting).

    Returns:
        Path to the saved dataset directory.
    """
    config_str = json.dumps(config, sort_keys=True)
    fingerprint = hashlib.sha256(config_str.encode()).hexdigest()[:12]
    save_path = Path(cache_dir) / f"processed_{fingerprint}"
    save_path.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(save_path))
    # Save config sidecar for provenance
    with open(save_path / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    return save_path
```

---

## B. Local File Loading

### CSV Loading with Type Inference

```python
import pandas as pd
import json
from pathlib import Path

def load_csv_dataset(
    path: str,
    target_column: str,
    feature_columns: list[str] | None = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> tuple[pd.DataFrame, dict]:
    """Load a CSV file with automatic type inference and schema export.

    Args:
        path: Path to CSV file.
        target_column: Name of the label/target column.
        feature_columns: Columns to use as features. None = all except target.
        delimiter: CSV delimiter.
        encoding: File encoding.

    Returns:
        df: Loaded DataFrame.
        schema: Inferred schema dict (column -> dtype string).
    """
    df = pd.read_csv(path, delimiter=delimiter, encoding=encoding)

    # Validate target column exists
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not in columns: {list(df.columns)}")

    # Select feature columns
    if feature_columns is None:
        feature_columns = [c for c in df.columns if c != target_column]

    # Infer and export schema
    schema = {col: str(df[col].dtype) for col in df.columns}

    # Save schema sidecar
    schema_path = Path(path).with_suffix(".schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)

    return df[feature_columns + [target_column]], schema
```

### JSON Loading

```python
def load_json_dataset(
    path: str,
    records_key: str | None = None,
) -> pd.DataFrame:
    """Load a JSON file into a DataFrame.

    Args:
        path: Path to JSON file.
        records_key: Key containing the records array (None if top-level is array).

    Returns:
        DataFrame of records.
    """
    with open(path) as f:
        data = json.load(f)
    if records_key is not None:
        data = data[records_key]
    return pd.DataFrame(data)
```

### Parquet Loading

```python
def load_parquet_dataset(path: str) -> pd.DataFrame:
    """Load a Parquet file with schema validation.

    Parquet preserves types natively, so type inference is not needed.
    """
    df = pd.read_parquet(path)
    return df
```

### Schema Validation

Re-validate a dataset against a previously saved schema to catch drift:

```python
def validate_schema(df: pd.DataFrame, schema_path: str) -> list[str]:
    """Validate DataFrame columns and dtypes against a saved schema.

    Returns:
        List of validation error messages (empty if valid).
    """
    with open(schema_path) as f:
        expected = json.load(f)

    errors = []
    for col, expected_dtype in expected.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        elif str(df[col].dtype) != expected_dtype:
            errors.append(f"Column '{col}': expected {expected_dtype}, got {df[col].dtype}")

    for col in df.columns:
        if col not in expected:
            errors.append(f"Unexpected column: {col}")

    return errors
```

---

## C. Benchmark Wrappers

### Pattern: Load Benchmark + Standard Metric

Thin wrapper that loads a standard benchmark, attaches its canonical metric, and verifies against known statistics:

```python
from datasets import load_dataset
import evaluate

class BenchmarkWrapper:
    """Thin wrapper around a standard benchmark with its canonical metric.

    Attributes:
        name: Benchmark name (e.g., "glue/sst2").
        dataset: Loaded HuggingFace Dataset.
        metric: Loaded evaluate metric.
        known_baseline: Published baseline accuracy for sanity checking.
    """

    def __init__(
        self,
        dataset_name: str,
        config_name: str | None,
        metric_name: str,
        revision: str | None = None,
        known_baseline: float | None = None,
    ):
        self.name = f"{dataset_name}/{config_name}" if config_name else dataset_name
        self.dataset = load_dataset(
            dataset_name,
            config_name,
            revision=revision,
            trust_remote_code=False,
        )
        self.metric = evaluate.load(metric_name)
        self.known_baseline = known_baseline

    def verify_loading(self) -> dict:
        """Verify that the dataset loaded correctly by checking sample count."""
        report = {}
        for split_name, split_data in self.dataset.items():
            report[split_name] = {
                "num_samples": len(split_data),
                "columns": split_data.column_names,
            }
        return report

    def compute_metric(
        self, predictions: list, references: list
    ) -> dict:
        """Compute the canonical metric for this benchmark."""
        return self.metric.compute(predictions=predictions, references=references)
```

### Common Benchmarks Reference

| Benchmark | HuggingFace ID | Config | Metric | Published Baseline (BERT-base) |
|-----------|---------------|--------|--------|-------------------------------|
| SST-2 | `glue` | `sst2` | `accuracy` | 93.5% |
| MNLI | `glue` | `mnli` | `accuracy` | 84.6% |
| QQP | `glue` | `qqp` | `f1` / `accuracy` | 71.2% F1 |
| MRPC | `glue` | `mrpc` | `f1` / `accuracy` | 88.9% F1 |
| SuperGLUE BoolQ | `super_glue` | `boolq` | `accuracy` | 77.7% |
| MMLU | `cais/mmlu` | `all` | `accuracy` | 43.5% (GPT-3) |

---

## D. Dataset Versioning and Fingerprinting

### Hash-Based Fingerprinting

Record a deterministic fingerprint of the dataset contents so that future loads can verify identity:

```python
import hashlib
import torch
from torch.utils.data import Dataset

def compute_dataset_fingerprint(
    dataset: Dataset,
    n_samples: int = 100,
    seed: int = 0,
) -> str:
    """Compute a SHA-256 fingerprint of a dataset by hashing a sample of items.

    Args:
        dataset: Any torch Dataset with __getitem__ and __len__.
        n_samples: Number of items to include in the fingerprint.
        seed: Seed for selecting sample indices.

    Returns:
        Hex digest string (first 16 chars).
    """
    g = torch.Generator().manual_seed(seed)
    n = min(n_samples, len(dataset))
    indices = torch.randperm(len(dataset), generator=g)[:n].tolist()

    hasher = hashlib.sha256()
    for idx in sorted(indices):
        item = dataset[idx]
        if isinstance(item, tuple):
            for t in item:
                if isinstance(t, torch.Tensor):
                    hasher.update(t.numpy().tobytes())
        elif isinstance(item, dict):
            for k in sorted(item.keys()):
                v = item[k]
                if isinstance(v, torch.Tensor):
                    hasher.update(v.numpy().tobytes())

    return hasher.hexdigest()[:16]
```

### Recording Fingerprints in Config

Add the fingerprint to the Hydra config for reproducibility auditing:

```yaml
# run/conf/dataset/sst2.yaml
name: "sst2"
type: "benchmark"
source: "glue"
config_name: "sst2"
revision: "fd8e832271b85e7f2e0ea3548e9407aa38b0e22b"
fingerprint: "a3b4c5d6e7f80912"   # auto-populated after first load
split:
  train: "train"
  val: "validation"
  test: "test"
max_length: 128
```

### Version Mismatch Detection

On every load, recompute the fingerprint and compare against the stored value:

```python
def verify_fingerprint(
    dataset: Dataset,
    expected: str,
    n_samples: int = 100,
) -> bool:
    """Check that a dataset matches its expected fingerprint.

    Returns:
        True if fingerprints match, False otherwise.
    """
    actual = compute_dataset_fingerprint(dataset, n_samples=n_samples)
    if actual != expected:
        print(f"WARNING: Dataset fingerprint mismatch. Expected {expected}, got {actual}.")
        print("This may indicate the dataset version has changed.")
        return False
    return True
```
