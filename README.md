<div align="center">
  <img src="LOGO.png" alt="Claude Scholar Logo" width="100%"/>

  <p>
    <a href="https://github.com/Galaxy-Dawn/claude-scholar/stargazers"><img src="https://img.shields.io/github/stars/Galaxy-Dawn/claude-scholar?style=flat-square&color=yellow" alt="Stars"/></a>
    <a href="https://github.com/Galaxy-Dawn/claude-scholar/network/members"><img src="https://img.shields.io/github/forks/Galaxy-Dawn/claude-scholar?style=flat-square" alt="Forks"/></a>
    <img src="https://img.shields.io/github/last-commit/Galaxy-Dawn/claude-scholar?style=flat-square" alt="Last Commit"/>
    <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"/>
    <img src="https://img.shields.io/badge/Claude_Code-Compatible-blueviolet?style=flat-square" alt="Claude Code"/>
    <img src="https://img.shields.io/badge/Codex_CLI-Compatible-blue?style=flat-square" alt="Codex CLI"/>
    <img src="https://img.shields.io/badge/OpenCode-Compatible-orange?style=flat-square" alt="OpenCode"/>
  </p>

  <strong>Language</strong>: <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</div>

> Semi-automated research assistant for academic research and software development. Supports [Claude Code](https://github.com/anthropics/claude-code), [Codex CLI](https://github.com/openai/codex), and [OpenCode](https://github.com/opencode-ai/opencode) across literature review, coding, experiments, reporting, writing, and project knowledge management.

## Recent News

- **2026-03-18**: **Results reporting, writing memory, and workflow cleanup** — split post-experiment work into `results-analysis` for strict statistics, real scientific figures, `analysis-report` / `stats-appendix` / `figure-catalog`, and `results-report` for decision-oriented post-experiment reports with Obsidian write-back; removed the redundant `data-analyst` entrypoint, made `/analyze-results` the default one-shot command for analysis + report generation, introduced a global `paper-miner` writing memory with the new `/mine-writing-patterns` command, wired `ml-paper-writing` and `review-response` to read that shared memory, refreshed the README around human-centered semi-automation, and updated the project logo.
- **2026-03-17**: **Obsidian project knowledge base** — filesystem-first project knowledge base with project import, repo-bound auto-sync, durable knowledge routed across `Papers / Knowledge / Experiments / Results / Writing`, round-level experiment reports stored under `Results/Reports/`, and no MCP requirement.
- **2026-02-26**: **Zotero MCP Web API mode** — remote Zotero access, DOI/arXiv/URL import, collection management, item updates, and safer setup guidance across Claude Code, Codex CLI, and OpenCode.

<details>
<summary>View older changelog</summary>

- **2026-02-25**: **Codex CLI** support — added `codex` branch supporting [OpenAI Codex CLI](https://github.com/openai/codex) with config.toml, 40 skills, 14 agents, and sandbox security
- **2026-02-23**: Added `setup.sh` installer — backup-aware incremental updates for existing `~/.claude`, auto-backup `settings.json`, additive hooks/mcpServers/plugins merge
- **2026-02-21**: **OpenCode** support — Claude Scholar now supports [OpenCode](https://github.com/opencode-ai/opencode) as an alternative CLI; switch to the `opencode` branch for OpenCode-compatible configuration
- **2026-02-20**: Bilingual config — translated `CLAUDE.md` to English for international readability; added `CLAUDE.zh-CN.md` as Chinese backup; Chinese users can switch with `cp CLAUDE.zh-CN.md CLAUDE.md`
- **2026-02-15**: Zotero MCP integration — added `/zotero-review` and `/zotero-notes` commands, updated `research-ideation` skill with Zotero integration guide, enhanced `literature-reviewer` agent with Zotero MCP support for automated paper import, collection management, full-text reading, and citation export
- **2026-02-14**: Hooks optimization — restructured `security-guard` to two-tier system (Block + Confirm), `skill-forced-eval` now groups skills into 6 categories with silent scan mode, `session-start` limits display to top 5, `session-summary` adds 30-day log auto-cleanup, `stop-summary` shows separate added/modified/deleted counts; removed deprecated shell scripts (lib/common.sh, lib/platform.sh)
- **2026-02-11**: Major update — added 10 new skills (research-ideation, results-analysis, citation-verification, review-response, paper-self-review, post-acceptance, daily-coding, frontend-design, ui-ux-pro-max, web-design-reviewer), 7 new agents, 8 research workflow commands, 2 new rules (security, experiment-reproducibility); restructured CLAUDE.md; 89 files changed
- **2026-01-26**: Rewrote all Hooks to cross-platform Node.js; completely rewrote README; expanded ML paper writing knowledge base; merged PR #1 (cross-platform support)
- **2026-01-25**: Project open-sourced, v1.0.0 released with 25 skills (architecture-design, bug-detective, git-workflow, kaggle-learner, scientific-writing, etc.), 2 agents (paper-miner, kaggle-miner), 30+ commands (including SuperClaude suite), 5 Shell Hooks, and 2 rules (coding-style, agents)

</details>

## Quick Navigation

| Section | What it helps with |
|---|---|
| [Why Claude Scholar](#why-claude-scholar) | Understand the project positioning and target use cases. |
| [Core Workflow](#core-workflow) | See the end-to-end research pipeline from ideation to publication. |
| [Quick Start](#quick-start) | Install Claude Scholar in full, minimal, or selective mode. |
| [Integrations](#integrations) | Learn how Zotero and Obsidian fit into the workflow. |
| [Primary Workflows](#primary-workflows) | Browse the main research and development workflows. |
| [Supporting Workflows](#supporting-workflows) | See the background systems that strengthen the main workflow. |
| [Documentation](#documentation) | Jump to setup docs, configuration, and templates. |
| [Citation](#citation) | Cite Claude Scholar in papers, reports, or project docs. |

## Why Claude Scholar

Claude Scholar is **not** an end-to-end autonomous research system that tries to replace the researcher.

Its core idea is simple:

> **human decision-making stays at the center; the assistant accelerates the workflow around it.**

That means Claude Scholar is designed to help with the heavy, repetitive, and structure-sensitive parts of research — literature organization, note-taking, experiment analysis, reporting, and writing support — while still keeping the key judgments in human hands:

- which problem is worth pursuing,
- which papers actually matter,
- which hypotheses are worth testing,
- which results are convincing,
- and what should be written, submitted, or abandoned.

In other words, Claude Scholar is a **semi-automated research assistant**, not a “fully automated scientist.”

## Core Workflow

- **Ideation**: turn a vague topic into concrete questions, research gaps, and an initial plan.
- **Literature**: search, import, organize, and read papers through Zotero collections.
- **Paper notes**: convert papers into structured reading notes and reusable claims.
- **Knowledge base**: route durable knowledge into Obsidian across `Papers / Knowledge / Experiments / Results / Writing`, with round-level experiment reports stored under `Results/Reports/`.
- **Experiments**: track hypotheses, experiment lines, run history, findings, and next actions.
- **Analysis**: generate strict statistics, real scientific figures, and analysis artifacts with `results-analysis`.
- **Reporting**: produce a complete post-experiment report with `results-report`, then write it back into Obsidian.
- **Writing and publication**: carry stable findings into literature reviews, papers, rebuttals, slides, posters, and promotion.

## Quick Start

### Requirements

- [Claude Code](https://github.com/anthropics/claude-code)
- Git
- (Optional) Python + [uv](https://docs.astral.sh/uv/) for Python development
- (Optional) [Zotero](https://www.zotero.org/) + [Galaxy-Dawn/zotero-mcp](https://github.com/Galaxy-Dawn/zotero-mcp) for literature workflows
- (Optional) [Obsidian](https://obsidian.md/) for project knowledge-base workflows

### Option 1: Full Installation (Recommended)

```bash
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar
bash /tmp/claude-scholar/scripts/setup.sh
```

The installer is **backup-aware and incremental-update friendly**:
- updates repo-managed `skills/commands/agents/rules/hooks/scripts/CLAUDE*.md`,
- backs up overwritten files to `~/.claude/.claude-scholar-backups/<timestamp>/`,
- backs up `settings.json` to `settings.json.bak`,
- preserves your existing `env`, model/provider settings, API keys, permissions, and current `mcpServers` values,
- adds missing hook entries instead of replacing your entire hook set.

To update later:

```bash
cd /tmp/claude-scholar
git pull --ff-only
bash scripts/setup.sh
```

### Option 2: Minimal Installation

Install only a small research-focused subset:

```bash
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar
mkdir -p ~/.claude/hooks ~/.claude/skills
cp /tmp/claude-scholar/hooks/*.js ~/.claude/hooks/
cp -r /tmp/claude-scholar/skills/ml-paper-writing ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/research-ideation ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/results-analysis ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/results-report ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/review-response ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/writing-anti-ai ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/git-workflow ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/bug-detective ~/.claude/skills/
```

**Post-install**: minimal/manual install does **not** auto-merge `settings.json`; copy only the hooks or MCP entries you want from `settings.json.template`.

### Option 3: Selective Installation

Copy only the parts you need:

```bash
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar
cd /tmp/claude-scholar

cp hooks/*.js ~/.claude/hooks/
cp -r skills/latex-conference-template-organizer ~/.claude/skills/
cp -r skills/architecture-design ~/.claude/skills/
cp agents/paper-miner.md ~/.claude/agents/
cp rules/coding-style.md ~/.claude/rules/
cp rules/agents.md ~/.claude/rules/
```

**Post-install**: selective/manual install does **not** auto-merge `settings.json`; copy only the hooks or MCP entries you actually want from `settings.json.template`.

## Platform Support

Claude Scholar is maintained for:

- **Claude Code** — the primary installation target.
- **Codex CLI** — supported workflow and documentation are available in this repo ecosystem.
- **OpenCode** — supported as an alternative CLI workflow.

The top-level workflow is the same: research, coding, experiments, reporting, and project knowledge management.

## Integrations

### Zotero

Use Zotero when you want Claude Scholar to help with:
- paper import via DOI / arXiv / URL,
- collection-based reading workflows,
- full-text access through Zotero MCP,
- detailed paper notes and literature synthesis.

See [MCP_SETUP.md](./MCP_SETUP.md).

### Obsidian

Use Obsidian when you want Claude Scholar to maintain a filesystem-first research knowledge base:
- `Papers/`
- `Experiments/`
- `Results/`
- `Results/Reports/`
- `Writing/`
- `Daily/`

See [OBSIDIAN_SETUP.md](./OBSIDIAN_SETUP.md).

## Primary Workflows

Complete academic research lifecycle — 7 stages from idea to publication.

### 1. Research Ideation (Zotero-Integrated)

End-to-end research startup from idea generation to literature management.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `research-ideation` | Turn vague topics into structured questions, gap analysis, and an initial research plan. |
| Agent | `literature-reviewer` | Search, classify, and synthesize papers into an actionable literature picture. |
| Command | `/research-init` | Start a new topic from literature search to Zotero organization and proposal drafting. |
| Command | `/zotero-review` | Review an existing Zotero collection and generate a structured literature synthesis. |
| Command | `/zotero-notes` | Batch-read a Zotero collection and create structured paper reading notes. |

**How it works**
- **5W1H Brainstorming**: turn a vague topic into structured questions (`What / Why / Who / When / Where / How`).
- **Literature Search & Import**: search papers, extract DOI/arXiv/URLs, import them into Zotero, and organize them into themed collections.
- **PDF & Full Text**: attach PDFs when available, read full text when possible, and fall back to abstract-level analysis when necessary.
- **Gap Analysis**: identify literature, methodological, application, interdisciplinary, or temporal gaps.
- **Research Question & Planning**: convert the review into concrete questions, initial hypotheses, and next-step planning.

**Typical output**
- literature review notes
- structured Zotero collection
- project proposal / research direction draft

### 2. ML Project Development

Maintainable ML project structure for experiment code and iteration.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `architecture-design` | Define maintainable ML project structure when new registrable components or modules are introduced. |
| Skill | `git-workflow` | Enforce branch hygiene, commit conventions, and safer collaboration workflows. |
| Skill | `bug-detective` | Debug stack traces, shell failures, and code-path issues systematically. |
| Agent | `code-reviewer` | Review modified code for correctness, maintainability, and implementation quality. |
| Agent | `dev-planner` | Break complex engineering work into concrete implementation steps. |
| Command | `/plan` | Create or refine an implementation plan before coding. |
| Command | `/commit` | Prepare a conventional commit for the current changes. |
| Command | `/code-review` | Run a focused review on the current code changes. |
| Command | `/tdd` | Drive feature work through small, test-backed implementation steps. |

**How it works**
- **Structure**: use Factory / Registry patterns for new ML components when appropriate.
- **Code Quality**: keep files maintainable, typed, and config-driven.
- **Debugging**: inspect stack traces, shell failures, and code-path issues systematically.
- **Git Discipline**: use branch hygiene, conventional commits, and safer merge/rebase workflows.

### 3. Experiment Analysis

Strict analysis of experimental results with scientific figures and report-ready artifacts.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `results-analysis` | Produce a strict analysis bundle with rigorous statistics, real scientific figures, and analysis artifacts. |
| Skill | `results-report` | Turn analysis artifacts into a complete post-experiment report with decisions, limitations, and next actions. |
| Command | `/analyze-results` | Run the full experiment workflow in one shot: strict analysis first, then final report generation. |

**How it works**
- **Data Processing**: read experiment logs, metrics files, and result directories.
- **Statistical Testing**: run strict statistical checks such as t-test / ANOVA / Wilcoxon where appropriate.
- **Visualization**: generate real scientific figures with interpretation guidance, not just vague plotting suggestions.
- **Ablation & Comparison**: analyze component contribution, performance tradeoffs, and stability.
- **Post-Experiment Reporting**: turn the analysis bundle into a full retrospective report with conclusions, limitations, and next actions.

**Typical output**
- `analysis-report.md`
- `stats-appendix.md`
- `figure-catalog.md`
- `figures/`
- post-experiment summary report in Obsidian `Results/Reports/`

### 4. Paper Writing

Systematic academic writing from structure setup to draft refinement.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `ml-paper-writing` | Draft publication-oriented ML/AI papers from repo context, evidence, and literature. |
| Skill | `citation-verification` | Check references, metadata, and claim-citation alignment to prevent citation mistakes. |
| Skill | `writing-anti-ai` | Reduce robotic phrasing and improve clarity, rhythm, and human academic tone. |
| Skill | `latex-conference-template-organizer` | Clean messy conference templates into an Overleaf-ready writing structure. |
| Agent | `paper-miner` | Mine strong papers for reusable writing patterns, structure, and venue expectations. |
| Command | `/mine-writing-patterns` | Read a paper and merge reusable writing knowledge into the global paper-miner writing memory. |

**How it works**
- **Template Preparation**: clean conference templates into an Overleaf-ready structure.
- **Citation Verification**: verify references, metadata, and claim-citation alignment.
- **Systematic Writing**: draft sections from repo context, experiment evidence, and literature notes.
- **Style Refinement**: reduce robotic phrasing and improve rhythm, clarity, and tone.

### 5. Paper Self-Review

Quality assurance before submission.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `paper-self-review` | Audit structure, logic, citations, figures, and compliance before submission. |

**How it works**
- **Structure Check**: logical flow, section balance, and narrative coherence.
- **Logic Validation**: claim-evidence alignment, assumption clarity, and argument consistency.
- **Citation Audit**: reference correctness and completeness.
- **Figure Quality**: caption completeness, readability, and accessibility.
- **Compliance**: page limits, formatting, and disclosure requirements.

### 6. Submission & Rebuttal

Submission preparation and review response workflow.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `review-response` | Structure reviewer comments into an evidence-based rebuttal workflow. |
| Agent | `rebuttal-writer` | Draft professional, respectful, and strategically organized rebuttal text. |
| Command | `/rebuttal` | Generate a complete rebuttal draft from review comments and evidence. |

**How it works**
- **Pre-submission Checks**: venue-specific formatting, anonymization, and checklist requirements.
- **Review Analysis**: classify reviewer comments into actionable categories.
- **Response Strategy**: decide whether to accept, defend, clarify, or propose new experiments.
- **Rebuttal Writing**: generate structured, evidence-based responses with professional tone.

### 7. Post-Acceptance Processing

Conference preparation and research promotion after acceptance.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `post-acceptance` | Support talks, posters, and research promotion after acceptance. |
| Command | `/presentation` | Generate presentation structure and speaking guidance for the accepted work. |
| Command | `/poster` | Organize the work into poster-ready content and layout guidance. |
| Command | `/promote` | Draft public-facing promotion content such as summaries, posts, or threads. |

**How it works**
- **Presentation**: prepare talk structure and slide guidance.
- **Poster**: organize content into poster-ready layout and hierarchy.
- **Promotion**: generate social media, blog, or summary material for broader communication.

## Supporting Workflows

These workflows run in the background to strengthen the primary workflows.

### Obsidian Project Knowledge Base

Use Obsidian as the durable sink for project knowledge, not just as a note dump.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `obsidian-project-memory` | Maintain the project-level Obsidian knowledge base and decide what durable knowledge should be written back. |
| Skill | `obsidian-project-bootstrap` | Initialize an Obsidian knowledge base for a new or existing research project. |
| Skill | `obsidian-research-log` | Record daily research progress, plans, ideas, and TODOs into the knowledge base. |
| Skill | `obsidian-experiment-log` | Capture experiment setup, run history, outcomes, and follow-up actions in Obsidian. |
| Command | `/obsidian-ingest` | Ingest a new Markdown file or folder into the correct place in the knowledge base. |
| Command | `/obsidian-note` | Manage a single note lifecycle such as lookup, rename, archive, or purge. |
| Command | `/obsidian-views` | Generate or refresh optional Obsidian views such as `.base` files. |

**How it works**
- bind an existing repo to an Obsidian vault,
- route stable knowledge into `Papers / Knowledge / Experiments / Results / Writing`, with round-level experiment reports stored under `Results/Reports/`,
- keep `Daily/` and project memory updated conservatively,
- ingest new Markdown files into the correct canonical destination,
- optionally generate extra views and canvases.

### Automated Enforcement Workflow

Cross-platform hooks automate routine workflow checks and reminders.

**Hooks**
- `skill-forced-eval.js`
- `session-start.js`
- `session-summary.js`
- `stop-summary.js`
- `security-guard.js`

**How it works**
- **Before prompts**: evaluate applicable skills and surface relevant workflow hints.
- **At session start**: show Git state, available commands, and project-memory context.
- **At session end/stop**: summarize work and remind the user about minimum maintenance tasks.
- **Security**: block catastrophic commands and require confirmation for dangerous but legitimate ones.

### Knowledge Extraction Workflow

Specialized agents can mine reusable knowledge from papers and competitions.

| Type | Name | One-line explanation |
|---|---|---|
| Agent | `paper-miner` | Extract reusable writing knowledge, structure patterns, and venue heuristics from strong papers. |
| Agent | `kaggle-miner` | Extract engineering practices and solution patterns from strong Kaggle workflows. |

**How it works**
- extract writing patterns, venue expectations, and rebuttal strategies from papers,
- extract engineering patterns and solution structure from Kaggle workflows,
- feed those insights back into skills and reference material.

### Skill Evolution System

Claude Scholar also contains a self-improvement loop for its own skills.

| Type | Name | One-line explanation |
|---|---|---|
| Skill | `skill-development` | Create new skills with clear triggers, structure, and progressive disclosure. |
| Skill | `skill-quality-reviewer` | Review skills across content quality, organization, style, and structural integrity. |
| Skill | `skill-improver` | Apply structured improvement plans to evolve existing skills. |

**How it works**
- create new skills with clear trigger descriptions,
- review them across quality dimensions,
- apply structured improvements and iterate.

## Documentation

- [MCP_SETUP.md](./MCP_SETUP.md) — Zotero/browser MCP setup
- [OBSIDIAN_SETUP.md](./OBSIDIAN_SETUP.md) — Obsidian knowledge base workflow
- [CLAUDE.md](./CLAUDE.md) — full local configuration, skill list, and workflow details
- [CLAUDE.zh-CN.md](./CLAUDE.zh-CN.md) — Chinese version of the main configuration doc
- [settings.json.template](./settings.json.template) — optional settings template for hooks/plugins/MCP

## Project Rules

Claude Scholar includes project rules for:
- coding style,
- agent orchestration,
- security,
- experiment reproducibility.

These are reflected in the shipped rules and in `CLAUDE.md`.

## Contributing

Issues, PRs, and workflow improvements are welcome.

If you propose changes to installer behavior, Zotero workflows, or Obsidian routing, please include:
- the user scenario,
- the current limitation,
- the expected behavior,
- and any compatibility concerns.

## License

MIT License.

## Citation

If Claude Scholar helps your research or engineering workflow, you can cite the repository as:

```bibtex
@misc{claude_scholar_2026,
  title        = {Claude Scholar: Semi-automated research assistant for academic research and software development},
  author       = {Gaorui Zhang},
  year         = {2026},
  howpublished = {\url{https://github.com/Galaxy-Dawn/claude-scholar}},
  note         = {GitHub repository}
}
```

## Acknowledgments

Built with Claude Code CLI and enhanced by the open-source community.

### References

This project is inspired by and builds upon excellent work from the community:

- **[everything-claude-code](https://github.com/anthropics/everything-claude-code)** - Comprehensive resource for Claude Code CLI
- **[AI-research-SKILLs](https://github.com/zechenzhangAGI/AI-research-SKILLs)** - Research-focused skills and configurations

These projects provided valuable insights and foundations for the research-oriented features in Claude Scholar.

---

**For data science, AI research, and academic writing.**

Repository: [https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar)
