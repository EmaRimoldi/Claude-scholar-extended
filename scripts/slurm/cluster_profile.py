#!/usr/bin/env python3
"""Auto-detect SLURM cluster resources and write cluster-profile.json.

Usage:
    python cluster_profile.py [--output cluster-profile.json]
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime


def run(cmd: str) -> str:
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def parse_time_to_seconds(t: str) -> int:
    """Convert SLURM time format to seconds. Handles D-HH:MM:SS, HH:MM:SS, MM:SS."""
    days = 0
    if "-" in t:
        d, t = t.split("-", 1)
        days = int(d)
    parts = t.split(":")
    if len(parts) == 3:
        return days * 86400 + int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return days * 86400 + int(parts[0]) * 60 + int(parts[1])
    return days * 86400


def detect_partitions() -> dict:
    """Parse sinfo to get partition details."""
    raw = run('sinfo -o "%P|%l|%m|%G|%a|%D|%c" --noheader')
    if not raw:
        return {}

    partitions = {}
    for line in raw.splitlines():
        parts = line.split("|")
        if len(parts) < 7:
            continue
        name = parts[0].rstrip("*")
        is_default = parts[0].endswith("*")
        time_limit = parts[1]
        mem_mb = int(re.sub(r"[^0-9]", "", parts[2]) or "0")
        gres = parts[3]
        avail = parts[4]
        nodes = int(parts[5])
        cpus = int(re.sub(r"[^0-9]", "", parts[6]) or "0")

        if avail != "up":
            continue

        # Parse GPU info from GRES
        gpu_info = None
        if gres and gres != "(null)":
            m = re.match(r"gpu:(?:(\w+):)?(\d+)", gres)
            if m:
                gpu_type = m.group(1) or "generic"
                gpu_count = int(m.group(2))
                gpu_info = {"type": gpu_type, "count": gpu_count, "nodes": nodes}

        if name not in partitions:
            partitions[name] = {
                "max_time": time_limit,
                "max_time_seconds": parse_time_to_seconds(time_limit),
                "max_mem_mb": mem_mb,
                "max_cpus": cpus,
                "gpu_types": [],
                "default": is_default,
                "preemptable": "preempt" in name.lower(),
            }
        else:
            partitions[name]["max_mem_mb"] = max(partitions[name]["max_mem_mb"], mem_mb)
            partitions[name]["max_cpus"] = max(partitions[name]["max_cpus"], cpus)

        if gpu_info and gpu_info not in partitions[name]["gpu_types"]:
            partitions[name]["gpu_types"].append(gpu_info)

    return partitions


def detect_user_info() -> dict:
    """Detect user account and QOS."""
    user = os.environ.get("USER", "unknown")
    raw = run(f"sacctmgr show associations user={user} format=Account,Partition,QOS -p --noheader")
    account = "default"
    qos = "normal"
    for line in raw.splitlines():
        parts = line.strip("|").split("|")
        if parts and parts[0]:
            account = parts[0]
        if len(parts) > 2 and parts[2]:
            qos = parts[2]
    return {"user": user, "account": account, "default_qos": qos}


def detect_modules() -> dict:
    """Detect available CUDA modules."""
    raw = run("module avail cuda 2>&1")
    cuda_versions = re.findall(r"cuda/[\d.]+", raw)
    cudnn_versions = re.findall(r"cudnn/[\S]+", raw)
    return {
        "cuda": cuda_versions,
        "cudnn": cudnn_versions,
        "default_cuda": cuda_versions[-1] if cuda_versions else "",
        "default_cudnn": cudnn_versions[0] if cudnn_versions else "",
    }


def build_job_profiles(partitions: dict) -> dict:
    """Build standard job profiles based on available partitions."""
    # Find best GPU partition (non-preemptable first)
    gpu_partitions = [
        (name, p)
        for name, p in partitions.items()
        if p["gpu_types"] and not p["preemptable"]
    ]
    preempt_gpu = [
        (name, p)
        for name, p in partitions.items()
        if p["gpu_types"] and p["preemptable"]
    ]
    cpu_partitions = [
        (name, p)
        for name, p in partitions.items()
        if not p["gpu_types"] and not p["preemptable"]
    ]

    # Pick defaults
    cpu_part = next((n for n, p in cpu_partitions if p["default"]), None)
    if not cpu_part and cpu_partitions:
        cpu_part = cpu_partitions[0][0]

    gpu_part = gpu_partitions[0][0] if gpu_partitions else None
    large_part = preempt_gpu[0][0] if preempt_gpu else gpu_part

    # Find most common GPU type in guaranteed partition
    gpu_type = "gpu"
    if gpu_part and partitions[gpu_part]["gpu_types"]:
        best = max(partitions[gpu_part]["gpu_types"], key=lambda g: g["nodes"])
        gpu_type = best["type"]

    profiles = {}
    if cpu_part:
        profiles["cpu-light"] = {
            "partition": cpu_part, "cpus": 4, "mem_gb": 16,
            "time": "01:00:00", "gpus": 0,
        }
        profiles["cpu-heavy"] = {
            "partition": cpu_part, "cpus": 16, "mem_gb": 64,
            "time": "04:00:00", "gpus": 0,
        }
    if gpu_part:
        profiles["gpu-single"] = {
            "partition": gpu_part, "cpus": 8, "mem_gb": 64,
            "time": "04:00:00", "gpus": 1, "gpu_type": gpu_type,
        }
        profiles["gpu-multi"] = {
            "partition": gpu_part, "cpus": 16, "mem_gb": 128,
            "time": "06:00:00", "gpus": 4, "gpu_type": gpu_type,
        }
    if large_part:
        large_type = gpu_type
        if large_part in partitions and partitions[large_part]["gpu_types"]:
            best = max(partitions[large_part]["gpu_types"], key=lambda g: g.get("nodes", 0))
            large_type = best["type"]
        profiles["gpu-large"] = {
            "partition": large_part, "cpus": 32, "mem_gb": 256,
            "time": "1-00:00:00", "gpus": 8, "gpu_type": large_type,
        }

    return profiles


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Auto-detect SLURM cluster resources")
    parser.add_argument("--output", default="cluster-profile.json")
    args = parser.parse_args()

    print("Detecting cluster resources...")
    partitions = detect_partitions()
    user_info = detect_user_info()
    modules = detect_modules()
    profiles = build_job_profiles(partitions)

    # Find venv
    venv_path = ""
    for candidate in ["rag-lit-synthesis/.venv", ".venv", "venv"]:
        if os.path.isdir(candidate):
            venv_path = candidate
            break

    profile = {
        "cluster_name": "Auto-detected SLURM cluster",
        "detected_at": datetime.now().strftime("%Y-%m-%d"),
        **user_info,
        "modules": modules,
        "venv_path": venv_path,
        "partitions": partitions,
        "job_profiles": profiles,
    }

    with open(args.output, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"Cluster profile saved to {args.output}")
    print(f"  User: {user_info['user']} / Account: {user_info['account']}")
    print(f"  Partitions: {len(partitions)}")
    gpu_parts = [n for n, p in partitions.items() if p["gpu_types"]]
    print(f"  GPU partitions: {', '.join(gpu_parts)}")
    print(f"  Job profiles: {', '.join(profiles.keys())}")


if __name__ == "__main__":
    main()
