#!/usr/bin/env python3
"""
audit_claim_coverage.py — Verify that every factual assertion in the manuscript
is registered in the Claim Dependency Graph, and every registered claim appears
in the manuscript.

Two complementary checks:
  1. Unregistered claims: manuscript makes an assertion that was never added to
     claim_graph.json. These are claims that bypassed the evidence verification pipeline.
  2. Dropped claims: claim_graph.json has a registered claim with supporting evidence
     that does not appear anywhere in the manuscript. This means verified evidence
     is being wasted.

Called at Step 33 (/claim-source-align), alongside confidence_to_hedging.py.

Usage:
    python scripts/audit_claim_coverage.py \\
        --claim-graph $PROJECT_DIR/.epistemic/claim_graph.json \\
        --manuscript  $PROJECT_DIR/manuscript/ \\
        --output      $PROJECT_DIR/claim-coverage-report.md

    # Single file mode:
    python scripts/audit_claim_coverage.py \\
        --claim-graph $PROJECT_DIR/.epistemic/claim_graph.json \\
        --tex-file    $PROJECT_DIR/manuscript/main.tex \\
        --output      $PROJECT_DIR/claim-coverage-report.md

Exit codes:
    0 — No unregistered claims found (dropped claims produce warnings only)
    1 — One or more unregistered claims found — hard block
    2 — Input file error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Assertion extraction patterns
# ---------------------------------------------------------------------------

# Heuristic patterns for factual / causal assertions in academic prose
_ASSERTION_PATTERNS = [
    # "we show / demonstrate / prove / find that ..."
    re.compile(
        r"(?:we|our (?:method|approach|model|system|results?))\s+"
        r"(?:show|demonstrate|prove|establish|confirm|find|observe|report)\s+"
        r"(?:that\s+)?(.{10,200}?)[.!]",
        re.IGNORECASE,
    ),
    # "X achieves / outperforms / surpasses Y"
    re.compile(
        r"(?:our (?:method|approach|model)|the proposed .{0,30}?)\s+"
        r"(?:achieves?|obtains?|reaches?|outperforms?|surpasses?|improves?)\s+"
        r"(.{10,150}?)[.!]",
        re.IGNORECASE,
    ),
    # Numerical result statements: "X% improvement", "accuracy of X%"
    re.compile(
        r"(?:improvement|accuracy|precision|recall|F1|BLEU|ROUGE|AUC|score)\s+"
        r"(?:of\s+)?(\d+\.?\d*\s*(?:%|points?|pp))",
        re.IGNORECASE,
    ),
    # "is the first / only / best"
    re.compile(
        r"(?:is|are)\s+(?:the\s+)?(?:first|only|best|state-of-the-art|SOTA)\s+(.{5,80}?)[.,!;]",
        re.IGNORECASE,
    ),
    # Causal claims: "X causes / leads to / results in Y"
    re.compile(
        r"(.{10,80}?)\s+(?:causes?|leads?\s+to|results?\s+in|enables?|improves?)\s+(.{5,80}?)[.,!;]",
        re.IGNORECASE,
    ),
]

# Phrases that disqualify a sentence as a claim (background / motivation)
_NON_CLAIM_INDICATORS = re.compile(
    r"\b(prior work|previous work|existing method|baseline|related work|"
    r"others have|it is known|it has been shown|traditionally|typically|"
    r"commonly|generally|in the literature|motivated by|inspired by)\b",
    re.IGNORECASE,
)


def extract_assertions(tex_source: str) -> list[str]:
    """
    Extract factual assertion phrases from LaTeX source.
    Returns a deduplicated list of assertion strings.
    """
    # Strip LaTeX comments
    text = re.sub(r"%.*", "", tex_source)
    # Strip non-prose environments
    for env in ("equation", "align", "figure", "table", "lstlisting", "verbatim",
                "algorithm", "algorithmic", "tikzpicture", "biblio"):
        text = re.sub(
            rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}", "", text, flags=re.DOTALL
        )
    # Clean LaTeX markup conservatively
    text = re.sub(r"\\(?:textbf|textit|emph|text|mathrm)\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?\{([^}]*)\}", r"\2", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    assertions: list[str] = []
    for pattern in _ASSERTION_PATTERNS:
        for m in pattern.finditer(text):
            full_match = m.group(0).strip()
            # Discard if the sentence is about background work, not the contribution
            if not _NON_CLAIM_INDICATORS.search(full_match):
                assertions.append(full_match[:250])

    # Deduplicate preserving order
    seen: set[str] = set()
    unique = []
    for a in assertions:
        normalised = re.sub(r"\s+", " ", a).lower().strip()
        if normalised not in seen:
            seen.add(normalised)
            unique.append(a)

    return unique


# ---------------------------------------------------------------------------
# Claim matching
# ---------------------------------------------------------------------------

def extract_keywords(text: str) -> list[str]:
    """Extract numeric values and capitalised terms as matching keywords."""
    numerics = re.findall(r"\d+\.?\d*\s*(?:%|points?|pp)?", text)
    cap_terms = re.findall(r"[A-Z][a-zA-Z0-9]+(?:-[A-Z][a-zA-Z0-9]+)*", text)
    long_words = [w for w in text.split() if len(w) > 6]
    return list(dict.fromkeys(numerics + cap_terms + long_words[:6]))


def assertion_matches_claim(assertion: str, claim_text: str) -> bool:
    """
    Determine whether an assertion likely expresses a registered claim.
    Uses bidirectional keyword overlap: keywords from the claim appear in the
    assertion AND keywords from the assertion appear in the claim.
    """
    claim_kws = extract_keywords(claim_text)
    assertion_lower = assertion.lower()
    claim_lower = claim_text.lower()

    if not claim_kws:
        return False

    # Check how many claim keywords appear in the assertion
    hits_in_assertion = sum(1 for kw in claim_kws if kw.lower() in assertion_lower)

    # Also check keyword overlap in the other direction
    assertion_kws = extract_keywords(assertion)
    hits_in_claim = sum(1 for kw in assertion_kws if kw.lower() in claim_lower)

    threshold = max(1, len(claim_kws) * 0.4)
    return hits_in_assertion >= threshold or (hits_in_claim >= 2 and hits_in_claim >= len(assertion_kws) * 0.4)


def find_registered_claim(assertion: str, claims: list[dict]) -> str | None:
    """
    Return the ID of the first claim in claim_graph.json that matches this assertion,
    or None if no match found.
    """
    for claim in claims:
        if assertion_matches_claim(assertion, claim.get("text", "")):
            return claim["id"]
    return None


def claim_appears_in_manuscript(claim_text: str, all_assertions: list[str]) -> bool:
    """Check whether a registered claim is expressed anywhere in the manuscript assertions."""
    claim_kws = extract_keywords(claim_text)
    if not claim_kws:
        return False
    for assertion in all_assertions:
        hits = sum(1 for kw in claim_kws if kw.lower() in assertion.lower())
        if hits >= max(1, len(claim_kws) * 0.4):
            return True
    return False


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(
    unregistered: list[dict],
    dropped: list[dict],
    output_path: Path,
) -> None:
    """Write claim-coverage-report.md."""
    lines = [
        "# Claim Coverage Audit Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Unregistered claims (manuscript → not in graph):** {len(unregistered)}",
        f"**Dropped claims (graph → not in manuscript):** {len(dropped)}",
        "",
    ]

    if not unregistered and not dropped:
        lines += [
            "## Result: PASS",
            "",
            "All manuscript assertions are registered in the claim graph. "
            "All registered claims appear in the manuscript.",
        ]
    else:
        result = "BLOCK" if unregistered else "WARN"
        lines += [f"## Result: {result}", ""]
        if unregistered:
            lines += [
                "**BLOCK:** The following assertions were found in the manuscript but "
                "are not registered in claim_graph.json. They have bypassed the "
                "evidence verification pipeline. Either add them to claim-ledger.md "
                "with supporting evidence, or remove them from the manuscript.",
                "",
                "### Unregistered Claims",
                "",
            ]
            for i, item in enumerate(unregistered, 1):
                lines += [
                    f"#### UC{i}",
                    f"- **Manuscript assertion:** {item['assertion']}",
                    f"- **Location hint:** {item.get('location', 'unknown')}",
                    f"- **Action required:** Add to claim-ledger.md with evidence, or remove from manuscript.",
                    "",
                ]

        if dropped:
            lines += [
                "### Dropped Claims (registered but absent from manuscript)",
                "",
                "These claims have evidence support in the graph but do not appear in the "
                "manuscript. This may indicate unused results or a claim that was removed "
                "during editing without updating the graph.",
                "",
            ]
            for item in dropped:
                lines += [
                    f"- **{item['claim_id']}:** {item['claim_text'][:120]}",
                    f"  - Confidence: {item.get('confidence', 'unknown')}",
                    f"  - Evidence count: {item.get('evidence_count', 0)}",
                    "",
                ]

    lines += [
        "---",
        "",
        "## Audit Methodology",
        "",
        "Assertions are extracted using heuristic patterns matching: we show/demonstrate/find, "
        "achieves/outperforms/surpasses, numerical result statements, causal claims. "
        "Background sentences (mentioning prior work, baselines, related work) are excluded.",
    ]

    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit claim coverage: manuscript assertions vs claim_graph.json"
    )
    parser.add_argument("--claim-graph", required=True, help="Path to .epistemic/claim_graph.json")
    parser.add_argument("--manuscript", default="", help="Path to manuscript directory")
    parser.add_argument("--tex-file", default="", help="Path to single .tex file")
    parser.add_argument("--output", required=True, help="Output path for claim-coverage-report.md")
    args = parser.parse_args()

    # Load claim graph
    claim_graph_path = Path(args.claim_graph)
    if not claim_graph_path.exists():
        print(f"ERROR: claim_graph.json not found: {claim_graph_path}", file=sys.stderr)
        sys.exit(2)
    graph = json.loads(claim_graph_path.read_text())
    claims = graph.get("claims", [])

    if not claims:
        print("ERROR: claim_graph.json contains no claims.", file=sys.stderr)
        sys.exit(2)

    # Collect manuscript text
    tex_sources: list[tuple[str, str]] = []  # (content, filename)
    if args.tex_file:
        p = Path(args.tex_file)
        if not p.exists():
            print(f"ERROR: tex file not found: {p}", file=sys.stderr)
            sys.exit(2)
        tex_sources.append((p.read_text(), p.name))
    elif args.manuscript:
        manuscript_dir = Path(args.manuscript)
        if not manuscript_dir.exists():
            print(f"ERROR: manuscript directory not found: {manuscript_dir}", file=sys.stderr)
            sys.exit(2)
        for tex_file in sorted(manuscript_dir.rglob("*.tex")):
            tex_sources.append((tex_file.read_text(), tex_file.name))
    else:
        print("ERROR: provide --manuscript or --tex-file", file=sys.stderr)
        sys.exit(2)

    if not tex_sources:
        print("ERROR: no .tex files found", file=sys.stderr)
        sys.exit(2)

    # Extract assertions from all tex sources
    all_assertions: list[str] = []
    assertion_locations: dict[str, str] = {}
    for content, filename in tex_sources:
        file_assertions = extract_assertions(content)
        for a in file_assertions:
            all_assertions.append(a)
            assertion_locations[a[:100]] = filename

    print(f"Extracted {len(all_assertions)} assertions from {len(tex_sources)} .tex file(s)")
    print(f"Registered claims in graph: {len(claims)}")

    # Check 1: Unregistered claims (in manuscript but not in graph)
    unregistered: list[dict] = []
    for assertion in all_assertions:
        matched_id = find_registered_claim(assertion, claims)
        if matched_id is None:
            unregistered.append({
                "assertion": assertion,
                "location": assertion_locations.get(assertion[:100], "unknown"),
            })

    # Check 2: Dropped claims (in graph but not in manuscript)
    dropped: list[dict] = []
    for claim in claims:
        if claim.get("status") == "unsupported":
            continue  # already flagged by build_claim_graph.py
        if not claim_appears_in_manuscript(claim.get("text", ""), all_assertions):
            dropped.append({
                "claim_id": claim["id"],
                "claim_text": claim.get("text", ""),
                "confidence": claim.get("confidence", ""),
                "evidence_count": len(claim.get("evidence", [])),
            })

    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(unregistered, dropped, output_path)

    print(f"Unregistered claims: {len(unregistered)}")
    print(f"Dropped claims: {len(dropped)}")
    print(f"Report written to: {output_path}")

    if unregistered:
        print(
            f"\n[HARD BLOCK] {len(unregistered)} unregistered claim(s) in manuscript. "
            f"Add to claim-ledger.md with evidence or remove from manuscript.",
            file=sys.stderr,
        )
        sys.exit(1)

    if dropped:
        print(f"[WARNING] {len(dropped)} registered claim(s) absent from manuscript.")

    sys.exit(0)


if __name__ == "__main__":
    main()
