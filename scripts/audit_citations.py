#!/usr/bin/env python3
"""
audit_citations.py — Cross-reference LaTeX \\cite{} commands against
citation_ledger.json and claim_graph.json.

Three checks:
  1. Hallucinated citations: \\cite{key} appears in manuscript but key is absent
     from citation_ledger.json. Either the citation was hallucinated by the LLM
     or manually added without provenance tracking.
  2. Unused HIGH-relevance citations: citation_ledger.json marks a paper as
     relevance: HIGH but it is never cited in the manuscript. The related work
     section may be ignoring important prior work.
  3. Misaligned claim-citation links: the manuscript cites paper X in a sentence
     that expresses claim Y, but claim_graph.json does not link paper X to claim Y.

Called at Step 31 (/produce-manuscript), citation audit sub-step.

Usage:
    python scripts/audit_citations.py \\
        --manuscript     $PROJECT_DIR/manuscript/ \\
        --citation-ledger $PROJECT_DIR/.epistemic/citation_ledger.json \\
        --claim-graph    $PROJECT_DIR/.epistemic/claim_graph.json \\
        --output         $PROJECT_DIR/citation-audit-report.md

    # Single file mode:
    python scripts/audit_citations.py \\
        --tex-file       $PROJECT_DIR/manuscript/main.tex \\
        --citation-ledger $PROJECT_DIR/.epistemic/citation_ledger.json \\
        --claim-graph    $PROJECT_DIR/.epistemic/claim_graph.json \\
        --output         $PROJECT_DIR/citation-audit-report.md

Exit codes:
    0 — No hallucinated citations or misaligned claim-citation links
    1 — Hallucinated citations or misaligned links found — hard block
    2 — Input file error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# LaTeX citation extraction
# ---------------------------------------------------------------------------

def extract_citations_from_tex(tex_source: str) -> list[tuple[str, str]]:
    """
    Extract all \\cite{...} commands from LaTeX source.

    Returns list of (cite_key, surrounding_sentence) tuples.
    Handles \\cite, \\citep, \\citet, \\citealt, \\citeauthor, \\citeyear,
    \\citep*, \\citet*, and \\citenum. Handles multi-key: \\cite{key1,key2}.
    """
    # Remove comments
    text = re.sub(r"%.*", "", tex_source)

    results: list[tuple[str, str]] = []

    # Find all cite commands with their surrounding context
    cite_pattern = re.compile(
        r"\\cite(?:[tp]?\*?|alt|author|year|num)?\{([^}]+)\}",
        re.IGNORECASE,
    )

    for m in cite_pattern.finditer(text):
        keys_raw = m.group(1)
        # Extract surrounding sentence (±200 chars)
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 200)
        context = text[start:end]
        # Clean context to readable text
        context = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?\{([^}]*)\}", r"\2", context)
        context = re.sub(r"\\[a-zA-Z]+\*?", " ", context)
        context = re.sub(r"[{}]", " ", context)
        context = re.sub(r"\s+", " ", context).strip()

        for key in keys_raw.split(","):
            key = key.strip()
            if key:
                results.append((key, context[:300]))

    return results


def collect_tex_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.tex"))


# ---------------------------------------------------------------------------
# Citation ledger loading
# ---------------------------------------------------------------------------

def load_citation_ledger(path: Path) -> dict[str, dict]:
    """
    Load citation_ledger.json and return a dict keyed by cite_key.
    Handles both list format and dict format.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}

    if isinstance(data, list):
        return {entry.get("cite_key", ""): entry for entry in data if "cite_key" in entry}
    if isinstance(data, dict):
        return data
    return {}


