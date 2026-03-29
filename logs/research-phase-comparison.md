# Research Phase Comparison: Repo A vs Repo B

**Repo A**: `test-claude-researcher` (agent-centric)
**Repo B**: `Claude-scholar-extended` (skill-centric)
**Date**: 2026-03-28

---

## Phase 1: Literature Review

### Side-by-side

| Aspect | Repo A | Repo B |
|--------|--------|--------|
| **Entry point** | `.claude/commands/literature-review.md` | `commands/research-init.md` |
| **Core worker** | `literature-scout` agent (Sonnet, 30 turns) | `literature-reviewer` agent (Opus, 25 turns) + `research-ideation` skill |
| **Search enforcement** | Prompt says "Search broadly first, then specifically" — no minimum count | **Mandatory minimums**: 5+ WebSearch queries, 3+ papers with real citations, 2+ WebFetch calls; step marked incomplete if minimums not met |
| **Citation verification** | Agent prompt says "Never make up papers — if you aren't sure a paper exists, say so" | Dedicated `citation-verification` skill with 4-layer check: format → API (Semantic Scholar, CrossRef, arXiv) → info consistency → content accuracy |
| **Zotero integration** | None | Full MCP integration: auto-create collections, import by DOI, batch-attach PDFs, full-text reading, BibTeX export |
| **Paper storage** | Flat `research/literature/literature-map.md` with per-paper entries | Zotero collections (Core Papers, Methods, Applications, Baselines, To-Read) + `$PROJECT_DIR/docs/literature-review.md` |
| **Dataset discovery** | Separate `data/datasets.md` output | Embedded in literature review |
| **Gap analysis** | Delegated to `synthesis-writer` agent as separate step | Built into Step 4 of `/research-init`: identifies 2-3 concrete gaps, formulates research questions |
| **Deduplication** | None | Two-step pre-import dedup: DOI match via search_library, then title token overlap ratio (>0.8 = duplicate) |
| **Error handling** | None specified | 6 fallback strategies (create_collection fails, DOI import fails, fulltext fails, PDF fails, single paper fails, rate limit) |
| **Output verification** | None | Completion checklist with 7 checkboxes; reports search call counts |
| **Scope control** | Fixed: "8-10 papers" per invocation | Configurable: focused (3yr, 20-50 papers) vs broad (5yr, 50-100 papers) |
| **Hypothesis generation** | Separate phase (hypothesis-generator agent) | Hypotheses generated at end of `/research-init` as `hypotheses.md` |

### Best practices from A

1. **Separation of search and synthesis**: A uses `literature-scout` for pure finding and `synthesis-writer` for interpretation. This enforces the principle that the searcher doesn't editorialize. B merges search and synthesis into one workflow.
   - File: `research-pipeline-template/.claude/agents/literature-scout.md` line 7: "You do NOT interpret or synthesize — that is the synthesis-writer's job. You FIND and DOCUMENT."

2. **Dataset-specific output**: A has a dedicated `data/datasets.md` file for dataset discovery with fields: Source, Size, Tasks, License, Relevance. B doesn't systematically catalog datasets separately from the literature review.
   - File: `research-pipeline-template/.claude/agents/literature-scout.md`, Dataset section

3. **Per-paper structured annotations**: A's output format for each paper includes: Key Contribution (1 sentence), Relevance to Project (2-3 sentences), Tags. This is more structured than a prose review.
   - File: `research-pipeline-template/.claude/agents/literature-scout.md`, Output Format section

### Best practices from B

1. **Mandatory search minimums with verification**: B requires 5+ WebSearch, 3+ papers with real citations, 2+ WebFetch — and the step is marked incomplete if these minimums aren't met. A has no enforcement.
   - File: `commands/research-init.md` lines 18-31

2. **4-layer citation verification**: B has a dedicated `citation-verification` skill that programmatically verifies citations via Semantic Scholar, CrossRef, and arXiv APIs. A relies on the agent's honor system ("Never make up papers").
   - File: `skills/citation-verification/SKILL.md`

