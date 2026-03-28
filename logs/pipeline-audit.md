# Pipeline Audit: Tracing 8 Paper Weaknesses to Pipeline Origins

**Date**: 2026-03-28
**Auditor**: Claude Opus 4.6 (automated trace)
**Scope**: Full research pipeline in Claude-scholar-extended, tracing 8 weaknesses of a hypothetical paper (attention-based explainability on HateXplain with BERT-base) back to specific pipeline commands, skills, hooks, and structural gaps.

---

## Methodology

Each weakness is traced through the 18-step pipeline defined in `/run-pipeline`:

```
research-init -> check-competition -> design-experiments -> scaffold ->
build-data -> setup-model -> implement-metrics -> validate-setup ->
plan-compute -> run-experiment -> collect-results -> analyze-results ->
map-claims -> position -> story -> produce-manuscript -> compile-manuscript -> rebuttal
```

For each weakness, the trace identifies:
- **Root cause**: The pipeline step where the weakness was introduced
- **Contributing factors**: Other steps that amplified or failed to catch the issue
- **Missing gate**: The check that should have existed but did not
- **Fix needed**: Structural change to prevent recurrence

---

## W1: "No faithfulness metrics despite title claim"

**Description**: Title claims "Improves Faithfulness" but NO faithfulness metrics are reported (only macro-F1/accuracy).

```
W1: "No faithfulness metrics despite title claim"
|-- Root cause: experiment-design skill (Step 3: /design-experiments)
|   The experiment-design skill (skills/experiment-design/SKILL.md) produces
|   experiment-plan.md with a "Metrics" section listing "Primary metric,
|   secondary metrics, with justification." However, the skill has NO
|   requirement that chosen metrics align with the paper's central claim
|   or title. It selects metrics based on hypothesis-formulation output
|   and community convention, not based on the semantic content of the
|   contribution statement. If the hypothesis says "improve classification
|   with better attention" and the metric section lists macro-F1/accuracy,
|   no gate verifies that "faithfulness" -- the concept in the title --
|   is operationalized as a measurable quantity.
|
|-- Contributing: hypothesis-formulation skill (pre-Step 3)
|   The hypothesis-formulation skill (skills/hypothesis-formulation/SKILL.md)
|   defines "Success/Failure Criteria" with "Metric selection: Primary metric
|   with justification, secondary metrics." But it does not cross-check that
|   the metric set covers ALL key terms in the research question or planned
|   title. A hypothesis like "attention heads improve faithfulness" can pass
|   with only accuracy as the primary metric if faithfulness is treated as
|   an informal description rather than a measurable construct.
|
|-- Contributing: measurement-implementation skill (Step 7: /implement-metrics)
|   The measurement-implementation skill (skills/measurement-implementation/SKILL.md)
|   faithfully implements whatever metrics appear in experiment-plan.md. It has
|   a rich catalog (classification, similarity, scaling, information-theoretic)
|   but NO catalog entry for faithfulness metrics (comprehensiveness, sufficiency,
|   AOPC, degradation curves). The skill cannot implement what was never requested.
|
|-- Contributing: claim-evidence-bridge skill (Step 13: /map-claims)
|   The claim-evidence-bridge skill (skills/claim-evidence-bridge/SKILL.md)
|   explicitly checks for "Alternative interpretations: Confounds or
|   alternative explanations" and rates evidence strength as Strong/Moderate/
|   Weak/Unsupported. If the title claims faithfulness but no faithfulness
|   metric exists, this skill SHOULD flag the title claim as "Unsupported."
|   However, the skill depends on the user or pipeline to enumerate claims
|   accurately -- if "faithfulness" is bundled into a vague claim like
|   "improves explainability," the specific metric gap is not surfaced.
|
|-- Contributing: paper-self-review skill (post-Step 16)
|   The SECTION-CHECKLIST.md reference includes: "the title does not convey
|   stronger certainty than the weakest primary claim's evidence level."
|   This check SHOULD catch a title containing "faithfulness" when no
|   faithfulness metric exists. However, paper-self-review is NOT a
|   mandatory pipeline step -- it is triggered manually and has no
|   dedicated step in the 18-step /run-pipeline sequence.
|
|-- Missing gate: Title-to-metric consistency check
|   No pipeline step requires that every key term in the planned title
|   or abstract is backed by at least one implemented metric. The
|   claim-evidence-bridge operates on claims, not on title keywords.
|   There is no "title audit" step.
|
|-- Fix needed:
|   1. Add a "key-term coverage" check in experiment-design: extract
|      key terms from the hypothesis/title and verify each maps to at
|      least one metric in the plan.
|   2. Add faithfulness-specific metrics (AOPC, sufficiency,
|      comprehensiveness) to the measurement-implementation catalog
|      in references/analytical-reference-catalog.md.
|   3. Make paper-self-review a mandatory Step 17 in /run-pipeline,
|      not an optional manual invocation.
|   4. Add a title-claim consistency sub-check to claim-evidence-bridge
|      that parses the planned title and verifies each substantive
|      term maps to evidence.
```

