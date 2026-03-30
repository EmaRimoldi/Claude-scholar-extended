#!/usr/bin/env python3
"""
consistency_oracle.py — Epistemic consistency service.

Verifies that claim confidence levels, hedging language, and terminology
are consistent across the manuscript and the epistemic layer. Called at
Step 31 (after prose generation) and Step 35 (adversarial review prep).

Usage:
    # Sweep all claims in the epistemic layer against the manuscript
    python scripts/consistency_oracle.py sweep \
        --project      $PROJECT_DIR \
        --manuscript   $PROJECT_DIR/manuscript/ \
        --output       $PROJECT_DIR/.epistemic/consistency_ledger.json \
        --report       $PROJECT_DIR/consistency-report.md

    # Check a specific claim ID
    python scripts/consistency_oracle.py check \
        --project      $PROJECT_DIR \
        --claim-id     C1 \
        --context      "The proposed method achieves 94.2% accuracy..." \
        --output       $PROJECT_DIR/.epistemic/consistency_ledger.json

Exit codes:
    0 — Consistent (or check passed)
    1 — Inconsistencies found (CRITICAL severity in sweep mode)
    2 — Input error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> object:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def collect_tex_files(manuscript_path: Path) -> list[Path]:
    if manuscript_path.is_file():
        return [manuscript_path]
    return sorted(manuscript_path.rglob("*.tex"))


def load_manuscript(manuscript_path: Path) -> str:
    files = collect_tex_files(manuscript_path)
    parts = []
    for f in files:
        try:
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n".join(parts)


def strip_latex(text: str) -> str:
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\(?:textbf|textit|emph|text)\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Confidence / hedging logic (mirrors confidence_to_hedging.py thresholds)
# ---------------------------------------------------------------------------

ASSERTIVE_THRESHOLD = 0.80
HEDGED_THRESHOLD = 0.50

_ASSERTIVE_PATTERNS = re.compile(
    r"\bwe\s+(?:show|prove|demonstrate|establish)\b|"
    r"\bsignificantly\s+(?:better|outperform|improve)\b|"
    r"\bsuperior\s+to\b|"
    r"\bstate.of.the.art\b.*\bachieve\b|"
    r"\balways\b|\bnever\b|\buniversally\b",
    re.IGNORECASE,
)

_HEDGED_PATTERNS = re.compile(
    r"\bwe\s+(?:suggest|propose|argue|believe|find)\b|"
    r"\bappear[s]?\s+to\b|\bseem[s]?\s+to\b|"
    r"\bmay\b|\bmight\b|\bcould\b|"
    r"\bin\s+(?:most|many)\s+cases\b|"
    r"\btend\s+to\b|\bgenerally\b",
    re.IGNORECASE,
)

_CAUTIOUS_PATTERNS = re.compile(
    r"\blimit(?:ed|ation)s?\b|\bpreliminary\b|\bfuture\s+work\b|"
    r"\brequires?\s+further\b|\bcannot\s+(?:rule\s+out|be\s+sure)\b|"
    r"\bunclear\b|\bopen\s+question\b|\bnot\s+(?:yet\s+)?(?:clear|established)\b",
    re.IGNORECASE,
)


def classify_prose_strength(text: str) -> str:
    """Return 'assertive', 'hedged', or 'cautious' for a sentence/passage."""
    if _CAUTIOUS_PATTERNS.search(text):
        return "cautious"
    if _ASSERTIVE_PATTERNS.search(text):
        return "assertive"
    if _HEDGED_PATTERNS.search(text):
        return "hedged"
    return "neutral"


def required_strength(confidence: float) -> str:
    if confidence >= ASSERTIVE_THRESHOLD:
        return "assertive"
    if confidence >= HEDGED_THRESHOLD:
        return "hedged"
    return "cautious"


# ---------------------------------------------------------------------------
# Claim extraction from manuscript
# ---------------------------------------------------------------------------

def extract_sentences(text: str, min_words: int = 5) -> list[str]:
    return [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text)
        if len(s.split()) >= min_words
    ]


def find_claim_sentences(manuscript_text: str, claim_text: str) -> list[str]:
    """Find sentences in the manuscript that express a given claim."""
    norm_claim = set(re.sub(r"[^\w\s]", " ", claim_text.lower()).split())
    # Remove stopwords
    stopwords = {"the", "a", "an", "is", "are", "we", "our", "this", "that", "in",
                 "of", "to", "and", "or", "by", "for", "with", "on", "at"}
    norm_claim -= stopwords

    if len(norm_claim) < 3:
        return []

    sentences = extract_sentences(strip_latex(manuscript_text))
    matches = []
    for sent in sentences:
        norm_sent = set(re.sub(r"[^\w\s]", " ", sent.lower()).split())
        overlap = len(norm_claim & norm_sent) / max(len(norm_claim), 1)
        if overlap >= 0.35:
            matches.append(sent)
    return matches[:5]  # Return at most 5 matching sentences


# ---------------------------------------------------------------------------
# Consistency checks
# ---------------------------------------------------------------------------

def check_claim_hedging(
    claim: dict,
    manuscript_text: str,
    confidence_tracker: dict,
) -> list[dict]:
    """
    Check that the manuscript sentences expressing this claim use appropriate
    hedging language given the registered confidence.
    """
    issues: list[dict] = []
    claim_id = claim.get("id", "")
    claim_text = claim.get("text", "")

    # Get confidence from tracker or from claim directly
    confidence = confidence_tracker.get(claim_id, {})
    if isinstance(confidence, dict):
        conf_val = confidence.get("confidence", claim.get("confidence", 0.5))
    else:
        conf_val = float(confidence) if confidence else claim.get("confidence", 0.5)

    if not isinstance(conf_val, (int, float)):
        try:
            conf_val = float(conf_val)
        except (ValueError, TypeError):
            conf_val = 0.5

    required = required_strength(conf_val)
    matching_sentences = find_claim_sentences(manuscript_text, claim_text)

    for sent in matching_sentences:
        actual = classify_prose_strength(sent)
        if actual == "neutral":
            continue

        if required == "cautious" and actual == "assertive":
            issues.append({
                "claim_id": claim_id,
                "confidence": conf_val,
                "required_strength": required,
                "actual_strength": actual,
                "severity": "CRITICAL",
                "sentence": sent[:200],
                "issue": (
                    f"Claim {claim_id} has confidence {conf_val:.2f} (requires CAUTIOUS hedging) "
                    f"but manuscript sentence is ASSERTIVE."
                ),
            })
        elif required == "hedged" and actual == "assertive":
            issues.append({
                "claim_id": claim_id,
                "confidence": conf_val,
                "required_strength": required,
                "actual_strength": actual,
                "severity": "MAJOR",
                "sentence": sent[:200],
                "issue": (
                    f"Claim {claim_id} has confidence {conf_val:.2f} (requires HEDGED language) "
                    f"but manuscript sentence is ASSERTIVE."
                ),
            })
        elif required == "assertive" and actual == "cautious":
            issues.append({
                "claim_id": claim_id,
                "confidence": conf_val,
                "required_strength": required,
                "actual_strength": actual,
                "severity": "MINOR",
                "sentence": sent[:200],
                "issue": (
                    f"Claim {claim_id} has confidence {conf_val:.2f} (allows ASSERTIVE language) "
                    f"but manuscript uses overly cautious hedging — may undersell contribution."
                ),
            })

    return issues


def check_terminology_drift(manuscript_text: str, previous_ledger: dict) -> list[dict]:
    """
    Check if key terms used in previous sweeps have been changed in the manuscript.
    """
    issues = []
    canonical_terms = previous_ledger.get("canonical_terms", {})
    plain = strip_latex(manuscript_text).lower()

    for canonical, variants in canonical_terms.items():
        # If the canonical form is absent but a variant is present
        if canonical.lower() not in plain:
            for var in variants:
                if var.lower() in plain and var.lower() != canonical.lower():
                    issues.append({
                        "severity": "MINOR",
                        "issue": (
                            f"Canonical term '{canonical}' not found; "
                            f"variant '{var}' used instead. Update to canonical form."
                        ),
                    })
                    break

    return issues


def extract_canonical_terms(manuscript_text: str) -> dict[str, list[str]]:
    """
    Build canonical term map from current manuscript (most-frequent form wins).
    Groups variants of the same base term.
    """
    plain = strip_latex(manuscript_text)
    # Find multi-word capitalized terms and acronyms
    candidates = re.findall(
        r"\b([A-Z][a-zA-Z]+(?:[-\s][A-Z][a-zA-Z]+)+|[A-Z]{2,6}(?:-[a-zA-Z0-9]+)?)\b",
        plain,
    )
    freq: dict[str, int] = {}
    for c in candidates:
        freq[c] = freq.get(c, 0) + 1

    # Group by lowercase
    groups: dict[str, list[tuple[int, str]]] = {}
    for term, count in freq.items():
        key = term.lower().replace("-", "").replace(" ", "")
        groups.setdefault(key, []).append((count, term))

    canonical: dict[str, list[str]] = {}
    for key, variants in groups.items():
        if len(variants) >= 2:
            variants.sort(reverse=True)
            can = variants[0][1]
            canonical[can] = [v for _, v in variants if v != can]

    return canonical


# ---------------------------------------------------------------------------
# Consistency ledger
# ---------------------------------------------------------------------------

def load_ledger(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {
        "last_sweep": None,
        "sweep_count": 0,
        "issues": [],
        "canonical_terms": {},
        "claim_checks": {},
    }


def save_ledger(path: Path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2))


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_sweep(args: argparse.Namespace) -> int:
    """Sweep all claims against the manuscript."""
    project_dir = Path(args.project)
    manuscript_path = Path(args.manuscript)
    output_path = Path(args.output)
    report_path = Path(args.report) if args.report else None

    claim_graph_path = project_dir / ".epistemic" / "claim_graph.json"
    confidence_tracker_path = project_dir / ".epistemic" / "confidence_tracker.json"

    claim_graph = load_json(claim_graph_path)
    confidence_tracker = load_json(confidence_tracker_path)
    ledger = load_ledger(output_path)

    if not manuscript_path.exists():
        print(f"ERROR: manuscript not found: {manuscript_path}", file=sys.stderr)
        return 2

    manuscript_text = load_manuscript(manuscript_path)
    if not manuscript_text:
        print(f"WARNING: manuscript is empty at {manuscript_path}", file=sys.stderr)

    claims = [
        n for n in claim_graph.get("nodes", [])
        if n.get("type") in ("claim", "contribution", "finding", None)
           and n.get("text")
    ]

    print(f"Sweeping {len(claims)} claims against manuscript...")

    all_issues: list[dict] = []

    for claim in claims:
        issues = check_claim_hedging(claim, manuscript_text, confidence_tracker)
        all_issues.extend(issues)

    # Terminology drift
    canonical_now = extract_canonical_terms(manuscript_text)
    term_issues = check_terminology_drift(manuscript_text, ledger)
    all_issues.extend(term_issues)

    # Update ledger
    ledger["last_sweep"] = datetime.now(timezone.utc).isoformat()
    ledger["sweep_count"] = ledger.get("sweep_count", 0) + 1
    ledger["issues"] = all_issues
    ledger["canonical_terms"] = canonical_now
    save_ledger(output_path, ledger)

    criticals = [i for i in all_issues if i.get("severity") == "CRITICAL"]
    majors = [i for i in all_issues if i.get("severity") == "MAJOR"]
    minors = [i for i in all_issues if i.get("severity") == "MINOR"]

    print(
        f"Issues — CRITICAL: {len(criticals)}  MAJOR: {len(majors)}  MINOR: {len(minors)}"
    )

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        _write_sweep_report(all_issues, report_path, len(claims))
        print(f"Report written to: {report_path}")

    if criticals:
        print(
            f"\n[BLOCK] {len(criticals)} CRITICAL consistency issue(s). "
            f"Resolve before proceeding.",
            file=sys.stderr,
        )
        return 1

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check a specific claim ID against a provided context string."""
    project_dir = Path(args.project)
    output_path = Path(args.output)

    claim_graph_path = project_dir / ".epistemic" / "claim_graph.json"
    confidence_tracker_path = project_dir / ".epistemic" / "confidence_tracker.json"

    claim_graph = load_json(claim_graph_path)
    confidence_tracker = load_json(confidence_tracker_path)
    ledger = load_ledger(output_path)

    # Find the claim
    claim = None
    for n in claim_graph.get("nodes", []):
        if n.get("id") == args.claim_id:
            claim = n
            break

    if claim is None:
        print(f"WARNING: Claim '{args.claim_id}' not found in claim_graph.json", file=sys.stderr)
        return 0

    issues = check_claim_hedging(claim, args.context, confidence_tracker)

    if issues:
        for issue in issues:
            severity = issue.get("severity", "MINOR")
            print(f"[{severity}] {issue['issue']}")
        # Update ledger
        existing = ledger.get("claim_checks", {})
        existing[args.claim_id] = {
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "issues": issues,
        }
        ledger["claim_checks"] = existing
        save_ledger(output_path, ledger)
    else:
        print(f"[PASS] Claim {args.claim_id} consistency check passed.")

    criticals = [i for i in issues if i.get("severity") == "CRITICAL"]
    return 1 if criticals else 0