3. **Zotero integration**: Full reference management with collections, DOI import, PDF attachment, full-text reading, and BibTeX export. A has no external reference manager.
   - File: `commands/research-init.md` Steps 1-3

4. **Pre-import deduplication**: Two-step dedup prevents importing papers already in the library.
   - File: `commands/research-init.md` Step 2.4

5. **Error handling with fallbacks**: 6 specific fallback strategies for common failures.
   - File: `commands/research-init.md` Error Handling section

6. **Configurable scope**: focused vs broad scope with different time ranges and paper counts.
   - File: `commands/research-init.md` args section

### Recommended merge

Keep B's `/research-init` as the base (Zotero, search minimums, citation verification, error handling). Add from A:
- Explicit separation of search and synthesis roles (add a synthesis sub-step after search)
- Dedicated dataset discovery output (`datasets.md`)
- Per-paper structured annotation format (Key Contribution, Relevance, Tags fields)

---

## Phase 2: Hypothesis Generation

### Side-by-side

| Aspect | Repo A | Repo B |
|--------|--------|--------|
| **Entry point** | `.claude/commands/generate-hypotheses.md` | Embedded in `/research-init` output + `hypothesis-formulation` skill |
| **Core worker** | `hypothesis-generator` agent (Opus, 18 turns) | `hypothesis-formulation` skill (no dedicated agent) |
| **Pre-conditions** | Checks that `literature-map.md` has ≥5 papers | Requires completed literature review |
| **Hypothesis count** | 5-10 per invocation, minimum 5 enforced | Not specified as minimum |
| **Scoring criteria** | 3 dimensions: Novelty (1-5), Feasibility (1-5), Impact (1-5) | **5 dimensions**: Novelty, Feasibility, Impact, Testability, Specificity |
| **Falsifiability** | Listed as quality criterion: "States a prediction that could be wrong" | **Mandatory per-hypothesis**: explicit success criteria, failure criteria, and falsification test |
| **Grounding** | "Every hypothesis must cite at least one paper from the literature map" | Links each hypothesis to specific gap in literature review |
| **Success/failure criteria** | Not explicit — only "Key experiment needed: [1 sentence]" | **Explicit**: each hypothesis must have `If confirmed: [implication]` and `If refuted: [implication]` |
| **Ranking** | Top-5 by (Novelty + Feasibility + Impact) in `ranked-hypotheses.md` | Prioritized by combined score, no separate ranked file |
| **Duplication check** | Reads existing `hypothesis-log.md` to avoid duplication | Not explicitly stated |
| **Power analysis** | Not at this stage | Not at this stage (deferred to experiment-design) |
| **Output format** | Detailed: H[N] title, full statement, motivation, 3 scores with justifications, priority, key experiment | Structured but less detailed per-hypothesis |
| **Competition notes** | "Note where competing hypotheses exist in the field" | Not at hypothesis stage (separate competitive-check step) |

### Best practices from A

1. **Dedicated hypothesis agent using Opus**: A uses a standalone agent with `model: opus` and 18-turn budget specifically for hypothesis generation. The agent prompt is focused and detailed (57 lines). B embeds hypothesis generation within a broader skill.
   - File: `research-pipeline-template/.claude/agents/hypothesis-generator.md`

2. **Minimum count enforcement**: A requires "Minimum 5 new hypotheses per invocation." B has no minimum.
   - File: `research-pipeline-template/.claude/agents/hypothesis-generator.md`, Rules section

3. **Per-hypothesis justification for each score**: A requires a justification string after each score (e.g., "Novelty: 4/5 — no prior work on X for Y"). B scores but doesn't mandate justifications.
   - File: `research-pipeline-template/.claude/agents/hypothesis-generator.md`, Output Format

4. **Separate ranked output file**: A maintains `ranked-hypotheses.md` with top-5, distinct from the full `hypothesis-log.md`. This gives a quick reference for what to pursue next.

5. **Competing hypothesis documentation**: A requires noting "where competing hypotheses exist in the field." This surfaces known controversies and alternative explanations early.

### Best practices from B

