---
name: recency-sweep
description: Pass 5 of the multi-pass research system. Targeted search for work published in the last 3–6 months. Called at three points in the pipeline — after hypothesis formulation (sweep-1), after results (sweep-2), and within 48h of submission (sweep-final). Produces concurrent-work-report.md.
args:
  - name: sweep_id
    description: "Which sweep: 1 (post-hypothesis), 2 (post-results), or final (pre-submission)"
    required: true
  - name: lookback_days
    description: How many days back to search (default 90)
    required: false
    default: "90"
tags: [Research, Novelty, Concurrent Work, Pipeline]
---

# /recency-sweep — Recency and Concurrent Work Check (Pass 5)

## Purpose

Research projects take weeks. New papers appear daily. The recency sweep is a **time-aware search** that specifically targets work published during the project period. It is the mechanism that catches a paper that appeared on arXiv while you were running experiments — the paper a reviewer read last week that isn't in any review database yet.

This command is called **three times** across the pipeline:
- **Sweep 1** (after hypothesis formulation, Day 3–4): establish the concurrent work baseline
- **Sweep 2** (after results, Day 16–17): catch papers that appeared during execution
- **Sweep Final** (within 48 hours of submission, Day 28+): last chance before submission

## Project Directory

Read `pipeline-state.json` → `project_dir`.

**Required inputs:**
- `$PROJECT_DIR/hypotheses.md`
- `$PROJECT_DIR/novelty-reassessment.md` (for Sweep 2 and Final — actual contribution, not just hypothesis)
- `$PROJECT_DIR/competitive-landscape.md` (if available)

**Outputs (per sweep):**
- `$PROJECT_DIR/concurrent-work-report-sweep{sweep_id}.md`
- `$PROJECT_DIR/concurrent-work-report.md` (canonical, updated by each sweep)
- Updated `$PROJECT_DIR/.epistemic/citation_ledger.json`

---

## Execution

### Step 1: Build Watchlist Queries

Generate search queries from the **actual contribution** (not just the topic). For Sweep 2 and Final, read `novelty-reassessment.md` to get the actual contribution framing — do not use only the original hypothesis.

**Query categories:**

1. **Key terms from actual contribution:**
   - Extract the 3–5 most specific technical terms in the actual contribution
   - Run each as a separate search

2. **Method + task combinations:**
   - "[method name] [task name] 2024 2025 2026"
   - "[method name] [task name] preprint"

3. **Closest prior work forward citations:**
   - Search for papers that cite the closest prior work (from `adversarial-novelty-report.md`)
   - New papers citing the same prior work may be concurrent

4. **Lab/author monitoring:**
   - If the closest prior work has known authors, search for their recent work

**Target window:** Publications in the last `$lookback_days` days.

### Step 2: Source-Specific Recency Search

Hit all sources that have recency-aware interfaces:

| Source | Method | Date Filter |
|--------|--------|-------------|
| arXiv | `WebSearch site:arxiv.org [terms] 2024 2025 2026` | Implicit in date terms |
| arXiv new submissions | `WebFetch https://arxiv.org/search/?query=[terms]&searchtype=all&start=0` | Sort by submission date |
| OpenReview | `WebSearch site:openreview.net [terms] 2025` | Recent submissions |
| Semantic Scholar | API with `year` filter if available | `year_filter: [current_year-1, current_year]` |
| Twitter/X (academic) | `WebSearch site:x.com OR site:twitter.com [terms] "arxiv" lang:en` | Recent threads |
| Research lab blogs | Anthropic, DeepMind, FAIR, Google Research, MSR — check for recent posts | Manual check |

**Do not skip the lab blogs for Sweep Final.** A paper announced on a lab blog may not yet be indexed.

### Step 3: Filter and Assess

For each paper found in the recency window:

**Is it genuinely new?** Check `citation_ledger.json` — if already recorded, skip (update `last_seen_sweep` field only).

**Relevance screen:** Is this paper relevant to the proposed contribution? Apply the same decomposition from Pass 2: does it overlap with any of the [method, task, result, mechanism] components?

**If relevant:** Read the abstract. Assign severity:

