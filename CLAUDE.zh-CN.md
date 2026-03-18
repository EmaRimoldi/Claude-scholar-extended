# Claude Scholar 配置

## 项目概述

**Claude Scholar** - 面向学术研究和软件开发的半自动研究助手

**Mission**: 支持 Claude Code、OpenCode 和 Codex CLI，覆盖构思、编码、实验、写作、发表，以及插件开发和项目管理。

---

## 用户背景

### 学术背景
- **学历**: 计算机科学 PhD
- **投稿目标**:
  - 顶会：NeurIPS, ICML, ICLR, KDD
  - 高影响期刊：Nature, Science, Cell, PNAS
- **关注点**: 学术写作质量、逻辑连贯性、自然表达

### 技术栈偏好

**Python 生态**:
- **包管理**: `uv` - 现代化 Python 包管理器
- **配置管理**: Hydra + OmegaConf（配置组合、覆盖、类型安全）
- **模型训练**: Transformers Trainer

**Git 规范**:
- **提交规范**: Conventional Commits
  ```
  Type: feat, fix, docs, style, refactor, perf, test, chore
  Scope: data, model, config, trainer, utils, workflow
  ```
- **分支策略**: master/develop/feature/bugfix/hotfix/release
- **合并策略**: 功能分支用 rebase 同步，用 merge --no-ff 合并

---

## 全局配置

### 语言设置
- 用中文进行回答
- 专业术语保持英文（如 NeurIPS, RLHF, TDD, Git）
- 不翻译特定名词或名称

### 工作目录规范
- 计划文档：`/plan` 文件夹
- 临时文件：`/temp` 文件夹
- 文件夹不存在时自动创建

### 任务执行原则
- 复杂任务先交流意见，再拆解实施
- 实施后进行示例测试
- 做好备份，不影响现有功能
- 完成后及时删除临时文件

### 工作风格
- **任务管理**: 使用 TodoWrite 跟踪进度，复杂任务先规划再执行，优先使用已有 skills
- **沟通方式**: 不确定时主动询问，重要操作前先确认，遵循 hook 强制流程
- **代码风格**: Python 遵循 PEP 8，注释使用中文，命名使用英文

---

## 核心工作流

### 研究生命周期（7 阶段）

```
构思 → ML开发 → 实验分析 → 论文写作 → 自审 → 投稿/Rebuttal → 录用后处理
```

| 阶段 | 核心工具 | 命令 |
|------|---------|------|
| 1. 研究构思 | `research-ideation` skill + `literature-reviewer` agent + Zotero MCP | `/research-init`, `/zotero-review`, `/zotero-notes` |
| 2. ML 项目开发 | `architecture-design` skill + `code-reviewer` agent | `/plan`, `/commit`, `/tdd` |
| 3. 实验分析 | `results-analysis` skill + `results-report` skill | `/analyze-results` |
| 4. 论文写作 | `ml-paper-writing` skill + `paper-miner` agent | `/mine-writing-patterns` |
| 5. 论文自审 | `paper-self-review` skill | - |
| 6. 投稿与 Rebuttal | `review-response` skill + `rebuttal-writer` agent | `/rebuttal` |
| 7. 录用后处理 | `post-acceptance` skill | `/presentation`, `/poster`, `/promote` |

### 支撑工作流

- **自动化执行**: 5 个 Hook 在会话各阶段自动触发（技能评估、环境初始化、工作总结、安全检查）
- **Zotero 集成**: 通过 Zotero MCP 服务器实现论文自动导入、集合管理、全文阅读和准确引用导出
- **Obsidian 知识库**: 内置的 filesystem-first 项目知识库，统一管理文献、计划、TODO、实验、结果、写作、会议与归档，不依赖 MCP；默认图谱仅维护 `Maps/literature.canvas`，`.base` 视图需显式触发
- **知识提取**: `paper-miner` 和 `kaggle-miner` agent 持续从论文和竞赛中提取知识
- **技能进化**: `skill-development` → `skill-quality-reviewer` → `skill-improver` 三步改进循环

