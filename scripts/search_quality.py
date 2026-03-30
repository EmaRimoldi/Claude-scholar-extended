#!/usr/bin/env python3
"""
search_quality.py — Measure and report search quality metrics for the multi-pass research system.

Computes:
  - Recall estimate: fraction of relevant papers found by primary search vs. audit
  - Precision: fraction of flagged papers that are actually relevant
  - Coverage: are all major research threads represented?
  - Threat detection rate: among genuine novelty threats, fraction found

Usage:
    # Compute coverage and precision from the research landscape
    python scripts/search_quality.py coverage \
        --landscape $PROJECT_DIR/research-landscape.md \
        --ledger $PROJECT_DIR/.epistemic/citation_ledger.json \
        --output $PROJECT_DIR/search-quality-report.md

    # Estimate recall by cross-checking audit against primary search
    python scripts/search_quality.py recall \
        --primary-results $PROJECT_DIR/.epistemic/citation_ledger.json \
        --audit-results audit_search.json \
        --output $PROJECT_DIR/search-quality-report.md

    # Full quality report
    python scripts/search_quality.py full \
        --project $PROJECT_DIR \
        --output $PROJECT_DIR/search-quality-report.md
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json_safe(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"WARNING: Could not parse {path}: {e}", file=sys.stderr)
        return {}


def extract_clusters(landscape_text: str) -> list[str]:
    """Extract cluster names from research-landscape.md."""
    clusters = re.findall(r"###\s+Cluster\s+\d+[:\s]+([^\n]+)", landscape_text, re.IGNORECASE)
    if not clusters:
        # Fallback: any ### heading
        clusters = re.findall(r"###\s+([^\n]+)", landscape_text)
    return [c.strip() for c in clusters]


def count_papers_per_cluster(ledger: dict, landscape_text: str) -> dict[str, int]:
    """
    Heuristic: check how many ledger papers mention each cluster keyword.
    Underestimate — papers may be relevant to clusters without mentioning the cluster name.
    """
    clusters = extract_clusters(landscape_text)
    counts: dict[str, int] = {c: 0 for c in clusters}

    for entry in ledger.values():
        title = (entry.get("title") or "").lower()
        for cluster in clusters:
            keywords = cluster.lower().split()[:3]  # first 3 words
            if any(kw in title for kw in keywords):
                counts[cluster] += 1
                break  # count paper once per cluster

    return counts


def estimate_precision(ledger: dict) -> tuple[float, int, int]:
    """
    Precision: fraction of ledger entries with relevance_tier <= 2 (Tier 1 or 2).
    Tier 3 entries are "found but deemed not relevant" = false positives.
    """
    total = len(ledger)
    if total == 0:
        return 0.0, 0, 0
    relevant = sum(1 for e in ledger.values() if e.get("relevance_tier", 3) <= 2)
    return relevant / total, relevant, total


def estimate_threat_detection(ledger: dict, claim_overlap_text: str) -> tuple[float, int, int]:
    """
    Threat detection rate: of papers with claim_overlap_level HIGH or MEDIUM in the ledger,
    compare against distinct HIGH/MEDIUM papers mentioned in claim-overlap-report.
    This is an internal consistency check, not true recall.
    """
    # Count threats in ledger
    ledger_threats = sum(
        1 for e in ledger.values()
        if e.get("claim_overlap_level") in ("HIGH", "MEDIUM")
    )
    # Count threats mentioned in claim overlap report
    report_threats = len(re.findall(r"\*\*Overlap level:\*\*\s*(HIGH|MEDIUM)", claim_overlap_text, re.IGNORECASE))
    if report_threats == 0:
        return 1.0, 0, 0
    rate = min(ledger_threats / report_threats, 1.0)
    return rate, ledger_threats, report_threats


def compute_recall_vs_audit(primary: dict, audit: list[dict], threshold: float = 0.85) -> tuple[float, int, int]:
    """
    Recall estimate: how many papers from the audit search are already in the primary ledger?
    Uses title-overlap to match (same logic as dedup_papers.py).
    """
    from scripts.dedup_papers import normalize_title, token_overlap_ratio  # type: ignore

    primary_titles = [normalize_title(e.get("title", "")) for e in primary.values()]
    found_in_primary = 0
    for paper in audit:
        audit_title = normalize_title(paper.get("title", ""))
        if any(token_overlap_ratio(audit_title, pt) >= threshold for pt in primary_titles):
            found_in_primary += 1

    total_audit = len(audit)
    recall = found_in_primary / total_audit if total_audit > 0 else 1.0
    return recall, found_in_primary, total_audit


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_coverage(args: argparse.Namespace) -> int:
    project_landscape = Path(args.landscape)
    ledger_path = Path(args.ledger)

    if not project_landscape.exists():
        print(f"ERROR: landscape file not found: {project_landscape}", file=sys.stderr)
        return 2
    landscape_text = project_landscape.read_text()
    ledger = load_json_safe(ledger_path)
    if not isinstance(ledger, dict):
        ledger = {}

    clusters = extract_clusters(landscape_text)
    per_cluster = count_papers_per_cluster(ledger, landscape_text)
    zero_coverage = [c for c, count in per_cluster.items() if count == 0]
    precision, n_relevant, n_total = estimate_precision(ledger)

    report_lines = [
        "# Search Quality Report — Coverage & Precision",
        f"\n**Date:** {datetime.utcnow().date()}",
        f"**Total papers in ledger:** {n_total}",
        f"**Relevant papers (Tier 1 or 2):** {n_relevant}",
        f"**Precision estimate:** {precision:.0%} (target: >70%)",
        "",
        "## Cluster Coverage",
        "",
        "| Cluster | Papers in Ledger |",
        "|---------|-----------------|",
    ]
    for cluster in clusters:
        count = per_cluster.get(cluster, 0)
        status = "✓" if count > 0 else "⚠ MISSING"
        report_lines.append(f"| {cluster} | {count} {status} |")

    if zero_coverage:
        report_lines += [
            "",
            f"**⚠ {len(zero_coverage)} clusters with zero coverage:**",
            *[f"  - {c}" for c in zero_coverage],
            "",
            "**Action:** Run additional targeted searches for these clusters before proceeding.",
        ]
    else:
        report_lines.append("\n**✓ All clusters have at least one paper in the ledger.**")

    report_lines += [
        "",
        "## Coverage Targets",
        f"- Clusters covered: {len(clusters) - len(zero_coverage)}/{len(clusters)} "
        f"({'✓ PASS' if not zero_coverage else '✗ FAIL — missing clusters'})",
        f"- Precision: {precision:.0%} ({'✓ PASS' if precision >= 0.70 else '✗ BELOW TARGET (70%)'})",
    ]

    report = "\n".join(report_lines)
    if args.output:
        Path(args.output).write_text(report)
        print(f"Coverage report written to {args.output}")
    else:
        print(report)

    return 0 if not zero_coverage and precision >= 0.70 else 1


def cmd_recall(args: argparse.Namespace) -> int:
    primary_path = Path(args.primary_results)
    audit_path = Path(args.audit_results)

    primary = load_json_safe(primary_path)
    audit_raw = load_json_safe(audit_path)
    if isinstance(audit_raw, dict):
        audit_list = list(audit_raw.values())
    else:
        audit_list = audit_raw  # type: ignore

    if not isinstance(primary, dict):
        print("ERROR: primary results must be a JSON object (citation ledger format)", file=sys.stderr)
        return 2

    try:
        recall, found, total = compute_recall_vs_audit(primary, audit_list)
    except ImportError:
        # If dedup_papers not importable, use simple title matching
        primary_titles = [e.get("title", "").lower() for e in primary.values()]
        found = sum(1 for p in audit_list if p.get("title", "").lower() in primary_titles)
        total = len(audit_list)
        recall = found / total if total > 0 else 1.0

    report_lines = [
        "# Search Quality Report — Recall Estimate",
        f"\n**Date:** {datetime.utcnow().date()}",
        f"**Audit papers:** {total}",
        f"**Found in primary search:** {found}",
        f"**Recall estimate:** {recall:.0%} (target: >85%)",
        f"**Status:** {'✓ PASS' if recall >= 0.85 else '✗ BELOW TARGET — consider additional search passes'}",
    ]

    if recall < 0.85:
        missed = total - found
        report_lines += [
            "",
            f"**{missed} papers from the audit were not found by primary search.**",
            "Review the missed papers and determine which search strategies would have found them.",
        ]

    report = "\n".join(report_lines)
    if args.output:
        Path(args.output).write_text(report)
        print(f"Recall report written to {args.output}")
    else:
        print(report)

    return 0 if recall >= 0.85 else 1


def cmd_full(args: argparse.Namespace) -> int:
    project = Path(args.project)

    landscape_path = project / "research-landscape.md"
    ledger_path = project / ".epistemic" / "citation_ledger.json"
    claim_overlap_path = project / "claim-overlap-report.md"

    ledger = load_json_safe(ledger_path) if ledger_path.exists() else {}
    if not isinstance(ledger, dict):
        ledger = {}
    landscape_text = landscape_path.read_text() if landscape_path.exists() else ""
    claim_overlap_text = claim_overlap_path.read_text() if claim_overlap_path.exists() else ""

    precision, n_relevant, n_total = estimate_precision(ledger)
    threat_rate, n_ledger_threats, n_report_threats = estimate_threat_detection(ledger, claim_overlap_text)
    clusters = extract_clusters(landscape_text)
    per_cluster = count_papers_per_cluster(ledger, landscape_text)
    zero_clusters = [c for c, cnt in per_cluster.items() if cnt == 0]

    lines = [
        "# Search Quality Report — Full Assessment",
        f"\n**Date:** {datetime.utcnow().date()}",
        f"**Project:** {project.name}",
        "",
        "## Metrics",
        "",
        f"| Metric | Value | Target | Status |",
        f"|--------|-------|--------|--------|",
        f"| Precision | {precision:.0%} | >70% | {'✓' if precision >= 0.70 else '✗'} |",
        f"| Cluster coverage | {len(clusters)-len(zero_clusters)}/{len(clusters)} | 100% | {'✓' if not zero_clusters else '✗'} |",
        f"| Threat detection (internal) | {threat_rate:.0%} | >95% | {'✓' if threat_rate >= 0.95 else '✗'} |",
        f"| Total papers in ledger | {n_total} | ≥50 | {'✓' if n_total >= 50 else '✗'} |",
        "",
        "## Missing Coverage",
    ]
    if zero_clusters:
        lines += [f"  - Cluster missing: {c}" for c in zero_clusters]
    else:
        lines.append("  None — all clusters covered.")

    lines += [
        "",
        "## Recommendations",
    ]
    if precision < 0.70:
        lines.append("  - Low precision: many papers flagged as relevant may not be. Tighten search queries.")
    if zero_clusters:
        lines.append("  - Run targeted searches for missing clusters.")
    if threat_rate < 0.95:
        lines.append("  - Threat detection below target: re-run adversarial search with broader queries.")
    if n_total < 50:
        lines.append("  - Paper count below minimum: run additional search passes.")
    if all([precision >= 0.70, not zero_clusters, threat_rate >= 0.95, n_total >= 50]):
        lines.append("  ✓ All metrics meet targets. Search quality is sufficient.")

    report = "\n".join(lines)
    output = args.output or str(project / "search-quality-report.md")
    Path(output).write_text(report)
    print(f"Full search quality report written to {output}")

    all_pass = precision >= 0.70 and not zero_clusters and threat_rate >= 0.95 and n_total >= 50
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Measure research search quality metrics")
    sub = parser.add_subparsers(dest="command")

    p_cov = sub.add_parser("coverage", help="Cluster coverage and precision")
    p_cov.add_argument("--landscape", required=True)
    p_cov.add_argument("--ledger", required=True)
    p_cov.add_argument("--output")

    p_recall = sub.add_parser("recall", help="Recall estimate via audit search")
    p_recall.add_argument("--primary-results", required=True)
    p_recall.add_argument("--audit-results", required=True)
    p_recall.add_argument("--output")

    p_full = sub.add_parser("full", help="Full quality report for a project")
    p_full.add_argument("--project", required=True)
    p_full.add_argument("--output")

    args = parser.parse_args()
    dispatch = {"coverage": cmd_coverage, "recall": cmd_recall, "full": cmd_full}

    if not args.command or args.command not in dispatch:
        parser.print_help()
        sys.exit(2)

    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
