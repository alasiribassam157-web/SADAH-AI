"""What a trained version records about how it was made, so a run can be reproduced and audited."""
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def data_fingerprint(pairs: list[tuple[str, int]]) -> str:
    """sha256 of the exact (text, label) training pairs, in order: same fingerprint = same training data."""
    digest = hashlib.sha256()
    for text, label in pairs:
        digest.update(f"{label}\t{text}\n".encode("utf-8"))
    return digest.hexdigest()


def git_commit() -> str:
    """Short commit of the code that trained the brain ('' outside a git checkout; '+dirty' if uncommitted)."""
    try:
        run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        commit = run("rev-parse", "--short", "HEAD")
        return commit + ("+dirty" if commit and run("status", "--porcelain", "--", "core", "agent", "agents") else "")
    except (OSError, subprocess.SubprocessError):
        return ""
