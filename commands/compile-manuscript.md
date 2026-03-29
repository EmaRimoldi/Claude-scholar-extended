---
name: compile-manuscript
description: Compile LaTeX manuscript to PDF and create Overleaf-ready ZIP package. Tries tectonic, pdflatex, or xelatex. Always produces an Overleaf-ready ZIP as fallback.
tags: [Manuscript, LaTeX, Pipeline]
---

# /compile-manuscript - LaTeX Compilation & Overleaf Package

## Project Directory

All output files for this step MUST be written inside the active project directory (stored in `pipeline-state.json` → `project_dir`). Read `pipeline-state.json` to resolve `$PROJECT_DIR` before writing any files.

- Compiled PDF → `$PROJECT_DIR/manuscript/`
- Overleaf ZIP → `$PROJECT_DIR/manuscript/`

Never write compiled outputs to the repository root.

You are now the manuscript compiler. Your job is to compile the LaTeX manuscript to PDF and create an Overleaf-ready ZIP package.

## Execution

Run the deterministic compilation and packaging script:

```bash
python scripts/compile_manuscript.py --project-dir $PROJECT_DIR
```

The script automatically:
1. Locates `main.tex` (searches `manuscript/`, `*/manuscript/`, project root)
2. Tries compilers in order (tectonic → pdflatex+bibtex → xelatex+bibtex)
3. Creates `overleaf-ready.zip` with all `.tex`, `.bib`, `.sty`, `.cls`, `.bst`, and `figures/` files
4. Prints a structured summary with paths and Overleaf upload instructions

Options: `--compiler auto|tectonic|pdflatex|xelatex`, `--no-compile` (ZIP only), `--output-zip <name>`. Run `--help` for details.