---

## W2: "Only 3 random seeds -- insufficient statistical power, no formal tests, tiny effect sizes"

**Description**: Only 3 random seeds used, insufficient statistical power, no formal significance tests reported, tiny effect sizes.

```
W2: "Only 3 random seeds -- insufficient statistical power"
|-- Root cause: experiment-design skill (Step 3: /design-experiments)
|   The experiment-design skill explicitly addresses seed count in section 3
|   "Sample Size & Seeds" and includes a power analysis section. However,
|   the skill explicitly allows a "convention-based default" of "3 seeds
|   minimum for a quick validation pass" when no prior effect size is
|   available (the common case). The skill states: "Sample size is based
|   on community convention, not statistical power. If the effect is small,
|   more runs may be needed." This caveat is logged but does NOT block
|   proceeding with 3 seeds. The skill treats 3 seeds as acceptable for
|   quick validation but never enforces escalation to 5+ seeds for the
|   full sweep.
|
|-- Contributing: results-analysis skill (Step 12: /analyze-results)
|   The results-analysis skill (skills/results-analysis/SKILL.md) has a
|   strong "Non-negotiable quality bar" including: "Report complete
|   statistics... 95% CI, effect size, multiple-comparison handling" and
|   a failure mode policy: "too few runs -> effect size may be unstable;
|   report this limitation." The skill SHOULD flag 3 seeds as
|   insufficient for inferential claims. However, it reports the
|   limitation rather than blocking the pipeline. The analysis proceeds
|   with descriptive statistics and a caveat.
|
|-- Contributing: measurement-implementation skill (Step 7: /implement-metrics)
|   The measurement-implementation skill implements statistical tests
|   (paired t-test, Wilcoxon, bootstrap CI, permutation test) and states:
|   "default to nonparametric if n < 30." With n=3, all parametric tests
|   are invalid. The skill implements the tests correctly but the tests
|   were never invoked in the final paper because the analysis skill
|   only reported limitations rather than forcing their use.
|
|-- Contributing: setup-validation skill (Step 8: /validate-setup)
|   The setup-validation skill verifies the pipeline produces correct
|   output but does NOT check whether the planned seed count is
|   statistically adequate for the planned comparisons. It runs 1 seed
|   as a smoke test and passes.
|
|-- Missing gate: Minimum seed enforcement for publication claims
|   The experiment-design skill flags 3 seeds as a limitation but no
|   downstream step blocks manuscript production when seed count is
|   below a publication-quality threshold. The claim-evidence-bridge
|   could flag claims as "Weak" due to 3-seed evidence, but this
|   depends on the analysis skill surfacing the limitation prominently.
|
|-- Fix needed:
|   1. Add a "publication-readiness" gate in experiment-design that
|      distinguishes "quick validation" (3 seeds OK) from "full sweep
|      for publication" (minimum 5 seeds, ideally 10+ for small effects).
|   2. Add a hard warning in results-analysis: if seed count < 5 and
|      the user intends to publish, block inferential claims and
|      require explicit override.
|   3. Add seed-count-to-effect-size validation: if observed effect
|      size is small (Cohen's d < 0.5), warn that 3 seeds cannot
|      reliably detect it.
|   4. Make results-analysis require running formal statistical tests
|      (not just reporting limitations) before passing to map-claims.
```

