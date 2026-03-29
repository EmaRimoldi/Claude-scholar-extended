# Claude Scholar Reference

> Complete directory of skills, commands, agents, and hooks. For core configuration, see [CLAUDE.md](../CLAUDE.md).

---

## Skills Directory (65 skills)

### Research & Analysis (5 skills)

- **research-ideation**: Research startup (5W1H, literature review, gap analysis, research question formulation, Zotero integration)
- **results-analysis**: Strict experiment analysis (rigorous statistics, scientific figures, ablation studies)
- **results-report**: Complete post-experiment summary reporting (retrospection, decision support, Obsidian results reports)
- **citation-verification**: Citation verification (multi-layer: format→API→info→content)
- **daily-paper-generator**: Daily paper generator for research tracking

### Research Validation, Design & Iteration (7 skills)

- **novelty-assessment**: Compare proposed contribution against closest prior works, flag incremental contributions
- **hypothesis-formulation**: Convert research gaps into falsifiable hypotheses with success/failure criteria
- **competitive-check**: Generate structured search queries for competitive landscape checks, analyze user-provided results
- **experiment-design**: Pre-experiment planning: baselines, ablations, sample size, resource estimation
- **failure-diagnosis**: Systematic diagnosis of research-level experiment failures (not code bugs)
- **hypothesis-revision**: Iterative hypothesis refinement with pivot/persevere/abandon decisions, Obsidian write-back
- **claim-evidence-bridge**: Map paper claims to experimental evidence, manage paper scope

### Experiment Implementation (5 skills)

- **project-scaffold**: Generate runnable project from experiment plan (pyproject.toml, Factory/Registry, Hydra, entry point)
- **experiment-data-builder**: Translate dataset specs into generators/loaders (synthetic, HuggingFace, benchmarks)
- **model-setup**: Load, introspect, hook, and ablate models (HuggingFace, hooks, architecture discovery, surgery)
- **measurement-implementation**: Implement metrics, analytical references, statistical tests (OLS, GD, ridge, Bayes-optimal catalog)
- **setup-validation**: Pre-flight checklist: data integrity, model loading, measurement correctness, ablation, baseline, smoke test

### Compute & Execution (3 skills)

- **compute-planner**: GPU/memory estimation, SLURM script generation, MIT Engaging partition selection, scheduling strategy
- **experiment-runner**: Execute experiment matrix via SLURM with phased gates, failure recovery, progress tracking
- **result-collector**: Aggregate per-run outputs into structured tables for results-analysis

### Manuscript Pipeline (3 skills)

- **contribution-positioning**: Differentiation matrix, contribution statement, reviewer objection anticipation
- **story-construction**: Narrative arc, result triage, figure plan, section outline → paper-blueprint.md
- **manuscript-production**: Publication-quality figures, full prose, LaTeX source, submission package

### Paper Writing & Publication (7 skills)

- **ml-paper-writing**: ML/AI paper writing assistance (NeurIPS, ICML, ICLR, ACL, AAAI, COLM, Nature, Science, Cell, PNAS)
- **writing-anti-ai**: Remove AI writing patterns, bilingual (Chinese/English)
- **paper-self-review**: Paper self-review (6-item quality checklist)
- **review-response**: Systematic rebuttal writing
- **post-acceptance**: Post-acceptance processing (presentation, poster, promotion)
- **doc-coauthoring**: Document co-authoring workflow
- **latex-conference-template-organizer**: LaTeX conference template organization

### Development Workflows (6 skills)

- **daily-coding**: Daily coding checklist (minimal mode, auto-triggered)
- **git-workflow**: Git workflow standards (Conventional Commits, branch management)
- **code-review-excellence**: Code review best practices
- **bug-detective**: Debugging and error investigation (Python, Bash/Zsh, JavaScript/TypeScript)
- **architecture-design**: ML project code architecture and design patterns
- **verification-loop**: Verification loops and testing

### Plugin Development (8 skills)

- **skill-development**: Skill development guide
- **skill-improver**: Skill improvement tool
- **skill-quality-reviewer**: Skill quality review
- **command-development**: Slash command development
- **plugin-structure**: Plugin structure guide
- **agent-identifier**: Agent development configuration
- **hook-development**: Hook development and event handling
- **mcp-integration**: MCP server integration

### Tools & Utilities (4 skills)

- **planning-with-files**: Planning and progress tracking with Markdown files
- **uv-package-manager**: uv package manager usage
- **webapp-testing**: Local web application testing
- **kaggle-learner**: Kaggle competition learning

### Obsidian Knowledge Base (11 skills)

