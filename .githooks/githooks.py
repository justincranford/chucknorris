#!/usr/bin/env python3
"""
Unified cross-platform githooks script.
- Default: run `pre-commit` for the pre-commit stage (concurrent jobs by CPU count)
- -i/--install: install hooks (set core.hooksPath to .githooks and run pre-commit install)
- -d/--dev-setup: install dev dependencies (pip install -e .[dev]) then install hooks

This script delegates actual implementation to the `githooks.hooks` package so that the
logic is importable by console scripts declared in pyproject.toml.
"""
from __future__ import annotations

import sys

from githooks.hooks import main

if __name__ == "__main__":
    sys.exit(main())
