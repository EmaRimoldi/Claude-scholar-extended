#!/usr/bin/env python3
"""
Pipeline State Manager for Claude Scholar.

Manages persistent state for the end-to-end research pipeline orchestrator.
State is stored in pipeline-state.json in the project root.

Usage:
    python pipeline_state.py init [--force]
    python pipeline_state.py status
    python pipeline_state.py start <step_id>
    python pipeline_state.py complete <step_id>
    python pipeline_state.py skip <step_id>
    python pipeline_state.py fail <step_id> [--reason REASON]
    python pipeline_state.py next
    python pipeline_state.py reset
    python pipeline_state.py reset-range <from_step_id> <to_step_id>
    python pipeline_state.py get-generation
    python pipeline_state.py set-generation <N>
    python pipeline_state.py new-generation --trigger-reason REASON [--rerun-from STEP] [--rerun-to STEP]
    python pipeline_state.py write-step-result <step_id> <json_string_or_@file>
    python pipeline_state.py append-decision <json_string_or_@file>
    python pipeline_state.py add-archive-path <path> [--generation N]
    python pipeline_state.py check-readiness
"""

import sys

if sys.version_info < (3, 6):
    sys.stderr.write("Error: pipeline_state.py requires Python 3.6+\n")
    sys.exit(1)

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STATE_FILE = "pipeline-state.json"
STATE_DIR = "state"
DEFAULT_INPUTS_FILE = "RESEARCH_PROPOSAL.md"

# Default project directory structure created for each project.
PROJECT_SUBDIRS = ["docs", "configs", "src", "data", "results", "results/tables",
                   "results/figures", "manuscript", "logs", "notebooks"]

# Canonical v3 pipeline steps in execution order (38 steps across 6 phases).
# Each tuple: (step_id, slash_command, description, prerequisite_files, needs_online)
# prerequisite_files are relative to project_dir (e.g. "docs/hypotheses.md").
# Steps with command "—" are inline orchestrator sub-tasks (no separate slash command).
PIPELINE_STEPS = [
    # --- Phase 1: Research & Novelty Assessment (Days 1–5) ---
    (
        "research-landscape",
        "/research-landscape",
        "Pass 1: Broad territory mapping, 50–100 papers, Citation Ledger init",
        [],
        True,
    ),
    (
        "cross-field-search",
        "/cross-field-search",
        "Pass 4: Abstract problem, identify adjacent fields, produce cross-field-report.md",
        ["docs/research-landscape.md"],
        True,
    ),
    (
        "formulate-hypotheses",
        "/research-init",
        "Hypothesis generation from gaps (hypothesis-generator agent)",
        ["docs/research-landscape.md"],
        False,
    ),
    (
        "claim-search",
        "/claim-search",
        "Pass 2: Decompose hypothesis into atomic claims, search each",
        ["docs/hypotheses.md"],
        True,
    ),
    (
        "citation-traversal",
        "/citation-traversal",
        "Pass 3: Citation graph traversal from top seed papers",
        ["docs/research-landscape.md"],
        True,
    ),
    (
        "adversarial-search",
        "/adversarial-search",
        "Pass 6: Actively attempt to kill novelty claim",
        ["docs/claim-overlap-report.md"],
        True,
    ),
    (
        "novelty-gate-n1",
        "/novelty-gate gate=N1",
        "Gate N1: Full novelty evaluation. PROCEED/REPOSITION/PIVOT/KILL",
        ["docs/adversarial-novelty-report.md", "docs/cross-field-report.md"],
        False,
    ),
    (
        "recency-sweep-1",
        "/recency-sweep sweep_id=1",
        "Pass 5: First recency check for concurrent work",
        ["docs/hypotheses.md"],
        True,
    ),
    # --- Phase 2: Experiment Design (Days 5–6) ---
    (
        "design-experiments",
        "/design-experiments",
        "Full experiment plan with baselines, ablations, power analysis",
        ["docs/hypotheses.md", "docs/novelty-assessment.md"],
        False,
    ),
    (
        "design-novelty-check",
        "/design-novelty-check",
        "Gate N2: Does design test the novelty claim? Baselines correct?",
        ["docs/experiment-plan.md", "docs/claim-overlap-report.md"],
        False,
    ),
    # --- Phase 3: Implementation (Days 6–10) ---
    (
        "scaffold",
        "/scaffold",
        "Generate project structure",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "build-data",
        "/build-data",
        "Dataset generators and loaders",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "setup-model",
        "/setup-model",
        "Load and configure models",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "implement-metrics",
        "/implement-metrics",
        "Metrics and statistical tests",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "validate-setup",
        "/validate-setup",
        "Pre-flight validation checklist (hard block)",
        [],
        False,
    ),
    # --- Phase 4: Execution (Days 10–19, SLURM) ---
    (
        "download-data",
        "/download-data",
        "Download datasets/models to cluster cache",
        ["docs/experiment-plan.md"],
        True,
    ),
    (
        "plan-compute",
        "/plan-compute",
        "GPU estimation, SLURM scripts",
        ["docs/experiment-plan.md"],
        False,
    ),
    (
        "run-experiment",
        "/run-experiment",
        "Submit experiment matrix, monitor, recover",
        [],
        False,
    ),
    (
        "collect-results",
        "/collect-results",
        "Aggregate outputs into structured tables",
        [],
        False,
    ),
    # --- Phase 5A: Analysis & Epistemic Grounding (Days 19–23) ---
    (
        "analyze-results",
        "/analyze-results",
        "Statistical analysis, figures, hypothesis outcomes",
        [],
        False,
    ),
    (
        "gap-detection",
        "—",
        "Gap Detection: missing ablations/baselines (inline; may loop back to step 9)",
        ["docs/analysis-report.md"],
        False,
    ),
    (
        "post-results-novelty",
        "/novelty-gate gate=N3",
        "Gate N3: Re-evaluate novelty given actual results",
        ["docs/analysis-report.md", "docs/hypothesis-outcomes.md"],
        False,
    ),
    (
        "recency-sweep-2",
        "/recency-sweep sweep_id=2",
        "Pass 5 again: concurrent work during execution",
        ["docs/novelty-reassessment.md"],
        True,
    ),
    (
        "literature-rescan",
        "—",
        "Results-contextualized literature re-scan (inline)",
        ["docs/analysis-report.md", "docs/novelty-reassessment.md"],
        True,
    ),
    (
        "method-code-reconciliation",
        "—",
        "Method-Code consistency check (hard block on discrepancy; inline)",
        ["experiment-state.json"],
        False,
    ),
    # --- Phase 5B: Claim Architecture & Writing Cycle (Days 23–29) ---
    (
        "map-claims",
        "/map-claims",
        "Claim-evidence architecture, Claim Dependency Graph, Skeptic Agent",
        ["docs/analysis-report.md"],
        False,
    ),
    (
        "position",
        "/position",
        "Contribution positioning using novelty-reassessment.md as primary input",
        ["docs/novelty-reassessment.md", "docs/claim-ledger.md"],
        False,
    ),
    (
        "story",
        "/story",
        "Narrative arc, paper blueprint, figure plan",
        ["docs/positioning.md"],
        False,
    ),
    (
        "narrative-gap-detect",
        "—",
        "Narrative Gap Detector: may loop back to Step 20 or Step 9 (inline)",
        ["docs/paper-blueprint.md"],
        False,
    ),
    (
        "argument-figure-align",
        "—",
        "Figure-argument alignment; redesign figures that don't serve their claim (inline)",
        ["docs/figure-plan.md"],
        False,
    ),
    (
        "produce-manuscript",
        "/produce-manuscript",
        "Full prose + Citation Audit sub-step",
        ["docs/paper-blueprint.md"],
        False,
    ),
    (
        "cross-section-consistency",
        "—",
        "5-check cross-section consistency (hard block on failure; inline)",
        ["manuscript/"],
        False,
    ),
    (
        "claim-source-align",
        "—",
        "Claim-Source Alignment Verifier (hard block on untraced claims; inline)",
        ["manuscript/"],
        False,
    ),
    (
        "verify-paper",
        "/verify-paper",
        "7-dimensional quality verifier (45 criteria)",
        ["docs/claim-alignment-report.md", "docs/cross-section-report.md"],
        False,
    ),
    # --- Phase 6: Pre-Submission & Publication (Days 29–38) ---
    (
        "adversarial-review",
        "—",
        "3 hostile simulated reviewers, routes upstream (inline)",
        ["manuscript/"],
        False,
    ),
    (
        "recency-sweep-final",
        "/recency-sweep sweep_id=final",
        "Pass 5 final: last concurrent work check within 48h of submission",
        ["docs/novelty-reassessment.md"],
        True,
    ),
    (
        "novelty-gate-n4",
        "/novelty-gate gate=N4",
        "Gate N4: Final novelty confirmation before compilation",
        ["docs/concurrent-work-report.md"],
        False,
    ),
    (
        "compile-manuscript",
        "/compile-manuscript",
        "Compile LaTeX to PDF, Overleaf ZIP, chktex",
        ["manuscript/"],
        False,
    ),
]