| Severity | Description | Action |
|----------|-------------|--------|
| `blocks_project` | Paper proposes same method, same task, comparable results | Escalate to Gate N1/N3/N4 immediately. KILL or emergency reposition. |
| `requires_repositioning` | Paper overlaps substantially; contribution needs reframing | Route to positioning step; update related work |
| `should_be_cited` | Paper is related and strengthens our case, or is adjacent but a reviewer might expect it cited | Add to citation ledger; plan to cite in related work |
| `no_impact` | Paper is recent but not relevant to our contribution | Log and dismiss |

### Step 4: Concurrent Work Classification

For papers classified `blocks_project` or `requires_repositioning`:

1. Read in full (WebFetch)
2. Determine if it is:
   - **Direct competition:** Proposes the same approach to the same problem
   - **Independent confirmation:** Arrives at a similar conclusion through a different path — actually *strengthens* the paper (frame as "concurrent validation")
   - **Supersets our contribution:** Does everything we do and more
   - **Subset of our contribution:** Does part of what we do but is narrower

Only "direct competition" and "supersets" are blocking. Independent confirmation should be framed positively in the related work section.

### Step 5: Watchlist Cache

Cache the queries and date ranges used in this sweep so they can be re-run efficiently in subsequent sweeps:

```bash
python scripts/recency_sweep.py \
  --sweep-id $sweep_id \
  --queries queries_used.json \
  --results concurrent_work_raw.json \
  --cache $PROJECT_DIR/.cache/recency_sweeps/
```

For Sweep 2 and Final: compare against Sweep 1 (or Sweep 2) cache to identify papers that appeared *after* the previous sweep.

---

## Output: `concurrent-work-report.md` (updated by each sweep)

```markdown
# Concurrent Work Report

**Last updated:** YYYY-MM-DD (Sweep N)
**Project start date:** YYYY-MM-DD
**Current date:** YYYY-MM-DD

## Sweep History

| Sweep | Date | Papers Found | Severity | Action Taken |
|-------|------|-------------|---------|--------------|
| Sweep 1 | ... | N | [max severity] | [action] |
| Sweep 2 | ... | N | [max severity] | [action] |
| Sweep Final | ... | N | [max severity] | [action] |

## Active Concurrent Work (Requires Attention)

### [Paper Title] — [Author et al., YYYY-MM]
- **arXiv ID / URL:** ...
- **First found:** Sweep N
- **Severity:** blocks_project / requires_repositioning / should_be_cited
- **Overlap description:** [what specifically overlaps]
- **Classification:** direct_competition / independent_confirmation / superset / subset
- **Action taken:** [framed as concurrent validation / repositioned / escalated to kill gate]
- **Related work update:** [how this paper will be cited in the manuscript]

## Dismissed Papers (no_impact)

[Title, date, reason for dismissal]

## Kill Signal Events

[Any paper that triggered a `blocks_project` classification, with outcome]

## Pre-Submission Checklist (Sweep Final only)

- [ ] All papers published in the last 30 days in the relevant area have been checked
- [ ] Lab blogs checked: Anthropic, DeepMind, FAIR, Google Research, MSR, OpenAI
- [ ] OpenReview checked for submissions to upcoming [venue] deadline
- [ ] Citation ledger updated with all new papers
- [ ] Related work section updated in manuscript (if needed)
- [ ] Positioning updated if any `requires_repositioning` papers found
```

---

## Gate Criteria

Before marking complete:

- [ ] All query categories executed
- [ ] All source types searched
- [ ] All relevant papers classified by severity
- [ ] `blocks_project` papers: escalated immediately (do not wait)
- [ ] `concurrent-work-report.md` updated
- [ ] Citation ledger updated

**Special rule for Sweep Final:** If a `blocks_project` paper is found within 72 hours of the submission deadline, escalate to human researcher immediately. Do not attempt autonomous repositioning on this timeline.

---

## Integration

- **Sweep 1** follows `/adversarial-search` — runs at end of Phase 1 (Day 3–4)
- **Sweep 2** runs after `/post-results-novelty` — in Phase 5A (Day 16–17)
- **Sweep Final** runs in Phase 6 before `/compile-manuscript` — within 48h of submission
- **All sweeps feed into:** `/novelty-gate` (appropriate gate: N1, N3, N4)
- **Concurrent work report** used by: Paper Quality Verifier (Dimension 1, criterion N3)
- **Agent:** `literature-reviewer` (opus)
