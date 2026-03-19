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

  <strong>语言</strong>: <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</div>

> 面向学术研究和软件开发的半自动研究助手。支持 [Claude Code](https://github.com/anthropics/claude-code)、[Codex CLI](https://github.com/openai/codex) 和 [OpenCode](https://github.com/opencode-ai/opencode)，覆盖文献管理、编码、实验分析、结果报告、写作与项目知识库维护。

## 最新动态

- **2026-03-18**: **实验结果报告、写作记忆与工作流整理** — 将实验后处理明确拆成两层：`results-analysis` 负责严格统计、真实科研图、`analysis-report` / `stats-appendix` / `figure-catalog`，`results-report` 负责面向决策的实验总结报告与 Obsidian 写回；移除了冗余的 `data-analyst` 入口，把 `/analyze-results` 调整为默认的一键分析 + 成稿命令；同时为 `paper-miner` 引入全局 writing memory 与新的 `/mine-writing-patterns` 命令，并让 `ml-paper-writing` 与 `review-response` 统一读取这份共享记忆；此外还重写了 README 的定位，明确其是以人类决策为中心的半自动研究助手，并更新了项目 logo。
- **2026-03-17**: **Obsidian 项目知识库** — 基于以文件系统为核心的项目知识库工作流，支持项目导入、已绑定仓库自动同步、`Papers / Experiments / Results / Results/Reports / Writing` 路由，且不依赖 MCP。
- **2026-02-26**: **Zotero MCP Web API 模式** — 支持远程 Zotero 访问、DOI/arXiv/URL 导入、集合管理、条目更新，并补充了 Claude Code、Codex CLI、OpenCode 的配置说明。

<details>
<summary>查看历史更新日志</summary>

- **2026-02-25**: **Codex CLI** 支持 — 新增 `codex` 分支，支持 [OpenAI Codex CLI](https://github.com/openai/codex)，包含 config.toml、40 个 skills、14 个 agents 和 sandbox 安全机制
- **2026-02-23**: 新增 `setup.sh` 安装脚本 — 面向已有 `~/.claude` 的带备份增量更新，自动备份 `settings.json`，以追加方式合并 hooks/mcpServers/plugins
- **2026-02-21**: **OpenCode** 支持 — Claude Scholar 现已支持 [OpenCode](https://github.com/opencode-ai/opencode) 作为替代 CLI；切换到 `opencode` 分支获取兼容配置
- **2026-02-20**: 双语配置 — 将 `CLAUDE.md` 翻译为英文以便国际用户阅读；新增 `CLAUDE.zh-CN.md` 作为中文备份；中文用户可通过 `cp CLAUDE.zh-CN.md CLAUDE.md` 切换回中文版
- **2026-02-15**: Zotero MCP 集成 — 新增 `/zotero-review` 和 `/zotero-notes` 命令，更新 `research-ideation` skill 添加 Zotero 集成指南，增强 `literature-reviewer` agent 支持 Zotero MCP 自动论文导入、集合管理、全文阅读和引用导出
- **2026-02-14**: Hooks 优化 — `security-guard` 重构为两层系统（Block + Confirm），`skill-forced-eval` 按 6 类分组并切换为静默扫描模式，`session-start` 限制显示前 5 项，`session-summary` 新增 30 天日志自动清理，`stop-summary` 分别显示新增/修改/删除计数；移除废弃的 shell 脚本（lib/common.sh、lib/platform.sh）
- **2026-02-11**: 大版本更新 — 新增 10 个 skills（research-ideation、results-analysis、citation-verification、review-response、paper-self-review、post-acceptance、daily-coding、frontend-design、ui-ux-pro-max、web-design-reviewer）、7 个 agents、8 个研究工作流命令、2 条新规则（security、experiment-reproducibility）；重构 CLAUDE.md；涉及 89 个文件
- **2026-01-26**: 所有 Hooks 重写为跨平台 Node.js 版本；README 完全重写；扩展 ML 论文写作知识库；合并 PR #1（跨平台支持）
- **2026-01-25**: 项目正式开源，v1.0.0 发布，包含 25 个 skills（architecture-design、bug-detective、git-workflow、kaggle-learner、scientific-writing 等）、2 个 agents（paper-miner、kaggle-miner）、30+ 个命令（含 SuperClaude 命令套件）、5 个 Shell Hooks、2 条规则（coding-style、agents）

</details>

## 快速导航

| 部分 | 作用 |
|---|---|
| [为什么使用 Claude Scholar](#为什么使用-claude-scholar) | 快速理解项目定位和适用场景。 |
| [核心工作流](#核心工作流) | 查看从研究构思到发表的主链路。 |
| [快速开始](#快速开始) | 选择完整、最小或选择性安装方式。 |
| [集成能力](#集成能力) | 了解 Zotero 和 Obsidian 如何接入工作流。 |
| [主要工作流](#主要工作流) | 查看核心研究与开发工作流。 |
| [支撑工作流](#支撑工作流) | 查看支撑主工作流的后台机制。 |
| [文档入口](#文档入口) | 快速跳转到 setup、配置和模板文档。 |
| [引用](#引用) | 在论文、报告或项目文档中引用 Claude Scholar。 |

## 为什么使用 Claude Scholar

Claude Scholar **不是**那种试图替代研究者、追求端到端全自动化科研的系统。

它的核心思想很简单：

> **以人的决策为中心，让助手去加速科研流程，而不是替人做最终判断。**

这意味着 Claude Scholar 更适合承担科研中那些高重复、重结构、但仍需要人来把关的环节，例如文献整理、知识沉淀、实验分析、结果汇报和写作辅助；而真正关键的判断始终应该由研究者自己做出：

- 这个问题值不值得做，
- 哪些文献真正重要，
- 哪些假设值得继续验证，
- 哪些结果足够可信，
- 以及什么应该继续推进、写成论文、投稿，或者及时放弃。

换句话说，Claude Scholar 是一个**以人类决策为中心的半自动研究助手**，而不是一个“全自动科研代理”。

## 核心工作流

- **研究构思**：把模糊主题收敛成具体研究问题、研究空白和初步计划。
- **文献工作流**：通过 Zotero 文献集合检索、导入、组织并阅读论文。
- **论文笔记**：把论文转成结构化阅读笔记和可复用论点。
- **知识库沉淀**：将稳定知识写入 Obsidian，并按 `Papers / Knowledge / Experiments / Results / Results/Reports / Writing` 路由整理。
- **实验推进**：跟踪假设、实验线、运行历史、关键发现和下一步动作。
- **严格分析**：使用 `results-analysis` 生成严谨统计、真实科研图和分析产物。
- **结果报告**：使用 `results-report` 生成完整实验复盘报告，并写回 Obsidian。
- **写作与发表**：把稳定结论延伸到综述、论文、rebuttal、演示文稿、海报和传播材料中。

## 快速开始

### 系统要求

- Git
- （可选）Python + [uv](https://docs.astral.sh/uv/) 用于 Python 开发
- （可选）[Zotero](https://www.zotero.org/) + [Galaxy-Dawn/zotero-mcp](https://github.com/Galaxy-Dawn/zotero-mcp) 用于文献工作流
- （可选）[Obsidian](https://obsidian.md/) 用于项目知识库工作流

### 选项 1：完整安装（推荐）

```bash
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar
bash /tmp/claude-scholar/scripts/setup.sh
```

安装器现在支持**带备份的安全增量更新**：
- 更新仓库托管的 `skills/commands/agents/rules/hooks/scripts/CLAUDE*.md`
- 将被覆盖的文件备份到 `~/.claude/.claude-scholar-backups/<timestamp>/`
- 同时把 `settings.json` 备份为 `settings.json.bak`
- 保留已有的 `env`、模型/provider 配置、API key、permissions，以及当前 `mcpServers` 的现有取值
- 对 hooks 采用追加缺失项的方式，而不是整体替换

以后做增量更新时：

```bash
cd /tmp/claude-scholar
git pull --ff-only
bash scripts/setup.sh
```

### 选项 2：最小化安装

只安装一组较小的研究工作流子集：

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

**安装后**：最小化/手动安装**不会自动合并** `settings.json`；请按需从 `settings.json.template` 复制你需要的 hooks 或 MCP 条目。

### 选项 3：选择性安装

只复制你需要的部分：

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

**安装后**：选择性/手动安装**不会自动合并** `settings.json`；请按需从 `settings.json.template` 复制你需要的 hooks 或 MCP 条目。

## 平台支持

Claude Scholar 目前面向以下 CLI 工作流：

- **Claude Code** — 主安装目标
- **Codex CLI** — 支持对应工作流与文档
- **OpenCode** — 作为替代 CLI 支持

顶层目标一致：研究、编码、实验、报告、写作、项目知识库维护。

## 集成能力

### Zotero

适合这些场景：
- 通过 DOI / arXiv / URL 导入论文
- 按 collection 批量阅读论文
- 通过 Zotero MCP 读取全文
- 生成详细论文笔记与文献综合分析

详见 [MCP_SETUP.zh-CN.md](./MCP_SETUP.zh-CN.md)。

### Obsidian

适合这些场景：
- 维护以文件系统为核心的项目知识库
- 管理 `Papers/`
- 管理 `Experiments/`
- 管理 `Results/`
- 管理 `Results/Reports/`
- 管理 `Writing/` 与 `Daily/`

详见 [OBSIDIAN_SETUP.zh-CN.md](./OBSIDIAN_SETUP.zh-CN.md)。

## 主要工作流

完整学术研究生命周期 —— 从研究构思到发表的 7 个阶段。

### 1. 研究构思（Zotero 集成）

从想法生成到文献管理的一体化研究启动流程。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `research-ideation` | 把模糊研究主题收敛成结构化问题、研究空白分析和初始研究计划。 |
| Agent | `literature-reviewer` | 搜索、分类并综合论文，形成可执行的文献图景。 |
| Command | `/research-init` | 从文献检索、Zotero 组织到研究提案草稿，一键启动新研究主题。 |
| Command | `/zotero-review` | 对已有 Zotero collection 做结构化文献综述与比较。 |
| Command | `/zotero-notes` | 批量阅读 Zotero collection，并生成结构化论文阅读笔记。 |

**工作方式**
- **5W1H 头脑风暴**：把模糊主题收敛成结构化问题。
- **文献检索与导入**：搜索论文、提取 DOI/arXiv/URL、导入 Zotero，并组织到主题文献集合。
- **PDF 与全文**：能挂 PDF 就挂 PDF，能读全文就读全文，必要时回退到摘要分析。
- **研究空白分析**：识别 literature / methodology / application / interdisciplinary / temporal 等不同类型的研究空白。
- **研究问题与规划**：把文献综述进一步转成明确研究问题、初始假设和下一步计划。

**典型产出**
- 文献综述笔记
- 结构化 Zotero 文献集合
- 研究计划 / 方向草稿

### 2. ML 项目开发

面向实验代码的可维护 ML 项目开发工作流。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `architecture-design` | 在新增可注册组件或模块时设计可维护的 ML 项目结构。 |
| Skill | `git-workflow` | 约束分支规范、commit 规范和更安全的协作流程。 |
| Skill | `bug-detective` | 系统化排查 stack trace、shell 报错和代码路径问题。 |
| Agent | `code-reviewer` | 审查改动代码的正确性、可维护性和实现质量。 |
| Agent | `dev-planner` | 把复杂工程任务拆成可执行的实现步骤。 |
| Command | `/plan` | 在编码前创建或细化实现计划。 |
| Command | `/commit` | 为当前改动生成符合规范的 commit。 |
| Command | `/code-review` | 对当前代码改动执行一次聚焦审查。 |
| Command | `/tdd` | 以小步、测试驱动的方式推进功能实现。 |

**工作方式**
- **结构设计**：在合适场景下使用 Factory / Registry 模式组织 ML 组件。
- **代码质量**：保持文件规模、类型提示与配置驱动设计。
- **问题排查**：系统化处理 stack trace、shell 报错和代码路径问题。
- **Git 纪律**：维持分支策略、commit 规范和更安全的 merge/rebase 流程。

### 3. 实验分析

严格实验分析工作流：统计、科研图、分析产物与实验后报告。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `results-analysis` | 生成由严格统计、真实科研图和分析附录组成的严格分析产物包。 |
| Skill | `results-report` | 把分析产物组织成完整实验总结报告，明确结论、限制和下一步动作。 |
| Command | `/analyze-results` | 一键执行完整实验后工作流：先严格分析，再生成最终实验报告。 |

**工作方式**
- **数据处理**：读取实验日志、metrics 文件和结果目录。
- **统计检验**：在合适前提下执行 t-test / ANOVA / Wilcoxon 等严格统计检验。
- **科研可视化**：生成真实科研图和解释线索，而不是只给模糊的绘图建议。
- **消融与比较**：分析组件贡献、性能 tradeoff 和稳定性。
- **实验后报告**：把分析产物包转成完整实验后总结报告，包含结论、限制和下一步动作。

**典型产出**
- `analysis-report.md`
- `stats-appendix.md`
- `figure-catalog.md`
- `figures/`
- 写入 Obsidian `Results/Reports/` 的实验总结报告

### 4. 论文写作

从结构准备到草稿迭代的系统化论文写作工作流。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `ml-paper-writing` | 基于 repo、实验结果和文献上下文撰写投稿导向的 ML/AI 论文。 |
| Skill | `citation-verification` | 检查参考文献、元数据和 claim-citation 对齐，避免引用错误。 |
| Skill | `writing-anti-ai` | 减少机械化表述，提升清晰度、节奏和更自然的学术语气。 |
| Skill | `latex-conference-template-organizer` | 把混乱的会议模板整理成 Overleaf-ready 写作结构。 |
| Agent | `paper-miner` | 从高质量论文中提炼可复用的写作模式、结构和投稿经验。 |
| Command | `/mine-writing-patterns` | 读取论文并把可复用写作知识合并进全局 paper-miner writing memory。 |

**工作方式**
- **模板准备**：把会议模板清理成 Overleaf-ready 结构。
- **引用核验**：检查参考文献、元数据和 claim-citation 对齐。
- **系统化写作**：基于 repo、实验结果和文献上下文逐节写作。
- **风格打磨**：减少 AI 痕迹，改善节奏、清晰度和学术语气。

### 5. 论文自审

投稿前的质量保障工作流。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `paper-self-review` | 在投稿前系统检查结构、逻辑、引用、图表和合规性。 |

**工作方式**
- **结构检查**：检查逻辑流、章节平衡和叙事连贯性。
- **逻辑校验**：检查 claim-evidence 对齐、假设清晰度和论证一致性。
- **引用审计**：检查引用准确性与完整性。
- **图表质量**：检查 caption 完整性、可读性和可访问性。
- **合规性检查**：检查页数限制、格式和披露要求。

### 6. 投稿与 Rebuttal

投稿准备和审稿回复工作流。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `review-response` | 把审稿意见组织成基于证据的 rebuttal 工作流。 |
| Agent | `rebuttal-writer` | 起草专业、礼貌且结构清晰的 rebuttal 文本。 |
| Command | `/rebuttal` | 基于审稿意见和现有证据生成完整 rebuttal 草稿。 |

**工作方式**
- **投稿前检查**：检查会议/期刊格式、匿名化和清单要求。
- **审稿意见分析**：把审稿意见分类成可执行的问题。
- **回复策略**：决定是 accept、defend、clarify 还是补实验。
- **Rebuttal 写作**：生成结构化、基于证据、语气专业的回复文档。

### 7. 录用后处理

论文录用后的会议准备与研究传播工作流。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `post-acceptance` | 支持论文录用后的报告、海报和传播材料准备。 |
| Command | `/presentation` | 生成会议报告的结构和讲解指导。 |
| Command | `/poster` | 整理论文内容并生成海报版式与内容指导。 |
| Command | `/promote` | 起草面向外部传播的摘要、帖子或 thread 内容。 |

**工作方式**
- **报告准备**：准备报告结构和演示文稿指导。
- **海报整理**：整理海报内容层级和版式。
- **传播内容**：生成社交媒体、博客或简明研究摘要。

## 支撑工作流

这些工作流运行在主工作流背后，用来增强整体使用体验。

### Obsidian 项目知识库

把 Obsidian 当作稳定科研知识的沉淀中心，而不是随手堆放笔记的地方。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `obsidian-project-memory` | 维护项目级 Obsidian 知识库，并决定哪些稳定知识需要写回。 |
| Skill | `obsidian-project-bootstrap` | 为新项目或已有科研项目初始化对应的 Obsidian 知识库结构。 |
| Skill | `obsidian-research-log` | 将每日研究进展、计划、想法和 TODO 写入知识库。 |
| Skill | `obsidian-experiment-log` | 在 Obsidian 中记录实验设置、运行过程、结果和后续动作。 |
| Command | `/obsidian-ingest` | 把新的 Markdown 文件或目录整理并纳入正确的知识库位置。 |
| Command | `/obsidian-note` | 对单个 note 执行查找、重命名、归档或删除等生命周期操作。 |
| Command | `/obsidian-views` | 生成或刷新可选的 Obsidian 视图文件，例如 `.base`。 |

**工作方式**
- 将已有 repo 绑定到 Obsidian vault
- 把稳定知识路由进 `Papers / Experiments / Results / Results/Reports / Writing`
- 以保守方式维护 `Daily/` 和项目记忆
- 把新的 Markdown 文件分类并合并进正确的规范笔记
- 按需生成额外视图和 canvas

### 自动化约束工作流

跨平台 hooks 自动执行日常检查与提醒。

**Hook 列表**
- `skill-forced-eval.js`
- `session-start.js`
- `session-summary.js`
- `stop-summary.js`
- `security-guard.js`

**工作方式**
- **用户提问前**：评估当前 prompt 应该触发哪些 skills，并补充相关 workflow 提示。
- **会话开始时**：显示 Git 状态、可用命令和项目记忆上下文。
- **会话结束或停止时**：总结工作内容，并提醒最小维护动作。
- **安全防护**：拦截灾难性命令，并对危险但合理的操作要求确认。

### 知识提炼工作流

专门的 agents 可持续提炼论文和竞赛中的可复用知识。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Agent | `paper-miner` | 从高质量论文中提炼可复用的写作知识、结构模式和投稿经验。 |
| Agent | `kaggle-miner` | 从优秀 Kaggle 工作流中提炼工程实践和解决方案模式。 |

**工作方式**
- 从论文中提炼写作模式、会议要求和 rebuttal 策略
- 从 Kaggle 工作流中提炼工程模式和解决方案结构
- 再把这些知识回流进 skills 与 references 中。

### 技能进化系统

Claude Scholar 也内置了自我改进的 skill 工作流。

| 类型 | 名字 | 一句话解释 |
|---|---|---|
| Skill | `skill-development` | 创建具备清晰触发条件、结构和渐进展开方式的新技能模块。 |
| Skill | `skill-quality-reviewer` | 从内容质量、组织方式、表达风格和结构完整性审查 skill。 |
| Skill | `skill-improver` | 根据结构化改进计划持续优化已有 skills。 |

**工作方式**
- 创建带有清晰触发描述的新 skill
- 按多个质量维度审查 skill
- 合并改进建议并持续迭代

## 文档入口

- [MCP_SETUP.zh-CN.md](./MCP_SETUP.zh-CN.md) — Zotero / 浏览器 MCP 配置
- [OBSIDIAN_SETUP.zh-CN.md](./OBSIDIAN_SETUP.zh-CN.md) — Obsidian 项目知识库工作流
- [CLAUDE.md](./CLAUDE.md) — 完整本地配置、技能列表与工作流说明
- [CLAUDE.zh-CN.md](./CLAUDE.zh-CN.md) — 中文版主配置文档
- [settings.json.template](./settings.json.template) — hooks / plugins / MCP 的可选模板

## 项目规则

Claude Scholar 包含以下方面的项目规则：
- 代码风格
- agent 编排
- 安全约束
- 实验可复现性

这些规则体现在仓库附带的 rules 以及 `CLAUDE.md` 中。

## 贡献

欢迎提交 issue、PR 和工作流改进建议。

如果你想改 installer、Zotero 工作流或 Obsidian 路由，建议在提案中说明：
- 用户场景
- 当前限制
- 预期行为
- 兼容性影响

## 许可证

MIT 许可证。

## 引用

如果 Claude Scholar 对你的研究或工程工作流有帮助，你可以按下面方式引用：

```bibtex
@misc{claude_scholar_2026,
  title        = {Claude Scholar: Semi-automated research assistant for academic research and software development},
  author       = {Gaorui Zhang},
  year         = {2026},
  howpublished = {\url{https://github.com/Galaxy-Dawn/claude-scholar}},
  note         = {GitHub repository}
}
```

## 致谢

使用 Claude Code CLI 构建，并由开源社区增强。

### 参考资料

本项目受到社区优秀工作的启发和构建：

- **[everything-claude-code](https://github.com/anthropics/everything-claude-code)** - Claude Code CLI 的综合资源
- **[AI-research-SKILLs](https://github.com/zechenzhangAGI/AI-research-SKILLs)** - 研究导向的技能和配置

这些项目为 Claude Scholar 的研究导向功能提供了宝贵的见解和基础。

---

**面向数据科学、AI 研究和学术写作。**

仓库：[https://github.com/Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar)
