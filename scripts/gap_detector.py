#!/usr/bin/env python3
"""
gap_detector.py — Step 21: Analysis-to-Design feedback gate.

Compares planned experiments (experiment-plan.md) against completed analysis
(analysis-report.md) to identify critical missing experiments, ablations,
baselines, and statistical rigor gaps.

Usage:
    python scripts/gap_detector.py \
        --experiment-plan  $PROJECT_DIR/experiment-plan.md \
        --analysis-report  $PROJECT_DIR/analysis-report.md \
        --hypotheses       $PROJECT_DIR/hypotheses.md \
        --landscape        $PROJECT_DIR/competitive-landscape.md \
        --output           $PROJECT_DIR/gap-detection-report.md

Exit codes:
    0 — No Critical gaps found (Important/Minor gaps may still exist)
    1 — One or more Critical gaps found → triggers Loop 1 back to Step 9
    2 — Input file error
"""

import argparse
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


def extract_section(text: str, section_pattern: str) -> str:
    """Extract text under a markdown heading matching the pattern."""
    pattern = re.compile(
        rf"^#{1,3}\s+{section_pattern}.*?$(.+?)(?=^#{1,3}\s|\Z)",
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def extract_list_items(text: str) -> list[str]:
    """Extract bullet/numbered list items from markdown text."""
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        m = re.match(r"^[-*+•]\s+(.+)", stripped)
        if not m:
            m = re.match(r"^\d+[.)]\s+(.+)", stripped)
        if m:
            items.append(m.group(1).strip())
    return items


def extract_headings(text: str, level: int = 3) -> list[str]:
    """Extract all headings of a given level."""
    pattern = re.compile(rf"^{'#' * level}\s+(.+)", re.MULTILINE)
    return [m.group(1).strip() for m in pattern.finditer(text)]


def normalize(s: str) -> str:
    """Lowercase + strip punctuation + collapse spaces."""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def token_overlap(a: str, b: str) -> float:
    """Jaccard similarity on word sets."""
    ta = set(normalize(a).split())
    tb = set(normalize(b).split())
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Gap detection logic
# ---------------------------------------------------------------------------

_HYPER_PATTERNS = [
    r"learning[_ ]rate", r"\blr\b", r"batch[_ ]size", r"epoch", r"layer",
    r"dropout", r"hidden[_ ]size", r"optimizer", r"weight[_ ]decay",
    r"momentum", r"scheduler",
]

_STAT_INDICATORS = [
    r"confidence interval", r"\bCI\b", r"p[- ]value", r"\bp\s*[<=>]",
    r"standard deviation", r"\bstd\b", r"effect size", r"significance",
    r"ANOVA", r"t-test", r"Wilcoxon", r"Mann-Whitney", r"correction",
]

_ABLATION_WORDS = re.compile(
    r"\bablat|w/o\b|without\b|remove[sd]?\b|effect of\b|impact of\b",
    re.IGNORECASE,
)

_BASELINE_WORDS = re.compile(
    r"\bbaseline\b|\bcompar[ei]|\bvs\.?\b|\bversus\b|\bstate.of.the.art\b|\bSOTA\b",
    re.IGNORECASE,
)


def extract_planned_experiments(plan_text: str) -> dict:
    """
    Extract planned experiments from experiment-plan.md.
    Returns dict with keys: baselines, ablations, primary_experiments, hypotheses_covered.
    """
    text = plan_text

    # Look for experiment identifiers in various common formats
    planned: dict[str, list[str]] = {
        "baselines": [],
        "ablations": [],
        "primary": [],
        "hypotheses": [],
    }

    # Extract baselines
    baseline_section = extract_section(text, r"[Bb]aseline")
    if not baseline_section:
        baseline_section = extract_section(text, r"[Cc]omparison")
    planned["baselines"] = extract_list_items(baseline_section) if baseline_section else []

    # Also pick up inline baseline mentions from entire doc
    if not planned["baselines"]:
        for line in text.splitlines():
            if _BASELINE_WORDS.search(line) and any(
                c.isupper() for c in line
            ):
                planned["baselines"].append(line.strip())

    # Extract ablations
    ablation_section = extract_section(text, r"[Aa]blat")
    planned["ablations"] = extract_list_items(ablation_section) if ablation_section else []

    # Extract primary experiments / hypothesis-driven experiments
    hyp_section = extract_section(text, r"[Hh]ypothes")
    planned["hypotheses"] = extract_list_items(hyp_section) if hyp_section else []

    # Use h3 headings as experiment identifiers
    planned["primary"] = [
        h for h in extract_headings(text, 3)
        if not re.search(r"baseline|ablat|hypothes|statistic|power|budget",
                         h, re.IGNORECASE)
    ]

    return planned


def extract_completed_experiments(analysis_text: str) -> dict:
    """
    Extract what was actually reported in analysis-report.md.
    """
    completed: dict[str, list[str]] = {
        "reported_sections": extract_headings(analysis_text, 3),
        "has_statistical_rigor": False,
        "has_baselines": bool(_BASELINE_WORDS.search(analysis_text)),
        "has_ablations": bool(_ABLATION_WORDS.search(analysis_text)),
        "statistical_tests": [],
    }

    # Check for statistical rigor indicators
    for pat in _STAT_INDICATORS:
        if re.search(pat, analysis_text, re.IGNORECASE):
            completed["has_statistical_rigor"] = True
            completed["statistical_tests"].append(
                re.search(pat, analysis_text, re.IGNORECASE).group()
            )

    return completed


# ---------------------------------------------------------------------------
# Gap classification
# ---------------------------------------------------------------------------

def classify_gaps(
    planned: dict,
    completed: dict,
    plan_text: str,
    analysis_text: str,
    hypotheses_text: str,
    landscape_text: str,
) -> list[dict]:
    """Return a list of gap dicts with keys: name, severity, description, action, route_to."""
    gaps: list[dict] = []

    # --- Gap 1: Missing ablations ---
    if planned["ablations"]:
        missing_ablations = []
        for abl in planned["ablations"]:
            # Check if this ablation appears in analysis
            found = any(
                token_overlap(abl, sec) > 0.4
                for sec in completed["reported_sections"]
            ) or normalize(abl) in normalize(analysis_text)
            if not found:
                missing_ablations.append(abl)
        if missing_ablations:
            severity = "Critical" if len(missing_ablations) >= 2 else "Important"
            gaps.append({
                "name": "Missing ablation experiments",
                "severity": severity,
                "description": (
                    f"{len(missing_ablations)} planned ablation(s) not found in analysis: "
                    + "; ".join(missing_ablations[:5])
                ),
                "action": (
                    "Run the missing ablations and add results to analysis-report.md. "
                    "Without ablations, individual contribution components cannot be isolated."
                ),
                "route_to": "experiments",
            })
    elif not completed["has_ablations"]:
        gaps.append({
            "name": "No ablation study",
            "severity": "Important",
            "description": (
                "No ablation experiments found in analysis-report.md. "
                "Reviewers typically require ablations to validate each contribution component."
            ),
            "action": "Design and run ablations for each claimed contribution component.",
            "route_to": "experiments",
        })

    # --- Gap 2: Missing baselines ---
    if planned["baselines"]:
        missing_baselines = []
        for bl in planned["baselines"]:
            found = normalize(bl) in normalize(analysis_text) or any(
                token_overlap(bl, sec) > 0.45
                for sec in completed["reported_sections"]
            )
            if not found:
                missing_baselines.append(bl)
        if missing_baselines:
            severity = "Critical" if missing_baselines else "Important"
            gaps.append({
                "name": "Missing baseline comparisons",
                "severity": severity,
                "description": (
                    f"{len(missing_baselines)} planned baseline(s) not reported: "
                    + "; ".join(missing_baselines[:5])
                ),
                "action": (
                    "Add comparisons against missing baselines. "
                    "Missing prior-work baselines are a primary rejection cause."
                ),
                "route_to": "experiments",
            })

    # --- Gap 3: Competitive landscape baselines ---
    if landscape_text and not completed["has_baselines"]:
        # Check if landscape lists specific papers that should be baselines
        high_overlap = re.findall(
            r"HIGH.{0,100}?([A-Z][a-zA-Z]+\s+et\s+al\.?,?\s*\d{4}|[A-Z][a-zA-Z]+ \d{4})",
            landscape_text,
        )
        if high_overlap:
            gaps.append({
                "name": "HIGH-overlap competitive papers not used as baselines",
                "severity": "Critical",
                "description": (
                    "competitive-landscape.md identifies HIGH-overlap papers but analysis "
                    "does not include them as baselines: "
                    + "; ".join(high_overlap[:3])
                ),
                "action": (
                    "Include HIGH-overlap papers as baselines, or document a justified "
                    "exclusion reason. Reviewers expect comparison against cited prior work."
                ),
                "route_to": "experiments",
            })

    # --- Gap 4: Statistical rigor ---
    if not completed["has_statistical_rigor"]:
        gaps.append({
            "name": "Missing statistical significance testing",
            "severity": "Critical",
            "description": (
                "analysis-report.md contains no evidence of statistical testing "
                "(confidence intervals, p-values, effect sizes, or statistical tests). "
                "NeurIPS/ICML/ICLR reviewers require statistical significance."
            ),
            "action": (
                "Run statistical tests on primary results. Report mean ± std or 95% CI "
                "for all primary comparisons. Apply multiple-comparison correction if needed."
            ),
            "route_to": "analysis",
        })

    # --- Gap 5: Replication fidelity ---
    # If experiment plan contains conditions explicitly labeled as replications of
    # prior work, flag missing citation of source conditions (MAJOR) and metric
    # differences (MAJOR). Does not produce CRITICAL — replication issues are
    # important but do not block the pipeline.
    _REPLICATION_PATTERN = re.compile(
        r"\breplicat[ei]|\breplication\b|\bre-implement|\bre.implement",
        re.IGNORECASE,
    )
    if _REPLICATION_PATTERN.search(plan_text):
        # Extract lines mentioning replication to identify the conditions
        replication_lines = [
            line.strip()
            for line in plan_text.splitlines()
            if _REPLICATION_PATTERN.search(line)
        ]
        # Check 1: Is there a citation / source reference for the replication?
        citation_pattern = re.compile(r"\(\w+\s*\d{4}|\[.*?\]|\barXiv\b|cite_key", re.IGNORECASE)
        has_citation = any(citation_pattern.search(ln) for ln in replication_lines)
        if not has_citation:
            gaps.append({
                "name": "Replication condition lacks source citation",
                "severity": "Important",
                "description": (
                    "experiment-plan.md contains replication condition(s) but does not cite "
                    "the original paper's hyperparameters or experimental setup. "
                    "Uncited replications may use different settings and invalidate comparisons."
                ),
                "action": (
                    "For each replication condition, cite the source paper and specify "
                    "which hyperparameters / data splits are taken from the original work. "
                    "Note any intentional deviations (e.g., different dataset, annotation subset)."
                ),
                "route_to": "experiments",
            })
        # Check 2: Are the evaluation metrics the same as the original?
        # Heuristic: if analysis report uses metrics not mentioned in replication lines, flag.
        replication_context = " ".join(replication_lines)
        standard_metrics = re.findall(
            r"\bF1\b|\baccuracy\b|\bAUC\b|\bMCC\b|\bcomprehensiveness\b|\bsufficiency\b"
            r"|\bIoU\b|\bspearman\b|\bpearson\b",
            analysis_text,
            re.IGNORECASE,
        )
        original_metrics = re.findall(
            r"\bF1\b|\baccuracy\b|\bAUC\b|\bMCC\b|\bcomprehensiveness\b|\bsufficiency\b"
            r"|\bIoU\b|\bspearman\b|\bpearson\b",
            replication_context,
            re.IGNORECASE,
        )
        # Only flag if replication context mentions specific metrics and analysis differs
        if original_metrics and standard_metrics:
            orig_set = {m.lower() for m in original_metrics}
            anal_set = {m.lower() for m in standard_metrics}
            metrics_only_in_analysis = anal_set - orig_set
            if metrics_only_in_analysis:
                gaps.append({
                    "name": "Replication evaluated on different metrics than original",
                    "severity": "Important",
                    "description": (
                        f"Replication condition references metrics {sorted(orig_set)} but "
                        f"analysis uses additional metrics {sorted(metrics_only_in_analysis)}. "
                        "This may indicate the comparison is not apples-to-apples with the "
                        "original paper."
                    ),
                    "action": (
                        "Verify that the replication evaluation protocol matches the original "
                        "paper's evaluation. Document any intentional differences explicitly."
                    ),
                    "route_to": "analysis",
                })

    # --- Gap 7 (renumbered from 5): Hypothesis coverage ---
    if hypotheses_text and planned["hypotheses"]:
        # Count how many hypotheses are mentioned in analysis
        h_lines = [
            line.strip() for line in hypotheses_text.splitlines()
            if re.match(r"^H\d|^-\s|^\*\s", line.strip())
        ]
        if h_lines:
            missing_hs = [
                h for h in h_lines
                if token_overlap(h, analysis_text) < 0.20
            ]
            if len(missing_hs) > len(h_lines) // 2:
                gaps.append({
                    "name": "Hypotheses not covered by analysis",
                    "severity": "Important",
                    "description": (
                        f"{len(missing_hs)}/{len(h_lines)} hypotheses from hypotheses.md "
                        "do not appear to be addressed in analysis-report.md."
                    ),
                    "action": (
                        "Ensure every primary hypothesis has a corresponding analysis section "
                        "with results and interpretation."
                    ),
                    "route_to": "analysis",
                })

    # --- Gap 8 (renumbered from 6): Missing primary experiments ---
    if planned["primary"]:
        missing_primary = [
            exp for exp in planned["primary"]
            if not any(
                token_overlap(exp, sec) > 0.40
                for sec in completed["reported_sections"]
            ) and normalize(exp) not in normalize(analysis_text)
        ]
        if len(missing_primary) >= 2:
            gaps.append({
                "name": "Primary experiments not reported",
                "severity": "Critical" if len(missing_primary) >= 3 else "Important",
                "description": (
                    f"{len(missing_primary)} planned experiment(s) not found in analysis: "
                    + "; ".join(missing_primary[:5])
                ),
                "action": (
                    "Execute and analyze the missing experiments, or document why they "
                    "were dropped and update the experiment plan."
                ),
                "route_to": "experiments",
            })

    return gaps


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(
    gaps: list[dict],
    output_path: Path,
    plan_path: Path,
    analysis_path: Path,
) -> None:
    critical = [g for g in gaps if g["severity"] == "Critical"]
    important = [g for g in gaps if g["severity"] == "Important"]
    minor = [g for g in gaps if g["severity"] == "Minor"]

    lines = [
        "---",
        f"critical_gaps_found: {'true' if critical else 'false'}",
        f"total_gaps: {len(gaps)}",
        f"critical: {len(critical)}",
        f"important: {len(important)}",
        f"minor: {len(minor)}",
        "---",
        "",
        "# Gap Detection Report (Step 21)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Experiment plan:** `{plan_path}`",
        f"**Analysis report:** `{analysis_path}`",
        "",
        f"## Summary",
        "",
        f"- **Critical gaps:** {len(critical)} {'← triggers loop back to Step 9' if critical else ''}",
        f"- **Important gaps:** {len(important)}",
        f"- **Minor gaps:** {len(minor)}",
        "",
    ]

    if not gaps:
        lines += [
            "**Result: PASS** — No gaps detected. All planned experiments appear to be "
            "addressed in the analysis report.",
        ]
    else:
        lines += [
            f"**Result: {'BLOCK' if critical else 'WARN'}**",
            "",
        ]

    def write_gap_section(title: str, gap_list: list[dict]) -> list[str]:
        if not gap_list:
            return []
        out = [f"## {title}", ""]
        for g in gap_list:
            out += [
                f"### {g['name']}",
                "",
                f"- **Severity:** {g['severity']}",
                f"- **Description:** {g['description']}",
                f"- **Required action:** {g['action']}",
                f"- **Route to:** `{g.get('route_to', 'experiments')}`",
                "",
            ]
        return out

    lines += write_gap_section("Critical Gaps", critical)
    lines += write_gap_section("Important Gaps", important)
    lines += write_gap_section("Minor Gaps", minor)

    lines += [
        "---",
        "",
        "## Loop Routing",
        "",
        "If `critical_gaps_found: true`:",
        "```bash",
        "python scripts/pipeline_state.py increment-counter gap_detection_loops --max 2",
        "# Exit 0: route back to Step 9 (design-experiments)",
        "# Exit 1: proceed with gaps documented as limitations",
        "```",
    ]

    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 21: Detect experimental gaps between plan and analysis"
    )
    parser.add_argument("--experiment-plan", required=True, help="Path to experiment-plan.md")
    parser.add_argument("--analysis-report", required=True, help="Path to analysis-report.md")
    parser.add_argument("--hypotheses", default="", help="Path to hypotheses.md")
    parser.add_argument("--landscape", default="", help="Path to competitive-landscape.md")
    parser.add_argument("--output", required=True, help="Output path for gap-detection-report.md")
    args = parser.parse_args()

    plan_path = Path(args.experiment_plan)
    analysis_path = Path(args.analysis_report)

    if not plan_path.exists():
        print(f"ERROR: experiment-plan not found: {plan_path}", file=sys.stderr)
        sys.exit(2)
    if not analysis_path.exists():
        print(f"ERROR: analysis-report not found: {analysis_path}", file=sys.stderr)
        sys.exit(2)

    plan_text = load_text(plan_path)
    analysis_text = load_text(analysis_path)
    hypotheses_text = load_text(Path(args.hypotheses)) if args.hypotheses else ""
    landscape_text = load_text(Path(args.landscape)) if args.landscape else ""

    planned = extract_planned_experiments(plan_text)
    completed = extract_completed_experiments(analysis_text)

    gaps = classify_gaps(
        planned, completed,
        plan_text, analysis_text,
        hypotheses_text, landscape_text,
    )

    critical = [g for g in gaps if g["severity"] == "Critical"]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(gaps, output_path, plan_path, analysis_path)

    print(
        f"Gaps found — Critical: {len(critical)}  "
        f"Important: {len([g for g in gaps if g['severity'] == 'Important'])}  "
        f"Minor: {len([g for g in gaps if g['severity'] == 'Minor'])}"
    )
    print(f"Report written to: {output_path}")

    if critical:
        print(
            f"\n[LOOP TRIGGER] {len(critical)} critical gap(s) found. "
            f"Increment gap_detection_loops counter and route back to Step 9.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
