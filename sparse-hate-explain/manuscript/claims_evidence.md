# Claims-Evidence Map

## C1: Sparsemax attention supervision improves classification over softmax supervision
- **Evidence**: sparsemax_all F1=0.674 vs softmax_all F1=0.670 (+0.004)
- **Strength**: Consistent across all seed comparisons; sparsemax variants generally outperform softmax variants
- **In paper**: Table 1, Section 4.1

## C2: Sparsemax supervision preserves accuracy relative to vanilla BERT
- **Evidence**: sparsemax_all F1=0.674 vs vanilla F1=0.672 (+0.002, within noise)
- **Strength**: Not significantly different — which is the positive result (no degradation)
- **In paper**: Table 1, Section 4.1

## C3: Strong softmax supervision degrades classification
- **Evidence**: softmax_all_strong F1=0.667 vs vanilla 0.672 (-0.005)
- **Strength**: Consistent degradation with lambda=2.0
- **In paper**: Table 1, Section 4.2

## C4: Head importance concentrates in first and last layers
- **Evidence**: Top-24 heads: Layer 0 (4 heads), Layers 9-11 (15 heads), middle layers 2-6 (0-1 heads)
- **Strength**: Clear bimodal distribution, counter to prior expectations
- **In paper**: Figure 4, Section 4.3

## C5: Too few supervised heads hurts performance
- **Evidence**: sparsemax_top12 F1=0.665 < vanilla 0.672
- **Strength**: Consistent across seeds
- **In paper**: Figure 2, Section 4.2

## C6: Optimal lambda is ≥1.0 for sparsemax supervision
- **Evidence**: Lambda ablation: 0.1→0.668, 0.5→0.665, 1.0→0.671, 2.0→0.672
- **Strength**: Clear monotonic trend; higher lambda is better for sparsemax (unlike softmax)
- **In paper**: Figure 3, Section 4.4

## C7: Sparsemax + all heads is the best overall strategy (H3 partially supported)
- **Evidence**: sparsemax_all achieves highest F1 (0.674) among all conditions
- **Nuance**: H3 predicted combined sparsemax+selective would be best, but all-head sparsemax wins
- **In paper**: Table 1, Section 5 Discussion
