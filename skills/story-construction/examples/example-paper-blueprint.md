# Example: Paper Blueprint

## Project: In-Context Learning as Implicit Algorithm Selection -- Bridging Circuits and Algorithms
## Target Venue: ICML
## Input Mode: Pipeline (claim-evidence-map.md detected)

---

## Narrative Arc

### One-Sentence Story

This paper shows that in-context learning in Transformers implements distinct computational circuits for different algorithmic strategies (gradient descent vs. Bayesian inference), selected by input structure, which means ICL behavior is predictable from input properties rather than opaque model internals.

### Setup (Known Context + Gap)

In-context learning (ICL) enables Transformers to learn from examples provided in the prompt without gradient updates. Two lines of prior work explain ICL: the *circuits view* (specific attention patterns implement ICL) and the *algorithms view* (ICL approximates known learning algorithms like gradient descent). These views developed independently and sometimes contradict each other -- the circuits view describes *how* ICL is implemented, while the algorithms view describes *what* ICL computes, but no work has connected the two.

### Question

Do distinct attention circuit motifs correspond to distinct implicit learning algorithms, and can the algorithm be predicted from input structure alone?

### Evidence

1. Circuit analysis reveals two distinct motifs that activate on different input distributions (structured vs. noisy)
2. Motif A's output matches gradient descent predictions; Motif B's output matches Bayesian ridge regression predictions
3. Ablating motif-specific heads selectively degrades the corresponding algorithm
4. Input structure features (covariance rank, noise level) predict which motif activates with 92% accuracy

### Implication

ICL is not a single mechanism but a repertoire of algorithms with corresponding circuits, selected by input properties. This makes ICL behavior predictable and suggests principled approaches to controlling which algorithm a model uses in-context.

---

## Result Triage

| # | Result | Evidence Strength | Narrative Category | Placement |
|---|--------|------------------|--------------------|-----------|
| R1 | Two distinct circuit motifs identified via activation patching | Strong | **Primary** | Results 4.1, Figure 2 |
| R2 | Motif A output matches gradient descent on structured inputs (R^2 = 0.94) | Strong | **Primary** | Results 4.2, Figure 3 |
| R3 | Motif B output matches Bayesian ridge regression on noisy inputs (R^2 = 0.91) | Strong | **Primary** | Results 4.2, Figure 3 |
| R4 | Ablating motif-specific heads selectively impairs corresponding algorithm | Strong | **Primary** | Results 4.3, Table 1 |
| R5 | Input structure predicts active motif with 92% accuracy | Strong | **Supporting** | Results 4.4, Figure 4 |
| R6 | Circuit motifs are consistent across model scales (125M, 350M, 1.3B) | Moderate | **Supporting** | Results 4.5, Table 2 |
| R7 | Attention head overlap between motifs is minimal (<8% shared heads) | Moderate | **Diagnostic** | Methods 3.2 (brief mention) |
| R8 | Motif B fails to match Bayesian prediction on adversarial distributions | Weak | **Null/Negative** | Discussion 6.1 (limitation) |

---

## Figure Plan

### Figure 1: Method Schematic

- **Type**: Schematic diagram
- **Layout**: Single panel, left-to-right flow
- **Content**: Input sequence enters Transformer; activation patching identifies circuit motifs; motif outputs compared against algorithm predictions
- **Reader takeaway**: "This figure shows the analysis pipeline: we identify circuits via activation patching and compare their outputs to known learning algorithms."
- **Annotations**: Novel steps highlighted in color (circuit-algorithm comparison)
- **Caption must include**: Overview of the three-stage analysis pipeline

### Figure 2: Circuit Motif Identification

- **Type**: Heatmap + schematic (2-panel)
- **Layout**: Left panel: activation patching heatmap (layers x heads, color = causal effect); Right panel: extracted circuit diagrams for Motif A and Motif B
- **X-axis (left)**: Attention head index; **Y-axis (left)**: Layer index; **Color**: Causal effect magnitude
- **Reader takeaway**: "This figure shows that activation patching reveals two spatially distinct circuit motifs with minimal overlap."
- **Statistical annotations**: Threshold line for significant causal effect (p < 0.01)
- **Caption must include**: Number of heads per motif, overlap percentage, significance threshold

### Figure 3: Algorithm Matching

- **Type**: Scatter plot (2-panel)
- **Layout**: Left panel: Motif A output vs. gradient descent prediction; Right panel: Motif B output vs. Bayesian ridge prediction
- **X-axis**: Algorithm prediction (gradient descent or Bayesian ridge); **Y-axis**: Circuit motif output; **Color**: Input distribution type
- **Reader takeaway**: "This figure shows that each circuit motif closely matches a specific learning algorithm, with R^2 > 0.91 for both."
- **Statistical annotations**: R^2 values, regression line, 95% CI band, identity line (dashed)
- **Caption must include**: Number of test sequences, R^2 values, input distribution details

### Figure 4: Input-Driven Algorithm Selection

