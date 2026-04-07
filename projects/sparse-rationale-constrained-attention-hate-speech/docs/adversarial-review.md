# Adversarial Review: Sparse Rationale-Constrained Attention for Hate Speech Detection

Simulated hostile NeurIPS reviewers. Paper under review:
`manuscript/paper.tex`

---

## Reviewer A — Methodology Skeptic (Faithfulness metric gaming)

**Rating: Weak Reject (4)**

### Main concern
The headline +111% comprehensiveness AOPC gain is not evidence of genuine
faithfulness improvement; it is a near-tautological consequence of sparsemax's
structural zeros combined with the MSE-to-rationale supervision. When you
delete the rationale tokens at evaluation (the comprehensiveness operator),
C4's attention mass over the remaining tokens is *exactly zero by construction*
(Proposition 1), so the post-mask logits collapse mechanically. This is
metric-gaming at the operator level, not a mechanistic claim about what the
model "uses." The paper itself concedes the logic of the chain M1 -> M2 -> M3
(lines 312-324), but never asks the obvious counterfactual: would a
non-attention-based classifier that simply *hard-masks* non-rationale tokens at
inference produce an even larger "comprehensiveness" number while being
trivially uninformative as an explanation?

### Specific attack points
- **Lines 81-84 (Prop. 1)** and **lines 207-210**: authors explicitly state
  C4 produces structural zeros at every site. By definition, removing the
  rationale leaves the model nothing to attend to. Comprehensiveness AOPC is
  therefore a circular measurement.
- **Line 323**: "nothing is left for the model to attend to, so the prediction
  confidence collapses" — this is the authors admitting the metric is
  mechanically determined.
- **Lines 326-334**: C3 (sparsemax-only, *no* supervision) still beats C2 on
  swap KL, showing the operator alone drives a large share of "faithfulness"
  signal. The paper does not report C3 comprehensiveness/sufficiency (Table 1
  line 249 shows "---"), precisely where a control is needed.
- **Line 288**: plausibility = 0 for all conditions. The one ERASER metric
  that would cross-validate faithfulness against human rationales is absent.
- **Line 386**: n=5, so the "d=8.36" is computed on 5 paired differences and
  is not interpretable as a population effect size.

### Strongest authors' counter
Proposition 1 shows structural zeros *at training time* for the attention map,
but comprehensiveness AOPC is computed by *input-space masking of tokens*, not
attention masking. A model with structural attention zeros on non-rationale
tokens could still encode non-rationale information through embeddings,
position encodings, and downstream MLP mixing — so the "collapse" is
empirical, not tautological. The authors should add a **C3 comprehensiveness
number** (operator-only control): if C3 alone produces a comparable AOPC, the
reviewer is right; if not, the gain is attributable to supervision, not to
sparsemax structure.

---

## Reviewer B — Empirical Rigor Skeptic (Statistics and scope)

**Rating: Reject (3)**

### Main concern
The statistical scaffolding is too thin to support headline claims. The
Wilcoxon p = 0.031 is not "significant at p = 0.031" — it is the **floor
p-value at n = 5**, meaning any monotone dominance gives exactly that number
regardless of effect magnitude. The TOST at p = 0.047 is borderline at a
margin of +/- 1.0 pp chosen by the authors themselves. H4 is missed
(1.47x vs pre-registered 2x). Plausibility is zero on the single dataset
evaluated. Single backbone (BERT-base). Single dataset (HateXplain). Five
seeds. Any one of these would be acceptable; in combination they are not.

### Specific attack points
- **Line 268**: "statistic 15 with p = 0.031 (the smallest possible p-value
  at n = 5)" — authors literally state this is the minimum attainable p.
  The test has no power to distinguish a +111% gain from a +15% gain.
- **Line 260-262**: TOST p = 0.047 at the pre-chosen +/- 1.0 pp margin. Why
  1.0 pp? No justification. At +/- 0.5 pp the test would fail.
- **Lines 275-282 (H4)**: pre-registered 2x threshold missed at 1.47x. The
  post-hoc explanation (operator/alignment cancellation) is unverifiable and
  was not part of the preregistration.
- **Lines 284-288**: plausibility = 0 across all conditions. The paper
  dismisses this as "dataset artefact," but HateXplain is the paper's *only*
  dataset. This means the only human-alignment check is unavailable.
- **Lines 378-386 (Limitations)**: authors themselves acknowledge single
  dataset, single backbone, n = 5.
- **Lines 218-219**: only seeds {13, 17, 29, 42, 71}; no sensitivity to
  hyperparameter lambda = 0.1.

### Strongest authors' counter
Per-seed monotone dominance (line 291-294: every seed shows C4 > C2 by at
least 0.13) is a stronger claim than the Wilcoxon p alone; with five
independent seeds, probability of monotone dominance under H0 is 1/32
= 0.031, which *is* the correct frequentist reading, and the minimum-
attainable-p objection is a known but non-fatal property of exact rank
tests. The H4 miss is reported honestly (not rebranded). To strengthen:
add (i) a second dataset (Civil Comments or SBIC rationale subsets),
(ii) bootstrap CI on per-seed differences, (iii) lambda sensitivity curve.

---

## Reviewer C — Novelty Skeptic (Theoretical contribution)

**Rating: Weak Reject (4)**

