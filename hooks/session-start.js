#!/usr/bin/env node
/**
 * SessionStart Hook: Display project status (cross-platform version)
 *
 * Event: SessionStart
 * Function: Display project status, Git info, todos, plugins, and commands at session start
 */

const path = require('path');
const os = require('os');
const fs = require('fs');

// Import shared utility library
const common = require('./hook-common');

// Import package manager detection
const { getPackageManager, getSelectionPrompt } = require('../scripts/lib/package-manager');

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

const cwd = input.cwd || process.cwd();
const projectName = path.basename(cwd);
const homeDir = os.homedir();
const binding = common.getProjectMemoryBinding(cwd);
const researchCandidate = common.detectResearchProject(cwd);

// Build output
let output = '';

// Session start info
output += `🚀 ${projectName} Session started\n`;
output += `▸ Time: ${common.formatDateTime()}\n`;
output += `▸ Directory: ${cwd}\n\n`;

// Git status
const gitInfo = common.getGitInfo(cwd);

if (gitInfo.is_repo) {
  output += `▸ Git branch: ${gitInfo.branch}\n\n`;

  if (gitInfo.has_changes) {
    output += `⚠️  Uncommitted changes (${gitInfo.changes_count} files):\n`;

    // Show change list (up to 5)
    const statusIcons = {
      'M': '📝',  // Modified
      'A': '➕',  // Added
      'D': '❌',  // Deleted
      'R': '🔄',  // Renamed
      '??': '❓'  // Untracked
    };

    for (let i = 0; i < Math.min(gitInfo.changes.length, 5); i++) {
      const change = gitInfo.changes[i];
      const status = change.substring(0, 2).trim();
      const file = change.substring(3).trim();

      const icon = statusIcons[status] || '•';
      output += `  ${icon} ${file}\n`;
    }

    if (gitInfo.changes_count > 5) {
      output += `  ... (${gitInfo.changes_count - 5} more files)\n`;
    }
  } else {
    output += `✅ Working directory clean\n`;
  }
  output += '\n';
} else {
  output += `▸ Git: Not a repository\n\n`;
}

if (binding.bound) {
  output += '🧠 Obsidian project memory: bound\n';
  output += `  - Project: ${binding.projectId || 'unknown'}\n`;
  output += `  - Status: ${binding.status || 'unknown'}\n`;
  output += `  - Auto-sync: ${binding.autoSync ? 'on' : 'off'}\n`;
  if (binding.vaultRoot) {
    output += `  - Vault root: ${binding.vaultRoot}\n`;
  }
  output += '  - Suggested commands: /obsidian-sync, /obsidian-note\n\n';
} else if (researchCandidate.candidate) {
  output += '🧠 Obsidian project memory: research repo candidate\n';
  output += `  - Detected markers: ${researchCandidate.markers.join(', ')}\n`;
  output += '  - Suggested command: /obsidian-init\n\n';
}

// Check for misplaced research documents in repo root
const RESEARCH_DOCS = [
  'literature-review.md', 'hypotheses.md', 'experiment-plan.md',
  'experiment-state.json', 'compute-plan.md', 'validation-report.md',
  'analysis-report.md', 'claim-evidence-map.md', 'contribution-positioning.md',
  'paper-blueprint.md', 'research-proposal.md', 'cluster-profile.json',
];
const misplacedDocs = RESEARCH_DOCS.filter(f => fs.existsSync(path.join(cwd, f)));
if (misplacedDocs.length > 0) {
  output += `⚠️  Research documents found in repo root (should be in projects/<name>/docs/):\n`;
  for (const doc of misplacedDocs) {
    output += `  - ${doc}\n`;
  }
  output += `  → Run: git mv <file> projects/<project-name>/docs/\n\n`;
}

// Pipeline orchestrator state detection
const pipelineStateFile = path.join(cwd, 'pipeline-state.json');
if (fs.existsSync(pipelineStateFile)) {
  try {
    const pState = JSON.parse(fs.readFileSync(pipelineStateFile, 'utf8'));
    const steps = pState.steps || {};
    const order = [
      'research-init', 'check-competition', 'design-experiments', 'scaffold',
      'build-data', 'setup-model', 'implement-metrics', 'validate-setup',
      'plan-compute', 'run-experiment', 'collect-results', 'analyze-results',
      'map-claims', 'position', 'story', 'produce-manuscript',
      'quality-review', 'compile-manuscript', 'rebuttal'
    ];
    const completed = order.filter(id => steps[id]?.status === 'completed').length;
    const skipped = order.filter(id => steps[id]?.status === 'skipped').length;
    const failed = order.filter(id => steps[id]?.status === 'failed').length;
    const total = order.length;
    const nextStep = order.find(id => ['pending', 'failed'].includes(steps[id]?.status));

    output += `🔄 Pipeline: ${completed}/${total} completed`;
    if (skipped > 0) output += `, ${skipped} skipped`;
    if (failed > 0) output += `, ${failed} failed`;
    output += '\n';
    if (nextStep) {
      output += `  → Next: ${steps[nextStep].command} — ${steps[nextStep].description}\n`;
      output += `  → Run /run-pipeline --resume to continue\n`;
    } else {
      output += `  → All steps done!\n`;
    }
    output += '\n';
  } catch {
    // Ignore parse errors
  }
}

