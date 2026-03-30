#!/usr/bin/env python3
"""
method_reconcile.py — Step 25: Method-Code Consistency Check.

Extracts methodological claims (hyperparameters, architecture specs, training
procedures, evaluation protocols) from the experiment plan and cross-references
them against actual config files and training logs.

Usage:
    python scripts/method_reconcile.py \
        --experiment-plan  $PROJECT_DIR/experiment-plan.md \
        --configs          $PROJECT_DIR/configs/ \
        --runs             $PROJECT_DIR/runs/ \
        --experiment-state $PROJECT_DIR/experiment-state.json \
        --output           $PROJECT_DIR/method-reconciliation-report.md

Exit codes:
    0 — No CRITICAL or MAJOR discrepancies
    1 — One or more CRITICAL/MAJOR discrepancies found (hard block)
    2 — Input error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------

def load_yaml_like(text: str) -> dict[str, str]:
    """
    Lightweight YAML/TOML key-value extractor (no full parser needed —
    we only want hyperparameter scalar values).
    Returns {key: value_str} for simple key: value lines.
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        # Match patterns like:  lr: 1e-4  OR  learning_rate = 0.001
        m = re.match(
            r"^\s*([a-zA-Z][a-zA-Z0-9_.-]*)[\s:=]+([^\s{}\[\]#,]+)",
            line.strip(),
        )
        if m:
            key = m.group(1).lower().replace("-", "_")
            val = m.group(2).strip().strip('"').strip("'")
            result[key] = val
    return result