---

## W3: "No comparison with IG as alternative explanation method"

**Description**: Integrated Gradients (IG) is used for head selection but never evaluated as a rationale extractor -- a missing baseline.

```
W3: "No comparison with IG as alternative explanation method"
|-- Root cause: experiment-design skill (Step 3: /design-experiments)
|   The experiment-design skill's "Baseline Selection" section requires:
|   "Trivial baseline, Standard baseline, SOTA baseline, Ablation baseline"
|   with a "Fairness checklist: Same preprocessing, splits, hyperparameter
|   budget." However, it does NOT require that every tool used internally
|   in the proposed method also be evaluated as a standalone baseline.
|   IG is used as a component (for head selection) but not listed as a
|   comparison method. The skill's baseline selection logic focuses on
|   published methods, not on internal components repurposed as
|   competitors.
|
|-- Contributing: novelty-assessment skill (pre-Step 3)
|   The novelty-assessment skill compares the proposed contribution
|   against 3-5 closest prior works. If IG-based rationale extraction
|   is a known approach in the field (it is -- e.g., DeYoung et al. 2020),
|   this skill should have flagged it as a required comparison. The
|   "Differentiation Matrix" would reveal that the paper's attention-based
|   approach directly competes with gradient-based approaches.
|
|-- Contributing: contribution-positioning skill (Step 14: /position)
|   The contribution-positioning skill anticipates reviewer objections
|   including "Missing comparison with [Z]" and prepares responses.
|   The objection template states: "Either add the baseline or explain
|   why the comparison is not applicable." If IG was identified as a
|   closest work, this skill would have flagged the missing comparison.
|   But it operates on whatever closest works were selected upstream.
|
|-- Contributing: paper-self-review SECTION-CHECKLIST
|   The checklist includes: "baselines and ablations are interpretable"
|   but does not specifically check "every method component used internally
|   is also evaluated as an alternative approach."
|
|-- Missing gate: Internal-component-as-baseline check
|   No pipeline step requires that tools used as components within the
|   method (e.g., IG for head selection) also be evaluated as standalone
|   alternatives. This is a specific blind spot: the method uses IG to
|   select heads, which implicitly assumes IG is a good explanation
|   method, yet never tests whether IG alone is sufficient.
|
|-- Fix needed:
|   1. Add a "component-as-competitor" check in experiment-design: for
|      every external method used as a component, require either (a)
|      evaluating it as a standalone baseline, or (b) explicitly
|      justifying why it is not a valid comparison.
|   2. Strengthen novelty-assessment to flag gradient-based explanation
|      methods (IG, SHAP, LIME) as mandatory comparisons when the
|      paper's domain is explainability/interpretability.
|   3. Add a reviewer objection specifically about "tools used internally
|      but not compared against" in contribution-positioning.
```

---

## W4: "Single dataset (HateXplain), single model (BERT-base) -- no generalizability"

**Description**: Evaluation on only one dataset and one model architecture, with no evidence of generalization.

