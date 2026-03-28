---
name: analyze-results
description: Run the full post-experiment workflow in one command: strict statistical analysis, real scientific figures, and a decision-oriented results report. Uses results-analysis + results-report as a two-stage workflow.
args:
  - name: data_path
    description: Path to experimental results (CSV, JSON, logs, or directory)
    required: false
  - name: analysis_type
    description: Type of analysis (full, comparison, ablation, visualization)
    required: false
    default: full
  - name: purpose
    description: Optional report purpose slug (e.g. transfer-summary, ablation-report)
    required: false
    default: auto
  - name: round
    description: Optional experiment round number for report naming
    required: false
  - name: experiment_line
    description: Optional experiment line slug for report naming
    required: false
tags: [Research, Analysis, Statistics, Visualization, Reporting]
---

# Analyze Results Command

一键执行**实验后分析 + 报告成稿**工作流。

这是用户默认应该使用的入口。

如果你只是想“跑严格统计和科研图，不写总结报告”，才单独走 `results-analysis`。

## 目标

此命令负责把一次实验结果处理成两层产物：

### Phase 1: strict analysis bundle
- 严格统计分析
- 真实科研图
- figure interpretation checklist
- 可追溯的统计附录

### Phase 2: complete results report
- 完整实验总结报告
- 逐图解释与结论串联
- 面向决策的 next actions
- 如已绑定 Obsidian，则自动写回知识库

换句话说，`/analyze-results` 不只是“分析”，而是：

> **先做 evidence-first analysis，再基于证据生成完整实验报告。**

## 默认编排

命令默认按以下顺序执行：

1. **定位输入**
   - 找到实验目录、CSV/JSON、日志、图表原料与比较对象
2. **Phase 1 严格分析**
   - 使用 `results-analysis`
3. **Phase 2 完整报告**
   - 使用 `results-report`
   - 基于 Phase 1 产物写出完整实验总结报告
4. **知识库回写**
   - 如果当前 repo 已绑定 Obsidian project memory，则写回 `Results/Reports/`、相关 `Experiments/`、`Daily/` 和 project memory
5. **显式报告 blocker**
   - 若统计输入不足、无法画图或命名信息缺失，必须说明阻塞点，不能伪造结论

## 使用方法

### 基本用法

```bash
/analyze-results
```

### 指定实验目录

```bash
/analyze-results path/to/experiment_dir
```

### 指定分析类型

```bash
/analyze-results path/to/results comparison
```

### 指定报告用途与轮次

