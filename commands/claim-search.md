---
name: claim-search
description: Pass 2 of the multi-pass research system. Claim-level decomposition and targeted search. Decomposes the proposed hypothesis into atomic claims and searches for each independently. The output is the primary novelty threat assessment.
args:
  - name: hypothesis_file
    description: Path to hypotheses.md (defaults to $PROJECT_DIR/hypotheses.md)
    required: false
    default: ""
tags: [Research, Novelty, Literature, Pipeline, Phase1]
---

# /claim-search — Claim-Level Decomposition and Search (Pass 2)

## Purpose

Pass 1 mapped the territory. Pass 2 **targets the contribution**. It decomposes the proposed hypothesis into its atomic claims and runs a separate targeted search for each claim component. This is the pass most likely to find papers that directly threaten novelty — papers that may not share vocabulary with the research topic but make the same underlying claim.

This pass populates `claim-overlap-report.md`, the primary input to the novelty gate (Gate N1) and the Paper Quality Verifier.

## Project Directory

Read `pipeline-state.json` → `project_dir`. All outputs go to `$PROJECT_DIR`.

**Required inputs:**
- `$PROJECT_DIR/hypotheses.md` (from `/formulate-hypotheses`)
- `$PROJECT_DIR/research-landscape.md` (from `/research-landscape`)
- `$PROJECT_DIR/.epistemic/citation_ledger.json`

**Outputs:**
- `$PROJECT_DIR/claim-overlap-report.md`
- Updated `$PROJECT_DIR/.epistemic/citation_ledger.json`

---

## Execution

### Step 1: Hypothesis Parsing

Read `hypotheses.md`. For the primary hypothesis, extract the core claim in this canonical form:

> "We show that **[method/technique]** achieves **[result/outcome]** on **[task/domain]** by **[mechanism/insight]**."

If the hypothesis doesn't fit this template, force-fit it: identify the closest approximation for each slot. If a slot is absent (no stated mechanism), mark it as `[UNSPECIFIED]`.

### Step 2: Claim Decomposition

Decompose the canonical claim into searchable atomic components:

| Component | Search question |
|-----------|----------------|
| Method | Who else has used [method/technique] on any task? |
| Task/Domain | Who else has worked on [task/domain] with any method? |
| Result | Who else has achieved [result type] or similar improvements? |
| Mechanism | Who else has exploited [mechanism]? |
| Method × Task | Who has combined [method] with [task] specifically? |
| Method × Result | Who claims [method] achieves [result] anywhere? |
| Task × Result | Who claims [result] is achievable on [task] by any means? |

Generate search queries for each row. Each query must be distinct — do not reuse the same phrasing.

Also search for papers that overlap on 2+ components — these are the highest novelty threats.

### Step 3: Execute Claim-Level Searches

**Mandatory: Use WebSearch for every row in the decomposition table.**

Do not skip any row. If a search returns zero results, log the query and result explicitly — zero results is a valid finding.

Additional targeted sources:
- **OpenReview** (`site:openreview.net`): catches submissions under review that may not yet be indexed elsewhere
- **arXiv recent** (`arxiv.org cs.* 2024 2025`): catches preprints
- **Semantic Scholar** with the exact method name in quotes

Minimum queries: 2× the number of decomposition rows (run each with at least 2 phrasings).

### Step 4: De-duplication

Run de-duplication against papers already found in Pass 1:

```bash
python scripts/dedup_papers.py \
  --new-results claim_search_raw.json \
  --existing $PROJECT_DIR/.epistemic/citation_ledger.json \
  --output claim_search_deduped.json
```

If the script is unavailable, manually check: for each newly found paper, is it already in the citation ledger? If yes, update its `claims_supported` field with the newly identified claim overlap — do not create a duplicate entry.

### Step 5: Overlap Assessment

For each paper found that overlaps with the proposed contribution:

