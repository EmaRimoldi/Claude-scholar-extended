#!/usr/bin/env python3
"""Launcher for project_kb: runs on Python 3.6+ so a clear error prints before 3.7+ syntax is parsed.

The full CLI lives in `_project_kb_impl.py` and is loaded only after Python 3.10+ is confirmed.
"""
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def main():
    if sys.version_info < (3, 10):
        here = Path(__file__).resolve()
        sys.stderr.write(
            "project_kb.py requires Python 3.10 or newer (found %s).\n"
            "Fix: install Python 3.10+, or run: uv run --python 3.12 %s <args>\n"
            "Or use: %s\n"
            % (
                sys.version.split()[0],
                here,
                here.parent / "project_kb_run.sh",
            )
        )
        sys.exit(1)

    impl = Path(__file__).resolve().parent / "_project_kb_impl.py"
    spec = spec_from_file_location("project_kb_impl", impl)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load %s" % (impl,))
    mod = module_from_spec(spec)
    # Register before exec_module so dataclasses / typing can resolve __module__
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.main()


if __name__ == "__main__":
    main()
