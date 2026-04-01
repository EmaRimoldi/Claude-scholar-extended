---
name: paper-quality-check
description: Audit a research paper against 8 quality dimensions (claim-evidence alignment, statistical rigor, baseline completeness, generalizability, mechanistic validation, error analysis, presentation accuracy, reproducibility). Can be invoked at any pipeline stage to catch issues early.
tags: [Quality, Review, Research, Verification]
---

# Paper Quality Check Skill

This skill performs a comprehensive quality audit of a research paper at any stage of the pipeline. It can check partial artifacts (experiment plans, results, drafts) or complete manuscripts.

## When to Use

- After `/design-experiments` — check metric coverage, baseline completeness, statistical plan
- After `/analyze-results` — check statistical rigor, contradiction detection, error analysis
- After `/produce-manuscript` — full quality review before submission
- Anytime the user says "check quality", "review paper", "audit", or "is this ready?"

## Quality Dimensions

### 1. Claim-Evidence Alignment

**Check at design stage:**
- Every key term in the research question has a corresponding metric in the experiment plan
- "Faithfulness" → comprehensiveness, sufficiency, AOPC, attention-IG correlation
- "Accuracy" → macro-F1, per-class F1, accuracy
- "Plausibility" → token-F1, AUPRC vs human rationales
- "Sparsity" → attention entropy, % zero weights

**Check at results stage:**
- Every hypothesis has a verdict (supported/contradicted/inconclusive)
- No hypothesis is claimed as supported without statistical evidence
- Contradicted hypotheses are honestly reported

**Check at manuscript stage:**
- Every claim in abstract has a corresponding result
- Title keywords all map to measured metrics
- No overclaiming (claims stronger than evidence)

### 2. Statistical Rigor

**Minimum requirements:**
- ≥ 5 seeds per condition (10 for primary comparison)
- Formal statistical test for every comparison (bootstrap, Wilcoxon, permutation)
- 95% confidence intervals reported
- Effect sizes (Cohen's d) for all comparisons
- Power analysis if effect sizes are small (d < 0.5)

**Red flags:**
- Claims of "improvement" with overlapping confidence intervals
- No p-values or CI anywhere in the paper
- n < 5 seeds for any published comparison

### 3. Baseline Completeness

**Required baselines:**
- Vanilla/no-intervention baseline
- For explanation methods: at least one gradient-based alternative (IG, SHAP, LIME)
- For each method component: ablation removing that component
- At least one "obvious alternative" a reviewer would suggest

**Missing baseline detection:**
- If paper uses attention for explanations but doesn't compare with IG → flag
- If paper modifies training but doesn't compare with post-hoc methods → flag

### 4. Generalizability

- Multiple datasets preferred (at least 2)
- Multiple model sizes or architectures preferred
- If single dataset/model: must be discussed as limitation
- Cross-lingual or cross-domain evaluation if applicable

### 5. Mechanistic Validation

- If claiming attention is faithful: adversarial attention swap test required
- If claiming causal relationships: intervention experiments required
- Ablation studies must isolate each component independently
- Correlation claims must not be stated as causation

### 6. Error Analysis

**Required stratifications:**
- Per-class performance breakdown
- At least one additional dimension (sample length, difficulty, annotator agreement)
- Failure case analysis: characterize what the model gets wrong

### 7. Presentation Accuracy

- Abstract matches results (no invented claims)
- Numbers in text match tables exactly
- Contributions accurately reflect what was achieved
- Limitations section is honest and complete

### 8. Reproducibility

- All hyperparameters listed
- Random seeds specified
- Hardware/compute described
- Code availability mentioned

## Output Format

Generate a quality report with:
1. Score for each dimension (1-10)
2. Specific findings (what's good, what's missing)
3. Required fixes (blocking issues)
4. Recommendations (non-blocking improvements)
5. Overall verdict: PASS (all ≥ 5, criticals ≥ 6) or FAIL

## Integration with Pipeline

This skill is automatically invoked by:
- `/verify-paper` command (**pipeline step 34** in v3; replaces `/quality-review`)
- `/validate-setup` when checking experiment plan quality
- Any manual invocation

The structured verifier writes **`manuscript/paper-quality-report.md`** (see [`commands/verify-paper.md`](../../commands/verify-paper.md)). Legacy `/quality-review` used `manuscript/quality-review.md`; prefer `/verify-paper` before `/compile-manuscript`.
