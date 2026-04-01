<div align="center">

<img src="docs/assets/aletheia-logo.png" alt="ALETHEIA — AleTHEIA · Automated Learning for THEoretical Inference & Analysis · ἀλήθεια" width="720"/>

<p>
  <a href="https://github.com/EmaRimoldi/Claude-scholar-extended/stargazers"><img src="https://img.shields.io/github/stars/EmaRimoldi/Claude-scholar-extended?style=flat-square&color=yellow" alt="Stars"/></a>
  <a href="https://github.com/EmaRimoldi/Claude-scholar-extended/network/members"><img src="https://img.shields.io/github/forks/EmaRimoldi/Claude-scholar-extended?style=flat-square" alt="Forks"/></a>
  <img src="https://img.shields.io/github/last-commit/EmaRimoldi/Claude-scholar-extended?style=flat-square" alt="Last commit"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Claude_Code-Primary-blueviolet?style=flat-square" alt="Claude Code"/>
</p>

**ALETHEIA** — *Automated Learning for THEoretical Inference & Analysis* · **ἀλήθεια** (truth, disclosure)

[From idea to paper](#from-a-simple-idea-to-a-paper-start-here) · [Workflow diagram](#research-workflow-v3) · [Input contract](#input-contract-schema--artifacts) · [Run the pipeline in Claude](#run-the-full-pipeline-in-claude-code) · [Quick start](#quick-start) · [Documentation](#documentation)

</div>

---

ALETHEIA is a **semi-automated research assistant** for computer science and AI researchers: literature and novelty assessment, experiment design, implementation, cluster execution, statistical analysis, manuscript preparation, and submission checks. **Human judgment stays central**; [Claude Code](https://github.com/anthropics/claude-code) runs skills, slash commands, hooks, and the **v3 pipeline** (38 steps, six phases, four novelty gates).

This repository extends and maintains the workflow originally shaped by the **[Claude Scholar](https://github.com/Galaxy-Dawn/claude-scholar)** ecosystem (skills, commands, agents, Obsidian/Zotero integration). ALETHEIA is the project name for this line of work; the repo remains a **Claude Code plugin / configuration bundle** you install into `~/.claude` or use from a cloned tree.

---

## From a simple idea to a paper (start here)

Have you ever wondered whether you could start from a **single rough idea** and still end somewhere that looks like a real paper—literature, experiments, figures, and a manuscript—without losing the plot on day one? The pipeline is built for that: the hard part is not “what button to press,” it is **stating your question clearly once** so every later step has something to lean on.

Here is the recipe.

1. **Open the template** [`examples/pipeline-inputs.min.json`](examples/pipeline-inputs.min.json). Treat it as your kitchen notepad: short, explicit, and easy to edit.
2. **Change two strings** that define your paper before anything else runs:
   - **`project.slug`** — a short kebab-case name (it becomes `projects/<slug>/` on disk).
   - **`research.topic`** — your actual research question in one paragraph (this is what Step 1 feeds to `/research-landscape`; be concrete, not poetic).
3. **Bake that into state** so the orchestrator is deterministic. From the repo root, run (use the same slug and the same wording as `research.topic`):

   ```bash
   python scripts/pipeline_state.py init --project your-slug-here \
     --topic "Paste the same research question you wrote in research.topic"
   ```

   That creates or updates **`pipeline-state.json`** in the directory where you run the command (usually the repo root). The field that matters for the pipeline is **`research_topic`**—that is the string `/run-pipeline` uses for unattended **`--auto`**. If you prefer not to use the CLI, you can edit **`pipeline-state.json`** directly and set **`research_topic`** yourself; the template JSON is still the clearest place to draft it first.

4. **Run** `/run-pipeline` (or `/run-pipeline --auto`) in Claude Code. Your idea is no longer floating in chat—it is anchored in files the workflow reads.

Later, your hypotheses and claims will live in documents under `projects/<slug>/docs/` (for example `hypotheses.md`). The file you touch **at the very beginning** is either **`examples/pipeline-inputs.min.json`** (to draft) or **`pipeline-state.json`** (what the runner actually reads via **`research_topic`**). Same question, two representations: draft in the example, canonical in state.

---

## Research workflow (v3)

The pipeline is **opinionated and checkpointed**: each phase can stop for your decision before continuing.

The diagrams and the summary table below describe the **same six phases** (aligned layout: **960px** wide figures). The first figure is **sequential** (what runs in order and what is script vs LLM). The second is **dependency-oriented** (which artifacts and gates connect phases—not only the main forward path).

### Input contract (schema + artifacts)

Before **`/run-pipeline --auto`**, fix a small set of inputs so the orchestrator does not infer a research question from chat:

- **Machine-readable contract:** [`docs/schemas/pipeline-inputs.schema.json`](docs/schemas/pipeline-inputs.schema.json) (JSON Schema) and example [`examples/pipeline-inputs.min.json`](examples/pipeline-inputs.min.json).
- **Human-readable spec:** [`docs/PIPELINE_INPUTS.md`](docs/PIPELINE_INPUTS.md) — field definitions, implicit dependencies per phase, and a **schema → step** mapping table.
- **Minimum at init:** `python scripts/pipeline_state.py init --project <slug> --topic "…"` stores `research_topic` in `pipeline-state.json` for Step 1 (`/research-landscape`). **`--auto` does not invent a topic.**

Runtime step status and feedback-loop counters stay in **`pipeline-state.json`** and are *not* part of the input schema.

<div align="center">

<img src="docs/assets/aletheia-workflow.svg" width="960" alt="ALETHEIA v3 pipeline — six phases, scripts vs LLM, compute defaults"/>

<img src="docs/assets/aletheia-pipeline-dependencies.svg" width="960" alt="ALETHEIA v3 — artifact flow and feedback loops between phases"/>

<table style="max-width:960px;width:100%;">
<thead>
<tr><th align="left">Phase</th><th align="left">Focus</th><th align="left">Gates / checkpoints</th></tr>
</thead>
<tbody>
<tr><td><b>1</b></td><td>Research &amp; novelty — landscape, claims, citations, adversarial search</td><td><b>N1</b></td></tr>
<tr><td><b>2</b></td><td>Experiment design — baselines, ablations, power (default <b>5 seeds</b> per condition)</td><td><b>N2</b></td></tr>
<tr><td><b>3</b></td><td>Implementation — scaffold, data, model, metrics, validation</td><td>—</td></tr>
<tr><td><b>4</b></td><td>Execution — download, <b>/plan-compute</b>, SLURM jobs, collection. Defaults: <b>1 GPU per job</b>, seed sweeps via <b>job arrays</b> (not one job requesting all GPUs). Validate with <code>scripts/compute_budget_check.py</code>; policy in <a href="rules/compute-budget.md"><code>rules/compute-budget.md</code></a>.</td><td>—</td></tr>
<tr><td><b>5</b></td><td>Analysis &amp; writing — results, claims, story, manuscript, <b>/verify-paper</b></td><td><b>N3</b></td></tr>
<tr><td><b>6</b></td><td>Pre-submission — reviews, recency, <b>N4</b>, compile PDF / Overleaf ZIP</td><td><b>N4</b></td></tr>
</tbody>
</table>

</div>

Details: [`commands/run-pipeline.md`](commands/run-pipeline.md), [`pipeline-v3-spec.md`](pipeline-v3-spec.md). State machine: [`scripts/pipeline_state.py`](scripts/pipeline_state.py).

---

## Run the full pipeline in Claude Code

The intended way to execute the end-to-end flow is the **`/run-pipeline`** slash command inside a **Claude Code** session. It reads and updates **`pipeline-state.json`** and directs work under your **`PROJECT_DIR`** (typically `projects/<topic-slug>/`), not the plugin repo root.

### 1. Install ALETHEIA into Claude Code

From a clone of this repository:

```bash
git clone https://github.com/EmaRimoldi/Claude-scholar-extended.git
cd Claude-scholar-extended
bash scripts/setup.sh
```

`setup.sh` merges skills, commands, agents, rules, hooks, and scripts into `~/.claude/` (with backups). See [Quick start](#quick-start) for minimal or selective installs.

### 2. Open a project and initialize pipeline state

In Claude Code, either work inside the cloned repo or open your research repository that already uses these commands.

1. Create a dedicated project directory and state (if you do not already have one):

   ```
   /new-project "Your research topic"
   ```

   This sets up `projects/<slug>/` and ties **`pipeline-state.json`** to that folder.

2. Or initialize state manually (include **`--topic`** for deterministic Step 1):

   ```bash
   python scripts/pipeline_state.py init --project your-topic-slug \
     --topic "Your full research question for /research-landscape?"
   ```

### 3. Run the orchestrator

In the Claude Code chat, run:

| Command | Effect |
|---------|--------|
| `/run-pipeline` | Interactive mode: next pending step, confirm between steps |
| `/run-pipeline --auto` | Run steps without asking for confirmation |
| `/run-pipeline --resume` | Continue from last incomplete step in `pipeline-state.json` |
| `/run-pipeline --from scaffold` | Start at a given **step id** (e.g. `scaffold`, `analyze-results`) |
| `/run-pipeline --status` | Print progress and exit |
| `/run-pipeline --reset` | Reset all steps to pending |
| `/run-pipeline --skip-online` | Skip steps that need network access |

The command implementation is [`commands/run-pipeline.md`](commands/run-pipeline.md): Claude follows that spec to invoke each slash command in order (e.g. `/research-landscape`, `/design-experiments`, … `/compile-manuscript`).

### 4. Check state from the terminal

```bash
python3 scripts/pipeline_state.py status
python3 scripts/pipeline_state.py steps | head
```

### 5. Read next

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** — prerequisites, credentials, Obsidian bootstrap, phase overview  
- **[docs/CLAUDE_REFERENCE.md](docs/CLAUDE_REFERENCE.md)** — full skill and command index  
- **[CLAUDE.md](CLAUDE.md)** — workspace defaults and lifecycle summary  

---

## Quick start

### Requirements

- [Claude Code](https://github.com/anthropics/claude-code) (primary)
- Git  
- Optional: Python 3.10+ and [uv](https://docs.astral.sh/uv/) for `scripts/` helpers  
- Optional: [Zotero](https://www.zotero.org/) + [zotero-mcp](https://github.com/Galaxy-Dawn/zotero-mcp) for literature workflows  
- Optional: [Obsidian](https://obsidian.md/) for the project knowledge base  

### Full install (recommended)

```bash
git clone https://github.com/EmaRimoldi/Claude-scholar-extended.git
cd Claude-scholar-extended
bash scripts/setup.sh
```

On Windows, use Git Bash or WSL. To update later: `git pull --ff-only` and run `bash scripts/setup.sh` again.

### Minimal install

Copy only the hooks, skills, or commands you need into `~/.claude/`; see the [original quick-start patterns](https://github.com/Galaxy-Dawn/claude-scholar) (subset of `skills/`, `hooks/`). You must merge MCP and hook entries from `settings.json.template` yourself.

### Environment for Python scripts

See [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md).

---

## Core capabilities

| Area | What ALETHEIA supports |
|------|-------------------------|
| Literature & novelty | Multi-pass search, citation ledger, novelty gates, competitive checks |
| Experiments | Design, scaffolded code (Hydra, Registry patterns), SLURM helpers, result collection |
| Analysis | Strict statistics, figures, gap detection, claim–evidence mapping |
| Writing | Manuscript production, `/verify-paper`, LaTeX compile, rebuttal workflow |
| Knowledge | Obsidian project memory, Zotero bridge, daily / experiment logs |

---

## Integrations

- **Zotero** — import, collections, full text via MCP: [MCP_SETUP.md](MCP_SETUP.md)  
- **Obsidian** — filesystem-first project vault: [OBSIDIAN_SETUP.md](OBSIDIAN_SETUP.md)  

---

## Documentation

| File | Contents |
|------|----------|
| [CLAUDE.md](CLAUDE.md) | Workspace configuration and v3 lifecycle summary |
| [docs/CLAUDE_REFERENCE.md](docs/CLAUDE_REFERENCE.md) | Skills, commands, agents |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Researcher onboarding |
| [docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md) | Where paper/project outputs live (`projects/<slug>/`) |
| [docs/PIPELINE_INPUTS.md](docs/PIPELINE_INPUTS.md) | Formal input spec, schema link, field→step map, `/run-experiment` prerequisites |
| [docs/schemas/pipeline-inputs.schema.json](docs/schemas/pipeline-inputs.schema.json) | JSON Schema for pre-pipeline inputs |
| [settings.json.template](settings.json.template) | Hooks, plugins, MCP template |

---

## Contributing

Issues and pull requests are welcome. For installer or workflow changes, describe the scenario, current limitation, and expected behavior.

---

## License

MIT License.

---

## Citation

If ALETHEIA helps your work, you can cite this repository as:

```bibtex
@misc{aletheia_2026,
  title        = {{ALETHEIA}: Semi-automated research assistant (Claude Code workflow)},
  author       = {Rimoldi, Ema},
  year         = {2026},
  howpublished = {\url{https://github.com/EmaRimoldi/Claude-scholar-extended}},
  note         = {Extends the Claude Scholar plugin ecosystem}
}
```

---

## Acknowledgments

- Built for **[Claude Code](https://github.com/anthropics/claude-code)**.  
- Workflow lineage and community roots: **[Claude Scholar](https://github.com/Galaxy-Dawn/claude-scholar)** (Gaorui Zhang et al.).  
- Inspiration: [everything-claude-code](https://github.com/anthropics/everything-claude-code), [AI-research-SKILLs](https://github.com/zechenzhangAGI/AI-research-SKILLs).

---

**Repository:** [https://github.com/EmaRimoldi/Claude-scholar-extended](https://github.com/EmaRimoldi/Claude-scholar-extended)
