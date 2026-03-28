#!/usr/bin/env python3
"""Generate SLURM sbatch scripts from cluster profile and job profiles.

Usage:
    python job_builder.py --profile gpu-single --command "python src/main.py" [--test]
    python job_builder.py --profile cpu-heavy --command "python src/data/benchmark_builder.py"
    python job_builder.py --partition mit_preemptable --gpus 2 --gpu-type h100 --command "..."
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CLUSTER_PROFILE = PROJECT_ROOT / "cluster-profile.json"
LOGS_DIR = PROJECT_ROOT / "logs" / "slurm"


def load_cluster_profile(path: str = None) -> dict:
    """Load cluster profile JSON."""
    p = Path(path) if path else CLUSTER_PROFILE
    if not p.exists():
        print(f"Error: cluster profile not found at {p}", file=sys.stderr)
        print("Run: python scripts/slurm/cluster_profile.py", file=sys.stderr)
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


def resolve_profile(cluster: dict, profile_name: str, overrides: dict = None) -> dict:
    """Resolve a job profile with optional overrides."""
    profiles = cluster.get("job_profiles", {})
    if profile_name not in profiles:
        available = ", ".join(profiles.keys())
        print(f"Error: unknown profile '{profile_name}'. Available: {available}", file=sys.stderr)
        sys.exit(1)

    config = dict(profiles[profile_name])
    if overrides:
        for k, v in overrides.items():
            if v is not None:
                config[k] = v
    return config


def generate_sbatch(
    job_name: str,
    command: str,
    config: dict,
    cluster: dict,
    email: str = None,
) -> str:
    """Generate a complete sbatch script."""
    partition = config["partition"]
    cpus = config.get("cpus", 4)
    mem_gb = config.get("mem_gb", 16)
    time_limit = config.get("time", "04:00:00")
    gpus = config.get("gpus", 0)
    gpu_type = config.get("gpu_type", "")
    account = cluster.get("account", "")
    modules = cluster.get("modules", {})
    venv_path = cluster.get("venv_path", "")

    # Build GRES string
    gres_line = ""
    if gpus > 0:
        if gpu_type:
            gres_line = f"#SBATCH --gres=gpu:{gpu_type}:{gpus}"
        else:
            gres_line = f"#SBATCH --gres=gpu:{gpus}"

    # Build module loads
    module_lines = ""
    if gpus > 0:
        cuda_mod = modules.get("default_cuda", "")
        cudnn_mod = modules.get("default_cudnn", "")
        loads = []
        if cuda_mod:
            loads.append(f"module load {cuda_mod}")
        if cudnn_mod:
            loads.append(f"module load {cudnn_mod}")
        if loads:
            module_lines = "\n".join(loads)

    # Build venv activation
    venv_line = ""
    if venv_path:
        venv_line = f"source {venv_path}/bin/activate"

    # Email notification
    email_lines = ""
    if email:
        email_lines = f"#SBATCH --mail-user={email}\n#SBATCH --mail-type=END,FAIL"

    # Log directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = f"logs/slurm/{date_str}"

    lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name={job_name}",
        f"#SBATCH --partition={partition}",
        f"#SBATCH --account={account}",
        f"#SBATCH --cpus-per-task={cpus}",
        f"#SBATCH --mem={mem_gb}G",
        f"#SBATCH --time={time_limit}",
        f"#SBATCH --output={log_dir}/{job_name}-%j.out",
        f"#SBATCH --error={log_dir}/{job_name}-%j.err",
    ]
    if gres_line:
        lines.append(gres_line)
    if email_lines:
        lines.extend(email_lines.splitlines())

    lines.append("")
    lines.append("# --- Environment setup ---")
    lines.append("set -euo pipefail")
    lines.append('echo "Job $SLURM_JOB_ID started at $(date)"')
    lines.append('echo "Node: $(hostname), Partition: $SLURM_JOB_PARTITION"')
    if module_lines:
        lines.extend(module_lines.splitlines())
    if venv_line:
        lines.append(venv_line)

    lines.append("")
    lines.append(f"cd {PROJECT_ROOT}")
    lines.append(f"mkdir -p {log_dir}")

    if gpus > 0:
        lines.append("")
        lines.append("# GPU info")
        lines.append("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
        lines.append("echo '---'")

    lines.append("")
    lines.append("# --- Run command ---")
    lines.append(command)
    lines.append("")
    lines.append('echo "Job $SLURM_JOB_ID finished at $(date)"')

    return "\n".join(lines) + "\n"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate SLURM sbatch scripts")
    parser.add_argument("--profile", default="gpu-single",
                        help="Job profile: cpu-light, cpu-heavy, gpu-single, gpu-multi, gpu-large")
    parser.add_argument("--command", required=True, help="Command to run")
    parser.add_argument("--job-name", default=None, help="Job name (auto-generated if omitted)")
    parser.add_argument("--cluster-profile", default=None, help="Path to cluster-profile.json")
    parser.add_argument("--output", "-o", default=None, help="Output sbatch file path")
    parser.add_argument("--test", action="store_true", help="Print script to stdout, don't write file")
    parser.add_argument("--email", default=None, help="Email for notifications")
    # Overrides
    parser.add_argument("--partition", default=None)
    parser.add_argument("--gpus", type=int, default=None)
    parser.add_argument("--gpu-type", default=None)
    parser.add_argument("--cpus", type=int, default=None)
    parser.add_argument("--mem-gb", type=int, default=None)
    parser.add_argument("--time", default=None)

    args = parser.parse_args()

    cluster = load_cluster_profile(args.cluster_profile)
    overrides = {
        "partition": args.partition,
        "gpus": args.gpus,
        "gpu_type": args.gpu_type,
        "cpus": args.cpus,
        "mem_gb": args.mem_gb,
        "time": args.time,
    }
    config = resolve_profile(cluster, args.profile, overrides)

    job_name = args.job_name or f"cls-{args.profile}-{datetime.now().strftime('%H%M%S')}"
    script = generate_sbatch(job_name, args.command, config, cluster, args.email)

    if args.test:
        print(script)
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = PROJECT_ROOT / "logs" / "slurm" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = Path(args.output) if args.output else output_dir / f"{job_name}.sbatch"
    output_path.write_text(script)
    print(f"Script written to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    main()
