import os
import subprocess
import sys


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


if __name__ == "__main__":
    sys.exit(install())
