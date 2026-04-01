#!/usr/bin/env python3
"""
Ensure every Claude Code slash command under commands/ has a matching skill shim under skills/<name>/.

Some Claude Code builds resolve slash commands via the Skill tool; without skills/<name>/SKILL.md
the client reports "Unknown skill: <name>".

This script creates minimal delegation stubs (marked command_shim: true). It never overwrites
existing SKILL.md files that are not shims (e.g. full skills like experiment-design).

Usage:
  python3 scripts/sync_command_skill_shims.py           # create missing shims
  python3 scripts/sync_command_skill_shims.py --check   # exit 1 if any command lacks a shim
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_frontmatter_name(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            raw = line[5:].strip()
            if raw.startswith('"') and raw.endswith('"'):
                return raw[1:-1]
            if raw.startswith("'") and raw.endswith("'"):
                return raw[1:-1]
            return raw
    return None


def is_command_shim(skill_md: Path) -> bool:
    try:
        content = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if "command_shim: true" in content[:800]:
        return True
    return "<!-- command-skill-shim" in content


def stub_body(name: str, rel_cmd: str) -> str:
    return f"""---
name: {name}
description: Slash-command shim for /{name}. Delegates to commands/{rel_cmd}; use when the client resolves this command via the Skill tool.
version: 0.1.0
tags: [SlashCommand, ClaudeCode, ALETHEIA]
command_shim: true
---

# /{name} (command shim)

This skill exists so Claude Code can resolve **`/{name}`** when slash commands are routed through the Skill tool.

**Do this:** Read and follow **`commands/{rel_cmd}`** at the repository root (or **`~/.claude/commands/{Path(rel_cmd).name}`** after `bash scripts/setup.sh`), then execute that specification.

<!-- command-skill-shim generated; safe to regenerate with scripts/sync_command_skill_shims.py -->
"""


def collect_commands(commands_dir: Path) -> list[tuple[str, str]]:
    """List of (name, relative path under commands/)."""
    out: list[tuple[str, str]] = []
    for md in sorted(commands_dir.rglob("*.md")):
        rel = md.relative_to(commands_dir).as_posix()
        text = md.read_text(encoding="utf-8", errors="replace")
        name = parse_frontmatter_name(text)
        if not name:
            continue
        out.append((name, rel))
    return out


def skill_dir_for_name(skills_root: Path, name: str) -> Path:
    # Directory name must match how skills are stored; use exact `name` (colons OK on Linux/macOS).
    return skills_root / name


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Fail if any command is missing a shim")
    args = ap.parse_args()

    root = repo_root()
    commands_dir = root / "commands"
    skills_root = root / "skills"

    if not commands_dir.is_dir():
        print("ERROR: commands/ not found", file=sys.stderr)
        return 2

    pairs = collect_commands(commands_dir)
    missing: list[str] = []
    created = 0
    skipped_protected = 0

    for name, rel in pairs:
        sdir = skill_dir_for_name(skills_root, name)
        smd = sdir / "SKILL.md"
        if smd.is_file():
            if is_command_shim(smd):
                pass  # shim exists
            else:
                skipped_protected += 1
            continue
        missing.append(name)
        if args.check:
            continue
        sdir.mkdir(parents=True, exist_ok=True)
        smd.write_text(stub_body(name, rel), encoding="utf-8")
        created += 1
        print(f"+ {name} -> skills/{name}/SKILL.md")

    if args.check:
        if missing:
            print("Missing skill shims for commands:", ", ".join(missing), file=sys.stderr)
            print("Run: python3 scripts/sync_command_skill_shims.py", file=sys.stderr)
            return 1
        print("OK: every command has a skill directory with SKILL.md")
        return 0

    print(
        f"Done. Created {created} shims; "
        f"skipped {skipped_protected} existing non-shim skills; "
        f"total commands with names: {len(pairs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
