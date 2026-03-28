#!/usr/bin/env python3
"""Submit all experiment phases to SLURM in proper order.

Usage:
    python scripts/submit_experiments.py --phase 1   # Baselines
    python scripts/submit_experiments.py --phase 2   # Head importance (after phase 1)
    python scripts/submit_experiments.py --phase 3   # Sparsemax experiments (after phase 2)
    python scripts/submit_experiments.py --phase 4   # Lambda ablation (after phase 2)
    python scripts/submit_experiments.py --phase all  # Submit all with dependencies
    python scripts/submit_experiments.py --status     # Check all job status
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
VENV = PROJECT_ROOT.parent / ".venv" / "bin" / "activate"
LOG_DIR = PROJECT_ROOT.parent / "logs" / "slurm" / datetime.now().strftime("%Y-%m-%d")

SEEDS = [42, 123, 456]
PARTITION = "pi_tpoggio"
GPU_TYPE = "a100"


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()


def make_sbatch(job_name: str, command: str, time: str = "02:00:00",
                mem_gb: int = 32, cpus: int = 8, gpus: int = 1,
                dependency: str = None) -> str:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dep_line = f"#SBATCH --dependency=afterok:{dependency}" if dependency else ""
    return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={PARTITION}
#SBATCH --gres=gpu:{GPU_TYPE}:{gpus}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem_gb}G
#SBATCH --time={time}
#SBATCH --output={LOG_DIR}/{job_name}-%j.out
#SBATCH --error={LOG_DIR}/{job_name}-%j.err
{dep_line}

set -euo pipefail
source {VENV}
cd {PROJECT_ROOT}

echo "=== Job: {job_name} ==="
echo "Date: $(date)"
echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo ""

{command}

echo ""
echo "=== Done: {job_name} ==="
"""


def submit(script: str, job_name: str) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{job_name}.sbatch"
    path.write_text(script)
    output = run(f"sbatch {path}")
    match = re.search(r"(\d+)", output)
    if not match:
        print(f"FAILED to submit {job_name}: {output}", file=sys.stderr)
        return -1
    job_id = int(match.group(1))
    print(f"  Submitted {job_name} -> job {job_id}")
    return job_id


def phase1_baselines() -> list:
    """Phase 1: Baseline experiments (vanilla, softmax_all, softmax_all_strong)."""
    print("=== Phase 1: Baselines ===")
    jobs = []
    for seed in SEEDS:
        for exp, extra in [
            ("vanilla", ""),
            ("softmax_all", ""),
            ("softmax_all", "model.lambda_attn=2.0"),
        ]:
            name = f"{exp}{'_strong' if 'lambda_attn=2.0' in extra else ''}_s{seed}"
            output_dir = RESULTS_DIR / name
            cmd = (
                f"python -m src.main +experiment={exp} seed={seed} "
                f"output_dir={output_dir} data.cache_dir=data/cache "
                f"{extra}"
            )
            script = make_sbatch(f"p1-{name}", cmd)
            job_id = submit(script, f"p1-{name}")
            jobs.append({"name": name, "job_id": job_id, "phase": 1})
    return jobs


def phase2_head_importance(dependency: str = None) -> list:
    """Phase 2: Head importance analysis on best vanilla model."""
    print("=== Phase 2: Head Importance ===")
    # Use first vanilla seed as representative
    vanilla_dir = RESULTS_DIR / "vanilla_s42"
    cmd = (
        f"python -m src.main +experiment=vanilla mode=head_importance "
        f"checkpoint={vanilla_dir}/best_model.pt "
        f"output_dir={RESULTS_DIR}/head_importance "
        f"data.cache_dir=data/cache"
    )
    script = make_sbatch("p2-head-importance", cmd, time="00:30:00",
                         dependency=dependency)
    job_id = submit(script, "p2-head-importance")
    return [{"name": "head_importance", "job_id": job_id, "phase": 2}]


