#!/usr/bin/env node
/**
 * Research Document Guard Hook
 *
 * Event: PostToolUse (Write, Edit)
 * Function: Warns when research documents are written to the repo root
 *           instead of inside projects/<name>/docs/
 */

const path = require('path');
const fs = require('fs');

// Known research document patterns that should live in projects/<name>/docs/
const RESEARCH_DOC_PATTERNS = [
  'literature-review.md',
  'hypotheses.md',
  'experiment-plan.md',
  'experiment-state.json',
  'compute-plan.md',
  'validation-report.md',
  'analysis-report.md',
  'claim-evidence-map.md',
  'contribution-positioning.md',
  'paper-blueprint.md',
  'research-proposal.md',
  'references.bib',
  'cluster-profile.json',
];

let input = {};
try {
  const stdinData = fs.readFileSync(0, 'utf8');
  if (stdinData.trim()) {
    input = JSON.parse(stdinData);
  }
} catch {
  process.exit(0);
}

const cwd = input.cwd || process.cwd();

// Check if the tool wrote a file to the repo root
const toolInput = input.tool_input || {};
const filePath = toolInput.file_path || toolInput.path || '';

if (!filePath) {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}

const fileName = path.basename(filePath);
const fileDir = path.dirname(path.resolve(filePath));
const repoRoot = path.resolve(cwd);

// Check: is a research doc being written to the repo root?
const isRepoRoot = fileDir === repoRoot;
const isResearchDoc = RESEARCH_DOC_PATTERNS.includes(fileName);

if (isRepoRoot && isResearchDoc) {
  // Find the active project_dir from pipeline-state.json
  let projectDir = 'projects/<project-name>';
  try {
    const statePath = path.join(cwd, 'pipeline-state.json');
    if (fs.existsSync(statePath)) {
      const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
      if (state.project_dir) {
        projectDir = state.project_dir;
      }
    }
  } catch {
    // ignore
  }

  const suggestedPath = path.join(projectDir, 'docs', fileName);
  const message =
    `⚠️  Research document "${fileName}" is being written to the repo root.\n` +
    `   It should be in: ${suggestedPath}\n` +
    `   Read pipeline-state.json → project_dir to find the correct output directory.`;

  console.log(JSON.stringify({
    continue: true,
    systemMessage: message,
  }));
  process.exit(0);
}

console.log(JSON.stringify({ continue: true }));
process.exit(0);
