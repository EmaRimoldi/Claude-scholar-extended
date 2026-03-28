#!/usr/bin/env bash
# compile_latex.sh - Compile LaTeX manuscript and create Overleaf-ready ZIP
#
# Usage:
#   bash compile_latex.sh [manuscript_dir]
#
# If manuscript_dir is not given, searches for main.tex automatically.
# Always creates overleaf-ready.zip. Exits 0 even if compilation fails.

set -euo pipefail

# --- Locate manuscript directory ---
find_manuscript_dir() {
    local candidates=(
        "manuscript"
        "."
    )
    # Add any sparse-*/manuscript or */manuscript dirs
    for d in sparse-*/manuscript */manuscript; do
        [ -d "$d" ] && candidates+=("$d")
    done

    for dir in "${candidates[@]}"; do
        if [ -f "$dir/main.tex" ]; then
            echo "$dir"
            return 0
        fi
    done
    return 1
}

MANUSCRIPT_DIR="${1:-}"
if [ -z "$MANUSCRIPT_DIR" ]; then
    MANUSCRIPT_DIR=$(find_manuscript_dir) || {
        echo "ERROR: Could not find main.tex in any standard location." >&2
        echo "Usage: $0 [manuscript_dir]" >&2
        exit 1
    }
fi

if [ ! -f "$MANUSCRIPT_DIR/main.tex" ]; then
    echo "ERROR: $MANUSCRIPT_DIR/main.tex not found." >&2
    exit 1
fi

MANUSCRIPT_DIR=$(cd "$MANUSCRIPT_DIR" && pwd)
echo "Manuscript directory: $MANUSCRIPT_DIR"

# --- Compilation ---
PDF_OK=0
COMPILER_USED="none"

compile_tectonic() {
    echo "Trying tectonic..."
    cd "$MANUSCRIPT_DIR"
    if command -v tectonic &>/dev/null; then
        if tectonic main.tex; then
            return 0
        fi
    fi
    return 1
}

compile_pdflatex() {
    echo "Trying pdflatex + bibtex..."
    cd "$MANUSCRIPT_DIR"
    if command -v pdflatex &>/dev/null; then
        pdflatex -interaction=nonstopmode main.tex || true
        bibtex main 2>/dev/null || true
        pdflatex -interaction=nonstopmode main.tex || true
        if pdflatex -interaction=nonstopmode main.tex; then
            return 0
        fi
    fi
    return 1
}

compile_xelatex() {
    echo "Trying xelatex + bibtex..."
    cd "$MANUSCRIPT_DIR"
    if command -v xelatex &>/dev/null; then
        xelatex -interaction=nonstopmode main.tex || true
        bibtex main 2>/dev/null || true
        xelatex -interaction=nonstopmode main.tex || true
        if xelatex -interaction=nonstopmode main.tex; then
            return 0
        fi
    fi
    return 1
}

if compile_tectonic; then
    PDF_OK=1
    COMPILER_USED="tectonic"
elif compile_pdflatex; then
    PDF_OK=1
    COMPILER_USED="pdflatex"
elif compile_xelatex; then
    PDF_OK=1
    COMPILER_USED="xelatex"
fi

cd "$MANUSCRIPT_DIR"

if [ "$PDF_OK" -eq 1 ] && [ -f main.pdf ]; then
    echo ""
    echo "PDF compiled successfully with $COMPILER_USED"
    echo "PDF: $MANUSCRIPT_DIR/main.pdf"
else
    echo ""
    echo "LaTeX compilation did not produce a PDF."
    if ! command -v tectonic &>/dev/null && ! command -v pdflatex &>/dev/null && ! command -v xelatex &>/dev/null; then
        echo "No LaTeX compiler found. Install tectonic or texlive."
    fi
fi

# --- Overleaf-ready ZIP ---
echo ""
echo "Creating Overleaf-ready ZIP..."

cd "$MANUSCRIPT_DIR"
ZIP_FILE="overleaf-ready.zip"
rm -f "$ZIP_FILE"

# Collect files
FILES_TO_ZIP=()

# .tex files
for f in *.tex; do [ -f "$f" ] && FILES_TO_ZIP+=("$f"); done

# .bib files
for f in *.bib; do [ -f "$f" ] && FILES_TO_ZIP+=("$f"); done

# .sty files
for f in *.sty; do [ -f "$f" ] && FILES_TO_ZIP+=("$f"); done

# .cls files
for f in *.cls; do [ -f "$f" ] && FILES_TO_ZIP+=("$f"); done

# .bst files
for f in *.bst; do [ -f "$f" ] && FILES_TO_ZIP+=("$f"); done

# Figure directories
DIRS_TO_ZIP=()
[ -d "figures" ] && DIRS_TO_ZIP+=("figures/")
[ -d "images" ] && DIRS_TO_ZIP+=("images/")

# Create the zip
if [ ${#FILES_TO_ZIP[@]} -gt 0 ] || [ ${#DIRS_TO_ZIP[@]} -gt 0 ]; then
    zip -r "$ZIP_FILE" "${FILES_TO_ZIP[@]}" "${DIRS_TO_ZIP[@]}" 2>/dev/null || true
fi

# Ensure main.tex is included
zip -u "$ZIP_FILE" main.tex 2>/dev/null || true

if [ -f "$ZIP_FILE" ]; then
    FILE_COUNT=$(unzip -l "$ZIP_FILE" 2>/dev/null | tail -1 | awk '{print $2}')
    echo "Overleaf ZIP: $MANUSCRIPT_DIR/$ZIP_FILE ($FILE_COUNT files)"
else
    echo "WARNING: Failed to create ZIP file." >&2
fi

# --- Summary ---
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Compilation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$PDF_OK" -eq 1 ] && [ -f main.pdf ]; then
    echo "  PDF:  $MANUSCRIPT_DIR/main.pdf (compiled with $COMPILER_USED)"
else
    echo "  PDF:  not produced"
fi
echo "  ZIP:  $MANUSCRIPT_DIR/$ZIP_FILE"
echo ""

# Always exit 0 - the ZIP is the guaranteed output
exit 0
