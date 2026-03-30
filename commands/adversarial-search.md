---
name: adversarial-search
description: Pass 6 of the multi-pass research system. Actively attempts to destroy the project's novelty claim. Formulates the strongest possible argument that this work is not novel, then searches for evidence to support that argument. Output is the adversarial-novelty-report.md used by Gate N1 and the Paper Quality Verifier.
args:
  - name: mode
    description: "Search mode: 'full' (all attacks) or 'targeted' (rerun on specific claim after results). Default: full"
    required: false
    default: full
tags: [Research, Novelty, Adversarial, Pipeline, Phase1]
---

# /adversarial-search — Adversarial Novelty Attack (Pass 6)

## Purpose

This is the **stress test pass**. Its goal is not to find related work — it is to **find the single most damaging paper that could sink this project**. Every other pass looks for relevant work. This pass looks for *devastating* work.

The adversarial search simulates what a hostile Reviewer 2 would do: search for the most damaging prior work, reframe the contribution as incremental, and find the paper that makes the reviewers say "this has been done."

If this pass cannot find a devastating counter-paper, that is strong evidence the contribution is genuinely novel.

## Project Directory

Read `pipeline-state.json` → `project_dir`.

**Required inputs:**
- `$PROJECT_DIR/hypotheses.md`
- `$PROJECT_DIR/claim-overlap-report.md` (Pass 2 output)
- `$PROJECT_DIR/research-landscape.md`
- `$PROJECT_DIR/docs/cross-field-report.md` (Pass 4 output — used to seed Step 6)

**Outputs:**
- `$PROJECT_DIR/adversarial-novelty-report.md`
- Updated `$PROJECT_DIR/.epistemic/citation_ledger.json`

---

## Execution

### Step 1: Generic Restating

Take the proposed contribution and restate it in the most **generic, uncharitable** terms possible. The goal is to strip away all the specific framing that makes the contribution sound novel.

**Examples of generic restating:**
- "We propose a novel attention mechanism for long documents" → "We apply a known efficiency technique to a known task"
- "We show that pretraining on domain-specific data improves performance" → "We fine-tune a pretrained model on domain data and get improvement"
- "We present a theoretical analysis of gradient descent convergence" → "We analyze a known algorithm"

Write 3–5 generic restatements. These become the adversarial search queries.

### Step 2: The Survey Attack

Surveys and tutorials are the most dangerous papers — if the proposed contribution fits neatly into an existing taxonomy as an incremental variant, the work is not novel.

Search for:
```
[topic] survey
[topic] review
[topic] tutorial
[problem class] survey 2022 2023 2024 2025
"overview of [method type]"
```

For any survey found: read the taxonomy section. Does the proposed contribution fit neatly as a variant of an existing category? If yes, flag this explicitly.

### Step 3: The "Already Done" Attack

Search for the generic restatements from Step 1:
```
[generic restatement 1] site:arxiv.org
[generic restatement 2] YYYY YYYY+1
[method type] [task] already
[method name] [task name] previous work
```

Also search in the most likely blind spot: a highly-cited paper from 3–5 years ago that a subfield would consider "well-known" but that keyword search might miss because it's pre-hype.

### Step 4: The Closest-Prior-Work Attack

Identify the **single closest prior paper** — the paper most likely to be cited by a reviewer as "this has been done." Criteria:
- Same method type on same task domain
- OR same result type achieved by a different method
- OR same mechanism exploited in an adjacent paper

For this paper:
1. Read it in full (WebFetch)
2. Write an explicit technical comparison:
   - What they do that we also do
   - What they do that we don't do
   - What we do that they don't do
   - Whether what we do that they don't constitutes a meaningful advance

If the "what we do that they don't" section is short, vague, or amounts to minor variations, **this is a kill signal**.

### Step 5: The Incremental-Variation Attack

Search for:
```
[method] [task] variant
[method] [task] extension
[method] improved
"similar to [method]"
ablation [method type]
```

This targets papers that are technically different from the proposed contribution but produce the same result via a different route. If the same result can be achieved by trivially varying a prior method, the contribution is incremental.

### Step 6: The Cross-Field Anticipation Attack

**First, read `cross-field-report.md`** (produced by `/cross-field-search`, Step 2). The cross-field search has already identified adjacent fields and found relevant papers. Do not duplicate that work.

From `cross-field-report.md`:
1. Read the "Gate N1 Input Summary" section for cross-field kill signals.
2. For every paper with `prior_art_threat: HIGH` or `prior_art_threat: MEDIUM`, attack the contribution using that paper as ammunition — construct the adversarial argument "this work is just [adjacent-field paper] repackaged in [source field] vocabulary."
3. If `cross-field-report.md` recommendation is `blocks_novelty_claim` or `reposition_needed`, this attack is already pre-loaded — use the exact paper and field as the attack vector.

