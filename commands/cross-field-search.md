---
name: cross-field-search
description: Pass 4 of the multi-pass research system. Abstracts the hypothesis to domain-agnostic terms, identifies 3–5 adjacent fields, and searches each using field-specific terminology to find prior art that keyword search in the source field would miss. Produces cross-field-report.md required for Gate N1.
args:
  - name: project_dir
    description: Project directory path (reads from pipeline-state.json if not set)
    required: false
    default: ""
tags: [Research, Novelty, Pass4, Cross-Field, Gate, Pipeline]
---

# /cross-field-search — Cross-Field Prior Art Search (Pass 4)

## Purpose

Search for the *problem* (not the method) in adjacent research fields. The most common novelty blind spot in automated research is that an idea is "novel" within the source field but is standard practice in another community under different terminology. This command finds that prior art before Gate N1.

**Critical rule:** Never search adjacent fields using your source field's keywords. The whole point is to translate the problem into each target field's own vocabulary and search with *those* terms. A search for "efficient attention" in a signal processing corpus finds nothing useful; a search for "sparse structured linear operator approximation" finds the relevant work.

## Project Directory

Read `pipeline-state.json` → `project_dir`. All outputs written to `$PROJECT_DIR/docs/`.

---

## Required Inputs

- `$PROJECT_DIR/docs/hypotheses.md` — the hypothesis to abstract
- `$PROJECT_DIR/docs/research-landscape.md` — existing field map (to avoid duplicating papers already found in Pass 1)
- `$PROJECT_DIR/.epistemic/citation_ledger.json` — updated with all papers found here

---

## Execution

### Step 1: Abstract the Problem

Read `hypotheses.md`. Extract the core contribution statement in the form:

> "We show that [method] achieves [result] on [task/domain] by [mechanism]."

Then restate it in **domain-agnostic terms**, stripping all field-specific vocabulary:

- Replace [method] with its abstract mathematical or computational description
- Replace [task/domain] with the abstract problem class
- Replace [mechanism] with the abstract structural principle

**Example transformations:**

| Source description | Domain-agnostic restatement |
|-------------------|-----------------------------|
| "efficient attention for long sequences in NLP" | "sparse structured approximation of quadratic pairwise interaction operators" |
| "few-shot generalization in image classifiers" | "rapid hypothesis formation from limited samples in high-dimensional spaces" |
| "GNN scalability on large graphs" | "scalable local message aggregation in irregular graph-structured data" |
| "protein structure prediction via co-evolutionary signals" | "inverse problem reconstruction from correlated residual patterns in discrete sequences" |
| "continual learning without catastrophic forgetting" | "sequential parameter update under non-stationary distributions with interference constraints" |

Write the domain-agnostic problem statement as a dedicated section in the output before proceeding. This statement drives all downstream field identification. If you cannot write a clean domain-agnostic restatement, the hypothesis is likely too narrow or too dependent on source-field framing — flag this.

---

### Step 2: Identify Adjacent Fields

Based on the domain-agnostic problem statement, identify **3–5 fields** where researchers work on structurally similar problems under different terminology.

**Reasoning template:**
- "The core challenge is [abstract problem]. Which research communities independently study [abstract problem]?"

**Candidate field list to consider** (not exhaustive):
- Computer vision / image processing
- Signal processing / compressed sensing
- Computational biology / bioinformatics
- Physics-based simulation / computational physics
- Control theory / reinforcement learning
- Quantum computing / quantum information
- Finance / econometrics / time series analysis
- Operations research / combinatorial optimization
- Neuroscience / computational neuroscience
- Statistics / probabilistic inference
- Database systems / information retrieval
- Robotics / planning under uncertainty

For each candidate field, evaluate:
1. Do researchers in this field face the same abstract problem?
2. Is there a substantial literature on it in this field?
3. Could they have solved it in a way that constitutes prior art for the proposed contribution?

Select the **3–5 most structurally similar** fields, prioritizing those where the abstract problem is actively studied — not just topically adjacent fields.

---

### Step 3: Translate and Search Each Field

For each identified adjacent field, perform three substeps:

**3a. Vocabulary translation**

Identify the dominant vocabulary this field uses for the abstract problem. Use WebSearch to find 1–2 key survey papers or landmark papers in this field that anchor the terminology:

