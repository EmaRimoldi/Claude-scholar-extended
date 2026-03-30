#!/usr/bin/env python3
"""
cross_section_check.py — Step 32: Cross-Section Coherence Check.

Extracts core claims from each section of the manuscript and verifies
bidirectional alignment. Runs 5 deterministic sub-checks.

Usage:
    python scripts/cross_section_check.py \
        --manuscript  $PROJECT_DIR/manuscript/ \
        --tex-file    $PROJECT_DIR/manuscript/main.tex \
        --output      $PROJECT_DIR/cross-section-report.md

    # Single file:
    python scripts/cross_section_check.py \
        --tex-file $PROJECT_DIR/manuscript/main.tex \
        --output   $PROJECT_DIR/cross-section-report.md

Exit codes:
    0 — All 5 sub-checks pass
    1 — One or more sub-checks FAIL (hard block on Step 33)
    2 — Input error
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# LaTeX section extraction
# ---------------------------------------------------------------------------

def strip_latex_commands(text: str) -> str:
    """Remove common LaTeX commands, leaving readable text."""
    # Remove comments
    text = re.sub(r"%.*", "", text)
    # Remove environments (figure, table, equation, etc.)
    text = re.sub(
        r"\\begin\{(?:figure|table|align|equation|tabular)[^}]*\}.*?\\end\{[^}]+\}",
        " ",
        text,
        flags=re.DOTALL,
    )
    # Expand common text commands
    text = re.sub(r"\\(?:textbf|textit|emph|text|mbox|hbox)\{([^}]+)\}", r"\1", text)
    # Remove remaining commands with arguments
    text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)
    # Remove remaining commands without arguments
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    # Remove remaining braces
    text = re.sub(r"[{}]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_section_text(full_text: str, section_name: str) -> str:
    """
    Extract text under a LaTeX section/subsection heading.
    section_name is a regex pattern (e.g., 'abstract', 'conclusion').
    """
    # Try \begin{abstract}...\end{abstract} first
    if section_name == "abstract":
        m = re.search(
            r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
            full_text,
            re.DOTALL | re.IGNORECASE,
        )
        if m:
            return strip_latex_commands(m.group(1))

    # Try \section or \section*
    pattern = re.compile(
        rf"\\section\*?\{{{section_name}[^}}]*\}}(.*?)(?=\\section|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(full_text)
    if m:
        return strip_latex_commands(m.group(1))

    # Also try case-insensitive section heading
    pattern2 = re.compile(
        rf"\\(?:section|subsection)\*?\{{[^}}]*{section_name}[^}}]*\}}(.*?)(?=\\(?:section|subsection)|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern2.search(full_text)
    if m:
        return strip_latex_commands(m.group(1))

    return ""


def collect_tex_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix == ".tex":
        return [path]
    # Follow \input and \include at a shallow level
    files = sorted(path.rglob("*.tex"))
    return files


def load_full_tex(tex_files: list[Path]) -> str:
    """Concatenate all tex files into one string."""
    parts = []
    for f in tex_files:
        try:
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Sentence / claim extraction
# ---------------------------------------------------------------------------

def extract_sentences(text: str, min_words: int = 5) -> list[str]:
    """Split text into sentences (rough heuristic)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.split()) >= min_words]


def extract_claims(text: str) -> list[str]:
    """
    Extract claim-bearing sentences: those with assertive language.
    Filters out purely descriptive/transitional sentences.
    """
    claim_patterns = re.compile(
        r"\bwe\s+(?:show|demonstrate|prove|propose|find|present|introduce|achieve|outperform|"
        r"improve|observe|confirm|establish|report|argue|claim|note)\b|"
        r"\bour\s+(?:method|approach|model|system|results?|experiments?|analysis)\b|"
        r"\bthis\s+(?:paper|work|study)\b|\bsignificantly\b|\bsubstantially\b|"
        r"\bnovel\b|\bstate.of.the.art\b|\bbetter\s+than\b",
        re.IGNORECASE,
    )
    return [s for s in extract_sentences(text) if claim_patterns.search(s)]


