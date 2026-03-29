#!/usr/bin/env python3
"""Compile LaTeX manuscript and assemble Overleaf-ready ZIP."""

import argparse
import json
import subprocess
import shutil
import sys
import zipfile
from pathlib import Path
from typing import List, Optional

FIGURE_EXTS = {".pdf", ".png", ".svg", ".jpg", ".jpeg"}
TEX_ASSET_EXTS = {".tex", ".bib", ".sty", ".cls", ".bst"}
FIGURE_DIRS = {"figures", "images"}


def find_main_tex(project_dir: Path, manuscript_dir: str) -> Optional[Path]:
    """Locate main.tex by searching standard locations then recursively."""
    candidates = [
        project_dir / manuscript_dir / "main.tex",
        project_dir / "manuscript" / "main.tex",
    ]
    for c in candidates:
        if c.is_file():
            return c

    # Try pipeline-state.json for project_dir hint
    state_file = project_dir / "pipeline-state.json"
    if state_file.is_file():
        try:
            state = json.loads(state_file.read_text())
            pd = state.get("project_dir")
            if pd:
                p = Path(pd) / manuscript_dir / "main.tex"
                if p.is_file():
                    return p
        except (json.JSONDecodeError, KeyError):
            pass

    # Recursive fallback
    for p in project_dir.rglob("main.tex"):
        return p
    return None


def compiler_available(name: str) -> bool:
    return shutil.which(name) is not None


def run_tectonic(main_tex: Path) -> bool:
    """Compile with tectonic (single invocation)."""
    result = subprocess.run(
        ["tectonic", str(main_tex)],
        cwd=str(main_tex.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def run_latex_3pass(compiler: str, main_tex: Path) -> bool:
    """Compile with pdflatex/xelatex using 3-pass + bibtex."""
    cwd = main_tex.parent
    stem = main_tex.stem
    cmd = [compiler, "-interaction=nonstopmode", str(main_tex)]
    run_kw = dict(cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Pass 1
    r = subprocess.run(cmd, **run_kw)
    if r.returncode != 0:
        return False

    # BibTeX
    subprocess.run(["bibtex", stem], **run_kw)

    # Pass 2 + 3
    for _ in range(2):
        r = subprocess.run(cmd, **run_kw)
        if r.returncode != 0:
            return False
    return True


COMPILERS = {
    "tectonic": run_tectonic,
    "pdflatex": lambda t: run_latex_3pass("pdflatex", t),
    "xelatex": lambda t: run_latex_3pass("xelatex", t),
}
COMPILER_ORDER = ["tectonic", "pdflatex", "xelatex"]


def compile_tex(main_tex: Path, compiler: str) -> Optional[str]:
    """Compile and return the compiler name used, or None on failure."""
    order = COMPILER_ORDER if compiler == "auto" else [compiler]
    for name in order:
        if not compiler_available(name):
            if compiler != "auto":
                print("Error: compiler '{}' not found on PATH.".format(name), file=sys.stderr)
            continue
        print("Trying {}...".format(name))
        if COMPILERS[name](main_tex):
            return name
        print("  {} failed.".format(name), file=sys.stderr)
    return None


def collect_zip_files(manuscript_root: Path) -> List[Path]:
    """Gather files for the Overleaf ZIP."""
    files = []  # type: List[Path]

    for p in manuscript_root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix in TEX_ASSET_EXTS:
            files.append(p)
        elif p.suffix.lower() in FIGURE_EXTS:
            # Only include figures under known dirs or manuscript root
            try:
                rel = p.relative_to(manuscript_root)
            except ValueError:
                continue
            parts = rel.parts
            if len(parts) == 1 or parts[0].lower() in FIGURE_DIRS:
                files.append(p)
    return sorted(files)


def create_zip(manuscript_root: Path, output_zip: Path) -> int:
    """Create Overleaf-ready ZIP; return file count."""
    files = collect_zip_files(manuscript_root)
    if not files:
        print("Warning: no files found to include in ZIP.", file=sys.stderr)
        return 0

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            arcname = str(f.relative_to(manuscript_root))
            zf.write(f, arcname)
    return len(files)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile LaTeX manuscript and create Overleaf-ready ZIP."
    )
    parser.add_argument("--project-dir", default=".", help="Project root (default: '.')")
    parser.add_argument("--manuscript-dir", default="manuscript/",
                        help="Manuscript subdirectory (default: 'manuscript/')")
    parser.add_argument("--output-zip", default="overleaf-ready.zip",
                        help="Output ZIP filename (default: 'overleaf-ready.zip')")
    parser.add_argument("--compiler", choices=["auto", "tectonic", "pdflatex", "xelatex"],
                        default="auto", help="LaTeX compiler (default: auto)")
    parser.add_argument("--no-compile", action="store_true",
                        help="Skip compilation, only create ZIP")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    project_dir = Path(args.project_dir).resolve()

    main_tex = find_main_tex(project_dir, args.manuscript_dir)
    if main_tex is None:
        print("Error: main.tex not found.", file=sys.stderr)
        return 1

    manuscript_root = main_tex.parent
    print("Found main.tex at {}".format(main_tex))

    compiler_used = "skipped"  # type: Optional[str]
    pdf_path = None  # type: Optional[Path]
    if not args.no_compile:
        compiler_used = compile_tex(main_tex, args.compiler)
        if compiler_used is None:
            print("Error: compilation failed with all attempted compilers.", file=sys.stderr)
            return 1
        pdf_path = main_tex.with_suffix(".pdf")
        if not pdf_path.is_file():
            print("Error: PDF not produced despite successful exit.", file=sys.stderr)
            return 1

    output_zip = project_dir / args.output_zip
    file_count = create_zip(manuscript_root, output_zip)

    print("\n--- Compilation Summary ---")
    print("  Compiler : {}".format(compiler_used))
    print("  PDF      : {}".format(pdf_path or "N/A"))
    print("  ZIP      : {}".format(output_zip))
    print("  Files    : {}".format(file_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