```
WebSearch: "[field name] [abstract problem keyword] survey review"
WebSearch: "[field name] [abstract problem keyword] seminal work"
```

Read the abstract and introduction of any found surveys. Extract the key terms this field uses.

**3b. Targeted search**

Construct 3–5 queries using *this field's vocabulary*, not your source field's:

```
WebSearch: "[field-specific term 1] [field-specific term 2]"
WebSearch: "[field-specific term 1] [field-specific term 3] 2022 2023 2024 2025"
WebSearch: "[field-specific term] [field venue] best paper"
WebSearch: "[field-specific term] tutorial introduction"
```

Sources to search per field:
- arXiv with field-specific category (cs.CV, stat.ML, q-bio.QM, eess.SP, etc.)
- Google Scholar for field-specific journals
- Field-specific top venues (IEEE Signal Processing, Bioinformatics, Nature Methods, SIAM journals, etc.)

**3c. Relevance evaluation**

For each paper found, answer:
1. Does it solve the same abstract problem?
2. Does it use a technique structurally equivalent to the proposed method?
3. If translated into source-field vocabulary, would it read as the same contribution?

Classify the prior art threat for each paper:
- **HIGH:** A researcher familiar with both fields would say "they already did this." The method is the same; only the terminology differs.
- **MEDIUM:** Substantial structural overlap. A diligent reviewer would likely cite this work and ask for explicit differentiation.
- **LOW:** Related problem but meaningfully different approach or scope.
- **NONE:** Adjacent field was searched but no relevant work found, or found work is clearly distinct.

**Scan at minimum 5–10 papers per field at the abstract level. Read the methods section in detail for any paper with threat level MEDIUM or higher.**

---

### Step 4: Write Differential Statements for MEDIUM and HIGH Threats

For every paper with threat level HIGH or MEDIUM, write an explicit differential statement:

> "[Paper] solves [abstract problem formulation] in [Field] using [their approach]. Our proposed work addresses [our abstract problem] in [Source Field] using [our approach]. The specific technical difference is [Z]. This is not a transfer of their work because [concrete reason — scope, constraints, inputs, outputs, or mathematical structure differ in X way]."

**If this statement cannot be written clearly and honestly, upgrade the threat to HIGH and flag it.** The inability to articulate a clean differential is itself a novelty signal — it means the contribution may be a field transfer rather than a novel contribution.

---

### Step 5: Update Citation Provenance Ledger

For **all papers found** during the search (not just threats), add entries to `$PROJECT_DIR/.epistemic/citation_ledger.json`.

Read the existing file first. Do not overwrite entries that already exist from earlier search passes. Add only new entries.

New entry format:
```json
{
  "cite_key": "<firstauthor><year><keyword>",
  "title": "Full paper title",
  "year": YYYY,
  "venue": "Venue or journal name",
  "source_field": "The adjacent field in which this paper was found",
  "claims_supported": [],
  "claims_supported_text": [],
  "first_introduced": "cross-field-search",
  "used_in_manuscript": false,
  "audit_status": "unchecked",
  "relevance": "HIGH|MEDIUM|LOW",
  "prior_art_threat": "HIGH|MEDIUM|LOW|NONE",
  "found_via": "cross-field-search",
  "cross_field_note": "Why this field was searched and how this paper relates to the abstract problem"
}
```

---

### Step 6: Update Research Landscape

If adjacent field search reveals new research clusters not represented in `research-landscape.md`, append a section:

```markdown
## Adjacent Field Findings (from Pass 4)

### [Field Name]
- **Abstract problem overlap:** [description]
- **Key papers found:** [list]
- **Novelty implication:** [how this affects the source-field contribution]
```

Only append — do not overwrite or restructure the existing landscape document.

---

## Output Files

### `$PROJECT_DIR/docs/cross-field-report.md`

Write this file with the exact structure below. Downstream commands (`/novelty-gate`, `/adversarial-search`) parse specific sections by heading.