// Experiment iteration loop state detection
const stateFile = path.join(cwd, 'experiment-state.json');
if (fs.existsSync(stateFile)) {
  try {
    const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    output += '🔬 Experiment iteration loop: active\n';
    output += `  - Project: ${state.project}\n`;
    output += `  - Iteration: ${state.iteration}/${state.max_iterations}\n`;
    output += `  - Hypothesis: ${state.active_hypothesis?.summary || 'unknown'}\n`;
    output += `  - Status: ${state.status}\n`;

    // Status-specific nudge
    const nudges = {
      'planned': '  → Ready to run experiments. Execute the plan in experiment-plan.md.',
      'running': '  → Experiments in progress. Run /analyze-results when done.',
      'analyzing': '  → Analysis in progress. Check analysis-output/ for results.',
      'diagnosing': '  → Diagnosis in progress. Review failure-diagnosis.md, then activate hypothesis-revision.',
      'revising': '  → Revision pending. Review hypotheses.md, then run /design-experiments for the next iteration.',
      'confirmed': '  → Hypothesis confirmed! Run /map-claims to prepare for writing.',
      'abandoned': '  → Research line abandoned. Consider running novelty-assessment for a new direction.'
    };
    output += (nudges[state.status] || '') + '\n';

    if (state.latest_analysis?.primary_result) {
      output += `  - Latest result: ${state.latest_analysis.primary_result}\n`;
    }
    if (state.resource_budget?.remaining_gpu_hours !== undefined) {
      output += `  - GPU budget remaining: ${state.resource_budget.remaining_gpu_hours}h\n`;
    }
    if (state.deadline) {
      output += `  - Deadline: ${state.deadline}\n`;
    }
    output += '\n';
  } catch {
    output += '🔬 Experiment state file found but unreadable\n\n';
  }
}

// Package manager detection
try {
  const pm = getPackageManager();
  output += `📦 Package manager: ${pm.name} (${pm.source})\n`;

  // If detected via fallback, suggest setup
  if (pm.source === 'fallback' || pm.source === 'default') {
    output += `💡 Run /setup-pm to configure preferred package manager\n`;
  }
} catch (err) {
  // Package manager detection failed, silently ignore
}

output += '\n';

// Todos
output += `📋 Todos:\n`;
const todoInfo = common.getTodoInfo(cwd);

if (todoInfo.found) {
  output += `  - ${todoInfo.pending} pending / ${todoInfo.done} completed\n`;

  // Show top 5 pending items
  if (fs.existsSync(todoInfo.path)) {
    try {
      const content = fs.readFileSync(todoInfo.path, 'utf8');
      const pendingItems = content.match(/^[\-\*] \[ \].+$/gm) || [];

      if (pendingItems.length > 0) {
        output += `\n  Recent todos:\n`;
        for (let i = 0; i < Math.min(5, pendingItems.length); i++) {
          const item = pendingItems[i].replace(/^[\-\*] \[ \]\s*/, '').substring(0, 60);
          output += `  - ${item}\n`;
        }
      }
    } catch {
      // Ignore errors
    }
  }
} else {
  output += `  No todo file found (TODO.md, docs/todo.md etc)\n`;
}

output += '\n';

// Enabled plugins
output += `🔌 Enabled plugins:\n`;
const enabledPlugins = common.getEnabledPlugins(homeDir);

if (enabledPlugins.length > 0) {
  for (let i = 0; i < Math.min(5, enabledPlugins.length); i++) {
    output += `  - ${enabledPlugins[i].name}\n`;
  }
  if (enabledPlugins.length > 5) {
    output += `  ... and ${enabledPlugins.length - 5} more plugins\n`;
  }
} else {
  output += `  None\n`;
}

output += '\n';

// Available commands
output += `💡 Available commands:\n`;
const availableCommands = common.getAvailableCommands(homeDir);

if (availableCommands.length > 0) {
  for (const cmd of availableCommands.slice(0, 5)) {
    const description = common.getCommandDescription(cmd.path) || `${cmd.plugin} command`;
    const truncatedDesc = description.length > 40 ? description.substring(0, 40) + '...' : description;
    output += `  /${cmd.name.padEnd(20)} ${truncatedDesc}\n`;
  }

  if (availableCommands.length > 5) {
    output += `  ... and ${availableCommands.length - 5} more commands, use /help to list all\n`;
  }
} else {
  output += `  No commands found\n`;
}

// Output JSON
const result = {
  continue: true,
  systemMessage: output
};

console.log(JSON.stringify(result));

process.exit(0);
