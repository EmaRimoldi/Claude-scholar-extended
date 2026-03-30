#!/usr/bin/env python3
"""
confidence_to_hedging.py — Flag manuscript claims whose prose tone is more assertive
than their registered confidence level.

Reads confidence_tracker.json (or claim_graph.json) for per-claim confidence values,
then scans the manuscript LaTeX for sentences that express those claims. Classifies
sentence tone as assertive, hedged, or cautious and flags mismatches where the prose
is stronger than the confidence warrants.

Called at Step 33 (/claim-source-align).

Usage:
    python scripts/confidence_to_hedging.py \\
        --claim-graph   $PROJECT_DIR/.epistemic/claim_graph.json \\
        --confidence    $PROJECT_DIR/.epistemic/confidence_tracker.json \\
        --manuscript    $PROJECT_DIR/manuscript/ \\
        --output        $PROJECT_DIR/claim-hedging-report.md

    # Run on a single .tex file:
    python scripts/confidence_to_hedging.py \\
        --claim-graph   $PROJECT_DIR/.epistemic/claim_graph.json \\
        --confidence    $PROJECT_DIR/.epistemic/confidence_tracker.json \\
        --tex-file      $PROJECT_DIR/manuscript/main.tex \\
        --output        $PROJECT_DIR/claim-hedging-report.md

Exit codes:
    0 — No CRITICAL mismatches (MAJOR or MINOR issues may exist but do not hard-block)
    1 — One or more CRITICAL mismatches found (assertive prose when confidence < 0.5)
    2 — Input file error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Confidence thresholds (must match build_claim_graph.py and spec)
# ---------------------------------------------------------------------------

ASSERTIVE_THRESHOLD = 0.80   # confidence >= 0.80 → assertive language appropriate
HEDGED_THRESHOLD = 0.50      # 0.50 <= confidence < 0.80 → hedged language appropriate
# confidence < 0.50 → cautious language required


# ---------------------------------------------------------------------------
# Linguistic tone classifiers
# ---------------------------------------------------------------------------

# Patterns that indicate assertive tone ("we show", "achieves", hard statements)
_ASSERTIVE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(we show|we prove|we demonstrate|we establish|we confirm)\b",
        r"\b(achieves|outperforms|surpasses|exceeds|is superior to|beats)\b",
        r"\b(our method|our approach|our model|our system)\s+\w+\s+(achieves|reaches|obtains)\b",
        r"\b(is the (first|only|best|state-of-the-art))\b",
        r"\b(definitively|clearly shows|unambiguously)\b",
        r"\b(proves that|demonstrates that|confirms that)\b",
    ]
]

# Patterns that indicate hedged tone ("suggest", "appear", "results indicate")
_HEDGED_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(suggest|suggests|suggested)\b",
        r"\b(indicate|indicates|indicated)\b",
        r"\b(appear|appears|seem|seems)\b",
        r"\b(results (show|suggest|indicate|imply))\b",
        r"\b(we observe|we find|we note)\b",
        r"\b(may|might|could)\s+(be|improve|help|allow)\b",
        r"\b(consistent with|in line with)\b",
    ]
]

# Patterns that indicate cautious / tentative tone
_CAUTIOUS_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(preliminary|tentative|exploratory)\b",
        r"\b(may indicate|might suggest|could potentially)\b",
        r"\b(we conjecture|we speculate|we hypothesize)\b",
        r"\b(trend|tendency)\b",
        r"\b(not conclusive|limited evidence|inconclusive)\b",
        r"\b(warrant(s)? further|requires? further)\b",
    ]
]


def classify_tone(sentence: str) -> str:
    """
    Classify a sentence's tone as 'assertive', 'hedged', or 'cautious'.
    Returns the strongest signal found; defaults to 'hedged' if ambiguous.
    """
    has_cautious = any(p.search(sentence) for p in _CAUTIOUS_PATTERNS)
    has_hedged = any(p.search(sentence) for p in _HEDGED_PATTERNS)
    has_assertive = any(p.search(sentence) for p in _ASSERTIVE_PATTERNS)

    if has_cautious and not has_assertive:
        return "cautious"
    if has_assertive and not has_cautious:
        return "assertive"
    if has_hedged:
        return "hedged"
    # No pattern matched — default to hedged (not escalating without evidence)
    return "hedged"


def expected_tone(confidence: float) -> str:
    """Map a confidence score to the expected prose tone per spec."""
    if confidence >= ASSERTIVE_THRESHOLD:
        return "assertive"
    if confidence >= HEDGED_THRESHOLD:
        return "hedged"
    return "cautious"


def mismatch_severity(expected: str, actual: str) -> str | None:
    """
    Return severity if actual tone is stronger than expected, else None.

    Tone ordering: cautious < hedged < assertive
    Mismatch only when actual is STRONGER than expected (overclaiming).
    """
    ordering = {"cautious": 0, "hedged": 1, "assertive": 2}
    if ordering[actual] > ordering[expected]:
        if expected == "cautious" and actual == "assertive":
            return "CRITICAL"
        return "MAJOR"
    return None


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def collect_tex_files(manuscript_dir: Path) -> list[Path]:
    """Collect all .tex files under manuscript_dir."""
    return sorted(manuscript_dir.rglob("*.tex"))


def extract_sentences(tex_source: str) -> list[str]:
    """
    Extract claim-bearing sentences from LaTeX source.

    Strips LaTeX commands conservatively to preserve readable text.
    Splits on sentence boundaries.
    """
    # Remove comments
    text = re.sub(r"%.*", "", tex_source)
    # Remove common LaTeX environments that don't contain prose claims
    for env in ("equation", "align", "figure", "table", "lstlisting", "verbatim",
                "algorithm", "algorithmic", "tikzpicture"):
        text = re.sub(
            rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}", "", text, flags=re.DOTALL
        )
    # Strip common LaTeX commands but keep their text arguments
    text = re.sub(r"\\(?:textbf|textit|emph|text|mathrm|mathbf)\{([^}]+)\}", r"\1", text)
    # Strip remaining backslash commands
    text = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?\{([^}]*)\}", r"\2", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    # Strip braces
    text = re.sub(r"[{}]", " ", text)
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split into sentences (naive but sufficient for tone detection)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Filter to claim-bearing sentences (contain "we", "our", "the method", result numbers)
    claim_indicators = re.compile(
        r"\b(we|our|the (method|model|approach|system|algorithm)|"
        r"achieves?|outperforms?|improves?|surpasses?|shows?|demonstrates?|"
        r"\d+\.?\d*\s*%|p\s*[<=>]|accuracy|precision|recall|F1|BLEU|ROUGE)\b",
        re.IGNORECASE,
    )
    return [s.strip() for s in sentences if len(s.strip()) > 20 and claim_indicators.search(s)]


# ---------------------------------------------------------------------------
# Claim matching
# ---------------------------------------------------------------------------

def find_matching_sentences(claim_text: str, sentences: list[str]) -> list[str]:
    """
    Find manuscript sentences that likely express a given claim.

    Strategy: extract key nouns and numbers from the claim, then find sentences
    that contain a majority of those key terms.
    """
    # Extract keywords: numbers, capitalized terms, method/task names
    keywords = re.findall(
        r"(?:\d+\.?\d*\s*%|\d+\.?\d+|[A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)*)",
        claim_text,
    )
    if not keywords:
        # Fall back to longest words
        keywords = sorted(claim_text.split(), key=len, reverse=True)[:4]

    if not keywords:
        return []

    matched = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        hits = sum(1 for kw in keywords if kw.lower() in sentence_lower)
        # Require at least 40% keyword overlap, minimum 1
        if hits >= max(1, len(keywords) * 0.4):
            matched.append(sentence)

    return matched


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run_check(
    claim_graph: dict,
    confidence_tracker: dict,
    all_sentences: list[str],
) -> list[dict]:
    """
    For each claim in the graph, find matching sentences and check tone alignment.

    Returns list of mismatch dicts.
    """
    mismatches = []

    claims = claim_graph.get("claims", [])

    for claim in claims:
        c_id = claim["id"]
        claim_text = claim.get("text", "")

        # Get confidence from tracker first; fall back to claim node
        tracker_entry = confidence_tracker.get(c_id, {})
        confidence = tracker_entry.get("confidence", claim.get("confidence", 0.6))

        exp_tone = expected_tone(confidence)
        matching = find_matching_sentences(claim_text, all_sentences)

        for sentence in matching:
            actual_tone = classify_tone(sentence)
            severity = mismatch_severity(exp_tone, actual_tone)
            if severity is not None:
                # Generate suggested revision
                suggestion = _suggest_revision(sentence, exp_tone)
                mismatches.append({
                    "claim_id": c_id,
                    "claim_text": claim_text[:120] + ("..." if len(claim_text) > 120 else ""),
                    "confidence": confidence,
                    "expected_tone": exp_tone,
                    "detected_tone": actual_tone,
                    "sentence": sentence[:300],
                    "severity": severity,
                    "suggested_revision": suggestion,
                })

    return mismatches


def _suggest_revision(sentence: str, expected_tone: str) -> str:
    """
    Produce a simple suggested revision by replacing assertive indicators
    with the appropriate tone markers.
    """
    if expected_tone == "cautious":
        s = re.sub(r"\b(we show|we demonstrate|we prove)\b", "preliminary results indicate", sentence, flags=re.IGNORECASE)
        s = re.sub(r"\b(achieves?|outperforms?|surpasses?)\b", "appears to achieve", s, flags=re.IGNORECASE)
        s = re.sub(r"\b(is superior to|is better than|beats)\b", "may outperform", s, flags=re.IGNORECASE)
    elif expected_tone == "hedged":
        s = re.sub(r"\b(we show|we prove)\b", "our results suggest", sentence, flags=re.IGNORECASE)
        s = re.sub(r"\b(we demonstrate)\b", "we observe that", s, flags=re.IGNORECASE)
        s = re.sub(r"\b(achieves?)\b", "appears to achieve", s, flags=re.IGNORECASE)
    else:
        s = sentence  # assertive is appropriate; no change needed

    return s if s != sentence else "[Revise: replace assertive language with appropriate hedging]"


def write_report(mismatches: list[dict], output_path: Path) -> None:
    """Write the claim-hedging-report.md file."""
    critical_count = sum(1 for m in mismatches if m["severity"] == "CRITICAL")
    major_count = sum(1 for m in mismatches if m["severity"] == "MAJOR")

    lines = [
        "# Claim-Hedging Alignment Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Total mismatches:** {len(mismatches)}  "
        f"(CRITICAL: {critical_count}, MAJOR: {major_count})",
        "",
    ]

    if not mismatches:
        lines += [
            "## Result: PASS",
            "",
            "All claim-bearing sentences in the manuscript use language consistent "
            "with the registered confidence levels. No overclaiming detected.",
        ]
    else:
        lines += [
            "## Result: " + ("BLOCK" if critical_count > 0 else "REVISE"),
            "",
        ]
        if critical_count > 0:
            lines += [
                "**BLOCK:** One or more sentences use assertive language for claims with "
                "confidence < 0.50. These claims must be in the Limitations section or "
                "reworded to cautious language before submission.",
                "",
            ]

        # Sort by severity: CRITICAL first
        sorted_mismatches = sorted(mismatches, key=lambda m: (0 if m["severity"] == "CRITICAL" else 1))

        for m in sorted_mismatches:
            lines += [
                f"---",
                "",
                f"### {m['claim_id']}: {m['claim_text']}",
                "",
                f"- **Confidence:** {m['confidence']:.2f}",
                f"- **Expected tone:** {m['expected_tone']}",
                f"- **Detected tone:** {m['detected_tone']}",
                f"- **Severity:** {m['severity']}",
                f"- **Manuscript sentence:**",
                f"  > {m['sentence']}",
                f"- **Suggested revision:**",
                f"  > {m['suggested_revision']}",
                "",
            ]

    lines += [
        "---",
        "",
        "## Confidence Level Reference",
        "",
        "| Confidence | Expected tone | Example phrases |",
        "|-----------|--------------|-----------------|",
        "| ≥ 0.80 | assertive | \"we show that\", \"achieves X%\" |",
        "| 0.50–0.79 | hedged | \"results suggest\", \"appears to\" |",
        "| < 0.50 | cautious | \"preliminary evidence\", \"we conjecture\" |",
    ]

    output_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check manuscript prose tone against registered claim confidence levels"
    )
    parser.add_argument("--claim-graph", required=True, help="Path to .epistemic/claim_graph.json")
    parser.add_argument("--confidence", default="", help="Path to .epistemic/confidence_tracker.json (optional; falls back to claim_graph.json values)")
    parser.add_argument("--manuscript", default="", help="Path to manuscript directory (scans all .tex files)")
    parser.add_argument("--tex-file", default="", help="Path to a single .tex file (alternative to --manuscript)")
    parser.add_argument("--output", required=True, help="Output path for claim-hedging-report.md")
    args = parser.parse_args()

    # Load claim graph
    claim_graph_path = Path(args.claim_graph)
    if not claim_graph_path.exists():
        print(f"ERROR: claim_graph.json not found: {claim_graph_path}", file=sys.stderr)
        print("Run: python scripts/build_claim_graph.py first", file=sys.stderr)
        sys.exit(2)
    claim_graph = json.loads(claim_graph_path.read_text())

    # Load confidence tracker (optional)
    confidence_tracker: dict = {}
    if args.confidence:
        ct_path = Path(args.confidence)
        if ct_path.exists():
            confidence_tracker = json.loads(ct_path.read_text())

    # Collect manuscript text
    tex_sources: list[str] = []
    if args.tex_file:
        tex_path = Path(args.tex_file)
        if not tex_path.exists():
            print(f"ERROR: tex file not found: {tex_path}", file=sys.stderr)
            sys.exit(2)
        tex_sources.append(tex_path.read_text())
    elif args.manuscript:
        manuscript_dir = Path(args.manuscript)
        if not manuscript_dir.exists():
            print(f"ERROR: manuscript directory not found: {manuscript_dir}", file=sys.stderr)
            sys.exit(2)
        for tex_file in collect_tex_files(manuscript_dir):
            tex_sources.append(tex_file.read_text())
    else:
        print("ERROR: provide --manuscript or --tex-file", file=sys.stderr)
        sys.exit(2)

    if not tex_sources:
        print("ERROR: no .tex files found in manuscript directory", file=sys.stderr)
        sys.exit(2)

    # Extract all claim-bearing sentences
    all_sentences: list[str] = []
    for source in tex_sources:
        all_sentences.extend(extract_sentences(source))

    print(f"Extracted {len(all_sentences)} claim-bearing sentences from manuscript")

    # Run check
    mismatches = run_check(claim_graph, confidence_tracker, all_sentences)

    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(mismatches, output_path)

    # Summary
    critical = sum(1 for m in mismatches if m["severity"] == "CRITICAL")
    major = sum(1 for m in mismatches if m["severity"] == "MAJOR")

    print(f"Hedging check complete. Mismatches: {len(mismatches)} (CRITICAL: {critical}, MAJOR: {major})")
    print(f"Report written to: {output_path}")

    if critical > 0:
        print(
            f"\n[HARD BLOCK] {critical} CRITICAL mismatch(es): assertive prose for claims "
            f"with confidence < 0.50. These must be moved to Limitations or reworded.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