```
W4: "Single dataset, single model -- no generalizability"
|-- Root cause: experiment-design skill (Step 3: /design-experiments)
|   The experiment-design skill includes "Datasets & splits: Which
|   datasets, how to split, cross-validation strategy" in its output
|   but does NOT enforce a minimum number of datasets or models. The
|   skill is designed to be resource-aware ("Resource-constrained: need
|   to maximize information from limited GPU budget") and will accept
|   a single-dataset plan if the user provides one. The "Execution
|   Ordering" section prioritizes: "Extended experiments last: Secondary
|   hypotheses, additional datasets" -- placing generalization testing
|   at the lowest priority, easily cut when resources are limited.
|
|-- Contributing: hypothesis-formulation skill (pre-Step 3)
|   If the hypothesis is scoped to "BERT-base on HateXplain," the
|   hypothesis-formulation skill will not expand it to other datasets
|   or models. The skill formulates hypotheses from the user's
|   description and does not independently assess generalizability
|   scope.
|
|-- Contributing: contribution-positioning skill (Step 14: /position)
|   The contribution-positioning skill includes a "Limited evaluation"
|   reviewer objection pattern: "Few datasets or metrics -> Justify
|   dataset choice, discuss generalization evidence." This would flag
|   the issue, but only at the writing stage (Step 14), far too late
|   to run additional experiments. The response strategy is defensive
|   ("justify") rather than corrective ("run more experiments").
|
|-- Contributing: claim-evidence-bridge skill (Step 13: /map-claims)
|   Evidence Strength Criteria state: "Moderate: Significant but small
|   effect, OR significant but only on one dataset." A single-dataset
|   result would be rated "Moderate" at best. However, this rating
|   leads to hedged language, not to running more experiments.
|
|-- Contributing: story-construction skill (Step 15: /story)
|   The venue calibration section states that NeurIPS/ICML/ICLR expect
|   "Thorough experiments." A single-dataset, single-model evaluation
|   violates this expectation, but the skill's response is to adjust
|   the narrative scope, not to trigger additional experiments.
|
|-- Missing gate: Minimum generalization threshold for target venue
|   No pipeline step enforces a minimum dataset/model count calibrated
|   to the target venue. The experiment-design skill does not have a
|   venue-aware "minimum scope" check. The weakness is flagged late
|   (at writing) but never early enough (at design) to change the
|   experiment plan.
|
|-- Fix needed:
|   1. Add venue-calibrated generalization requirements in experiment-design:
|      e.g., top venues require >= 2 datasets and >= 2 model sizes for
|      claims about a general method.
|   2. Add a "generalization scope" checkpoint between results-analysis
|      and map-claims: before writing, explicitly ask whether the
|      evidence supports general vs. dataset-specific claims, and
|      trigger additional experiments if the claim scope exceeds the
|      evidence scope.
|   3. Surface the "Moderate" evidence rating from claim-evidence-bridge
|      as a blocking issue in the pipeline, not just hedged language.
```

---

## W5: "No adversarial attention test -- Jain & Wallace 2019 cited but their test never applied"

**Description**: The paper cites Jain & Wallace (2019) on attention not being explanation, but never applies their adversarial permutation test.

