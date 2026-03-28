#!/usr/bin/env node
/**
 * UserPromptSubmit Hook: Forced skill activation flow (cross-platform version)
 *
 * Event: UserPromptSubmit
 * Function: Force AI to evaluate available skills and begin implementation after activation
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const common = require('./hook-common');

// Read stdin input
let input = {};
try {
  const stdinData = require('fs').readFileSync(0, 'utf8');
  if (stdinData.trim()) {
    input = JSON.parse(stdinData);
  }
} catch {
  // Use default empty object
}

const userPrompt = input.user_prompt || '';
const cwd = input.cwd || process.cwd();

// Check if it is a slash command (escape)
if (userPrompt.startsWith('/')) {
  // Distinguish commands from paths:
  // - Commands: /commit, /update-github (no second slash after the first)
  // - Paths: /Users/xxx, /path/to/file (contains path separators)
  const rest = userPrompt.substring(1);
  if (rest.includes('/')) {
    // This is a path, continue with skill scanning
  } else {
    // This is a command, skip skill evaluation
    console.log(JSON.stringify({ continue: true }));
    process.exit(0);
  }
}

const homeDir = os.homedir();

// Dynamically collect skill list
function collectSkills() {
  const skills = [];
  const skillsDir = path.join(homeDir, '.claude', 'skills');

  // 1. Collect local skills
  if (fs.existsSync(skillsDir)) {
    const skillDirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const skillName of skillDirs) {
      skills.push(skillName);
    }
  }

  // 2. Collect plugin skills
  const pluginsCache = path.join(homeDir, '.claude', 'plugins', 'cache');

  if (fs.existsSync(pluginsCache)) {
    const marketplaces = fs.readdirSync(pluginsCache, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const marketplace of marketplaces) {
      const marketplacePath = path.join(pluginsCache, marketplace);
      const plugins = fs.readdirSync(marketplacePath, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith('.'))
        .map(d => d.name);

      for (const plugin of plugins) {
        const pluginPath = path.join(marketplacePath, plugin);
        const versions = fs.readdirSync(pluginPath, { withFileTypes: true })
          .filter(d => d.isDirectory())
          .map(d => d.name)
          .sort()
          .reverse();

        if (versions.length > 0) {
          const latestVersion = versions[0];
          const skillsDirPath = path.join(pluginPath, latestVersion, 'skills');

          if (fs.existsSync(skillsDirPath)) {
            const skillDirs = fs.readdirSync(skillsDirPath, { withFileTypes: true })
              .filter(d => d.isDirectory())
              .map(d => d.name);

            for (const skillName of skillDirs) {
              skills.push(`${plugin}:${skillName}`);
            }
          }
        }
      }
    }
  }

  // Deduplicate
  return [...new Set(skills)].sort();
}

// Categorize skills into groups
function categorizeSkills(skills) {
  const categories = {
    'Research & Writing': /research|paper|writing|citation|review-response|rebuttal|post-acceptance|doc-coauthoring|latex|daily-paper|ml-paper|results-analysis|results-report|brainstorm|novelty|hypothesis|competitive|experiment-design|failure-diagnosis|hypothesis-revision|claim-evidence|contribution-positioning|story-construction|manuscript-production|result-collector|compute-planner|experiment-runner/,
    'Development': /coding|git|code-review|bug|architecture|verification|tdd|uv-package|webapp-testing|kaggle|driven-development|development-branch|planning|dispatching|executing|using-superpowers|project-scaffold|experiment-data|model-setup|measurement-implementation|setup-validation/,
    'Plugin Dev': /skill-|command-|hook-|mcp-|agent-identifier|plugin-structure/,
    'Design & UI': /frontend|ui-ux|web-design|canvas|brand|theme|algorithmic-art|slack-gif|figma/,
    'Documents': /docx|xlsx|pptx|pdf|internal-comms|web-artifacts/,
  };

  const grouped = {};
  for (const cat of Object.keys(categories)) {
    grouped[cat] = [];
  }
  grouped['Other'] = [];

  for (const skill of skills) {
    let matched = false;
    for (const [cat, regex] of Object.entries(categories)) {
      if (regex.test(skill)) {
        grouped[cat].push(skill);
        matched = true;
        break;
      }
    }
    if (!matched) {
      grouped['Other'].push(skill);
    }
  }

  return grouped;
}

// Keyword-to-skill mapping for pre-matching
// Note: \b doesn't work with CJK characters, so we use separate patterns
// English keywords use \b for precision; Chinese keywords match without \b
const KEYWORD_SKILL_MAP = [
  { keywords: /\b(git|github|commit|push|pull|merge|rebase|branch|tag|stash|cherry.?pick|develop|master|main)\b|分支|合并|推送|提交代码|上传.*分支|主分支/i, skills: ['git-workflow'] },
  { keywords: /\b(debug|bug|error|broken|failing|traceback|exception)\b|排查|调试|报错|出错|不工作/i, skills: ['bug-detective'] },
  { keywords: /\b(tdd|test.?driven)\b|写测试|测试驱动/i, skills: ['superpowers:test-driven-development'] },
  { keywords: /\b(code.?review|review code)\b|审查代码|代码审查/i, skills: ['code-review-excellence'] },
  { keywords: /\b(paper|manuscript|draft)\b|论文|写作|投稿/i, skills: ['ml-paper-writing'] },
  { keywords: /\b(research|idea|brainstorm)\b|研究|构思|文献/i, skills: ['research-ideation'] },
  { keywords: /\b(rebuttal|reviewer|response to reviewer)\b|审稿|回复审稿/i, skills: ['review-response'] },
  { keywords: /\b(frontend|landing.?page|dashboard)\b|前端|界面|网页设计/i, skills: ['frontend-design'] },
  { keywords: /\b(create|write|develop|improve).*skill|skill.*(开发|创建|写|改进)|开发.*skill|写.*skill|改进.*skill/i, skills: ['skill-development'] },
  { keywords: /\b(create|write|develop).*hook|hook.*(开发|创建|写)|开发.*hook|写.*hook/i, skills: ['hook-development'] },
  { keywords: /\b(create|write|develop).*command|slash.*command|command.*(开发|创建|写)|开发.*command|写.*命令/i, skills: ['command-development'] },
  { keywords: /\b(create|write|develop).*agent|agent.*(开发|创建|写)|开发.*agent|写.*agent/i, skills: ['agent-identifier'] },
  { keywords: /\b(mcp)\b|mcp.*server|mcp.*集成/i, skills: ['mcp-integration'] },
  { keywords: /\b(architecture|factory|registry)\b|架构|设计模式/i, skills: ['architecture-design'] },
  { keywords: /\b(uv|pip|package.*manager|venv)\b|包管理|虚拟环境/i, skills: ['uv-package-manager'] },
  { keywords: /\b(kaggle|competition)\b|竞赛/i, skills: ['kaggle-learner'] },
  { keywords: /\b(citation|reference.*check)\b|引用|引文|参考文献/i, skills: ['citation-verification'] },
  { keywords: /\b(latex.*template|overleaf)\b|模板整理/i, skills: ['latex-conference-template-organizer'] },
  { keywords: /\b(ablation)\b|实验结果|results.*analysis|统计检验|消融实验|科学绘图|实验统计/i, skills: ['results-analysis'] },
  { keywords: /\b(experiment.?report|results.?report|retrospective|wrap.?up)\b|实验报告|实验总结|实验复盘|结果总结/i, skills: ['results-report'] },
  { keywords: /\b(poster|presentation|promote)\b|海报|演讲|推广/i, skills: ['post-acceptance'] },
  { keywords: /\b(plan|planning)\b|规划|计划/i, skills: ['planning-with-files'] },
  { keywords: /\b(verify|verification)\b|验证/i, skills: ['verification-loop'] },
  { keywords: /\b(self.?review)\b|自审|论文检查/i, skills: ['paper-self-review'] },
  { keywords: /\b(anti.?ai|humanize)\b|去.*ai.*痕迹|AI写作/i, skills: ['writing-anti-ai'] },
  { keywords: /\b(implement|write code|add feature|modify|refactor)\b|写代码|改代码|实现|添加功能|修改|重构/i, skills: ['daily-coding'] },
  { keywords: /\b(hypothes[ie]s|falsifiable|success.?criteria|testable|make.*testable|what.*should.*test)\b|假设|可证伪|成功标准/i, skills: ['hypothesis-formulation'] },
  { keywords: /\b(experiment.?design|design.?experiment|baseline.?selection|ablation.?plan|power.?analysis|how.?many.?seeds|how.?many.?runs|sample.?size)\b|实验设计|基线选择|消融计划|样本量/i, skills: ['experiment-design'] },
  { keywords: /\b(novelty|incremental|contribution.*compare|prior.*work.*compare)\b|新颖性|增量.*贡献|贡献.*比较/i, skills: ['novelty-assessment'] },
  { keywords: /\b(competing|scoop|concurrent.*work|someone.*published|check.*competition)\b|竞争|被抢发|并发.*工作/i, skills: ['competitive-check'] },
  { keywords: /\b(claim.*evidence|evidence.*map|what.*can.*I.*claim|scope.*paper|include.*paper|over.?claim)\b|证据.*映射|论文.*范围|过度.*声称/i, skills: ['claim-evidence-bridge'] },
  { keywords: /\b(scaffold|project.*structure|pyproject|init.*project|create.*project.*structure)\b|项目.*脚手架|项目.*结构/i, skills: ['project-scaffold'] },
  { keywords: /\b(data.*generat|synthetic.*data|build.*data|dataset.*construct|data.*loader)\b|数据.*生成|合成.*数据/i, skills: ['experiment-data-builder'] },
  { keywords: /\b(model.*load|hook|model.*surgery|activation.*extract|attention.*head|introspect)\b|模型.*加载|激活.*提取/i, skills: ['model-setup'] },
  { keywords: /\b(metric.*implement|analytical.*reference|measurement|cosine.*similar|statistical.*test|significance)\b|度量.*实现|分析.*参考/i, skills: ['measurement-implementation'] },
  { keywords: /\b(sanity.*check|pre.?flight|validate.*setup|baseline.*replic|smoke.*test)\b|健全.*检查|基线.*复现/i, skills: ['setup-validation'] },
  { keywords: /\b(slurm|sbatch|gpu.*hours?|cluster|engaging|partition|compute.*plan)\b|集群|计算.*计划/i, skills: ['compute-planner'] },
  { keywords: /\b(run.*matrix|experiment.*sweep|phase.*gate|submit.*jobs?|monitor.*experiment)\b|运行.*矩阵|实验.*扫描/i, skills: ['experiment-runner'] },
  { keywords: /\b(aggregate.*results?|collect.*metrics?|collect.*results?|gather.*outputs?)\b|汇总.*结果|收集.*指标/i, skills: ['result-collector'] },
  { keywords: /\b(contribution.*position|differentiat|reviewer.*objection|articulate.*contribution)\b|贡献.*定位|审稿人.*反对/i, skills: ['contribution-positioning'] },
  { keywords: /\b(narrative|story.*construct|figure.*plan|paper.*blueprint|section.*outline)\b|叙事|故事.*构建|论文.*蓝图/i, skills: ['story-construction'] },
  { keywords: /\b(figure.*produc|latex.*source|submission.*package|manuscript.*produc|camera.*ready|compile.*paper)\b|图.*制作|手稿.*生产|投稿.*包/i, skills: ['manuscript-production'] },
];

// Pre-match user prompt against keyword map
function suggestSkills(prompt) {
  const suggested = new Set();
  for (const { keywords, skills } of KEYWORD_SKILL_MAP) {
    if (keywords.test(prompt)) {
      for (const s of skills) suggested.add(s);
    }
  }
  return [...suggested];
}

// Context-aware skill activation for research iteration loop
// Must run BEFORE the standard KEYWORD_SKILL_MAP loop to handle disambiguation
function contextAwareSkillSuggestions(prompt, projectRoot) {
  const suggestions = [];

  const hasResearchContext = ['hypotheses.md', 'experiment-plan.md', 'experiment-state.json']
    .some(f => fs.existsSync(path.join(projectRoot, f)));

  // 1. failure-diagnosis vs bug-detective
  //    Research failure keywords overlap with code debugging keywords.
  //    Route to failure-diagnosis ONLY in research projects.
  const failureDiagnosisPattern = /\b(experiment.*fail|results.*worse|hypothesis.*wrong|not.*learning|underperform|why.*didn.?t.*work)\b|实验.*失败|结果.*差|假设.*错/i;
  if (failureDiagnosisPattern.test(prompt) && hasResearchContext) {
    suggestions.push('failure-diagnosis');
  }

  // 2. hypothesis-revision — only meaningful with existing hypotheses
  const hypothesisRevisionPattern = /\b(pivot|persevere|revise.*hypothes|update.*hypothes|what.*next.*experiment|should.*I.*continue)\b|修订.*假设|是否.*继续/i;
  if (hypothesisRevisionPattern.test(prompt) && hasResearchContext) {
    suggestions.push('hypothesis-revision');
  }

  return suggestions;
}

// Generate skill list
const SKILL_LIST = collectSkills();
const SKILL_GROUPS = categorizeSkills(SKILL_LIST);
const suggestedSkills = suggestSkills(userPrompt);

// Add context-aware suggestions
const contextSuggestions = contextAwareSkillSuggestions(userPrompt, cwd);
for (const s of contextSuggestions) {
  suggestedSkills.push(s);
}
const binding = common.getProjectMemoryBinding(cwd);
const isResearchPrompt = common.promptLooksResearchRelated(userPrompt);

if (binding.bound && isResearchPrompt) {
  if (SKILL_LIST.includes('obsidian-project-memory')) {
    suggestedSkills.push('obsidian-project-memory');
  }
  if (/\b(zotero|collection|doi|arxiv|citation)\b|zotero|文献|参考文献|collection/i.test(userPrompt) &&
      SKILL_LIST.includes('zotero-obsidian-bridge')) {
    suggestedSkills.push('zotero-obsidian-bridge');
  }
  if (/\b(paper|papers|literature|review|claim|method|evidence)\b|论文|综述|paper/i.test(userPrompt) &&
      SKILL_LIST.includes('obsidian-literature-workflow')) {
    suggestedSkills.push('obsidian-literature-workflow');
  }
}

const dedupedSuggestedSkills = [...new Set(suggestedSkills)];

// Format grouped skills (skip empty groups)
const groupedDisplay = Object.entries(SKILL_GROUPS)
  .filter(([, skills]) => skills.length > 0)
  .map(([cat, skills]) => `[${cat}] ${skills.join(', ')}`)
  .join('\n');

// Build suggested skills hint
const suggestedHint = dedupedSuggestedSkills.length > 0
  ? `\n**Pre-matched skills (MUST activate these)**: ${dedupedSuggestedSkills.join(', ')}\nThese skills matched keywords in the user's prompt. You MUST activate them via Skill tool.\n`
  : '';

const boundRepoHint = binding.bound && isResearchPrompt
  ? `\n**Bound Obsidian repo detected**: ${binding.projectId || 'unknown-project'}\nUse lightweight curator behavior by default: keep \`Daily/YYYY-MM-DD.md\` and \`.claude/project-memory/<project_id>.md\` in sync when this turn changes research state, and touch \`00-Hub.md\` only when top-level project status really changes. Consider the \`research-knowledge-curator-obsidian\` agent when the task spans plans, papers, experiments, results, or writing.\n`
  : '';

// Generate output
const output = `## Instruction: Forced Skill Activation (Mandatory)

Silently scan the user's request against available skills. Do NOT list every skill with Yes/No.

Available skills:
${groupedDisplay}
${suggestedHint}${boundRepoHint}
**Action**:
- If any skill matches → Activate via Skill tool, then output: "Activating: [skill-name] — [reason]"
- If no skill matches → Output: "No skills needed"
- Begin implementation only after activation is complete.
- When multiple skills match, activate all of them.
`;

console.log(output);

process.exit(0);
