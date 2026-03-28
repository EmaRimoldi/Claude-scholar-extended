---
name: model-setup
description: This skill should be used when the user asks to "load a model", "inspect model architecture", "extract activations", "attach hooks", "ablate attention heads", "zero ablation", "mean ablation", "activation patching", "compare model representations", "model surgery", "freeze layers", "inspect layers", or when setting up models for any experiment. Handles loading, configuring, introspecting, and surgically modifying models from any source.
version: 0.1.0
tags: [ML, Model, Interpretability, Hooks, Ablation, Architecture]
---

# Model Setup

Handles loading, configuring, introspecting, and surgically modifying models. This skill is experiment-agnostic -- the same procedures apply to any experiment that needs to look inside or modify a model. It covers the full lifecycle from loading a pretrained model through attaching hooks, identifying components, performing ablations, and comparing representations across models.

## Core Features

### 1. Model Loading

Load models from multiple sources with correct configuration:

- **HuggingFace Hub**: `AutoModel.from_pretrained()` with correct config, dtype, device placement
  - Specify `torch_dtype` (float32, float16, bfloat16) based on available hardware
  - Use `device_map="auto"` for models that exceed single-GPU memory
  - Pass `trust_remote_code=True` only when loading custom architectures from trusted sources
  - Handle tokenizer loading in parallel: `AutoTokenizer.from_pretrained()`
- **Local checkpoints**: `torch.load()` with `map_location` handling
  - Detect checkpoint format: full state dict, sharded state dict, or wrapped checkpoint with optimizer state
  - Extract model state dict from training checkpoint: `checkpoint["model_state_dict"]`
  - Handle dtype mismatches between checkpoint and target device
- **Custom architectures**: Use `@register_model` pattern from `architecture-design`
  - Model class registered via decorator, instantiated via `ModelFactory(name)`
  - Config-driven: `__init__` accepts `cfg` parameter, all hyperparameters from config
  - Compatible with Factory/Registry wiring in `src/model_module/`
- **Multi-GPU**: For large models that do not fit on a single GPU
  - `device_map="auto"` with `accelerate` for automatic sharding
  - Manual device placement for custom sharding strategies
  - `torch.nn.DataParallel` or `DistributedDataParallel` for data parallelism
  - Memory estimation before loading: parameter count x bytes per parameter

### 2. Architecture Discovery

Programmatically inspect any model to understand its structure:

- **Module enumeration**: `model.named_modules()` to list all layers with their types and shapes
  - Distinguish container modules (Sequential, ModuleList) from leaf modules (Linear, LayerNorm)
  - Identify attention layers, MLP layers, embedding layers, normalization layers
  - Report parameter count per module and total parameter count
- **Transformer structure identification**:
  - Number of layers (transformer blocks)
  - Number of attention heads per layer, head dimension, hidden dimension
  - Vocabulary size, max sequence length, positional encoding type
  - Whether the model uses multi-head attention, multi-query attention, or grouped-query attention
- **Module naming conventions**: Handle differences across implementations
  - HuggingFace GPT-2: `transformer.h.{i}.attn`, `transformer.h.{i}.mlp`
  - HuggingFace LLaMA: `model.layers.{i}.self_attn`, `model.layers.{i}.mlp`
  - HuggingFace BERT: `encoder.layer.{i}.attention`, `encoder.layer.{i}.intermediate`
  - Custom models: user-defined naming discovered via `named_modules()`
- **Output**: Generate structured `model-architecture.json` with:
  - Model class name, total parameter count, dtype
  - Per-layer entries: index, module name, module type, input/output shapes, parameter count
  - Summary: number of attention layers, MLP layers, embedding layers, normalization layers

### 3. Hook Infrastructure

Attach hooks to extract intermediate representations during forward passes:

- **Forward hooks**: Capture layer inputs, outputs, attention patterns, key/query/value vectors
  - `module.register_forward_hook(fn)` with signature `fn(module, input, output)`
  - Selective extraction: only save specified tensors to manage memory
  - Support for nested extraction: hook on attention module to get Q, K, V, attention weights