def extract_research_questions(intro_text: str) -> list[str]:
    """Extract research question statements from introduction."""
    rq_patterns = re.compile(
        r"\bRQ\d+\b|research question|how\s+(?:does|can|do)|why\s+(?:does|do)|"
        r"what\s+(?:is|are|effect|impact)|whether|investigate[sd]?\b|examine[sd]?\b|"
        r"address[ed]?\b.*\bproblem",
        re.IGNORECASE,
    )
    return [s for s in extract_sentences(intro_text) if rq_patterns.search(s)]


def normalize_token_set(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "we", "our", "this", "that",
        "in", "on", "at", "to", "of", "for", "and", "or", "but", "with", "by",
        "from", "it", "its", "be", "as", "not", "have", "has", "can", "do",
    }
    return {w for w in text.split() if w not in stopwords and len(w) > 2}


def semantic_overlap(a: str, b: str) -> float:
    ta = normalize_token_set(a)
    tb = normalize_token_set(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Sub-checks
# ---------------------------------------------------------------------------

def check1_abstract_conclusion(abstract: str, conclusion: str) -> dict:
    """
    Sub-check 1: Every major claim in the abstract has a corresponding statement
    in the conclusion.
    """
    name = "Abstract ↔ Conclusion Alignment"
    if not abstract:
        return {"name": name, "result": "SKIP", "issues": [], "note": "No abstract section found."}
    if not conclusion:
        return {"name": name, "result": "SKIP", "issues": [], "note": "No conclusion section found."}

    abstract_claims = extract_claims(abstract)
    conclusion_text_norm = normalize_token_set(conclusion)

    issues = []
    for claim in abstract_claims:
        if semantic_overlap(claim, conclusion) < 0.20:
            issues.append(
                f"Abstract claim not reflected in conclusion: "
                f'"{claim[:120]}"'
            )

    return {
        "name": name,
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "note": (
            f"Checked {len(abstract_claims)} abstract claim(s) against conclusion. "
            f"{len(issues)} not covered."
        ),
    }


def check2_intro_questions_vs_results(intro: str, results: str, discussion: str) -> dict:
    """
    Sub-check 2: Research questions posed in introduction are addressed in
    results or discussion.
    """
    name = "Introduction Questions → Results Coverage"
    if not intro:
        return {"name": name, "result": "SKIP", "issues": [], "note": "No introduction section found."}

    rqs = extract_research_questions(intro)
    if not rqs:
        return {
            "name": name,
            "result": "PASS",
            "issues": [],
            "note": "No explicit research questions detected in introduction.",
        }

    results_discussion = (results + " " + discussion).lower()
    issues = []
    for rq in rqs:
        if semantic_overlap(rq, results_discussion) < 0.20:
            issues.append(
                f"Research question not answered in results/discussion: "
                f'"{rq[:120]}"'
            )

    return {
        "name": name,
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "note": (
            f"Checked {len(rqs)} research question(s). "
            f"{len(issues)} not answered."
        ),
    }


def check3_discussion_scope(results: str, discussion: str) -> dict:
    """
    Sub-check 3: Discussion does not introduce new empirical claims not
    grounded in the results section.
    """
    name = "Discussion Scope (No New Claims)"
    if not discussion:
        return {"name": name, "result": "SKIP", "issues": [], "note": "No discussion section found."}

    discussion_claims = extract_claims(discussion)
    issues = []

    for claim in discussion_claims:
        # A claim that references specific numbers/percentages should be in results
        has_numbers = bool(re.search(r"\d+\.?\d*\s*(?:%|points?|pp|×)", claim))
        if has_numbers and semantic_overlap(claim, results) < 0.25:
            issues.append(
                f"Discussion introduces numerical claim not found in results section: "
                f'"{claim[:120]}"'
            )

    return {
        "name": name,
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "note": (
            f"Checked {len(discussion_claims)} discussion claim(s) for scope violations. "
            f"{len(issues)} potential new claims."
        ),
    }


def check4_terminology_consistency(full_text: str) -> dict:
    """
    Sub-check 4: Key technical terms (model name, method name, dataset name)
    are used consistently throughout.
    """
    name = "Terminology Consistency"

    # Find candidate key terms (multi-word capitalized or acronym patterns)
    term_candidates = re.findall(
        r"\b([A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)+|[A-Z]{2,6}(?:-[a-zA-Z0-9]+)?)\b",
        full_text,
    )
    term_counts: dict[str, int] = {}
    for t in term_candidates:
        term_counts[t] = term_counts.get(t, 0) + 1

    # Find high-frequency terms (used 3+ times)
    key_terms = {t for t, c in term_counts.items() if c >= 3}

    # Check for variant spellings (simple heuristic: same lowercase, different case)
    lower_to_variants: dict[str, set[str]] = {}
    for t in key_terms:
        lower_to_variants.setdefault(t.lower(), set()).add(t)

    issues = []
    for lower, variants in lower_to_variants.items():
        if len(variants) > 1:
            issues.append(
                f"Term '{lower}' appears in {len(variants)} different forms: "
                + ", ".join(f'"{v}"' for v in sorted(variants))
            )

    # Check for hyphenation inconsistency
    # e.g., "pre-training" vs "pretraining"
    hyphen_check: dict[str, set[str]] = {}
    for t in re.findall(r"\b[a-z]+-[a-z]+\b", full_text.lower()):
        unhyphenated = t.replace("-", "")
        hyphen_check.setdefault(unhyphenated, set()).add(t)

    for base, variants in hyphen_check.items():
        if len(variants) > 1 and base in full_text.lower():
            variants.add(base)
            if len(variants) > 1:
                issues.append(
                    f"Inconsistent hyphenation: " + ", ".join(f'"{v}"' for v in sorted(variants))
                )

    return {
        "name": name,
        "result": "PASS" if not issues else "FAIL",
        "issues": issues[:10],  # Cap at 10 to avoid noise
        "note": (
            f"Checked {len(key_terms)} key terms for consistency. "
            f"{len(issues)} inconsistency(ies) found."
        ),
    }


def check5_reference_integrity(full_text: str) -> dict:
    """
    Sub-check 5: Every \\ref{X} has a matching \\label{X}.
    Every figure/table is referenced in the text.
    """
    name = "Figure/Table Reference Integrity"

    # Collect all \label{X}
    labels = set(re.findall(r"\\label\{([^}]+)\}", full_text))
    # Collect all \ref{X} and \eqref{X}
    refs = set(re.findall(r"\\(?:ref|eqref|autoref|cref|Cref)\{([^}]+)\}", full_text))

    # Broken refs: referenced but no label
    broken_refs = refs - labels

    # Orphan labels: label exists but never referenced
    # Only flag figure/table labels as orphans (eq/sec labels are often intentionally unlabeled)
    fig_table_labels = {
        l for l in labels
        if re.match(r"(?:fig|tab|table|figure|eq|sec)\b", l, re.IGNORECASE)
    }
    orphan_labels = fig_table_labels - refs

    issues = []
    for ref in sorted(broken_refs)[:10]:
        issues.append(f"Broken reference: \\ref{{{ref}}} — no matching \\label{{{ref}}}")
    for label in sorted(orphan_labels)[:10]:
        issues.append(f"Orphan label: \\label{{{label}}} — never referenced in text")

    return {
        "name": name,
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "note": (
            f"Labels: {len(labels)}, Refs: {len(refs)}. "
            f"Broken refs: {len(broken_refs)}, Orphan fig/tab labels: {len(orphan_labels)}."
        ),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(
    checks: list[dict],
    output_path: Path,
    tex_files: list[Path],
) -> None:
    failures = [c for c in checks if c["result"] == "FAIL"]
    passes = [c for c in checks if c["result"] == "PASS"]
    skips = [c for c in checks if c["result"] == "SKIP"]

    overall = "PASS" if not failures else "FAIL"

    lines = [
        "# Cross-Section Consistency Report (Step 32)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Files checked:** {', '.join(str(f) for f in tex_files[:5])}",
        "",
        f"## Overall Result: {overall}",
        "",
        f"- Passed: {len(passes)}  |  Failed: {len(failures)}  |  Skipped: {len(skips)}",
        "",
        "| Sub-check | Result | Notes |",
        "|-----------|--------|-------|",
    ]
    for c in checks:
        icon = "✓" if c["result"] == "PASS" else ("✗" if c["result"] == "FAIL" else "—")
        lines.append(
            f"| {c['name']} | {icon} {c['result']} | {c['note'][:80]} |"
        )
    lines.append("")

    if failures:
        lines += [
            "## Failures (Hard Block)",
            "",
            "These issues must be resolved before Step 33 (Claim-Source Alignment).",
            "",
        ]
        for c in failures:
            lines += [
                f"### {c['name']}",
                "",
                f"**Note:** {c['note']}",
                "",
            ]
            for issue in c["issues"]:
                lines.append(f"- {issue}")
            lines.append("")

    if passes:
        lines += ["## Passing Sub-checks", ""]
        for c in passes:
            lines.append(f"- **{c['name']}**: {c['note']}")
        lines.append("")

    if skips:
        lines += ["## Skipped Sub-checks", ""]
        for c in skips:
            lines.append(f"- **{c['name']}**: {c['note']}")
        lines.append("")

    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 32: Cross-section coherence check on manuscript"
    )
    parser.add_argument("--manuscript", default="", help="Path to manuscript directory")
    parser.add_argument("--tex-file", default="", help="Path to single .tex file")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    tex_files: list[Path] = []
    if args.tex_file:
        p = Path(args.tex_file)
        if not p.exists():
            print(f"ERROR: tex file not found: {p}", file=sys.stderr)
            sys.exit(2)
        tex_files = [p]
    elif args.manuscript:
        manuscript_dir = Path(args.manuscript)
        if not manuscript_dir.exists():
            print(f"ERROR: manuscript directory not found: {manuscript_dir}", file=sys.stderr)
            sys.exit(2)
        tex_files = collect_tex_files(manuscript_dir)
    else:
        print("ERROR: provide --manuscript or --tex-file", file=sys.stderr)
        sys.exit(2)

    if not tex_files:
        print("ERROR: no .tex files found", file=sys.stderr)
        sys.exit(2)

    full_text = load_full_tex(tex_files)
    print(f"Loaded {len(tex_files)} .tex file(s), {len(full_text)} characters total")

    # Extract sections
    abstract = extract_section_text(full_text, "abstract")
    intro = extract_section_text(full_text, "introduction|intro")
    results = extract_section_text(full_text, "result|experiment")
    discussion = extract_section_text(full_text, "discussion|analysis|ablat")
    conclusion = extract_section_text(full_text, "conclusion")

    print(f"Sections found — Abstract: {bool(abstract)}, Intro: {bool(intro)}, "
          f"Results: {bool(results)}, Discussion: {bool(discussion)}, "
          f"Conclusion: {bool(conclusion)}")

    # Run all 5 sub-checks
    checks = [
        check1_abstract_conclusion(abstract, conclusion),
        check2_intro_questions_vs_results(intro, results, discussion),
        check3_discussion_scope(results, discussion),
        check4_terminology_consistency(full_text),
        check5_reference_integrity(full_text),
    ]

    failures = [c for c in checks if c["result"] == "FAIL"]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(checks, output_path, tex_files)

    print(f"Sub-checks passed: {len([c for c in checks if c['result'] == 'PASS'])}/5")
    print(f"Report written to: {output_path}")

    if failures:
        print(
            f"\n[HARD BLOCK] {len(failures)} sub-check(s) failed. "
            f"Resolve before Step 33.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
