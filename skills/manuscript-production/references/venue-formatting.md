# Venue-Specific Formatting Reference

Quick reference for submission formatting requirements at major ML/AI venues.

## NeurIPS 2025

- **Style file**: `neurips.sty` (from `ml-paper-writing/templates/neurips2025/`)
- **Page limit**: 9 pages main body + unlimited references + unlimited appendix
- **Format**: Single column, letter paper
- **Anonymization**: Required for review submission
  - No author names or affiliations
  - No acknowledgments section
  - No identifying URLs (use anonymous GitHub or suppress)
  - Avoid excessive self-citation that reveals identity
- **Checklist**: Mandatory paper checklist (last section before references)
  - Covers: claims, limitations, theory, experiments, reproducibility, broader impact
  - Every item must be answered (Yes / No / N/A) with justification
- **Supplementary**: Appendix in the same PDF, placed after references
- **Font**: Default LaTeX (Computer Modern) -- do not change
- **Abstract**: Max 250 words

## ICML 2025

- **Style file**: `icml2026.sty` (from `ml-paper-writing/templates/icml2026/`)
- **Page limit**: 8 pages main body + unlimited references + unlimited appendix
- **Format**: Two columns, letter paper
- **Anonymization**: Required for review submission (same rules as NeurIPS)
- **Broader impact**: Optional but recommended; can be placed in appendix
- **Supplementary**: Appendix after references in the same PDF
- **Figures**: Use `figure*` environment for full-width (two-column) figures
- **Font**: Default LaTeX (Computer Modern)
- **Abstract**: Max 200 words

## ICLR 2026

- **Style file**: `iclr2026_conference.sty` (from `ml-paper-writing/templates/iclr2026/`)
- **Page limit**: 10 pages main body + unlimited references + unlimited appendix
- **Format**: Single column, letter paper
- **Submission**: Via OpenReview platform (upload PDF)
- **Anonymization**: Required for review submission
- **Supplementary**: Appendix in same PDF or separate upload on OpenReview
- **Review process**: Open peer review; author responses are public
- **Font**: Default LaTeX (Computer Modern)
- **Abstract**: No strict word limit, but keep under 300 words

## ACL 2025

- **Style file**: `acl.sty` (from `ml-paper-writing/templates/acl/`)
- **Page limit**: 8 pages main body + unlimited references
- **Format**: Two columns, letter paper
- **Limitations section**: Required. Discuss limitations of the approach, experiments, or evaluation.
- **Ethics statement**: Required if the work raises ethical concerns (data privacy, bias, dual use)
- **Supplementary**: Separate PDF upload, max 100 MB
  - Appendices for proofs, data details, additional experiments
  - Software and data as separate uploads
- **Font**: Times New Roman (via `times` package)
- **Abstract**: Max 200 words

## Common LaTeX Gotchas

### Float Placement

```latex
% Force figure placement near text
\begin{figure}[t]   % top of page (preferred)
\begin{figure}[h]   % here (often ignored by LaTeX)
\begin{figure}[!ht] % try here, then top, override restrictions
```

- Never use `[H]` from the `float` package in conference submissions -- it breaks column balancing.
- If a figure drifts far from its reference, add `\FloatBarrier` (from `placeins` package) before the next section.

### Bibliography Style

```latex
% NeurIPS / ICML / ICLR: natbib with plainnat or custom .bst
\bibliographystyle{plainnat}
\bibliography{references}

% ACL: custom acl_natbib.bst
\bibliographystyle{acl_natbib}
\bibliography{references}
```

- Always use `\citet{}` for textual citations ("Smith et al. (2024) showed...") and `\citep{}` for parenthetical ("...as shown previously \citep{smith2024}").
- Check for broken citations: search the compiled PDF for "?" marks.

### Hyperref Conflicts

```latex
% Load hyperref LAST (after all other packages)
\usepackage[colorlinks=true,citecolor=blue,linkcolor=blue]{hyperref}
% Exception: cleveref must load AFTER hyperref
\usepackage{cleveref}
```

- Some venue style files load hyperref internally. Check before adding it manually.
- If you get "destination with the same identifier" warnings, add `\usepackage[hypertexnames=false]{hyperref}`.

### Number Formatting

```latex
\usepackage{siunitx}
\sisetup{group-separator={,}, group-minimum-digits=4}
% Usage: \num{12345} renders as 12,345
% Tables: S column type for aligned decimals
```

## Pre-Submission Formatting Checklist

Run through every item before uploading:

1. **Page limit**: Count main body pages (before references). Exclude references and appendix from the count.
2. **Anonymization**: Search PDF for author names, institution names, grant numbers, GitHub usernames. All must be absent.
3. **Figure legibility**: View PDF at 50% zoom. All figure text must be readable (minimum 6pt effective).
4. **Table formatting**: Use `booktabs` package. No vertical rules. Consistent decimal alignment.
5. **Reference completeness**: Compile with `bibtex`/`biber`. Check log for "Citation undefined" warnings. Search PDF for "?" in citation positions.
6. **Supplementary linkage**: If appendix exists, verify `\ref{}` cross-references between main paper and appendix resolve correctly.
7. **Checklist / limitations**: If required by venue, verify the section exists and is complete.
8. **No leftover markers**: Search source for `TODO`, `FIXME`, `PLACEHOLDER`, `XXX`, `HACK`. Remove all.
9. **Abstract word count**: Count words in abstract. Verify compliance with venue limit.
10. **PDF file size**: Check that the final PDF is under 50 MB (most venues reject larger files). Compress bitmap images if needed.
