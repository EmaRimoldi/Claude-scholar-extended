#!/usr/bin/env python3
"""Validate compute planning against ALETHEIA defaults (seeds, GPUs per job).

Exits non-zero on policy violations unless override flags are passed.
Load defaults from config/compute_defaults.yaml when present."""

import argparse
import os
import sys
from pathlib import Path

def load_defaults(repo_root: Path) -> dict:
    """Parse simple key: value YAML subset without PyYAML dependency."""
    path = repo_root / "config" / "compute_defaults.yaml"
    out = {
        "max_seeds_per_condition": 5,
        "gpus_per_job": 1,
        "max_concurrent_single_gpu_jobs": 8,
    }
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if key in out and val:
            if val.isdigit():
                out[key] = int(val)
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    defaults = load_defaults(repo_root)

    p = argparse.ArgumentParser(
        description="Check seeds/GPU policy for ALETHEIA compute plans.",
    )
    p.add_argument(
        "--seeds",
        type=int,
        required=True,
        help="Planned seeds per experimental condition.",
    )
    p.add_argument(
        "--conditions",
        type=int,
        default=1,
        help="Number of distinct experimental conditions (e.g. 9 configs).",
    )
    p.add_argument(
        "--gpus-per-job",
        type=int,
        default=defaults["gpus_per_job"],
        help="GPUs requested per SLURM job (default from compute_defaults.yaml).",
    )
    p.add_argument(
        "--allow-extra-seeds",
        action="store_true",
        help="Allow seeds > max_seeds_per_condition (document why in compute-plan.md).",
    )
    p.add_argument(
        "--allow-multi-gpu",
        action="store_true",
        help="Allow gpus-per-job > 1 (DDP / model-parallel only).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors.",
    )
    args = p.parse_args()

    max_seeds = int(
        os.environ.get("ALETHEIA_MAX_SEEDS", defaults["max_seeds_per_condition"])
    )
    errors: list[str] = []
    warnings: list[str] = []

    if args.seeds > max_seeds and not args.allow_extra_seeds:
        errors.append(
            f"Seeds {args.seeds} > default max {max_seeds}. "
            f"Reduce to {max_seeds}, or pass --allow-extra-seeds with justification in docs."
        )

    if args.gpus_per_job > 1 and not args.allow_multi_gpu:
        errors.append(
            f"gpus-per-job={args.gpus_per_job} > 1. Standard training uses 1 GPU per job; "
            "use SLURM arrays for seed sweeps. Pass --allow-multi-gpu for true multi-GPU runs."
        )

    if not args.quiet:
        print("ALETHEIA compute budget check")
        print(f"  Defaults file: {repo_root / 'config' / 'compute_defaults.yaml'}")
        print(f"  Conditions: {args.conditions}, seeds/condition: {args.seeds}, GPUs/job: {args.gpus_per_job}")
        print(f"  Total runs (approx): {args.conditions * args.seeds}")
        n = min(args.seeds, max_seeds) if not args.allow_extra_seeds else args.seeds
        hi = max(0, n - 1)
        print(
            f"  Scheduling: 1 GPU per run; prefer #SBATCH --array=0-{hi} for seed sweeps (not N×GPUs in one job)."
        )

    if args.gpus_per_job * args.conditions > 64:
        warnings.append(
            "Very large aggregate GPU request across conditions; submit in waves or use arrays."
        )

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