```bash
/analyze-results path/to/results full transfer-summary 3 freezing
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `data_path` | 实验结果路径，可为目录、CSV、JSON 或日志 |
| `analysis_type` | `full` / `comparison` / `ablation` / `visualization` |
| `purpose` | 报告用途 slug；默认自动推断，无法推断时需显式说明 |
| `round` | 实验轮次；用于报告命名，未知时允许暂用 `r00` 并注明 |
| `experiment_line` | 实验线 slug，如 `freezing`、`contrastive-adversarial` |

## 分析类型

| 类型 | 说明 | Phase 1 重点 | Phase 2 重点 |
|------|------|--------------|--------------|
| `full` | 完整严格分析（默认） | 完整统计 + 主图 + supporting figure | 完整实验总结报告 |
| `comparison` | 模型对比 | 显著性检验 + effect size + 主对比图 | 哪个方案更值得继续 |
| `ablation` | 消融实验 | 组件贡献分析 + 稳定性分析 | 哪个组件真正改变了结果 |
| `visualization` | 图表优先 | 高质量科研图 + 图表解释 | 图驱动的结果复盘 |

## 输出产物

### Phase 1 输出

```text
analysis-output/
├── analysis-report.md
├── stats-appendix.md
├── figure-catalog.md
└── figures/
```

### Phase 2 输出

```text
Results/Reports/
└── YYYY-MM-DD--{experiment-line}--r{round}--{purpose}.md
```

报告标题默认遵循：

```text
{Experiment Line} / Round {N} / {Purpose} / {YYYY-MM-DD}
```

## Statistical Tests (mandatory)

Every pairwise comparison in the analysis MUST include the following:

1. **Paired bootstrap test** with 10,000 resamples to compute p-values
2. **95% confidence intervals** for all reported metrics
3. **Cohen's d effect size** for every comparison

### Rules

- Flag comparisons where confidence intervals overlap as **"not statistically distinguishable"**
- If `n_seeds < 5`, emit a **WARNING** in the analysis output: `"⚠ Only {n} seeds — statistical power is limited; interpret with caution."`
- Include a **Statistical Summary** table with the following columns:

| Condition | Mean | Std | 95% CI | p-value vs baseline | Cohen's d |
|-----------|------|-----|--------|---------------------|-----------|

## Contradiction Detection (mandatory)

After computing results, systematically check alignment with stated hypotheses:

1. Load `hypotheses.md` and enumerate each hypothesis
2. For each hypothesis, determine whether the results **support**, **partially support**, **contradict**, or are **inconclusive**
3. If a stated contribution is contradicted by results (e.g., "selective head supervision improves X" but results show no improvement or degradation), **flag it explicitly** with a prominent warning
4. Generate a **Hypothesis Verdict** table:

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| H1: ... | supported / partially / contradicted / inconclusive | Key metric values and statistical test results |

## Error Analysis (mandatory)

Go beyond aggregate metrics to understand failure modes:

1. **Stratify results by at least 2 dimensions** (e.g., per-class and by sample difficulty, or per-class and by sequence length)
2. Include a **per-class F1 breakdown** table
3. **Analyze failure cases**: identify what the worst-performing samples have in common (e.g., class imbalance, short sequences, ambiguous labels, domain shift)
4. Report at minimum:
   - Which classes or strata have the largest performance gap vs baseline
   - Whether errors are systematic (concentrated in specific strata) or random

## Results Health Check

Before proceeding to Phase 2 (report generation), run the following health check and output a **pass/fail summary**:

| Check | Criterion | Status |
|-------|-----------|--------|
| Equal seed counts | All conditions have the same number of seeds/runs | pass/fail |
| No missing results | All expected result files are present | pass/fail |
| Statistical tests complete | All pairwise comparisons have bootstrap p-values, CIs, and Cohen's d | pass/fail |
| Hypothesis verdicts assigned | Every hypothesis in hypotheses.md has a verdict | pass/fail |

If any check **fails**, the health check must be reported as a blocker before generating the final report.

## 执行规则

### 统计与图表
- 必须优先生成真实科研图，而不是只写 visualization specs
- 必须报告样本单位、seed/run 数、`95% CI`、effect size、multiple-comparison handling
- 假设不满足时必须改用 non-parametric fallback 或显式说明不能做强推断

### 报告生成
- 报告必须基于 Phase 1 的真实证据，而不是凭印象总结
- 报告必须覆盖：main findings、statistical validation、figure-by-figure interpretation、negative results、next actions
- 报告默认是**内部实验总结报告**，不是论文 `Results` section

### Obsidian 写回
如果 repo 已绑定 Obsidian knowledge base，则至少执行：
- 新建/更新 `Results/Reports/{report-name}.md`
- 回链对应 `Experiments/` note
- 若结论已稳定，更新 canonical `Results/` note
- 追加当天 `Daily/YYYY-MM-DD.md`
- 更新 `.claude/project-memory/<project_id>.md`

## 何时不用这个命令

以下场景不必默认使用 `/analyze-results`：

1. **你只要统计和图，不要实验总结报告**
   - 直接用 `results-analysis` 生成 Phase 1 strict analysis bundle
2. **你已经有 analysis bundle，只差最终报告**
   - 直接用 `results-report`
3. **你要写论文 Results section**
   - 不应由本命令直接替代 manuscript writing workflow

## 集成关系

- **Primary user entrypoint**: `/analyze-results`
- **Phase 1 skill**: `results-analysis`
- **Phase 2 skill**: `results-report`

## 成功标准

完成后至少应满足：
- 有 strict analysis bundle
- 有命名规范正确的 results report
- 图表与文字解释一致
- blocker 与限制被明确写出
- 若 repo 绑定 Obsidian，知识库已完成最小写回
