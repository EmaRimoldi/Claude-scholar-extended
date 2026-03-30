#!/usr/bin/env python3
"""
build_claim_graph.py — Construct the Claim Dependency Graph and Confidence Tracker.

Parses the LLM-generated claim-ledger.md (produced by /map-claims) together with
analysis-report.md, citation_ledger.json, and evidence_registry.json to produce:

  - .epistemic/claim_graph.json      — directed graph: claims → evidence
  - .epistemic/confidence_tracker.json — per-claim confidence levels for hedging

Called at Step 26 (/map-claims).

Usage:
    python scripts/build_claim_graph.py \\
        --claim-ledger  $PROJECT_DIR/docs/claim-ledger.md \\
        --analysis      $PROJECT_DIR/docs/analysis-report.md \\
        --citation-ledger $PROJECT_DIR/.epistemic/citation_ledger.json \\
        --evidence-registry $PROJECT_DIR/.epistemic/evidence_registry.json \\
        --output-dir    $PROJECT_DIR/.epistemic/

    # Incremental update (add new claims without overwriting existing graph):
    python scripts/build_claim_graph.py \\
        --claim-ledger  $PROJECT_DIR/docs/claim-ledger.md \\
        --output-dir    $PROJECT_DIR/.epistemic/ \\
        --update

Exit codes:
    0 — Graph built successfully; no orphan claims
    1 — One or more orphan claims found (claims with zero evidence) — hard block
    2 — Input file error or parse failure
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLDS = {
    "STRONG": 0.85,
    "MODERATE": 0.60,
    "WEAK": 0.35,
}

MULTI_EVIDENCE_BONUS = 0.08   # per additional evidence entry beyond the first
CONFIDENCE_CAP = 0.97


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_claim_ledger(path: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Parse claim-ledger.md produced by /map-claims.

    Expected format (the LLM is instructed to produce this by map-claims.md):

    ## Claims

    | Claim ID | Claim text | Evidence IDs | Evidence type | Edge strength | Section |
    |----------|-----------|--------------|--------------|---------------|---------|
    | C1 | Our method achieves X | E1, E2 | experimental | STRONG | results |

    ## Evidence

    | Evidence ID | Description | Source | Statistical test | Type |
    |-------------|-------------|--------|-----------------|------|
    | E1 | 94.3% accuracy on benchmark X (±0.4%, n=5 seeds) | analysis-report.md#table-3 | paired t-test p<0.001 | experimental_result |

    ## Citations

    | Claim ID | Cite key | Relationship |
    |----------|----------|-------------|
    | C1 | smith2025 | supports_method |

    Returns (claims, evidence, citation_links).
    """
    if not path.exists():
        print(f"ERROR: claim-ledger not found: {path}", file=sys.stderr)
        sys.exit(2)

    text = path.read_text()
    claims = _parse_md_table_section(text, "Claims")
    evidence = _parse_md_table_section(text, "Evidence")
    citations = _parse_md_table_section(text, "Citations")

    # Normalise header names (strip spaces, lowercase)
    claims = [{k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items()} for row in claims]
    evidence = [{k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items()} for row in evidence]
    citations = [{k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items()} for row in citations]

    return claims, evidence, citations


def _parse_md_table_section(text: str, section_name: str) -> list[dict]:
    """Extract rows from a markdown table under a given ## heading."""
    # Find section
    pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not m:
        return []

    section_text = m.group(1).strip()
    lines = [l.strip() for l in section_text.splitlines() if l.strip()]

    # Find table header row (contains |)
    table_lines = [l for l in lines if l.startswith("|")]
    if len(table_lines) < 3:  # header + separator + at least one row
        return []

    # Parse header
    header_line = table_lines[0]
    headers = [h.strip() for h in header_line.strip("|").split("|")]

    rows = []
    for line in table_lines[2:]:  # skip header and separator
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
        elif cells:
            # Pad or truncate to match header count
            padded = cells[:len(headers)] + [""] * max(0, len(headers) - len(cells))
            rows.append(dict(zip(headers, padded)))

    return rows