# ---------------------------------------------------------------------------
# Package 5: Completion contracts for high-risk steps
# ---------------------------------------------------------------------------
#
# REQUIRED_OUTPUTS: files that MUST exist (relative to --dir / project_dir)
# before a step can be marked `completed`.  Paths ending with "/" are treated
# as directory-existence + non-empty checks.
#
# STEP_RESULT_REQUIRED: steps that additionally require a written step-result
# artifact (state/step-results/<step_id>.json) before completion is valid.
# ---------------------------------------------------------------------------

REQUIRED_OUTPUTS: dict = {
    "formulate-hypotheses": [
        "docs/hypotheses.md",
    ],
    "novelty-gate-n1": [
        "docs/novelty-assessment.md",
        "state/gates/novelty-gate-n1.json",
    ],
    "design-experiments": [
        "docs/experiment-plan.md",
    ],
    "analyze-results": [
        "state/execution-readiness.json",   # Package 6: readiness gate (ready_for_analysis must be true)
        "docs/analysis-report.md",
        "docs/hypothesis-outcomes.md",
    ],
    "map-claims": [
        "docs/claim-ledger.md",
    ],
    "produce-manuscript": [
        "manuscript/",            # directory must exist and be non-empty
    ],
    "verify-paper": [
        "docs/paper-quality-report.md",
    ],
}

# Steps that require a step-result artifact written by the orchestrator before
# `complete` will succeed.  All high-risk steps require this.
STEP_RESULT_REQUIRED: frozenset = frozenset(REQUIRED_OUTPUTS.keys())


def _check_required_output(project_dir: str, rel_path: str) -> bool:
    """
    Return True if the required output exists and (for directories) is non-empty.
    Paths ending with '/' are treated as directory checks.
    """
    full = os.path.join(project_dir, rel_path.rstrip("/"))
    if rel_path.endswith("/"):
        return os.path.isdir(full) and bool(os.listdir(full))
    return os.path.isfile(full)


def check_completion_contracts(
    project_dir: str,
    step_id: str,
    state_root: str | None = None,
) -> list:
    """
    Validate completion contracts for a high-risk step.
    Returns a list of failure reason strings.  Empty list means all clear.

    project_dir: directory for checking required output files (docs/, etc.)
    state_root: directory for checking state/step-results/ artifacts.
                Defaults to project_dir when not provided (legacy behaviour).
    """
    failures: list = []
    _state_root = state_root if state_root is not None else project_dir

    # 1. Required output files
    for req in REQUIRED_OUTPUTS.get(step_id, []):
        if not _check_required_output(project_dir, req):
            failures.append(f"required output missing: {req}")

    # 2. Step-result artifact (lives under state_root/state/step-results/)
    if step_id in STEP_RESULT_REQUIRED:
        result_path = _step_result_path(_state_root, step_id)
        if not os.path.exists(result_path):
            failures.append(
                f"step-result artifact missing: state/step-results/{step_id}.json "
                f"(write it first with: python scripts/pipeline_state.py write-step-result {step_id} '{{...}}')"
            )

    return failures


