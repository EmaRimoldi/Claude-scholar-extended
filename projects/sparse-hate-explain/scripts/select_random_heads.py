#!/usr/bin/env python3
"""
select_random_heads.py — Seed-controlled random head selection for B5 baseline.

Generates a JSON file containing K randomly selected (layer, head) pairs drawn
from the full 12×12 = 144 attention head pool.  The RNG is seeded with the
experiment seed so that (a) selections are reproducible and (b) each seed
produces a *different* random set, matching the B5 experimental design.

Usage:
    python scripts/select_random_heads.py \\
        --seed 42 \\
        --k 24 \\
        --n-layers 12 \\
        --n-heads 12 \\
        --output-dir results/head_importance/

Output: results/head_importance/random_heads_seed42.json
  A JSON array of [layer, head] pairs, e.g. [[0, 3], [1, 11], ...]
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Tuple


def select_random_heads(
    seed: int,
    k: int,
    n_layers: int = 12,
    n_heads: int = 12,
) -> List[Tuple[int, int]]:
    """Return K randomly chosen (layer, head) pairs using the given seed."""
    all_heads = [(l, h) for l in range(n_layers) for h in range(n_heads)]
    rng = random.Random(seed)
    selected = rng.sample(all_heads, k)
    return sorted(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Random head selection for B5 baseline")
    parser.add_argument("--seed", type=int, required=True, help="RNG seed")
    parser.add_argument("--k", type=int, default=24, help="Number of heads to select")
    parser.add_argument("--n-layers", type=int, default=12)
    parser.add_argument("--n-heads", type=int, default=12)
    parser.add_argument("--output-dir", required=True, help="Directory to write JSON file")
    args = parser.parse_args()

    selected = select_random_heads(args.seed, args.k, args.n_layers, args.n_heads)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"random_heads_seed{args.seed}.json"

    with open(output_path, "w") as fh:
        json.dump(selected, fh, indent=2)

    print(f"Saved {len(selected)} random heads (seed={args.seed}) → {output_path}")
    print(f"First 5: {selected[:5]}")


if __name__ == "__main__":
    main()