### Obsidian 项目知识库规则

- 如果当前仓库包含 `.claude/project-memory/registry.yaml`，默认启用 `obsidian-project-memory`，并将 Obsidian 视为该仓库的默认项目知识库。
- 如果仓库还没绑定，但具备科研项目特征，默认启用 `obsidian-project-bootstrap` 自动导入到 vault。
- 每个重要的项目 turn 至少更新：当日 daily note 与 repo 本地的 project memory；只有顶层项目状态真正变化时才更新 hub note。
- 这个工作流不允许要求用户额外配置任何 Obsidian API 或密钥。

---

## 技能目录（47 skills）

### 🔬 研究与分析 (5 skills)

- **research-ideation**: 研究构思启动（5W1H、文献综述、Gap 分析、研究问题制定、Zotero 自动集成）
- **results-analysis**: 严格实验分析（严谨统计、科研绘图、消融实验）
- **results-report**: 完整实验总结报告（复盘、决策支持、Obsidian 结果报告）
- **citation-verification**: 引文验证（多层验证：格式→API→信息→内容）
- **daily-paper-generator**: 每日论文生成器，用于研究追踪

### 📝 论文写作与发表 (7 skills)

- **ml-paper-writing**: ML/AI 论文写作辅助
  - 顶会：NeurIPS, ICML, ICLR, ACL, AAAI, COLM
  - 期刊：Nature, Science, Cell, PNAS
- **writing-anti-ai**: 去除 AI 写作痕迹，支持中英文双语
- **paper-self-review**: 论文自审（6 项质量检查清单）
- **review-response**: 系统化 rebuttal 写作
- **post-acceptance**: 录用后处理（演讲、海报、推广）
- **doc-coauthoring**: 文档协作工作流
- **latex-conference-template-organizer**: LaTeX 会议模板整理

### 💻 开发工作流 (6 skills)

- **daily-coding**: 日常编码检查清单（极简模式，自动触发）
- **git-workflow**: Git 工作流规范（Conventional Commits, 分支管理策略）
- **code-review-excellence**: 代码审查最佳实践
- **bug-detective**: 调试和错误排查（Python, Bash/Zsh, JavaScript/TypeScript）
- **architecture-design**: ML 项目代码框架和设计模式
- **verification-loop**: 验证循环和测试

### 🔌 插件开发 (8 skills)

- **skill-development**: Skill 开发指南
- **skill-improver**: Skill 改进工具
- **skill-quality-reviewer**: Skill 质量审查
- **command-development**: Slash 命令开发
- **command-name**: 插件结构指南
- **agent-identifier**: Agent 开发配置
- **hook-development**: Hook 开发和事件处理
- **mcp-integration**: MCP 服务器集成

### 🧪 工具与实用 (4 skills)

- **planning-with-files**: 使用 Markdown 文件进行规划和进度跟踪
- **uv-package-manager**: uv 包管理器使用
- **webapp-testing**: 本地 Web 应用测试
- **kaggle-learner**: Kaggle 竞赛学习

### 🧠 Obsidian 知识库 (11 skills)

- **obsidian-project-memory**: 项目目录内默认启用的 Obsidian project memory 总控技能
- **obsidian-project-bootstrap**: 将新项目或已有科研仓库导入 Obsidian 项目知识库
- **obsidian-research-log**: daily、TODO、计划、会议记录
- **obsidian-experiment-log**: 实验与结果沉淀
- **obsidian-link-graph**: legacy 兼容辅助，用于修复 canonical notes 之间的 wikilink
- **obsidian-synthesis-map**: legacy 兼容辅助，用于更高层的 synthesis notes 与比较总结
- **obsidian-project-lifecycle**: detach、archive、purge、rebuild
- **zotero-obsidian-bridge**: 将 Zotero collection/全文桥接到 Obsidian 详细论文笔记与默认的 `Maps/literature.canvas`
- **obsidian-literature-workflow**: 项目 vault 内的论文笔记规范化与综述工作流
- **obsidian-markdown**: 内置官方 Obsidian Markdown skill
- **obsidian-cli**: 内置官方 Obsidian CLI skill
- **obsidian-bases / json-canvas / defuddle**: 内置官方 `.base`、`.canvas` 与网页内容提取支持

