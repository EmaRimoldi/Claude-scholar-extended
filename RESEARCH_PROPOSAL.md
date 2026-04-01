---
schema_version: 1

# Required (this is what Step 1 consumes)
project_slug: your-paper-slug
research_topic: "Write your research question here (1–3 sentences). Be concrete: method, metric, benchmark, constraints."

# Optional (leave out anything you don't care about)
display_title: "Your Paper Title (optional)"
domain_hints:
  - optional keyword
  - optional adjacent field
target_venue: neurips
skip_online: false
seeds_per_condition: 5
gpus_per_job: 1
---

# Research proposal (start here) ✨🧪

If you only do one thing before running the pipeline, do this:

1. Edit the frontmatter fields above:
   - `research_topic` (your question)
   - `project_slug` (kebab-case id → becomes `projects/<slug>/`)
2. Run:

```bash
python scripts/pipeline_state.py init --inputs RESEARCH_PROPOSAL.md
```

Everything else below is optional structure to help you think (and helps the pipeline later when it generates hypotheses, experiments, and a manuscript).

---

## 0. Context and goal

Describe the problem, why now, and what would count as “success”.

## 1. Core claims (hypotheses in plain language)

- H1: …
- H2: …

## 2. Assumptions & risks

- A1: …
- A2: …

## 3. Experiments (high level)

- **Datasets**: …
- **Baselines**: …
- **Ablations**: …
- **Primary metric**: …

## 4. Compute / constraints (optional)

- Budget: …
- Deadline: …

