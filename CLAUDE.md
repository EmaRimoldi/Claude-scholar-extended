# Claude Scholar Configuration

> For the complete skills/commands/agents reference, see [docs/CLAUDE_REFERENCE.md](docs/CLAUDE_REFERENCE.md).

## Project Overview

**Claude Scholar** - Semi-automated research assistant for academic research and software development.

**Mission**: Support Claude Code, OpenCode, and Codex CLI across ideation, coding, experiments, writing, publication, plugin development, and project management.

---

## User Background

- **Degree**: Computer Science PhD
- **Target Venues**: NeurIPS, ICML, ICLR, KDD, Nature, Science, Cell, PNAS
- **Focus**: Academic writing quality, logical coherence, natural expression
- **Package manager**: `uv` | **Config**: Hydra + OmegaConf | **Training**: Transformers Trainer
- **Git**: Conventional Commits, rebase for sync, merge --no-ff for integration

---

## Global Configuration

### Language
- Respond in English; keep technical terms in English; do not translate proper nouns

### Working Directories
- Plan documents: `/plan` | Temporary files: `/temp` | Auto-create if missing

### Work Style
- Discuss approach before breaking down complex tasks
- Run example tests after implementation; make backups; clean up temp files
- Python follows PEP 8, comments and identifiers in English
- Use TodoWrite to track progress; ask proactively when uncertain

---

## Research Lifecycle (20-Step Pipeline)

```
Ideation → Validation → Design → Execute → Analyze → [Iterate] → Pre-Write → Write → Review → Submit → Post
```

| Stage | Steps | Key Commands |
|-------|-------|-------------|
| Ideation & Validation | 1-2 | `/research-init`, `/check-competition` |
| Experiment Design | 3 | `/design-experiments` |
| Implementation | 4-8 | `/scaffold`, `/build-data`, `/setup-model`, `/implement-metrics`, `/validate-setup` |
| Execution | 9-13 | `/download-data`, `/plan-compute`, `/run-experiment`, `/collect-results`, `/analyze-results` |
| Pre-Writing | 14-16 | `/map-claims`, `/position`, `/story` |
| Manuscript | 17-20 | `/produce-manuscript`, `/quality-review`, `/compile-manuscript`, `/rebuttal` |

**Orchestrator**: `/run-pipeline` (supports `--auto`, `--resume`, `--from <step>`, `--status`, `--reset`, `--skip-online`)

### Supporting Workflows

- **Automation**: 5 hooks auto-trigger at session lifecycle stages
- **Zotero**: Automated paper import, collection management, full-text reading, citation export
- **Obsidian**: Filesystem-first project knowledge base (literature, plans, daily logs, experiments, results, writing)
- **Knowledge Extraction**: `paper-miner` and `kaggle-miner` agents extract knowledge from papers and competitions

### Obsidian Project Knowledge Base Rule

- If repo contains `.claude/project-memory/registry.yaml` → auto-activate `obsidian-project-memory`
- If unbound research project → auto-activate `obsidian-project-bootstrap`
- On every substantial turn, update daily note and repo-local project memory file
- Touch `00-Hub.md` only when top-level project status really changes
- No extra Obsidian API configuration or keys required

---

## Rules (5 Global Constraints)

| Rule | Purpose |
|------|---------|
| `coding-style.md` | 200-400 line files, immutable config, type hints, Factory & Registry patterns |
| `agents.md` | Auto-invocation timing, parallel execution, multi-perspective analysis |
| `security.md` | Key management, sensitive file protection, pre-commit security checks |
| `experiment-reproducibility.md` | Random seeds, config recording, environment recording, checkpoints |
| `context-engineering.md` | Token budgets, summarization strategies, context thresholds |

---

## Naming Conventions

- **Skills**: kebab-case, prefer gerund form (`scientific-writing`, `bug-detective`)
- **Tags**: Title Case, abbreviations all caps (`[Writing, Research, TDD]`)
- **Descriptions**: Third person, include purpose and use cases

---

## Task Completion Summary

After each task, proactively provide:

```
📋 Operation Review
1. [Main operation]
2. [Modified files]

📊 Current Status
• [Git/filesystem/runtime status]

💡 Next Steps
1. [Targeted suggestions]
```
