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

## Step 1: Locate the Manuscript Directory

Search for `main.tex` in these locations (in order):

1. `manuscript/main.tex`
2. `sparse-*/manuscript/main.tex` (glob)
3. `*/manuscript/main.tex` (glob)
4. `main.tex` in the project root

Set `MANUSCRIPT_DIR` to the directory containing `main.tex`. If no `main.tex` is found, report the error and stop.

Print:
```
Found manuscript: <MANUSCRIPT_DIR>/main.tex
```

## Step 2: Try LaTeX Compilation

Use the helper script if available:

```bash
bash scripts/compile_latex.sh "$MANUSCRIPT_DIR"
```

If the script is not available, perform the compilation manually by trying these compilers **in order** until one succeeds:

### Option A: tectonic

```bash
cd "$MANUSCRIPT_DIR" && tectonic main.tex
```

### Option B: pdflatex + bibtex

```bash
cd "$MANUSCRIPT_DIR"
pdflatex -interaction=nonstopmode main.tex
bibtex main || true
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

### Option C: xelatex + bibtex

```bash
cd "$MANUSCRIPT_DIR"
xelatex -interaction=nonstopmode main.tex
bibtex main || true
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

After compilation, check if `main.pdf` exists in `MANUSCRIPT_DIR`.

- If yes: report success and the absolute path to the PDF.
- If no: report that compilation failed but continue to the ZIP step.

## Step 3: Create Overleaf-Ready ZIP

**Always** create the ZIP, regardless of whether compilation succeeded.

Collect the following files from `MANUSCRIPT_DIR` into `overleaf-ready.zip`:

- `main.tex` (required)
- All `.tex` files (sections, appendices, etc.)
- All `.bib` files (bibliography)
- All `.sty` files (custom style files)
- All `.cls` files (document classes)
- All `.bst` files (bibliography styles)
- A `figures/` directory if it exists (include all files, especially `.pdf`, `.png`, `.eps`)
- Any `images/` directory if it exists
- Any `.pdf` figures in the manuscript directory root

Create the ZIP:

```bash
cd "$MANUSCRIPT_DIR"
zip -r overleaf-ready.zip \
  *.tex *.bib *.sty *.cls *.bst \
  figures/ images/ \
  2>/dev/null || true
# Ensure at least main.tex is in the zip
zip -u overleaf-ready.zip main.tex 2>/dev/null || true
```

## Step 4: Report Results

Display a summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Manuscript Compilation Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PDF compiled:  Yes / No (compiler used: <name>)
  PDF path:      <absolute path to main.pdf, or N/A>

  Overleaf ZIP:  <absolute path to overleaf-ready.zip>
  ZIP contents:  <number> files

  To upload to Overleaf:
  1. Go to https://www.overleaf.com/project
  2. Click "New Project" -> "Upload Project"
  3. Upload: <overleaf-ready.zip path>
  4. Overleaf will auto-compile on import
```

If no LaTeX compiler was available, add:

```
  Note: No LaTeX compiler found on this system.
        Install tectonic (`cargo install tectonic`) or texlive
        (`apt install texlive-full`) to compile locally.
        The Overleaf ZIP can still be uploaded and compiled there.
```
