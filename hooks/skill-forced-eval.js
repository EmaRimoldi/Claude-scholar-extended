#!/usr/bin/env node
/**
 * UserPromptSubmit Hook: Minimal skill activation trigger
 *
 * Event: UserPromptSubmit
 * Function: Pattern-match user input against skill keywords, output minimal trigger hints.
 *           Full skill content is loaded when Claude invokes the Skill tool.
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const common = require('./hook-common');

let input = {};
try {
  const stdinData = fs.readFileSync(0, 'utf8');
  if (stdinData.trim()) input = JSON.parse(stdinData);
} catch { /* use default */ }

const userPrompt = input.user_prompt || '';
const cwd = input.cwd || process.cwd();

// Skip slash commands (but not file paths)
if (userPrompt.startsWith('/') && !userPrompt.substring(1).includes('/')) {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}

// Keyword-to-skill mapping (ordered by specificity)
const KEYWORD_SKILL_MAP = [
  { keywords: /\b(git|commit|push|pull|merge|rebase|branch)\b/i, skill: 'git-workflow' },
  { keywords: /\b(debug|bug|error|broken|failing|traceback|exception)\b/i, skill: 'bug-detective' },
  { keywords: /\b(tdd|test.?driven)\b/i, skill: 'superpowers:test-driven-development' },
  { keywords: /\b(code.?review|review code)\b/i, skill: 'code-review-excellence' },
  { keywords: /\b(paper|manuscript|draft)\b/i, skill: 'ml-paper-writing' },
  { keywords: /\b(research|brainstorm)\b/i, skill: 'research-ideation' },
  { keywords: /\b(rebuttal|reviewer|response to reviewer)\b/i, skill: 'review-response' },
  { keywords: /\b(frontend|landing.?page|dashboard)\b/i, skill: 'frontend-design' },
  { keywords: /\b(create|write|develop|improve).*skill/i, skill: 'skill-development' },
  { keywords: /\b(create|write|develop).*hook/i, skill: 'hook-development' },
  { keywords: /\b(create|write|develop).*command|slash.*command/i, skill: 'command-development' },
  { keywords: /\b(create|write|develop).*agent/i, skill: 'agent-identifier' },
  { keywords: /\bmcp\b/i, skill: 'mcp-integration' },
  { keywords: /\b(architecture|factory|registry)\b/i, skill: 'architecture-design' },
  { keywords: /\b(uv|pip|package.*manager|venv)\b/i, skill: 'uv-package-manager' },
  { keywords: /\b(kaggle|competition)\b/i, skill: 'kaggle-learner' },
  { keywords: /\b(citation|reference.*check)\b/i, skill: 'citation-verification' },
  { keywords: /\b(latex.*template|overleaf)\b/i, skill: 'latex-conference-template-organizer' },
  { keywords: /\b(ablation|results.*analysis)\b/i, skill: 'results-analysis' },
  { keywords: /\b(experiment.?report|results.?report|retrospective)\b/i, skill: 'results-report' },
  { keywords: /\b(poster|presentation|promote)\b/i, skill: 'post-acceptance' },
  { keywords: /\b(plan|planning)\b/i, skill: 'planning-with-files' },
  { keywords: /\b(verify|verification)\b/i, skill: 'verification-loop' },
  { keywords: /\b(self.?review)\b/i, skill: 'paper-self-review' },
  { keywords: /\b(anti.?ai|humanize)\b/i, skill: 'writing-anti-ai' },
  { keywords: /\b(hypothes[ie]s|falsifiable|success.?criteria)\b/i, skill: 'hypothesis-formulation' },
  { keywords: /\b(experiment.?design|design.?experiment|baseline.?selection|ablation.?plan)\b/i, skill: 'experiment-design' },
  { keywords: /\b(novelty|incremental|contribution.*compare)\b/i, skill: 'novelty-assessment' },
  { keywords: /\b(competing|scoop|concurrent.*work|check.*competition)\b/i, skill: 'competitive-check' },
  { keywords: /\b(claim.*evidence|evidence.*map|scope.*paper|over.?claim)\b/i, skill: 'claim-evidence-bridge' },
  { keywords: /\b(scaffold|project.*structure|pyproject)\b/i, skill: 'project-scaffold' },
  { keywords: /\b(data.*generat|synthetic.*data|build.*data|dataset.*construct)\b/i, skill: 'experiment-data-builder' },
  { keywords: /\b(model.*load|model.*surgery|activation.*extract|introspect)\b/i, skill: 'model-setup' },
  { keywords: /\b(metric.*implement|analytical.*reference|measurement|significance)\b/i, skill: 'measurement-implementation' },
  { keywords: /\b(sanity.*check|pre.?flight|validate.*setup|smoke.*test)\b/i, skill: 'setup-validation' },
  { keywords: /\b(slurm|sbatch|gpu.*hours?|cluster|compute.*plan)\b/i, skill: 'compute-planner' },
  { keywords: /\b(run.*matrix|experiment.*sweep|phase.*gate|submit.*jobs?)\b/i, skill: 'experiment-runner' },
  { keywords: /\b(aggregate.*results?|collect.*metrics?|collect.*results?)\b/i, skill: 'result-collector' },
  { keywords: /\b(contribution.*position|differentiat|reviewer.*objection)\b/i, skill: 'contribution-positioning' },
  { keywords: /\b(narrative|story.*construct|figure.*plan|paper.*blueprint)\b/i, skill: 'story-construction' },
  { keywords: /\b(figure.*produc|latex.*source|submission.*package|manuscript.*produc|camera.*ready)\b/i, skill: 'manuscript-production' },
  { keywords: /\b(experiment.*fail|results.*worse|not.*learning|underperform)\b/i, skill: 'failure-diagnosis' },
  { keywords: /\b(pivot|persevere|revise.*hypothes|update.*hypothes)\b/i, skill: 'hypothesis-revision' },
];