### Main concern
Stripped of rhetoric, the contribution is: "apply sparsemax to all heads of
all layers instead of one head, and use MSE instead of KL." That is a
two-line change to a prior method (SRA, Eilertsen 2025). Proposition 1 is
presented as the theoretical backbone, but it is a restatement of a
well-known property of sparsemax (Martins & Astudillo 2016, Sec. 2.3) — exact
zeros below a threshold — dressed up with an MSE minimizer that is trivially
the rationale-uniform distribution. Nothing in the proposition connects the
structural-zeros property to a *quantitative* bound on comprehensiveness,
and the "residual escape route" is presented as a mechanism but never
formally characterized, measured, or bounded. The paper is an ablation
study of SRA, not a new method.

### Specific attack points
- **Lines 74-92 (Contribution)**: the "Method" contribution is (a) apply
  sparsemax everywhere, (b) MSE instead of KL, (c) supervise every layer.
  Each of these changes is a single configuration knob.
- **Lines 188-205 (Proposition 1)**: the proof sketch relies entirely on
  the closed-form `a_i = max(z_i - tau, 0)` from Martins 2016. The MSE
  optimality argument (line 199-201) is elementary.
- **Line 208-210**: "Proposition 1 is the formal reason ... the all-layer
  combination matters" — but the proposition is stated pointwise (per head);
  there is no theorem that aggregates across layers, no bound on how much
  residual-stream leakage there is, and no rate for the improvement.
- **Lines 69-72**: "residual escape route" is named but never formalized
  (no definition of the leakage measure, no upper/lower bound).
- **Lines 362-366 (Related Work)**: the authors correctly identify SRA as
  "the closest precedent" — C4 differs by two hyperparameters (operator site
  set and loss form).

### Strongest authors' counter
The contribution is *structural-mechanistic* rather than algorithmic: the
paper diagnoses *why* prior SRA underperforms (single-head supervision is
dominated by eleven unconstrained residual paths), provides a falsifiable
mechanism (M1->M2->M3), and validates it with a layerwise ablation (C5 top-6
vs C4 all-12). "Simple fix plus mechanism" is a valid NeurIPS contribution
pattern when the mechanism was previously unrecognized. The "trivial
configuration change" framing is reductive: the prior work (Eilertsen 2025)
explicitly argued one supervised head was sufficient; refuting that claim
with a structural explanation is the contribution.

---

## Author Response Strategy — Top 3 Pre-emptive Additions

To reviewer-proof the paper **before submission**, prioritize:

### 1. Add C3 faithfulness numbers (kills Reviewer A)
Table 1 currently shows `---` for C3 on comprehensiveness and sufficiency
(line 249). **Fill those cells.** If C3 (sparsemax-only, no supervision)
produces comprehensiveness AOPC close to C4, the tautology critique is
fatal; if C3 is close to C2 or C1, it proves the gain comes from
supervision + all-layer coverage, not from the sparsemax operator. Either
way, reporting it is mandatory. Add one paragraph in Section 5.1 explicitly
decomposing "operator effect" vs "supervision effect" using C1, C3, C2, C4
as a 2x2.

### 2. Add a second dataset or an out-of-distribution faithfulness probe
(kills Reviewer B)
The single-dataset weakness is the paper's most exploitable flaw. Options
in order of cost:
- **Cheapest**: rerun C1/C2/C4 on Social Bias Frames (SBIC) with its
  rationale-like target groups, or on the Civil Comments toxic-span
  subset. Even 3 seeds would be enough to show the comprehensiveness gain
  is not HateXplain-specific.
- **Complementary**: add a **lambda sensitivity sweep** (lambda in
  {0.03, 0.1, 0.3, 1.0}) on HateXplain. Even one-seed curves strengthen
  the claim that the effect is not a single-hyperparameter artifact.
- Also add bootstrap 95% CI on per-seed differences to supplement the
  minimum-p Wilcoxon.

### 3. Formalize the residual escape route (kills Reviewer C)
Proposition 1 is pointwise and Reviewer C is right that it is thin. Add a
**Proposition 2** (or lemma) that either:
- bounds the L1 mass that non-rationale tokens receive in the `[CLS]` row
  of the final-layer attention, as a function of how many layers are
  supervised; OR
- empirically quantifies "residual leakage" by measuring the L1 mass on
  non-rationale tokens at each layer for C2 vs C4 (a single new figure
  plotted from existing checkpoints). This operationalizes the "escape
  route" metaphor and converts a rhetorical argument into a measurable
  quantity. The layerwise leakage curve is likely already computable from
  saved attention maps and would be a decisive addition.

### Secondary fixes (if space permits)
- Justify the +/- 1.0 pp TOST margin with reference to prior HateXplain
  work (variance of reported F1 across papers is typically >= 1.0 pp).
- Rename "H4 missed" paragraph to include a **power analysis**: at n=5,
  detecting a 2x ratio with the observed variance would have required ~8
  seeds. This reframes H4 as underpowered, not disconfirmed.
- Add one sentence in the abstract stating the scope (single dataset,
  BERT-base) to pre-empt Reviewer B's opening line.

---

**Overall simulated verdict**: 3 / 4 / 4 — borderline reject without
revisions. With the three additions above, the paper moves to a likely
6 / 5 / 6 range (weak accept to borderline).
