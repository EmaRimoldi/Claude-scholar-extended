# LaTeX Patterns Reference

Common LaTeX patterns for assembling ML/AI conference submissions.

## Document Structure Template

```latex
\documentclass{article}
% Venue style (load first)
\usepackage{neurips_2025}  % or icml2026, iclr2026_conference, acl

% Standard packages
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{natbib}
\usepackage{xcolor}
\usepackage{subcaption}        % for subfigures
\usepackage{algorithm,algorithmic}
\usepackage{siunitx}           % number formatting

% Hyperref (load last, before cleveref)
\usepackage[colorlinks=true,citecolor=blue,linkcolor=blue,urlcolor=blue]{hyperref}
\usepackage{cleveref}

% Custom notation commands
\input{notation.tex}

\title{Paper Title}

\begin{document}
\maketitle

\begin{abstract}
\input{sections/abstract.tex}
\end{abstract}

\input{sections/introduction.tex}
\input{sections/related-work.tex}
\input{sections/method.tex}
\input{sections/results.tex}
\input{sections/discussion.tex}

\bibliographystyle{plainnat}
\bibliography{references}

\appendix
\input{sections/appendix.tex}

\end{document}
```

## Figure Inclusion

### Single Figure

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/fig1-pipeline.pdf}
  \caption{Overview of the proposed method. (a) Input processing.
           (b) Core module. (c) Output generation.}
  \label{fig:pipeline}
\end{figure}
```

### Subfigures

```latex
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\linewidth}
    \includegraphics[width=\linewidth]{figures/fig2a-train.pdf}
    \caption{Training curves}
    \label{fig:results-train}
  \end{subfigure}
  \hfill
  \begin{subfigure}[b]{0.48\linewidth}
    \includegraphics[width=\linewidth]{figures/fig2b-eval.pdf}
    \caption{Evaluation metrics}
    \label{fig:results-eval}
  \end{subfigure}
  \caption{Training and evaluation results across five seeds.
           Error bands show 95\% confidence intervals.}
  \label{fig:results}
\end{figure}
```

### Full-Width Figure (Two-Column Venues)

```latex
% Use figure* for ICML and ACL (two-column formats)
\begin{figure*}[t]
  \centering
  \includegraphics[width=0.9\textwidth]{figures/fig3-comparison.pdf}
  \caption{Comparison across all baselines and datasets.}
  \label{fig:comparison}
\end{figure*}
```

## Table Formatting

### Standard Results Table

```latex
\begin{table}[t]
  \centering
  \caption{Main results on benchmark datasets. Best results in \textbf{bold},
           second best \underline{underlined}. Mean $\pm$ std over 5 seeds.}
  \label{tab:main-results}
  \begin{tabular}{lSSS}
    \toprule
    Method & {Dataset A} & {Dataset B} & {Dataset C} \\
    \midrule
    Baseline 1        & 72.3 \pm 1.2 & 68.5 \pm 0.8 & 81.2 \pm 0.5 \\
    Baseline 2        & 74.1 \pm 0.9 & 70.2 \pm 1.1 & 82.8 \pm 0.7 \\
    \midrule
    Ours              & \textbf{76.8 \pm 0.6} & \textbf{73.4 \pm 0.7} & \textbf{85.1 \pm 0.4} \\
    \bottomrule
  \end{tabular}
\end{table}
```

### Multicolumn Headers

```latex
\begin{tabular}{l*{2}{SS}*{2}{SS}}
  \toprule
  & \multicolumn{2}{c}{Setting A} & \multicolumn{2}{c}{Setting B} \\
  \cmidrule(lr){2-3} \cmidrule(lr){4-5}
  Method & {Acc.} & {F1} & {Acc.} & {F1} \\
  \midrule
  ...
  \bottomrule
\end{tabular}
```

## Mathematical Notation

### Defining Custom Commands

```latex
% notation.tex -- load via \input{notation.tex} in preamble

% Operators
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator{\softmax}{softmax}
\DeclareMathOperator{\relu}{ReLU}

% Common symbols
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\loss}{\mathcal{L}}
\newcommand{\dataset}{\mathcal{D}}
\newcommand{\model}{f_\theta}
\newcommand{\params}{\theta}

% Vectors and matrices (bold)
\newcommand{\vx}{\mathbf{x}}
\newcommand{\vy}{\mathbf{y}}
\newcommand{\vz}{\mathbf{z}}
\newcommand{\mW}{\mathbf{W}}
\newcommand{\mH}{\mathbf{H}}
```

### Usage in Text

```latex
Given a dataset $\dataset = \{(\vx_i, \vy_i)\}_{i=1}^{N}$, we train
$\model$ by minimizing the loss $\loss(\params) = \E_{(\vx,\vy) \sim \dataset}
[\ell(\model(\vx), \vy)]$.
```

## Bibliography Management

### BibTeX File Organization

```bibtex
% references.bib -- group entries by topic

% === Foundational Methods ===
@inproceedings{vaswani2017attention,
  title     = {Attention is All You Need},
  author    = {Vaswani, Ashish and others},
  booktitle = {NeurIPS},
  year      = {2017}
}

% === Our Method's Predecessors ===
...

% === Benchmarks and Datasets ===
...
```

- Use consistent key format: `{firstauthor}{year}{keyword}`.
- Include DOI or URL for every entry when available.
- Use `and others` for papers with many authors; BibTeX will render "et al." automatically.

## Supplementary Material Setup

### Appendix in Same PDF

```latex
% After \bibliography{references}
\appendix

\section{Proof of Theorem 1}
\label{app:proof}
...

\section{Additional Experimental Details}
\label{app:details}

\subsection{Hyperparameter Settings}
...

\subsection{Additional Results}
...

\section{Extended Figures}
\label{app:figures}
...
```

### Separate Supplementary PDF (ACL)

```latex
% supplementary/supplementary.tex
\documentclass{article}
\usepackage{amsmath,graphicx,booktabs}
\title{Supplementary Material for: Paper Title}
\begin{document}
\maketitle

\section{Extended Proofs}
...

\section{Full Results Tables}
...

\end{document}
```

Cross-reference between main paper and supplementary using consistent labeling: "See Appendix A in the supplementary material."
