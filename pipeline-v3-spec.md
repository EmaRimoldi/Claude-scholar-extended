# Research Orchestrator v3 — Revised Pipeline Specification

> Addresses all 10 weak points (WP1–WP10) and 4 architectural gaps (A1–A4) identified in `critique.md`.

---

## Part 0: What Changed and Why

The v2 pipeline was engineered for **completion** — making sure a paper gets produced. v3 is engineered for **quality** — making sure the paper is actually defensible. The three structural interventions that drive every specific change are:

1. **Epistemic infrastructure parallel to engineering infrastructure.** Engineering infrastructure (hooks, guards, state files) tracks whether the process ran. Epistemic infrastructure (Evidence Registry, Claim Dependency Graph, Consistency Oracle) tracks whether the claims are warranted.

2. **Verification agents alongside generative agents.** Every generative step now has a corresponding adversarial pass: a Skeptic, a Reproducibility checker, a Reviewer simulator, a Scope monitor. Generation and verification are not the same task and must not be performed by the same agent in the same pass.

3. **Phase 5 is a revision cycle, not a linear sequence.** Analysis → claim mapping → positioning → narrative → draft → multi-dimensional review → remediation routing → re-draft. This loop terminates on convergence or escalation, not on completion of a step.

Step count: **33 steps** across 6 phases (up from 24). New modules: 11. New feedback loops: 4. New infrastructure components: 6.

---

## Part 1: Persistent Infrastructure

Infrastructure components that are initialized once and queried/updated throughout the entire pipeline. These are not phase-specific steps; they are services.

### 1.1 Epistemic Layer [A1]

Stored at: `$PROJECT_DIR/.epistemic/`

#### Evidence Registry (`evidence_registry.json`)

A persistent JSON object tracking every piece of evidence entering the pipeline.

**Schema per entry:**
```json
{
  "id": "EV-042",
  "type": "experimental_result | literature_finding | statistical_test | ablation",
  "source": "step_id + artifact path",
  "description": "one-line summary",
  "strength": "strong | moderate | weak | contested",
  "claims_dependent": ["CL-007", "CL-012"],
  "last_updated": "step_14",
  "notes": ""
}
```

**Lifecycle:** Seeded at Step 1 (literature findings). Updated at every step that produces results (Steps 4, 13, 14, 16, 17, 18). Queried at every claim-generating step (Steps 3, 19, 24).

**Failure mode:** Evidence Registry stale (not updated after iteration). Guard: `check_registry_freshness.py` runs before Steps 19 and 24 and blocks if the registry has not been updated since the last result-producing step.

#### Claim Dependency Graph (`claim_graph.json`)

A directed graph where nodes are claims and edges point to evidence entries. If evidence is revised or downgraded, all dependent claims are flagged with status `NEEDS_REVIEW`.

**Schema per claim node:**
```json
{
  "id": "CL-007",
  "text": "Our method achieves 3.2% improvement on benchmark X",
  "strength": "strong | moderate | hedged | speculative",
  "evidence": ["EV-042", "EV-043"],
  "section": "results | abstract | discussion | conclusion",
  "status": "verified | needs_review | unsupported | overclaimed",
  "last_verified": "step_26"
}
```

**Lifecycle:** Populated at Step 19 (/map-claims). Updated at Steps 24–27 (writing and review cycle). Queried by Claim-Source Alignment Verifier (Step 26) and the Consistency Oracle.

**Failure mode:** Claim added to manuscript without graph registration. Guard: `audit_claim_coverage.py` at Step 26 flags unregistered claims.

#### Confidence Tracker (`confidence_tracker.json`)

Maps each claim ID to a calibrated confidence level that propagates into manuscript hedging language. The manuscript-production agent reads this file before generating prose for any claim and selects hedging language accordingly.

**Confidence levels → hedging templates:**
- `high (0.8–1.0)` → "X achieves Y" / "we show that"
- `moderate (0.5–0.79)` → "X appears to achieve Y" / "results suggest"
- `low (0.2–0.49)` → "preliminary results indicate" / "we observe a trend"
- `speculative (<0.2)` → must be in Limitations section, not Results