// Match skills
const matched = new Set();
for (const { keywords, skill } of KEYWORD_SKILL_MAP) {
  if (keywords.test(userPrompt)) matched.add(skill);
}

// Context-aware: Obsidian integration for bound repos
const binding = common.getProjectMemoryBinding(cwd);
const isResearch = common.promptLooksResearchRelated(userPrompt);

if (binding.bound && isResearch) {
  matched.add('obsidian-project-memory');
  if (/\b(zotero|collection|doi|arxiv)\b/i.test(userPrompt)) matched.add('zotero-obsidian-bridge');
  if (/\b(paper|literature|review|claim|evidence)\b/i.test(userPrompt)) matched.add('obsidian-literature-workflow');
}

// Output: minimal trigger hints only
const skills = [...matched];

if (skills.length === 0) {
  // No output — don't waste tokens
  console.log(`## Instruction: Forced Skill Activation (Mandatory)

Silently scan the user's request against available skills. Do NOT list every skill with Yes/No.

Available skills:

${''/* Skills are discoverable via Skill tool — no need to list them here */}
**Action**:
- If any skill matches → Activate via Skill tool, then output: "Activating: [skill-name] — [reason]"
- If no skill matches → Output: "No skills needed"
- Begin implementation only after activation is complete.
- When multiple skills match, activate all of them.
`);
} else {
  const hints = skills.map(s => `Activating: ${s}`).join('\n');
  const boundHint = binding.bound && isResearch
    ? `\nBound Obsidian repo: ${binding.projectId || 'unknown'}. Update daily note and project memory on research state changes.`
    : '';

  console.log(`## Instruction: Forced Skill Activation (Mandatory)

Silently scan the user's request against available skills. Do NOT list every skill with Yes/No.

Available skills:

${''/* Skills are discoverable via Skill tool */}
**Pre-matched skills (MUST activate these)**: ${skills.join(', ')}
These skills matched keywords in the user's prompt. You MUST activate them via Skill tool.
${boundHint}
**Action**:
- If any skill matches → Activate via Skill tool, then output: "Activating: [skill-name] — [reason]"
- If no skill matches → Output: "No skills needed"
- Begin implementation only after activation is complete.
- When multiple skills match, activate all of them.
`);
}

process.exit(0);