1. **5-dimension scoring vs 3**: B adds Testability and Specificity alongside Novelty, Feasibility, Impact. These two additional dimensions directly address reviewability.
   - File: `skills/hypothesis-formulation/SKILL.md`

2. **Mandatory success/failure criteria**: B requires explicit `If confirmed: [implication]` and `If refuted: [implication]` for each hypothesis. A only has a vague "Key experiment needed: [1 sentence]".
   - File: `skills/hypothesis-formulation/SKILL.md`

3. **Explicit falsification test**: B requires a falsification test per hypothesis — what result would disprove it. A lists falsifiability as a quality criterion but doesn't mandate documenting the specific test.
   - File: `skills/hypothesis-formulation/SKILL.md`

4. **Separate novelty and competition steps**: B separates novelty assessment and competitive check into their own phases (Phase 3) rather than bundling everything into hypothesis generation. This prevents the hypothesis generator from both generating and evaluating.

### Recommended merge

Use A's **dedicated hypothesis-generator agent** (Opus, 18 turns, standalone invocation) as the execution mechanism. Adopt B's **5-dimension scoring** and **mandatory success/failure criteria with falsification tests**. Keep A's minimum count (5), per-score justifications, ranked output file, and competing hypothesis notes.

---

## Phase 3: Novelty Assessment & Competition Check

### Side-by-side

| Aspect | Repo A | Repo B |
|--------|--------|--------|
| **Separate phase?** | **No** — embedded in hypothesis-generator's Novelty score (1-5) | **Yes** — dedicated `/check-competition` command + `novelty-assessment` skill + `competitive-check` skill |
| **Competition search** | None — assumes literature-scout already found competing work | Structured search query generation from hypotheses, user executes searches, Claude analyzes results |
| **Novelty quantification** | Single score: Novelty 1-5 with justification | **Contribution comparison matrix**: lists 3-5 closest works, delta type (method variant/complementary/extension/overlap), overlap level (None/Low/Medium/High) |
| **Novelty classification** | None | **Taxonomy**: Novel method, Novel application, Novel analysis, Scale improvement, Incremental |
| **Venue calibration** | None | Yes — "Does delta meet novelty bar for target venue?" with venue-specific expectations |
| **Kill switch** | None — low novelty score is informational only | **Explicit**: if novelty is insufficient, skill suggests differentiation strategies or recommends abandoning the direction |
| **Timing** | At hypothesis generation time (before any experiment design) | Between hypothesis generation and experiment design (Step 2 of 20) |
| **Prior work comparison** | "Note where competing hypotheses exist" (qualitative) | Formal comparison matrix with columns: What related works do, What we propose, Delta, Overlap assessment |

### Best practices from A

1. **None identified for this phase.** A's approach of embedding novelty into hypothesis generation is simpler but strictly inferior for catching non-novel ideas. A has no competitive landscape check at all.

### Best practices from B

1. **Dedicated novelty assessment with comparison matrix**: B's `novelty-assessment` skill creates a structured comparison against 3-5 closest prior works with explicit delta typing and overlap quantification.
   - File: `skills/novelty-assessment/SKILL.md`

2. **Novelty classification taxonomy**: Novel method / Novel application / Novel analysis / Scale improvement / Incremental. This maps directly to how reviewers think.
   - File: `skills/novelty-assessment/SKILL.md`

3. **Venue calibration**: B calibrates novelty expectations to venue type (top conference vs workshop). A doesn't consider venue.
   - File: `skills/novelty-assessment/SKILL.md`

4. **Competitive check with structured queries**: B generates specific search queries from hypotheses for the user to execute, then analyzes results for concurrent/competing work.
   - File: `commands/check-competition.md` + `skills/competitive-check/SKILL.md`

5. **Kill switch**: B explicitly recommends abandoning low-novelty directions rather than proceeding to waste implementation effort.
   - File: `skills/novelty-assessment/SKILL.md`

### Recommended merge

Adopt B's full Phase 3 as-is. It is strictly superior to A's approach. A has nothing to contribute here.

---

## Phase 4: Experiment Design

