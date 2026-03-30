#!/usr/bin/env python3
"""
narrative_gap_detector.py — Step 29: Writing→Analysis Feedback Gate.

Before generating prose, checks whether the paper blueprint requires evidence
that does not exist in the epistemic layer. Triggers the writing-to-analysis
feedback loop when critical evidence is missing.

Usage:
    python scripts/narrative_gap_detector.py \
        --blueprint       $PROJECT_DIR/paper-blueprint.md \
        --figure-plan     $PROJECT_DIR/figure-plan.md \
        --claim-graph     $PROJECT_DIR/.epistemic/claim_graph.json \
        --evidence-registry $PROJECT_DIR/.epistemic/evidence_registry.json \
        --figures-dir     $PROJECT_DIR/figures/ \
        --output          $PROJECT_DIR/narrative-gap-report.md

Exit codes:
    0 — No Critical evidence-missing gaps
    1 — One or more Critical evidence-missing gaps found → triggers Loop 2
    2 — Input error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> object:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def token_overlap(a: str, b: str) -> float:
    ta = set(normalize(a).split())
    tb = set(normalize(b).split())
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Blueprint parsing
# ---------------------------------------------------------------------------

def parse_blueprint(text: str) -> list[dict]:
    """
    Parse paper-blueprint.md into sections.
    Each section dict: {title, claims, evidence_refs, figure_refs, word_budget}.

    Expected format (from /story output):
    ## Section: Introduction
    **Core claim:** ...
    **Evidence:** ...
    **Figures:** Figure 1, Figure 2
    **Word budget:** 500
    """
    sections: list[dict] = []
    current: dict | None = None

    section_pat = re.compile(r"^#{1,3}\s+(?:Section[:\s]+)?(.+)", re.IGNORECASE)
    claim_pat = re.compile(r"\*\*(?:Core\s+)?[Cc]laim[s]?\*\*:?\s*(.+)")
    evidence_pat = re.compile(r"\*\*[Ee]vidence\*\*:?\s*(.+)")
    figure_pat = re.compile(r"\*\*[Ff]igure[s]?\*\*:?\s*(.+)")
    budget_pat = re.compile(r"\*\*[Ww]ord\s+[Bb]udget\*\*:?\s*(\d+)")

    for line in text.splitlines():
        m_sec = section_pat.match(line.strip())
        if m_sec:
            if current:
                sections.append(current)
            current = {
                "title": m_sec.group(1).strip(),
                "claims": [],
                "evidence_refs": [],
                "figure_refs": [],
                "word_budget": 0,
            }
            continue

        if current is None:
            continue

        m = claim_pat.search(line)
        if m:
            current["claims"].append(m.group(1).strip())
            continue

        m = evidence_pat.search(line)
        if m:
            # Parse comma-separated evidence IDs or descriptions
            raw = m.group(1).strip()
            current["evidence_refs"].extend(
                [e.strip() for e in re.split(r"[,;]", raw) if e.strip()]
            )
            continue

        m = figure_pat.search(line)
        if m:
            raw = m.group(1).strip()
            current["figure_refs"].extend(
                [f.strip() for f in re.split(r"[,;]", raw) if f.strip()]
            )
            continue

        m = budget_pat.search(line)
        if m:
            current["word_budget"] = int(m.group(1))
            continue

        # Also capture inline bullet claims
        bullet = re.match(r"^[-*+]\s+(.+)", line.strip())
        if bullet and current and not current["claims"]:
            current["claims"].append(bullet.group(1).strip())

    if current:
        sections.append(current)

    # If no structured sections found, fall back to heading-based parsing
    if not sections:
        for heading in re.finditer(r"^#{2,3}\s+(.+)", text, re.MULTILINE):
            sections.append({
                "title": heading.group(1).strip(),
                "claims": [],
                "evidence_refs": [],
                "figure_refs": [],
                "word_budget": 0,
            })

    return sections


# ---------------------------------------------------------------------------
# Epistemic layer lookups
# ---------------------------------------------------------------------------

def build_claim_lookup(claim_graph: dict) -> dict[str, dict]:
    """Build {claim_id: claim_dict} and {normalized_text: claim_dict} lookups."""
    claims_by_id: dict[str, dict] = {}
    claims_by_text: dict[str, dict] = {}
    for node in claim_graph.get("nodes", []):
        if node.get("type") in ("claim", "contribution", "finding", None):
            cid = node.get("id", "")
            text = node.get("text", "")
            if cid:
                claims_by_id[cid] = node
            if text:
                claims_by_text[normalize(text)] = node
    return claims_by_id, claims_by_text


def build_evidence_lookup(evidence_registry: dict) -> set[str]:
    """Return set of evidence IDs / result IDs that exist in the registry."""
    ids: set[str] = set()
    if isinstance(evidence_registry, dict):
        # Format: {evidence_id: {...}} or {"entries": [...]}
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


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------

def detect_gaps(
    sections: list[dict],
    claims_by_id: dict[str, dict],
    claims_by_text: dict[str, dict],
    evidence_ids: set[str],
    figures_dir: Path,
    figure_plan_text: str,
) -> list[dict]:
    """
    Check each section's claims and figure references against the epistemic layer.
    Returns list of gap dicts.
    """
    gaps: list[dict] = []

    for section in sections:
        title = section["title"]

        # Skip metadata-only sections
        if re.match(r"abstract|title|acknowledgement|reference|appendix",
                    title, re.IGNORECASE):
            continue

        # --- Check claims ---
        for claim_text in section["claims"]:
            if not claim_text or len(claim_text) < 10:
                continue

            # Try to find claim in graph by ID or text match
            claim_node = None
            if claim_text in claims_by_id:
                claim_node = claims_by_id[claim_text]
            else:
                # Text-based fuzzy match
                norm = normalize(claim_text)
                for existing_norm, node in claims_by_text.items():
                    if token_overlap(norm, existing_norm) > 0.5:
                        claim_node = node
                        break

            if claim_node is None:
                # Claim not registered in the graph at all
                gaps.append({
                    "section": title,
                    "type": "Claim unsupported",
                    "severity": "Important",
                    "description": (
                        f"Section '{title}' claims: '{claim_text[:100]}' — "
                        "this claim is not registered in claim_graph.json. "
                        "Either register it in /map-claims or remove it from the blueprint."
                    ),
                    "route_to": "analysis",
                })
                continue

            # Check claim status
            status = claim_node.get("status", "")
            if status == "unsupported":
                gaps.append({
                    "section": title,
                    "type": "Claim unsupported",
                    "severity": "Critical",
                    "description": (
                        f"Section '{title}' claim '{claim_text[:100]}' is registered in "
                        "claim_graph.json with status: unsupported. No evidence linked."
                    ),
                    "route_to": "analysis",
                })
                continue

            # Check that claim has evidence in the registry
            claim_evidence_ids = claim_node.get("evidence", [])
            if not claim_evidence_ids:
                # Check edges
                claim_edges = [
                    e for e in claim_node.get("edges", [])
                    if e.get("type") == "supported_by"
                ]
                if not claim_edges:
                    gaps.append({
                        "section": title,
                        "type": "Evidence missing",
                        "severity": "Critical",
                        "description": (
                            f"Section '{title}' claim '{claim_text[:100]}' (ID: "
                            f"{claim_node.get('id', '?')}) has no evidence links in "
                            "claim_graph.json. A claim with no evidence cannot proceed "
                            "to manuscript production."
                        ),
                        "route_to": "analysis",
                    })
            else:
                # Check that referenced evidence exists in the registry
                missing_evidence = [
                    eid for eid in claim_evidence_ids
                    if eid not in evidence_ids
                ]
                if missing_evidence:
                    gaps.append({
                        "section": title,
                        "type": "Evidence missing",
                        "severity": "Critical",
                        "description": (
                            f"Section '{title}' claim '{claim_text[:100]}' references "
                            f"evidence ID(s) not in evidence_registry.json: "
                            + ", ".join(missing_evidence[:5])
                        ),
                        "route_to": "analysis",
                    })

        # --- Check figure references ---
        for fig_ref in section["figure_refs"]:
            if not fig_ref:
                continue

            # Check if this figure exists in the figures directory
            fig_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", fig_ref.lower())
            found = (
                figures_dir.exists()
                and any(
                    f.stem.lower() == fig_name.rstrip("_")
                    or token_overlap(fig_ref, f.stem) > 0.6
                    for f in figures_dir.iterdir()
                    if f.suffix in (".png", ".pdf", ".svg", ".eps", ".jpg")
                )
            )

            if not found:
                # Check figure plan to see if it's flagged for generation
                in_plan = fig_ref.lower() in figure_plan_text.lower()
                gaps.append({
                    "section": title,
                    "type": "Figure missing",
                    "severity": "Important" if in_plan else "Important",
                    "description": (
                        f"Section '{title}' references figure '{fig_ref}' "
                        f"which does not exist in figures/ directory. "
                        f"{'Flagged for generation in figure-plan.md.' if in_plan else 'Not found in figure-plan.md either.'}"
                    ),
                    "route_to": "analysis",
                })

    return gaps


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(gaps: list[dict], output_path: Path) -> None:
    critical = [g for g in gaps if g["severity"] == "Critical"]
    important = [g for g in gaps if g["severity"] == "Important"]
    minor = [g for g in gaps if g["severity"] == "Minor"]

    evidence_missing = [g for g in gaps if g["type"] == "Evidence missing"]
    figure_missing = [g for g in gaps if g["type"] == "Figure missing"]
    claim_unsupported = [g for g in gaps if g["type"] == "Claim unsupported"]

    lines = [
        "# Narrative Gap Report (Step 29)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Evidence-missing gaps:** {len(evidence_missing)}",
        f"**Figure-missing gaps:** {len(figure_missing)}",
        f"**Claim-unsupported gaps:** {len(claim_unsupported)}",
        "",
        f"## Result: {'BLOCK' if critical else ('WARN' if important else 'PASS')}",
        "",
    ]

    if not gaps:
        lines += [
            "No narrative gaps detected. All blueprint claims have evidence links "
            "and all referenced figures exist.",
        ]

    def write_gap_group(title: str, gap_list: list[dict]) -> list[str]:
        if not gap_list:
            return []
        out = [f"## {title}", ""]
        for g in gap_list:
            out += [
                f"### [{g['severity']}] {g['section']} — {g['type']}",
                "",
                f"{g['description']}",
                "",
                f"- **Route to:** `{g['route_to']}`",
                "",
            ]
        return out

    lines += write_gap_group("Critical Evidence-Missing Gaps", [g for g in critical if g["type"] == "Evidence missing"])
    lines += write_gap_group("Critical Claim-Unsupported Gaps", [g for g in critical if g["type"] == "Claim unsupported"])
    lines += write_gap_group("Important Gaps", important)
    lines += write_gap_group("Minor Gaps", minor)

    lines += [
        "---",
        "",
        "## Loop Routing",
        "",
        "If critical `Evidence missing` gaps exist:",
        "```bash",
        "python scripts/pipeline_state.py increment-counter narrative_gap_loops --max 2",
        "# Exit 0: route back to step indicated in gap's route_to field",
        "#   route_to: analysis → Step 20 (analyze-results)",
        "#   route_to: experiments → Step 9 (design-experiments)",
        "# Exit 1: document remaining gaps as Limitations, proceed",
        "```",
    ]

    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 29: Check blueprint claims against epistemic layer before prose generation"
    )
    parser.add_argument("--blueprint", required=True, help="Path to paper-blueprint.md")
    parser.add_argument("--figure-plan", default="", help="Path to figure-plan.md")
    parser.add_argument("--claim-graph", required=True, help="Path to .epistemic/claim_graph.json")
    parser.add_argument("--evidence-registry", default="", help="Path to .epistemic/evidence_registry.json")
    parser.add_argument("--figures-dir", default="", help="Path to figures/ directory")
    parser.add_argument("--output", required=True, help="Output path for narrative-gap-report.md")
    args = parser.parse_args()

    blueprint_path = Path(args.blueprint)
    if not blueprint_path.exists():
        print(f"ERROR: blueprint not found: {blueprint_path}", file=sys.stderr)
        sys.exit(2)

    blueprint_text = load_text(blueprint_path)
    figure_plan_text = load_text(Path(args.figure_plan)) if args.figure_plan else ""
    claim_graph = load_json(Path(args.claim_graph))
    evidence_registry = load_json(Path(args.evidence_registry)) if args.evidence_registry else {}
    figures_dir = Path(args.figures_dir) if args.figures_dir else Path("/nonexistent")

    sections = parse_blueprint(blueprint_text)
    claims_by_id, claims_by_text = build_claim_lookup(claim_graph)
    evidence_ids = build_evidence_lookup(evidence_registry)

    if not sections:
        print("WARNING: No sections parsed from blueprint. Check blueprint format.", file=sys.stderr)

    gaps = detect_gaps(
        sections, claims_by_id, claims_by_text,
        evidence_ids, figures_dir, figure_plan_text,
    )

    critical = [g for g in gaps if g["severity"] == "Critical"]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(gaps, output_path)

    evidence_critical = [g for g in critical if g["type"] == "Evidence missing"]
    print(
        f"Gaps — Evidence missing: {len([g for g in gaps if g['type'] == 'Evidence missing'])}  "
        f"Figure missing: {len([g for g in gaps if g['type'] == 'Figure missing'])}  "
        f"Claim unsupported: {len([g for g in gaps if g['type'] == 'Claim unsupported'])}"
    )
    print(f"Report written to: {output_path}")

    if evidence_critical:
        print(
            f"\n[LOOP TRIGGER] {len(evidence_critical)} critical evidence-missing gap(s). "
            f"Increment narrative_gap_loops counter and route back.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