### 🎨 网页设计 (3 skills)

- **frontend-design**: 创建独特、生产级的前端界面，避免通用 AI 美学
- **ui-ux-pro-max**: UI/UX 设计智能（50+ 风格、97 色板、57 字体配对、9 技术栈）
- **web-design-reviewer**: 网站设计视觉检查，识别并修复响应式、可访问性、布局问题

---

## 命令（50+ Commands）

### 研究工作流命令

| 命令 | 功能 |
|------|------|
| `/research-init` | 启动 Zotero 集成研究构思工作流（自动建集合、导入论文、全文分析） |
| `/zotero-review` | 从 Zotero 集合读取论文，并综合到 Obsidian 文献综述与下游项目笔记 |
| `/zotero-notes` | 批量阅读 Zotero 论文，创建/更新 Obsidian 详细阅读笔记并刷新 `Maps/literature.canvas` |
| `/obsidian-init` | 为当前科研仓库初始化或导入 Obsidian 项目知识库 |
| `/obsidian-ingest` | 将新的 Markdown 文件或目录按 classify -> promote / merge / stage-to-daily 入库 |
| `/obsidian-review` | 从 Obsidian 项目笔记生成项目级文献综述 |
| `/obsidian-notes` | 规范化论文笔记，并连接到项目知识、实验与结果 note |
| `/obsidian-sync` | 强制执行 repo、project memory、Obsidian 三者之间的同步修复 |
| `/obsidian-link` | 重建或增强项目 wikilinks 与知识图 |
| `/obsidian-note` | 对单个 canonical note 执行 archive、purge 或 rename |
| `/obsidian-project` | detach、archive、purge、rebuild 项目知识库 |
| `/obsidian-views` | 显式生成可选的 `.base` 视图与额外 canvases |
| `/analyze-results` | 分析实验结果（统计检验、可视化、消融实验） |
| `/rebuttal` | 生成系统化 rebuttal 文档 |
| `/presentation` | 创建会议演讲大纲 |
| `/poster` | 生成学术海报设计方案 |
| `/promote` | 生成推广内容（Twitter、LinkedIn、博客） |

### 开发工作流命令

| 命令 | 功能 |
|------|------|
| `/plan` | 创建实施计划 |
| `/commit` | 提交代码（遵循 Conventional Commits） |
| `/update-github` | 提交并推送到 GitHub |
| `/update-readme` | 更新 README 文档 |
| `/code-review` | 代码审查 |
| `/tdd` | 测试驱动开发工作流 |
| `/build-fix` | 修复构建错误 |
| `/verify` | 验证更改 |
| `/checkpoint` | 创建检查点 |
| `/refactor-clean` | 重构和清理 |
| `/learn` | 从代码中提取可重用模式 |
| `/create_project` | 创建新项目 |
| `/setup-pm` | 配置包管理器（uv/pnpm） |
| `/update-memory` | 检查并更新 CLAUDE.md 记忆 |

### SuperClaude 命令集 (`/sc`)

- `/sc agent` - Agent 调度
- `/sc analyze` - 代码分析
- `/sc brainstorm` - 交互式头脑风暴
- `/sc build` - 构建项目
- `/sc business-panel` - 业务面板
- `/sc cleanup` - 代码清理
- `/sc design` - 系统设计
- `/sc document` - 生成文档
- `/sc estimate` - 工作量估算
- `/sc explain` - 代码解释
- `/sc git` - Git 操作
- `/sc help` - 帮助信息
- `/sc implement` - 功能实现
- `/sc improve` - 代码改进
- `/sc index` - 项目索引
- `/sc index-repo` - 仓库索引
- `/sc load` - 加载上下文
- `/sc pm` - 包管理器操作
- `/sc recommend` - 推荐方案
- `/sc reflect` - 反思总结
- `/sc research` - 技术调研
- `/sc save` - 保存上下文
- `/sc select-tool` - 工具选择
- `/sc spawn` - 生成子任务
- `/sc spec-panel` - 规格面板
- `/sc task` - 任务管理
- `/sc test` - 测试执行
- `/sc troubleshoot` - 问题排查
- `/sc workflow` - 工作流管理