```
W5: "No adversarial attention test -- Jain & Wallace 2019 cited but test never applied"
|-- Root cause: experiment-design skill (Step 3: /design-experiments)
|   The experiment-design skill designs ablation studies but its "Ablation
|   Planning" section focuses on "Component identification: Which parts of
|   the method are novel?" It does not include a category for
|   "adversarial robustness tests from cited work." If a paper cites a
|   known critique (Jain & Wallace 2019), the experiment plan should
|   include the critic's test as a mandatory validation. But the skill
|   has no mechanism to extract cited critiques and convert them into
|   required experiments.
|
|-- Contributing: research-ideation / literature-reviewer (Step 1)
|   The research-ideation skill and literature-reviewer agent identify
|   related work and gaps. If Jain & Wallace (2019) was identified as
|   a key critique during literature review, it should have been flagged
|   as requiring a direct response (i.e., running their test). However,
|   the output is a literature review document, not a mandatory
|   experiment checklist.
|
|-- Contributing: novelty-assessment skill (pre-Step 3)
|   The novelty-assessment skill should identify Jain & Wallace as
|   "closest work" since it directly challenges the premise of
|   attention-as-explanation. The differentiation matrix should then
|   require addressing their specific critique experimentally, not
|   just citing it.
|
|-- Contributing: manuscript-production skill (Step 16: /produce-manuscript)
|   The manuscript-production skill's Discussion section template
|   requires "Alternative explanations paragraph" and "What would make
|   this conclusion false?" (MANDATORY paragraph). This is the right
|   structural requirement, but it operates at the prose level, not
|   the experimental level. By Step 16, it is too late to run the
|   adversarial test.
|
|-- Missing gate: Cited-critique-to-experiment mapping
|   No pipeline step requires that cited critiques of the paper's
|   premise be addressed experimentally, not just rhetorically. The
|   skill for "cited work -> required validation experiment" does not
|   exist.
|
|-- Fix needed:
|   1. Add a "critical references" section in hypothesis-formulation:
|      for each hypothesis, identify known published critiques and
|      require either (a) an experiment addressing the critique, or
|      (b) an explicit argument for why the critique does not apply.
|   2. Add an adversarial/robustness test category in experiment-design
|      alongside ablations: "For attention-based methods, apply the
|      Jain & Wallace adversarial permutation test."
|   3. Add a "cited-but-not-tested" check in claim-evidence-bridge:
|      scan the reference list for papers that critique the paper's
|      core premise and verify each has a corresponding experiment.
```

---

## W6: "Head selection presented as contribution but results show it doesn't work"

**Description**: Head selection is presented as a contribution, but sparsemax-all (no selection) beats all selective variants -- the contribution is a negative result.

```
W6: "Head selection presented as contribution but results show it doesn't work"
|-- Root cause: claim-evidence-bridge skill (Step 13: /map-claims)
|   The claim-evidence-bridge skill rates evidence strength as Strong/
|   Moderate/Weak/Unsupported and recommends scope decisions: "Remove:
|   Claims with weak/no evidence (move to future work)." If head
|   selection is claimed as a contribution but sparsemax-all beats it,
|   the evidence for head selection as a contribution is "Unsupported"
|   or at best "Weak." The skill SHOULD flag this and recommend either
|   removing the claim or reframing head selection as a negative finding.
|   HOWEVER: this depends on the analysis skill surfacing the comparison
|   clearly (sparsemax-all vs. selective variants), and on the user
|   faithfully reporting it. If the comparison is buried in an ablation
|   table, the claim-evidence-bridge may not catch the reversal.
|
|-- Contributing: results-analysis skill (Step 12: /analyze-results)
|   The results-analysis skill includes a "Final QA gate" requiring
|   "the primary comparison question is explicit" and "limitations and
|   blockers are explicit." If sparsemax-all outperforms selective
|   variants, this should be flagged as a key finding that contradicts
|   the planned contribution. However, the skill does not specifically
|   check "does the proposed method beat its own ablated version?"
|   It reports numbers but may not flag the reversal as a contribution-
|   threatening finding.
|
|-- Contributing: story-construction skill (Step 15: /story)
|   The story-construction skill triages results into Primary/Supporting/
|   Diagnostic/Null-Negative. The quality gate requires "Null/negative
|   results are placed in discussion or appendix (not silently dropped)."
|   Head selection performing worse than sparsemax-all is a negative
|   result and should be triaged as "Null/Negative" -- but only if
|   the analysis explicitly frames it as such.
|
|-- Contributing: manuscript-production skill (Step 16: /produce-manuscript)
|   The Discussion template requires "What would make this conclusion
|   false?" (MANDATORY). If head selection is claimed as a contribution,
|   the answer to "what would falsify this?" is "sparsemax-all beating
|   all selective variants" -- which is exactly what happened. The
|   manuscript production skill should flag this contradiction if the
|   claim-evidence-bridge has rated it as unsupported.
|
|-- Missing gate: Ablation-contradicts-contribution detection
|   No pipeline step specifically checks whether an ablation result
|   (removing the proposed component) outperforms the full method.
|   This is the most damning type of negative result -- the proposed
|   contribution makes things worse -- and it should trigger an
|   automatic reframing requirement.
|
|-- Fix needed:
|   1. Add an "ablation reversal" detector in results-analysis: if
|      removing a proposed component improves performance, flag it as
|      a BLOCKING finding that requires reframing the contribution.
|   2. Add a specific check in claim-evidence-bridge: for each claimed
|      contribution, verify it is not contradicted by ablation results.
|      If the "full method minus component X" outperforms the full
|      method, the claim about component X must be removed or reframed.
|   3. Add a "negative result reframing" option in story-construction:
|      when a claimed contribution is a negative result, offer a
|      reframing template (e.g., "We find that head selection does
|      not improve over full sparsemax, suggesting that...").
```