def load_claim_graph(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------

def check_hallucinated(
    citations: list[tuple[str, str]],
    ledger: dict[str, dict],
) -> list[dict]:
    """
    Check 1: Find cite keys that appear in manuscript but not in ledger.
    """
    hallucinated = []
    seen: set[str] = set()
    for key, context in citations:
        if key in seen:
            continue
        seen.add(key)
        if key not in ledger:
            hallucinated.append({"cite_key": key, "context": context})
    return hallucinated


def check_unused_high_relevance(
    cited_keys: set[str],
    ledger: dict[str, dict],
) -> list[dict]:
    """
    Check 2: Find ledger entries with relevance: HIGH that are never cited.
    """
    unused = []
    for key, entry in ledger.items():
        relevance = entry.get("relevance", "").upper()
        prior_art_threat = entry.get("prior_art_threat", "").upper()
        if key not in cited_keys and relevance == "HIGH":
            unused.append({
                "cite_key": key,
                "title": entry.get("title", ""),
                "relevance": relevance,
                "prior_art_threat": prior_art_threat,
                "audit_status": entry.get("audit_status", "unchecked"),
            })
    return unused


def check_misaligned_links(
    citations: list[tuple[str, str]],
    ledger: dict[str, dict],
    claim_graph: dict,
) -> list[dict]:
    """
    Check 3: For each citation in context, find if the context expresses a claim
    that the citation is NOT linked to in the graph.

    Strategy: extract claim IDs from context heuristically (by matching claim text
    keywords), then verify the cite_key appears in that claim's citations list.
    """
    claims = claim_graph.get("claims", [])
    if not claims:
        return []

    misaligned = []
    seen: set[tuple[str, str]] = set()

    for key, context in citations:
        if key not in ledger:
            continue  # already reported as hallucinated

        # Find which registered claims this context might be expressing
        expressed_claims = []
        for claim in claims:
            claim_text = claim.get("text", "")
            if _context_matches_claim(context, claim_text):
                expressed_claims.append(claim)

        for claim in expressed_claims:
            pair = (key, claim["id"])
            if pair in seen:
                continue
            seen.add(pair)

            # Check if this cite_key is linked to this claim in the graph
            claim_citations = claim.get("citations", [])
            ledger_entry = ledger.get(key, {})
            ledger_claims_supported = ledger_entry.get("claims_supported", [])

            if key not in claim_citations and claim["id"] not in ledger_claims_supported:
                misaligned.append({
                    "cite_key": key,
                    "claim_id": claim["id"],
                    "claim_text": claim.get("text", "")[:120],
                    "context": context[:200],
                    "issue": (
                        f"'{key}' is cited in a sentence expressing claim {claim['id']}, "
                        f"but neither claim_graph.json nor citation_ledger.json links "
                        f"this citation to this claim."
                    ),
                })

    return misaligned


def _context_matches_claim(context: str, claim_text: str) -> bool:
    """Lightweight keyword overlap check between a citation context and a claim."""
    # Extract numeric values and multi-word capitalised terms
    claim_kws = re.findall(
        r"\d+\.?\d*\s*(?:%|points?|pp)?|[A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)*",
        claim_text,
    )
    if not claim_kws:
        return False
    context_lower = context.lower()
    hits = sum(1 for kw in claim_kws if kw.lower() in context_lower)
    return hits >= max(1, len(claim_kws) * 0.35)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def write_report(
    hallucinated: list[dict],
    unused_high: list[dict],
    misaligned: list[dict],
    total_cited: int,
    output_path: Path,
) -> None:
    block = bool(hallucinated or misaligned)
    result = "BLOCK" if block else ("WARN" if unused_high else "PASS")

    lines = [
        "# Citation Audit Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Total distinct cite keys in manuscript:** {total_cited}",
        f"**Hallucinated citations:** {len(hallucinated)}",
        f"**Unused HIGH-relevance citations:** {len(unused_high)}",
        f"**Misaligned claim-citation links:** {len(misaligned)}",
        "",
        f"## Result: {result}",
        "",
    ]

    if result == "PASS":
        lines += [
            "All citations are present in the ledger, all HIGH-relevance papers are cited, "
            "and all claim-citation links are consistent.",
        ]

    if hallucinated:
        lines += [
            "",
            "## Hallucinated / Untracked Citations",
            "",
            "These cite keys appear in the manuscript but have no entry in `citation_ledger.json`. "
            "Either the LLM generated them without basis or they were manually added without "
            "provenance tracking. Each must be verified and added to the ledger.",
            "",
        ]
        for item in hallucinated:
            lines += [
                f"### `{item['cite_key']}`",
                f"- **Context:** `{item['context'][:200]}`",
                f"- **Action required:** Verify paper exists and add to citation_ledger.json with `audit_status: verified`, or remove the citation.",
                "",
            ]

    if unused_high:
        lines += [
            "",
            "## Unused HIGH-Relevance Citations",
            "",
            "These papers were marked `relevance: HIGH` in the citation ledger but are never "
            "cited in the manuscript. A reviewer familiar with this literature may notice their "
            "absence.",
            "",
        ]
        for item in unused_high:
            threat_note = f" **Prior art threat: {item['prior_art_threat']}**" if item["prior_art_threat"] in ("HIGH", "MEDIUM") else ""
            lines += [
                f"- `{item['cite_key']}`: {item['title'][:80]}{threat_note}",
            ]
        lines.append("")

    if misaligned:
        lines += [
            "",
            "## Misaligned Claim-Citation Links",
            "",
            "These citations are used to support claims they are not linked to in the claim graph. "
            "Either the citation ledger needs updating, or the citation is being used incorrectly.",
            "",
        ]
        for item in misaligned:
            lines += [
                f"### `{item['cite_key']}` cited for `{item['claim_id']}`",
                f"- **Claim:** {item['claim_text']}",
                f"- **Context:** `{item['context'][:200]}`",
                f"- **Issue:** {item['issue']}",
                f"- **Action required:** Verify that `{item['cite_key']}` actually supports "
                f"`{item['claim_id']}` and add the link to citation_ledger.json, or replace "
                f"with the correct citation.",
                "",
            ]

    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit manuscript citations against citation_ledger.json and claim_graph.json"
    )
    parser.add_argument("--manuscript", default="", help="Path to manuscript directory")
    parser.add_argument("--tex-file", default="", help="Path to single .tex file")
    parser.add_argument("--citation-ledger", required=True, help="Path to .epistemic/citation_ledger.json")
    parser.add_argument("--claim-graph", default="", help="Path to .epistemic/claim_graph.json (for link alignment check)")
    parser.add_argument("--output", required=True, help="Output path for citation-audit-report.md")
    args = parser.parse_args()

    # Collect tex sources
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

    # Extract all citations
    all_citations: list[tuple[str, str]] = []
    for tex_file in tex_files:
        all_citations.extend(extract_citations_from_tex(tex_file.read_text()))

    cited_keys = {key for key, _ in all_citations}
    print(f"Found {len(all_citations)} citation instances ({len(cited_keys)} distinct keys) "
          f"across {len(tex_files)} .tex file(s)")

    # Load ledger and graph
    ledger = load_citation_ledger(Path(args.citation_ledger))
    claim_graph = load_claim_graph(Path(args.claim_graph)) if args.claim_graph else {}

    if not ledger:
        print("WARNING: citation_ledger.json is empty or missing. "
              "All citations will be flagged as hallucinated.", file=sys.stderr)

    # Run checks
    hallucinated = check_hallucinated(all_citations, ledger)
    unused_high = check_unused_high_relevance(cited_keys, ledger)
    misaligned = check_misaligned_links(all_citations, ledger, claim_graph) if claim_graph else []

    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(hallucinated, unused_high, misaligned, len(cited_keys), output_path)

    print(f"Hallucinated: {len(hallucinated)}  "
          f"Unused HIGH: {len(unused_high)}  "
          f"Misaligned: {len(misaligned)}")
    print(f"Report written to: {output_path}")

    if hallucinated or misaligned:
        count = len(hallucinated) + len(misaligned)
        print(
            f"\n[HARD BLOCK] {count} citation integrity issue(s). "
            f"Resolve before proceeding to submission.",
            file=sys.stderr,
        )
        sys.exit(1)

    if unused_high:
        high_threat = [u for u in unused_high if u["prior_art_threat"] in ("HIGH", "MEDIUM")]
        if high_threat:
            print(
                f"[WARNING] {len(high_threat)} unused citation(s) with HIGH/MEDIUM prior art threat — "
                f"reviewers may notice their absence."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
