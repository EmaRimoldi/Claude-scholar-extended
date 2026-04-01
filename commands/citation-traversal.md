---
name: citation-traversal
description: Pass 3 of the multi-pass research system. Citation graph traversal — takes the 10–20 most relevant papers found in Passes 1–2 as seeds, retrieves their forward citations and backward references, and scans second-order papers for relevance. Finds papers that keyword search misses.
args:
  - name: seed_count
    description: Number of seed papers to use (default 15, max 20)
    required: false
    default: "15"
tags: [Research, Literature, Pipeline, Phase1]
---

# /citation-traversal — Citation Graph Exploration (Pass 3)

## Purpose

Passes 1 and 2 used keyword and semantic search. Pass 3 uses **intellectual lineage** — it follows citation links to find papers that share conceptual ancestry with the research but don't share surface vocabulary. These are the papers that keyword search systematically misses.

This pass is run in parallel with Pass 2 (`/claim-search`). It appends its findings to `claim-overlap-report.md` and `research-landscape.md`.

## Project Directory

Read `pipeline-state.json` → `project_dir`.

**Required inputs:**
- `$PROJECT_DIR/research-landscape.md` (Tier 1 papers = seed candidates)
- `$PROJECT_DIR/claim-overlap-report.md` (if Pass 2 complete) or `hypotheses.md`
- `$PROJECT_DIR/.epistemic/citation_ledger.json`

**Outputs:**
- Appended findings in `$PROJECT_DIR/claim-overlap-report.md`
- Updated `$PROJECT_DIR/research-landscape.md`
- Updated `$PROJECT_DIR/.epistemic/citation_ledger.json`
- `$PROJECT_DIR/citation-traversal-report.md`

---

## Execution

### Step 1: Select Seed Papers

From `research-landscape.md` Tier 1 papers and any HIGH/MEDIUM threat papers from `claim-overlap-report.md` (if available), select up to `$seed_count` seeds. Prioritization:

1. HIGH/MEDIUM overlap papers from Pass 2 (highest priority — their citation neighborhood is most dangerous)
2. Foundational papers in the field (most cited Tier 1 papers)
3. Most recent highly-cited papers (likely cite the state of the art)
4. Papers from the most relevant cluster in the landscape map

Record the seed list in the report.

### Step 2: Retrieve Citation Graphs

For each seed paper, retrieve:

**Forward citations** (papers that cite the seed):
- Preferred: `semantic-scholar` MCP (`paper_citations` / equivalent tool)
- Fallback: WebSearch `"[exact title]" site:semanticscholar.org` → click through to see citing papers
- Fallback: Google Scholar "Cited by N" link → scrape first 2 pages

**Backward references** (papers cited by the seed):
- Preferred: `semantic-scholar` MCP (`paper_references` / equivalent tool)
- Fallback: read the paper's reference list from the PDF (use `arxiv-mcp-server` read tool if possible) or arXiv page

**Rate limiting:** If using Semantic Scholar API, respect the 100 requests/5 min rate limit. Batch requests where possible. Log any rate limit errors and retry after 60 seconds (max 3 retries per paper).

**Cache results:** Store raw citation graph data in `$PROJECT_DIR/.cache/citation_graphs/{cite_key}.json` to avoid redundant API calls if the step is re-run.

### Step 3: Rank Second-Order Papers

For each second-order paper (forward or backward from seed papers), score it:

**Citation overlap score:** Count how many seed papers this paper has a citation relationship with.
- 3+ seed connections → Score HIGH (likely very relevant)
- 2 seed connections → Score MEDIUM
- 1 seed connection → Score LOW

**Recency bonus:** Papers from 2023–2025 get +1 to their priority tier.

Select papers to scan in detail:
- All HIGH scored papers: scan abstract + conclusions
- Top 50% of MEDIUM scored papers: scan abstract
- LOW scored papers: title only unless the title is clearly relevant

### Step 4: Screen for Relevance

For each paper selected for scanning:

1. Read abstract and conclusions.
2. Does it overlap with any decomposition component from Pass 2?
3. Does it represent a research approach or finding not covered by the existing landscape map?

Categorize:
- **Relevant + novel find:** A paper not in Pass 1 or 2 that has meaningful relevance → add to citation ledger, assign tier, assess overlap
- **Relevant + duplicate:** Already in citation ledger → update with `found_via: citation_traversal`
- **Not relevant:** Log as scanned, no action

For relevant + novel finds that are HIGH/MEDIUM overlap: read in full (WebFetch) and write a differential statement.

### Step 5: Landscape Update

If this pass found papers representing a research thread not in the existing cluster map, add a new cluster to `research-landscape.md` or update an existing cluster.

### Step 6: De-duplication

```bash
python scripts/dedup_papers.py \
  --new-results citation_traversal_raw.json \
  --existing $PROJECT_DIR/.epistemic/citation_ledger.json \
  --output citation_traversal_deduped.json
```

---

## Output: `citation-traversal-report.md`

```markdown
# Citation Traversal Report (Pass 3)

**Date:** YYYY-MM-DD
**Seed papers:** N (listed below)
**Second-order papers examined:** N
**New papers found:** N

## Seed Papers

| # | Cite Key | Title | Selection Reason |
|---|----------|-------|-----------------|
| 1 | ... | ... | HIGH overlap / foundational / recent |
[...]

## Citation Graph Statistics

| Seed Paper | Forward Citations Retrieved | Backward References Retrieved | High-Score 2nd-Order |
|-----------|---------------------------|------------------------------|---------------------|
[...]

## New Relevant Papers Found

For each new paper with meaningful relevance:

### [Author et al., YYYY] — [Title]
- **Found via:** forward citation of [seed] / backward reference of [seed]
- **Citation overlap score:** N seed connections
- **Overlap with proposed contribution:** [description]
- **Overlap level:** HIGH / MEDIUM / LOW
- **Added to:** citation_ledger.json

## Missed Threads

[List any research clusters or intellectual threads suggested by the citation graph that were not captured in Pass 1 or 2]

## Coverage Assessment

**Papers scanned at abstract level:** N
**Papers read in full:** N
**New HIGH/MEDIUM overlap papers:** N

Pass 3 complete. Findings appended to claim-overlap-report.md.
```

---

## Gate Criteria

Before marking complete:

- [ ] ≥ 10 seed papers used
- [ ] Forward citations AND backward references retrieved for each seed
- [ ] All HIGH-score second-order papers scanned at minimum
- [ ] All new HIGH/MEDIUM overlap papers read in full with differential statements
- [ ] Citation ledger updated with new papers and `found_via: citation_traversal` field
- [ ] `citation-traversal-report.md` written

---

## Integration

- **Runs in parallel with:** `/claim-search` (Pass 2)
- **Follows:** `/research-landscape` (needs Tier 1 seeds)
- **Feeds into:** `/adversarial-search` (Pass 6), `/novelty-gate` (Gate N1)
- **Appends to:** `claim-overlap-report.md`, `research-landscape.md`
- **Caches to:** `$PROJECT_DIR/.cache/citation_graphs/`
- **Agent:** `literature-reviewer` (opus)
