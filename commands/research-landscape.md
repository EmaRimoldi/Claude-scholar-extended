---
name: research-landscape
description: Pass 1 of the multi-pass research system. Broad territory mapping — scan 50–100 papers, identify major research threads, active groups, standard benchmarks, and open problems. Seeds the Citation Provenance Ledger and Evidence Registry.
args:
  - name: topic
    description: Research topic or problem statement
    required: true
  - name: venue
    description: Target venue (NeurIPS/ICML/ICLR/ACL/KDD/etc.)
    required: false
    default: ""
tags: [Research, Literature, Pipeline, Phase1]
---

# /research-landscape — Broad Territory Mapping (Pass 1)

## Purpose

This is the **first pass** of the multi-pass research system. Its job is territorial: map the entire research space at sufficient depth to know where the edges are. It does not deeply analyze any single paper — it achieves coverage.

This step initializes the **Citation Provenance Ledger** and seeds the **Evidence Registry** with literature findings.

## Project Directory

Read `pipeline-state.json` to resolve `$PROJECT_DIR`. All output files MUST be written inside `$PROJECT_DIR`. Never write to the repository root.

- `$PROJECT_DIR/research-landscape.md`
- `$PROJECT_DIR/.epistemic/citation_ledger.json` (initialize)
- `$PROJECT_DIR/.epistemic/evidence_registry.json` (seed)

## MCP-first search policy (mandatory)

If MCP servers are configured, you MUST use them as the **primary** retrieval layer:
- `semantic-scholar` for search + citations/references expansion
- `arxiv-mcp-server` for arXiv search + PDF download + reading
- `crossref` for DOI/metadata resolution when needed
- `zotero` to import/organize the final reading set and (when possible) attach PDFs

**Fallback is allowed and expected**: if MCP is unavailable, rate-limited, or missing a paper, use WebSearch/WebFetch and log the fallback.

**Minimum required (combined MCP + web):**
- 8+ distinct search queries (via MCP tools and/or WebSearch)
- 3+ full papers read (via `arxiv-mcp-server` read tool, Zotero fulltext, or WebFetch)
- 50+ papers scanned at abstract level
- 15–25 papers read in detail

---

## Execution

### Step 1: Query Expansion

Expand `$topic` into a query matrix covering:

1. **Topic variants**: restate the problem at different levels of abstraction
   - Most specific: exact method/task pair
   - Mid-level: the problem class
   - Abstract: the underlying computational challenge

2. **Temporal sweep**: include `2022`, `2023`, `2024`, `2025` in separate queries to catch recent work

3. **Venue-specific**: if `$venue` is set, search the venue's accepted papers directly
   - ACL Anthology for NLP venues
   - OpenReview for ICLR/NeurIPS/ICML
   - DBLP for CS venues

**Minimum queries to run:**
```
[topic exact phrase] site:arxiv.org
[topic] survey OR review 2023 2024 2025
[problem class] benchmark evaluation
[method type] [task domain] state of the art
[topic] workshop [venue year]
[topic] limitations open problems
```

### Step 1b: Recency-Boosted Core Topic Search

**Run immediately after Step 1, before triage.** After generating the initial query matrix, run a second set of date-filtered queries targeting the last 6 months to catch very recent concurrent work that may not yet have high citation counts but is directly relevant.

For each major cluster identified in Step 1 (especially HIGH-relevance clusters), generate 1–2 queries restricted to recent papers:

```
[cluster key terms] 2025 2026 site:arxiv.org
[exact topic phrase] arXiv 2025
[method] [task] 2026 NeurIPS ICML ICLR ACL
```

**Sources:** arXiv (date-filtered search or `arxiv.org/search/?searchtype=all&query=...&start=0&order=-announced_date_first`), Semantic Scholar (year filter: 2025, 2026)

**Triage rule:** Any paper published in the last 6 months in a HIGH-relevance cluster is automatically Tier 1 — read in full. Do NOT defer these to later passes. Concurrent work threats from the last 6 months missed at Pass 1 are not recoverable until Pass 5 (recency sweep), which is after hypothesis formulation and experiment design.

