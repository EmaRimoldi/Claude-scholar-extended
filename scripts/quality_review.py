#!/usr/bin/env python3
"""Extract programmatically checkable facts from a manuscript for quality review.
Performs mechanical checks so the LLM reviewer only handles judgment-heavy scoring.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

# -- LaTeX helpers ----------------------------------------------------------

def _resolve_inputs(tex_dir, text, seen=None):
    # type: (Path, str, set) -> str
    """Recursively inline \\input{} files."""
    if seen is None:
        seen = set()
    def _replace(m):
        name = m.group(1)
        if not name.endswith(".tex"):
            name += ".tex"
        if name in seen:
            return ""
        seen.add(name)
        p = tex_dir / name
        if p.is_file():
            return _resolve_inputs(tex_dir, p.read_text(errors="replace"), seen)
        return ""
    return re.sub(r"\\input\{([^}]+)\}", _replace, text)


def _extract_env(text, env):
    m = re.search(rf"\\begin\{{{env}\}}(.*?)\\end\{{{env}\}}", text, re.S)
    return m.group(1).strip() if m else ""


def _extract_braced(text, cmd):
    """Extract content of \\cmd{...} handling nested braces and multiline."""
    pat = re.compile(rf"\\{cmd}\s*\{{")
    m = pat.search(text)
    if not m:
        return ""
    depth, start = 1, m.end()
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i].strip()
    return ""


def _find_all(text, cmd):
    return re.findall(rf"\\{cmd}\{{([^}}]+)\}}", text)

# -- Checks -----------------------------------------------------------------

BANNED = ["universal", "general", "always", "any", "all"]
RESTRICTED = ["robust", "consistent", "reliable", "task-agnostic"]
STOP_WORDS = {
    "a", "an", "the", "of", "for", "in", "on", "to", "with", "by", "and",
    "or", "is", "are", "was", "were", "be", "been", "being", "from", "at",
    "as", "via", "using", "through", "into", "between", "across", "over",
}
PREPOSITIONS_VERBS = STOP_WORDS | {
    "show", "shows", "demonstrate", "achieve", "use", "uses", "learn",
    "learns", "predict", "predicts", "improve", "improves", "based",
}


def title_audit(title):
    lower = title.lower()
    words = re.findall(r"[a-z][\w-]*", lower)
    qualifiers = [w for w in words if w not in PREPOSITIONS_VERBS]
    return {
        "title": title,
        "banned_found": [w for w in BANNED if w in lower],
        "restricted_found": [w for w in RESTRICTED if w in lower],
        "qualifiers": qualifiers,
    }


def scope_evidence(results_path):
    counts = {"model": set(), "dataset": set(), "method": set()}
    try:
        with results_path.open(newline="") as f:
            reader = csv.DictReader(f)
            cols = [c.lower() for c in (reader.fieldnames or [])]
            for row in reader:
                for key in counts:
                    for col in cols:
                        if key in col:
                            val = row.get(col) or row.get(col.title(), "")
                            if val:
                                counts[key].add(val.strip())
    except Exception:
        return {}
    return {k: {"count": len(v), "values": sorted(v)} for k, v in counts.items()}


def abstract_evidence(abstract, labels):
    """Flag abstract sentences with numbers but no figure/table ref."""
    sentences = re.split(r"(?<=[.!?])\s+", abstract)
    flags = []
    for s in sentences:
        has_number = bool(re.search(r"\d+\.?\d*%?", s))
        has_ref = bool(re.search(r"(?:Table|Figure|Fig\.|Tab\.)\s*\d", s, re.I))
        if has_number and not has_ref:
            flags.append({"sentence": s.strip(), "issue": "quantitative_claim_no_ref"})
    return flags


def statistical_scan(text):
    patterns = {
        "p_values": r"p\s*[<>=]",
        "confidence_intervals": r"(?:CI|confidence)",
        "effect_sizes": r"(?:Cohen|η²|eta|effect.size)",
        "test_names": r"(?:ANOVA|t-test|Tukey|Wilcoxon|Mann-Whitney)",
    }
    return {k: len(re.findall(v, text, re.I)) for k, v in patterns.items()}


def efficiency_check(intro_abstract, results_text):
    claim_kws = ["faster", "cheaper", "efficient", "memory", "parameter",
                  "compute", "cost", "speed"]
    measure_pat = r"(?:wall.time|throughput|GPU.memory|peak.memory|examples.per.second)"
    claimed = [w for w in claim_kws if w in intro_abstract.lower()]
    measured = bool(re.search(measure_pat, results_text, re.I)) if claimed else False
    return {
        "efficiency_claimed": bool(claimed),
        "keywords_found": claimed,
        "measurement_present": measured,
        "flag": bool(claimed) and not measured,
    }


def limitation_claims(limitations, abstract):
    strong = r"\b(?:show|demonstrate|achieve|outperform|establish)\b"
    claims = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abstract)
              if re.search(strong, s, re.I)]
    lim_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", limitations) if s.strip()]
    return {"abstract_claims": claims, "limitation_sentences": lim_sents}


def reproducibility_check(text):
    return {
        "seed_mentioned": bool(re.search(r"\bseed\b", text, re.I)),
        "hyperparameter_table": bool(re.search(r"\\begin\{table\}", text)),
        "code_availability": bool(re.search(
            r"(?:code.available|github\.com|open.source|supplementary.code)", text, re.I)),
        "hardware_mentioned": bool(re.search(r"\b(?:GPU|A100|V100|TPU|H100)\b", text)),
    }

# -- Section extraction -----------------------------------------------------

def _section_text(full, name):
    pat = re.compile(rf"\\section\{{{name}\}}(.*?)(?=\\section\{{|\\end\{{document\}}|$)", re.S | re.I)
    m = pat.search(full)
    return m.group(1).strip() if m else ""

# -- Main -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Mechanical quality-review data extractor.")
    ap.add_argument("--manuscript-dir", default="manuscript/", help="LaTeX source directory")
    ap.add_argument("--results", default=None, help="Optional results CSV")
    ap.add_argument("--output", default="quality-review-data.json", help="Output JSON path")
    args = ap.parse_args()

    ms_dir = Path(args.manuscript_dir)
    main_tex = ms_dir / "main.tex"
    report = {"auto_fail": [], "warnings": []}

    # --- Parse LaTeX ---
    if not main_tex.is_file():
        report["auto_fail"].append("main.tex not found")
        Path(args.output).write_text(json.dumps(report, indent=2))
        return 1

    raw = main_tex.read_text(errors="replace")
    full = _resolve_inputs(ms_dir, raw)

    title = _extract_braced(full, "title")
    abstract = _extract_env(full, "abstract")
    labels = _find_all(full, "label")
    refs = _find_all(full, "ref")
    cites = _find_all(full, "cite")
    discussion = _section_text(full, "Discussion")
    limitations = _section_text(full, "Limitations")
    results_sec = _section_text(full, "Results") or _section_text(full, "Experiments")
    intro = _section_text(full, "Introduction")

    report["manuscript"] = {
        "title": title,
        "abstract": abstract,
        "labels": labels,
        "refs": refs,
        "cites": cites,
        "discussion_length": len(discussion.split()),
        "limitations_length": len(limitations.split()),
    }

    # --- Title audit ---
    report["title_audit"] = title_audit(title)
    if report["title_audit"]["banned_found"]:
        report["auto_fail"].append(
            f"Title contains banned word(s): {report['title_audit']['banned_found']}")
    if report["title_audit"]["restricted_found"]:
        report["warnings"].append(
            f"Title contains restricted word(s): {report['title_audit']['restricted_found']}")

    # --- Scope-evidence ---
    if args.results:
        rp = Path(args.results)
        if rp.is_file():
            report["scope_evidence"] = scope_evidence(rp)
        else:
            report["warnings"].append(f"Results CSV not found: {args.results}")

    # --- Abstract-evidence ---
    report["abstract_evidence_flags"] = abstract_evidence(abstract, labels)

    # --- Statistical scan ---
    report["statistical_reporting"] = statistical_scan(full)

    # --- Efficiency check ---
    report["efficiency_check"] = efficiency_check(intro + " " + abstract, results_sec)
    if report["efficiency_check"]["flag"]:
        report["warnings"].append("Efficiency claimed but no measurement found in results")

    # --- Limitation-claim pairs ---
    report["limitation_claims"] = limitation_claims(limitations, abstract)

    # --- Reproducibility ---
    report["reproducibility"] = reproducibility_check(full)

    Path(args.output).write_text(json.dumps(report, indent=2))
    print(f"Quality-review data written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
