import os
import subprocess
import sys
from typing import Sequence

DEFAULT_JOBS = 4


def get_jobs(override: int | None = None) -> int:
    if override is not None:
        return max(1, int(override))
    # Default to a fixed JOBS value (4) for consistent performance
    return DEFAULT_JOBS


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

        # Ensure the repository hook file exists and is executable: we will *not* call
        # `pre-commit install --install-hooks`, which writes platform-provided wrappers
        # and could overwrite our single-file hook approach. Instead we keep a single
        # canonical hook file here and mark it executable.
        hook_path = os.path.join(hooks_dir, "pre-commit")
        if not os.path.exists(hook_path):
            # If our canonical hook doesn't exist for some reason, try to copy from the
            # repo root's .githooks/pre-commit (we assume the file in the repo is the source)
            repo_hook = os.path.join(os.getcwd(), ".githooks", "pre-commit")
            if os.path.exists(repo_hook) and repo_hook != hook_path:
                with open(repo_hook, "rb") as src, open(hook_path, "wb") as dst:
                    dst.write(src.read())
        # Make the hook executable.
        try:
            # POSIX chmod
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | 0o111)
        except Exception:
            # On Windows, set the executable bit in git index
            try:
                subprocess.check_call(["git", "update-index", "--add", "--chmod=+x", hook_path])
            except Exception:
                # If we cannot set exec bit, continue — developers may still run hooks
                pass
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
    # If the user passed a -j or --jobs in the forward args, prefer that
    override = None
    if args:
        for i, a in enumerate(args):
            if a == "-j" and i + 1 < len(args):
                try:
                    override = int(args[i + 1])
                except ValueError:
                    pass
            if a.startswith("--jobs="):
                try:
                    override = int(a.split("=", 1)[1])
                except ValueError:
                    pass
    jobs = get_jobs(override)
    cmd = [sys.executable, "-m", "pre_commit", "run", "--hook-stage", "pre-commit", "-j", str(jobs)] + args
    result = subprocess.run(cmd)
    return result.returncode


def dev_setup(_: None = None) -> int:
    """Install dev dependencies and register githooks

    This will run `python -m pip install -e .[dev]` and then configure the git
    hooks path and install pre-commit hooks.
    """
    # Ensure Node.js is installed and meets the minimum required version
    try:
        check_node_min_version = "24.11.1"
        node_ok = _check_node_version(check_node_min_version)
        if not node_ok:
            print(f"Node.js >= {check_node_min_version} is required to run Pyright pre-commit hooks.")
            print("Install Node.js or update to a recent version: https://nodejs.org/")
            return 1
    except Exception:
        # If anything goes wrong checking Node, warn and continue; this preserves existing dev-setup
        # behavior for environments that do not need Node, but we prefer to fail loudly so devs
        # are aware of missing tooling required for pre-commit pyright checks.
        print("Warning: Unable to verify Node.js installation. Pyright pre-commit hooks may fail.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    except subprocess.CalledProcessError as cpe:
        print("Failed to install dev dependencies:", file=sys.stderr)
        print(str(cpe), file=sys.stderr)
        return cpe.returncode
    # After installing dev deps, ensure repo-level hooks are registered
    code = install()
    if code != 0:
        return code
    # Run a quick pre-commit check to validate hooks; uses a default 4 jobs concurrency
    try:
        subprocess.check_call([sys.executable, "-m", "pre_commit", "run", "--all-files", "--show-diff-on-failure", "-j", str(DEFAULT_JOBS)])
    except subprocess.CalledProcessError as cpe:
        # Return non-zero if pre-commit failed
        return cpe.returncode
    return 0


def _check_node_version(min_version: str) -> bool:
    """Check that the installed Node.js version is >= specified min_version.

    Returns True if Node is installed and the version is >= min_version, otherwise False.
    """
    try:
        completed = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if completed.returncode != 0:
            return False
        version = completed.stdout.strip()
        # Node reports version as `v24.11.1`
        if version.startswith("v"):
            version = version[1:]
        # Parse numeric components
        v_parts = [int(p) for p in version.split(".") if p.isdigit() or p.lstrip("-").isdigit()]
        min_parts = [int(p) for p in min_version.split(".")]
        # Zero pad
        while len(v_parts) < len(min_parts):
            v_parts.append(0)
        for a, b in zip(v_parts, min_parts):
            if a > b:
                return True
            if a < b:
                return False
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


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
