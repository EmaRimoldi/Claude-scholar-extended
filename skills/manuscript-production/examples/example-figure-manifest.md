# Example Figure Manifest

This manifest maps generated figure files to their locations in the paper. Update after each figure generation or reorganization.

## Paper: "Induction Heads and Gradient Descent Alignment in Transformers"

| Filename | Paper Location | Type | Caption Summary |
|---|---|---|---|
| fig1-schematic.pdf | Figure 1 (Introduction) | Schematic | Pipeline overview showing the three-stage analysis: IH detection, GD alignment measurement, and nonlinear extension |
| fig2-main-comparison.pdf | Figure 2 (Results, Section 4.1) | Bar chart | Cosine similarity between IH and non-IH attention patterns across 6 model scales |
| fig3-nonlinear.pdf | Figure 3 (Results, Section 4.2) | Line plot | Linear vs. nonlinear task alignment scores, showing divergence beyond 2-layer models |
| fig4-training-dynamics.pdf | Figure 4 (Results, Section 4.3) | Line plot | IH-GD alignment over training steps (0-100k), with phase transition annotation at step 42k |
| fig5-ablation-heatmap.pdf | Figure 5 (Results, Section 4.4) | Heatmap | Ablation matrix: rows = components removed, columns = datasets, cells = relative performance drop |
| fig6-qualitative.pdf | Figure 6 (Discussion) | Multi-panel | Attention pattern visualizations for representative examples from each alignment category |

## Supplementary Figures

| Filename | Paper Location | Type | Caption Summary |
|---|---|---|---|
| figS1-all-seeds.pdf | Appendix A, Figure S1 | Line plot | Full training curves for all 5 seeds (main paper shows mean + CI) |
| figS2-additional-models.pdf | Appendix B, Figure S2 | Bar chart | Extended comparison including 4 additional baseline architectures |
| figS3-hyperparameter-sensitivity.pdf | Appendix C, Figure S3 | Heatmap | Sensitivity analysis over learning rate and weight decay grid |

## Notes

- All figures exported as vector PDF with embedded fonts (pdf.fonttype: 42).
- Style: NeurIPS 2025 single-column format (5.5 in width), serif font (Times), 9pt.
- Palette: Wong colorblind-safe (see `references/figure-style-guide.md`).