1. **Read the paper in detail** (Tier 1 treatment — use WebFetch on arXiv or PDF link).
2. Assign an overlap level:
   - **HIGH:** The paper covers ≥ 2 decomposition components for the same claim. This is a direct threat.
   - **MEDIUM:** The paper covers 1 decomposition component with meaningful overlap.
   - **LOW:** The paper is related but does not directly overlap with the proposed claim.

3. Write a differential statement for every HIGH or MEDIUM overlap paper:
   > "[Prior work] does A but not B. Our work does B. The specific technical difference is [X]. This leads to [outcome difference Y]."

   If this statement cannot be written clearly and honestly for a HIGH-overlap paper, **flag this as a potential kill signal** and escalate in the report.

4. Record the overlap level in `citation_ledger.json` under a new field: `claim_overlap_level`.

### Step 6: Composite Threat Assessment

After assessing all found papers, produce a composite threat assessment:

- **Overall threat level:** CRITICAL / HIGH / MEDIUM / LOW
  - CRITICAL: A paper covers all 4 decomposition components for the primary claim. Near-full anticipation.
  - HIGH: A paper covers 3 components, or multiple papers together cover all components.
  - MEDIUM: Papers exist that cover 1–2 components; differentiation is possible but requires explicit articulation.
  - LOW: No paper found that covers more than 1 component; novelty appears strong.

---

## Output: `claim-overlap-report.md`

```markdown
# Claim-Level Search Report (Pass 2)

**Date:** YYYY-MM-DD
**Hypothesis:** [full hypothesis text]

## Canonical Claim Decomposition

| Component | Value | Search Queries Run | Papers Found |
|-----------|-------|-------------------|-------------|
| Method | ... | N queries | N papers |
| Task/Domain | ... | N queries | N papers |
| Result | ... | N queries | N papers |
| Mechanism | ... | N queries | N papers |
| Method × Task | ... | N queries | N papers |
[...]

## High-Threat Papers

For each paper with overlap level HIGH:

### [Author et al., YYYY] — [Title] — [Venue]
- **Overlap components:** [list of matched components]
- **Overlap level:** HIGH
- **What they do:** [specific description]
- **What we do differently:** [explicit differential statement]
- **Is differentiation sufficient?** YES / NO / UNCERTAIN
- **Action required:** [cite and differentiate / reposition / kill signal]
- **Cite key:** `authorYEARkeyword`

## Medium-Threat Papers

[Same format, briefer]

## Low-Threat Papers (list only)

[Author et al., YYYY] — [Title] — overlap on: [component(s)]

## Composite Threat Assessment

**Overall threat level:** CRITICAL / HIGH / MEDIUM / LOW
**Reasoning:** [2–3 sentences explaining the threat level]
**Primary threat paper:** [single most dangerous prior work]
**Differentiability:** [can we clearly state how we differ from every HIGH-threat paper?]

## Kill Signal Flags

[List any cases where the differential statement could not be written clearly, or where a HIGH-threat paper appears to fully anticipate the contribution]

## Search Coverage

**Total new queries run:** N (minimum required: 14+)
**New papers found:** N
**Papers read in full:** N
**HIGH overlap papers:** N
**MEDIUM overlap papers:** N

## Epistemic Updates

Citation ledger updated with N new entries.
Existing entries updated with claim_overlap_level: N entries.
```

---

## Gate Criteria

Before marking complete:

- [ ] ≥ 2 queries per decomposition row executed
- [ ] All HIGH/MEDIUM overlap papers read in full
- [ ] Differential statement written for every HIGH overlap paper
- [ ] Composite threat assessment produced
- [ ] `claim-overlap-report.md` written
- [ ] Citation ledger updated with claim_overlap_level fields

---

## Integration

- **Follows:** `/formulate-hypotheses` (requires `hypotheses.md`)
- **Runs in parallel with:** `/citation-traversal` (Pass 3)
- **Feeds into:** `/novelty-gate` (Gate N1), Paper Quality Verifier (Dimension 1)
- **Claim-Source Alignment Verifier** (Step 26 of pipeline) uses `claim-overlap-report.md` as ground truth for N3 criterion
- **Agent:** `literature-reviewer` (opus) + `claim-evidence-bridge` skill