**Minimum:** 4 date-filtered queries (1 per HIGH-relevance cluster).

---

### Step 2: Multi-Source Search

Search the following sources in order. Do not skip a source unless it fails with an error.

| Source | Access Method | Priority |
|--------|--------------|---------|
| arXiv | WebSearch + WebFetch abstract page | High |
| Semantic Scholar | WebSearch `site:semanticscholar.org` + API if available | High |
| ACL Anthology | WebSearch `site:aclanthology.org` | High (NLP) |
| OpenReview | WebSearch `site:openreview.net` | High (ML venues) |
| DBLP | WebSearch `site:dblp.org` | Medium |
| Google Scholar | WebSearch | Medium |

For each source: collect paper titles, authors, year, venue, abstract. Record the source that found each paper.

### Step 3: Paper Triage

For each paper found, assign a relevance tier:

- **Tier 1 (read in full):** Papers that appear central to the topic — foundational methods, recent SOTA, closest prior work candidates. Target: 15–25 papers.
- **Tier 2 (abstract only):** Papers in adjacent areas, older baselines, survey papers. Scan abstract and conclusions. Target: 30–75 papers.
- **Tier 3 (title only):** Papers that appeared in search results but are clearly tangential. Log for completeness.

Read all Tier 1 papers using (in order): `arxiv-mcp-server` (download/read) → Zotero fulltext (if imported) → WebFetch (fallback).

### Step 4: Cluster Analysis

After collecting papers, organize them into thematic clusters:

For each cluster, document:
- **Cluster name** (1–3 words)
- **Key papers** (3–5 representative papers with citation keys)
- **Core methodology** (what approach does this cluster use?)
- **Standard benchmarks** (what does this cluster evaluate on?)
- **Active research groups** (which labs / authors are prolific here?)
- **Open problems** (what does this cluster acknowledge it has not solved?)
- **Relevance to our topic** (HIGH / MEDIUM / LOW)

Target: 4–8 clusters covering the research space.

### Step 5: Gap Identification

Based on the cluster map, identify concrete research gaps:
- Problems that are widely acknowledged but unsolved
- Evaluations that no cluster has attempted
- Combinations of approaches from different clusters that have not been tried
- Negative results that suggest an opportunity

Minimum: 3 distinct, actionable research gaps.

### Step 6: Initialize Epistemic Infrastructure

Create or update the following files:

**`.epistemic/citation_ledger.json`**: For each paper reviewed in Tier 1 or 2:
```json
{
  "cite_key": "authorYEARkeyword",
  "title": "...",
  "authors": ["..."],
  "year": YYYY,
  "venue": "...",
  "source_url": "...",
  "claims_supported": [],
  "claims_supported_text": [],
  "first_introduced": "step_research-landscape",
  "used_in_manuscript": false,
  "audit_status": "unchecked",
  "relevance_tier": 1
}
```

**`.epistemic/evidence_registry.json`**: Seed with literature findings:
```json
{
  "id": "EV-LIT-001",
  "type": "literature_finding",
  "source": "research-landscape + [cite_key]",
  "description": "...",
  "strength": "strong | moderate | weak",
  "claims_dependent": [],
  "last_updated": "step_research-landscape",
  "notes": ""
}
```

---

## Output: `research-landscape.md`