def phase3_sparsemax(dependency: str = None) -> list:
    """Phase 3: Sparsemax experiments."""
    print("=== Phase 3: Sparsemax Experiments ===")
    jobs = []
    conditions = [
        ("sparsemax_all", "sparsemax_all", ""),
        ("sparsemax_top12", "sparsemax_topk", "model.top_k=12"),
        ("sparsemax_top24", "sparsemax_topk", "model.top_k=24"),
        ("sparsemax_top36", "sparsemax_topk", "model.top_k=36"),
        ("softmax_top24", "sparsemax_topk", "model.attention_transform=softmax model.top_k=24"),
        ("sparsemax_top24_strong", "sparsemax_topk", "model.top_k=24 model.lambda_attn=2.0"),
    ]
    for seed in SEEDS:
        for name_prefix, exp, extra in conditions:
            name = f"{name_prefix}_s{seed}"
            output_dir = RESULTS_DIR / name
            cmd = (
                f"python -m src.main +experiment={exp} seed={seed} "
                f"output_dir={output_dir} data.cache_dir=data/cache "
                f"model.head_importance_path={RESULTS_DIR}/head_importance/head_importance.json "
                f"{extra}"
            )
            script = make_sbatch(f"p3-{name}", cmd, dependency=dependency)
            job_id = submit(script, f"p3-{name}")
            jobs.append({"name": name, "job_id": job_id, "phase": 3})
    return jobs


def phase4_lambda_ablation(dependency: str = None) -> list:
    """Phase 4: Lambda sweep on sparsemax_top24."""
    print("=== Phase 4: Lambda Ablation ===")
    jobs = []
    for seed in SEEDS:
        for lam in [0.1, 0.5, 1.0, 2.0]:
            lam_str = str(lam).replace(".", "")
            name = f"sparsemax_top24_lam{lam_str}_s{seed}"
            output_dir = RESULTS_DIR / name
            cmd = (
                f"python -m src.main +experiment=sparsemax_topk seed={seed} "
                f"output_dir={output_dir} data.cache_dir=data/cache "
                f"model.top_k=24 model.lambda_attn={lam} "
                f"model.head_importance_path={RESULTS_DIR}/head_importance/head_importance.json"
            )
            script = make_sbatch(f"p4-{name}", cmd, dependency=dependency)
            job_id = submit(script, f"p4-{name}")
            jobs.append({"name": name, "job_id": job_id, "phase": 4})
    return jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="all", help="Phase to submit: 1, 2, 3, 4, or all")
    parser.add_argument("--status", action="store_true", help="Show job status")
    parser.add_argument("--dep", default=None, help="SLURM dependency job ID")
    args = parser.parse_args()

    if args.status:
        output = run(f"squeue -u {os.environ.get('USER', '')} -o '%.8i %.10P %.30j %.2t %.10M'")
        print(output or "No active jobs.")
        return

    all_jobs = []
    tracker_path = RESULTS_DIR / "job_tracker.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.phase in ("1", "all"):
        all_jobs.extend(phase1_baselines())

    if args.phase in ("2", "all"):
        dep = args.dep
        if args.phase == "all":
            p1_ids = [j["job_id"] for j in all_jobs if j["phase"] == 1 and j["job_id"] > 0]
            dep = ":".join(str(x) for x in p1_ids) if p1_ids else None
        all_jobs.extend(phase2_head_importance(dep))

    if args.phase in ("3", "all"):
        dep = args.dep
        if args.phase == "all":
            p2_ids = [j["job_id"] for j in all_jobs if j["phase"] == 2 and j["job_id"] > 0]
            dep = ":".join(str(x) for x in p2_ids) if p2_ids else None
        all_jobs.extend(phase3_sparsemax(dep))

    if args.phase in ("4", "all"):
        dep = args.dep
        if args.phase == "all":
            p2_ids = [j["job_id"] for j in all_jobs if j["phase"] == 2 and j["job_id"] > 0]
            dep = ":".join(str(x) for x in p2_ids) if p2_ids else None
        all_jobs.extend(phase4_lambda_ablation(dep))

    # Save job tracker
    with open(tracker_path, "w") as f:
        json.dump(all_jobs, f, indent=2)
    print(f"\nTotal jobs submitted: {len(all_jobs)}")
    print(f"Job tracker saved to: {tracker_path}")


if __name__ == "__main__":
    main()
