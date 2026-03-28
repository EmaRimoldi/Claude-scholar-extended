# Example: Phase Gate Evaluation and State Update

## Context

After Phase 1 (quick validation) completes, the runner loads results from `outputs/`, evaluates the gate criterion from `experiment-plan.md`, and updates `experiment-state.json`.

---

## Phase Gate Evaluation Function

```python
import json
import glob
import numpy as np
from pathlib import Path
from datetime import datetime, timezone


def evaluate_phase_gate(
    phase: str,
    outputs_dir: str,
    gate_criterion: dict,
    baseline_method: str,
    proposed_method: str,
    primary_metric: str = "balanced_accuracy",
) -> dict:
    """
    Evaluate a phase gate by comparing proposed vs baseline results.

    Args:
        phase: Phase identifier (e.g., "phase_1").
        outputs_dir: Root outputs directory.
        gate_criterion: Dict with "metric", "threshold", "direction" keys.
        baseline_method: Name of the baseline method in run IDs.
        proposed_method: Name of the proposed method in run IDs.
        primary_metric: Key to read from metrics.json.

    Returns:
        Gate evaluation result dict.
    """
    # Collect metrics for proposed and baseline runs in this phase
    phase_prefix = phase.replace("phase_", "p")  # "phase_1" -> "p1"

    proposed_scores = _load_scores(
        outputs_dir, f"{phase_prefix}_{proposed_method}_*", primary_metric
    )
    baseline_scores = _load_scores(
        outputs_dir, f"{phase_prefix}_{baseline_method}_*", primary_metric
    )

    if not proposed_scores or not baseline_scores:
        return {
            "decision": "DIAGNOSE",
            "reason": f"Missing results: {len(proposed_scores)} proposed, {len(baseline_scores)} baseline",
            "timestamp": _now(),
        }

    proposed_mean = np.mean(proposed_scores)
    proposed_std = np.std(proposed_scores)
    baseline_mean = np.mean(baseline_scores)
    baseline_std = np.std(baseline_scores)
    improvement = proposed_mean - baseline_mean
    threshold = gate_criterion["threshold"]

    # Decide: PROCEED, STOP, or DIAGNOSE
    if improvement >= threshold:
        decision = "PROCEED"
        reason = f"Improvement {improvement:.4f} >= threshold {threshold}"
    elif improvement < 0:
        decision = "STOP"
        reason = f"Proposed underperforms baseline by {abs(improvement):.4f}"
    else:
        decision = "DIAGNOSE"
        reason = f"Improvement {improvement:.4f} < threshold {threshold}, but positive"

    return {
        "phase": phase,
        "decision": decision,
        "reason": reason,
        "proposed": {"mean": round(proposed_mean, 4), "std": round(proposed_std, 4), "n": len(proposed_scores)},
        "baseline": {"mean": round(baseline_mean, 4), "std": round(baseline_std, 4), "n": len(baseline_scores)},
        "improvement": round(improvement, 4),
        "threshold": threshold,
        "timestamp": _now(),
    }


def _load_scores(outputs_dir: str, pattern: str, metric_key: str) -> list[float]:
    """Load metric values from all matching run directories."""
    scores = []
    for metrics_file in glob.glob(f"{outputs_dir}/{pattern}/metrics.json"):
        with open(metrics_file) as f:
            metrics = json.load(f)
        if metric_key in metrics:
            scores.append(float(metrics[metric_key]))
    return scores


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
```

## Updating experiment-state.json

```python
def update_state_after_gate(
    state_path: str,
    phase: str,
    gate_result: dict,
    gpu_hours_used: float,
) -> None:
    """
    Update experiment-state.json with phase gate results.

    Args:
        state_path: Path to experiment-state.json.
        phase: Phase identifier (e.g., "phase_1").
        gate_result: Output from evaluate_phase_gate().
        gpu_hours_used: GPU-hours consumed by this phase.
    """
    with open(state_path) as f:
        state = json.load(f)

    # Update resource tracking
    state["resource_budget"]["used_gpu_hours"] += gpu_hours_used
    if state["resource_budget"]["total_gpu_hours"] is not None:
        state["resource_budget"]["remaining_gpu_hours"] = (
            state["resource_budget"]["total_gpu_hours"]
            - state["resource_budget"]["used_gpu_hours"]
        )

    # Record phase result
    if "phases" not in state:
        state["phases"] = {}
    state["phases"][phase] = {
        "status": "completed",
        "gate_result": gate_result["decision"],
        "gate_metric": {
            "proposed": gate_result["proposed"]["mean"],
            "baseline": gate_result["baseline"]["mean"],
            "improvement": gate_result["improvement"],
        },
        "gpu_hours_used": gpu_hours_used,
        "completed_at": gate_result["timestamp"],
    }

    # Transition overall status based on gate decision
    if gate_result["decision"] == "PROCEED":
        state["status"] = "running"
    elif gate_result["decision"] == "STOP":
        state["status"] = "diagnosing"
    else:  # DIAGNOSE
        state["status"] = "diagnosing"

    # Append to history
    state["history"].append({
        "event": f"{phase}_gate",
        "decision": gate_result["decision"],
        "reason": gate_result["reason"],
        "timestamp": gate_result["timestamp"],
    })

    state["updated"] = _now()

    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
```
