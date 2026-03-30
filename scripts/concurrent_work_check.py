#!/usr/bin/env python3
"""
concurrent_work_check.py — Step 36: Contribution-Term-Derived arXiv Query Generation.

Extracts contribution terms from the manuscript and novelty-reassessment.md,
generates targeted arXiv search queries, and compares against the existing
concurrent-work-report.md to identify what new searches need to be run.

Called by /recency-sweep sweep_id=final as the query generation step.

Usage:
    python scripts/concurrent_work_check.py \
        --novelty-reassessment $PROJECT_DIR/novelty-reassessment.md \
        --manuscript           $PROJECT_DIR/manuscript/ \
        --existing-report      $PROJECT_DIR/concurrent-work-report.md \
        --output-queries       $PROJECT_DIR/.cache/recency_sweeps/final_queries.json \
        --output-report-section $PROJECT_DIR/.cache/recency_sweeps/concurrent_delta.md

Exit codes:
    0 — Queries generated successfully
    1 — No contribution terms extracted (likely missing input files)
    2 — Input error
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Term extraction
# ---------------------------------------------------------------------------

def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def strip_latex(text: str) -> str:
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\(?:textbf|textit|emph|text)\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_contribution_terms_from_reassessment(text: str) -> dict[str, list[str]]:
    """
    Extract structured contribution terms from novelty-reassessment.md.
    Returns {category: [terms]}.
    """
    terms: dict[str, list[str]] = {
        "method_terms": [],
        "task_terms": [],
        "dataset_terms": [],
        "metric_terms": [],
        "contribution_statements": [],
    }

    # Contribution statement patterns
    contrib_pat = re.compile(
        r"(?:\*\*)?(?:[Cc]ontribution|[Cc]laim|[Ff]inding|[Rr]esult)[s]?(?:\*\*)?[:\s]+(.+?)(?:\n|$)",
        re.MULTILINE,
    )
    for m in contrib_pat.finditer(text):
        stmt = m.group(1).strip().strip("*")
        if len(stmt) > 10:
            terms["contribution_statements"].append(stmt)

    # Method terms: look for "we propose X" / "our X" / "X method"
    method_pat = re.compile(
        r"(?:we\s+propose|our\s+(?:proposed\s+)?|novel\s+|introduce\s+a?\s*)([A-Z][a-zA-Z]+(?:\s+[A-Za-z]+){0,3})",
        re.IGNORECASE,
    )
    for m in method_pat.finditer(text):
        candidate = m.group(1).strip()
        if len(candidate.split()) <= 4:
            terms["method_terms"].append(candidate)

    # Task/domain terms
    task_pat = re.compile(
        r"(?:for|on|applied\s+to|evaluating\s+on)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\s+(?:task|benchmark|dataset|corpus)",
        re.IGNORECASE,
    )
    for m in task_pat.finditer(text):
        terms["task_terms"].append(m.group(1).strip())

    # Dataset names (ALL-CAPS or proper noun + digits)
    dataset_pat = re.compile(
        r"\b([A-Z]{2,}(?:[-_][A-Z0-9]+)*|[A-Z][a-z]+[A-Z][a-zA-Z]*\d*)\b"
    )
    datasets = re.findall(dataset_pat, text)
    # Filter to likely dataset names (not common acronyms)
    _common_acronyms = {"ICLR", "ICML", "NeurIPS", "AAAI", "ACL", "EMNLP", "NAACL",
                        "AI", "ML", "NLP", "CV", "RL", "LLM", "GPT", "BERT"}
    terms["dataset_terms"] = [d for d in datasets if d not in _common_acronyms][:10]

    # Metric terms
    metric_pat = re.compile(
        r"\b(F1|BLEU|ROUGE|accuracy|AUC|mAP|NDCG|perplexity|MRR|recall|precision|"
        r"top-[1-5]|FLOP[Ss]?|MAE|MSE|RMSE|R²|R\^2)\b",
        re.IGNORECASE,
    )
    terms["metric_terms"] = list(set(re.findall(metric_pat, text)))[:8]

    return terms


def extract_contribution_terms_from_manuscript(manuscript_text: str) -> list[str]:
    """
    Extract contribution terms from manuscript abstract and introduction.
    Returns flat list of key terms/phrases.
    """
    plain = strip_latex(manuscript_text)

    # Focus on abstract if available
    abs_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", manuscript_text, re.DOTALL)
    if abs_match:
        plain = strip_latex(abs_match.group(1))

    terms: list[str] = []

    # Multi-word noun phrases (heuristic: adj* noun+)
    noun_phrase_pat = re.compile(
        r"\b(?:[A-Z][a-zA-Z]+\s+){1,3}[A-Z][a-zA-Z]+\b"
    )
    terms.extend(re.findall(noun_phrase_pat, plain))

    # "our X" patterns
    our_pat = re.compile(r"\bour\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\b", re.IGNORECASE)
    for m in our_pat.finditer(plain):
        terms.append(m.group(1).strip())

    return list(set(terms))[:20]


# ---------------------------------------------------------------------------
# Query generation
# ---------------------------------------------------------------------------

def generate_arxiv_queries(terms: dict[str, list[str]], flat_terms: list[str]) -> list[dict]:
    """
    Generate targeted arXiv search queries from contribution terms.
    Returns list of {query_string, category, rationale}.
    """
    queries: list[dict] = []

    # 1. Contribution statement queries (most targeted)
    for stmt in terms["contribution_statements"][:3]:
        # Extract 3-5 most distinctive words
        words = re.findall(r"\b[a-zA-Z]{4,}\b", stmt)
        stopwords = {"that", "with", "from", "this", "have", "been", "more", "than",
                     "which", "when", "also", "both", "such", "over", "into", "show",
                     "shows", "their", "using", "used", "paper", "work", "method"}
        keywords = [w.lower() for w in words if w.lower() not in stopwords][:5]
        if len(keywords) >= 3:
            queries.append({
                "query": " ".join(keywords),
                "category": "contribution_statement",
                "rationale": f"Derived from contribution statement: '{stmt[:80]}'",
                "sources": ["arxiv", "semantic_scholar"],
            })

    # 2. Method × task queries
    for method in terms["method_terms"][:3]:
        for task in terms["task_terms"][:2]:
            queries.append({
                "query": f"{method} {task}",
                "category": "method_task",
                "rationale": f"Method '{method}' applied to task '{task}'",
                "sources": ["arxiv"],
            })
        if not terms["task_terms"]:
            queries.append({
                "query": method,
                "category": "method_only",
                "rationale": f"Method term '{method}' — broad search",
                "sources": ["arxiv", "openreview"],
            })

    # 3. Dataset-specific queries
    for dataset in terms["dataset_terms"][:3]:
        queries.append({
            "query": f"{dataset} benchmark",
            "category": "dataset",
            "rationale": f"New papers using dataset '{dataset}'",
            "sources": ["arxiv", "papers_with_code"],
        })

    # 4. Flat term queries from manuscript
    for term in flat_terms[:5]:
        queries.append({
            "query": term.lower(),
            "category": "manuscript_term",
            "rationale": f"Key term from manuscript: '{term}'",
            "sources": ["arxiv"],
        })

    # 5. Recency-focused variants (add date suffix in LLM step)
    for query in queries[:3]:
        queries.append({
            "query": query["query"] + " 2024 2025",
            "category": "recency_" + query["category"],
            "rationale": query["rationale"] + " [recency-filtered]",
            "sources": ["arxiv"],
        })

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for q in queries:
        if q["query"] not in seen:
            seen.add(q["query"])
            unique.append(q)

    return unique


def load_existing_report(path: Path) -> set[str]:
    """
    Extract paper titles/IDs already in the concurrent-work-report.md.
    Returns set of normalized titles for dedup.
    """
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Extract paper titles from report (### Title lines)
    titles = re.findall(r"^###\s+(.+)", text, re.MULTILINE)
    return {t.lower().strip() for t in titles}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_queries_json(queries: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "query_count": len(queries),
        "queries": queries,
    }, indent=2))


def write_report_section(
    queries: list[dict],
    terms: dict[str, list[str]],
    output_path: Path,
    existing_titles: set[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Concurrent Work Check — Query Generation (Step 36)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).date()}",
        f"**Queries generated:** {len(queries)}",
        "",
        "## Extracted Contribution Terms",
        "",
        f"**Method terms:** {', '.join(terms['method_terms'][:5]) or '(none extracted)'}",
        f"**Task terms:** {', '.join(terms['task_terms'][:5]) or '(none extracted)'}",
        f"**Dataset terms:** {', '.join(terms['dataset_terms'][:5]) or '(none extracted)'}",
        f"**Metric terms:** {', '.join(terms['metric_terms'][:5]) or '(none extracted)'}",
        "",
        "## Generated Queries",
        "",
        "Run these queries on arXiv, OpenReview, and Papers-with-Code within 48 hours of submission.",
        "",
        "| Query | Category | Sources | Rationale |",
        "|-------|----------|---------|-----------|",
    ]
    for q in queries:
        sources = ", ".join(q["sources"])
        lines.append(
            f"| `{q['query']}` | {q['category']} | {sources} | {q['rationale'][:60]} |"
        )
    lines += [
        "",
        "## Papers Already in Concurrent-Work-Report",
        "",
        f"Existing report contains {len(existing_titles)} tracked paper(s). "
        "Newly found papers from the queries above should be compared against this list to identify truly new work.",
        "",
        "## Routing",
        "",
        "After running queries:",
        "- New `blocks_project` paper → escalate to human immediately (do not attempt autonomous repositioning)",
        "- New `requires_repositioning` paper → update related work section + positioning.md",
        "- `should_be_cited` paper → append to citation_ledger.json and related work",
    ]
    output_path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 36: Generate targeted arXiv queries from contribution terms"
    )
    parser.add_argument("--novelty-reassessment", required=True,
                        help="Path to novelty-reassessment.md")
    parser.add_argument("--manuscript", default="",
                        help="Path to manuscript/ directory or main.tex")
    parser.add_argument("--existing-report", default="",
                        help="Path to existing concurrent-work-report.md for dedup")
    parser.add_argument("--output-queries", required=True,
                        help="Output path for generated queries JSON")
    parser.add_argument("--output-report-section", default="",
                        help="Optional path for Markdown report section")
    args = parser.parse_args()

    reassessment_path = Path(args.novelty_reassessment)
    if not reassessment_path.exists():
        print(f"ERROR: novelty-reassessment.md not found: {reassessment_path}", file=sys.stderr)
        sys.exit(2)

    reassessment_text = load_text(reassessment_path)
    terms = extract_contribution_terms_from_reassessment(reassessment_text)

    # Also extract from manuscript if available
    flat_terms: list[str] = []
    if args.manuscript:
        ms_path = Path(args.manuscript)
        if ms_path.is_dir():
            tex_files = sorted(ms_path.rglob("*.tex"))
            manuscript_text = "\n".join(
                load_text(f) for f in tex_files[:5]
            )
        elif ms_path.is_file():
            manuscript_text = load_text(ms_path)
        else:
            manuscript_text = ""
        if manuscript_text:
            flat_terms = extract_contribution_terms_from_manuscript(manuscript_text)

    if not any(terms.values()) and not flat_terms:
        print(
            "WARNING: No contribution terms extracted. Check novelty-reassessment.md format.",
            file=sys.stderr,
        )
        sys.exit(1)

    queries = generate_arxiv_queries(terms, flat_terms)
    print(f"Generated {len(queries)} queries from contribution terms")

    existing_titles = load_existing_report(
        Path(args.existing_report) if args.existing_report else Path("/nonexistent")
    )

    write_queries_json(queries, Path(args.output_queries))
    print(f"Queries written to: {args.output_queries}")

    if args.output_report_section:
        write_report_section(queries, terms, Path(args.output_report_section), existing_titles)
        print(f"Report section written to: {args.output_report_section}")

    sys.exit(0)


if __name__ == "__main__":
    main()
