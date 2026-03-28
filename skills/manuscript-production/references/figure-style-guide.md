# Figure Style Guide

Reference for producing publication-quality figures across ML/AI venues.

## Matplotlib rcParams by Venue

### NeurIPS

```python
rcParams = {
    "font.family": "serif",
    "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.figsize": (5.5, 3.5),       # single column
    "figure.dpi": 150,                   # screen; export at 300+
    "lines.linewidth": 1.0,
    "lines.markersize": 4,
    "axes.linewidth": 0.6,
    "grid.linewidth": 0.4,
    "pdf.fonttype": 42,                  # TrueType embedding
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
}
# Double column: set figure.figsize = (11.0, 3.5)
```

### ICML

```python
rcParams = {
    "font.family": "serif",
    "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.figsize": (3.25, 2.5),       # single column
    "figure.dpi": 150,
    "lines.linewidth": 1.0,
    "lines.markersize": 3.5,
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.3,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
}
# Double column: set figure.figsize = (6.75, 2.5)
```

### ICLR

```python
# ICLR uses single-column format, similar sizing to NeurIPS
rcParams = {
    "font.family": "serif",
    "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.figsize": (5.5, 3.5),
    "figure.dpi": 150,
    "lines.linewidth": 1.0,
    "lines.markersize": 4,
    "axes.linewidth": 0.6,
    "grid.linewidth": 0.4,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
}
```

### ACL

```python
rcParams = {
    "font.family": "serif",
    "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.figsize": (3.3, 2.5),        # single column
    "figure.dpi": 150,
    "lines.linewidth": 1.0,
    "lines.markersize": 3.5,
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.3,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
}
# Double column: set figure.figsize = (6.8, 2.5)
```

## Colorblind-Safe Palettes

### Qualitative (6-color, Wong palette)

For categorical comparisons with up to 6 groups:

| Index | Name     | Hex       | RGB            |
|-------|----------|-----------|----------------|
| 0     | Blue     | `#0072B2` | (0, 114, 178)  |
| 1     | Orange   | `#E69F00` | (230, 159, 0)  |
| 2     | Green    | `#009E73` | (0, 158, 115)  |
| 3     | Red      | `#D55E00` | (213, 94, 0)   |
| 4     | Purple   | `#CC79A7` | (204, 121, 167)|
| 5     | Cyan     | `#56B4E9` | (86, 180, 233) |

```python
WONG_PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]
```

### Sequential

Use for ordered data (e.g., performance across epochs):

- **viridis**: Default choice. Perceptually uniform, colorblind-safe.
- **inferno**: Higher contrast at the dark end. Good for heatmaps with many near-zero values.
- **cividis**: Optimized specifically for color vision deficiency.

### Diverging

Use for data with a meaningful center (e.g., correlation matrices, difference maps):

- **coolwarm**: Desaturated blue-to-red. Readable in grayscale.
- **RdBu_r**: Red-to-blue reversed. Higher saturation; use when contrast matters more.

## Bar Chart Conventions

- Use grouped bars for multi-method comparisons.
- Add hatching patterns for grayscale compatibility: `/`, `\\`, `x`, `.`, `o`, `+`.
- Error bars: always state in the caption whether they show 95% CI or standard deviation.
- Include a horizontal dashed line for the strongest baseline for quick visual comparison.
- Bar width: 0.15-0.25 per group member, with 0.02-0.05 gaps between bars in a group.
- Sort bars by a meaningful order (not alphabetical): best-to-worst, or chronological.

## Line Plot Conventions

- Assign distinct markers to each method: `o`, `s`, `^`, `D`, `v`, `P`.
- Vary line styles for grayscale: `-`, `--`, `-.`, `:`.
- Shading for confidence intervals: alpha = 0.2-0.3.
- Axis labels must include units: "Accuracy (%)", "Training Steps (x1000)".
- Use `ax.set_xlim` and `ax.set_ylim` to avoid wasted whitespace.
- Legend placement: outside the plot area if it occludes data, otherwise upper-right or lower-right.

## Heatmap Conventions

- Annotate cells with values when the matrix is small (< 15x15).
- Color normalization: linear for most cases; log scale for data spanning orders of magnitude.
- Aspect ratio: 1:1 (square cells) unless the matrix is highly rectangular.
- Colorbar: always include, with a descriptive label.
- Row/column labels: readable font size (>= 7pt), rotated if necessary.

## Multi-Panel Layout

- Use `plt.subplots(nrows, ncols, figsize=(...))` for consistent sizing.
- Shared axes: use `sharex=True` or `sharey=True` when panels share a dimension.
- Panel labels: add `(a)`, `(b)`, `(c)` in the upper-left corner of each panel using `ax.text(-0.1, 1.05, ...)` with `transform=ax.transAxes`.
- Spacing: `plt.subplots_adjust(wspace=0.3, hspace=0.3)` or `fig.tight_layout()`.
- Consistent y-axis ranges across panels when comparing the same metric.

## Export Checklist

1. Format: vector PDF (`fig.savefig("name.pdf")`).
2. Font embedding: `pdf.fonttype: 42` in rcParams.
3. Whitespace: `bbox_inches='tight'`, `pad_inches=0.02`.
4. Resolution: `dpi=300` for any rasterized elements.
5. File size: check that vector PDFs are reasonable (< 5 MB per figure).
6. Verify: open the exported PDF and confirm text is selectable (not rasterized).
7. Print test: view at 50% zoom to simulate print size; all text and labels must be legible.