If `cross-field-report.md` shows `no_impact` or `cite_and_differentiate` for all fields, then construct a fresh cross-field attack:
1. Abstract the proposed contribution to its mathematical or computational core.
2. Select 1–2 additional adjacent fields NOT already covered in `cross-field-report.md`.
3. Search each field with field-specific terminology.

Example: "We propose sparse attention for long sequences" → abstract to "sparse approximation of quadratic kernel" → search in: kernel methods literature, randomized algorithms, signal processing.

If an adjacent field has a cleaner or stronger solution to the same underlying problem, **flag as novelty threat**.

### Step 7: Adversarial Rebuttal

For the single most dangerous paper found (or the single most dangerous conceptual attack, if no devastating paper was found):

Write the adversarial argument:
> "This work is not novel because [strongest attack]."

Then write the rebuttal:
> "This attack fails because [response]. Specifically, [technical differentiation]."

If the rebuttal is:
- **Strong** (clear technical differentiation, different outcomes, different mechanisms): NOVELTY HOLDS
- **Weak** (minor differences, "we do it better," incremental variants): NOVELTY AT RISK — flag for Gate N1
- **Unable to be written**: KILL SIGNAL

---

## Kill Signal Logic

A kill signal is issued if ANY of the following are true:
- A paper is found that proposes the same method, applies it to the same problem, and reports comparable results (full anticipation)
- The generic restatement search finds papers that cover 3+ decomposition components
- A survey taxonomy already contains the proposed contribution as a named variant
- The adversarial rebuttal cannot be written clearly

Kill signals are logged in `adversarial-novelty-report.md` with full justification. The novelty gate (Gate N1) makes the final KILL decision — this pass is the evidence source.

---

## Output: `adversarial-novelty-report.md`

```markdown
# Adversarial Novelty Report (Pass 6)

**Date:** YYYY-MM-DD
**Mode:** full / targeted
**Attacks executed:** N

## Proposed Contribution

[Canonical form: method → result → task → mechanism]

## Generic Restatements (Adversarial Queries)

1. [most generic restatement]
2. ...

## Attack Results

### Survey Attack
**Surveys found:** N
**Taxonomy threat:** [Does the contribution fit as a named variant in any existing survey?]
**Verdict:** NO THREAT / PARTIAL THREAT / KILL SIGNAL

### "Already Done" Attack
**Papers found matching generic restatements:** N
**Most concerning:** [title, authors, year] — overlap: [description]
**Verdict:** NO THREAT / PARTIAL THREAT / KILL SIGNAL

### Closest Prior Work Attack

**Identified closest prior paper:** [Author et al., YYYY] — [Title]
**What they do that we also do:**
- ...

**What they do that we don't:**
- ...

**What we do that they don't:**
- ...

**Is "what we do that they don't" a meaningful advance?** YES / NO / MARGINAL
**Verdict:** NO THREAT / PARTIAL THREAT / KILL SIGNAL

### Incremental Variation Attack
**Verdict:** NO THREAT / PARTIAL THREAT / KILL SIGNAL

### Cross-Field Anticipation Attack
**Fields searched:** [list]
**Most concerning finding:** ...
**Verdict:** NO THREAT / PARTIAL THREAT / KILL SIGNAL

---

## Adversarial Case (Strongest Attack Against This Project)

**Adversarial argument:**
> [The strongest possible argument that this work is not novel]

**Rebuttal:**
> [The technical differentiation that defeats this argument]

**Rebuttal strength:** STRONG / WEAK / UNABLE TO WRITE

---

## Kill Signal Summary

**Kill signals triggered:** N
[If N > 0: list each with description and source]

---

## Verdict for Gate N1

**Novelty status:** CLEAR / PARTIAL / INSUFFICIENT
**Recommendation:** PROCEED / REPOSITION / PIVOT / KILL
**Confidence:** HIGH / MEDIUM / LOW
**Evidence:** [list of passes contributing to this verdict]
```

---

## Gate Criteria

Before marking complete:

- [ ] All 5 attack types executed
- [ ] Closest prior work identified and read in full
- [ ] Adversarial argument + rebuttal written
- [ ] Kill signal assessment completed
- [ ] `adversarial-novelty-report.md` written with structured verdict

---

## Integration

- **Follows:** `/claim-search` (Pass 2) and `/citation-traversal` (Pass 3) — needs their outputs
- **Feeds into:** `/novelty-gate` (Gate N1), Paper Quality Verifier (Dimension 1, criterion N3)
- **Re-invoked at:** Gate N3 (post-results, with `mode: targeted` targeting the actual contribution)
- **Agent:** `skeptic-agent` (opus) + `novelty-assessment` skill
