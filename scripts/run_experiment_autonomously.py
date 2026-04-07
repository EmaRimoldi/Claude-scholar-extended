#!/usr/bin/env python3
"""Autonomous experiment runner with mandatory validation gates.

Orchestrates the complete experiment workflow:
1. Pre-flight validation (10-15 seconds)
2. CPU smoke test (1-5 minutes)
3. SLURM submission (if both pass)
4. Job monitoring and gate evaluation

Usage:
  python scripts/run_experiment_autonomously.py --phase 2 --project-dir projects/my-project
  python scripts/run_experiment_autonomously.py --auto (resume next pending phase)
"""
import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def read_experiment_state(project_dir: Path) -> Dict:
    """Read experiment-state.json from project directory."""
    state_file = project_dir / "experiment-state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"experiment-state.json not found: {state_file}")

    with open(state_file) as f:
        return json.load(f)


def write_experiment_state(project_dir: Path, state: Dict) -> None:
    """Write updated experiment-state.json."""
    state_file = project_dir / "experiment-state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, default=str)
    logger.info(f"Updated: {state_file}")


def run_validation_step(project_dir: Path, step_name: str, command: List[str], timeout: int) -> Tuple[int, str]:
    """Run a validation step (pre-flight or CPU smoke test)."""
    logger.info(f"\n[1/3] {step_name}")
    logger.info("=" * 50)

    try:
        result = subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Display output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        msg = f"{step_name} timed out after {timeout}s"
        logger.error(msg)
        return 1, msg
    except Exception as e:
        msg = f"{step_name} failed: {e}"
        logger.error(msg)
        return 1, msg


def run_pre_flight_validation(project_dir: Path) -> Tuple[int, str]:
    """Run pre-flight validation (10-15 seconds)."""
    return run_validation_step(
        project_dir,
        "PRE-FLIGHT VALIDATION",
        ["make", "pre-flight-validate"],
        timeout=30,
    )


def run_cpu_smoke_test(project_dir: Path) -> Tuple[int, str]:
    """Run CPU smoke test (1-5 minutes)."""
    return run_validation_step(
        project_dir,
        "CPU SMOKE TEST (max_steps=2)",
        ["make", "cpu-smoke-test"],
        timeout=600,  # 10 minutes
    )