```markdown
# Cross-Field Search Report

**Date:** YYYY-MM-DD
**Hypothesis summary:** [one-line from hypotheses.md]
**Passes run:** Pass 4 (Cross-Field)

## Abstract Problem Statement

[Domain-agnostic restatement, 2–4 sentences. This is what was used to identify adjacent fields.]

## Adjacent Fields Searched

### [Field 1 Name]

**Why searched:** [Connection to abstract problem — 1–2 sentences]

**Vocabulary used:** [Key terms from this field]

**Queries executed:**
- `[query 1]`
- `[query 2]`
- `[query 3]`

**Sources searched:** arXiv ([category]), Google Scholar, [field venue]

**Papers scanned:** N total, M relevant

**Key findings:**

| Paper | Year | Venue | Relation to proposed contribution | Threat level |
|-------|------|-------|----------------------------------|--------------|
| [Author et al.] | YYYY | [venue] | [1–2 sentence description] | HIGH/MEDIUM/LOW/NONE |

**Prior art threat level for this field:** NONE / LOW / MEDIUM / HIGH

**Differential statements (for MEDIUM/HIGH threats):**

> [Author et al. YYYY]: [Write differential statement following the template from Step 4. If none needed, omit this subsection.]

---

[Repeat ### section for each adjacent field searched]

## Overall Cross-Field Assessment

| Field | Papers scanned | Relevant | Highest threat paper | Threat level |
|-------|---------------|---------|---------------------|--------------|
| [Field 1] | N | M | [paper] | NONE/LOW/MEDIUM/HIGH |
| [Field 2] | N | M | [paper] | NONE/LOW/MEDIUM/HIGH |

**Fields with prior art concerns:** [list or "None"]

**Highest overall threat:** [paper + field + reason, or "None identified across all fields searched"]

**Recommendation:**
- `no_impact` — No cross-field prior art found. Proceed to hypothesis formulation.
- `cite_and_differentiate` — Related work found; must be cited and explicitly differentiated in the related work section of the manuscript.
- `reposition_needed` — Prior art in adjacent field substantively overlaps; novelty claim needs repositioning to acknowledge field transfer.
- `blocks_novelty_claim` — Prior art in adjacent field constitutes full prior art for the proposed contribution. Gate N1 will likely fail on Application novelty dimension.

## Gate N1 Input Summary

This section is read directly by `/novelty-gate gate=N1`:

**Application novelty status:** [CLEAR / PARTIAL / NO — based on cross-field findings]
**Cross-field threats to cite:** [bulleted list of papers, or "None"]
**Cross-field kill signals:** [Yes/No. If Yes: paper, field, and reason]
**Differential statements written for all HIGH/MEDIUM threats:** [Yes/No]
```

---

## Gate Criteria

Before marking complete:

- [ ] Domain-agnostic problem statement written and clearly separated from source-field vocabulary
- [ ] 3–5 adjacent fields identified with explicit reasoning connecting each to the abstract problem
- [ ] Each field searched with field-specific terminology (verified: source-field keywords NOT used as primary queries)
- [ ] 5+ papers evaluated per field at abstract level
- [ ] All MEDIUM/HIGH threat papers read in detail (methods section)
- [ ] Differential statements written for all MEDIUM/HIGH threat papers
- [ ] Citation ledger updated with all papers found (not just threats)
- [ ] Research landscape updated with any new clusters
- [ ] `cross-field-report.md` written to `$PROJECT_DIR/docs/`
- [ ] Overall recommendation set to one of: `no_impact`, `cite_and_differentiate`, `reposition_needed`, `blocks_novelty_claim`
- [ ] If `blocks_novelty_claim`: flag immediately — do not wait for Gate N1

---

## Integration

- **Runs at Step 2** in the pipeline, after `/research-landscape` (Step 1) and before `/formulate-hypotheses` (Step 3)
- **Prerequisite for Gate N1:** `/novelty-gate gate=N1` requires `cross-field-report.md`. Gate N1 will fail its prerequisite check if this file is absent.
- **Seeds adversarial search:** `/adversarial-search` (Step 6) uses `cross-field-report.md` HIGH/MEDIUM threat papers as the starting point for its "Cross-Field Anticipation" attack type.
- **Feeds Application novelty dimension:** The Gate N1 per-dimension assessment for Application novelty reads directly from the "Gate N1 Input Summary" section.
- **Agent:** `cross-field-search` skill (opus, extended thinking — field translation requires deep reasoning to avoid superficial matches)
- **Online required:** Yes — uses WebSearch for each adjacent field. Cannot be run with `--skip-online`.
