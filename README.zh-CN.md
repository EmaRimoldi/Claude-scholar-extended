<div align="center">
  <img src="LOGO.png" alt="Claude Scholar Logo" width="100%"/>

  <p>
    <a href="https://github.com/Galaxy-Dawn/claude-scholar/stargazers"><img src="https://img.shields.io/github/stars/Galaxy-Dawn/claude-scholar?style=flat-square&color=yellow" alt="Stars"/></a>
    <a href="https://github.com/Galaxy-Dawn/claude-scholar/network/members"><img src="https://img.shields.io/github/forks/Galaxy-Dawn/claude-scholar?style=flat-square" alt="Forks"/></a>
    <img src="https://img.shields.io/github/last-commit/Galaxy-Dawn/claude-scholar?style=flat-square" alt="Last Commit"/>
    <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"/>
    <img src="https://img.shields.io/badge/Claude_Code-Compatible-blueviolet?style=flat-square" alt="Claude Code"/>
  </p>

  <strong>语言</strong>: <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</div>

> 面向学术研究和软件开发的个人 Claude Code / **OpenCode** 配置仓库 — 覆盖从构思到发表的完整研究生命周期。

## News

- **2026-02-26**: **Zotero MCP Web API 模式** — 支持远程访问，可通过 DOI/arXiv ID/URL 导入论文，进行集合管理、条目更新，安全删除；附 [Claude Code](./MCP_SETUP.zh-CN.md)、[Codex CLI](./MCP_SETUP.zh-CN.md#codex-cli)、[OpenCode](./MCP_SETUP.zh-CN.md#opencode) 三平台配置指南
- **2026-02-25**: **Codex CLI** 支持 — 新增 `codex` 分支，支持 [OpenAI Codex CLI](https://github.com/openai/codex)，包含 config.toml、40 个 skills、14 个 agents 和 sandbox 安全机制
- **2026-02-23**: 新增 `setup.sh` 安装脚本 — 安全合并到已有 `~/.claude`，自动备份 `settings.json`，智能合并 hooks/mcpServers/plugins
- **2026-02-21**: **OpenCode** 支持 — Claude Scholar 现已支持 [OpenCode](https://github.com/opencode-ai/opencode) 作为替代 CLI；切换到 `opencode` 分支获取兼容配置

<details>
<summary>查看历史更新日志</summary>

- **2026-02-20**: 双语配置 — 将 `CLAUDE.md` 翻译为英文以便国际用户阅读；新增 `CLAUDE.zh-CN.md` 作为中文备份；中文用户可通过 `cp CLAUDE.zh-CN.md CLAUDE.md` 切换回中文版
- **2026-02-15**: Zotero MCP 集成 — 新增 `/zotero-review` 和 `/zotero-notes` 命令，更新 `research-ideation` skill 添加 Zotero 集成指南，增强 `literature-reviewer` agent 支持 Zotero MCP 自动论文导入、集合管理、全文阅读和引用导出
- **2026-02-14**: Hooks 优化 — `security-guard` 重构为两层系统（Block + Confirm），`skill-forced-eval` 按 6 类分组并切换为静默扫描模式，`session-start` 限制显示前 5 项，`session-summary` 新增 30 天日志自动清理，`stop-summary` 分别显示新增/修改/删除计数；移除废弃的 shell 脚本（lib/common.sh、lib/platform.sh）
- **2026-02-11**: 大版本更新，新增 10 个 skills（research-ideation、results-analysis、citation-verification、review-response、paper-self-review、post-acceptance、daily-coding、frontend-design、ui-ux-pro-max、web-design-reviewer）、7 个 agents、8 个研究工作流命令、2 条新规则（security、experiment-reproducibility）；重构 CLAUDE.md；涉及 89 个文件
- **2026-01-26**: 所有 Hooks 重写为跨平台 Node.js 版本；README 完全重写；扩展 ML 论文写作知识库；合并 PR #1（跨平台支持）
- **2026-01-25**: 项目正式开源，v1.0.0 发布，包含 25 个 skills（architecture-design、bug-detective、git-workflow、kaggle-learner、scientific-writing 等）、2 个 agents（paper-miner、kaggle-miner）、30+ 个命令（含 SuperClaude 命令套件）、5 个 Shell Hooks、2 条规则（coding-style、agents）

</details>

## 简介

Claude Scholar 是一个面向 Claude Code CLI 的个人配置系统，提供丰富的技能、命令、代理和钩子，针对以下场景优化：
- **学术研究** - 完整的研究生命周期：想法生成 → 实验 → 结果分析 → 论文写作 → 审稿回复 → 会议准备
- **软件开发** - Git 工作流、代码审查、测试驱动开发、ML 项目架构
- **插件开发** - Skill、Command、Agent、Hook 开发指南与质量评估
- **项目管理** - 规划文档、代码规范、跨平台钩子驱动的自动化工作流

## 快速导航

| 主题 | 说明 |
|------|------|
| 🚀 [快速开始](#快速开始) | 快速上手指南 |
| 📚 [核心工作流](#核心工作流) | 论文写作、代码组织、技能进化 |
| 🛠️ [功能亮点](#功能亮点) | 技能、命令、代理概览 |
| 📖 [安装指南](#安装选项) | 完整、最小化或选择性安装 |
| 📦 [MCP 配置](#mcp-服务配置) | Zotero MCP 研究工作流集成 |
| 🔧 [项目规则](#项目规则) | 代码风格和代理编排 |

## 核心工作流

### 主要工作流

完整的学术研究生命周期 - 从想法到发表的 7 个阶段。

#### 1. 研究构思（Zotero 集成）

从想法生成到文献管理的端到端研究启动：

**工具**: `research-ideation` skill + `literature-reviewer` agent + Zotero MCP

**流程**:
- **5W1H 头脑风暴**: What, Why, Who, When, Where, How → 结构化思维框架
- **文献搜索与导入**: WebSearch 搜索论文 → 提取 DOI → 通过 `add_items_by_doi` 自动导入 Zotero → 分类到主题子集合（Core Papers、Methods、Applications、Baselines、To-Read）
- **PDF 与全文分析**: `find_and_attach_pdfs` 批量附加开放获取 PDF → `get_item_fulltext` 读取论文全文进行深度分析（回退：摘要 + 领域知识）
- **Gap 分析**: 5 种类型（文献、方法论、应用、跨学科、时间）→ 识别 2-3 个具体研究机会
- **研究问题**: SMART 原则 → 制定具体、可衡量的问题
- **方法选择与规划**: 评估方法适用性 → 时间线、里程碑、风险评估

**Zotero 集合结构**:
```
📁 Research-{Topic}-{YYYY-MM}
  ├── 📁 Core Papers
  ├── 📁 Methods
  ├── 📁 Applications
  ├── 📁 Baselines
  └── 📁 To-Read
```

**输出**: `literature-review.md` + `research-proposal.md` + `references.bib`（从 Zotero 导出）+ 带 PDF 的有序 Zotero 集合

**命令**:
- `/research-init "topic"` → 完整工作流：创建 Zotero 集合 → 搜索导入论文 → 全文分析 → Gap 分析 → 生成综述与提案
- `/zotero-review "collection"` → 分析已有 Zotero 集合 → 生成带对比矩阵的文献综述
- `/zotero-notes "collection"` → 批量阅读论文 → 生成结构化阅读笔记（summary/detailed/comparison 三种格式）

#### 2. ML 项目开发

可维护的 ML 项目结构，用于实验代码：

**工具**: `architecture-design` skill + `code-reviewer` agent + `git-workflow` skill

**流程**:
- **结构**: Factory & Registry 模式 → 配置驱动模型（仅 `cfg` 参数）→ 由 `rules/coding-style.md` 强制执行
- **代码风格**: 200-400 行文件 → 需要类型提示 → 配置使用 `@dataclass(frozen=True)` → 最多 3 层嵌套
- **调试** (`bug-detective`): Python/Bash/JS 的错误模式匹配 → 堆栈跟踪分析 → 反模式识别
- **Git**: Conventional Commits (`feat/scope: message`) → 分支策略（master/develop/feature）→ 使用 `--no-ff` 合并

**命令**: `/plan`, `/commit`, `/code-review`, `/tdd`

#### 3. 实验分析

实验结果的统计分析和可视化：

**工具**: `results-analysis` skill + `data-analyst` agent

**流程**:
- **数据处理**: 自动化清理和预处理实验日志
- **统计检验**: t-test, ANOVA, Wilcoxon signed-rank → 验证显著性
- **可视化**: matplotlib/seaborn 集成 → 发表级图表（折线图、柱状图、热图）
- **消融实验**: 系统化组件分析 → 理解每个部分的贡献

**命令**: `/analyze-results <experiment_dir>` → 生成带有图表和统计数据的分析报告

#### 4. 论文写作

从模板到最终草稿的系统化论文写作：

**工具**: `ml-paper-writing` skill + `paper-miner` agent + `latex-conference-template-organizer` skill

**流程**:
- **模板准备**: 下载会议 .zip → 提取主文件 → 删除示例内容 → 输出适合 Overleaf 的干净结构
- **引文验证** (`citation-verification`): 多层验证（格式 → API → 信息 → 内容）→ 防止幻觉引用
- **系统化写作**: 叙事框架 → 5 句式摘要公式 → 分节起草与反馈循环
- **去 AI 化处理** (`writing-anti-ai`): 移除夸大象征、宣传语言、模糊归因 → 添加人性化声音和节奏 → 双语支持（中英文）

**会议**: NeurIPS, ICML, ICLR, ACL, AAAI, COLM, Nature, Science, Cell, PNAS

#### 5. 论文自审

提交前的质量保证：

**工具**: `paper-self-review` skill

**流程**:
- **结构检查**: 逻辑流畅性、章节平衡、叙事连贯性
- **逻辑验证**: 论证合理性、主张-证据对齐、假设清晰性
- **引文审计**: 引用准确性、适当归属、引文完整性
- **图表质量**: 视觉清晰度、标题完整性、色彩无障碍性
- **写作润色**: 语法、清晰度、简洁性、学术语气
- **合规性**: 页数限制、格式要求、伦理披露

**6 项检查清单** → 系统化质量评估

#### 6. 论文提交与 Rebuttal

论文提交和审稿意见回复：

**工具**: `review-response` skill + `rebuttal-writer` agent

**提交流程**:
- **提交前检查**: 会议特定检查清单（NeurIPS 16 项、ICML 更广泛影响、ICLR LLM 披露）
- **格式检查**: 页数限制、匿名化、补充材料
- **最终审查**: 校对、检查引用、验证图表

**Rebuttal 流程**:
- **审稿意见分析**: 解析并分类评论（主要/次要/错字/误解）
- **回复策略**: 接受/辩护/澄清/实验 → 针对每种评论类型的定制方法
- **Rebuttal 写作**: 结构化回复，包含证据和推理
- **语气管理**: 专业、尊重、基于证据的语言

**命令**: `/rebuttal <review_file>` → 生成完整的 rebuttal 文档和实验计划

#### 7. 录用后处理

会议准备和研究推广：

**工具**: `post-acceptance` skill

**流程**:
- **演讲**: 幻灯片创建指导（15/20/30 分钟格式）→ 视觉设计原则 → 叙事结构
- **海报**: 学术海报模板（A0/A1 尺寸）→ 布局优化 → 视觉层次
- **推广**: 社交媒体内容（Twitter/X, LinkedIn）→ 博客文章 → 新闻稿 → 研究摘要

**命令**: `/presentation`, `/poster`, `/promote` → 自动化内容生成

**覆盖范围**: 90% 的学术研究生命周期（从想法到发表）

### 支撑工作流

这些工作流在后台运行，增强主要工作流。

#### 自动化执行工作流

跨平台钩子（Node.js）自动化工作流执行：

```
会话开始 → 技能评估 → 会话结束 → 会话停止
```

- **skill-forced-eval** (`skill-forced-eval.js`): 在每次用户提示之前 → 将所有可用技能（本地 + 插件）按 6 类分组 → 静默扫描模式，仅输出匹配的技能 → 要求实现前激活 → 确保不遗漏相关技能
- **session-start** (`session-start.js`): 会话开始时 → 显示 Git 状态、待办事项、可用命令（前 5 项，折叠显示）、包管理器 → 一目了然地展示项目上下文
- **session-summary** (`session-summary.js`): 会话结束时 → 生成全面的工作日志 → 总结所做的所有更改 → 提供下一步的智能建议 → 自动清理 30 天前的日志
- **stop-summary** (`stop-summary.js`): 会话停止时 → 快速状态检查，分别显示新增/修改/删除计数 → 按文件夹分组临时文件（每组前 3 个）→ 显示可操作的清理建议
- **security-guard** (`security-guard.js`): 两层安全系统 — **Block 层**: 立即拒绝灾难性命令（rm -rf /、dd、mkfs、系统目录）；**Confirm 层**: 注入 systemMessage 强制模型在执行危险但合法的操作前询问用户（git push --force、git reset --hard、chmod 777、SQL DROP/DELETE/TRUNCATE、敏感文件写入）

**跨平台**: 所有钩子使用 Node.js（非 shell 脚本），确保 Windows/macOS/Linux 兼容性。

#### 知识提取工作流

两个专门的挖掘代理持续提取知识以改进技能：

- **paper-miner** (agent): 分析研究论文（PDF/DOCX/arXiv 链接）→ 提取写作模式、结构见解、会议要求、审稿意见回复策略 → 使用分类条目更新 `ml-paper-writing/references/knowledge/`（structure.md、writing-techniques.md、submission-guides.md、review-response.md）
- **kaggle-miner** (agent): 研究获胜的 Kaggle 竞赛解决方案 → 提取竞赛简介、前排方案详细技术分析、代码模板、最佳实践 → 更新 `kaggle-learner` skill 的知识库（`references/knowledge/[domain]/` 目录，按 NLP/CV/Time Series/Tabular/Multimodal 分类）

**知识反馈循环**: 每篇分析的论文或解决方案都会丰富知识库，创建一个随您研究进化的自我改进系统。

#### 技能进化系统

维护和改进技能的 3 步持续改进循环：

```
skill-development → skill-quality-reviewer → skill-improver
```

1. **开发** (`skill-development`): 创建具有正确 YAML frontmatter 的技能 → 清晰的描述和触发短语 → 渐进式披露（精简的 SKILL.md，详细信息在 `references/`）
2. **审查** (`skill-quality-reviewer`): 4 维质量评估 → 描述质量（25%）、内容组织（30%）、写作风格（20%）、结构完整性（25%）→ 生成优先修复的改进计划
3. **改进** (`skill-improver`): 合并建议更改 → 更新文档 → 根据反馈迭代 → 自动读取并应用改进计划

## 文件结构

<details>
<summary>查看文件结构</summary>

```
claude-scholar/
├── hooks/               # 跨平台 JavaScript 钩子（自动化执行）
│   ├── hook-common.js           # 共享工具（git diff、变更分析）
│   ├── session-start.js         # 会话开始 - Git 状态、待办事项、前 5 个命令
│   ├── skill-forced-eval.js     # 静默扫描，6 类技能分组
│   ├── session-summary.js       # 会话结束 - 工作日志、30 天日志自动清理
│   ├── stop-summary.js          # 会话停止 - 新增/修改/删除计数、分组临时文件
│   └── security-guard.js        # 两层安全：Block（灾难性）+ Confirm（危险操作）
│
├── skills/              # 32 个专业技能（领域知识 + 工作流）
│   ├── ml-paper-writing/        # 完整论文写作：NeurIPS, ICML, ICLR, ACL, AAAI, COLM
│   │   └── references/
│   │       └── knowledge/        # 从成功论文中提取的模式
│   │       ├── structure.md           # 论文组织模式
│   │       ├── writing-techniques.md  # 句子模板、过渡
│   │       ├── submission-guides.md   # 会议要求（页数限制等）
│   │       └── review-response.md     # 审稿意见回复策略
│   │
│   ├── research-ideation/        # 研究启动：5W1H、文献综述、Gap 分析
│   │   └── references/
│   │       ├── 5w1h-framework.md           # 系统化思维工具
│   │       ├── gap-analysis-guide.md       # 5 种研究 Gap 类型
│   │       ├── literature-search-strategies.md
│   │       ├── research-question-formulation.md
│   │       ├── method-selection-guide.md
│   │       └── research-planning.md
│   │
│   ├── results-analysis/         # 实验分析：统计、可视化、消融
│   │   └── references/
│   │       ├── statistical-methods.md      # t-test, ANOVA, Wilcoxon
│   │       ├── visualization-best-practices.md  # matplotlib/seaborn
│   │       ├── results-writing-guide.md    # 结果章节写作
│   │       └── common-pitfalls.md          # 常见分析错误
│   │
│   ├── review-response/          # 系统化 rebuttal 写作
│   │   └── references/
│   │       ├── review-classification.md    # 主要/次要/错字/误解
│   │       ├── response-strategies.md      # 接受/辩护/澄清/实验
│   │       ├── rebuttal-templates.md       # 结构化回复模板
│   │       └── tone-guidelines.md          # 专业语言
│   │
│   ├── paper-self-review/        # 6 项质量检查清单
│   ├── post-acceptance/          # 会议准备
│   │   └── references/
│   │       ├── presentation-templates/     # 幻灯片创建（15/20/30 分钟）
│   │       ├── poster-templates/           # 学术海报设计
│   │       ├── promotion-examples/         # 社交媒体内容
│   │       └── design-guidelines.md        # 视觉设计原则
│   │
│   ├── citation-verification/    # 多层引文验证
│   ├── writing-anti-ai/         # 移除 AI 模式：象征主义、宣传语言
│   │   └── references/
│   │       ├── patterns-english.md    # 要移除的英文 AI 模式
│   │       └── patterns-chinese.md     # 要移除的中文 AI 模式
│   │
│   ├── architecture-design/     # ML 项目模式：Factory、Registry、配置驱动
│   ├── git-workflow/            # Git 纪律：Conventional Commits、分支
│   ├── bug-detective/           # 调试：Python、Bash、JS/TS 错误模式
│   ├── code-review-excellence/  # 代码审查：安全性、性能、可维护性
│   ├── skill-development/       # 技能创建：YAML、渐进式披露
│   ├── skill-quality-reviewer/  # 技能评估：4 维评分
│   ├── skill-improver/          # 技能进化：合并改进
│   ├── kaggle-learner/          # 从 Kaggle 获胜解决方案中学习
│   ├── doc-coauthoring/         # 文档协作工作流
│   ├── latex-conference-template-organizer  # Overleaf 模板清理
│   └── ... （10+ 更多技能）
│
├── commands/            # 50+ 斜杠命令（快速工作流执行）
│   ├── research-init.md         # 启动研究启动工作流
│   ├── zotero-review.md         # 从 Zotero 读取论文，生成文献综述
│   ├── zotero-notes.md          # 批量阅读 Zotero 论文，生成阅读笔记
│   ├── analyze-results.md       # 分析实验结果
│   ├── rebuttal.md              # 生成系统化 rebuttal 文档
│   ├── presentation.md          # 创建会议演讲大纲
│   ├── poster.md                # 生成学术海报设计方案
│   ├── promote.md               # 生成推广内容
│   ├── plan.md                  # 带代理委托的实施方案规划
│   ├── commit.md                # Conventional Commits：feat/fix/docs/refactor
│   ├── code-review.md           # 质量和安全审查工作流
│   ├── tdd.md                   # 测试驱动开发：Red-Green-Refactor
│   ├── build-fix.md             # 自动修复构建错误
│   ├── verify.md                # 运行验证循环
│   ├── checkpoint.md            # 保存验证状态
│   ├── refactor-clean.md        # 移除死代码
│   ├── learn.md                 # 从代码中提取模式
│   ├── update-github.md         # 提交并推送到 GitHub
│   ├── update-readme.md         # 更新 README 文档
│   ├── update-memory.md         # 检查并更新 CLAUDE.md 记忆
│   ├── create_project.md        # 从模板创建新项目
│   ├── setup-pm.md              # 配置包管理器（uv/pnpm）
│   └── sc/                      # SuperClaude 命令套件（30 个命令）
│       ├── sc-agent.md           # 代理管理
│       ├── sc-estimate.md       # 开发时间估算
│       ├── sc-improve.md         # 代码改进
│       └── ...
│
├── agents/              # 14 个专业代理（专注任务委托）
│   ├── literature-reviewer.md   # 文献搜索和趋势分析
│   ├── data-analyst.md          # 自动化数据分析和可视化
│   ├── rebuttal-writer.md       # 系统化 rebuttal 写作
│   ├── paper-miner.md           # 提取论文知识：结构、技巧
│   ├── architect.md             # 系统设计：架构决策
│   ├── code-reviewer.md         # 审查代码：质量、安全、最佳实践
│   ├── tdd-guide.md             # 指导 TDD：测试优先开发
│   ├── kaggle-miner.md          # 从 Kaggle 提取工程实践
│   ├── build-error-resolver.md  # 修复构建错误：分析和解决
│   ├── refactor-cleaner.md      # 移除死代码：检测和清理
│   ├── bug-analyzer.md          # 深度代码执行流分析和根因调查
│   ├── dev-planner.md           # 实施规划和任务拆解
│   ├── ui-sketcher.md           # UI 蓝图设计和交互规范
│   └── story-generator.md       # 用户故事和需求生成
│
├── rules/               # 全局指导原则（始终遵循的约束）
│   ├── coding-style.md          # ML 项目标准：文件大小、不可变性、类型
│   ├── agents.md                # 代理编排：何时委托、并行执行
│   ├── security.md              # 密钥管理、敏感文件保护
│   └── experiment-reproducibility.md  # 随机种子、配置记录、检查点
│
├── CLAUDE.md            # 全局配置：项目概述、偏好设置、规则
│
└── README.md            # 本文件 - 概述、安装、功能
```

</details>

## 功能亮点

### 技能（32 个）

**网页设计：**
- `frontend-design` - 创建独特、生产级的前端界面
- `ui-ux-pro-max` - UI/UX 设计智能（50+ 风格、97 色板、9 技术栈）
- `web-design-reviewer` - 视觉检查和设计问题修复

**写作与学术：**
- `ml-paper-writing` - 顶级会议/期刊的完整论文写作指导
- `writing-anti-ai` - 移除 AI 写作模式（双语支持）
- `doc-coauthoring` - 结构化文档协作工作流
- `latex-conference-template-organizer` - LaTeX 模板管理
- `daily-paper-generator` - 自动化每日论文生成，用于研究追踪

**研究工作流：**
- `research-ideation` - 研究启动：5W1H 头脑风暴、文献综述、Gap 分析
- `results-analysis` - 实验分析：统计检验、可视化、消融实验
- `review-response` - 系统化 rebuttal 写作，语气管理
- `paper-self-review` - 6 项质量检查清单
- `post-acceptance` - 会议准备：演讲、海报、推广
- `citation-verification` - 多层引文验证，防止幻觉引用

**开发：**
- `daily-coding` - 日常编码检查清单（极简模式，自动触发）
- `git-workflow` - Git 最佳实践（Conventional Commits、分支）
- `code-review-excellence` - 代码审查指南
- `bug-detective` - Python、Bash、JS/TS 调试
- `architecture-design` - ML 项目设计模式
- `verification-loop` - 测试和验证

**插件开发：**
- `skill-development` - 技能创建指南
- `skill-improver` - 技能改进工具
- `skill-quality-reviewer` - 质量评估
- `command-development` - 斜杠命令创建
- `agent-identifier` - 代理配置
- `hook-development` - 钩子开发指南
- `mcp-integration` - MCP 服务器集成

**工具：**
- `uv-package-manager` - 现代 Python 包管理
- `planning-with-files` - 基于 Markdown 的规划
- `webapp-testing` - 本地 Web 应用测试
- `kaggle-learner` - 从 Kaggle 解决方案中学习

### 命令（50+）

**研究命令：**
| 命令 | 用途 |
|------|------|
| `/research-init` | 启动研究启动工作流（5W1H、文献综述、Gap 分析） |
| `/zotero-review` | 从 Zotero 集合读取论文，生成结构化文献综述 |
| `/zotero-notes` | 批量阅读 Zotero 论文，生成结构化阅读笔记 |
| `/analyze-results` | 分析实验结果（统计检验、可视化、消融实验） |
| `/rebuttal` | 从审稿意见生成系统化 rebuttal 文档 |
| `/presentation` | 创建会议演讲大纲 |
| `/poster` | 生成学术海报设计方案 |
| `/promote` | 生成推广内容（Twitter、LinkedIn、博客） |

**开发命令：**
| 命令 | 用途 |
|------|------|
| `/plan` | 创建实施计划 |
| `/commit` | 使用 Conventional Commits 提交 |
| `/update-github` | 提交并推送到 GitHub |
| `/update-readme` | 更新 README 文档 |
| `/update-memory` | 检查并更新 CLAUDE.md 记忆 |
| `/code-review` | 执行代码审查 |
| `/tdd` | 测试驱动开发工作流 |
| `/build-fix` | 修复构建错误 |
| `/verify` | 验证更改 |
| `/checkpoint` | 创建检查点 |
| `/refactor-clean` | 重构和清理 |
| `/learn` | 提取可重用模式 |
| `/create_project` | 从模板创建新项目 |
| `/setup-pm` | 配置包管理器（uv/pnpm） |
| `/sc` | SuperClaude 命令套件（30 个命令） |

### 代理（14 个专业）

**研究代理：**
- **literature-reviewer** - 文献搜索、分类和趋势分析
- **data-analyst** - 自动化数据分析和可视化
- **rebuttal-writer** - 系统化 rebuttal 写作，语气优化
- **paper-miner** - 从成功论文中提取写作知识

**开发代理：**
- **architect** - 系统架构设计
- **build-error-resolver** - 修复构建错误
- **code-reviewer** - 审查代码质量
- **refactor-cleaner** - 移除死代码
- **tdd-guide** - 指导 TDD 工作流
- **kaggle-miner** - 提取 Kaggle 工程实践
- **bug-analyzer** - 深度代码执行流分析和根因调查
- **dev-planner** - 实施规划和任务拆解

**设计与内容代理：**
- **ui-sketcher** - UI 蓝图设计和交互规范
- **story-generator** - 用户故事和需求生成

## 快速开始

### 安装选项

选择适合您需求的安装方式：

#### 选项 1：完整安装（推荐）

安全合并到已有的 `~/.claude` 目录，不会覆盖个人配置：

```bash
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar
bash /tmp/claude-scholar/scripts/setup.sh
```

脚本会将 skills/commands/agents/rules/hooks 复制到 `~/.claude`，并将 hooks/mcpServers/enabledPlugins 合并到 `settings.json`（自动备份为 `settings.json.bak`）。你的 env 和 permissions 不受影响。

**包含**：所有 32 个技能、50+ 命令、14 个代理、5 个钩子和项目规则。

#### 选项 2：最小化安装

仅核心钩子和基本技能（加载更快，复杂度更低）：

```bash
# 克隆仓库
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar

# 仅复制钩子和核心技能
mkdir -p ~/.claude/hooks ~/.claude/skills
cp /tmp/claude-scholar/hooks/*.js ~/.claude/hooks/
cp -r /tmp/claude-scholar/skills/ml-paper-writing ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/research-ideation ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/results-analysis ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/review-response ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/writing-anti-ai ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/git-workflow ~/.claude/skills/
cp -r /tmp/claude-scholar/skills/bug-detective ~/.claude/skills/

# 清理
rm -rf /tmp/claude-scholar
```

**安装后**：需要将 hooks 配置合并到 `settings.json` — 参考 `settings.json.template` 中的 hooks 条目。

**包含**：5 个钩子、7 个核心技能（完整研究工作流 + 基本开发）。

#### 选项 3：选择性安装

选择和选择特定组件：

```bash
# 克隆仓库
git clone https://github.com/Galaxy-Dawn/claude-scholar.git /tmp/claude-scholar
cd /tmp/claude-scholar

# 复制您需要的内容，例如：
# - 仅钩子
cp hooks/*.js ~/.claude/hooks/

# - 特定技能
cp -r skills/latex-conference-template-organizer ~/.claude/skills/
cp -r skills/architecture-design ~/.claude/skills/

# - 特定代理
cp agents/paper-miner.md ~/.claude/agents/

# - 项目规则
cp rules/coding-style.md ~/.claude/rules/
cp rules/agents.md ~/.claude/rules/
```

**安装后**：需要将 hooks 配置合并到 `settings.json` — 参考 `settings.json.template`。

**推荐用于**：想要自定义配置的高级用户。

### 系统要求

- Claude Code CLI
- Git
- Node.js（钩子依赖，必需）
- uv、Python（用于 Python 开发）
- **Zotero**（用于 Zotero MCP 功能）

### MCP 服务配置

如需使用 Zotero 集成的研究工作流，请安装 MCP 服务器：

```bash
# 从 Galaxy-Dawn fork 安装（Web API 模式）
uv tool install git+https://github.com/Galaxy-Dawn/zotero-mcp.git
```

然后在 `~/.claude/settings.json` 中添加：

```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp",
      "args": ["serve"],
      "env": {
        "ZOTERO_API_KEY": "your-api-key",
        "ZOTERO_LIBRARY_ID": "your-library-id",
        "ZOTERO_LIBRARY_TYPE": "user",
        "UNPAYWALL_EMAIL": "your-email@example.com",
        "UNSAFE_OPERATIONS": "all"
      }
    }
  }
}
```

详细设置指南和故障排除请参阅 [MCP_SETUP.zh-CN.md](./MCP_SETUP.zh-CN.md)。

### 首次运行

安装后，钩子提供自动化工作流辅助：

1. **每次提示**触发 `skill-forced-eval` → 确保考虑适用技能
2. **会话开始**时使用 `session-start` → 显示项目上下文
3. **会话结束**时使用 `session-summary` → 生成带有建议的工作日志
4. **会话停止**时使用 `stop-summary` → 提供状态检查

## 项目规则

### 代码风格

由 `rules/coding-style.md` 强制执行：
- **文件大小**：最大 200-400 行
- **不可变性**：配置使用 `@dataclass(frozen=True)`
- **类型提示**：所有函数都需要
- **模式**：所有模块使用 Factory & Registry
- **配置驱动**：模型仅接受 `cfg` 参数

### 代理编排

在 `rules/agents.md` 中定义：
- 可用的代理类型和用途
- 并行任务执行
- 多视角分析

### 安全规则

在 `rules/security.md` 中定义：
- 密钥管理（环境变量、`.env` 文件）
- 敏感文件保护（禁止提交 token、密钥、凭证）
- 通过钩子进行提交前安全检查

### 实验可复现性

在 `rules/experiment-reproducibility.md` 中定义：
- 随机种子管理，确保可复现性
- 配置记录（Hydra 自动保存）
- 环境记录和检查点管理

## 贡献

这是个人配置，但欢迎您：
- Fork 并适应您自己的研究
- 通过 issue 提交错误
- 通过 issue 建议改进

## 许可证

MIT 许可证

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