def parse_analysis_report(path: Path) -> list[dict]:
    """
    Extract empirical findings from analysis-report.md.

    Looks for patterns like:
    - Tables with numeric results
    - Lines starting with "Finding:", "Result:", or numbered result summaries
    - Markdown bold result statements

    Returns a list of evidence dict stubs to merge with the ledger.
    """
    if not path.exists():
        return []

    text = path.read_text()
    findings = []
    ev_idx = 1

    # Pattern 1: lines matching "Finding N:" or "Result N:"
    for m in re.finditer(
        r"(?:^|\n)\s*(?:\*\*)?(?:Finding|Result|Observation)\s*(\d+)[:\.\)]?\s*(?:\*\*)?(.+)",
        text, re.IGNORECASE
    ):
        findings.append({
            "id": f"EV-AR-{ev_idx:03d}",
            "type": "experimental_result",
            "source": f"analysis-report.md#finding-{m.group(1)}",
            "description": m.group(2).strip()[:200],
            "strength": "moderate",
            "claims_dependent": [],
            "last_updated": "build_claim_graph",
            "notes": "auto-extracted from analysis-report.md",
        })
        ev_idx += 1

    # Pattern 2: bold key result statements (**X achieves Y%**)
    for m in re.finditer(r"\*\*([^*]{10,120}(?:\d+\.?\d*\s*%|p\s*[<=>]\s*0\.\d+)[^*]*)\*\*", text):
        findings.append({
            "id": f"EV-AR-{ev_idx:03d}",
            "type": "experimental_result",
            "source": "analysis-report.md",
            "description": m.group(1).strip()[:200],
            "strength": "moderate",
            "claims_dependent": [],
            "last_updated": "build_claim_graph",
            "notes": "auto-extracted bold result from analysis-report.md",
        })
        ev_idx += 1

    return findings