---

## W7: "No error analysis or stratification"

**Description**: No per-class breakdown, no annotator agreement analysis, no stratification by difficulty or subgroup.

```
W7: "No error analysis or stratification"
|-- Root cause: experiment-design skill (Step 3: /design-experiments)
|   The experiment-design skill plans baselines, ablations, and metrics
|   but has NO section on error analysis, stratification, or per-class
|   breakdown. The skill's output template does not include an "Error
|   Analysis Plan" section. The closest it gets is "Ablation Planning"
|   which analyzes component contributions, not prediction error
|   patterns.
|
|-- Contributing: results-analysis skill (Step 12: /analyze-results)
|   The results-analysis skill requires "one supporting figure (training
|   dynamics / ablation / breakdown / error analysis)" -- it explicitly
|   mentions "error analysis" as an option for the supporting figure.
|   However, this is listed as ONE option among several, not as a
|   mandatory requirement. The skill says "breakdown" but does not
|   enforce per-class stratification or annotator agreement analysis.
|   The skill's failure mode policy does not list "no error analysis"
|   as a blocker.
|
|-- Contributing: measurement-implementation skill (Step 7: /implement-metrics)
|   The measurement-implementation skill catalogs classification metrics
|   including "F1 (macro/micro/weighted)" but does not include per-class
|   metrics, confusion matrix generation, or annotator agreement metrics
|   (Fleiss' kappa, Krippendorff's alpha) in its reference catalog.
|   These are standard analysis tools for hate speech datasets but are
|   absent from the skill's vocabulary.
|
|-- Contributing: story-construction skill (Step 15: /story)
|   The story-construction skill's venue calibration notes that
|   ACL/EMNLP expect "Strong baselines, error analysis." If the target
|   venue is ACL, the skill would flag the missing error analysis.
|   However, for NeurIPS/ICML/ICLR, the expectation is listed as
|   "Thorough experiments, clear method" without explicit error analysis
|   requirements.
|
|-- Missing gate: Mandatory error analysis for classification tasks
|   No pipeline step requires per-class breakdown, confusion matrix,
|   or annotator agreement analysis for classification tasks. The
|   experiment-design skill should have a "classification-specific
|   analysis plan" that always includes these.
|
|-- Fix needed:
|   1. Add an "Error Analysis Plan" section to experiment-design output:
|      for classification tasks, mandate per-class metrics, confusion
|      matrix, and (when applicable) annotator agreement analysis.
|   2. Add annotator agreement metrics (Fleiss' kappa, Krippendorff's
|      alpha, Cohen's kappa) to the measurement-implementation catalog.
|   3. Make error analysis a mandatory (not optional) supporting figure
|      in results-analysis for classification tasks.
|   4. Add a task-specific checklist in results-analysis: for
|      classification, require stratified results; for generation,
|      require qualitative examples; for retrieval, require per-query
|      analysis.
```

