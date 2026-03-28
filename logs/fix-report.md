# Fix Report — Post-Diagnostic Issues

**Date**: 2026-03-28

## Summary

| # | Fix | Status | Notes |
|---|---|---|---|
| 1 | Python 3.10+ | ✅ Resolved | uv venv with Python 3.12.13 |
| 2 | ML dependencies | ✅ Resolved | All 84 packages installed via uv sync |
| 3 | Zotero MCP | ✅ Resolved | Installed via npm, fixed binary path in settings |
| 4 | Script compatibility | ✅ Resolved | Version check added, shebang correct |
| 5 | Git push auth | ✅ Resolved | credential.helper store configured |
| 6 | Hook paths | ✅ Verified | All 5 hooks exist and work correctly |
| 7 | .gitignore | ✅ Resolved | docs/ and logs/ unblocked, Python/ML artifacts added |
| 8 | experiment-state.json | ✅ Verified | Structure matches hook expectations, no conflict |
| 9 | Code validation | ✅ Resolved | All files compile, 14/14 tests pass |

## Detailed Results

### FIX 1: Python 3.10+ (CRITICAL)
- **Problem**: System Python 3.6.8, project requires 3.10+
- **Solution**: `uv venv --python 3.12 .venv` in `rag-lit-synthesis/`
- **Verified**: `python --version` → 3.12.13
- **No HPC modules needed** — uv manages its own Python installations

### FIX 2: ML Dependencies (CRITICAL)
- **Problem**: torch, transformers, faiss, etc. not installed
- **Solution**: Fixed pyproject.toml (added `[tool.hatch.build.targets.wheel]`), then `uv sync`
- **Verified**: All imports succeed. torch=2.11.0+cu130, transformers=5.4.0
- **Note**: CUDA=False on login node (expected), will work on GPU compute nodes

### FIX 3: Zotero MCP
- **Problem**: `zotero-mcp` binary not found
- **Solution**: `npm install -g zotero-mcp`. Binary is `zotero-mcp-server` (not `zotero-mcp`).
  Updated settings.local.json to use `node .../zotero-mcp/build/index.js`
- **Verified**: Package installed at `~/.nvm/versions/node/v24.14.1/lib/node_modules/zotero-mcp/`

### FIX 4: Script Compatibility
- **Problem**: pipeline_state.py had Python 3.10+ syntax (`str | None`, `required=True` in argparse)
- **Solution**: Already fixed in prior session. Added explicit version check at top of script.
- **Verified**: Runs on both system Python 3.6 and venv Python 3.12

### FIX 5: Git Push Authentication
- **Problem**: Push required manual token-in-URL workaround
- **Solution**: `git config --global credential.helper store` + wrote `~/.git-credentials`
- **Verified**: `git push --dry-run` succeeds without manual token
- **SSH**: Key exists (`~/.ssh/id_ecdsa`) but not registered on GitHub. Credential store is sufficient.
- **User action needed**: To use SSH instead, add the public key to GitHub:
  ```
  ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMOok5KPEZdnMW+qnXvXdM3H5wL5z3lQO9k5uI/66Me/A3g+355ZocsPD9wTVVYv/OI/ykqRnGFOeHpsd0oQt1Y= erimoldi@mgmt001
  ```

### FIX 6: Hook Paths
- **Problem**: Hooks pointed to `~/.claude/hooks/` (doesn't exist)
- **Status**: Already fixed in prior session (commit 40382f2). All paths use `process.cwd() + 'hooks/'`
- **Verified**: All 5 hooks tested and return valid JSON with `continue: true`

### FIX 7: .gitignore
- **Problem**: `docs/` and `logs/` were gitignored, blocking commits of QUICKSTART.md and diagnostic reports
- **Solution**: Removed `docs/` and `logs/` from .gitignore. Added Python artifacts (`__pycache__/`, `*.pyc`, `.venv/`), ML checkpoints (`*.pt`, `*.pth`, `*.safetensors`), and `.git-credentials`
- **Verified**: `git add docs/ logs/` works without `-f`

### FIX 8: experiment-state.json
- **Problem**: Potential conflict with session-start hook expectations
- **Status**: No conflict. Hook reads `project`, `iteration`, `max_iterations`, `status`, `active_hypothesis.summary` — all present in generated file. `pipeline-state.json` is separate.

### FIX 9: Code Validation
- **Problem**: Needed syntax and import verification
- **Solution**: `py_compile` on all files, integration test of metrics, wrote 14 unit tests
- **Verified**: All files compile, all tests pass (14/14)
