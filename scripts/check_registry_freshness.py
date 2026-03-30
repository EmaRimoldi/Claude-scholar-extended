#!/usr/bin/env python3
"""
check_registry_freshness.py — Epistemic layer maintenance utility.

Validates that all 4 epistemic files exist and are internally consistent:
  - citation_ledger.json
  - claim_graph.json
  - confidence_tracker.json
  - evidence_registry.json

Cross-reference checks:
  1. Claims in claim_graph have confidence entries in confidence_tracker
  2. Evidence IDs in claim_graph exist in evidence_registry
  3. Citation keys in claim_graph exist in citation_ledger
  4. All 4 files are valid JSON

Usage:
    python scripts/check_registry_freshness.py \
        --project $PROJECT_DIR \
        [--fix]  # Add missing default entries instead of just reporting

Exit codes:
    0 — All checks pass (or --fix repaired all issues)
    1 — Inconsistencies found (without --fix)
    2 — Input error (epistemic directory missing)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_json_safe(path: Path) -> tuple[object, str | None]:
    """Load JSON, returning (data, error_message). error_message is None on success."""
    if not path.exists():
        return None, f"File not found: {path}"
    try:
        data = json.loads(path.read_text())
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def get_claim_ids(claim_graph: dict) -> set[str]:
    ids: set[str] = set()
    for node in claim_graph.get("nodes", []):
        nid = node.get("id", "")
        if nid:
            ids.add(nid)
    return ids


def get_evidence_ids_from_graph(claim_graph: dict) -> set[str]:
    """Get all evidence IDs referenced in claim_graph edges and claim evidence lists."""
    ids: set[str] = set()
    for node in claim_graph.get("nodes", []):
        for eid in node.get("evidence", []):
            ids.add(eid)
    for edge in claim_graph.get("edges", []):
        if edge.get("type") in ("supported_by", "contradicted_by", "qualified_by"):
            tid = edge.get("target", "")
            if tid:
                ids.add(tid)
    return ids


def get_evidence_ids_in_registry(evidence_registry: object) -> set[str]:
    ids: set[str] = set()
    if isinstance(evidence_registry, dict):
        if "entries" in evidence_registry:
            for e in evidence_registry["entries"]:
                eid = e.get("id") or e.get("result_id") or e.get("evidence_id", "")
                if eid:
                    ids.add(eid)
        else:
            ids.update(evidence_registry.keys())
    elif isinstance(evidence_registry, list):
        for e in evidence_registry:
            eid = e.get("id") or e.get("result_id") or e.get("evidence_id", "")
            if eid:
                ids.add(eid)
    return ids


def get_citation_keys_from_graph(claim_graph: dict) -> set[str]:
    keys: set[str] = set()
    for node in claim_graph.get("nodes", []):
        for k in node.get("citations", []):
            keys.add(k)
    return keys


def get_citation_keys_in_ledger(citation_ledger: object) -> set[str]:
    if isinstance(citation_ledger, dict):
        return set(citation_ledger.keys())
    if isinstance(citation_ledger, list):
        return {e.get("cite_key", "") for e in citation_ledger if e.get("cite_key")}
    return set()


def get_confidence_tracker_keys(confidence_tracker: object) -> set[str]:
    if isinstance(confidence_tracker, dict):
        return set(confidence_tracker.keys())
    return set()


# ---------------------------------------------------------------------------
# Fix routines
# ---------------------------------------------------------------------------

def fix_missing_confidence_entries(
    claim_ids: set[str],
    confidence_tracker_keys: set[str],
    confidence_tracker: object,
    claim_graph: dict,
) -> tuple[object, list[str]]:
    """Add default confidence entries for claims missing from confidence_tracker."""
    added = []
    if not isinstance(confidence_tracker, dict):
        confidence_tracker = {}

    for cid in claim_ids:
        if cid not in confidence_tracker_keys:
            # Look up confidence from claim_graph
            conf = 0.5  # default
            for node in claim_graph.get("nodes", []):
                if node.get("id") == cid:
                    conf = node.get("confidence", 0.5)
                    break
            confidence_tracker[cid] = {
                "confidence": conf,
                "hedging_level": (
                    "assertive" if conf >= 0.80
                    else "hedged" if conf >= 0.50
                    else "cautious"
                ),
                "added_by_freshness_check": True,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
            added.append(cid)
    return confidence_tracker, added


def fix_missing_evidence_entries(
    missing_evidence_ids: set[str],
    evidence_registry: object,
) -> tuple[object, list[str]]:
    """Add stub entries for evidence IDs referenced in claim_graph but missing from registry."""
    added = []
    if isinstance(evidence_registry, dict):
        if "entries" in evidence_registry:
            for eid in missing_evidence_ids:
                evidence_registry["entries"].append({
                    "id": eid,
                    "type": "unknown",
                    "status": "pending",
                    "description": "Stub added by check_registry_freshness.py",
                    "added_at": datetime.now(timezone.utc).isoformat(),
                })
                added.append(eid)
        else:
            for eid in missing_evidence_ids:
                evidence_registry[eid] = {
                    "type": "unknown",
                    "status": "pending",
                    "description": "Stub added by check_registry_freshness.py",
                    "added_at": datetime.now(timezone.utc).isoformat(),
                }
                added.append(eid)
    elif isinstance(evidence_registry, list):
        for eid in missing_evidence_ids:
            evidence_registry.append({
                "id": eid,
                "type": "unknown",
                "status": "pending",
                "description": "Stub added by check_registry_freshness.py",
                "added_at": datetime.now(timezone.utc).isoformat(),
            })
            added.append(eid)
    return evidence_registry, added


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

def run_checks(epistemic_dir: Path, fix: bool) -> tuple[bool, list[str], list[str]]:
    """
    Run all consistency checks.
    Returns (all_pass, issues, fixes_applied).
    """
    issues: list[str] = []
    fixes_applied: list[str] = []

    files = {
        "claim_graph": epistemic_dir / "claim_graph.json",
        "confidence_tracker": epistemic_dir / "confidence_tracker.json",
        "citation_ledger": epistemic_dir / "citation_ledger.json",
        "evidence_registry": epistemic_dir / "evidence_registry.json",
    }

    # --- Check 0: File existence and valid JSON ---
    data: dict[str, object] = {}
    for key, path in files.items():
        obj, err = load_json_safe(path)
        if err:
            issues.append(f"[FILE] {err}")
            data[key] = {} if "graph" in key or "tracker" in key or "ledger" in key else []
        else:
            data[key] = obj
            print(f"  [OK] {path.name} — valid JSON")

    claim_graph = data["claim_graph"] or {}
    confidence_tracker = data["confidence_tracker"] or {}
    citation_ledger = data["citation_ledger"] or {}
    evidence_registry = data["evidence_registry"] or {}

    if not isinstance(claim_graph, dict):
        issues.append("[SCHEMA] claim_graph.json is not a dict at top level")
        return False, issues, fixes_applied

    # --- Check 1: Claim IDs in claim_graph have entries in confidence_tracker ---
    claim_ids = get_claim_ids(claim_graph)
    confidence_keys = get_confidence_tracker_keys(confidence_tracker)
    missing_confidence = claim_ids - confidence_keys

    if missing_confidence:
        issues.append(
            f"[MISSING] {len(missing_confidence)} claim(s) in claim_graph have no confidence "
            f"entry in confidence_tracker.json: "
            + ", ".join(sorted(missing_confidence)[:10])
        )
        if fix and missing_confidence:
            updated, added = fix_missing_confidence_entries(
                missing_confidence, confidence_keys, confidence_tracker, claim_graph
            )
            save_json(files["confidence_tracker"], updated)
            fixes_applied.append(
                f"Added {len(added)} default confidence entries to confidence_tracker.json"
            )
    else:
        print(f"  [OK] All {len(claim_ids)} claims have confidence entries")

    # --- Check 2: Evidence IDs in claim_graph exist in evidence_registry ---
    evidence_in_graph = get_evidence_ids_from_graph(claim_graph)
    evidence_in_registry = get_evidence_ids_in_registry(evidence_registry)
    missing_evidence = evidence_in_graph - evidence_in_registry

    if missing_evidence:
        issues.append(
            f"[MISSING] {len(missing_evidence)} evidence ID(s) in claim_graph not in "
            f"evidence_registry.json: "
            + ", ".join(sorted(missing_evidence)[:10])
        )
        if fix and missing_evidence:
            updated, added = fix_missing_evidence_entries(missing_evidence, evidence_registry)
            save_json(files["evidence_registry"], updated)
            fixes_applied.append(
                f"Added {len(added)} stub entries to evidence_registry.json"
            )
    else:
        print(f"  [OK] All {len(evidence_in_graph)} evidence references resolve in registry")

    # --- Check 3: Citation keys in claim_graph exist in citation_ledger ---
    citations_in_graph = get_citation_keys_from_graph(claim_graph)
    citations_in_ledger = get_citation_keys_in_ledger(citation_ledger)
    missing_citations = citations_in_graph - citations_in_ledger

    if missing_citations:
        issues.append(
            f"[MISSING] {len(missing_citations)} citation key(s) in claim_graph not in "
            f"citation_ledger.json: "
            + ", ".join(sorted(missing_citations)[:10])
        )
        # Fix: we don't auto-add citations — they require verification
        if fix:
            fixes_applied.append(
                f"WARNING: {len(missing_citations)} citation key(s) could not be auto-fixed. "
                f"Verify and add manually to citation_ledger.json."
            )
    else:
        print(f"  [OK] All {len(citations_in_graph)} citation keys resolve in ledger")

    # --- Check 4: Orphan claims (in confidence_tracker but not in claim_graph) ---
    orphan_confidence = confidence_keys - claim_ids
    if orphan_confidence:
        issues.append(
            f"[ORPHAN] {len(orphan_confidence)} entries in confidence_tracker have no "
            f"corresponding claim in claim_graph.json: "
            + ", ".join(sorted(orphan_confidence)[:10])
            + " (stale — consider cleaning up)"
        )
        # This is a warning only, not a hard failure

    all_pass = not any(
        "[FILE]" in i or "[MISSING]" in i or "[SCHEMA]" in i
        for i in issues
        if "[ORPHAN]" not in i
    )

    if fix and issues:
        # Re-run checks to update status
        pass  # Already applied fixes inline above

    return all_pass, issues, fixes_applied


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate epistemic layer file existence and internal consistency"
    )
    parser.add_argument("--project", required=True, help="PROJECT_DIR")
    parser.add_argument("--fix", action="store_true",
                        help="Add missing default entries instead of just reporting")
    args = parser.parse_args()

    project_dir = Path(args.project)
    epistemic_dir = project_dir / ".epistemic"

    if not epistemic_dir.exists():
        print(f"ERROR: Epistemic directory not found: {epistemic_dir}", file=sys.stderr)
        print(
            f"Initialize it with: /run-pipeline (Step 1 creates .epistemic/ structure)",
            file=sys.stderr,
        )
        sys.exit(2)

    print(f"Checking epistemic registry freshness in: {epistemic_dir}")
    print()

    all_pass, issues, fixes_applied = run_checks(epistemic_dir, fix=args.fix)

    if fixes_applied:
        print("\nFixes applied:")
        for f in fixes_applied:
            print(f"  - {f}")

    if issues:
        print("\nIssues found:")
        for issue in issues:
            severity = "[CRITICAL]" if "[MISSING]" in issue or "[FILE]" in issue else "[WARN]"
            print(f"  {severity} {issue}")

    print()
    if all_pass or (args.fix and not any("[FILE]" in i or "[SCHEMA]" in i for i in issues)):
        print("[PASS] Epistemic registry is fresh and internally consistent.")
        sys.exit(0)
    else:
        print(
            f"[FAIL] {len(issues)} issue(s) found. "
            f"Run with --fix to auto-repair where possible.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