---

## W8: "Abstract overclaims 'more aligned with human rationales' without measuring alignment"

**Description**: Abstract states results are "more aligned with human rationales" but no alignment metric (e.g., token-level F1 against human rationale annotations, IOU, AUPRC) is reported.

```
W8: "Abstract overclaims 'more aligned with human rationales' without measuring alignment"
|-- Root cause: claim-evidence-bridge skill (Step 13: /map-claims)
|   The claim-evidence-bridge skill is the PRIMARY defense against
|   overclaiming. It maps every claim to supporting evidence and rates
|   strength. "More aligned with human rationales" is an implicit claim
|   that requires a specific alignment metric (token-level F1, IOU,
|   AUPRC against human annotations). If no such metric was implemented
|   or reported, this claim should be rated "Unsupported" with the
|   recommendation: "Remove from main claims, mention as future work."
|   The skill's Section 3 "Evidence Strength Criteria" states:
|   "Unsupported: No experimental evidence provided, OR evidence
|   contradicts the claim." This should catch it -- but only if the
|   claim is explicitly extracted and checked.
|
|-- Contributing: manuscript-production skill (Step 16: /produce-manuscript)
|   The manuscript-production skill's Abstract template uses a
|   "5-sentence formula" with sentence 4 being "Results: One-two
|   sentences on key quantitative findings." The word "quantitative"
|   is key -- "more aligned with human rationales" is qualitative,
|   not quantitative. The skill should flag abstract claims that lack
|   specific numbers. However, this is guidance, not enforcement.
|
|-- Contributing: paper-self-review SECTION-CHECKLIST
|   The Claim-Conclusion Audit includes: "the abstract's key result
|   sentence uses the same hedging level as recommended by the claim-
|   evidence map" and "no claim in Discussion or Conclusion is stated
|   more strongly than its claim-evidence-map rating warrants." These
|   checks SHOULD catch the overclaim -- but only if paper-self-review
|   is actually run AND the claim-evidence-map correctly rated the
|   alignment claim as Unsupported.
|
|-- Contributing: experiment-design skill (Step 3: /design-experiments)
|   Same issue as W1: the experiment plan did not include an alignment
|   metric despite the research goal involving alignment with human
|   rationales. The gap originates at experiment design and propagates
|   through every downstream step.
|
|-- Contributing: hypothesis-formulation skill (pre-Step 3)
|   If the hypothesis mentions "alignment with human rationales," the
|   success criteria should require an alignment metric. The skill
|   states: "Success threshold: Minimum effect size + statistical
|   significance level" and "Metric selection: Primary metric with
|   justification." If the hypothesis is about alignment but the
|   metric is accuracy, the formulation is internally inconsistent.
|
|-- Missing gate: Abstract-claim-to-metric verification
|   No pipeline step specifically verifies that every claim in the
|   abstract maps to a reported metric. The claim-evidence-bridge
|   checks claims generally, but the abstract is written late (Step 16)
|   and may introduce new claims not present in the original evidence
|   map. There is no "abstract audit" step after prose is written.
|
|-- Fix needed:
|   1. Add a post-abstract verification in manuscript-production: after
|      writing the abstract, parse each claim sentence and verify it
|      maps to a specific metric reported in the results.
|   2. Add alignment metrics (token-level F1, IOU, AUPRC against human
|      annotations) to the measurement-implementation catalog for
|      explainability/rationale tasks.
|   3. Make paper-self-review mandatory in the pipeline (Step 17 in
|      /run-pipeline) with the Claim-Conclusion Audit as a hard gate.
|   4. Add a "no new claims in abstract" rule: the abstract may only
|      contain claims that exist in claim-evidence-map.md, preventing
|      late-stage overclaiming during prose writing.
```

---

## Cross-Cutting Structural Findings

### Finding 1: The pipeline has strong late-stage checks but weak early-stage enforcement