---

## 代理（16 Agents）

### 研究工作流代理

- **literature-reviewer** - 文献搜索、分类和趋势分析（Zotero MCP 集成，支持自动导入、全文阅读）
- **literature-reviewer-obsidian** - 基于 filesystem 的 Obsidian 项目知识库文献综述
- **research-knowledge-curator-obsidian** - 默认维护项目计划、TODO、文献、实验、结果、会议和写作的 Obsidian curator
- **rebuttal-writer** - 系统化 rebuttal 写作，语气优化
- **paper-miner** - 从成功论文中提取写作知识

### 开发工作流代理

- **architect** - 系统架构设计
- **build-error-resolver** - 构建错误修复
- **bug-analyzer** - 深度代码执行流分析和根因调查
- **code-reviewer** - 代码审查
- **dev-planner** - 开发任务规划和拆解
- **refactor-cleaner** - 代码重构和清理
- **tdd-guide** - TDD 工作流指导
- **kaggle-miner** - Kaggle 工程实践提取

### 设计与内容代理

- **ui-sketcher** - UI 蓝图设计和交互规范
- **story-generator** - 用户故事和需求生成

---

## 钩子（5 Hooks）

跨平台 Node.js 钩子，自动化工作流执行：

| 钩子 | 触发时机 | 功能 |
|------|----------|------|
| `session-start.js` | 会话开始 | 显示 Git 状态、待办事项、可用命令，以及已绑定的 Obsidian project-memory 状态 |
| `skill-forced-eval.js` | 每次用户输入 | 强制评估所有可用技能，并在已绑定科研仓库中提示 Obsidian curator 流程 |
| `session-summary.js` | 会话结束 | 生成工作日志，检测 CLAUDE.md 更新，并提醒 bound repo 的最小 Obsidian 写回 |
| `stop-summary.js` | 会话停止 | 快速状态检查、临时文件检测，以及 bound repo 的 Obsidian 维护提醒 |
| `security-guard.js` | 文件操作 | 安全验证（密钥检测、危险命令拦截） |

---

## 规则（4 Rules）

全局约束，始终生效：

| 规则文件 | 作用 |
|---------|------|
| `coding-style.md` | ML 项目代码标准：文件 200-400 行、不可变配置、类型提示、Factory & Registry 模式 |
| `agents.md` | 代理编排：自动调用时机、并行执行、多视角分析 |
| `security.md` | 安全规范：密钥管理、敏感文件保护、提交前安全检查 |
| `experiment-reproducibility.md` | 实验可复现性：随机种子、配置记录、环境记录、检查点管理 |

---

## 命名规范

### Skill 命名
- 格式：kebab-case（小写+连字符）
- 形式：优先使用 gerund form（动词+ing）
- 示例：`scientific-writing`, `git-workflow`, `bug-detective`

### Tags 命名
- 格式：Title Case
- 缩写全大写：TDD, RLHF, NeurIPS, ICLR
- 示例：`[Writing, Research, Academic]`

### 描述规范
- 人称：第三人称
- 内容：包含用途和使用场景
- 示例："为学术论文写作提供指导，覆盖顶会投稿要求"

---

## 任务完成总结

每次任务完成时，主动提供简要总结：

```
📋 本次操作回顾
1. [主要操作]
2. [修改的文件]

📊 当前状态
• [Git/文件系统/运行状态]

💡 下一步建议
1. [针对性建议]
```