# Loop counter fields tracked in pipeline-state.json.
# These are incremented by the orchestrator when a feedback loop fires.
LOOP_COUNTERS = {
    "reposition_count":       {"max": 2, "loop": "N1 REPOSITION → Step 3"},
    "pivot_count":            {"max": 1, "loop": "N1 PIVOT → Step 1"},
    "design_novelty_loops":   {"max": 2, "loop": "N2 REVISE → Step 9"},
    "gap_detection_loops":    {"max": 2, "loop": "Gap Detection → Step 9"},
    "narrative_gap_loops":    {"max": 2, "loop": "Narrative Gap → Step 20 or Step 9"},
    "verify_paper_cycle":     {"max": 3, "loop": "Phase 5B Revision → Steps 26–33"},
    "adversarial_review_cycles": {"max": 2, "loop": "Adversarial Review → upstream"},
}

# ---------------------------------------------------------------------------
# Context budget and handoff system
# ---------------------------------------------------------------------------
#
# Each step MAY write a step-handoff-v1 artifact to state/handoffs/<step_id>.json
# after completing.  The orchestrator loads this INSTEAD of full prerequisite
# Markdown documents when check-budget reports a HIGH context budget, reducing
# token consumption by 5-10x for document-heavy steps.
#
# Schema: step-handoff-v1
#   step_id          (str)   — canonical or sub-step ID
#   key_outputs      (dict)  — field name → short value string (1-2 sentences each)
#   summary          (str)   — 1-3 sentence prose summary of what the step produced
#   critical_context (list)  — short strings the next step MUST know
#   token_estimate   (int)   — rough token count of the full output document
#   created_at       (str)   — ISO-8601 timestamp (auto-injected)
#   $schema          (str)   — "step-handoff-v1" (auto-injected)
#
# The handoff system is ADDITIVE:
# - Steps without a handoff remain fully functional.
# - Batch sub-step IDs (e.g. "research-landscape-batch-1") are valid and do
#   NOT need to appear in PIPELINE_STEPS.
# - write-handoff does NOT modify pipeline-state.json step statuses.
# ---------------------------------------------------------------------------

HANDOFF_REQUIRED_FIELDS = ("key_outputs", "summary", "critical_context", "token_estimate")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Package 2: State directory helpers
# ---------------------------------------------------------------------------

def get_state_dir(project_dir: str) -> str:
    """Return the absolute path of the state/ subdirectory."""
    return os.path.join(project_dir, STATE_DIR)


def _ensure_state_dir(project_dir: str) -> str:
    """Create state/ and state/step-results/ if needed; return state dir path."""
    state_dir = get_state_dir(project_dir)
    os.makedirs(os.path.join(state_dir, "step-results"), exist_ok=True)
    return state_dir


# --- Generation manifest ---

def _generation_manifest_path(project_dir: str) -> str:
    return os.path.join(get_state_dir(project_dir), "generation-manifest.json")


def load_generation_manifest(project_dir: str) -> dict:
    """Load state/generation-manifest.json; return {} if absent."""
    path = _generation_manifest_path(project_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_generation_manifest(project_dir: str, manifest: dict) -> None:
    _ensure_state_dir(project_dir)
    path = _generation_manifest_path(project_dir)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


def init_generation_manifest(project_dir: str) -> dict:
    """Create generation-manifest.json with generation 1 as the active entry."""
    manifest = {
        "$schema": "generation-manifest-v1",
        "active_generation": 1,
        "generations": [
            {
                "generation_id": 1,
                "parent_generation": None,
                "trigger_reason": "initial run",
                "created_at": now_iso(),
                "active": True,
                "rerun_range": None,
                "archived_paths": [],
            }
        ],
    }
    save_generation_manifest(project_dir, manifest)
    return manifest


def get_active_generation(project_dir: str) -> int:
    """Return active_generation from the manifest; return 1 if manifest is absent."""
    manifest = load_generation_manifest(project_dir)
    return int(manifest.get("active_generation", 1))


def set_active_generation(project_dir: str, generation: int) -> None:
    """Write active_generation to the manifest (creating it if absent)."""
    manifest = load_generation_manifest(project_dir)
    if not manifest:
        manifest = init_generation_manifest(project_dir)
    manifest["active_generation"] = generation
    # Mark all generations active/inactive based on new active id
    for entry in manifest.get("generations", []):
        entry["active"] = (entry["generation_id"] == generation)
    save_generation_manifest(project_dir, manifest)


def new_generation(
    project_dir: str,
    trigger_reason: str,
    rerun_from: Optional[str] = None,
    rerun_to: Optional[str] = None,
) -> int:
    """
    Append a new generation entry to the manifest and activate it.
    Returns the new generation_id.
    """
    manifest = load_generation_manifest(project_dir)
    if not manifest:
        manifest = init_generation_manifest(project_dir)

    current_gen = int(manifest.get("active_generation", 1))
    new_gen_id = current_gen + 1

    rerun_range = None
    if rerun_from or rerun_to:
        rerun_range = {
            "from_step": rerun_from,
            "to_step": rerun_to,
        }

    new_entry = {
        "generation_id": new_gen_id,
        "parent_generation": current_gen,
        "trigger_reason": trigger_reason,
        "created_at": now_iso(),
        "active": True,
        "rerun_range": rerun_range,
        "archived_paths": [],
    }

    # Mark all previous generations inactive
    for entry in manifest.get("generations", []):
        entry["active"] = False

    manifest["active_generation"] = new_gen_id
    manifest["generations"].append(new_entry)
    save_generation_manifest(project_dir, manifest)
    return new_gen_id


# --- Decision log ---

def _decision_log_path(project_dir: str) -> str:
    return os.path.join(get_state_dir(project_dir), "decision-log.jsonl")


def append_decision_record(project_dir: str, record: dict) -> None:
    """Append one JSON line to state/decision-log.jsonl."""
    _ensure_state_dir(project_dir)
    path = _decision_log_path(project_dir)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


# --- Step results ---

def _step_result_path(project_dir: str, step_id: str) -> str:
    return os.path.join(get_state_dir(project_dir), "step-results", f"{step_id}.json")


def write_step_result(project_dir: str, step_id: str, result: dict) -> None:
    """Write (overwrite) state/step-results/<step_id>.json."""
    _ensure_state_dir(project_dir)
    path = _step_result_path(project_dir, step_id)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)


