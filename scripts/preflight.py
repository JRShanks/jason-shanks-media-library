#!/usr/bin/env python3
"""Preflight checks for scheduled media-library maintenance."""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "data/media_links.json",
    "data/media_watchlist.json",
    "scripts/build.py",
    "scripts/normalize.py",
]


def run(cmd, *, capture=True):
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=capture,
    )


def fail(message):
    print(f"ERROR: {message}")
    return 1


def main():
    parser = argparse.ArgumentParser(description="Check repo state before media cron edits.")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow an already-dirty worktree. Intended only for manual local runs.",
    )
    parser.add_argument(
        "--skip-push-check",
        action="store_true",
        help="Skip git push --dry-run auth check.",
    )
    args = parser.parse_args()

    for rel in REQUIRED_FILES:
        if not (REPO_ROOT / rel).exists():
            return fail(f"missing required file: {rel}")

    inside = run(["git", "rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return fail("not inside a git worktree")

    fetch = run(["git", "fetch", "origin"], capture=False)
    if fetch.returncode != 0:
        return fail("git fetch origin failed")

    branch = run(["git", "branch", "--show-current"])
    if branch.returncode != 0 or not branch.stdout.strip():
        return fail("could not determine current branch")
    current_branch = branch.stdout.strip()

    upstream = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream.returncode != 0:
        return fail(f"branch {current_branch} has no upstream")
    upstream_name = upstream.stdout.strip()
    if upstream_name != "origin/main":
        return fail(f"branch {current_branch} tracks {upstream_name}, expected origin/main")

    status = run(["git", "status", "--porcelain"])
    if status.returncode != 0:
        return fail("git status failed")
    if status.stdout.strip() and not args.allow_dirty:
        return fail("worktree is dirty")

    divergence = run(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"])
    if divergence.returncode != 0:
        return fail("could not compare HEAD with upstream")
    ahead, behind = [int(part) for part in divergence.stdout.strip().split()]
    if behind:
        return fail(f"local branch is behind origin/main by {behind} commit(s)")
    if ahead:
        return fail(f"local branch is ahead of origin/main by {ahead} commit(s)")

    remote = run(["git", "ls-remote", "--exit-code", "origin", "HEAD"])
    if remote.returncode != 0:
        return fail("git ls-remote origin HEAD failed")

    if not args.skip_push_check:
        dry_run = run(["git", "push", "--dry-run", "--porcelain", "origin", "HEAD:main"])
        if dry_run.returncode != 0:
            return fail("git push dry-run failed")

    print("Preflight ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
