"""
Example: Setting matplotlib rcParams for NeurIPS 2025 format.

Usage:
    from example_rcparams import apply_neurips_style, WONG_PALETTE, save_figure
    apply_neurips_style(column="single")
    fig, ax = plt.subplots()
    ax.plot(x, y, color=WONG_PALETTE[0], marker="o")
    save_figure(fig, "fig1-example.pdf")
"""

import matplotlib.pyplot as plt

# Wong colorblind-safe palette (6 colors)
WONG_PALETTE = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # green
    "#D55E00",  # red
    "#CC79A7",  # purple
    "#56B4E9",  # cyan
]


def apply_neurips_style(column: str = "single") -> None:
    """Apply NeurIPS 2025 figure style to matplotlib.

    Args:
        column: "single" (5.5 in) or "double" (11 in).
    """
    width = 5.5 if column == "single" else 11.0
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.figsize": (width, 3.5),
        "figure.dpi": 150,
        "lines.linewidth": 1.0,
        "lines.markersize": 4,
        "axes.linewidth": 0.6,
        "grid.linewidth": 0.4,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


def save_figure(fig: plt.Figure, filename: str, dpi: int = 300) -> None:
    """Save figure as vector PDF with tight layout.

    Args:
        fig: Matplotlib figure object.
        filename: Output filename (should end in .pdf).
        dpi: Resolution for any rasterized elements.
    """
    fig.savefig(filename, format="pdf", dpi=dpi, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"Saved: {filename}")