def load_step_result(project_dir: str, step_id: str) -> dict:
    """Load state/step-results/<step_id>.json; return {} if absent."""
    path = _step_result_path(project_dir, step_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def add_archive_path(project_dir: str, archive_path: str, generation: Optional[int] = None) -> None:
    """
    Append archive_path to the archived_paths list of a generation entry.
    If generation is None, uses the active generation.
    """
    manifest = load_generation_manifest(project_dir)
    if not manifest:
        raise RuntimeError("No generation manifest found. Run 'init' first.")

    target_gen = generation if generation is not None else int(manifest.get("active_generation", 1))

    for entry in manifest.get("generations", []):
        if entry["generation_id"] == target_gen:
            if archive_path not in entry.get("archived_paths", []):
                entry.setdefault("archived_paths", []).append(archive_path)
            save_generation_manifest(project_dir, manifest)
            return

    raise ValueError(f"Generation {target_gen} not found in manifest.")


def _parse_json_arg(value: str) -> dict:
    """
    Parse a JSON argument that is either an inline JSON string or a @filepath
    pointing to a JSON file. Raises ValueError on parse failure.
    """
    if value.startswith("@"):
        file_path = value[1:]
        with open(file_path, "r") as f:
            return json.load(f)
    return json.loads(value)


def load_state(project_dir: str) -> dict:
    state_path = os.path.join(project_dir, STATE_FILE)
    if not os.path.exists(state_path):
        return {}
    with open(state_path, "r") as f:
        return json.load(f)


def save_state(project_dir: str, state: dict):
    state_path = os.path.join(project_dir, STATE_FILE)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def ensure_project_structure(base_dir: str, project_slug: str) -> str:
    """Create the canonical project folder structure and return the project_dir (relative)."""
    project_dir_rel = os.path.join("projects", project_slug)
    project_dir_abs = os.path.join(base_dir, project_dir_rel)

    for subdir in PROJECT_SUBDIRS:
        os.makedirs(os.path.join(project_dir_abs, subdir), exist_ok=True)

    return project_dir_rel


def slugify(text: str) -> str:
    """Best-effort slug generator (kebab-case, ascii-ish) for project names."""
    import re

    if not text:
        return ""
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def parse_frontmatter_md(text: str) -> dict:
    """
    Minimal YAML-frontmatter parser for RESEARCH_PROPOSAL.md.
    Supports:
    - key: value
    - key:
        - item
        - item
    - quoted strings
    This is intentionally tiny (no external deps).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    i = 1
    current_list_key: Optional[str] = None
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        if line.startswith("  - ") and current_list_key:
            out.setdefault(current_list_key, [])
            out[current_list_key].append(line[4:].strip().strip('"').strip("'"))
            i += 1
            continue

        current_list_key = None
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                # start list block (expect indented "- item" lines)
                current_list_key = key
                out[current_list_key] = []
            else:
                out[key] = val.strip().strip('"').strip("'")
        i += 1
    return out


def load_inputs(base_dir: str, inputs_path: Optional[str] = None) -> dict:
    """
    Load pre-pipeline inputs (JSON) used to infer project slug and topic.

    Resolution order:
    - explicit inputs_path (relative to base_dir or absolute)
    - DEFAULT_INPUTS_FILE in base_dir (if present)
    - else: {}
    """
    candidate: Optional[Path] = None
    if inputs_path:
        p = Path(inputs_path)
        candidate = p if p.is_absolute() else (Path(base_dir) / p)
    else:
        p = Path(base_dir) / DEFAULT_INPUTS_FILE
        candidate = p if p.exists() else None

    if not candidate or not candidate.exists():
        return {}

    try:
        raw = Path(str(candidate)).read_text(encoding="utf-8", errors="replace")
        if str(candidate).lower().endswith(".json"):
            return json.loads(raw)
        if str(candidate).lower().endswith(".md"):
            fm = parse_frontmatter_md(raw)
            # Normalize to the same shape as the JSON contract.
            project = {}
            research = {}
            if fm.get("project_slug"):
                project["slug"] = fm["project_slug"]
            if fm.get("display_title"):
                project["display_title"] = fm["display_title"]
            if fm.get("research_topic"):
                research["topic"] = fm["research_topic"]
            if fm.get("domain_hints"):
                research["domain_hints"] = fm["domain_hints"]
            out = {"project": project, "research": research}
            constraints = {}
            if fm.get("target_venue"):
                constraints["target_venue"] = fm["target_venue"]
            if constraints:
                out["constraints"] = constraints
            execution_defaults = {}
            if fm.get("skip_online") != "":
                if str(fm.get("skip_online", "")).lower() in ("true", "false"):
                    execution_defaults["skip_online"] = str(fm["skip_online"]).lower() == "true"
            if execution_defaults:
                out["execution_defaults"] = execution_defaults
            compute_defaults = {}
            if fm.get("seeds_per_condition"):
                try:
                    compute_defaults["seeds_per_condition"] = int(fm["seeds_per_condition"])
                except Exception:
                    pass
            if fm.get("gpus_per_job"):
                try:
                    compute_defaults["gpus_per_job"] = int(fm["gpus_per_job"])
                except Exception:
                    pass
            if compute_defaults:
                out["compute_defaults"] = compute_defaults
            return out
        return {}
    except Exception as e:
        print(f"WARNING: failed to parse inputs file {candidate}: {e}", file=sys.stderr)
        return {}


def init_state(base_dir: str, force: bool = False,
               project_slug: Optional[str] = None,
               research_topic: Optional[str] = None,
               inputs_path: Optional[str] = None) -> dict:
    state_path = os.path.join(base_dir, STATE_FILE)
    if os.path.exists(state_path) and not force:
        print(f"State file already exists: {state_path}")
        print("Use --force to reinitialize.")
        return load_state(base_dir)

    inputs = load_inputs(base_dir, inputs_path=inputs_path)

    # Infer project_slug and research_topic from inputs if not provided.
    if not project_slug:
        project_slug = (
            inputs.get("project", {}).get("slug")
            or slugify(inputs.get("project", {}).get("display_title", ""))
            or slugify(inputs.get("research", {}).get("topic", ""))
            or None
        )

    if not research_topic:
        rt = inputs.get("research", {}).get("topic")
        research_topic = rt.strip() if isinstance(rt, str) else None

    # Determine project_dir
    project_dir_rel = None
    if project_slug:
        project_dir_rel = ensure_project_structure(base_dir, project_slug)
        print(f"Project structure created: {project_dir_rel}/")

    state = {
        "version": 2,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "mode": "interactive",
        "project_dir": project_dir_rel,
        "research_topic": (research_topic.strip() if research_topic else None),
        "steps": {},
    }

    for step_id, command, description, prereqs, needs_online in PIPELINE_STEPS:
        state["steps"][step_id] = {
            "command": command,
            "description": description,
            "prerequisite_files": prereqs,
            "needs_online": needs_online,
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "skipped": False,
            "failure_reason": None,
            "slurm_job_id": None,
        }

    save_state(base_dir, state)
    print(f"Pipeline state initialized: {state_path}")
    if project_dir_rel:
        print(f"Project directory: {project_dir_rel}")

    # Package 2: initialize state/ directory and generation manifest
    _ensure_state_dir(base_dir)
    manifest_path = _generation_manifest_path(base_dir)
    if not os.path.exists(manifest_path):
        init_generation_manifest(base_dir)
        print(f"Generation manifest initialized: {manifest_path}")
    else:
        print(f"Generation manifest already exists: {manifest_path}")

    return state


def get_step_order():
    return [s[0] for s in PIPELINE_STEPS]


def find_next_step(state: dict) -> Optional[str]:
    order = get_step_order()
    for step_id in order:
        step = state["steps"].get(step_id, {})
        if step.get("status") in ("pending", "failed"):
            return step_id
    return None


def print_status(state: dict):
    order = get_step_order()
    symbols = {
        "pending": "  ",
        "running": ">>",
        "completed": "OK",
        "skipped": "--",
        "failed": "!!",
    }

    print()
    print("Pipeline Status")
    print("=" * 70)
    print(f"  Created:     {state.get('created_at', 'N/A')}")
    print(f"  Updated:     {state.get('updated_at', 'N/A')}")
    print(f"  Mode:        {state.get('mode', 'interactive')}")
    project_dir = state.get('project_dir')
    if project_dir:
        print(f"  Project dir: {project_dir}/")
    else:
        print(f"  Project dir: (not set — legacy state)")
    topic = state.get("research_topic")
    if topic:
        print(f"  Research topic: {topic}")
    else:
        print(f"  Research topic: (not set — pass init --topic or set in pipeline-state.json for /run-pipeline)")
    print()

    for i, step_id in enumerate(order, 1):
        step = state["steps"].get(step_id, {})
        status = step.get("status", "pending")
        sym = symbols.get(status, "??")
        cmd = step.get("command", "")
        desc = step.get("description", "")

        line = f"  [{sym}] {i:2d}. {cmd:<25s} {desc}"
        if status == "completed" and step.get("completed_at"):
            line += f"  ({step['completed_at'][:10]})"
        elif status == "failed" and step.get("failure_reason"):
            line += f"  FAIL: {step['failure_reason'][:40]}"
        elif status == "skipped":
            line += "  (skipped)"
        print(line)

    next_step = find_next_step(state)
    print()
    if next_step:
        print(f"  Next step: {state['steps'][next_step]['command']}")
    else:
        completed = sum(
            1
            for s in state["steps"].values()
            if s.get("status") in ("completed", "skipped")
        )
        total = len(state["steps"])
        print(f"  All {total} steps done ({completed} completed).")
    print()


def mark_start(state: dict, step_id: str) -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "running"
    state["steps"][step_id]["started_at"] = now_iso()
    state["updated_at"] = now_iso()
    return state


def mark_complete(state: dict, step_id: str) -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "completed"
    state["steps"][step_id]["completed_at"] = now_iso()
    state["updated_at"] = now_iso()
    return state


def mark_skip(state: dict, step_id: str) -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "skipped"
    state["steps"][step_id]["skipped"] = True
    state["steps"][step_id]["completed_at"] = now_iso()
    state["updated_at"] = now_iso()
    return state


def mark_fail(state: dict, step_id: str, reason: str = "") -> dict:
    if step_id not in state["steps"]:
        print(f"Unknown step: {step_id}", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "failed"
    state["steps"][step_id]["failure_reason"] = reason
    state["updated_at"] = now_iso()
    return state


def main():
    parser = argparse.ArgumentParser(description="Pipeline state manager")
    parser.add_argument(
        "--dir",
        default=os.environ.get("PROJECT_DIR", os.getcwd()),
        help="Project directory (default: cwd or $PROJECT_DIR)",
    )
    sub = parser.add_subparsers(dest="action")
    sub.required = True

    p_init = sub.add_parser("init", help="Initialize pipeline state")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--project", help="Project slug (creates projects/<slug>/ structure)")
    p_init.add_argument(
        "--inputs",
        default=None,
        help=f"Path to pre-pipeline inputs JSON (default: {DEFAULT_INPUTS_FILE} if present). "
             "Used to infer --project and --topic when omitted.",
    )
    p_init.add_argument(
        "--topic",
        default=None,
        help="Research question / topic string stored in pipeline-state.json for /run-pipeline (e.g. Pass 1 /research-landscape).",
    )

    sub.add_parser("status", help="Show pipeline status")

    p_start = sub.add_parser("start", help="Mark step as running")
    p_start.add_argument("step_id")

    p_complete = sub.add_parser("complete", help="Mark step as completed")
    p_complete.add_argument("step_id")

    p_skip = sub.add_parser("skip", help="Mark step as skipped")
    p_skip.add_argument("step_id")

    p_fail = sub.add_parser("fail", help="Mark step as failed")
    p_fail.add_argument("step_id")

    p_slurm = sub.add_parser("set-slurm-job", help="Associate a SLURM job ID with a step")
    p_slurm.add_argument("step_id")
    p_slurm.add_argument("job_id", type=int)
    p_fail.add_argument("--reason", default="")

    sub.add_parser("next", help="Print next pending step")

    sub.add_parser("reset", help="Reset all steps to pending")

    sub.add_parser("steps", help="List all step IDs")

    p_inc = sub.add_parser(
        "increment-counter",
        help="Increment a feedback loop counter field in pipeline-state.json. "
             "Exits 0 if counter is below max, exits 1 if counter has reached or exceeded max.",
    )
    p_inc.add_argument("field", help="Counter field name (e.g. reposition_count)")
    p_inc.add_argument(
        "--max", type=int, default=0,
        help="Maximum allowed value (0 = no limit). Exits 1 if current >= max before incrementing.",
    )

    p_get = sub.add_parser(
        "get-field",
        help="Print the value of a top-level field in pipeline-state.json. "
             "Exits 0 if found, 1 if missing.",
    )
    p_get.add_argument("field", help="Field name to read")

    # --- Package 2: new subcommands ---

    p_reset_range = sub.add_parser(
        "reset-range",
        help="Reset step statuses to pending for an inclusive step range only. "
             "Does not clear loop counters (use 'reset' for a full reset).",
    )
    p_reset_range.add_argument("from_step_id", help="First step in range (inclusive)")
    p_reset_range.add_argument("to_step_id", help="Last step in range (inclusive)")

    sub.add_parser(
        "get-generation",
        help="Print the active generation number from state/generation-manifest.json.",
    )

    p_set_gen = sub.add_parser(
        "set-generation",
        help="Set active_generation in state/generation-manifest.json.",
    )
    p_set_gen.add_argument("generation", type=int, help="Generation number to activate")

    p_new_gen = sub.add_parser(
        "new-generation",
        help="Append a new generation entry to state/generation-manifest.json and activate it. "
             "Returns the new generation ID on stdout.",
    )
    p_new_gen.add_argument(
        "--trigger-reason",
        required=True,
        help="Human-readable reason this generation was created (e.g. 'N1 REPOSITION #1').",
    )
    p_new_gen.add_argument(
        "--rerun-from",
        default=None,
        help="First step in the rerun range for this generation (optional).",
    )
    p_new_gen.add_argument(
        "--rerun-to",
        default=None,
        help="Last step in the rerun range for this generation (optional).",
    )

    p_write_result = sub.add_parser(
        "write-step-result",
        help="Write (overwrite) state/step-results/<step_id>.json. "
             "Accepts inline JSON or @filepath.",
    )
    p_write_result.add_argument("step_id", help="Step ID")
    p_write_result.add_argument(
        "json_data",
        help="JSON object as a string, or @path/to/file.json to read from a file.",
    )

    p_append_decision = sub.add_parser(
        "append-decision",
        help="Append one JSON record to state/decision-log.jsonl. "
             "Accepts inline JSON or @filepath.",
    )
    p_append_decision.add_argument(
        "json_data",
        help="JSON object as a string, or @path/to/file.json to read from a file.",
    )

    sub.add_parser(
        "check-readiness",
        help="Read state/execution-readiness.json and exit 0 if ready_for_analysis is true, "
             "exit 1 if absent, malformed, or ready_for_analysis is false. "
             "Use as a hard pre-start block before analyze-results.",
    )

    p_add_archive = sub.add_parser(
        "add-archive-path",
        help="Append a path string to the archived_paths list of a generation entry "
             "in state/generation-manifest.json. Defaults to the active generation.",
    )
    p_add_archive.add_argument(
        "archive_path",
        help="Path to record (relative to project_dir, e.g. 'archive/gen-1/docs').",
    )
    p_add_archive.add_argument(
        "--generation",
        type=int,
        default=None,
        help="Generation ID to update (default: active generation).",
    )

    # --- Context budget / handoff subcommands ---

    p_write_handoff = sub.add_parser(
        "write-handoff",
        help="Write state/handoffs/<step_id>.json — a compressed step summary for "
             "context-efficient loading by downstream steps. Accepts inline JSON or @filepath.",
    )
    p_write_handoff.add_argument(
        "step_id",
        help="Step ID that produced this handoff (may be a sub-step, e.g. 'research-landscape-batch-1').",
    )
    p_write_handoff.add_argument(
        "json_data",
        help="JSON object as a string, or @path/to/file.json to read from a file. "
             "Required fields: key_outputs (dict), summary (str), "
             "critical_context (list), token_estimate (int).",
    )

    p_check_budget = sub.add_parser(
        "check-budget",
        help="Measure total char size of prerequisite files for a step. "
             "Exits 0 (OK), 2 (HIGH: >threshold chars). "
             "Prints JSON with sizes, status, and available handoff alternatives.",
    )
    p_check_budget.add_argument(
        "step_id",
        help="Step ID to check budget for.",
    )
    p_check_budget.add_argument(
        "--threshold",
        type=int,
        default=100_000,
        help="Char threshold for HIGH status (default: 100000 chars ≈ 25K tokens).",
    )

    args = parser.parse_args()

    if args.action == "init":
        init_state(
            args.dir,
            force=args.force,
            project_slug=getattr(args, "project", None),
            research_topic=getattr(args, "topic", None),
            inputs_path=getattr(args, "inputs", None),
        )
        return

    state = load_state(args.dir)
    if not state:
        print("No pipeline state found. Run: python pipeline_state.py init",
              file=sys.stderr)
        sys.exit(1)

    if args.action == "status":
        print_status(state)

    elif args.action == "start":
        state = mark_start(state, args.step_id)
        save_state(args.dir, state)
        print(f"Started: {args.step_id}")

    elif args.action == "complete":
        step_id = args.step_id
        _resolved_project_dir = os.path.join(args.dir, state.get("project_dir") or "")
        failures = check_completion_contracts(_resolved_project_dir, step_id, state_root=args.dir)
        if failures:
            reason = "; ".join(failures)
            state = mark_fail(state, step_id, reason=reason)
            save_state(args.dir, state)
            print(
                f"[FAIL-CLOSED] Step '{step_id}' cannot be marked complete.\n"
                + "\n".join(f"  • {f}" for f in failures),
                file=sys.stderr,
            )
            print(f"Step '{step_id}' marked as FAILED. Resolve the above issues, then retry.")
            sys.exit(1)
        state = mark_complete(state, step_id)
        save_state(args.dir, state)
        print(f"Completed: {step_id}")

    elif args.action == "skip":
        state = mark_skip(state, args.step_id)
        save_state(args.dir, state)
        print(f"Skipped: {args.step_id}")

    elif args.action == "fail":
        state = mark_fail(state, args.step_id, reason=args.reason)
        save_state(args.dir, state)
        print(f"Failed: {args.step_id}")

    elif args.action == "next":
        next_id = find_next_step(state)
        if next_id:
            step = state["steps"][next_id]
            print(json.dumps({
                "step_id": next_id,
                "command": step["command"],
                "description": step["description"],
                "prerequisite_files": step["prerequisite_files"],
                "needs_online": step["needs_online"],
            }))
        else:
            print("{}")

    elif args.action == "reset":
        for step_id in state["steps"]:
            state["steps"][step_id]["status"] = "pending"
            state["steps"][step_id]["started_at"] = None
            state["steps"][step_id]["completed_at"] = None
            state["steps"][step_id]["skipped"] = False
            state["steps"][step_id]["failure_reason"] = None
            state["steps"][step_id]["slurm_job_id"] = None
        # W5 fix: clear all loop counters so a reset pipeline starts with
        # fresh loop budgets instead of inheriting exhausted counters.
        cleared_counters = []
        for field in list(LOOP_COUNTERS.keys()):
            if field in state:
                del state[field]
                cleared_counters.append(field)
        state["updated_at"] = now_iso()
        save_state(args.dir, state)
        print("All steps reset to pending.")
        if cleared_counters:
            print(f"Loop counters cleared: {', '.join(cleared_counters)}")
        else:
            print("Loop counters cleared: none were set.")

    elif args.action == "set-slurm-job":
        if args.step_id not in state["steps"]:
            print(f"Unknown step: {args.step_id}", file=sys.stderr)
            sys.exit(1)
        state["steps"][args.step_id]["slurm_job_id"] = args.job_id
        state["updated_at"] = now_iso()
        save_state(args.dir, state)
        print(f"Step {args.step_id} linked to SLURM job {args.job_id}")

    elif args.action == "steps":
        for step_id in get_step_order():
            print(step_id)

    elif args.action == "increment-counter":
        field = args.field
        max_val = args.max
        current = int(state.get(field, 0))

        if max_val > 0 and current >= max_val:
            print(
                f"Counter '{field}' has reached maximum ({current}/{max_val}). "
                f"Loop termination condition met.",
                file=sys.stderr,
            )
            sys.exit(1)

        state[field] = current + 1
        state["updated_at"] = now_iso()
        save_state(args.dir, state)

        new_val = state[field]
        limit_note = f"/{max_val}" if max_val > 0 else ""
        print(f"Counter '{field}' incremented to {new_val}{limit_note}")

        # Warn if one step below the limit
        if max_val > 0 and new_val >= max_val:
            print(
                f"WARNING: '{field}' is now at maximum ({new_val}/{max_val}). "
                f"Next loop trigger will terminate.",
                file=sys.stderr,
            )

    elif args.action == "get-field":
        field = args.field
        if field not in state:
            print(f"Field '{field}' not found in pipeline-state.json", file=sys.stderr)
            sys.exit(1)
        value = state[field]
        print(json.dumps(value) if not isinstance(value, str) else value)

    # --- Package 2: new action handlers ---

    elif args.action == "reset-range":
        order = get_step_order()
        from_step = args.from_step_id
        to_step = args.to_step_id
        if from_step not in state["steps"]:
            print(f"Unknown step: {from_step}", file=sys.stderr)
            sys.exit(1)
        if to_step not in state["steps"]:
            print(f"Unknown step: {to_step}", file=sys.stderr)
            sys.exit(1)
        try:
            from_idx = order.index(from_step)
            to_idx = order.index(to_step)
        except ValueError as exc:
            print(f"Step not in canonical order: {exc}", file=sys.stderr)
            sys.exit(1)
        if from_idx > to_idx:
            print(
                f"from_step '{from_step}' (position {from_idx + 1}) must come before "
                f"to_step '{to_step}' (position {to_idx + 1})",
                file=sys.stderr,
            )
            sys.exit(1)
        reset_ids = order[from_idx : to_idx + 1]
        for step_id in reset_ids:
            state["steps"][step_id]["status"] = "pending"
            state["steps"][step_id]["started_at"] = None
            state["steps"][step_id]["completed_at"] = None
            state["steps"][step_id]["skipped"] = False
            state["steps"][step_id]["failure_reason"] = None
            state["steps"][step_id]["slurm_job_id"] = None
        state["updated_at"] = now_iso()
        save_state(args.dir, state)
        print(f"Reset {len(reset_ids)} steps to pending: {from_step} → {to_step}")

    elif args.action == "get-generation":
        gen = get_active_generation(args.dir)
        print(gen)

    elif args.action == "set-generation":
        set_active_generation(args.dir, args.generation)
        print(f"Active generation set to {args.generation}")

    elif args.action == "new-generation":
        gen_id = new_generation(
            args.dir,
            trigger_reason=args.trigger_reason,
            rerun_from=args.rerun_from,
            rerun_to=args.rerun_to,
        )
        print(f"New generation created: {gen_id}")

    elif args.action == "write-step-result":
        try:
            result = _parse_json_arg(args.json_data)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            print(f"Error parsing step result JSON: {exc}", file=sys.stderr)
            sys.exit(1)
        # Inject required fields if caller omitted them
        result.setdefault("step_id", args.step_id)
        result.setdefault("generation", get_active_generation(args.dir))
        result.setdefault("created_at", now_iso())
        result.setdefault("$schema", "step-result-v1")
        write_step_result(args.dir, args.step_id, result)
        path = _step_result_path(args.dir, args.step_id)
        print(f"Step result written: {path}")

    elif args.action == "append-decision":
        try:
            record = _parse_json_arg(args.json_data)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            print(f"Error parsing decision JSON: {exc}", file=sys.stderr)
            sys.exit(1)
        # Inject required fields if caller omitted them
        record.setdefault("timestamp", now_iso())
        record.setdefault("generation", get_active_generation(args.dir))
        record.setdefault("$schema", "decision-v1")
        append_decision_record(args.dir, record)
        path = _decision_log_path(args.dir)
        print(f"Decision appended to: {path}")

    elif args.action == "check-readiness":
        readiness_path = os.path.join(args.dir, STATE_DIR, "execution-readiness.json")
        if not os.path.exists(readiness_path):
            print(
                f"[BLOCK] state/execution-readiness.json not found at {readiness_path}.\n"
                "        Run check_gates.py --output-json first.",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            with open(readiness_path) as f:
                readiness = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"[BLOCK] state/execution-readiness.json is unreadable: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        if not readiness.get("ready_for_analysis"):
            reason = readiness.get("blocking_reason") or "ready_for_analysis is false"
            print(
                f"[BLOCK] Execution not ready for analysis: {reason}\n"
                f"        Completion: {readiness.get('observed_runs')}/{readiness.get('expected_runs')} "
                f"({readiness.get('completion_ratio', 0):.1%})",
                file=sys.stderr,
            )
            sys.exit(1)
        # Ready
        gen = readiness.get("generation", "?")
        ratio = readiness.get("completion_ratio", 0)
        obs = readiness.get("observed_runs")
        exp = readiness.get("expected_runs")
        print(
            f"[READY] Execution ready for analysis "
            f"(gen {gen}: {obs}/{exp} runs = {ratio:.1%})"
        )

    elif args.action == "add-archive-path":
        target_gen = getattr(args, "generation", None)
        try:
            add_archive_path(args.dir, args.archive_path, generation=target_gen)
        except (RuntimeError, ValueError) as exc:
            print(f"Error updating archive paths: {exc}", file=sys.stderr)
            sys.exit(1)
        resolved_gen = target_gen if target_gen is not None else get_active_generation(args.dir)
        print(f"Archive path '{args.archive_path}' recorded for generation {resolved_gen}")

    # --- Context budget / handoff handlers ---

    elif args.action == "write-handoff":
        try:
            handoff = _parse_json_arg(args.json_data)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            print(f"Error parsing handoff JSON: {exc}", file=sys.stderr)
            sys.exit(1)
        # Validate required fields
        missing = [f for f in HANDOFF_REQUIRED_FIELDS if f not in handoff]
        if missing:
            print(
                f"[ERROR] Handoff JSON missing required field(s): {', '.join(missing)}\n"
                f"Required: key_outputs (dict), summary (str), "
                f"critical_context (list), token_estimate (int).",
                file=sys.stderr,
            )
            sys.exit(1)
        # Auto-inject schema fields
        handoff.setdefault("$schema", "step-handoff-v1")
        handoff.setdefault("step_id", args.step_id)
        handoff.setdefault("created_at", now_iso())
        handoff.setdefault("generation", get_active_generation(args.dir))
        # Write to state/handoffs/<step_id>.json
        handoffs_dir = os.path.join(args.dir, STATE_DIR, "handoffs")
        os.makedirs(handoffs_dir, exist_ok=True)
        handoff_path = os.path.join(handoffs_dir, f"{args.step_id}.json")
        with open(handoff_path, "w") as f:
            json.dump(handoff, f, indent=2)
        print(f"Handoff written: {handoff_path}")

    elif args.action == "check-budget":
        step_id = args.step_id
        threshold = args.threshold
        if step_id not in state["steps"]:
            print(f"Unknown step: {step_id}", file=sys.stderr)
            sys.exit(1)
        prereqs = state["steps"][step_id].get("prerequisite_files", [])
        # Resolve project_dir (may be relative to args.dir)
        project_dir_raw = state.get("project_dir") or args.dir
        if os.path.isabs(project_dir_raw):
            project_dir = project_dir_raw
        else:
            project_dir = os.path.join(args.dir, project_dir_raw)

        files_result: list = []
        total_chars = 0
        for rel in prereqs:
            full = os.path.join(project_dir, rel)
            if os.path.isfile(full):
                try:
                    size = os.path.getsize(full)
                    files_result.append({"file": rel, "chars": size, "exists": True})
                    total_chars += size
                except OSError:
                    files_result.append({"file": rel, "chars": 0, "exists": False})
            elif os.path.isdir(full):
                dir_size = sum(
                    os.path.getsize(os.path.join(dp, fn))
                    for dp, _, fns in os.walk(full)
                    for fn in fns
                )
                files_result.append({"file": rel, "chars": dir_size, "exists": True, "type": "dir"})
                total_chars += dir_size
            else:
                files_result.append({"file": rel, "chars": 0, "exists": False})

        # Collect available handoff alternatives
        handoffs_dir = os.path.join(project_dir, STATE_DIR, "handoffs")
        handoff_alternatives: list[str] = []
        if os.path.isdir(handoffs_dir):
            handoff_alternatives = sorted(
                f"state/handoffs/{fn}"
                for fn in os.listdir(handoffs_dir)
                if fn.endswith(".json")
            )

        budget_status = "HIGH" if total_chars > threshold else "OK"
        result = {
            "step_id": step_id,
            "total_chars": total_chars,
            "threshold": threshold,
            "budget_status": budget_status,
            "files": files_result,
            "handoff_alternatives": handoff_alternatives,
        }
        if budget_status == "HIGH":
            result["recommendation"] = (
                f"Total prereq size {total_chars:,} chars exceeds {threshold:,} char threshold. "
                f"Load state/handoffs/<dep_step>.json summaries instead of full documents."
            )
        print(json.dumps(result, indent=2))
        sys.exit(2 if budget_status == "HIGH" else 0)


if __name__ == "__main__":
    main()
