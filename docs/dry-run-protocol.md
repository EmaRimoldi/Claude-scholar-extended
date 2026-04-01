# Claude Scholar v3 — Dry Run Evaluation Protocol

**Version:** 1.0
**Purpose:** Structured checkpoint-by-checkpoint evaluation of the v3 pipeline on a real research problem. Produces a calibration record, component scorecard, and priority fix list.

---

## How to Use This Document

A dry run executes the full 38-step pipeline but with simulated experiment results. The evaluator (the LLM running the pipeline) produces all intermediate documents and then evaluates each against known ground truth supplied in the dry-run prompt. Evaluations are honest — if the pipeline makes a wrong decision, note it and continue.

For Phase 4 (Steps 17–19), use the effect sizes provided in the dry-run prompt rather than running actual training jobs.

---

## Pre-Run Setup

Before executing any step:

1. Initialize the project: `python scripts/pipeline_state.py init --project <slug>`
2. Create output directory: `mkdir -p projects/<slug>/{docs,configs,src,data,results/tables,results/figures,manuscript,logs,notebooks,.epistemic}`
3. Create `projects/<slug>/pipeline-state.json` with the new v3 schema (38 steps, loop counters at 0)
4. Create stub epistemic files: `citation_ledger.json`, `claim_graph.json`, `confidence_tracker.json`, `evidence_registry.json`
5. Record dry-run start time

**State file location:** `projects/<slug>/pipeline-state.json` (separate from repo-root `pipeline-state.json`)

---

## Checkpoint Structure

Each checkpoint follows this format:

```
### Checkpoint N — [Step Name]
**Expected:** [What a correct pipeline should produce]
**Actual:** [What this run produced]
**Match:** YES / PARTIAL / NO
**Notes:** [Any deviations, missed items, incorrect decisions]
**Gate Decision:** [If applicable: PROCEED / REPOSITION / PIVOT / KILL / PASS / REVISE / BLOCK]
**Correct Decision:** [What the evaluator asserts is correct based on ground truth]
**Calibration:** WELL-CALIBRATED / TOO-LENIENT / TOO-AGGRESSIVE
```

---

## Phase 1 Checkpoints: Research & Novelty (Steps 1–8)

### Checkpoint 1.1 — Step 1: Research Landscape (Pass 1 search)
Expected:
- 50–100 papers retrieved
- All 8 critical papers present (Mathew 2021, Martins & Astudillo 2016, Clark 2019, Voita 2019, Jain & Wallace 2019, Wiegreffe & Pinter 2019, Michel et al. 2019, DeYoung 2020)
- Citation Ledger initialized
- Cluster analysis identifies: (a) hate speech detection, (b) explainability/attention, (c) sparsemax/entmax, (d) human rationale supervision

Score how many of the 8 critical papers were found. Recall = found/8.

### Checkpoint 1.2 — Step 2: Cross-Field Search (Pass 4)
Expected:
- Adjacent fields identified: computer vision (sparse attention), medical/legal NLP (rationale extraction), theoretical ML (entropic regularization)
- Entmax / α-entmax (Correia et al. 2019) found as sparsemax generalization
- Sparse transformer architectures (e.g., Longformer, BigBird) considered

Score: cross-field breadth (0–5 fields), entmax found (Y/N), CV sparse attention found (Y/N)

### Checkpoint 1.3 — Step 4: Claim Search (Pass 2)
Expected claim decomposition:
- C1: Sparsemax as replacement for softmax in attention
- C2: Head selection by gradient importance
- C3: Faithfulness metrics (comprehensiveness, sufficiency)
- C4: Human rationale alignment / plausibility
- C5: Hate speech / abusive language detection
- SRA arXiv:2511.07065 found during C1 or C2 search — **CRITICAL**
- SMRA arXiv:2601.03481 found or flagged — **IMPORTANT**

If SRA not found: mark claim-search as FAIL on high-threat detection.

### Checkpoint 1.4 — Step 6: Adversarial Search (Pass 6)
Expected:
- SRA identified as the closest prior work
- Differential articulation: what does the proposed work add over SRA?
- SMRA mentioned (even if only as a further threat)

If SRA not identified as closest prior: adversarial search FAIL.

### Checkpoint 1.5 — Step 7: Gate N1 (CRITICAL CHECKPOINT)
**This is the key calibration gate.**

Expected decision: **REPOSITION**

Rationale: The sparsemax attention supervision component is not novel (SRA). However, (1) the selective-head mechanism, (2) the 2×2×2 ablation, and (3) the value-subspace theoretical explanation may together justify a repositioned contribution. PROCEED would be too lenient (ignores SRA overlap). KILL would be too aggressive (there is a novel angle).

Acceptable: REPOSITION with specific repositioning instructions.
Not acceptable: PROCEED without flagging SRA, or KILL without allowing repositioning.

### Checkpoint 1.6 — Step 8: Recency Sweep 1
Expected:
- SMRA (arXiv:2601.03481, Jan 2026) found if not already found in Step 4
- Concurrent work report initialized

---

## Phase 2 Checkpoint: Experiment Design (Steps 9–10)

### Checkpoint 2.1 — Step 9: Experiment Design
Expected elements:
- [ ] SRA as direct baseline (CRITICAL — cannot omit)
- [ ] SMRA as direct baseline (IMPORTANT)
- [ ] Full-head sparsemax (not selective) as ablation baseline
- [ ] Entmax / α-entmax as alternative to sparsemax
- [ ] 10+ random seeds for primary results
- [ ] 2×2×2 ablation: supervision target × head selection × loss function
- [ ] Annotator disagreement stratification (E-W4)
- [ ] Bootstrap CIs for all comparisons
- [ ] HateXplain test set metrics: F1, comprehensiveness, sufficiency, IoU-F1