def load_json_safe(path: Path) -> dict | list:
    """Load JSON file; return empty dict/list on missing or parse error."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"WARNING: could not parse {path}: {e}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def compute_confidence(evidence_ids: list[str], edge_strength: str, evidence_map: dict) -> float:
    """
    Compute a claim's confidence score from its evidence entries.

    Base confidence comes from the strongest edge. Additional evidence entries
    add a small bonus (diminishing returns).
    """
    base = CONFIDENCE_THRESHOLDS.get(edge_strength.upper(), 0.60)

    # Check evidence registry for any strength upgrades
    for ev_id in evidence_ids:
        ev = evidence_map.get(ev_id, {})
        ev_strength = ev.get("strength", "").upper()
        if ev_strength == "STRONG":
            base = max(base, CONFIDENCE_THRESHOLDS["STRONG"])
        elif ev_strength == "MODERATE":
            base = max(base, CONFIDENCE_THRESHOLDS["MODERATE"])

    # Bonus for multiple independent evidence entries
    bonus = MULTI_EVIDENCE_BONUS * max(0, len(evidence_ids) - 1)
    return min(CONFIDENCE_CAP, round(base + bonus, 3))


def build_graph(
    raw_claims: list[dict],
    raw_evidence: list[dict],
    raw_citations: list[dict],
    analysis_evidence: list[dict],
    citation_ledger: dict,
    evidence_registry: dict,
) -> tuple[dict, dict]:
    """
    Construct claim_graph.json and confidence_tracker.json data structures.

    Returns (graph, tracker).
    """
    # Build evidence map from ledger (for cross-referencing)
    # evidence_registry may be a list or dict; normalise to dict keyed by id
    ev_registry_map: dict = {}
    if isinstance(evidence_registry, list):
        ev_registry_map = {e["id"]: e for e in evidence_registry if "id" in e}
    elif isinstance(evidence_registry, dict):
        ev_registry_map = evidence_registry

    # Merge analysis_evidence into registry map (without overwriting existing entries)
    for ev in analysis_evidence:
        if ev["id"] not in ev_registry_map:
            ev_registry_map[ev["id"]] = ev

    # Build evidence nodes list for graph
    evidence_nodes: list[dict] = []
    evidence_id_set: set[str] = set()

    for row in raw_evidence:
        ev_id = row.get("evidence_id", row.get("id", "")).strip()
        if not ev_id:
            continue
        node = {
            "id": ev_id,
            "type": row.get("type", "experimental_result"),
            "source": row.get("source", "claim-ledger.md"),
            "description": row.get("description", ""),
            "statistical_test": row.get("statistical_test", row.get("statistical test", "")),
        }
        evidence_nodes.append(node)
        evidence_id_set.add(ev_id)

    # Also include analysis-extracted evidence that isn't already in the ledger
    for ev in analysis_evidence:
        if ev["id"] not in evidence_id_set:
            evidence_nodes.append({
                "id": ev["id"],
                "type": ev["type"],
                "source": ev["source"],
                "description": ev["description"],
                "statistical_test": "",
            })
            evidence_id_set.add(ev["id"])

    # Build citation lookup (cite_key → claim IDs it's linked to via raw_citations)
    cite_to_claims: dict[str, list[str]] = {}
    for row in raw_citations:
        c_id = row.get("claim_id", "").strip()
        cite_key = row.get("cite_key", "").strip()
        if c_id and cite_key:
            cite_to_claims.setdefault(cite_key, []).append(c_id)

    # Build claim nodes and edge list
    claim_nodes: list[dict] = []
    edges: list[dict] = []
    orphan_claims: list[str] = []
    tracker: dict = {}

    for row in raw_claims:
        c_id = row.get("claim_id", row.get("id", "")).strip()
        if not c_id:
            continue

        claim_text = row.get("claim_text", row.get("text", "")).strip()
        edge_strength_raw = row.get("edge_strength", row.get("strength", "MODERATE")).strip()
        ev_ids_raw = row.get("evidence_ids", row.get("evidence_id", "")).strip()
        section = row.get("section", "").strip().lower()

        # Parse comma-separated evidence IDs
        ev_ids = [e.strip() for e in ev_ids_raw.split(",") if e.strip()]

        # Find citations linked to this claim
        citations_for_claim = [
            k for k, claims in cite_to_claims.items() if c_id in claims
        ]
        # Also check citation_ledger for claims_supported links
        if isinstance(citation_ledger, dict):
            for cite_key, entry in citation_ledger.items():
                supported = entry.get("claims_supported", [])
                if c_id in supported and cite_key not in citations_for_claim:
                    citations_for_claim.append(cite_key)
        elif isinstance(citation_ledger, list):
            for entry in citation_ledger:
                cite_key = entry.get("cite_key", "")
                supported = entry.get("claims_supported", [])
                if c_id in supported and cite_key not in citations_for_claim:
                    citations_for_claim.append(cite_key)

        confidence = compute_confidence(ev_ids, edge_strength_raw, ev_registry_map)

        # Determine claim status
        if not ev_ids and not citations_for_claim:
            status = "unsupported"
            orphan_claims.append(c_id)
        else:
            status = "verified"

        # Map section to canonical form
        canonical_section = "results"
        for sec in ("abstract", "introduction", "methods", "results", "discussion", "conclusion"):
            if sec in section:
                canonical_section = sec
                break

        claim_node = {
            "id": c_id,
            "text": claim_text,
            "type": row.get("type", row.get("evidence_type", "empirical")).strip(),
            "strength": edge_strength_raw.upper(),
            "evidence": ev_ids,
            "citations": citations_for_claim,
            "confidence": confidence,
            "section": canonical_section,
            "status": status,
            "last_verified": "build_claim_graph",
        }
        claim_nodes.append(claim_node)

        # Create edges
        for ev_id in ev_ids:
            edges.append({
                "claim": c_id,
                "evidence": ev_id,
                "strength": edge_strength_raw.upper(),
                "type": "direct",
            })

        # Tracker entry
        strongest_link = edge_strength_raw.upper()
        tracker[c_id] = {
            "confidence": confidence,
            "evidence_count": len(ev_ids),
            "citation_count": len(citations_for_claim),
            "strongest_link": strongest_link,
            "status": status,
            "section": canonical_section,
        }

    # Flag evidence entries with no dependent claims
    all_used_ev_ids: set = {e["evidence"] for e in edges}
    unsupported_evidence = [
        ev["id"] for ev in evidence_nodes if ev["id"] not in all_used_ev_ids
    ]

    graph = {
        "schema_version": 1,
        "built_at": now_iso(),
        "built_by": "build_claim_graph.py",
        "claims": claim_nodes,
        "evidence": evidence_nodes,
        "edges": edges,
        "orphan_claims": orphan_claims,
        "unsupported_evidence": unsupported_evidence,
        "stats": {
            "claim_count": len(claim_nodes),
            "evidence_count": len(evidence_nodes),
            "edge_count": len(edges),
            "orphan_claim_count": len(orphan_claims),
            "unsupported_evidence_count": len(unsupported_evidence),
        },
    }

    return graph, tracker


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build claim dependency graph from claim-ledger.md"
    )
    parser.add_argument(
        "--claim-ledger",
        required=True,
        help="Path to claim-ledger.md (produced by /map-claims)",
    )
    parser.add_argument(
        "--analysis",
        default="",
        help="Path to analysis-report.md (optional, used to supplement evidence nodes)",
    )
    parser.add_argument(
        "--citation-ledger",
        default="",
        help="Path to .epistemic/citation_ledger.json",
    )
    parser.add_argument(
        "--evidence-registry",
        default="",
        help="Path to .epistemic/evidence_registry.json",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write claim_graph.json and confidence_tracker.json",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Merge into existing graph rather than overwriting (adds new claims/evidence only)",
    )
    args = parser.parse_args()

    claim_ledger_path = Path(args.claim_ledger)
    analysis_path = Path(args.analysis) if args.analysis else None
    citation_ledger_path = Path(args.citation_ledger) if args.citation_ledger else None
    evidence_registry_path = Path(args.evidence_registry) if args.evidence_registry else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    graph_path = output_dir / "claim_graph.json"
    tracker_path = output_dir / "confidence_tracker.json"

    # Parse inputs
    raw_claims, raw_evidence, raw_citations = parse_claim_ledger(claim_ledger_path)

    analysis_evidence: list[dict] = []
    if analysis_path:
        analysis_evidence = parse_analysis_report(analysis_path)

    citation_ledger = load_json_safe(citation_ledger_path) if citation_ledger_path else {}
    evidence_registry = load_json_safe(evidence_registry_path) if evidence_registry_path else {}

    if not raw_claims:
        print(
            "ERROR: No claims found in claim-ledger.md. "
            "Ensure /map-claims has produced a properly formatted ## Claims table.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Build graph
    graph, tracker = build_graph(
        raw_claims, raw_evidence, raw_citations,
        analysis_evidence, citation_ledger, evidence_registry,
    )

    # Merge with existing if --update
    if args.update and graph_path.exists():
        existing = load_json_safe(graph_path)
        if isinstance(existing, dict) and "claims" in existing:
            existing_claim_ids = {c["id"] for c in existing["claims"]}
            existing_ev_ids = {e["id"] for e in existing["evidence"]}

            new_claims = [c for c in graph["claims"] if c["id"] not in existing_claim_ids]
            new_evidence = [e for e in graph["evidence"] if e["id"] not in existing_ev_ids]
            new_edges = [
                e for e in graph["edges"]
                if e["claim"] not in existing_claim_ids
            ]

            existing["claims"].extend(new_claims)
            existing["evidence"].extend(new_evidence)
            existing["edges"].extend(new_edges)

            # Merge orphan/unsupported lists
            existing_orphans = set(existing.get("orphan_claims", []))
            existing_orphans.update(graph["orphan_claims"])
            existing["orphan_claims"] = sorted(existing_orphans)

            existing_unsupported = set(existing.get("unsupported_evidence", []))
            existing_unsupported.update(graph["unsupported_evidence"])
            existing["unsupported_evidence"] = sorted(existing_unsupported)

            existing["stats"] = {
                "claim_count": len(existing["claims"]),
                "evidence_count": len(existing["evidence"]),
                "edge_count": len(existing["edges"]),
                "orphan_claim_count": len(existing["orphan_claims"]),
                "unsupported_evidence_count": len(existing["unsupported_evidence"]),
            }
            existing["updated_at"] = now_iso()
            graph = existing

            # Merge tracker (new claims only)
            existing_tracker = load_json_safe(tracker_path)
            if isinstance(existing_tracker, dict):
                for k, v in tracker.items():
                    if k not in existing_tracker:
                        existing_tracker[k] = v
                tracker = existing_tracker

    # Write outputs
    graph_path.write_text(json.dumps(graph, indent=2))
    tracker_path.write_text(json.dumps(tracker, indent=2))

    # Report
    stats = graph["stats"]
    print(f"Claim graph written to: {graph_path}")
    print(f"Confidence tracker written to: {tracker_path}")
    print(f"Claims: {stats['claim_count']}  Evidence: {stats['evidence_count']}  "
          f"Edges: {stats['edge_count']}")

    orphans = graph["orphan_claims"]
    unsupported_ev = graph["unsupported_evidence"]

    if orphans:
        print(f"\n[HARD BLOCK] {len(orphans)} orphan claim(s) — zero evidence edges:", file=sys.stderr)
        for c_id in orphans:
            print(f"  - {c_id}", file=sys.stderr)
        print(
            "\nAn orphan claim means the paper will assert something it cannot support. "
            "Fix: either add evidence entries in claim-ledger.md or remove the claim.",
            file=sys.stderr,
        )
        sys.exit(1)

    if unsupported_ev:
        print(f"\n[WARNING] {len(unsupported_ev)} evidence entry(s) with no dependent claim — "
              f"may be unused results:")
        for ev_id in unsupported_ev:
            print(f"  - {ev_id}")

    print("\nGraph build successful. No orphan claims.")
    sys.exit(0)


if __name__ == "__main__":
    main()