def _write_sweep_report(issues: list[dict], report_path: Path, claim_count: int) -> None:
    criticals = [i for i in issues if i.get("severity") == "CRITICAL"]
    majors = [i for i in issues if i.get("severity") == "MAJOR"]
    minors = [i for i in issues if i.get("severity") == "MINOR"]

    result = "BLOCK" if criticals else ("WARN" if majors else "PASS")

    lines = [
        "# Consistency Oracle Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Claims checked:** {claim_count}",
        f"**Issues — CRITICAL:** {len(criticals)}, MAJOR: {len(majors)}, MINOR: {len(minors)}",
        "",
        f"## Result: {result}",
        "",
    ]

    if not issues:
        lines += ["All claims are consistent with their registered confidence levels."]

    def section(title: str, issue_list: list[dict]) -> list[str]:
        if not issue_list:
            return []
        out = [f"## {title}", ""]
        for item in issue_list:
            cid = item.get("claim_id", "—")
            conf = item.get("confidence", "?")
            out += [
                f"### Claim `{cid}` (confidence: {conf})",
                "",
                f"**Issue:** {item.get('issue', '')}",
                "",
                f"**Sentence:** `{item.get('sentence', '')[:200]}`",
                "",
            ]
        return out

    lines += section("CRITICAL Issues", criticals)
    lines += section("MAJOR Issues", majors)
    lines += section("MINOR Issues", minors)

    report_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Epistemic consistency oracle — check/sweep manuscript claims"
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # sweep subcommand
    sweep_p = subparsers.add_parser("sweep", help="Sweep all claims against manuscript")
    sweep_p.add_argument("--project", required=True, help="PROJECT_DIR")
    sweep_p.add_argument("--manuscript", required=True, help="Manuscript directory or file")
    sweep_p.add_argument("--output", required=True, help="Path for consistency_ledger.json")
    sweep_p.add_argument("--report", default="", help="Optional path for Markdown report")

    # check subcommand
    check_p = subparsers.add_parser("check", help="Check a specific claim")
    check_p.add_argument("--project", required=True)
    check_p.add_argument("--claim-id", required=True, help="Claim ID to check")
    check_p.add_argument("--context", required=True, help="Manuscript text or sentence to check against")
    check_p.add_argument("--output", required=True, help="Path for consistency_ledger.json")

    args = parser.parse_args()

    if args.subcommand == "sweep":
        sys.exit(cmd_sweep(args))
    elif args.subcommand == "check":
        sys.exit(cmd_check(args))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