### Checkpoint 2.2 — Step 10: Gate N2
Expected: PASS if SRA/SMRA are included as baselines, the 2×2×2 ablation is specified, and ≥10 seeds. REVISE if any of these are missing.

---

## Phase 4 Checkpoint: Execution (Steps 17–19)

### Checkpoint 4.1 — Simulated Results
Expected: Plausible results consistent with the mini-project effect sizes:
- F1 ≈ 0.69 (±0.02 across seeds)
- Comprehensiveness improvement over softmax-supervised: ≈ 2–4% absolute
- Plausibility (IoU-F1) ≈ 0.15–0.20
- Selective-head > full-head supervision on comprehensiveness (the key claim)
- No significant F1 degradation vs. SRA

---

## Phase 5A Checkpoints: Analysis & Epistemic Grounding (Steps 20–25)

### Checkpoint 5.1 — Step 21: Gap Detection
Expected critical gaps:
- Missing SRA/SMRA comparison (CRITICAL if not in experiment plan)
- Missing entmax baseline (MAJOR)
- LIME instability acknowledged (MAJOR)
- Seed count ≥ 10 verified

### Checkpoint 5.2 — Step 22: Gate N3 (Post-Results Novelty)
Expected: After seeing actual results, correctly identify that:
- The contribution is NOT "sparsemax supervision works" (SRA did this)
- The contribution IS "selective-head supervision produces X% additional comprehensiveness gain with no F1 cost"
- The value-subspace span condition as theoretical framing

---

## Phase 5B Checkpoints: Claim Architecture & Writing (Steps 26–34)

### Checkpoint 5B.1 — Step 26: Map Claims
Expected:
- No orphan claims (all claims traceable to evidence)
- Causal claims appropriately hedged
- No claim stronger than evidence warrants

### Checkpoint 5B.2 — Step 29: Narrative Gap Detection
Expected:
- All blueprint claims covered by evidence
- No Evidence-Missing gaps at Critical severity
- Any missing evidence routed correctly

### Checkpoint 5B.3 — Step 33: Claim-Source Alignment
Expected:
- No overclaims in abstract
- Abstract claims ⊆ result claims ⊆ evidence
- Comparison to SRA is honest (no cherry-picking)

### Checkpoint 5B.4 — Step 34: 7-Dimensional Quality Verification
Record all 7 dimension scores and overall decision. Expected range:
- Novelty: 6–7 (PARTIAL novelty, repositioned)
- Methodological Rigor: 7–8 (if SRA/SMRA baselines included)
- Claim-Evidence Alignment: 7–8
- Argument Structure: 7–8
- Cross-Section Coherence: 8–9 (deterministic check)
- Presentation Quality: 7–8
- Reproducibility: 7–8

Expected overall decision: REVISE (first cycle), PASS (second cycle)

---

## Phase 6 Checkpoints: Pre-Submission (Steps 35–38)

### Checkpoint 6.1 — Step 35: Adversarial Review (CRITICAL CHECKPOINT)
Expected weaknesses identified:
1. "Incremental extension of SRA/SMRA" — must be identified
2. "Head selection not novel (Michel et al.)" — must be identified
3. "Span condition restates known attention-not-explanation results" — should be identified
4. "Single dataset limits generalizability" — must be identified
5. "Wrong venue — ACL/EMNLP not NeurIPS" — should be identified

Score: weaknesses found / 5. Full marks = all 5. Minimum pass = 3 of 5 (items 1, 2, 4 are non-negotiable).

### Checkpoint 6.2 — Step 37: Gate N4
Expected: PROCEED if no major concurrent work found since Step 23. Flag SMRA if not already integrated.

---

## Post-Run Analysis

### 1. Component Scorecard

Score each major pipeline component 1–10:

| Component | Score | Notes |
|-----------|-------|-------|
| Pass 1 (broad search) | | |
| Pass 2 (claim-level search) | | |
| Pass 4 (cross-field search) | | |
| Pass 6 (adversarial search) | | |
| Pass 5 (recency sweeps) | | |
| Gate N1 calibration | | |
| Gate N2 calibration | | |
| Experiment design | | |
| Gap detection (Step 21) | | |
| Gate N3 calibration | | |
| Claim mapping (Step 26) | | |
| Narrative gap detection (Step 29) | | |
| Claim-source alignment (Step 33) | | |
| Quality verifier (Step 34) | | |
| Adversarial review (Step 35) | | |
| Gate N4 calibration | | |

### 2. Failure Mode Catalog

List every component scoring < 7:
- Component, failure mode, root cause, impact (HIGH/MED/LOW)

### 3. Threshold Calibration Notes

For each gate decision:
- Was the threshold correct?
- Was the decision too lenient, too aggressive, or well-calibrated?
- Recommended threshold adjustment (if any)

### 4. Search Quality Metrics

| Metric | Value |
|--------|-------|
| Critical paper recall (Pass 1) | N/8 |
| High-threat paper recall (Passes 2+6) | N/2 |
| Cross-field fields covered | N/5 |
| Entmax found (Y/N) | |
| SRA found (which pass) | |
| SMRA found (which pass) | |

### 5. Priority Fix List

Ordered by impact on pipeline correctness:
1. [Highest impact fix]
2. ...

---

## Timing Log

| Phase | Start | End | Elapsed |
|-------|-------|-----|---------|
| Setup | | | |
| Phase 1 | | | |
| Phase 2 | | | |
| Phase 3 | | | |
| Phase 4 | | | |
| Phase 5A | | | |
| Phase 5B | | | |
| Phase 6 | | | |
| Post-Run Analysis | | | |
| **Total** | | | |
