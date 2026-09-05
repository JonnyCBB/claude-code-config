#!/usr/bin/env python3
"""Real git repositories for tests.

No mocks: the worktree check shells out to git, so a fake would only test the
fake.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Ambient git config must not reach these repos. A global commit.gpgsign would
# break the commit under check=True, and a global excludesfile matching the
# scratch file would silently empty `git status --porcelain` and turn the dirty
# case green for the wrong reason.
_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="t",
    GIT_AUTHOR_EMAIL="t@example.invalid",
    GIT_COMMITTER_NAME="t",
    GIT_COMMITTER_EMAIL="t@example.invalid",
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_SYSTEM="/dev/null",
    GIT_TERMINAL_PROMPT="0",
)


def make_git_repo(directory, dirty=False, unpushed=False) -> Path:
    """A worktree with a real bare origin. Returns the working directory."""
    directory = Path(directory)
    work = directory / "work"
    origin = directory / "origin.git"
    work.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, env=_ENV)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True, env=_ENV)

    def run(*args):
        subprocess.run(
            ["git", "-C", str(work), *args], check=True, env=_ENV, capture_output=True
        )

    (work / "seed.txt").write_text("seed\n")
    run("add", "-A")
    run("commit", "-qm", "seed")
    run("remote", "add", "origin", str(origin))
    run("push", "-q", "origin", "main")
    if unpushed:
        (work / "later.txt").write_text("later\n")
        run("add", "-A")
        run("commit", "-qm", "unpushed")
    if dirty:
        (work / "scratch.txt").write_text("uncommitted\n")
    return work