```markdown
# Research Landscape: [Topic]

**Date:** YYYY-MM-DD
**Pass:** 1 (Broad Territory Mapping)
**Papers scanned:** N (Tier 1: X, Tier 2: Y, Tier 3: Z)

## Research Clusters

### Cluster 1: [Name]
**Core approach:** ...
**Key papers:** [Author et al. YYYY], ...
**Standard benchmarks:** ...
**Active groups:** ...
**Open problems:** ...
**Relevance:** HIGH / MEDIUM / LOW

[...repeat for each cluster...]

## Research Gaps

1. **[Gap name]**: [Description]. Supported by: [papers that acknowledge this gap].
2. ...

## Key Papers (Tier 1 — read in full)

For each paper:
- **[Author et al., YYYY]** — "[Title]" — [Venue]
  - *Contribution:* [1 sentence]
  - *Relevance:* [2 sentences — why this matters for our topic]
  - *Limitations:* [what this paper doesn't address]
  - *Cite key:* `authorYEARkeyword`

## Search Coverage

| Source | Papers Found | Queries Run |
|--------|-------------|-------------|
| arXiv | N | N |
| Semantic Scholar | N | N |
| OpenReview | N | N |
[...]

**Total queries:** N (minimum required: 8) ✓/✗
**Total papers found:** N (minimum required: 50) ✓/✗
**Tier 1 papers read in full:** N (minimum required: 15) ✓/✗

## Pass 1 Complete

Ready for Pass 2 (claim-level search) after hypothesis formulation at `/formulate-hypotheses`.
```

---

---

## Batched Processing Protocol (Context Management)

When processing ≥20 papers, use batched processing to prevent accumulating full paper
texts in active context. This is the **preferred mode for all runs**.

### Batch execution pattern

Process papers in groups of 10 (combining Tier 1 and Tier 2 from each search round):

1. Process 10 papers (search, read abstracts, read full text for Tier 1).
2. Write a partial batch handoff immediately:

```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-handoff \
  research-landscape-batch-N \
  '{"key_outputs": {
      "papers_processed": "Papers 1-10: [comma-separated titles or cite keys]",
      "clusters_emerging": "Clusters seen so far: [names and 1-line descriptions]",
      "tier1_findings": "Key findings from Tier 1 papers in this batch"
    },
    "summary": "Batch N: processed N papers. Emerging themes: ...",
    "critical_context": [
      "[Author YYYY]: [key finding most relevant to hypothesis]",
      "Cluster [name]: [methodology and relevance note]"
    ],
    "token_estimate": <estimated tokens for these 10 papers>}'
```

3. After writing the batch handoff, **discard the full paper text** from active context.
   Retain only the batch handoff summary and the running cluster map.
4. Repeat for the next batch.

### Consolidation handoff (write after ALL batches complete)

After all papers are processed and `research-landscape.md` is written:

```bash
python scripts/pipeline_state.py --dir $PROJECT_DIR write-handoff \
  research-landscape \
  '{"key_outputs": {
      "total_papers": "N papers scanned (Tier 1: X, Tier 2: Y, Tier 3: Z)",
      "clusters": "4-8 cluster names with 1-sentence descriptions",
      "top_gaps": "Top 3 actionable gaps with supporting cite keys",
      "tier1_papers": "Cite keys of all Tier 1 papers",
      "key_benchmarks": "Standard benchmarks found across clusters"
    },
    "summary": "...",
    "critical_context": ["...", "..."],
    "token_estimate": <int>}'
```

This consolidation handoff is what `cross-field-search` and `formulate-hypotheses` will
load when the context budget is HIGH.

Batch handoffs → `state/handoffs/research-landscape-batch-N.json`  
Consolidation handoff → `state/handoffs/research-landscape.json`  
Full output document → `$PROJECT_DIR/docs/research-landscape.md` (unchanged)

---

## Gate Criteria

Before marking this step complete, verify:

- [ ] ≥ 8 WebSearch queries executed
- [ ] ≥ 50 papers found and catalogued (at any tier)
- [ ] ≥ 15 papers read in full (Tier 1)
- [ ] ≥ 4 research clusters identified
- [ ] ≥ 3 research gaps identified
- [ ] `citation_ledger.json` initialized with all Tier 1 and 2 papers
- [ ] `evidence_registry.json` seeded with literature findings
- [ ] `research-landscape.md` written to `$PROJECT_DIR/`

If any criterion fails, continue searching before marking complete.

---

## Integration

- **Follows:** Project initialization
- **Feeds into:** `/check-competition` (Pass 4 cross-field), `/formulate-hypotheses`, then `/claim-search` (Pass 2)
- **Epistemic updates:** Citation Provenance Ledger initialized; Evidence Registry seeded
- **Skill:** `research-ideation`
- **Agent:** `literature-reviewer` (opus)