The claim-evidence-bridge (Step 13) and paper-self-review are well-designed to catch overclaiming, missing evidence, and unsupported claims. However, by Steps 13-16, experiments are already complete and it is too expensive to fix fundamental design gaps (missing metrics, missing baselines, insufficient seeds). The pipeline needs earlier enforcement, especially at Steps 3 (experiment-design) and 7 (implement-metrics).

| Weakness | First detectable at | Actually detected at | Too late? |
|-----------|--------------------|--------------------|-----------|
| W1 | Step 3 (design) | Step 13 (claims) | Yes |
| W2 | Step 3 (design) | Step 12 (analysis) | Partially |
| W3 | Step 1 (research-init) | Step 14 (position) | Yes |
| W4 | Step 3 (design) | Step 14 (position) | Yes |
| W5 | Step 1 (research-init) | Step 16 (manuscript) | Yes |
| W6 | Step 12 (analysis) | Step 13 (claims) | Partially |
| W7 | Step 3 (design) | Step 12 (analysis) | Partially |
| W8 | Step 3 (design) | Step 13 (claims) | Yes |

### Finding 2: paper-self-review is not in the pipeline

The paper-self-review skill has the most comprehensive claim-level checks (SECTION-CHECKLIST.md, Claim-Conclusion Audit) but it is NOT one of the 18 steps in `/run-pipeline`. It is triggered manually. This means the strongest quality gate is optional. Six of the eight weaknesses (W1, W3, W4, W5, W6, W8) would have been flagged by the Claim-Conclusion Audit if it were mandatory.

### Finding 3: No domain-specific metric catalogs

The measurement-implementation skill has a generic metric catalog (classification, similarity, scaling, information-theoretic) but lacks domain-specific catalogs for:
- Explainability metrics (faithfulness, plausibility, AOPC, sufficiency, comprehensiveness)
- Rationale alignment metrics (token-level F1, IOU, AUPRC)
- Annotator agreement metrics (Fleiss' kappa, Krippendorff's alpha)

Three weaknesses (W1, W7, W8) trace directly to missing metric types.

### Finding 4: No mechanism to convert cited critiques into required experiments

Weaknesses W3 and W5 both involve failing to experimentally address a known critique or alternative approach. The pipeline treats literature review output as informational (for positioning and writing) rather than prescriptive (for experiment design). There is no "cited-critique -> mandatory experiment" pathway.

### Finding 5: Hooks do not enforce quality gates

The five hooks (session-start, skill-forced-eval, session-summary, stop-summary, security-guard) handle skill routing, session state, and security. None of them enforce quality gates (e.g., "do not proceed to manuscript production if claim-evidence-bridge has Unsupported claims"). The pipeline orchestrator (`/run-pipeline`) checks prerequisite files but not prerequisite quality.

---

## Summary of Required Structural Changes

| Priority | Change | Prevents |
|----------|--------|----------|
| P0 | Add paper-self-review as mandatory Step 17 in /run-pipeline | W1, W3, W4, W5, W6, W8 |
| P0 | Add title/abstract-to-metric consistency check in experiment-design | W1, W8 |
| P1 | Add "ablation reversal" detector in results-analysis | W6 |
| P1 | Add cited-critique-to-experiment mapping in hypothesis-formulation | W3, W5 |
| P1 | Add venue-calibrated minimum scope (datasets, models) in experiment-design | W4 |
| P1 | Add publication-quality seed minimum (>= 5) enforcement in experiment-design | W2 |
| P2 | Add domain-specific metric catalogs (explainability, alignment, agreement) | W1, W7, W8 |
| P2 | Add mandatory error analysis for classification tasks in results-analysis | W7 |
| P2 | Add "component-as-competitor" baseline check in experiment-design | W3 |
| P2 | Add quality-aware prerequisite checks in /run-pipeline (not just file existence) | All |

---

*End of audit. No files were modified.*