- **Hook lifecycle management**: Register, use, remove with clean guarantees
  - Context manager pattern (`ActivationCache`) for automatic cleanup on exit
  - Explicit removal via hook handles: `handle.remove()`
  - Guard against hook leaks: always remove hooks even on exception
- **Memory-efficient caching**:
  - Detach tensors from computation graph before caching: `.detach()`
  - Move cached tensors to CPU to free GPU memory: `.cpu()`
  - Batch accumulation: append results across batches into a list, concatenate at the end
  - Gradient checkpointing interaction: hooks still fire, but intermediate activations may be recomputed
- **Batch processing**: Accumulate hook results across multiple batches
  - Pre-allocate storage if total size is known
  - Stream to disk for very large extraction jobs (memory-mapped files)

### 4. Component Identification

Identify specific components and their roles programmatically:

- **Attention head classification**:
  - Induction heads: measure prefix matching score (does head i attend to token j when token j-1 matches the current token's previous context?)
  - Copy heads: measure whether the head copies information from attended positions
  - Positional heads: measure whether attention pattern correlates with relative position
  - Method: run a set of diagnostic inputs, collect per-head attention patterns, compute classification scores
- **Neuron activation patterns**:
  - Identify neurons that activate for specific features (e.g., syntax, semantics, specific tokens)
  - Max-activating dataset examples: for each neuron, find the inputs that maximally activate it
  - Activation histograms: distribution of neuron activations across a reference dataset
- **Layer role analysis**:
  - Contribution of each layer to the final output (via logit lens or tuned lens)
  - Residual stream decomposition: which layers contribute most to a specific output direction
  - Early vs. late layer specialization: measure representational similarity across layers
- **Output**: Component identification report with:
  - Classified head indices (head_type, layer, head_index, score)
  - Neuron indices with activation statistics
  - Layer contribution scores for a given task or output

### 5. Ablation Operations

Modify model internals to test component necessity:

- **Zero ablation**: Set specific attention head outputs or MLP outputs to zero
  - Attach a forward hook that replaces the output tensor with zeros
  - Apply to individual heads by zeroing the appropriate slice of the multi-head output
  - Apply to entire layers by zeroing the full output
- **Mean ablation**: Replace component output with its mean across a reference dataset
  - First pass: collect component outputs on a reference dataset, compute the mean
  - Second pass: replace component output with the precomputed mean via hook
  - More informative than zero ablation because it preserves the expected scale
- **Activation patching**: Replace one component's output with the output from a different input
  - Run model on clean input, cache target component output
  - Run model on corrupted input, replace target component output with cached clean output
  - Measures the causal effect of that component on the difference between clean and corrupted
- **Reversible ablation**: Context manager that restores original weights/hooks on exit
  - Save original state before ablation, restore on `__exit__`
  - Works with both hook-based ablation (remove hooks) and weight-based ablation (restore weights)
  - Safe for nested ablations: each context manager tracks its own modifications
- **Surgical fine-tuning**: Freeze all parameters except specified components
  - `param.requires_grad_(False)` for all parameters, then selectively re-enable
  - Target specific layers, heads, or neurons for fine-tuning
  - Verify frozen parameters are not updated after an optimizer step

### 6. Model Comparison

Compare two models' internal representations:

- **CKA (Centered Kernel Alignment)**: Compare layer representations between two models
  - Compute linear CKA between activation matrices from two models on the same inputs
  - Produces a layer x layer similarity matrix
  - Identifies which layers in model A correspond to which layers in model B
- **Representational Similarity Analysis (RSA)**:
  - Compute pairwise distance matrix (cosine, Euclidean) for each model's representations
  - Correlate the two distance matrices (Spearman correlation)
  - Compare at each layer to track where representations diverge
- **Per-layer cosine similarity**:
  - For the same input, compute cosine similarity between layer i activations in model A and model B
  - Requires models to have the same hidden dimension (or project to a common space)
  - Useful for comparing a model before and after fine-tuning

Comparison workflow:
1. Load both models (can be different checkpoints of the same architecture, or different architectures)
2. Run the same set of inputs through both models, extracting activations at corresponding layers using hook infrastructure
3. Compute the chosen similarity metric for each layer pair
4. Output a comparison matrix (model A layers x model B layers) and summary statistics
5. Identify the most similar and most divergent layer pairs

## Model Loading Procedure

Step-by-step procedure for loading any model:

1. **Determine source**: HuggingFace Hub ID, local checkpoint path, or registered model name
2. **Read config**: For HuggingFace models, use `AutoConfig.from_pretrained()` to inspect architecture before loading weights
3. **Estimate memory**: `num_parameters * bytes_per_param` (4 bytes for float32, 2 for float16). Compare against available GPU memory.
4. **Choose dtype**: `torch.float32` for analysis and training, `torch.float16` or `torch.bfloat16` for inference on supported hardware
5. **Choose device placement**: Single GPU (`cuda:0`), multi-GPU (`device_map="auto"`), or CPU for small models
6. **Load model**: `AutoModel.from_pretrained()` or `torch.load()` with appropriate arguments
7. **Set mode**: `model.eval()` for analysis and inference; disable gradient checkpointing if extracting activations
8. **Verify**: Run a single forward pass with a dummy input, check output shape and dtype
9. **Discover architecture**: Run architecture discovery to generate `model-architecture.json`
10. **Record**: Log model name, source, dtype, device, parameter count to experiment config

## Input Modes

### Mode A: Pipeline (from predecessor)

1. **Experiment plan** -- from `experiment-design` output (`experiment-plan.md`)
2. **Scaffolded project** -- from `project-scaffold` output (`src/model_module/` exists)
3. The skill reads the plan to determine: which model(s) to load, from which source, what introspection is needed

### Mode B: Standalone (manual)

1. **Model identifier** -- user provides a HuggingFace model name, local checkpoint path, or custom architecture name
2. **Task description** -- user describes what they want to do with the model (inspect, hook, ablate, compare)
3. The skill generates the appropriate code in `src/model_module/`

When running in Mode B, state: "No experiment-plan.md found. Setting up model from user-provided description."

## Outputs

- **Model loading code**: `src/model_module/model/` with loading functions and `@register_model` wrappers
- **Hydra model config**: `run/conf/model/{model_name}.yaml` with model hyperparameters
- **Architecture report**: `model-architecture.json` with full model structure
- **Hook utilities**: `src/model_module/hooks.py` with `ActivationCache` context manager and hook helpers
- **Ablation utilities**: `src/model_module/ablation.py` with zero/mean/patch ablation and reversible context manager
- **Comparison utilities**: `src/model_module/comparison.py` with CKA, RSA, and cosine similarity functions

## Hydra Configuration

When operating in pipeline mode, generate `run/conf/model/` YAML files for each model:

```yaml
# run/conf/model/gpt2.yaml
model:
  name: gpt2
  source: huggingface            # huggingface | local | registry
  pretrained: gpt2               # Hub ID, local path, or registered name
  dtype: float32                 # float32 | float16 | bfloat16
  device_map: null               # null (single GPU) | auto (multi-GPU)
  eval_mode: true
  trust_remote_code: false
  hooks:
    enabled: false
    layers: []                   # List of module paths to hook
    cache_device: cpu            # cpu | cuda
    detach: true
  ablation:
    enabled: false
    method: null                 # zero | mean | patch
    targets: []                  # List of {layer, head_index} dicts
```

For custom models using the `@register_model` pattern:

```yaml
# run/conf/model/custom_model.yaml
model:
  name: MyCustomModel
  source: registry               # Uses ModelFactory from architecture-design
  hidden_dim: 768
  num_layers: 12
  num_heads: 12
  dropout: 0.1
  eval_mode: true
```

## Verification Checklist

After model setup, verify:

- [ ] Model loads without error on target device
- [ ] `model.eval()` produces deterministic output for the same input
- [ ] Hook extraction returns tensors with expected shapes
- [ ] Hook cleanup leaves no residual hooks: `len(list(model._forward_hooks))` is zero
- [ ] Ablation changes model output (sanity check that ablation is applied)
- [ ] Reversible ablation restores original output exactly (within floating-point tolerance)
- [ ] `model-architecture.json` matches manual inspection of `print(model)`

## When to Use

### Scenarios for This Skill

1. **After project scaffolding** -- project structure exists, need to load and configure the model
2. **Before running experiments** -- model must be loadable and introspectable
3. **Interpretability research** -- need hooks for activation extraction, component identification, or ablation experiments
4. **Model comparison** -- comparing two checkpoints, or pre- vs. post-fine-tuning representations
5. **Debugging model behavior** -- inspect intermediate representations to understand unexpected outputs
6. **Transfer learning setup** -- need to freeze layers and identify which components to fine-tune
7. **Mechanistic analysis** -- need to identify circuit components (induction heads, copy heads) in a transformer

### Typical Workflow

```
project-scaffold -> [model-setup] -> measurement-implementation -> experiment-runner
                        OR
user provides model -> [model-setup] -> experiment code
```

**Output Files:**
- Model loading and configuration code in `src/model_module/`
- `model-architecture.json` architecture report
- Hydra config in `run/conf/model/`

## Integration with Other Systems

### Complete Pipeline

```
experiment-plan.md
    |
project-scaffold (Create project)
    |
    +-- model-setup (Load, inspect, hook models)  <-- THIS SKILL
    |
    +-- measurement-implementation (Metrics, probes, measurements using hooks from model-setup)
    |
    +-- experiment-runner (Execute experiments with configured models)
    |
    +-- setup-validation (Verify model loading, hooks, ablation)
```

### Data Flow

- **Depends on**: `project-scaffold` (writes into `src/model_module/`)
- **Feeds into**: `measurement-implementation` (provides activation extraction via hooks), `experiment-runner` (models ready for evaluation), `setup-validation` (model loading verification)
- **Extends**: `architecture-design` (uses `@register_model` for custom models)
- **Hook activation**: Keywords "model loading", "hook", "ablation", "model surgery", "activation", "attention heads" in `skill-forced-eval.js`
- **New command**: `/setup-model`

### Key Configuration

- **Default dtype**: `torch.float32` (override with `model.dtype` in config)
- **Default device**: `cuda` if available, else `cpu`
- **Hook memory policy**: Detach and move to CPU by default
- **Checkpoint format**: Auto-detect full state dict vs. training checkpoint
- **Ablation default**: Reversible (context manager) unless permanent modification is requested
- **Architecture report**: Always generated on first model load

## Additional Resources

### Reference Files

Detailed methodology guides, loaded on demand:

- **`references/hook-patterns.md`** -- Hook Patterns Reference
  - Forward hook API and signature
  - Context manager pattern for activation caching
  - Memory management strategies
  - Multi-head attention extraction
  - Common hook pitfalls and solutions

- **`references/architecture-discovery.md`** -- Architecture Discovery Reference
  - Using `named_modules()` and `named_parameters()` to map model structure
  - Identifying transformer components by type
  - Handling different transformer implementations
  - Generating `model-architecture.json`

- **`references/ablation-patterns.md`** -- Ablation Patterns Reference
  - Zero ablation implementation
  - Mean ablation implementation
  - Activation patching implementation
  - Reversible ablation context manager
  - Choosing the right ablation method
  - Verifying ablation correctness

### Example Files

Complete working examples:

- **`examples/example-hook-extraction.py`** -- Hook Extraction Example
  - Load GPT-2 from HuggingFace
  - Attach hooks to all attention layers
  - Run a forward pass and extract per-head attention patterns
  - Print shapes of extracted tensors

- **`examples/example-ablation.py`** -- Ablation Example
  - Load a model and identify a specific attention head
  - Zero-ablate it using a reversible context manager
  - Verify outputs differ during ablation and match after restoration
