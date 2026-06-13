"""Shallow-clone a GitHub repo into a reusable cache dir and report its HEAD SHA.

The cache dir is shared across research runs so repos are cloned once and
updated in place. Returns a small JSON blob on stdout that the orchestrator
hands to the spec-writer subagents.

Inputs:
  --repo <url>       Required. GitHub URL (may include /tree/<branch>).
  --cache-dir <path> Optional. Explicit override of the cache location;
                     takes precedence over every other flag.
  --research-dir <path>
                     Optional. The research directory being built. The cache
                     is placed as a SIBLING of it — i.e. <research-dir>/../
                     .github-cache/ — so each research project keeps its
                     reusable clones next to its own folder. This is the
                     preferred way to locate the cache.
  --working-memory <path>
                     Optional legacy fallback used only when neither
                     --cache-dir nor --research-dir is given:
                     working-dir/.github-cache/.
  --branch <name>    Optional override for the branch. If omitted, takes the
                     branch from the repo URL (/tree/<branch>) or defaults
                     to `main`.

Output JSON shape (stdout):
  {
    "owner": "maximilien",
    "repo":  "weave-cli",
    "branch": "main",
    "clone_path": "/abs/path/<research-dir-parent>/.github-cache/maximilien-weave-cli",
    "commit_sha": "abcdef123...",
    "action": "cloned" | "updated" | "reused"
  }
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

GITHUB_URL_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/\s)]+)/(?P<repo>[^/\s)#]+)"
    r"(?:/(?:tree|blob)/(?P<branch>[^/\s)]+))?",
    re.IGNORECASE,
)


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def parse_repo_url(url: str, branch_override: str | None) -> tuple[str, str, str]:
    match = GITHUB_URL_RE.search(url)
    if not match:
        raise SystemExit(f"not a recognizable GitHub URL: {url}")
    owner = match.group("owner")
    repo = match.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]
    branch = branch_override or match.group("branch") or "main"
    return owner, repo, branch


def resolve_cache_dir(
    cache_dir: str | None,
    research_dir: str | None,
    working_memory: str | None,
) -> Path:
    """Locate the .github-cache root.

    Priority: explicit --cache-dir > sibling of --research-dir >
    legacy --working-memory > $PWD. Anchoring on the research dir's parent
    keeps each project's reusable clones next to its own research folder.
    """
    if cache_dir:
        return Path(cache_dir).expanduser().resolve()
    if research_dir:
        return Path(research_dir).expanduser().resolve().parent / ".github-cache"
    if working_memory:
        return Path(working_memory).expanduser().resolve() / ".github-cache"
    return Path.cwd() / ".github-cache"


def ensure_repo(clone_path: Path, clone_url: str, branch: str) -> str:
    """Clone if missing, else fetch+reset. Returns the action taken."""
    if clone_path.exists() and (clone_path / ".git").exists():
        try:
            run(["git", "fetch", "--depth=1", "origin", branch], cwd=clone_path)
            run(["git", "checkout", branch], cwd=clone_path)
            run(["git", "reset", "--hard", f"origin/{branch}"], cwd=clone_path)
            return "updated"
        except subprocess.CalledProcessError as err:
            print(
                f"warn: update failed ({err.stderr.strip()}), re-cloning",
                file=sys.stderr,
            )
            run(["rm", "-rf", str(clone_path)])

    clone_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "git",
            "clone",
            "--depth=1",
            "--branch",
            branch,
            clone_url,
            str(clone_path),
        ]
    )
    return "cloned"


def head_sha(clone_path: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], cwd=clone_path)
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--research-dir", default=None)
    parser.add_argument("--working-memory", default=None)
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()

    owner, repo, branch = parse_repo_url(args.repo, args.branch)
    cache_root = resolve_cache_dir(args.cache_dir, args.research_dir, args.working_memory)
    clone_path = cache_root / f"{owner}-{repo}"
    clone_url = f"https://github.com/{owner}/{repo}.git"

    action = ensure_repo(clone_path, clone_url, branch)
    sha = head_sha(clone_path)

    payload = {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "clone_path": str(clone_path),
        "commit_sha": sha,
        "action": action,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