def submit_slurm_jobs(project_dir: Path, state: Dict) -> Tuple[int, List[str]]:
    """Submit SLURM jobs for current phase/wave."""
    logger.info("\n[3/3] SLURM SUBMISSION")
    logger.info("=" * 50)

    phase = state.get("phase")
    wave = state.get("wave")

    # Find SLURM scripts matching this phase/wave
    scripts_dir = project_dir / "scripts"
    slurm_script = scripts_dir / "train.sh"
    if not slurm_script.exists():
        logger.error(f"SLURM script not found: {slurm_script}")
        return 1, []

    # Extract conditions from state
    conditions = state.get("conditions", [])
    if not conditions:
        logger.error("No conditions defined in experiment-state.json")
        return 1, []

    job_ids = []

    # Group conditions: 2 per job (convention from compute-plan)
    for i in range(0, len(conditions), 2):
        batch_conditions = conditions[i:i+2]
        logger.info(f"  Submitting: {' '.join(batch_conditions)}")

        try:
            result = subprocess.run(
                ["sbatch", str(slurm_script), "--conditions"] + batch_conditions,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Extract job ID from sbatch output: "Submitted batch job 12345"
                output = result.stdout.strip()
                if "Submitted batch job" in output:
                    job_id = output.split()[-1]
                    job_ids.append(job_id)
                    logger.info(f"    → Job ID: {job_id}")
                else:
                    logger.warning(f"Unexpected sbatch output: {output}")
            else:
                logger.error(f"sbatch failed: {result.stderr}")
                return 1, []
        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            return 1, []

    if job_ids:
        logger.info(f"  Result: SUCCESS ({len(job_ids)} jobs submitted)")

    return 0 if job_ids else 1, job_ids


def update_experiment_state_after_submission(project_dir: Path, state: Dict, job_ids: List[str]) -> None:
    """Update experiment-state.json with new job IDs and timestamps."""
    phase = state.get("phase")
    wave = state.get("wave")

    # Initialize phases dict if needed
    if "phases" not in state:
        state["phases"] = {}

    # Initialize phase entry
    phase_key = str(phase)
    if phase_key not in state["phases"]:
        state["phases"][phase_key] = {"status": "in_progress", "waves": {}}

    # Record wave submission
    wave_key = str(wave)
    state["phases"][phase_key]["waves"][wave_key] = {
        "status": "submitted",
        "jobs": job_ids,
        "submitted_at": datetime.now().isoformat(),
    }

    # Update top-level job tracking
    if "jobs" not in state:
        state["jobs"] = {}

    job_key = f"phase_{phase}_wave_{wave}"
    state["jobs"][job_key] = job_ids
    state["last_submitted"] = datetime.now().isoformat()

    write_experiment_state(project_dir, state)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Autonomous experiment runner")
    parser.add_argument("--phase", type=int, help="Phase number to run (1, 2, 3, ...)")
    parser.add_argument("--project-dir", type=Path, help="Project directory (defaults to cwd)")
    parser.add_argument("--auto", action="store_true", help="Auto-detect and resume next pending phase")

    args = parser.parse_args()

    # Resolve project directory
    project_dir = args.project_dir or Path.cwd()
    if not project_dir.is_dir():
        logger.error(f"Project directory not found: {project_dir}")
        return 1

    # Read experiment state
    try:
        state = read_experiment_state(project_dir)
    except FileNotFoundError as e:
        logger.error(f"Cannot read experiment state: {e}")
        return 1

    # Determine phase to run
    if args.phase:
        state["phase"] = args.phase
        state["wave"] = 1
    elif not args.auto:
        logger.error("Must specify --phase or --auto")
        return 1

    phase = state.get("phase")
    logger.info("=" * 60)
    logger.info(f"EXPERIMENT RUNNER: Phase {phase}")
    logger.info("=" * 60)

    # Step 1: Pre-flight validation
    exit_code, output = run_pre_flight_validation(project_dir)
    if exit_code != 0:
        logger.error("\n[ABORT] Pre-flight validation failed")
        logger.error("Suggestion: Check error messages above and fix code")
        logger.error("Then rerun: python scripts/run_experiment_autonomously.py --phase " + str(phase))
        return 1

    # Step 2: CPU smoke test
    exit_code, output = run_cpu_smoke_test(project_dir)
    if exit_code != 0:
        logger.error("\n[ABORT] CPU smoke test failed")
        logger.error("Suggestion: Check error messages above and fix code")
        logger.error("Then rerun: python scripts/run_experiment_autonomously.py --phase " + str(phase))
        return 1

    # Step 3: SLURM submission
    exit_code, job_ids = submit_slurm_jobs(project_dir, state)
    if exit_code != 0 or not job_ids:
        logger.error("\n[ABORT] SLURM submission failed")
        logger.error("Suggestion: Check cluster status (sinfo -s) and retry")
        return 1

    # Update experiment state with job IDs
    update_experiment_state_after_submission(project_dir, state, job_ids)

    # Final report
    logger.info("\n" + "=" * 60)
    logger.info("SUBMISSION SUCCESSFUL")
    logger.info("=" * 60)
    logger.info(f"Phase: {phase}")
    logger.info(f"Job IDs: {', '.join(job_ids)}")
    logger.info(f"Status: Pending queue execution")
    logger.info("")
    logger.info("Monitor job status:")
    logger.info(f"  squeue -j {','.join(job_ids)}")
    logger.info(f"  tail -f logs/sparse-hate_*.out")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Wait for Wave 1 to complete (~9 hours)")
    logger.info("  2. Run: python scripts/run_experiment_autonomously.py --phase 2")
    logger.info("     (or automatically triggered when Wave 1 finishes)")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