- **obsidian-project-memory**: Default Obsidian project-memory orchestrator for repo-bound research work
- **obsidian-project-bootstrap**: Bootstrap or import a research repository into an Obsidian project knowledge base
- **obsidian-research-log**: Daily notes, plans, hub updates, and durable progress routing
- **obsidian-experiment-log**: Experiments, ablations, and result logging
- **obsidian-link-graph**: Legacy compatibility helper for repairing wikilinks across canonical notes
- **obsidian-synthesis-map**: Legacy compatibility helper for higher-level synthesis notes and comparison summaries
- **obsidian-project-lifecycle**: Detach, archive, purge, and note-level lifecycle operations
- **zotero-obsidian-bridge**: Bridge Zotero collections/full text into durable Obsidian paper notes and the default `Maps/literature.canvas`
- **obsidian-literature-workflow**: Paper-note normalization and literature review inside the project vault
- **obsidian-markdown**: Vendored official Obsidian Flavored Markdown skill
- **obsidian-cli**: Vendored official Obsidian CLI skill
- **obsidian-bases / json-canvas / defuddle**: Vendored official optional support for `.base`, `.canvas`, and clean web-to-markdown extraction

### Web Design (3 skills)

- **frontend-design**: Create distinctive, production-grade frontend interfaces
- **ui-ux-pro-max**: UI/UX design intelligence (50+ styles, 97 palettes, 57 font pairings, 9 stacks)
- **web-design-reviewer**: Visual website inspection for responsive, accessibility, and layout issues

---

## Commands (50+ Commands)

### Research Workflow Commands

| Command | Function |
|---------|----------|
| `/research-init` | Start Zotero-integrated research ideation workflow (auto-create collections, import papers, full-text analysis) |
| `/zotero-review` | Read papers from Zotero collection, synthesize into Obsidian literature review and downstream project notes |
| `/zotero-notes` | Batch read Zotero papers, create/update detailed Obsidian paper notes and refresh `Maps/literature.canvas` |
| `/obsidian-init` | Bootstrap or import an Obsidian project knowledge base for the current research repository |
| `/obsidian-ingest` | Ingest a new Markdown file or directory via classify -> promote / merge / stage-to-daily |
| `/obsidian-review` | Generate project-linked literature synthesis from Obsidian paper notes |
| `/obsidian-notes` | Normalize paper notes and connect them to project knowledge, experiments, and results |
| `/obsidian-sync` | Force incremental or full repair sync between the repo, project memory, and Obsidian |
| `/obsidian-link` | Repair or strengthen project wikilinks across canonical notes |
| `/obsidian-note` | Archive, purge, or rename a single canonical note |
| `/obsidian-project` | Detach, archive, purge, or rebuild a project knowledge base |
| `/obsidian-views` | Explicitly generate optional `.base` views and extra canvases |
| `/design-experiments` | Generate full experiment plan from hypotheses (baselines, ablations, sample size, resource estimation) |
| `/check-competition` | Generate search queries for competitive landscape check, analyze pasted results |
| `/map-claims` | Map paper claims to experimental evidence, manage paper scope before writing |
| `/scaffold` | Generate runnable ML project from experiment plan (pyproject.toml, src/, configs, entry point) |
| `/build-data` | Translate dataset specs into working generators and loaders |
| `/setup-model` | Load, configure, introspect, and prepare models for experiments |
| `/implement-metrics` | Implement metrics, analytical references, and statistical tests |
| `/validate-setup` | Run pre-flight validation checklist before full experiment sweep |
| `/download-data` | Download datasets and models to local cache before GPU jobs |
| `/plan-compute` | Estimate GPU resources, generate SLURM scripts for MIT Engaging |
| `/run-experiment` | Execute experiment matrix via SLURM with phased gates and failure recovery |
| `/collect-results` | Aggregate raw outputs into structured tables for analysis |
| `/position` | Map contribution against closest prior works, anticipate reviewer objections |
| `/story` | Define narrative arc, triage results, create figure plan, produce paper blueprint |
| `/produce-manuscript` | Generate figures, prose, LaTeX source, and submission package |
| `/analyze-results` | Analyze experiment results (statistical tests, visualization, ablation) |
| `/run-pipeline` | Run the full research pipeline end-to-end with checkpoints (supports --auto, --resume, --from, --status) |
| `/slurm-status` | Show SLURM job status, queue, pipeline job tracking, and cluster GPU availability |
| `/rebuttal` | Generate systematic rebuttal document |
| `/presentation` | Create conference presentation outline |
| `/poster` | Generate academic poster design |
| `/promote` | Generate promotion content (Twitter, LinkedIn, blog) |

### Development Workflow Commands