### Side-by-side

| Aspect | Repo A | Repo B |
|--------|--------|--------|
| **Explicit design step?** | **Yes** — `experiment-planner` agent (Sonnet, 12 turns) | **Yes** — `/design-experiments` command + `experiment-design` skill |
| **Baselines** | Required: "Never propose an experiment without specifying baselines" | Required: explicit baseline completeness checklist |
| **Statistical methodology** | Specifies: significance threshold (p<0.05), split strategy, statistical test type | **More rigorous**: minimum 5 seeds per condition (10 for primary), multiple test types, effect size mandatory |
| **Success/failure criteria** | "If hypothesis is TRUE: [expected numbers]. If hypothesis is FALSE: [what you'd see instead]" | From hypothesis-formulation: success criteria, failure criteria, falsification test |
| **Compute estimation** | "Estimated GPU hours: [range], GPU type needed: [minimum]" | Deferred to separate `/plan-compute` step (compute-planner skill) |
| **Confound analysis** | "Confounds to watch for: [list]" | **Threat-to-validity analysis**: falsification test, confound identification, adversarial validation per hypothesis |
| **Metric-claim alignment** | Not explicit | **Mandatory**: "Every key term in hypotheses mapped to metrics" |
| **Ablation design** | Not systematic | Explicit ablation plan with component isolation |
| **Phase gates** | Not present | **Mandatory gate criteria**: pass/fail conditions per experiment phase |
| **Output format** | Single `exp-[N]-[short-name].md` per experiment | `experiment-plan.md` + `experiment-state.json` (tracks iteration state) |
| **Sample size** | Not discussed | "Minimum 5 seeds per condition (10 for primary comparison)" |

### Best practices from A