- **Type**: Line plot with decision boundary
- **Layout**: Single panel
- **X-axis**: Input covariance rank; **Y-axis**: Noise level; **Color/marker**: Active motif (A or B)
- **Reader takeaway**: "This figure shows that input structure (covariance rank and noise level) reliably predicts which circuit motif activates, with 92% classification accuracy."
- **Statistical annotations**: Decision boundary line, classification accuracy annotation, misclassified points marked
- **Caption must include**: Number of test inputs, classification accuracy, feature definitions

### Table 1: Ablation Results

- **Type**: Table
- **Layout**: Rows = ablation condition (no ablation, ablate Motif A heads, ablate Motif B heads, ablate both); Columns = performance on structured inputs, performance on noisy inputs
- **Reader takeaway**: "This table shows that ablating motif-specific heads selectively impairs the corresponding algorithm while leaving the other intact."
- **Statistical annotations**: Mean +/- SEM across 5 seeds, significance stars for degradation vs. no-ablation baseline
- **Caption must include**: Number of seeds, significance test used, metric definition

### Table 2: Cross-Scale Consistency

- **Type**: Table
- **Layout**: Rows = model scale (125M, 350M, 1.3B); Columns = Motif A R^2 (GD), Motif B R^2 (Bayesian), motif prediction accuracy
- **Reader takeaway**: "This table shows that circuit-algorithm correspondence holds across model scales, though the match improves with scale."
- **Statistical annotations**: 95% CI for R^2 values
- **Caption must include**: Model sizes, training data, evaluation protocol

---

## Section Outline

### Abstract (4 sentences)

1. **Setup**: In-context learning enables Transformers to learn from prompt examples, but the relationship between its circuit-level implementation and the algorithms it approximates remains unclear.
2. **Question**: We investigate whether distinct circuit motifs in Transformers correspond to distinct implicit learning algorithms and whether input structure determines which algorithm is used.
3. **Evidence**: We identify two circuit motifs via activation patching that match gradient descent (R^2 = 0.94) and Bayesian ridge regression (R^2 = 0.91) respectively, with input properties predicting the active motif at 92% accuracy.
4. **Implication**: These results reveal ICL as a repertoire of algorithm-circuit pairs selected by input structure, making ICL behavior predictable from input properties.

### Introduction

- **P1**: ICL as a capability; broad significance; practical relevance
- **P2**: Circuits view of ICL (induction heads, task vectors) -- cite Olsson et al., Todd et al.
- **P3**: Algorithms view of ICL (mesa-optimization, implicit GD, Bayesian inference) -- cite Akyurek et al., von Oswald et al.
- **P4**: The gap: these two views developed independently; no work connects specific circuits to specific algorithms
- **P5**: Our contribution: we bridge the two views by showing circuit motifs correspond to algorithms, selected by input structure
- **P6**: Contribution list: (1) circuit-algorithm correspondence [R1, R2, R3], (2) selective ablation validation [R4], (3) input-driven selection mechanism [R5]

### Related Work

- **P1**: Circuit-level analysis of Transformers (mechanistic interpretability)
- **P2**: ICL as implicit algorithm execution
- **P3**: Algorithm selection and meta-learning (connects to broader ML literature)
- **P4**: Gap paragraph: no prior work maps specific circuits to specific algorithms

### Method (Section 3)

- **3.1**: Experimental setup (model, training data, evaluation protocol)
- **3.2**: Activation patching procedure for circuit identification [R7 mentioned briefly here]
- **3.3**: Algorithm prediction baselines (gradient descent derivation, Bayesian ridge derivation)
- **3.4**: Circuit-algorithm matching metric (R^2 on held-out sequences)

### Results (Section 4)

- **4.1**: Circuit motif identification -- R1 -> Figure 2
- **4.2**: Algorithm matching -- R2, R3 -> Figure 3
- **4.3**: Selective ablation -- R4 -> Table 1
- **4.4**: Input-driven selection -- R5 -> Figure 4
- **4.5**: Cross-scale consistency -- R6 -> Table 2

### Discussion (Section 6)

- **6.1**: Limitations -- R8 (adversarial failure), moderate evidence for cross-scale (R6)
- **6.2**: Implications -- ICL as algorithm repertoire; predictions for new architectures
- **6.3**: Future work -- extending to other algorithms (kernel regression, nearest neighbor), real-world data, controlling algorithm selection

### Appendix

- **A.1**: Full activation patching heatmaps per model scale
- **A.2**: Additional algorithm matching scatter plots (individual layers)
- **A.3**: Hyperparameter sensitivity analysis (patching threshold, matching metric)
- **A.4**: Adversarial distribution analysis (R8 details)

---

## Venue Calibration: ICML

- **Page budget**: 8 pages + references + appendix
- **Figure budget**: 4 figures + 2 tables in main paper (within convention)
- **Depth**: Thorough mechanistic analysis expected; ICML audience values rigorous ablations
- **Adjustment**: Include cross-scale results (Table 2) in main paper since ICML reviewers value generality. Move per-layer scatter plots to appendix.
- **Reviewer anticipation**: Likely questions about (1) generalization to real-world data, (2) other algorithms beyond GD and Bayesian, (3) computational cost of circuit analysis. Address (1) and (2) in discussion, (3) in methods.
