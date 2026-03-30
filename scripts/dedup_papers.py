#!/usr/bin/env python3
"""
dedup_papers.py — De-duplicate papers across multi-pass search results.

Usage:
    python scripts/dedup_papers.py \
        --new-results path/to/new_results.json \
        --existing path/to/citation_ledger.json \
        --output path/to/deduped_output.json

The script identifies duplicates by:
  1. Exact DOI match
  2. arXiv ID match
  3. Title token overlap (ratio > 0.85, after normalization)
  4. Author + year + first-word-of-title exact match

For duplicates: the existing ledger entry is preserved. The new result's
fields are merged if they add information (e.g., new claim_overlap_level,
found_via source). Duplicates are logged but not added as new entries.

Output JSON:
  {
    "new_papers": [...],       # Papers not in existing ledger
    "duplicates": [...],       # Papers already in ledger (with merge info)
    "updated_entries": [...]   # Ledger keys that were updated with new fields
  }
"""

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_title(title: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def token_overlap_ratio(title_a: str, title_b: str) -> float:
    """Compute Jaccard similarity on title word sets."""
    a = set(normalize_title(title_a).split())
    b = set(normalize_title(title_b).split())
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def extract_arxiv_id(url_or_id: str) -> str | None:
    """Extract arXiv ID (YYMM.NNNNN) from URL or raw ID string."""
    if not url_or_id:
        return None
    pattern = r"(\d{4}\.\d{4,5})(v\d+)?"
    m = re.search(pattern, url_or_id)
    return m.group(1) if m else None


def author_year_firstword_key(paper: dict) -> str | None:
    """
    Build a dedup key from first author last name + year + first content word of title.
    e.g., "vaswani_2017_attention"
    Returns None if any component is missing.
    """
    # Extract first author last name
    authors = paper.get("authors") or paper.get("author") or ""
    if isinstance(authors, list):
        first_author = authors[0] if authors else ""
    else:
        first_author = str(authors).split(",")[0].strip()
    # Take last name (last token before comma or last word)
    last_name = first_author.split()[-1].lower() if first_author else ""
    last_name = re.sub(r"[^\w]", "", last_name)

    year = str(paper.get("year") or paper.get("published_year") or "").strip()[:4]
    if not re.match(r"\d{4}", year):
        year = ""

    title = paper.get("title") or ""
    # First content word of title (skip stopwords/articles)
    _stop = {"a", "an", "the", "on", "in", "of", "for", "with", "and", "or", "is", "are"}
    words = [w for w in normalize_title(title).split() if w not in _stop and len(w) > 2]
    first_word = words[0] if words else ""

    if last_name and year and first_word:
        return f"{last_name}_{year}_{first_word}"
    return None


def build_ledger_index(ledger: dict) -> dict:
    """Build fast-lookup indices from citation ledger."""
    by_doi: dict[str, str] = {}
    by_arxiv: dict[str, str] = {}
    by_title: list[tuple[str, str]] = []  # (normalized_title, cite_key)
    by_author_year_firstword: dict[str, str] = {}

    for cite_key, entry in ledger.items():
        doi = (entry.get("doi") or "").strip().lower()
        if doi:
            by_doi[doi] = cite_key

        arxiv_id = extract_arxiv_id(
            entry.get("arxiv_id") or entry.get("source_url") or ""
        )
        if arxiv_id:
            by_arxiv[arxiv_id] = cite_key

        title = entry.get("title") or ""
        if title:
            by_title.append((normalize_title(title), cite_key))

        ayfk = author_year_firstword_key(entry)
        if ayfk:
            by_author_year_firstword[ayfk] = cite_key

    return {
        "doi": by_doi,
        "arxiv": by_arxiv,
        "titles": by_title,
        "author_year_firstword": by_author_year_firstword,
    }


def find_duplicate(
    paper: dict, index: dict, threshold: float = 0.85
) -> str | None:
    """Return the cite_key of a duplicate, or None if no duplicate found."""
    # 1. DOI match
    doi = (paper.get("doi") or "").strip().lower()
    if doi and doi in index["doi"]:
        return index["doi"][doi]

    # 2. arXiv ID match
    arxiv_id = extract_arxiv_id(
        paper.get("arxiv_id") or paper.get("source_url") or ""
    )
    if arxiv_id and arxiv_id in index["arxiv"]:
        return index["arxiv"][arxiv_id]

    # 3. Title token overlap
    title = paper.get("title") or ""
    if title:
        norm_new = normalize_title(title)
        for norm_existing, cite_key in index["titles"]:
            if token_overlap_ratio(norm_new, norm_existing) >= threshold:
                return cite_key

    # 4. Author + year + first-word-of-title exact match
    ayfk = author_year_firstword_key(paper)
    if ayfk and ayfk in index["author_year_firstword"]:
        return index["author_year_firstword"][ayfk]

    return None


def merge_fields(existing: dict, new_paper: dict) -> dict:
    """
    Merge additive fields from new_paper into existing ledger entry.
    Never overwrites verified fields; only adds missing or list-extending info.
    Returns a dict of fields that were actually changed.
    """
    changes: dict = {}

    # Add new found_via sources
    existing_sources = set(existing.get("found_via", []))
    new_source = new_paper.get("found_via")
    if new_source and new_source not in existing_sources:
        existing_sources.add(new_source)
        existing["found_via"] = sorted(existing_sources)
        changes["found_via"] = existing["found_via"]

    # Update claim_overlap_level if new value is stronger
    overlap_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, None: 0, "": 0}
    existing_overlap = existing.get("claim_overlap_level") or ""
    new_overlap = new_paper.get("claim_overlap_level") or ""
    if overlap_rank.get(new_overlap, 0) > overlap_rank.get(existing_overlap, 0):
        existing["claim_overlap_level"] = new_overlap
        changes["claim_overlap_level"] = new_overlap

    # Append new claims_supported_text entries
    existing_texts = set(existing.get("claims_supported_text", []))
    for text in new_paper.get("claims_supported_text", []):
        if text not in existing_texts:
            existing_texts.add(text)
            changes.setdefault("claims_supported_text_added", []).append(text)
    if "claims_supported_text_added" in changes:
        existing["claims_supported_text"] = sorted(existing_texts)

    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="De-duplicate search results against citation ledger")
    parser.add_argument("--new-results", required=True, help="JSON file with new search results")
    parser.add_argument("--existing", required=True, help="citation_ledger.json path")
    parser.add_argument("--output", required=True, help="Output JSON path for de-duplicated results")
    parser.add_argument("--threshold", type=float, default=0.85, help="Title overlap threshold (default 0.85)")
    parser.add_argument("--update-ledger", action="store_true", help="Write merged changes back to the ledger")
    args = parser.parse_args()

    # Load inputs
    new_results_path = Path(args.new_results)
    ledger_path = Path(args.existing)

    if not new_results_path.exists():
        print(f"ERROR: new-results file not found: {new_results_path}", file=sys.stderr)
        sys.exit(1)

    if not ledger_path.exists():
        print(f"WARNING: citation ledger not found at {ledger_path}. Treating all papers as new.")
        ledger: dict = {}
    else:
        with ledger_path.open() as f:
            ledger = json.load(f)

    with new_results_path.open() as f:
        new_papers: list[dict] = json.load(f)

    if not isinstance(new_papers, list):
        # Support dict-of-dicts as well
        new_papers = list(new_papers.values()) if isinstance(new_papers, dict) else [new_papers]

    index = build_ledger_index(ledger)

    truly_new: list[dict] = []
    duplicates: list[dict] = []
    updated_keys: list[str] = []

    for paper in new_papers:
        dup_key = find_duplicate(paper, index, threshold=args.threshold)
        if dup_key:
            changes = merge_fields(ledger[dup_key], paper)
            duplicates.append({
                "new_paper_title": paper.get("title"),
                "matched_cite_key": dup_key,
                "matched_title": ledger[dup_key].get("title"),
                "fields_merged": changes,
            })
            if changes:
                updated_keys.append(dup_key)
        else:
            truly_new.append(paper)

    result = {
        "new_papers": truly_new,
        "duplicates": duplicates,
        "updated_entries": updated_keys,
        "summary": {
            "total_input": len(new_papers),
            "new": len(truly_new),
            "duplicates": len(duplicates),
            "ledger_entries_updated": len(updated_keys),
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(result, f, indent=2)

    print(
        f"De-duplication complete: {len(truly_new)} new, "
        f"{len(duplicates)} duplicates, {len(updated_keys)} ledger entries updated."
    )
    print(f"Output written to {output_path}")

    # Optionally write merged ledger back
    if args.update_ledger and updated_keys:
        with ledger_path.open("w") as f:
            json.dump(ledger, f, indent=2)
        print(f"Citation ledger updated at {ledger_path} ({len(updated_keys)} entries merged)")


if __name__ == "__main__":
    main()