1. **Expected results in both directions**: A's experiment plan template requires "If hypothesis is TRUE: [what numbers you'd expect]" and "If hypothesis is FALSE: [what you'd see instead]." This forces thinking about what both outcomes mean *before* running experiments.
   - File: `research-pipeline-template/.claude/agents/experiment-planner.md`, Expected Results section

2. **Implementation steps with time estimates**: A includes "Implementation Steps: 1. [Step 1 with estimated time]" directly in the experiment plan. B separates this into the scaffold/implementation phase.
   - File: `research-pipeline-template/.claude/agents/experiment-planner.md`, Implementation Steps section

3. **Integrated compute estimation**: A includes GPU hours, GPU type, and storage estimates in the experiment plan itself. B defers this to a separate `/plan-compute` step, which means the experiment design doesn't consider resource constraints during design.
   - File: `research-pipeline-template/.claude/agents/experiment-planner.md`, Compute Requirements section

4. **Confound documentation**: A requires explicit "Confounds to watch for: [list]" per experiment.
   - File: `research-pipeline-template/.claude/agents/experiment-planner.md`, Expected Results section

### Best practices from B

1. **Minimum seed counts**: B mandates 5 seeds per condition (10 for primary comparison). A says "statistical test" without specifying minimum runs.
   - File: `commands/design-experiments.md`

2. **Threat-to-validity analysis per hypothesis**: B requires falsification test, confound identification, and adversarial validation for each hypothesis. A only has a general confound list.
   - File: `commands/design-experiments.md`

3. **Metric-claim alignment**: B mandates that every key term in hypotheses maps to a measurable metric. A doesn't enforce this.
   - File: `commands/design-experiments.md`

4. **Phase gate criteria**: B defines pass/fail conditions for experiment phases, enabling automatic PROCEED/DIAGNOSE/STOP decisions. A has no gates.
   - File: `skills/experiment-design/SKILL.md`

5. **Experiment state tracking**: B uses `experiment-state.json` to persist iteration state, hypothesis revisions, and phase results. A has no state persistence.
   - File: `skills/experiment-design/SKILL.md`

### Recommended merge

Use B's `/design-experiments` as the base (seed minimums, threat-to-validity, metric-claim alignment, phase gates, state tracking). Add from A:
- Explicit "If TRUE / If FALSE" expected results section per hypothesis
- Integrated compute estimation (merge into design step rather than separate step)
- Per-experiment confound list
- Implementation time estimates

---

## Phase 5: Validation Before Experiments

### Side-by-side

| Aspect | Repo A | Repo B |
|--------|--------|--------|
| **Dedicated validation step?** | **No** — code-reviewer-agent reviews implementation quality but there's no pre-experiment validation | **Yes** — `/validate-setup` command + `setup-validation` skill + pre-flight checks in `/run-experiment` |
| **Data integrity check** | Not present | Yes: dataset loading, shape verification, label distribution |
| **Training loop test** | Not present | Yes: full Trainer init test required (not just import check) |
| **Metric validation** | Not present | Yes: metric implementation correctness check |
| **Baseline fairness check** | In code-reviewer: "Ensure fair baseline comparisons" (review-time only) | Yes: baseline completeness check in experiment design |
| **Dry run** | Not present | Mandatory: `python -m src.main --dry-run` before SLURM submission |
| **Data caching verification** | Not present | Mandatory: `HF_DATASETS_OFFLINE=1` test before submission |
| **SLURM readiness** | Not applicable (local execution) | Yes: `sinfo -s` check, venv Python verification |
| **Git commit before run** | Not present | Mandatory: commit code with hash recorded before SLURM submission |
| **Smoke test** | Not present | Yes: ablation smoke test on tiny data subset |

### Best practices from A

1. **Comprehensive code review**: A's `code-reviewer-agent` (376 lines) has a detailed 9-phase review covering: structure → correctness → quality → reproducibility → performance → methodology → testing → documentation → sign-off. The ML-specific checks (gradient verification, numerical stability, fair baselines) are thorough.
   - File: `EPFL:Sparsemax-project/.claude/agents/code-reviewer-agent.md`

2. **Minimum test count**: A requires "minimum 10-15 unit tests" in the implementation. B's validation doesn't specify a test count.
   - File: `research-pipeline-template/.claude/agents/ml-implementer-agent.md`

### Best practices from B

1. **Entire dedicated validation phase**: B has a full pre-flight validation step (`/validate-setup`) that A completely lacks.
   - File: `commands/validate-setup.md` + `skills/setup-validation/SKILL.md`

2. **Pre-flight checks before SLURM**: 5 mandatory checks (data cached, dry run passes, SLURM accessible, project dir exists, venv Python verified).
   - File: `commands/run-experiment.md` Pre-flight section

3. **Mandatory git commit before experiment**: Ensures reproducibility by recording the exact code state.
   - File: `commands/run-experiment.md`

4. **Data caching verification**: Tests that datasets and models are cached locally before submitting GPU jobs, preventing wasted compute.
   - File: `commands/run-experiment.md` check #1

5. **Training loop validation**: Full Trainer init test — not just import check — catches configuration errors before wasting GPU hours.
   - File: `skills/setup-validation/SKILL.md`

6. **Smoke test on tiny data**: Runs a quick ablation on a small data subset to verify the pipeline end-to-end.
   - File: `skills/setup-validation/SKILL.md`

### Recommended merge

Adopt B's entire validation phase. It is strictly superior — A has no pre-experiment validation at all. Transplant A's ML-specific code review criteria (gradient checking, numerical stability, minimum test count) into B's `setup-validation` skill as additional checklist items.

---

## Phase 6: Results Analysis & Claim Mapping

### Side-by-side

| Aspect | Repo A | Repo B |
|--------|--------|--------|
| **Entry point** | `.claude/commands/evaluate-results.md` | `commands/analyze-results.md` |
| **Core worker** | `results-analyzer-agent` (Sonnet, 15 turns) | `results-analysis` skill + `results-report` skill (two-stage) |
| **Two-stage analysis?** | **No** — single agent does everything | **Yes** — Stage 1: strict stats (analysis-report.md), Stage 2: decision-oriented report (results-report.md) |
| **Statistical tests** | Paired t-test, Wilcoxon signed-rank, Cohen's d, 95% CIs, Bonferroni correction | Paired bootstrap (10K resamples), 95% CIs, Cohen's d, plus all of A's tests |
| **Visualization** | 300 DPI PNGs, 7 figure types specified | Vector PDF, venue-specific rcParams (NeurIPS/ICML/ICLR dimensions), colorblind-safe palettes |
| **Hypothesis verdict** | Informal: confirmed/denied in narrative | **Mandatory verdict table**: each hypothesis → Confirmed/Partially Confirmed/Refuted with evidence |
| **Error analysis** | Yes: misclassification patterns, per-class breakdowns | **Mandatory**: stratification by ≥2 dimensions |
| **Negative results** | "What it means if results are negative" | Separate negative results audit in manuscript production |
| **Claim mapping** | Not present — goes directly from analysis to paper | **Dedicated phase**: `/map-claims` command + `claim-evidence-bridge` skill |
| **Overclaiming check** | Not present | Yes: claim-evidence-bridge checks that each claim has supporting data, flags overclaiming |
| **Figure catalog** | Not present | `figure-catalog.md` with interpretation checklists per figure |
| **Claim-evidence consistency** | Not present | Explicit mapping: each claim → specific result number |
| **Scope management** | Not present | Yes: `claim-evidence-bridge` manages what to include/exclude from paper |

### Best practices from A

1. **7 specific figure types in agent prompt**: A's results-analyzer explicitly lists: bar charts with error bars, violin plots, heatmaps, line plots, scatter plots, confusion matrices, and attention visualizations. This ensures diverse, appropriate visualization.
   - File: `EPFL:Sparsemax-project/.claude/agents/results-analyzer-agent.md`

2. **Hyperparameter sensitivity analysis**: A explicitly requires analyzing how results change with hyperparameters. B mentions ablation analysis but doesn't specifically call out hyperparameter sensitivity.
   - File: `EPFL:Sparsemax-project/.claude/agents/results-analyzer-agent.md`

3. **Per-class/per-dataset breakdowns as default**: A always produces breakdowns by class and dataset. B requires stratification but doesn't specify these specific cuts.
   - File: `EPFL:Sparsemax-project/.claude/agents/results-analyzer-agent.md`

### Best practices from B

1. **Two-stage analysis**: B separates strict statistical analysis (evidence) from interpretive reporting (narrative). This prevents mixing evidence with spin.
   - File: `commands/analyze-results.md` + `skills/results-analysis/SKILL.md`

2. **Paired bootstrap with 10K resamples**: More robust than A's parametric tests alone.
   - File: `commands/analyze-results.md`

3. **Mandatory hypothesis verdict table**: Forces explicit confirmation/refutation decision per hypothesis. A's verdicts are informal.
   - File: `commands/analyze-results.md`

4. **Dedicated claim mapping phase**: B's `/map-claims` + `claim-evidence-bridge` skill is an entire phase between analysis and writing. A goes straight from results to paper.
   - File: `commands/map-claims.md` + `skills/claim-evidence-bridge/SKILL.md`

5. **Overclaiming detection**: B flags claims that aren't supported by sufficient evidence.
   - File: `skills/claim-evidence-bridge/SKILL.md`

6. **Figure catalog with interpretation checklists**: B generates a `figure-catalog.md` that lists each figure with its interpretation checklist.
   - File: `skills/results-analysis/SKILL.md`

7. **Venue-specific figure standards**: B applies venue-specific matplotlib rcParams (NeurIPS: 5.5in single column, ICML: 6.75in, etc.) with colorblind-safe palettes.
   - File: `skills/results-analysis/SKILL.md`

### Recommended merge

Use B's two-stage analysis + claim mapping pipeline as the base. Add from A:
- Explicit list of figure types to always consider (7 types)
- Hyperparameter sensitivity analysis as mandatory
- Per-class and per-dataset breakdowns as default cuts

---

## Summary Table

| Phase | A's Strength | B's Strength | Recommended for Merge |
|-------|-------------|-------------|----------------------|
| **1. Literature Review** | Search/synthesis separation, dataset cataloging, per-paper structured annotations | Search minimums with verification, citation verification API, Zotero integration, dedup, error handling | **B's base** + A's search/synthesis separation and dataset output |
| **2. Hypothesis Generation** | Dedicated Opus agent, minimum 5 hypotheses, per-score justifications, ranked output, competing hypothesis notes | 5-dimension scoring, mandatory success/failure criteria, explicit falsification test | **A's agent** + B's 5-dimension scoring and falsification requirements |
| **3. Novelty/Competition** | None | Full novelty assessment: comparison matrix, classification, venue calibration, kill switch | **B entirely** — A has nothing here |
| **4. Experiment Design** | Expected results (both directions), compute estimation, confound documentation, time estimates | Seed minimums, threat-to-validity, metric-claim alignment, phase gates, state tracking | **B's base** + A's expected results format and integrated compute estimation |
| **5. Validation** | Comprehensive ML code review (gradient check, numerical stability, fair baselines, test count) | Entire validation phase: dry run, data caching, SLURM readiness, smoke test, git commit | **B's base** + A's ML-specific review criteria |
| **6. Results Analysis** | 7 figure types, hyperparameter sensitivity, per-class/dataset breakdowns | Two-stage analysis, bootstrap, hypothesis verdict table, claim mapping, overclaiming detection, venue figures | **B's base** + A's figure diversity and hyperparameter analysis |

---

## Concrete Improvement Plan

### Improvements to add to Repo B from Repo A

#### 1. Search/synthesis separation in literature review
- **What**: Add explicit separation between paper discovery and literature synthesis in `/research-init`
- **Which file**: `commands/research-init.md`
- **How**: After Step 3 (Paper Analysis), add a distinct "Synthesis" sub-step that explicitly follows the pattern: "You are now writing synthesis. Do NOT search for more papers. Work only from what was found above."
- **Priority**: Medium
- **Effort**: ~10 lines added to research-init.md

#### 2. Dedicated dataset discovery output
- **What**: Generate a `$PROJECT_DIR/docs/datasets.md` alongside `literature-review.md`
- **Which file**: `commands/research-init.md` (add to Step 5)
- **How**: Add output file with A's format: Dataset Name, Source, Size, Tasks, License, Relevance
- **Priority**: Medium
- **Effort**: ~15 lines added to research-init.md

#### 3. Dedicated hypothesis-generator agent
- **What**: Create an agent that runs hypothesis generation with Opus model, 18-turn budget, and enforced minimums
- **Which file**: New `agents/hypothesis-generator.md` (does not exist in B)
- **How**: Port A's `hypothesis-generator.md` agent definition, update scoring to B's 5-dimension system, add B's falsification requirements
- **Priority**: High
- **Effort**: ~60 lines (new agent file)

#### 4. Minimum hypothesis count enforcement
- **What**: Require minimum 5 hypotheses per generation
- **Which file**: `skills/hypothesis-formulation/SKILL.md`
- **How**: Add rule: "Minimum 5 new hypotheses per invocation"
- **Priority**: Medium
- **Effort**: ~2 lines

#### 5. Per-score justifications in hypothesis scoring
- **What**: Require justification text after each dimension score
- **Which file**: `skills/hypothesis-formulation/SKILL.md`
- **How**: Change output format to: "Novelty: [4/5] — [why this score]" for each dimension
- **Priority**: Medium
- **Effort**: ~10 lines

#### 6. Ranked hypotheses output file
- **What**: Generate separate `ranked-hypotheses.md` with top-5 by combined score
- **Which file**: `skills/hypothesis-formulation/SKILL.md`
- **How**: Add output step: "Update ranked-hypotheses.md with current top-5"
- **Priority**: Low
- **Effort**: ~5 lines

#### 7. Competing hypothesis documentation
- **What**: Require noting "where competing hypotheses exist in the field" per hypothesis
- **Which file**: `skills/hypothesis-formulation/SKILL.md`
- **How**: Add field: "Competing explanations: [known alternatives]"
- **Priority**: Medium
- **Effort**: ~3 lines

#### 8. "If TRUE / If FALSE" expected results in experiment design
- **What**: Add explicit expected results section per hypothesis in experiment plan
- **Which file**: `skills/experiment-design/SKILL.md`
- **How**: Add template section: "Expected Results: If TRUE: [specific numbers/patterns]. If FALSE: [what you'd see instead]."
- **Priority**: High
- **Effort**: ~10 lines

#### 9. Integrated compute estimation in experiment design
- **What**: Include GPU hours, type, and storage estimates in the experiment plan itself
- **Which file**: `skills/experiment-design/SKILL.md`
- **How**: Add "Compute Requirements" section to the experiment plan template (currently deferred to separate /plan-compute step)
- **Priority**: Medium
- **Effort**: ~8 lines

#### 10. ML-specific validation criteria
- **What**: Add gradient checking, numerical stability testing, fair baseline enforcement, minimum test count to setup validation
- **Which file**: `skills/setup-validation/SKILL.md`
- **How**: Add checklist items from A's code-reviewer-agent
- **Priority**: High
- **Effort**: ~15 lines

#### 11. Explicit figure type diversity
- **What**: List 7+ figure types to consider during results analysis
- **Which file**: `skills/results-analysis/SKILL.md`
- **How**: Add: "Consider these visualization types: bar charts with error bars, violin plots, heatmaps, line plots, scatter plots, confusion matrices, attention/feature visualizations"
- **Priority**: Low
- **Effort**: ~5 lines

#### 12. Mandatory hyperparameter sensitivity analysis
- **What**: Require hyperparameter sensitivity analysis in results
- **Which file**: `skills/results-analysis/SKILL.md` or `commands/analyze-results.md`
- **How**: Add: "Mandatory: Hyperparameter sensitivity analysis — how do results change with key hyperparameters?"
- **Priority**: Medium
- **Effort**: ~5 lines

### Improvements to B's existing files using A's approach

#### 1. Hypothesis formulation: use agent instead of skill-only
- **What**: Create a dedicated hypothesis-generator agent (Opus, 18 turns) that invokes the hypothesis-formulation skill
- **Why A's approach is better**: Agent isolation gives model control (Opus for deep reasoning), turn budget, and tool restrictions. Currently B's hypothesis generation runs in whatever model the session uses.
- **Which file**: New `agents/hypothesis-generator.md` + update `/research-init` to invoke it

#### 2. Experiment design: merge compute estimation
- **What**: Include compute estimation directly in the experiment plan rather than as a separate step
- **Why A's approach is better**: Knowing resource constraints during design prevents designing experiments that can't be executed. Currently B designs first, then discovers compute limitations.
- **Which file**: `skills/experiment-design/SKILL.md` — add Compute Requirements section

---

## Implementation Priority Order

| # | Change | Priority | Effort | Impact |
|---|--------|----------|--------|--------|
| 1 | Create hypothesis-generator agent (Opus) | High | ~60 lines | Better hypothesis quality through dedicated reasoning |
| 2 | Add "If TRUE / If FALSE" expected results to experiment design | High | ~10 lines | Forces pre-commitment to outcome interpretation |
| 3 | Add ML-specific validation criteria to setup-validation | High | ~15 lines | Catches more bugs before GPU waste |
| 4 | Add minimum hypothesis count + per-score justifications | Medium | ~12 lines | More rigorous hypothesis generation |
| 5 | Add competing hypothesis documentation | Medium | ~3 lines | Early identification of alternative explanations |
| 6 | Integrate compute estimation into experiment design | Medium | ~8 lines | Design considers resource constraints |
| 7 | Add search/synthesis separation to research-init | Medium | ~10 lines | Cleaner separation of concerns |
| 8 | Add dataset discovery output | Medium | ~15 lines | Systematic dataset cataloging |
| 9 | Add hyperparameter sensitivity analysis | Medium | ~5 lines | More thorough results analysis |
| 10 | Add figure type diversity list | Low | ~5 lines | Better visualization coverage |
| 11 | Add ranked hypotheses output | Low | ~5 lines | Quick reference for top hypotheses |
