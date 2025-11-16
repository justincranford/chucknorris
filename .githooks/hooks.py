#!/usr/bin/env python
"""
Shell-executable wrapper that imports and executes the install function from the
`githooks.hooks` package. This allows contributors to run `.githooks/hooks.py` as a
standalone executable script while keeping the importable code inside `githooks/`.
"""
import sys

from githooks.hooks import install

if __name__ == "__main__":
    sys.exit(install())
