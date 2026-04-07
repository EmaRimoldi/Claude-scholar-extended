#!/usr/bin/env python3
"""
kill_decision.py — Evaluate kill criteria for a research project.

Reads structured reports from the multi-pass search system and evaluates
whether any hard kill criterion has been triggered. Produces a machine-readable
JSON result for use by the novelty-gate command and pipeline orchestrator.

Usage:
    # Evaluate kill criteria
    python scripts/kill_decision.py \
        --claim-overlap $PROJECT_DIR/claim-overlap-report.md \
        --adversarial $PROJECT_DIR/adversarial-novelty-report.md \
        --concurrent $PROJECT_DIR/concurrent-work-report.md \
        --pipeline-state $PROJECT_DIR/pipeline-state.json \
        --output $PROJECT_DIR/kill-decision.json

    # Log a kill decision (and terminate pipeline)
    python scripts/kill_decision.py --log-kill \
        --project $PROJECT_DIR \
        --reason "Full anticipation by [Author et al. 2025]"

    # Trigger a specific criterion directly (used by orchestrator for loop termination)
    python scripts/kill_decision.py --log-kill \
        --criterion failed_reposition \
        --project $PROJECT_DIR \
        --reason "Gate N1 failed after 2 repositioning attempts"

    # Override a kill (human override)
    python scripts/kill_decision.py --override-kill \
        --project $PROJECT_DIR \
        --justification "Results are 40% better despite overlap; contribution is scale novelty"

    # Human override for significance_collapse specifically
    python scripts/kill_decision.py --override-kill --human-override \
        --project $PROJECT_DIR \
        --justification "Effect size is large enough for the venue despite weak rebuttal"

Kill criteria (from research-system-spec.md Part 6):
  1. full_anticipation    — prior paper: same method + same task + comparable results
  2. marginal_differentiation — closest prior differs only in minor details, result not surprising
  3. failed_reposition    — repositioned >= 2 times, still no clear novelty angle
  4. significance_collapse — technically novel but no evidence anyone cares
  5. concurrent_scoop     — paper appeared during execution fully anticipating contribution
                            (1 emergency reposition allowed)

Exit codes:
  0 — PROCEED: no kill criteria triggered
  1 — KILL: kill criteria triggered (hard stop)
  2 — REPOSITION: marginal differentiation or concurrent scoop (loop back to Step 3 with counter)
  3 — PIVOT: insufficient novelty, adjacent open problem identified (loop back to Step 1)
  4 — Error reading input files
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsers for markdown report files
# ---------------------------------------------------------------------------

def extract_section(text: str, section_heading: str) -> str:
    """Extract text under a markdown heading until the next same-level heading."""
    # Match ## Section heading
    pattern = rf"##\s+{re.escape(section_heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_claim_overlap(path: Path) -> dict:
    """
    Extract threat level and high-overlap paper count from claim-overlap-report.md.
    Returns:
        {
            "overall_threat_level": "CRITICAL|HIGH|MEDIUM|LOW",
            "high_overlap_count": int,
            "kill_signal_flags": [str],
            "full_anticipation_detected": bool
        }
    """
    if not path.exists():
        return {"error": f"File not found: {path}"}

    text = path.read_text()
    result: dict = {
        "overall_threat_level": "LOW",
        "high_overlap_count": 0,
        "kill_signal_flags": [],
        "full_anticipation_detected": False,
    }

    # Extract threat level
    threat_match = re.search(
        r"Overall threat level[:\*\s]+([A-Z]+)", text, re.IGNORECASE
    )
    if threat_match:
        result["overall_threat_level"] = threat_match.group(1).upper()

    # Count HIGH overlap papers
    result["high_overlap_count"] = len(
        re.findall(r"\*\*Overlap level:\*\*\s*HIGH", text, re.IGNORECASE)
    )

    # Check for kill signal flags section
    kill_section = extract_section(text, "Kill Signal Flags")
    if kill_section and "could not be written" in kill_section.lower():
        result["kill_signal_flags"].append(
            "Differential statement could not be written for HIGH-overlap paper"
        )

    # Full anticipation: CRITICAL threat + multiple HIGH overlaps on all components
    if result["overall_threat_level"] == "CRITICAL":
        result["full_anticipation_detected"] = True

    return result


def parse_adversarial(path: Path) -> dict:
    """
    Extract rebuttal strength and kill signals from adversarial-novelty-report.md.
    Returns:
        {
            "rebuttal_strength": "STRONG|WEAK|UNABLE_TO_WRITE",
            "kill_signals_count": int,
            "recommendation": "PROCEED|REPOSITION|PIVOT|KILL",
            "marginal_differentiation": bool
        }
    """
    if not path.exists():
        return {"error": f"File not found: {path}"}

    text = path.read_text()
    result: dict = {
        "rebuttal_strength": "STRONG",
        "kill_signals_count": 0,
        "recommendation": "PROCEED",
        "marginal_differentiation": False,
    }

    # Rebuttal strength
    rb_match = re.search(
        r"Rebuttal strength[:\*\s]+(STRONG|WEAK|UNABLE TO WRITE|UNABLE_TO_WRITE)",
        text, re.IGNORECASE
    )
    if rb_match:
        result["rebuttal_strength"] = rb_match.group(1).upper().replace(" ", "_")

    # Kill signals count
    ks_match = re.search(r"Kill signals triggered[:\*\s]+(\d+)", text, re.IGNORECASE)
    if ks_match:
        result["kill_signals_count"] = int(ks_match.group(1))

    # Recommendation
    rec_match = re.search(
        r"Recommendation[:\*\s]+(PROCEED|REPOSITION|PIVOT|KILL)",
        text, re.IGNORECASE
    )
    if rec_match:
        result["recommendation"] = rec_match.group(1).upper()

    # Marginal differentiation check
    closest_section = extract_section(text, "Closest Prior Work Attack")
    if re.search(r"Is.*meaningful advance.*NO|MARGINAL", closest_section, re.IGNORECASE):
        result["marginal_differentiation"] = True

    return result


def parse_concurrent(path: Path) -> dict:
    """
    Extract concurrent work severity from concurrent-work-report.md.
    Returns:
        {
            "max_severity": "blocks_project|requires_repositioning|should_be_cited|no_impact",
            "blocks_project_count": int,
            "scoop_detected": bool
        }
    """
    if not path.exists():
        return {"error": f"File not found: {path}"}

    text = path.read_text()
    result: dict = {
        "max_severity": "no_impact",
        "blocks_project_count": 0,
        "scoop_detected": False,
    }

    blocks = len(re.findall(r"blocks_project", text, re.IGNORECASE))
    requires = len(re.findall(r"requires_repositioning", text, re.IGNORECASE))

    result["blocks_project_count"] = blocks
    if blocks > 0:
        result["max_severity"] = "blocks_project"
        result["scoop_detected"] = True
    elif requires > 0:
        result["max_severity"] = "requires_repositioning"

    return result


def get_reposition_count(pipeline_state_path: Path) -> int:
    """Read number of reposition loops from pipeline-state.json."""
    if not pipeline_state_path.exists():
        return 0
    try:
        state = json.loads(pipeline_state_path.read_text())
        return int(state.get("reposition_count", 0))
    except (json.JSONDecodeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Kill criteria evaluation
# ---------------------------------------------------------------------------

def evaluate_kill_criteria(
    claim_overlap: dict,
    adversarial: dict,
    concurrent: dict,
    reposition_count: int,
) -> dict:
    """
    Evaluate all 5 kill criteria. Returns a structured verdict.
    """
    triggered: list[dict] = []
    warnings: list[str] = []

    # --- Criterion 1: Full anticipation ---
    if claim_overlap.get("full_anticipation_detected") or adversarial.get("recommendation") == "KILL":
        triggered.append({
            "criterion": "full_anticipation",
            "description": "Prior work fully anticipates the proposed contribution",
            "evidence": {
                "threat_level": claim_overlap.get("overall_threat_level"),
                "adversarial_recommendation": adversarial.get("recommendation"),
            },
        })

    # --- Criterion 2: Marginal differentiation ---
    if adversarial.get("marginal_differentiation") and not claim_overlap.get("full_anticipation_detected"):
        # Marginal is a KILL unless results are surprisingly large (human judgment needed)
        triggered.append({
            "criterion": "marginal_differentiation",
            "description": "Closest prior work differs only in minor details; no surprising result confirmed",
            "note": "Can be overridden if actual results show surprisingly large improvement",
            "evidence": {"marginal_differentiation": True},
        })

    # --- Criterion 3: Failed reposition ---
    if reposition_count >= 2:
        triggered.append({
            "criterion": "failed_reposition",
            "description": f"Project repositioned {reposition_count} times; still no clear novelty angle",
            "evidence": {"reposition_count": reposition_count},
        })
    elif reposition_count == 1:
        warnings.append(f"Reposition count: {reposition_count}/2 — one more failed reposition triggers KILL")

    # --- Criterion 4: Significance collapse ---
    # Weak rebuttal strength is treated as a significance_collapse KILL signal.
    # Use --human-override / --override-kill if the human researcher judges the
    # effect size is large enough despite a weak rebuttal.
    if adversarial.get("rebuttal_strength") in ("WEAK", "UNABLE_TO_WRITE") and not triggered:
        triggered.append({
            "criterion": "significance_collapse",
            "description": (
                "Adversarial rebuttal is weak or could not be written, indicating the "
                "contribution may not be significant enough to publish. "
                "Human override available via: "
                "python scripts/kill_decision.py --override-kill --human-override "
                "--project $PROJECT_DIR --justification '...'"
            ),
            "evidence": {"rebuttal_strength": adversarial.get("rebuttal_strength")},
        })

    # --- Criterion 5: Concurrent scoop ---
    if concurrent.get("scoop_detected"):
        existing_triggered = [t["criterion"] for t in triggered]
        if "full_anticipation" not in existing_triggered:
            triggered.append({
                "criterion": "concurrent_scoop",
                "description": "A paper appeared during execution that fully anticipates the contribution",
                "note": "1 emergency repositioning attempt allowed before KILL",
                "evidence": {"blocks_project_count": concurrent.get("blocks_project_count")},
            })

    # --- Additional rebuttal-based signal ---
    if adversarial.get("rebuttal_strength") == "UNABLE_TO_WRITE" and not triggered:
        triggered.append({
            "criterion": "rebuttal_failure",
            "description": "Adversarial rebuttal could not be written — differential statement absent",
            "evidence": {"rebuttal_strength": "UNABLE_TO_WRITE"},
        })

    # --- Build verdict ---
    if triggered:
        triggered_names = {t["criterion"] for t in triggered}
        # REPOSITION: only marginal_differentiation or concurrent_scoop (single attempt allowed)
        reposition_only = triggered_names <= {"marginal_differentiation", "concurrent_scoop"}
        # PIVOT: adversarial recommendation says PIVOT and no hard-kill criterion
        hard_kill_criteria = {
            "full_anticipation", "failed_reposition", "rebuttal_failure", "significance_collapse"
        }
        has_hard_kill = bool(triggered_names & hard_kill_criteria)

        if reposition_only and not has_hard_kill:
            recommendation = "REPOSITION"
        else:
            recommendation = "KILL"
    elif adversarial.get("recommendation") == "PIVOT" and not triggered:
        recommendation = "PIVOT"
    elif warnings:
        recommendation = "PROCEED_WITH_CAUTION"
    else:
        recommendation = "PROCEED"

    return {
        "kill_criteria_triggered": len(triggered) > 0,
        "triggered_criteria": triggered,
        "warnings": warnings,
        "recommendation": recommendation,
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate kill criteria for a research project")
    parser.add_argument("--claim-overlap", default="", help="Path to claim-overlap-report.md")
    parser.add_argument("--adversarial", default="", help="Path to adversarial-novelty-report.md")
    parser.add_argument("--concurrent", default="", help="Path to concurrent-work-report.md")
    parser.add_argument("--pipeline-state", default="", help="Path to pipeline-state.json")
    parser.add_argument("--output", default="", help="Output path for kill-decision.json (full verdict)")
    parser.add_argument(
        "--gate-output",
        default="",
        help="Output path for normalized gate decision artifact (gate-decision-v1 schema). "
             "Intended for state/gates/<gate_id>.json. This is the PRIMARY routing source.",
    )
    parser.add_argument(
        "--gate-id",
        default="novelty-gate-n1",
        help="Gate identifier embedded in the gate artifact (default: novelty-gate-n1).",
    )
    parser.add_argument(
        "--generation",
        type=int,
        default=1,
        help="Active generation number to embed in the gate artifact (default: 1).",
    )
    parser.add_argument("--log-kill", action="store_true", help="Log a KILL decision and terminate pipeline (exit 1)")
    parser.add_argument("--override-kill", action="store_true", help="Override a KILL decision (human)")
    parser.add_argument("--human-override", action="store_true", help="Flag override as human-initiated (used with --override-kill for significance_collapse)")
    parser.add_argument("--criterion", help="Directly trigger a specific kill criterion (e.g. failed_reposition). Used with --log-kill by orchestrator.")
    parser.add_argument("--project", help="Project directory (for --log-kill / --override-kill)")
    parser.add_argument("--reason", help="Kill reason (for --log-kill)")
    parser.add_argument("--justification", help="Override justification (for --override-kill)")
    args = parser.parse_args()

    # Handle kill logging
    if args.log_kill:
        if not args.project:
            print("ERROR: --project required with --log-kill", file=sys.stderr)
            sys.exit(4)
        project = Path(args.project)
        state_path = project / "pipeline-state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        state["status"] = "killed"
        state["kill_reason"] = args.reason or "Not specified"
        state["kill_criterion"] = args.criterion or "not_specified"
        state["killed_at"] = datetime.utcnow().isoformat() + "Z"
        state_path.write_text(json.dumps(state, indent=2))

        criterion_note = f"\n**Criterion:** `{args.criterion}`\n" if args.criterion else ""
        kill_log = project / "kill-justification.md"
        kill_log.write_text(
            f"# Project Kill Justification\n\n"
            f"**Date:** {datetime.utcnow().date()}\n"
            f"{criterion_note}"
            f"\n**Reason:** {args.reason or 'Not specified'}\n\n"
            f"**Artifacts preserved:** All files in {project} are retained for future reuse.\n\n"
            f"**To override (human):** "
            f"`python scripts/kill_decision.py --override-kill --human-override "
            f"--project {project} --justification '...'`\n"
        )
        print(f"Project killed. Justification written to {kill_log}")
        sys.exit(1)

    # Handle kill override
    if args.override_kill:
        if not args.project or not args.justification:
            print("ERROR: --project and --justification required with --override-kill", file=sys.stderr)
            sys.exit(4)
        project = Path(args.project)
        state_path = project / "pipeline-state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        state["status"] = "kill_overridden"
        state["kill_override_justification"] = args.justification
        state["kill_overridden_at"] = datetime.utcnow().isoformat() + "Z"
        if args.human_override:
            state["human_override"] = True
        state_path.write_text(json.dumps(state, indent=2))
        print(f"Kill override logged. Project status: kill_overridden")
        sys.exit(0)

    # Standard evaluation
    if not args.output and not args.gate_output:
        print(
            "ERROR: at least one of --output or --gate-output is required for evaluation mode",
            file=sys.stderr,
        )
        sys.exit(4)

    claim_overlap = parse_claim_overlap(Path(args.claim_overlap)) if args.claim_overlap else {}
    adversarial = parse_adversarial(Path(args.adversarial)) if args.adversarial else {}
    concurrent = parse_concurrent(Path(args.concurrent)) if args.concurrent else {}
    reposition_count = get_reposition_count(Path(args.pipeline_state)) if args.pipeline_state else 0

    for name, data in [("claim_overlap", claim_overlap), ("adversarial", adversarial), ("concurrent", concurrent)]:
        if isinstance(data, dict) and "error" in data:
            print(f"WARNING: {name}: {data['error']}", file=sys.stderr)

    verdict = evaluate_kill_criteria(claim_overlap, adversarial, concurrent, reposition_count)

    # Build inputs list for gate artifact
    inputs_used = []
    if args.claim_overlap:
        inputs_used.append(args.claim_overlap)
    if args.adversarial:
        inputs_used.append(args.adversarial)
    if args.concurrent:
        inputs_used.append(args.concurrent)

    # Build human-readable reason summary
    if verdict["triggered_criteria"]:
        reason_parts = [tc["description"] for tc in verdict["triggered_criteria"]]
        reason = "; ".join(reason_parts)
    elif verdict["warnings"]:
        reason = "; ".join(verdict["warnings"])
    else:
        reason = "No kill criteria triggered. Novelty claim supported."

    # Write full verdict to --output (human + downstream use)
    if args.output:
        verdict["inputs"] = {
            "claim_overlap_summary": claim_overlap,
            "adversarial_summary": adversarial,
            "concurrent_summary": concurrent,
            "reposition_count": reposition_count,
        }
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(verdict, indent=2))
        print(f"Full verdict written to {output_path}")

    # Write normalized gate decision artifact to --gate-output (PRIMARY routing source)
    if args.gate_output:
        gate_artifact = {
            "$schema": "gate-decision-v1",
            "gate_id": args.gate_id,
            "decision_type": "routing",
            "decision": verdict["recommendation"],
            "generation": args.generation,
            "trigger_step": args.gate_id,
            "reason": reason,
            "inputs_used": inputs_used,
            "validator_used": "kill_decision.py",
            "kill_criteria_triggered": verdict["kill_criteria_triggered"],
            "triggered_criteria": [tc["criterion"] for tc in verdict["triggered_criteria"]],
            "warnings": verdict["warnings"],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        gate_path = Path(args.gate_output)
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(json.dumps(gate_artifact, indent=2))
        print(f"Gate artifact written to {gate_path}")

    print(f"Kill decision: {verdict['recommendation']}")
    if verdict["triggered_criteria"]:
        for tc in verdict["triggered_criteria"]:
            print(f"  [TRIGGERED] {tc['criterion']}: {tc['description']}")
    for w in verdict["warnings"]:
        print(f"  [WARNING] {w}")

    recommendation = verdict["recommendation"]
    if recommendation == "KILL":
        sys.exit(1)
    elif recommendation == "REPOSITION":
        sys.exit(2)
    elif recommendation == "PIVOT":
        sys.exit(3)
    else:
        # PROCEED or PROCEED_WITH_CAUTION
        sys.exit(0)


if __name__ == "__main__":
    main()