| Command | Function |
|---------|----------|
| `/plan` | Create implementation plan |
| `/commit` | Commit code (following Conventional Commits) |
| `/update-github` | Commit and push to GitHub |
| `/update-readme` | Update README documentation |
| `/code-review` | Code review |
| `/tdd` | Test-driven development workflow |
| `/build-fix` | Fix build errors |
| `/verify` | Verify changes |
| `/checkpoint` | Create checkpoint |
| `/refactor-clean` | Refactor and clean up |
| `/learn` | Extract reusable patterns from code |
| `/create_project` | Create new project |
| `/setup-pm` | Configure package manager (uv/pnpm) |
| `/update-memory` | Check and update CLAUDE.md memory |

### SuperClaude Command Suite (`/sc`)

- `/sc agent` - Agent dispatch
- `/sc analyze` - Code analysis
- `/sc brainstorm` - Interactive brainstorming
- `/sc build` - Build project
- `/sc business-panel` - Business panel
- `/sc cleanup` - Code cleanup
- `/sc design` - System design
- `/sc document` - Generate documentation
- `/sc estimate` - Effort estimation
- `/sc explain` - Code explanation
- `/sc git` - Git operations
- `/sc help` - Help info
- `/sc implement` - Feature implementation
- `/sc improve` - Code improvement
- `/sc index` - Project index
- `/sc index-repo` - Repository index
- `/sc load` - Load context
- `/sc pm` - Package manager operations
- `/sc recommend` - Recommend solutions
- `/sc reflect` - Reflection summary
- `/sc research` - Technical research
- `/sc save` - Save context
- `/sc select-tool` - Tool selection
- `/sc spawn` - Spawn subtasks
- `/sc spec-panel` - Spec panel
- `/sc task` - Task management
- `/sc test` - Test execution
- `/sc troubleshoot` - Issue troubleshooting
- `/sc workflow` - Workflow management

---

## Agents (16 Agents)

### Research Workflow Agents

| Agent | Model | Max Turns | Role |
|-------|-------|-----------|------|
| literature-reviewer | opus | 25 | Literature search, classification, trend analysis (Zotero MCP) |
| literature-reviewer-obsidian | sonnet | 20 | Filesystem-first literature review from Obsidian |
| research-knowledge-curator-obsidian | sonnet | 15 | Default curator for Obsidian project knowledge base |
| rebuttal-writer | sonnet | 15 | Systematic rebuttal writing with tone optimization |
| paper-miner | sonnet | 20 | Extract writing knowledge from successful papers |

### Development Workflow Agents

| Agent | Model | Max Turns | Role |
|-------|-------|-----------|------|
| architect | sonnet | 15 | System architecture design |
| build-error-resolver | sonnet | 20 | Build error fixing (minimal diffs) |
| bug-analyzer | sonnet | 20 | Deep code execution flow analysis and root cause |
| code-reviewer | sonnet | 15 | Code review |
| dev-planner | sonnet | 15 | Development task planning and breakdown |
| refactor-cleaner | sonnet | 15 | Code refactoring and cleanup |
| tdd-guide | sonnet | 15 | TDD workflow guidance |
| kaggle-miner | sonnet | 20 | Extract engineering practices from Kaggle solutions |

### Design & Content Agents

| Agent | Model | Max Turns | Role |
|-------|-------|-----------|------|
| ui-sketcher | sonnet | 15 | UI blueprint design and interaction specifications |
| story-generator | sonnet | 15 | User story and requirement generation |

---

## Hooks (5 Hooks)

Cross-platform Node.js hooks for automated workflow execution:

| Hook | Trigger | Function |
|------|---------|----------|
| `session-start.js` | Session start | Show Git status, todos, commands, and bound Obsidian project-memory status |
| `skill-forced-eval.js` | Every user input | Minimal skill trigger hint based on keyword matching |
| `session-summary.js` | Session end | Generate work log, detect CLAUDE.md updates, and remind minimum Obsidian write-back for bound repos |
| `stop-summary.js` | Session stop | Quick status check, temp file detection, and bound-repo Obsidian maintenance reminder |
| `security-guard.js` | File operations | Security validation (key detection, dangerous command interception) |

---

## Rules (4 Rules)

Global constraints, always active:

| Rule File | Purpose |
|-----------|---------|
| `coding-style.md` | ML project code standards: 200-400 line files, immutable config, type hints, Factory & Registry patterns |
| `agents.md` | Agent orchestration: auto-invocation timing, parallel execution, multi-perspective analysis |
| `security.md` | Security standards: key management, sensitive file protection, pre-commit security checks |
| `experiment-reproducibility.md` | Experiment reproducibility: random seeds, config recording, environment recording, checkpoint management |
| `context-engineering.md` | Context management: token budgets, summarization strategies, memory layers |
