#!/usr/bin/env python3
"""
novelty_assess.py — Produce structured machine-readable novelty assessment output.

Reads the novelty gate reports and produces a normalized JSON assessment
that downstream pipeline steps (positioning, story, manuscript, verifier) can consume.

Usage:
    python scripts/novelty_assess.py \
        --gate N1 \
        --claim-overlap $PROJECT_DIR/claim-overlap-report.md \
        --adversarial $PROJECT_DIR/adversarial-novelty-report.md \
        --concurrent $PROJECT_DIR/concurrent-work-report.md \
        --hypotheses $PROJECT_DIR/hypotheses.md \
        --output $PROJECT_DIR/novelty-assessment.json

    # For Gate N3 (post-results), also provide:
        --analysis-report $PROJECT_DIR/analysis-report.md \
        --hypothesis-outcomes $PROJECT_DIR/hypothesis-outcomes.md

Output schema:
    {
      "gate": "N1|N2|N3|N4",
      "decision": "PROCEED|REPOSITION|PIVOT|KILL",
      "contribution": {
        "primary_dimension": "method|application|combination|empirical|theoretical|scale|negative",
        "canonical_statement": "...",
        "novelty_level": "CLEAR|PARTIAL|INSUFFICIENT",
        "confidence": "HIGH|MEDIUM|LOW"
      },
      "significance": {
        "problem_significance": "HIGH|MEDIUM|LOW",
        "improvement_magnitude": "LARGE|MODERATE|MARGINAL|WITHIN_NOISE",
        "generalizability": "BROAD|MODERATE|NARROW",
        "insight_value": "HIGH|MEDIUM|LOW"
      },
      "closest_prior_work": {
        "cite_key": "...",
        "title": "...",
        "differential": "..."
      },
      "threat_papers": [
        {"cite_key": "...", "overlap_level": "HIGH|MEDIUM", "differential": "..."}
      ],
      "kill_signals": [...],
      "reposition_guidance": "...",  // if REPOSITION
      "pivot_direction": "...",      // if PIVOT
      "kill_justification": "...",   // if KILL
      "evaluated_at": "ISO8601"
    }
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

def find_field(text: str, field_name: str, patterns: list[str] | None = None) -> str:
    """Extract a field value from markdown text using multiple pattern attempts."""
    default_patterns = [
        rf"\*\*{re.escape(field_name)}\*\*[:\s]+([^\n]+)",
        rf"{re.escape(field_name)}[:\s]+([^\n]+)",
        rf"`{re.escape(field_name)}`[:\s]+([^\n]+)",
    ]
    for pattern in (patterns or default_patterns):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".,")
    return ""


def extract_section(text: str, heading: str) -> str:
    pattern = rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Report parsers
# ---------------------------------------------------------------------------

def parse_hypotheses(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    text = path.read_text()
    # Try to extract canonical claim statement
    canonical = find_field(text, "Canonical claim") or find_field(text, "Primary hypothesis")
    if not canonical:
        # Fall back to first non-empty line after "## Primary" heading
        m = re.search(r"##\s+Primary\s+Hypothesis[^\n]*\n+([^\n#]+)", text, re.IGNORECASE)
        canonical = m.group(1).strip() if m else ""
    return {"canonical_statement": canonical}


def parse_claim_overlap_structured(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    text = path.read_text()

    threat_level = find_field(text, "Overall threat level") or "LOW"
    high_papers: list[dict] = []

    # Extract high-threat paper blocks
    # Pattern: ### [Author et al., YYYY] — [Title]
    paper_blocks = re.split(r"\n###\s+", text)
    for block in paper_blocks[1:]:  # Skip header
        lines = block.strip().split("\n")
        header = lines[0].strip()
        overlap_match = re.search(r"Overlap level.*?:\s*(HIGH|MEDIUM|LOW)", block, re.IGNORECASE)
        diff_match = re.search(r"What we do differently[:\*\s]+(.*?)(?=\n-|\n##|\Z)", block, re.DOTALL | re.IGNORECASE)
        if overlap_match:
            high_papers.append({
                "header": header,
                "overlap_level": overlap_match.group(1).upper(),
                "differential": diff_match.group(1).strip()[:200] if diff_match else "",
            })

    return {
        "overall_threat_level": threat_level.upper(),
        "threat_papers": high_papers,
    }


def parse_adversarial_structured(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    text = path.read_text()

    verdict_section = extract_section(text, "Verdict for Gate N1") or text
    novelty_status = find_field(verdict_section, "Novelty status") or "PARTIAL"
    recommendation = find_field(verdict_section, "Recommendation") or "PROCEED"
    rebuttal_str = find_field(text, "Rebuttal strength") or "STRONG"
    confidence = find_field(verdict_section, "Confidence") or "MEDIUM"

    # Extract adversarial argument (closest prior)
    adv_arg_section = extract_section(text, "Adversarial Case")
    adv_arg_match = re.search(r"Adversarial argument[:\*\s]*\n?>(.*?)(?=\n\*\*Rebuttal|\Z)", adv_arg_section, re.DOTALL | re.IGNORECASE)
    adv_arg = adv_arg_match.group(1).strip()[:300] if adv_arg_match else ""

    return {
        "novelty_status": novelty_status.upper(),
        "recommendation": recommendation.upper(),
        "rebuttal_strength": rebuttal_str.upper().replace(" ", "_"),
        "confidence": confidence.upper(),
        "adversarial_argument": adv_arg,
    }


def parse_concurrent_structured(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    text = path.read_text()
    blocks_count = len(re.findall(r"blocks_project", text, re.IGNORECASE))
    return {
        "scoop_detected": blocks_count > 0,
        "blocks_project_count": blocks_count,
    }


# ---------------------------------------------------------------------------
# Significance inference (heuristic — LLM gate provides the real assessment)
# ---------------------------------------------------------------------------

def infer_significance(adversarial: dict, claim_overlap: dict) -> dict:
    """
    Infer significance ratings from available signals.
    These are defaults — the LLM gate refines them.
    """
    threat = claim_overlap.get("overall_threat_level", "LOW")
    rebuttal = adversarial.get("rebuttal_strength", "STRONG")

    problem_sig = "MEDIUM"
    improvement_mag = "MODERATE"
    if rebuttal == "WEAK":
        improvement_mag = "MARGINAL"
    elif rebuttal == "STRONG" and threat == "LOW":
        improvement_mag = "LARGE"

    return {
        "problem_significance": problem_sig,
        "improvement_magnitude": improvement_mag,
        "generalizability": "MODERATE",
        "insight_value": "MEDIUM",
        "note": "Heuristic estimate — override with LLM gate assessment",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Produce structured novelty assessment JSON")
    parser.add_argument("--gate", required=True, choices=["N1", "N2", "N3", "N4"])
    parser.add_argument("--claim-overlap", help="claim-overlap-report.md path")
    parser.add_argument("--adversarial", help="adversarial-novelty-report.md path")
    parser.add_argument("--concurrent", help="concurrent-work-report.md path")
    parser.add_argument("--hypotheses", help="hypotheses.md path")
    parser.add_argument("--analysis-report", help="analysis-report.md path (Gate N3/N4)")
    parser.add_argument("--hypothesis-outcomes", help="hypothesis-outcomes.md path (Gate N3/N4)")
    parser.add_argument("--existing-assessment", help="Previous novelty-assessment.json to update (Gate N3)")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    hyp = parse_hypotheses(Path(args.hypotheses) if args.hypotheses else None)
    claim_overlap = parse_claim_overlap_structured(Path(args.claim_overlap) if args.claim_overlap else None)
    adversarial = parse_adversarial_structured(Path(args.adversarial) if args.adversarial else None)
    concurrent = parse_concurrent_structured(Path(args.concurrent) if args.concurrent else None)

    # Determine primary novelty level
    adv_novelty = adversarial.get("novelty_status", "PARTIAL")
    threat = claim_overlap.get("overall_threat_level", "LOW")

    if threat == "CRITICAL" or adv_novelty == "INSUFFICIENT":
        novelty_level = "INSUFFICIENT"
    elif threat in ("HIGH",) or adv_novelty == "PARTIAL":
        novelty_level = "PARTIAL"
    else:
        novelty_level = "CLEAR"

    # Map to decision
    recommendation = adversarial.get("recommendation", "PROCEED")
    if concurrent.get("scoop_detected") and recommendation != "KILL":
        recommendation = "REPOSITION"  # concurrent scoop → reposition first

    significance = infer_significance(adversarial, claim_overlap)

    # Build threat paper list
    threat_papers = claim_overlap.get("threat_papers", [])

    assessment = {
        "gate": args.gate,
        "decision": recommendation,
        "contribution": {
            "primary_dimension": "empirical",  # default; LLM gate sets the real value
            "canonical_statement": hyp.get("canonical_statement", ""),
            "novelty_level": novelty_level,
            "confidence": adversarial.get("confidence", "MEDIUM"),
        },
        "significance": significance,
        "closest_prior_work": {
            "cite_key": "",
            "title": "",
            "differential": adversarial.get("adversarial_argument", ""),
        },
        "threat_papers": [
            {
                "cite_key": "",
                "header": p.get("header", ""),
                "overlap_level": p.get("overlap_level", ""),
                "differential": p.get("differential", ""),
            }
            for p in threat_papers
            if p.get("overlap_level") in ("HIGH", "MEDIUM")
        ],
        "kill_signals": [],
        "reposition_guidance": "",
        "pivot_direction": "",
        "kill_justification": "",
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
    }

    # Carry over previous assessment fields for N3 update
    if args.existing_assessment:
        ep = Path(args.existing_assessment)
        if ep.exists():
            prev = json.loads(ep.read_text())
            assessment["previous_gate"] = prev.get("gate")
            assessment["previous_decision"] = prev.get("decision")
            assessment["contribution_shifted"] = (
                prev.get("contribution", {}).get("canonical_statement")
                != assessment["contribution"]["canonical_statement"]
            )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(assessment, indent=2))

    print(f"Novelty assessment ({args.gate}): {recommendation} [{novelty_level}]")
    print(f"Output written to {output_path}")

    sys.exit(1 if recommendation == "KILL" else 0)


if __name__ == "__main__":
    main()
