import os
import subprocess
import sys
from typing import Sequence


def get_jobs() -> int:
    return max(1, int(os.cpu_count() or 2))


def install(_: None = None) -> int:
    """Install repo-level git hooks into .githooks and configure the repo to use them

    This sets `core.hooksPath` to `.githooks` and calls `pre-commit install` to ensure
    pre-commit hooks are installed into the configured hooks path.
    Returns exit code (0 success, non-zero failure).
    """
    try:
        # Ensure .githooks exists
        hooks_dir = os.path.join(os.getcwd(), ".githooks")
        os.makedirs(hooks_dir, exist_ok=True)

        # Set the git hooks path for this repository
        subprocess.check_call(["git", "config", "--local", "core.hooksPath", ".githooks"])

        # Install pre-commit hooks into the current hooks path (pre-commit will use .git/hooks by default,
        # because we already set core.hooksPath, pre-commit will honor it)
        subprocess.check_call([sys.executable, "-m", "pre_commit", "install", "--install-hooks"])
    except subprocess.CalledProcessError as cpe:
        print("Failed to install hooks:", file=sys.stderr)
        print(str(cpe), file=sys.stderr)
        return cpe.returncode
    except Exception as e:
        print("Unexpected error installing hooks:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 1
    return 0


def run_pre_commit(args: Sequence[str] | None = None) -> int:
    args = list(args or [])
    cmd = [sys.executable, "-m", "pre_commit", "run", "--hook-stage", "pre-commit", "-j", str(get_jobs())] + args
    result = subprocess.run(cmd)
    return result.returncode


def dev_setup(_: None = None) -> int:
    """Install dev dependencies and register githooks

    This will run `python -m pip install -e .[dev]` and then configure the git
    hooks path and install pre-commit hooks.
    """
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    except subprocess.CalledProcessError as cpe:
        print("Failed to install dev dependencies:", file=sys.stderr)
        print(str(cpe), file=sys.stderr)
        return cpe.returncode
    # After installing dev deps, install hooks
    return install()


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    # Simple arg handling
    if not argv:
        return run_pre_commit()
    if argv[0] in ("-i", "--install"):
        return install()
    if argv[0] in ("-d", "--dev-setup"):
        return dev_setup()
    # otherwise forward args to pre-commit
    return run_pre_commit(argv)


if __name__ == "__main__":
    sys.exit(install())