**Update rule:** Confidence is downgraded if: (a) effect size is small (<0.2 Cohen's d), (b) p-value is marginal (0.05–0.1), (c) Skeptic Agent challenges and the challenge is not refuted, or (d) ablation shows the effect disappears under one variation.

---

### 1.2 Citation Provenance Ledger [WP10]

Stored at: `$PROJECT_DIR/.epistemic/citation_ledger.json`

**Schema per entry:**
```json
{
  "cite_key": "wang2023attention",
  "title": "...",
  "claims_supported": ["CPL-001", "CPL-002"],
  "claims_supported_text": ["transformers scale with data", "attention is O(n^2)"],
  "first_introduced": "step_1",
  "used_in_manuscript": true,
  "audit_status": "verified | misrepresented | unused | unchecked"
}
```

**Lifecycle:** Initialized at Step 1. Each claim entry in the ledger links to specific passages in the reviewed paper (stored in literature notes). Updated at Step 19 (/map-claims). Audited at Step 24 (Citation Audit sub-step of /produce-manuscript).

**Failure mode:** LLM writes a citation that hallucinated or misrepresents the source. The Citation Audit at Step 24 cross-references every `\cite{}` command in the LaTeX against the ledger and flags any citation with `audit_status != "verified"`.

---

### 1.3 Consistency Oracle [A3]

A persistent service implemented as a Python script (`consistency_oracle.py`) that can be queried at any stage.

**Interface:**
```
oracle.check(new_content: str, content_type: "claim|figure_caption|method_description|abstract", context: dict) → ConsistencyReport
oracle.sweep(manuscript_path: str) → FullConsistencyReport
```

**What it checks:**
- New claim vs. all existing claims in `claim_graph.json` (contradiction detection)
- New claim vs. all evidence in `evidence_registry.json` (scope detection)
- Figure caption vs. the claim it is supposed to support (argument-figure alignment)
- Method description vs. `experiment-state.json` + config files (method-code consistency)
- Cross-section claim consistency (abstract ↔ conclusion ↔ results)

**Implementation:** The oracle loads all epistemic state files and runs a structured LLM query with a fixed evaluation prompt. It is deterministic given the same inputs — it does not generate new content, only evaluates consistency of provided content.

**Query points (mandatory):** Before Step 24 (full sweep), before Step 28 (full sweep). Optional: at any step where new content is generated.

---

### 1.4 Pipeline State Files

All v2 state files are retained. New additions:

| File | Purpose |
|------|---------|
| `pipeline-state.json` | Step completion, phase status, current revision cycle count |
| `experiment-state.json` | Experiment execution status, SLURM job IDs, result paths |
| `.epistemic/evidence_registry.json` | Evidence inventory [new] |
| `.epistemic/claim_graph.json` | Claim dependency graph [new] |
| `.epistemic/confidence_tracker.json` | Per-claim confidence levels [new] |
| `.epistemic/citation_ledger.json` | Citation provenance tracking [new] |
| `.epistemic/consistency_log.json` | Consistency Oracle query history [new] |
| `gap-detection-report.md` | Output of Step 15 [new] |
| `novelty-reassessment.md` | Output of Step 16 [new] |
| `method-reconciliation-report.md` | Output of Step 18 [new] |
| `claim-alignment-report.md` | Output of Step 26 [new] |
| `review-battery-report.md` | Output of Step 27 [new] |
| `adversarial-review-report.md` | Output of Step 28 [new] |

---

## Part 2: Agent Roster

### 2.1 Generative Agents (retained, some enhanced)

| Agent | Model | Role | Enhancement |
|-------|-------|------|-------------|
| `hypothesis-generator` | opus | Generate, score, rank hypotheses | Reads novelty-reassessment.md on revision loops |
| `literature-reviewer` | opus | Literature search, trend analysis | Now invoked twice: Step 1 (broad) and Step 17 (results-contextualized) |
| `literature-reviewer-obsidian` | sonnet | Filesystem-first literature review | — |
| `research-knowledge-curator-obsidian` | sonnet | Obsidian KB curation | — |
| `rebuttal-writer` | opus | Rebuttal writing | Demoted to post-submission only; pre-submission adversarial review uses Reviewer Simulation Agent |
| `paper-miner` | opus | Extract writing patterns | — |
| `architect` | sonnet | System architecture | — |
| `build-error-resolver` | sonnet | Build error fixing | — |
| `bug-analyzer` | opus | Root cause analysis | — |
| `code-reviewer` | sonnet | Code review | — |
| `dev-planner` | sonnet | Development planning | — |
| `refactor-cleaner` | sonnet | Code cleanup | — |
| `tdd-guide` | sonnet | TDD workflow | — |
| `kaggle-miner` | sonnet | Kaggle practice extraction | — |
| `ui-sketcher` | sonnet | UI design | — |
| `story-generator` | sonnet | Story/requirement generation | — |

### 2.2 Verification Agent Cohort [A4] — New

These agents do not generate content. They evaluate, challenge, and flag. They read existing content and return structured reports.

| Agent | Model | Max Turns | Role |
|-------|-------|-----------|------|
| `skeptic-agent` | opus | 12 | Given any claim, systematically attempt to falsify it: find counterexamples in the literature, identify confounds, challenge the statistical interpretation, propose alternative explanations. Output: `skeptic-report.md` with challenge items and severity ratings. |
| `reproducibility-agent` | sonnet | 10 | Given manuscript + codebase, check whether the paper provides enough detail to reproduce the results: are all hyperparameters reported? is the dataset preprocessing described? are random seeds stated? Output: `reproducibility-checklist.md` with pass/fail per criterion. |
| `reviewer-simulation-agent` | opus | 15 | Simulate 3 distinct hostile-but-fair reviewers (Novelty Skeptic, Methods Pedant, Clarity Judge). Each reviewer produces an independent review with scores and specific objections in standard conference review format. Output: `simulated-reviews/reviewer_{1,2,3}.md`. |
| `scope-agent` | sonnet | 8 | Given manuscript claims and experiment design, flag any claim that generalizes beyond what the experiments tested. Examples: claiming performance on a distribution the model was not evaluated on, claiming speed improvements without profiling, claiming a result is "general" when only one dataset was used. Output: `scope-violations.md`. |

**Invocation policy:** Skeptic Agent runs at Step 19 (after /map-claims) and Step 27 (multi-dimensional review). Reproducibility Agent runs at Step 18 and Step 28. Reviewer Simulation Agent runs at Step 28 (adversarial review). Scope Agent runs at Step 26 (claim-source alignment) and Step 28.

---

## Part 3: Deterministic Scripts

All v2 scripts retained. New scripts:

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `check_registry_freshness.py` | `evidence_registry.json`, `pipeline-state.json` | Pass/fail + staleness report | Blocks claim-generation steps if registry is stale |
| `build_claim_graph.py` | `claim_ledger.md`, `evidence_registry.json` | `claim_graph.json` | Constructs directed graph from claim → evidence |
| `audit_claim_coverage.py` | manuscript LaTeX, `claim_graph.json` | Coverage report + unregistered claims | Flags manuscript claims not in the graph |
| `audit_citations.py` | manuscript LaTeX, `citation_ledger.json` | Citation audit report | Flags unused, misrepresented, or hallucinated citations |
| `method_reconcile.py` | manuscript method section, `experiment-state.json`, config files | Reconciliation report | Cross-references described vs. actual hyperparameters |
| `cross_section_check.py` | manuscript LaTeX (parsed by section) | Consistency report | Extracts core claims per section and checks bidirectional alignment |
| `confidence_to_hedging.py` | `confidence_tracker.json`, manuscript LaTeX | Hedging audit | Flags claims whose hedging language does not match their confidence level |
| `gap_detector.py` | `analysis-report.md`, `experiment-plan.md`, `hypotheses.md` | `gap-detection-report.md` | Identifies missing ablations, uncontrolled confounds, absent baselines |
| `narrative_gap_detector.py` | `paper-blueprint.md`, `claim_graph.json`, `evidence_registry.json` | `narrative-gap-report.md` | Flags story elements that require non-existent evidence |
| `concurrent_work_check.py` | `hypotheses.md`, `analysis-report.md` | arXiv search queries + results | Generates targeted queries for concurrent work check |

---

## Part 4: Pipeline Phases and Steps

### Notation

Each step entry has:
- **Function**: what the step does
- **Inputs**: required inputs
- **Outputs**: artifacts produced
- **Gate**: condition that must be satisfied before the next step proceeds
- **Epistemic updates**: which epistemic layer components are updated
- **Failure mode**: what goes wrong if this step fails silently

Feedback loop routing is described in Part 5.

---

### Phase 1: Research Ideation (Day 1–4)

#### Step 1: `/research-lit` — Literature Review with Provenance Initialization

**Function:** Comprehensive literature search and gap analysis. Simultaneously initializes the Citation Provenance Ledger and seeds the Evidence Registry with literature findings.

**Inputs:** Research topic, venue target, keyword list

**Outputs:**
- `$PROJECT_DIR/research-notes.md` — synthesis of literature
- `$PROJECT_DIR/literature-gaps.md` — identified gaps
- `.epistemic/citation_ledger.json` — initialized with all reviewed papers; for each paper, records the specific claims it supports
- `.epistemic/evidence_registry.json` — seeded with literature evidence entries (type: `literature_finding`)

**Gate:** At least 20 papers reviewed; at least 3 distinct research gaps identified; Citation Provenance Ledger has entries for all cited papers.

**Epistemic updates:** Citation Provenance Ledger initialized. Evidence Registry seeded.

**Failure mode:** Literature review is completed but the ledger is not populated, causing the Citation Audit at Step 24 to have no baseline to verify against.

---

#### Step 2: `/check-competition` — Competitive Landscape Check

**Function:** Map the research space: who is working on this, what has been published recently, what venues have rejected or accepted similar work. Requires online access.

**Inputs:** Research topic, initial gaps from Step 1

**Outputs:**
- `$PROJECT_DIR/competitive-landscape.md`
- Flagged: any concurrent work that is very close (within 6 months, same contribution)

**Gate:** Search coverage ≥ 3 databases; landscape document classifies papers into "directly competing", "adjacent", "baseline-eligible" categories.

**Failure mode:** Misses a directly competing paper that a reviewer will cite in rejection.

---

#### Step 3: `/assess-novelty-hypotheses` — Initial Novelty Assessment + Hypothesis Formulation

**Function:** Given literature and competitive landscape, assess novelty of candidate research directions and formulate falsifiable hypotheses. This assessment is explicitly preliminary — it will be revised at Step 16.

**Inputs:** `research-notes.md`, `competitive-landscape.md`, `literature-gaps.md`

**Outputs:**
- `$PROJECT_DIR/hypotheses.md` — each hypothesis with: statement, falsification criteria, expected direction, confidence level, literature support
- `$PROJECT_DIR/novelty-initial.md` — initial novelty assessment with explicit "this may change after results" flag
- `.epistemic/claim_graph.json` — initialized with hypothesis nodes (type: `hypothesized_claim`)

**Gate:** At least 2 primary hypotheses; at least 1 alternative hypothesis; all hypotheses are falsifiable (have stated success and failure criteria).

**Agents:** `hypothesis-generator` (opus, extended thinking), `novelty-assessment` skill

**Failure mode:** Hypotheses are too broad to falsify, leading to an unfalsifiable research design.

---

### Phase 2: Experiment Design (Day 4–5)

#### Step 4: `/design-experiments` — Experiment Planning

**Function:** Full experiment plan: baselines, ablations, sample size, resource estimation, statistical power analysis, success criteria, failure criteria. This step is the target of the Analysis→Design feedback loop and may be re-entered.

**Inputs:** `hypotheses.md`, `competitive-landscape.md`

**Outputs:**
- `$PROJECT_DIR/experiment-plan.md` — complete experiment matrix
- `$PROJECT_DIR/experiment-state.json` — initialized with all planned runs
- Ablation coverage matrix: for each hypothesis, which ablations test which components

**Gate:** Every hypothesis has at least one primary experiment and one ablation; sample size is justified by power analysis; compute budget is estimated.

**Epistemic updates:** Evidence Registry updated with planned experiment IDs (type: `planned_result`, status: `pending`).

**Failure mode:** Under-designed ablations — the paper has results but can't attribute them to the right component.

**Re-entry:** If Gap Detection (Step 15) routes back here, the experiment plan is amended with newly identified required experiments. Version control: `experiment-plan-v{N}.md`. Maximum 2 re-entries from the analysis loop; 3rd failure escalates to human review.

---

### Phase 3: Implementation (Day 5–9)

#### Step 5: `/scaffold` — Project Structure

**Function:** Generate runnable project: `pyproject.toml`, `src/`, `configs/`, entry point, Factory/Registry patterns, Hydra config.

**Inputs:** `experiment-plan.md`

**Outputs:** Runnable project directory

**Gate:** `uv run python -c "from src import *"` exits 0; all config schemas validate.

---

#### Step 6: `/build-data` — Dataset Pipeline

**Function:** Translate dataset specs into generators/loaders. Cache preprocessing. Verify data integrity hashes.

**Inputs:** Dataset specifications from `experiment-plan.md`

**Outputs:** Working data loaders, `data-manifest.json` with split sizes and hashes

**Gate:** All dataset splits load without error; shapes match spec; no data leakage between train/val/test.

---

#### Step 7: `/setup-model` — Model Configuration

**Function:** Load, configure, introspect, and prepare models. Register hooks for intermediate activation access.

**Inputs:** Model spec from `experiment-plan.md`

**Outputs:** Model config files, hook registry, parameter count report

**Gate:** Model loads without error; parameter count matches expected; forward pass on dummy input succeeds.

---

#### Step 8: `/implement-metrics` — Metrics and Statistical Tests

**Function:** Implement all evaluation metrics and statistical tests specified in the experiment plan.

**Inputs:** Metric specifications from `experiment-plan.md`

**Outputs:** Metric implementations, unit tests, baseline sanity values

**Gate:** All metrics pass unit tests; metrics produce expected values on known inputs.

---

#### Step 9: `/validate-setup` — Pre-Flight Validation

**Function:** Run all pre-flight checks: data integrity, model loading, metric correctness, ablation sanity, smoke test on 10 training steps, baseline reproducibility.

**Inputs:** All Phase 3 artifacts

**Outputs:** `$PROJECT_DIR/smoke-test-report.md`

**Gate (hard block):** All checks must pass. Any failure blocks Phase 4. No exceptions — this gate exists to prevent wasted compute on broken implementations.

**Failure mode:** A metric bug that produces inflated scores that are not caught until analysis.

---

### Phase 4: Execution (Day 9–18, SLURM Cluster)

#### Step 10: `/download-data` — Dataset and Model Cache

**Function:** Download all datasets and pretrained model weights to cluster cache before job submission.

**Inputs:** Dataset/model references from `experiment-plan.md`

**Outputs:** Cached files, download manifest with checksums

**Gate:** All checksums match; disk space sufficient for full experiment run.

---

#### Step 11: `/plan-compute` — GPU and SLURM Planning

**Function:** Estimate GPU memory, wall time, and queue strategy for each experiment. Generate SLURM scripts.

**Inputs:** `experiment-plan.md`, cluster specifications

**Outputs:** SLURM scripts in `$PROJECT_DIR/jobs/`, compute budget summary

**Gate:** Total estimated cost fits within budget; no single job exceeds partition wall time limit.

---

#### Step 12: `/run-experiment` — Experiment Execution

**Function:** Submit experiment matrix to SLURM. Monitor job status. Recover from transient failures.

**Inputs:** SLURM scripts, `experiment-state.json`

**Outputs:** Raw results in `$PROJECT_DIR/runs/`, updated `experiment-state.json`

**Gate:** All primary experiments complete with exit code 0; at least one result per hypothesis.

**Iteration Loop (Phase 4 internal):**
- `PRESET` → job failed before first checkpoint → resubmit with diagnostic logging
- `PROGRESSION` → job failed mid-run → resume from checkpoint
- `CORRECTION` → job failed due to OOM/timeout → reduce batch size / increase time limit and resubmit
- `ABANDON` → 3 consecutive failures on same job → flag for human review, continue other jobs
- Max 3 iterations per job before escalating to `ABANDON`.

---

#### Step 13: `/collect-results` — Result Aggregation

**Function:** Aggregate per-run outputs into structured tables. Compute summary statistics across runs and seeds.

**Inputs:** Raw results from `$PROJECT_DIR/runs/`

**Outputs:**
- `$PROJECT_DIR/results-tables/` — structured CSVs per experiment type
- Updated `experiment-state.json` with completion status per run

**Gate:** All primary experiments have results; per-experiment variance is within expected range (runaway variance flags a possible implementation bug).

**Epistemic updates:** Evidence Registry updated — all `planned_result` entries get status `completed` with result paths.

---

### Phase 5: Analysis, Synthesis, and Writing Cycle (Day 18–26)

Phase 5 is structured as two sub-phases: **5A: Analysis & Grounding** (Steps 14–18, partially iterative via the Analysis→Design loop) and **5B: Writing & Review Cycle** (Steps 19–27, iterative via the Phase 5 Revision Cycle). The forward flow moves through 5A, then enters the 5B loop.

#### Phase 5A: Analysis and Epistemic Grounding

---

#### Step 14: `/analyze-results` — Statistical Analysis and Figure Generation

**Function:** Run all planned statistical tests (t-tests, ANOVA, confidence intervals, effect sizes, multiple-comparison corrections). Generate analysis figures. Identify surprising or unexpected results. Identify which hypotheses were confirmed, partially confirmed, or refuted.

**Inputs:** `results-tables/`, `experiment-plan.md`, `hypotheses.md`

**Outputs:**
- `$PROJECT_DIR/analysis-report.md` — full statistical analysis, effect sizes, CIs
- `$PROJECT_DIR/figures/` — analysis figures (not yet publication-quality)
- `hypothesis-outcomes.md` — for each hypothesis: confirmed/partial/refuted + evidence

**Gate:** Effect sizes reported for all primary comparisons; confidence intervals provided; multiple-comparison correction applied where N > 3 comparisons.

**Epistemic updates:** Evidence Registry updated with statistical results as `experimental_result` entries. Confidence Tracker populated for each outcome.

**Failure mode:** Analysis produces inflated results due to a subtle multiple-comparison error, which later becomes a reviewer objection.

---

#### Step 15: `/gap-detection` — Analysis-to-Design Feedback [WP3 — NEW]

**Function:** Given the analysis results, systematically identify missing experiments. Executed by the `gap_detector.py` script followed by an LLM synthesis pass.

**Inputs:** `analysis-report.md`, `experiment-plan.md`, `hypotheses.md`, `competitive-landscape.md`

**Outputs:** `$PROJECT_DIR/gap-detection-report.md` — each gap classified as:
- **Critical:** The manuscript cannot make its primary claim without this experiment → triggers loop back to Phase 2
- **Important:** Weakens a secondary claim; should be added if compute allows
- **Minor:** Nice-to-have ablation; acceptable to note as a limitation

**Gate:** Report generated. Every gap is classified by severity.

**Feedback Loop — Analysis → Design [WP3]:**
- **Trigger:** At least one `Critical` gap identified.
- **Action:** Route back to Step 4 (`/design-experiments`) with the gap report as additional input. The experiment plan is amended, Phase 3 implementation is updated as needed, and the new experiments are executed (Steps 10–13). The new results are merged into the analysis.
- **Termination condition:** No `Critical` gaps remain after re-analysis. OR: the required experiment exceeds the remaining compute budget AND the gap is documented as a limitation in the manuscript → do not loop, continue forward.
- **Max iterations:** 2 loops back to Phase 2. Third gap detection pass: any remaining critical gaps are automatically demoted to Important and documented as limitations. This prevents infinite compute loops.
- **Escalation:** If after 2 loops a Critical gap persists and cannot be executed, flag to human researcher before proceeding.

---

#### Step 16: `/post-results-novelty` — Post-Results Novelty Reassessment [WP6 — NEW]

**Function:** Re-evaluate the actual novelty of the contribution given what the experiments showed, not what was hypothesized. Compare actual results against initial hypotheses. Identify whether the real contribution is (a) the hypothesized contribution, (b) a surprising finding that emerged from the data, or (c) a negative result with important implications.

**Inputs:** `analysis-report.md`, `hypothesis-outcomes.md`, `novelty-initial.md`, `competitive-landscape.md`

**Outputs:** `$PROJECT_DIR/novelty-reassessment.md` containing:
- Revised contribution statement based on actual results
- Delta from initial novelty assessment (what changed and why)
- Recommended framing: which result should be the lead finding
- Re-scored novelty against the competitive landscape

**Gate:** Reassessment explicitly compares to initial novelty assessment; any drift of >20% in contribution framing is flagged for human review.

**Agents:** `hypothesis-generator` (opus, extended thinking) with `hypothesis-revision` skill

**Epistemic updates:** `novelty-reassessment.md` is registered in the Evidence Registry as a meta-level finding. Claim Dependency Graph updated: the root claim nodes (contribution claims) now reference this reassessment.

**Failure mode:** Pipeline uses the original framing despite results pointing to a different, stronger contribution. Paper undersells or oversells.

---

#### Step 17: `/literature-rescan` — Results-Contextualized Literature Re-scan [WP4 — NEW]

**Function:** Perform a targeted literature re-scan focused on the *actual findings*, not the original hypothesis. Search for papers that: (a) have been published since the initial review, (b) are now relevant given what was actually found, (c) provide better baselines or comparison points for the real contribution.

**Inputs:** `analysis-report.md`, `novelty-reassessment.md`, original `research-notes.md`

**Outputs:**
- `$PROJECT_DIR/literature-rescan.md` — new papers found; updated positioning
- Updated `citation_ledger.json` with new papers
- Updated `research-notes.md` with new entries (appended, original preserved)
- `related-work-delta.md` — diff between what the related work section will say now vs. what it would have said after Step 1

**Gate:** Search covers ≥ 2 databases; time window includes papers published since Step 1; at least one search query derived from the actual findings (not just original keywords). Agent must explicitly report "no new relevant papers found" if applicable — this counts as passing the gate.

**Agents:** `literature-reviewer` (opus) invoked with results-contextualized prompt

**Citation Provenance Ledger:** Any new papers found are appended with the specific claims they support.

**Failure mode:** Related work is accurate as of day 3 but misses a closely related paper published during the project period. A reviewer finds it.

---

#### Step 18: `/method-code-reconciliation` — Method-Code Consistency Check [WP5 — NEW]

**Function:** Extract all methodological claims that will go into the manuscript (hyperparameters, architectures, training procedures, preprocessing steps, evaluation protocols) and cross-reference against the actual config files, training logs, and `experiment-state.json`. Flag every discrepancy.

**Inputs:** `experiment-state.json`, all config files in `configs/`, training logs in `runs/`, `experiment-plan.md`

**Outputs:** `$PROJECT_DIR/method-reconciliation-report.md` listing:
- Confirmed match: description matches execution
- Discrepancy: manuscript would say X, execution log says Y
- Missing detail: execution log has this information but it has not been captured for manuscript use

**Gate (hard block):** No `Discrepancy` items may proceed to manuscript production. All discrepancies must be resolved — either the config is corrected (if it was an execution error) or the planned manuscript description is updated (if the execution was correct and the description was a draft artifact).

**Script:** `method_reconcile.py` does the deterministic cross-reference. An LLM agent synthesizes the report and proposes resolutions.

**Agents:** `reproducibility-agent` (sonnet) performs the check

**Failure mode:** The methods section says "learning rate 1e-4" but the config shows 3e-4. A reader cannot reproduce the results. A reviewer asks why the learning rate seems unexpectedly low/high.

---

#### Phase 5B: Claim Architecture and Writing Cycle

The steps below (19–27) form the **Phase 5 Revision Cycle** [A2]. After an initial forward pass through Steps 19–27, the multi-dimensional review at Step 27 may route back to any step in this sub-phase. The cycle iterates until all review dimensions pass, subject to termination conditions.

---

#### Step 19: `/map-claims` — Claim-Evidence Architecture [WP10 updated]

**Function:** Map every claim the paper will make to its evidence sources. Populate the Claim Dependency Graph. Read the Confidence Tracker and assign hedging levels. Run the Skeptic Agent on the primary claims.

**Inputs:** `analysis-report.md`, `hypothesis-outcomes.md`, `novelty-reassessment.md`, `.epistemic/evidence_registry.json`, `.epistemic/citation_ledger.json`

**Outputs:**
- `$PROJECT_DIR/claim-ledger.md` — human-readable claim inventory with evidence links
- Updated `.epistemic/claim_graph.json` — populated with all claims and their evidence dependencies
- Updated `.epistemic/confidence_tracker.json` — per-claim confidence levels assigned
- `skeptic-report-claims.md` — Skeptic Agent's challenges to primary claims

**Gate:** Every primary claim has at least one evidence entry in the graph; no claim is listed as `unsupported`; Skeptic Agent's challenges are either (a) refuted with counter-evidence or (b) acknowledged and the claim is downgraded in confidence.

**Epistemic updates:** Claim Dependency Graph fully populated.

**Script:** `build_claim_graph.py` constructs the graph from the claim ledger.

**Agents:** `claim-evidence-bridge` skill; `skeptic-agent` (opus) on primary claims

**Failure mode:** A claim is added to the manuscript that was never in the ledger, bypassing all downstream verification.

---

#### Step 20: `/position` — Contribution Positioning

**Function:** Position the contribution against the competitive landscape and related work. Use the reassessed novelty (Step 16) and the results-contextualized literature (Step 17) as the primary inputs — not the original competitive landscape alone.

**Inputs:** `novelty-reassessment.md`, `literature-rescan.md`, `competitive-landscape.md`, `claim-ledger.md`

**Outputs:**
- `$PROJECT_DIR/positioning.md` — differentiation matrix, contribution statement, anticipated reviewer objections
- `related-work-outline.md` — outline of related work section organized by theme (to be drafted twice: this outline feeds the narrative; the full prose is generated at Step 24)

**Gate:** Contribution statement is grounded in reassessed novelty, not just initial hypothesis; at least 3 anticipated reviewer objections are documented with planned responses.

**Agents:** `contribution-positioning` skill (opus, extended thinking)

**Failure mode:** Positioning anchors on the original hypothesis rather than actual findings, leading to a narrative that doesn't match the results.

---

#### Step 21: `/story` — Narrative Arc and Paper Blueprint

**Function:** Define the narrative arc, triage results (which go in main paper vs. appendix), create the figure plan (which figures tell which part of the story), and produce the paper blueprint.

**Inputs:** `positioning.md`, `analysis-report.md`, `claim-ledger.md`, `hypothesis-outcomes.md`

**Outputs:**
- `$PROJECT_DIR/paper-blueprint.md` — section-by-section outline with: core claim per section, evidence to be cited, figure assignments, word budget
- `figure-plan.md` — for each major claim, the figure that provides primary visual evidence

**Gate:** Every section of the blueprint has at least one claim-evidence link from `claim_graph.json`; every figure assignment maps to an existing figure in `$PROJECT_DIR/figures/` or is flagged for generation.

**Agents:** `story-construction` skill

**Failure mode:** The narrative is organized around what is easy to write, not what the evidence best supports.

---

#### Step 22: `/narrative-gap-detect` — Writing→Analysis Feedback [WP3 — NEW]

**Function:** Before generating prose, check whether the paper blueprint requires evidence that does not exist. This is the writing-to-analysis feedback trigger.

**Inputs:** `paper-blueprint.md`, `figure-plan.md`, `.epistemic/claim_graph.json`, `.epistemic/evidence_registry.json`

**Outputs:** `$PROJECT_DIR/narrative-gap-report.md` classifying each gap as:
- **Evidence missing:** A section makes a claim with no evidence entry in the registry → triggers loop
- **Figure missing:** A figure is assigned in the plan but does not exist → flag for generation at Step 23
- **Claim unsupported:** A claim in the blueprint is in the graph but has `status: unsupported` → block or downgrade

**Script:** `narrative_gap_detector.py`

**Gate:** No `Evidence missing` gaps with severity `Critical` proceed. `Figure missing` entries are tracked for Step 23.

**Feedback Loop — Writing → Analysis [WP3]:**
- **Trigger:** At least one `Evidence missing: Critical` gap.
- **Routing logic:** If the missing evidence could come from a new analysis of existing results → route back to Step 14 (`/analyze-results`). If the missing evidence requires new experiments → route back to Step 4 (`/design-experiments`) and then through Phase 3 and Phase 4 again.
- **Termination condition:** No `Evidence missing: Critical` gaps remain. OR: the missing evidence is genuinely unobtainable and the claim is removed from the blueprint or moved to a Limitations statement.
- **Max iterations:** 1 loop back to Step 14; 1 loop back to Phase 4. Beyond this, all remaining gaps are documented as limitations. This prevents cascading reruns.
- **Escalation:** If after 2 loops a Critical narrative gap persists, flag to human researcher.

---

#### Step 23: `/argument-figure-align` — Figure-Argument Alignment [WP7 — NEW]

**Function:** For each major claim in the paper blueprint, evaluate whether the assigned figure is the most convincing visual evidence for that claim. Apply the "one figure, one point" principle. Redesign or regenerate figures that do not serve their assigned argument role.

**Inputs:** `figure-plan.md`, `paper-blueprint.md`, all figures in `$PROJECT_DIR/figures/`, `analysis-report.md`

**Outputs:**
- `figure-alignment-report.md` — for each figure: aligned/misaligned/redesign-needed
- Redesigned figures in `$PROJECT_DIR/figures/` (if any were inadequate)
- Updated `figure-plan.md`

**Gate:** Every figure in the plan is rated `aligned` — it has a clear single takeaway that matches the claim it supports. No `redesign-needed` items remain.

**Failure mode:** Figures show the data correctly but don't highlight the relevant comparison. The key result is buried in a table. A reviewer cannot see the contribution from the figures alone.

---

#### Step 24: `/produce-manuscript` — Manuscript Generation with Citation Audit [WP10 updated]

**Function:** Generate full prose manuscript: all sections in LaTeX, publication-quality figures (polished from Step 23 output), submission package. The Confidence Tracker is read before generating each claim's prose to calibrate hedging language. Related work is drafted using both the early outline from Step 20 and the rescan findings from Step 17. After prose generation, run the Citation Audit.

**Inputs:** `paper-blueprint.md`, `figure-plan.md`, all figures, `.epistemic/confidence_tracker.json`, `.epistemic/citation_ledger.json`, `related-work-outline.md`, `literature-rescan.md`

**Sub-step — Citation Audit (deterministic, after prose generation):**
- Extract all `\cite{}` commands from LaTeX
- Cross-reference each against `citation_ledger.json`
- Check: (a) every cited paper is in the ledger, (b) the cited paper's `claims_supported` includes the claim for which it is cited, (c) no citation has `audit_status: misrepresented`
- Output: `citation-audit-report.md`

**Outputs:**
- `$PROJECT_DIR/manuscript/` — LaTeX source, figures, bibliography
- `citation-audit-report.md`

**Gate:** Citation Audit passes with zero `misrepresented` entries and zero unresolved `unchecked` entries. If a citation is used for a claim not in the ledger, the agent must either verify it or remove the citation.

**Agents:** `manuscript-production` skill (opus); `ml-paper-writing` skill; `writing-anti-ai` skill

**Failure mode:** LLM generates a fluent citation to a paper that doesn't support the attributed claim. Without the Citation Audit, this would reach publication.

---

#### Step 25: `/cross-section-consistency` — Cross-Section Coherence Check [WP9 — NEW]

**Function:** Extract the core claims from each section (abstract, introduction, methods, results, discussion, conclusion) and verify bidirectional alignment. Check terminology consistency throughout. Verify all figure/table references.

**Inputs:** Manuscript LaTeX from Step 24

**Sub-checks (run by `cross_section_check.py`):**
1. Abstract → conclusion alignment: every claim in the abstract has a corresponding statement in the conclusion
2. Introduction research questions → results coverage: every research question posed in the introduction is addressed by at least one result
3. Discussion scope: no new claims in the discussion that are not grounded in results
4. Terminology consistency: key terms (model name, method name, dataset name) are used identically throughout
5. Figure/table reference integrity: every `\ref{}` exists; every figure/table is referenced in the text

**Outputs:** `$PROJECT_DIR/cross-section-report.md` with pass/fail per sub-check and specific locations of failures

**Gate:** All 5 sub-checks pass. Any failure blocks Step 26.

**Script:** `cross_section_check.py` + LLM agent for semantic alignment checks

**Failure mode:** Abstract claims X but conclusion only delivers Y. A reviewer notes the discrepancy as evidence of overclaiming. This is one of the most visible failure modes to reviewers.

---

#### Step 26: `/claim-source-align` — Claim-Source Alignment Verifier [WP1 — NEW]

**Function:** Extract every factual claim and causal assertion from the manuscript prose. Trace each to a specific result in the Evidence Registry or a specific citation in the Citation Provenance Ledger. Flag any claim that (a) cannot be traced, (b) is stronger than its evidence warrants given the Confidence Tracker, or (c) drops hedging language that the Confidence Tracker requires.

**Inputs:** Manuscript LaTeX, `.epistemic/claim_graph.json`, `.epistemic/evidence_registry.json`, `.epistemic/confidence_tracker.json`

**Sub-steps:**
1. `audit_claim_coverage.py` — flags manuscript claims not registered in `claim_graph.json`
2. `confidence_to_hedging.py` — flags claims whose prose strength exceeds their registered confidence level
3. Scope Agent review — flags generalizations beyond the scope of tested experiments
4. Skeptic Agent review — challenges the 5 highest-confidence claims; each challenge is logged

**Outputs:**
- `$PROJECT_DIR/claim-alignment-report.md` — claim inventory with trace status
- `scope-violations.md` — from Scope Agent
- `skeptic-report-manuscript.md` — from Skeptic Agent

**Gate (hard block):** Zero `untraced` claims. Zero claims rated `overclaimed`. All Scope Agent violations are either (a) refuted with evidence or (b) the claim is revised. All Skeptic Agent challenges are responded to (response logged, not required to agree with skeptic).

**Agents:** `scope-agent` (sonnet); `skeptic-agent` (opus) on top 5 claims

**Failure mode:** This is the single most important gate. Without it, the manuscript contains overclaims that a reviewer will identify and use to reject the paper.

---

#### Step 27: `/multi-dimensional-review` — Review Battery [WP2 — replaces /quality-review]

**Function:** Four independent reviewers evaluate the manuscript along distinct dimensions. Each reviewer can independently block progression with specific remediation instructions routed to the appropriate upstream step.

**Reviewer 1 — Methodological Reviewer:**
- Does the experimental design support the stated claims?
- Is the statistical methodology appropriate? Are multiple comparisons corrected?
- Are effect sizes reported? Are confidence intervals appropriate?
- Are there confounds that are acknowledged but not controlled?
- Score: 1–10. Block threshold: < 7.

**Reviewer 2 — Argument Structure Reviewer:**
- Does the introduction's framing lead to the correct research questions?
- Do the results address the stated research questions?
- Does the discussion overreach? Are limitations adequately stated?
- Is the related work section fair to competing approaches?
- Score: 1–10. Block threshold: < 7.

**Reviewer 3 — Coherence Reviewer:**
- Is terminology consistent throughout?
- Does the abstract match the conclusions?
- Are all figure/table references valid? (Cross-checks Step 25 output)
- Is the paper self-contained (does not require external knowledge to follow)?
- Score: 1–10. Block threshold: < 7.

**Reviewer 4 — Novelty/Positioning Reviewer:**
- Given the actual results, is the claimed contribution novel?
- Does the related work fairly represent the state of the art?
- Is the contribution undersold or oversold relative to the evidence?
- Score: 1–10. Block threshold: < 7.

**Inputs:** Manuscript LaTeX, `claim-alignment-report.md`, `cross-section-report.md`, `review-battery-report.md` from previous cycles (if any)

**Outputs:**
- `$PROJECT_DIR/review-battery-report.md` — four independent score sheets with specific line-referenced objections
- Per-dimension remediation routing table: each objection mapped to the step it routes back to

**Gate:** All four reviewers score ≥ 7/10. Any reviewer scoring < 7 blocks with specific remediation instructions.

**Remediation Routing:**
| Dimension | Typical routing target |
|-----------|----------------------|
| Methodological failure | Step 4 (design) or Step 14 (re-analysis) |
| Argument failure | Step 21 (story) or Step 24 (manuscript) |
| Coherence failure | Step 24 (manuscript revision) or Step 25 (re-check) |
| Novelty/positioning failure | Step 20 (position) or Step 24 (related work revision) |

**Agents:** Four independent LLM invocations with reviewer-specific system prompts (do not share context during the review pass — each reviewer sees only the manuscript, not other reviewers' scores)

**Phase 5 Revision Cycle termination [A2]:**
- **Pass:** All four dimensions ≥ 7 → proceed to Phase 6.
- **Soft failure:** 1–2 dimensions < 7 → route to specific upstream step, revise, re-run affected checks (Steps 25–27). Track revision cycle count.
- **Max revision cycles:** 3 complete passes through Steps 19–27. After cycle 3, any remaining dimension failures < 5 are escalated to human review. Failures in range 5–6.9 are documented as known weaknesses in a cover letter and the pipeline proceeds.
- **Reset condition:** If a revision introduces new coherence or claim failures (score decreases), revert to previous draft and take a more targeted fix.

---

### Phase 6: Pre-Submission and Publication (Day 26–32)

#### Step 28: `/adversarial-review` — Pre-Submission Adversarial Review [WP8 — restructured]

**Function:** Simulate 2–3 hostile-but-fair reviewers before compilation. Each simulated reviewer is distinct in priority. Weaknesses identified here are routed back upstream — the paper is revised before compilation, not after.

This step replaces the old Step 21 (`/rebuttal`). The rebuttal module (preparing actual reviewer responses post-submission) is moved to post-submission and is no longer part of the pre-submission pipeline.

**Reviewer profiles:**
- **Novelty Skeptic:** Questions whether the contribution is actually new; will cite obscure prior work. Challenge: "This is just a minor variation of [Wang 2023] with different hyperparameters."
- **Methods Pedant:** Demands methodological rigor; will find every statistical weakness. Challenge: "The improvement is within the confidence interval; why is this claim not hedged?"
- **Clarity Judge:** Evaluates whether a reader unfamiliar with the specific subfield can follow the paper. Challenge: "The notation in Section 3 is undefined at first use."

**Inputs:** Manuscript LaTeX, `review-battery-report.md`, `claim-alignment-report.md`, `novelty-reassessment.md`

**Outputs:**
- `$PROJECT_DIR/simulated-reviews/reviewer_1.md` (Novelty Skeptic)
- `$PROJECT_DIR/simulated-reviews/reviewer_2.md` (Methods Pedant)
- `$PROJECT_DIR/simulated-reviews/reviewer_3.md` (Clarity Judge)
- `$PROJECT_DIR/adversarial-review-report.md` — aggregated critical items with severity ratings and routing targets

**Gate:** Every `Critical` item in the adversarial review report is either (a) resolved by routing back to the appropriate upstream step and revising, or (b) explicitly accepted as a known limitation documented in the paper. No `Critical` items may remain unaddressed.

**Feedback routing:**
| Item type | Routing target |
|-----------|---------------|
| Missing experiment | Step 4 + Phase 3/4 (if compute allows); else document as limitation |
| Framing/positioning weakness | Step 20 (position), then re-run Steps 21–27 |
| Writing clarity issue | Step 24 (manuscript revision), then re-run Steps 25–27 |
| Statistical challenge | Step 14 (re-analysis) or Step 27 reviewer 1 remediation |

**Termination condition:** Max 2 routing cycles from adversarial review. After that, unresolved `Critical` items are escalated to human researcher. `Important` and `Minor` items are logged in `adversarial-review-report.md` but do not block compilation.

**Agents:** `reviewer-simulation-agent` (opus); `reproducibility-agent` (sonnet) runs its checklist concurrently

---

#### Step 29: `/concurrent-work-check` — Final Concurrent Work Check [WP4 — NEW]

**Function:** Within 48 hours of target submission date, run a targeted search for any papers posted to arXiv or published since Step 17 (literature re-scan) that are directly competitive or closely related. This is the last opportunity to update the related work section before submission.

**Inputs:** `novelty-reassessment.md`, `competitive-landscape.md`, submission date

**Script:** `concurrent_work_check.py` generates targeted arXiv search queries from the key terms of the actual contribution (not the original hypothesis).

**Outputs:** `$PROJECT_DIR/concurrent-work-report.md` — new papers found with their relevance classification

**Gate:** Search is run within 48 hours of submission. If a directly competing paper is found: (a) update the related work section to cite and differentiate, (b) update `positioning.md`, and (c) if the paper fully scoops the contribution, escalate to human researcher for go/no-go decision.

**Failure mode:** A reviewer is an author of a paper posted 2 weeks ago that directly competes; the paper ignores it. Instant desk rejection or a hostile review.

---

#### Step 30: `/compile-manuscript` — LaTeX Compilation

**Function:** Compile LaTeX to PDF. Run `biber`/`bibtex`. Run `chktex`. Generate Overleaf-ready ZIP package. Verify PDF page count against venue limits.

**Inputs:** `$PROJECT_DIR/manuscript/`

**Outputs:** `manuscript.pdf`, `overleaf-package.zip`, `compile-report.md`

**Gate:** LaTeX compiles without errors; zero `chktex` critical warnings; PDF page count ≤ venue limit; all `\cite{}` entries resolve; no overfull `\hbox` warnings in figure-containing pages.

---

#### Step 31: `/presentation` — Conference Presentation

**Function:** Generate slide deck outline and speaker notes based on the final paper.

**Inputs:** `manuscript.pdf`, `paper-blueprint.md`

**Outputs:** `$PROJECT_DIR/presentation/` — slide outline, key figures, speaker notes

---

#### Step 32: `/poster` — Academic Poster

**Function:** Generate academic poster layout from the paper's key results and figures.

**Inputs:** `manuscript.pdf`, `figures/`

**Outputs:** `$PROJECT_DIR/poster/` — poster layout specification

---

#### Step 33: `/announce` — Promotion Content

**Function:** Draft promotion content for X, LinkedIn, and a blog post based on the paper.

**Inputs:** `manuscript.pdf`, `contribution-statement.md` from Step 20

**Outputs:** `$PROJECT_DIR/promotion/` — platform-specific posts

---

## Part 5: All Feedback Loops

### Loop 1: Analysis → Experiment Design [WP3]

**Trigger step:** Step 15 (`/gap-detection`)
**Trigger condition:** At least one gap classified as `Critical` in `gap-detection-report.md`
**Routing target:** Step 4 (`/design-experiments`), then Steps 5–9 (implementation, if needed), then Steps 10–13 (execution), then re-run Step 14 and Step 15
**Termination conditions:**
1. No `Critical` gaps remain in the re-run of Step 15
2. Required experiment exceeds remaining compute budget AND the gap is documented as a limitation → do not loop, continue forward
3. Max 2 iterations of this loop. Third occurrence: all remaining Critical gaps are documented as limitations. Human escalation flag set.
**State tracking:** `pipeline-state.json` records loop count at `gap_detection_loops`.

---

### Loop 2: Writing → Analysis [WP3]

**Trigger step:** Step 22 (`/narrative-gap-detect`)
**Trigger condition:** At least one gap classified as `Evidence missing: Critical` in `narrative-gap-report.md`
**Routing target:**
- If missing evidence is derivable from existing results → Step 14 (`/analyze-results`), then re-run Steps 15–22
- If missing evidence requires new experiments → Step 4 (`/design-experiments`), then Phase 3/4, then re-run Steps 14–22
**Termination conditions:**
1. No `Evidence missing: Critical` gaps remain
2. The required evidence is genuinely unobtainable → claim removed from blueprint or moved to Limitations
3. Max 1 iteration back to Step 14; max 1 iteration back to Phase 4. Beyond this, escalate to human researcher.
**State tracking:** `pipeline-state.json` records loop count at `narrative_gap_loops`.

---

### Loop 3: Phase 5 Revision Cycle [A2 / WP2]

**Trigger step:** Step 27 (`/multi-dimensional-review`)
**Trigger condition:** Any of the four reviewers scores < 7/10
**Routing targets (per dimension):**
- Methodological failure → Step 4 (design) or Step 14 (analysis), then re-run Steps 19–27
- Argument failure → Step 21 (story) or Step 24 (manuscript prose), then re-run Steps 22–27
- Coherence failure → Step 24 (manuscript revision), then re-run Steps 25–27
- Novelty/positioning failure → Step 20 (position), then re-run Steps 21–27
**Termination conditions:**
1. All four reviewers score ≥ 7/10
2. Max 3 complete passes through Steps 19–27. After cycle 3: scores < 5 → escalate to human; scores 5–6.9 → document as known weakness in cover letter, proceed to Phase 6
**State tracking:** `pipeline-state.json` records `revision_cycle_count` and per-reviewer scores per cycle. If a revision causes a previously-passing dimension to drop, revert to previous draft version.

---

### Loop 4: Adversarial Review → Upstream [WP8]

**Trigger step:** Step 28 (`/adversarial-review`)
**Trigger condition:** At least one item classified as `Critical` in `adversarial-review-report.md`
**Routing targets:**
- Missing experiment → Step 4 (compute permitting); else document as limitation
- Framing weakness → Step 20, then re-run Steps 21–28
- Writing/clarity → Step 24, then re-run Steps 25–28
- Statistical challenge → Step 14, then re-run Steps 15–28
**Termination conditions:**
1. No `Critical` items remain unaddressed
2. Max 2 routing cycles. After cycle 2, remaining Critical items escalate to human researcher. Important and Minor items are logged but do not block.
**State tracking:** `pipeline-state.json` records `adversarial_review_cycles`.

---

## Part 6: Dependency and Flow Description

### Main Forward Flow

Phase 1 (Steps 1–3) → Phase 2 (Step 4) → Phase 3 (Steps 5–9) → Phase 4 (Steps 10–13) → Phase 5A (Steps 14–18) → Phase 5B initial pass (Steps 19–27) → Phase 6 (Steps 28–33).

Epistemic infrastructure (Evidence Registry, Claim Dependency Graph, Confidence Tracker, Citation Provenance Ledger) is initialized during Phase 1 and updated at every result-producing or claim-generating step throughout. The Consistency Oracle is queryable at any stage and is run in full sweep mode before Steps 24 and 28.

### Feedback Loops (upstream routing)

```
Step 15 (gap-detection)         → Step 4  [loop 1: missing experiments]
Step 22 (narrative-gap-detect)  → Step 14 or Step 4  [loop 2: evidence gaps]
Step 27 (multi-dim-review)      → Steps 4/14/20/21/24  [loop 3: revision cycle]
Step 28 (adversarial-review)    → Steps 4/14/20/24  [loop 4: pre-submission fixes]
```

Phase 4 also has its own internal loop (PRESET/PROGRESSION/CORRECTION/ABANDON) for execution failures, unchanged from v2.

### Independent Blocking Modules

The following modules can independently block pipeline progression without requiring any other module to act:

| Module | Step | Blocks if... |
|--------|------|-------------|
| Pre-flight validation | Step 9 | Any smoke test fails |
| Method-Code Reconciliation | Step 18 | Any discrepancy found |
| Claim-Source Alignment Verifier | Step 26 | Any untraced or overclaimed claim |
| Cross-Section Consistency Checker | Step 25 | Any cross-section alignment failure |
| Multi-Dimensional Review (any dimension) | Step 27 | Any reviewer scores < 7 |
| Citation Audit | Step 24 (sub-step) | Any misrepresented citation |
| Concurrent Work Check | Step 29 | Direct competitive paper found (routes to human, not block) |

### Persistent Services vs. Phase-Specific Steps

**Persistent services (initialized once, queried/updated throughout):**
- Evidence Registry
- Claim Dependency Graph
- Confidence Tracker
- Citation Provenance Ledger
- Consistency Oracle (queryable at any step)

**Phase-specific steps (execute once per forward pass, may be re-entered by loops):**
All Steps 1–33

**Phase-specific steps that can be re-entered (loop targets):**
- Step 4 (design): re-entered by Loops 1 and 4
- Step 14 (analysis): re-entered by Loops 2, 3, and 4
- Step 20 (position): re-entered by Loops 3 and 4
- Step 21 (story): re-entered by Loop 3
- Step 24 (manuscript): re-entered by Loops 3 and 4

---

## Part 7: Updated Timeline

| Phase | Days | Notes |
|-------|------|-------|
| Phase 1: Ideation | Day 1–4 | +1 day for Citation Provenance Ledger initialization |
| Phase 2: Design | Day 4–5 | Unchanged |
| Phase 3: Implementation | Day 5–9 | Unchanged |
| Phase 4: Execution | Day 9–18 | Unchanged (SLURM-bound) |
| Phase 5A: Analysis & Grounding | Day 18–21 | +2 days for Steps 15–18 (gap detection, novelty reassessment, lit rescan, method reconciliation) |
| Phase 5B: Writing & Review Cycle | Day 21–27 | +3 days for new steps + revision cycle (budget 2 revision cycles) |
| Phase 6: Pre-Submission | Day 27–32 | Adversarial review moved before compilation; +1 day for concurrent work check |
| **Total** | **Day 1–32** | **+4 days over v2 baseline** |

Iteration time: each full Phase 5B revision cycle adds 1–2 days. Each loop back to Phase 4 adds 3–5 days (SLURM execution). The timeline above budgets for 2 Phase 5B revision cycles and no Phase 4 re-runs. A full Phase 4 re-run would extend the timeline by 5–9 days.

---

## Part 8: Changelog

All changes organized by which critique item they address.

| Change | New/Modified Step(s) | Critique Items Addressed |
|--------|---------------------|--------------------------|
| Claim-Source Alignment Verifier: extracts every factual claim, traces to evidence, flags untraced or overclaimed | Step 26 (new) | WP1 |
| Claim Dependency Graph: directed graph tracking claim→evidence dependencies | A1 infrastructure | WP1, A1 |
| Confidence Tracker: per-claim confidence propagates into hedging language at manuscript generation | A1 infrastructure | WP1, A1 |
| Multi-dimensional review battery: four independent reviewers (Methodological, Argument, Coherence, Novelty) each can independently block with routed remediation | Step 27 (replaces /quality-review) | WP2 |
| Per-dimension remediation routing: each review failure routes to the specific upstream step responsible | Step 27 routing table | WP2, A2 |
| Gap Detection module: after analysis, identifies missing ablations/baselines/confounds; triggers Analysis→Design loop | Step 15 (new) | WP3 |
| Narrative Gap Detector: before manuscript, checks that every story element has evidence; triggers Writing→Analysis loop | Step 22 (new) | WP3 |
| Analysis→Design feedback loop with termination conditions | Loop 1 | WP3, A2 |
| Writing→Analysis feedback loop with termination conditions | Loop 2 | WP3, A2 |
| Literature Re-scan: results-contextualized search before positioning; searches for papers relevant to actual findings | Step 17 (new) | WP4 |
| Concurrent Work Check: within 48h of submission, final search for competitive papers | Step 29 (new) | WP4 |
| Related work drafted twice: outline from Step 20 (framing), full prose from Step 24 using Step 17 rescan | Steps 20, 24 (modified) | WP4 |
| Method-Code Reconciliation: cross-references manuscript method claims against config files, training logs, experiment-state.json | Step 18 (new) | WP5 |
| Post-Results Novelty Reassessment: re-evaluates actual contribution given what experiments showed; feeds positioning | Step 16 (new) | WP6 |
| Positioning now reads novelty-reassessment.md as primary input | Step 20 (modified) | WP6 |
| Argument-Figure Alignment: for each major claim, evaluates whether assigned figure provides most convincing visual evidence | Step 23 (new) | WP7 |
| Pre-Submission Adversarial Review: 3 hostile-but-fair simulated reviewers before compilation; weaknesses routed upstream | Step 28 (moved/restructured from /rebuttal) | WP8 |
| Adversarial review → upstream routing loop with termination | Loop 4 | WP8 |
| Rebuttal (/rebuttal) demoted to post-submission; pre-submission review now uses Reviewer Simulation Agent | Step 28 vs. old Step 21 | WP8 |
| Cross-Section Consistency Checker: 5 sub-checks for bidirectional claim alignment, terminology, reference integrity | Step 25 (new) | WP9 |
| Citation Provenance Ledger: initialized at Step 1; tracks which paper supports which claim; audited at Step 24 | Persistent infrastructure + Step 24 sub-step | WP10 |
| Citation Audit: post-generation check — every \cite{} matched against ledger, misrepresented citations flagged | Step 24 (sub-step, new) | WP10 |
| Evidence Registry: persistent inventory of all evidence with type, strength, and dependent claims | A1 infrastructure | A1 |
| Consistency Oracle: persistent service queryable at any stage to check consistency of new content | A3 infrastructure | A3 |
| Phase 5 Revision Cycle: Steps 19–27 form an iterative loop with termination conditions replacing linear sequence | Steps 19–27 (restructured) | A2 |
| Skeptic Agent: challenges any claim, tries to falsify; invoked at Steps 19 and 26 | Verification agent (new) | A4 |
| Reproducibility Agent: checks whether manuscript provides sufficient reproduction detail | Verification agent (new) | A4, WP5 |
| Reviewer Simulation Agent: models 3 hostile-but-fair reviewers at Step 28 | Verification agent (new) | A4, WP8 |
| Scope Agent: flags generalizations beyond what experiments tested; invoked at Steps 26 and 28 | Verification agent (new) | A4, WP1 |
| All feedback loops have explicit max iteration counts and escalation policies | Loops 1–4 | All WP3, WP8; A2 |
| `check_registry_freshness.py`: blocks claim-generation steps if Evidence Registry is stale | New deterministic script | A1 |
| `build_claim_graph.py`: constructs claim→evidence graph from claim ledger | New deterministic script | A1, WP1 |
| `audit_claim_coverage.py`: flags manuscript claims not registered in claim graph | New deterministic script | WP1 |
| `audit_citations.py`: flags unused, misrepresented, or hallucinated citations | New deterministic script | WP10 |
| `method_reconcile.py`: cross-references described vs. actual hyperparameters | New deterministic script | WP5 |
| `cross_section_check.py`: checks bidirectional alignment across manuscript sections | New deterministic script | WP9 |
| `confidence_to_hedging.py`: flags claims where prose strength exceeds registered confidence | New deterministic script | WP1, A1 |
| `gap_detector.py`: identifies missing experiments from analysis vs. experiment plan | New deterministic script | WP3 |
| `narrative_gap_detector.py`: flags story elements requiring non-existent evidence | New deterministic script | WP3 |
| `concurrent_work_check.py`: generates targeted arXiv queries from actual contribution terms | New deterministic script | WP4 |

---

*Pipeline v3 — 33 steps across 6 phases. 11 new modules. 4 feedback loops. 6 persistent epistemic infrastructure components. 4 verification agents. 10 new deterministic scripts.*