def load_json_flat(path: Path) -> dict[str, str]:
    """Load a JSON file and flatten scalar values to {key: str}."""
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    result: dict[str, str] = {}

    def flatten(obj: object, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                flatten(v, f"{prefix}{k}." if prefix else k)
        elif isinstance(obj, (str, int, float, bool)):
            key = prefix.rstrip(".").lower().replace("-", "_")
            result[key] = str(obj)

    flatten(data)
    return result


# ---------------------------------------------------------------------------
# Claim extraction from experiment-plan.md
# ---------------------------------------------------------------------------

_HYPER_KEYS = {
    "learning_rate", "lr", "batch_size", "epochs", "num_epochs",
    "hidden_size", "hidden_dim", "num_layers", "num_heads", "attention_heads",
    "dropout", "dropout_rate", "weight_decay", "optimizer", "scheduler",
    "warmup_steps", "warmup_ratio", "max_length", "seq_len", "seed",
    "gradient_clip", "grad_clip", "accumulation_steps", "precision",
    "embedding_dim", "vocab_size", "num_classes", "temperature",
}

_HYPER_PATTERN = re.compile(
    r"([a-zA-Z][a-zA-Z0-9_ /-]*)[\s:=]+([0-9eE+\-.]+[kKmMgG]?|True|False|adam\w*|sgd|none)",
    re.IGNORECASE,
)


def extract_plan_claims(plan_text: str) -> dict[str, str]:
    """
    Extract hyperparameter-style key-value pairs from experiment-plan.md.
    Returns {normalized_key: value_str}.
    """
    claims: dict[str, str] = {}
    for m in _HYPER_PATTERN.finditer(plan_text):
        raw_key = m.group(1).strip().lower().replace(" ", "_").replace("/", "_")
        # Keep only keys that look like real hyperparameters
        if any(hk in raw_key for hk in _HYPER_KEYS) or raw_key in _HYPER_KEYS:
            claims[raw_key] = m.group(2).strip()
    return claims


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_all_configs(configs_dir: Path) -> dict[str, dict[str, str]]:
    """Load all .yaml, .yml, .json config files. Returns {filename: {key: value}}."""
    result: dict[str, dict[str, str]] = {}
    if not configs_dir.exists():
        return result
    for ext in ("*.yaml", "*.yml", "*.json", "*.toml", "*.cfg", "*.ini"):
        for f in configs_dir.rglob(ext):
            text = f.read_text(encoding="utf-8", errors="ignore")
            if f.suffix in (".json",):
                vals = load_json_flat(f)
            else:
                vals = load_yaml_like(text)
            if vals:
                result[str(f)] = vals
    return result


def merge_config_view(configs: dict[str, dict[str, str]]) -> dict[str, tuple[str, str]]:
    """
    Merge all config files into a single view.
    Returns {key: (value, source_file)}.
    Last-write wins when keys conflict across files (files are sorted for determinism).
    """
    merged: dict[str, tuple[str, str]] = {}
    for filename in sorted(configs):
        for k, v in configs[filename].items():
            merged[k] = (v, filename)
    return merged


# ---------------------------------------------------------------------------
# Log scanning
# ---------------------------------------------------------------------------

def scan_training_logs(runs_dir: Path) -> dict[str, str]:
    """
    Scan training logs for logged hyperparameters.
    Looks for patterns like:  lr=1e-4  or  learning_rate: 0.001  in .log/.txt files.
    Returns {key: value} from the most recent log found.
    """
    logged: dict[str, str] = {}
    if not runs_dir.exists():
        return logged

    log_files = sorted(
        list(runs_dir.rglob("*.log")) + list(runs_dir.rglob("*.txt")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Also look for trainer_state.json or training_args.json (HF Trainer)
    for state_file in runs_dir.rglob("trainer_state.json"):
        logged.update(load_json_flat(state_file))
    for args_file in runs_dir.rglob("training_args.json"):
        logged.update(load_json_flat(args_file))

    # Parse the most recent 5 log files
    for log_file in log_files[:5]:
        text = log_file.read_text(encoding="utf-8", errors="ignore")
        for m in _HYPER_PATTERN.finditer(text):
            raw_key = m.group(1).strip().lower().replace(" ", "_")
            if any(hk in raw_key for hk in _HYPER_KEYS) or raw_key in _HYPER_KEYS:
                logged[raw_key] = m.group(2).strip()

    return logged


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def values_match(v1: str, v2: str) -> bool:
    """Compare two hyperparameter values, handling numeric equivalence."""
    if v1.lower() == v2.lower():
        return True
    try:
        f1 = float(v1)
        f2 = float(v2)
        return abs(f1 - f2) / max(abs(f1), abs(f2), 1e-12) < 0.01
    except (ValueError, ZeroDivisionError):
        return False


def reconcile(
    plan_claims: dict[str, str],
    config_view: dict[str, tuple[str, str]],
    log_view: dict[str, str],
) -> list[dict]:
    """
    Compare plan claims against config/log values.
    Returns list of {key, plan_value, actual_value, source, status, severity}.
    Status: MATCH | DISCREPANCY | MISSING_DETAIL | NOT_IN_PLAN
    """
    entries: list[dict] = []
    seen: set[str] = set()

    for key, plan_val in plan_claims.items():
        seen.add(key)
        actual_val: str | None = None
        source: str = "not found"

        # Check config files first (authoritative)
        if key in config_view:
            actual_val, source = config_view[key]
        # Also check with common aliases
        elif key.replace("_rate", "") in config_view:
            actual_val, source = config_view[key.replace("_rate", "")]
        elif f"train_{key}" in config_view:
            actual_val, source = config_view[f"train_{key}"]
        # Fall back to logs
        elif key in log_view:
            actual_val, source = log_view[key], "training_log"

        if actual_val is None:
            entries.append({
                "key": key,
                "plan_value": plan_val,
                "actual_value": None,
                "source": "not_found",
                "status": "MISSING_DETAIL",
                "severity": "MINOR",
                "note": "Planned value not found in any config or log. Confirm it is set correctly.",
            })
        elif values_match(plan_val, actual_val):
            entries.append({
                "key": key,
                "plan_value": plan_val,
                "actual_value": actual_val,
                "source": source,
                "status": "MATCH",
                "severity": "OK",
                "note": "",
            })
        else:
            entries.append({
                "key": key,
                "plan_value": plan_val,
                "actual_value": actual_val,
                "source": source,
                "status": "DISCREPANCY",
                "severity": "CRITICAL",
                "note": (
                    f"Manuscript would say '{plan_val}' but config/log shows '{actual_val}'. "
                    "Resolve: either update the config (if plan was wrong) or update "
                    "the manuscript description (if config was correct)."
                ),
            })

    # Report values in configs that are not in the plan (MISSING_DETAIL)
    for key, (val, source) in config_view.items():
        if key not in seen and key in _HYPER_KEYS:
            entries.append({
                "key": key,
                "plan_value": None,
                "actual_value": val,
                "source": source,
                "status": "MISSING_DETAIL",
                "severity": "MINOR",
                "note": (
                    f"Config has {key}={val} but it was not captured in the experiment plan. "
                    "Add to the manuscript methods description if relevant."
                ),
            })

    return entries


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(entries: list[dict], output_path: Path) -> None:
    discrepancies = [e for e in entries if e["status"] == "DISCREPANCY"]
    matches = [e for e in entries if e["status"] == "MATCH"]
    missing = [e for e in entries if e["status"] == "MISSING_DETAIL"]

    block = bool(discrepancies)
    result = "BLOCK" if block else ("WARN" if missing else "PASS")

    lines = [
        "# Method-Code Reconciliation Report (Step 25)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Matches:** {len(matches)}",
        f"**Discrepancies (CRITICAL):** {len(discrepancies)}",
        f"**Missing details:** {len(missing)}",
        "",
        f"## Result: {result}",
        "",
    ]

    if result == "PASS":
        lines += [
            "All claimed hyperparameters match their config/log counterparts. "
            "Method descriptions are consistent with execution.",
        ]

    if discrepancies:
        lines += [
            "",
            "## Discrepancies (Hard Block — must resolve before manuscript production)",
            "",
            "| Key | Plan says | Config/log says | Source | Action |",
            "|-----|-----------|-----------------|--------|--------|",
        ]
        for e in discrepancies:
            lines.append(
                f"| `{e['key']}` | `{e['plan_value']}` | `{e['actual_value']}` "
                f"| {e['source']} | {e['note'][:80]} |"
            )
        lines.append("")

    if missing:
        lines += [
            "",
            "## Missing Details (Informational)",
            "",
        ]
        for e in missing:
            if e["plan_value"] is None:
                lines.append(
                    f"- **`{e['key']}`**: Config/log shows `{e['actual_value']}` "
                    f"(from `{e['source']}`). {e['note']}"
                )
            else:
                lines.append(
                    f"- **`{e['key']}`**: Plan says `{e['plan_value']}` but not found in "
                    f"any config or log. {e['note']}"
                )
        lines.append("")

    if matches:
        lines += [
            "",
            "## Confirmed Matches",
            "",
            "| Key | Value | Source |",
            "|-----|-------|--------|",
        ]
        for e in matches:
            lines.append(f"| `{e['key']}` | `{e['actual_value']}` | {e['source']} |")
        lines.append("")

    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 25: Cross-reference method descriptions against configs and logs"
    )
    parser.add_argument("--experiment-plan", required=True)
    parser.add_argument("--configs", required=True, help="Path to configs/ directory")
    parser.add_argument("--runs", default="", help="Path to runs/ directory (training logs)")
    parser.add_argument("--experiment-state", default="", help="Path to experiment-state.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    plan_path = Path(args.experiment_plan)
    configs_dir = Path(args.configs)

    if not plan_path.exists():
        print(f"ERROR: experiment-plan not found: {plan_path}", file=sys.stderr)
        sys.exit(2)

    plan_text = plan_path.read_text(encoding="utf-8")
    plan_claims = extract_plan_claims(plan_text)

    configs = load_all_configs(configs_dir)
    config_view = merge_config_view(configs)

    log_view: dict[str, str] = {}
    if args.runs:
        log_view = scan_training_logs(Path(args.runs))

    if args.experiment_state:
        es_path = Path(args.experiment_state)
        if es_path.exists():
            log_view.update(load_json_flat(es_path))

    if not plan_claims:
        print(
            "WARNING: No hyperparameter claims extracted from experiment-plan.md. "
            "The plan may not contain explicit hyperparameter specifications.",
            file=sys.stderr,
        )

    entries = reconcile(plan_claims, config_view, log_view)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(entries, output_path)

    discrepancies = [e for e in entries if e["status"] == "DISCREPANCY"]
    print(
        f"Matches: {len([e for e in entries if e['status'] == 'MATCH'])}  "
        f"Discrepancies: {len(discrepancies)}  "
        f"Missing details: {len([e for e in entries if e['status'] == 'MISSING_DETAIL'])}"
    )
    print(f"Report written to: {output_path}")

    if discrepancies:
        print(
            f"\n[HARD BLOCK] {len(discrepancies)} method-code discrepancy(ies). "
            f"Resolve all before proceeding to manuscript production.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
