#!/usr/bin/env bash
# Run project_kb.py with Python 3.10+. Prefers `uv` when available (works on hosts where `python3` is 3.6).
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
KB_PY="${SCRIPT_DIR}/project_kb.py"

if [[ ! -f "$KB_PY" ]]; then
  echo "project_kb_run.sh: missing ${KB_PY}" >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run --python 3.12 "$KB_PY" "$@"
fi

for py in python3.12 python3.11 python3.10 python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    exec "$py" "$KB_PY" "$@"
  fi
done

echo "project_kb_run.sh: need Python 3.10+ or uv (https://astral.sh/uv)." >&2
echo "Example: uv run --python 3.12 ${KB_PY} \"\$@\"" >&2
exit 1
