"""Parse a blob of markdown text for GitHub file references and group them by module.

Used by `/research` when a GitHub repo URL is provided as a seed. Scans the
brain dump (and any linked markdown files) for file references against a specific
repo, and groups them by parent directory (the "module").

Inputs:
  --repo <url>      Required. The GitHub repo URL (with optional /tree/<branch>).
  --text <str>      Optional. A raw text blob to scan (e.g., the brain dump).
                    May be passed multiple times; contents are concatenated.
  --file <path>     Optional. A markdown file to read and scan. May be passed
                    multiple times. At least one of --text or --file must be
                    provided.
  --output <path>   Optional. Where to write the JSON output. Defaults to stdout.

Output JSON shape:
  {
    "repo_url":  "https://github.com/maximilien/weave-cli",
    "owner":     "maximilien",
    "repo":      "weave-cli",
    "branch":    "main",
    "modules": [
      {
        "module_path": "src/pkg/vectordb",
        "module_name": "vectordb",
        "files": [
          {
            "path": "src/pkg/vectordb/interfaces.go",
            "line_ranges": [[82, 97], [100, 115], [118, 142], [145, 157], [160, 172]]
          },
          ...
        ]
      },
      ...
    ]
  }

Supported reference forms:
  1. Markdown link with backticked path and repo-prefixed href:
       [`src/pkg/vectordb/interfaces.go`](weave-cli/src/pkg/vectordb/interfaces.go)
     Line ranges are taken from any `L<a>-<b>` or `L<a>` tokens that appear
     between this link and the next link on the same line.

  2. Direct GitHub URLs:
       https://github.com/<owner>/<repo>/blob/<branch>/<path>[#L<a>-L<b>]

  3. Brace-expansion in raw text (expanded to individual paths):
       src/pkg/vectordb/{weaviate,qdrant,milvus}/adapter.go

When the same file appears multiple times, line ranges are merged (unique,
order-preserving). When no references are found, `modules` is an empty list
and the orchestrator should fall back to global mode.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GITHUB_URL_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/\s)]+)/(?P<repo>[^/\s)#]+)"
    r"(?:/(?P<kind>tree|blob)/(?P<branch>[^/\s)]+)(?P<path>/[^\s)#]*)?)?"
    r"(?:#L(?P<l1>\d+)(?:-L?(?P<l2>\d+))?)?",
    re.IGNORECASE,
)

MARKDOWN_LINK_RE = re.compile(r"\[(?P<anchor>[^\]]+)\]\((?P<href>[^)\s]+)(?:\s+\"[^\"]*\")?\)")

LINE_RANGE_RE = re.compile(r"L(\d+)(?:[-–]L?(\d+))?")

BACKTICK_PATH_RE = re.compile(r"^`([^`]+)`$")

BRACE_EXPAND_RE = re.compile(r"([\w./\-]+)\{([^{}]+)\}([\w./\-]*)")


def parse_repo_url(repo_url: str) -> tuple[str, str, str]:
    """Return (owner, repo, branch) from a GitHub URL."""
    match = GITHUB_URL_RE.search(repo_url)
    if not match:
        raise SystemExit(f"not a recognizable GitHub URL: {repo_url}")
    owner = match.group("owner")
    repo = match.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]
    branch = match.group("branch") or "main"
    return owner, repo, branch


def strip_repo_prefix(path: str, owner: str, repo: str) -> str | None:
    """If path is prefixed with the repo slug or an absolute GitHub URL, strip it.

    Returns the repo-relative path, or None if the path doesn't clearly belong
    to the target repo.
    """
    path = path.strip()
    if not path:
        return None

    github_match = GITHUB_URL_RE.match(path)
    if github_match:
        if github_match.group("owner").lower() != owner.lower():
            return None
        matched_repo = github_match.group("repo")
        if matched_repo.endswith(".git"):
            matched_repo = matched_repo[:-4]
        if matched_repo.lower() != repo.lower():
            return None
        inner = github_match.group("path") or ""
        return inner.lstrip("/") or None

    prefix = f"{repo}/"
    if path.startswith(prefix):
        return path[len(prefix) :]

    if "://" in path:
        return None

    if "/" in path and not path.startswith("/"):
        return path

    return None


def looks_like_source_path(path: str) -> bool:
    """Filter: only accept paths that look like repo files (have an extension or dir)."""
    if not path:
        return False
    if path.endswith("/"):
        return False
    if "/" not in path and "." not in path:
        return False
    return True


def expand_brace(path: str) -> list[str]:
    """Expand `a/{b,c}/d` into `a/b/d`, `a/c/d`. Recursive for nested braces."""
    match = BRACE_EXPAND_RE.search(path)
    if not match:
        return [path]
    prefix, alts, suffix = match.group(1), match.group(2), match.group(3)
    results = []
    for alt in alts.split(","):
        alt = alt.strip()
        if "..." in alt or not alt:
            continue
        expanded = f"{prefix}{alt}{suffix}"
        tail = path[match.end() :]
        results.extend(expand_brace(expanded + tail))
    return results or [path]


def extract_line_ranges(segment: str) -> list[tuple[int, int]]:
    """Pull all L<a>-<b> or L<a> tokens from a text segment."""
    ranges: list[tuple[int, int]] = []
    for match in LINE_RANGE_RE.finditer(segment):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if end < start:
            start, end = end, start
        ranges.append((start, end))
    return ranges


def extract_path_from_link(anchor: str, href: str, owner: str, repo: str) -> str | None:
    """Pick the most reliable repo-relative path from a markdown link."""
    anchor_match = BACKTICK_PATH_RE.match(anchor.strip())
    if anchor_match:
        anchor_path = anchor_match.group(1).strip()
        if looks_like_source_path(anchor_path):
            return anchor_path

    stripped = strip_repo_prefix(href, owner, repo)
    if stripped and looks_like_source_path(stripped):
        return stripped

    return None


def scan_markdown_links(text: str, owner: str, repo: str) -> list[tuple[str, list[tuple[int, int]]]]:
    """For each line, walk markdown links and assign nearby L-ranges to each."""
    hits: list[tuple[str, list[tuple[int, int]]]] = []
    for line in text.splitlines():
        link_matches = list(MARKDOWN_LINK_RE.finditer(line))
        if not link_matches:
            continue
        for idx, match in enumerate(link_matches):
            path = extract_path_from_link(match.group("anchor"), match.group("href"), owner, repo)
            if not path:
                continue
            segment_start = match.end()
            segment_end = link_matches[idx + 1].start() if idx + 1 < len(link_matches) else len(line)
            ranges = extract_line_ranges(line[segment_start:segment_end])
            hits.append((path, ranges))
    return hits


def scan_bare_github_urls(text: str, owner: str, repo: str) -> list[tuple[str, list[tuple[int, int]]]]:
    """Pick up `https://github.com/<owner>/<repo>/blob/<branch>/<path>[#L..]` forms."""
    hits: list[tuple[str, list[tuple[int, int]]]] = []
    for match in GITHUB_URL_RE.finditer(text):
        if match.group("owner").lower() != owner.lower():
            continue
        if match.group("repo").lower() != repo.lower():
            continue
        if match.group("kind") != "blob":
            continue
        inner = (match.group("path") or "").lstrip("/")
        if not looks_like_source_path(inner):
            continue
        ranges: list[tuple[int, int]] = []
        if match.group("l1"):
            start = int(match.group("l1"))
            end = int(match.group("l2")) if match.group("l2") else start
            ranges.append((min(start, end), max(start, end)))
        hits.append((inner, ranges))
    return hits


def scan_brace_expansions(text: str, owner: str, repo: str) -> list[tuple[str, list[tuple[int, int]]]]:
    """Pick up `src/pkg/.../{a,b,c}/file.ext` paths from raw prose."""
    hits: list[tuple[str, list[tuple[int, int]]]] = []
    for line in text.splitlines():
        for match in BRACE_EXPAND_RE.finditer(line):
            raw = line[match.start() :]
            token_match = re.match(r"[\w./\-]+\{[^{}]+\}[\w./\-]*", raw)
            if not token_match:
                continue
            token = token_match.group(0)
            stripped = strip_repo_prefix(token, owner, repo) or token
            if not looks_like_source_path(stripped):
                continue
            for expanded in expand_brace(stripped):
                if looks_like_source_path(expanded):
                    hits.append((expanded, []))
    return hits


def merge_hits(
    hits: list[tuple[str, list[tuple[int, int]]]],
) -> dict[str, list[tuple[int, int]]]:
    """Dedupe by path, union line ranges order-preservingly."""
    merged: dict[str, list[tuple[int, int]]] = {}
    for path, ranges in hits:
        existing = merged.setdefault(path, [])
        for r in ranges:
            if r not in existing:
                existing.append(r)
    return merged


def group_by_module(files: dict[str, list[tuple[int, int]]]) -> list[dict]:
    """Group files by parent directory; module_name is the leaf dir."""
    modules: dict[str, list[dict]] = {}
    order: list[str] = []
    for path, ranges in files.items():
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        if parent not in modules:
            modules[parent] = []
            order.append(parent)
        modules[parent].append({"path": path, "line_ranges": [list(r) for r in ranges]})
    out = []
    for module_path in order:
        module_name = module_path.rsplit("/", 1)[-1] if module_path else "root"
        out.append(
            {
                "module_path": module_path,
                "module_name": module_name,
                "files": modules[module_path],
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if not args.text and not args.file:
        raise SystemExit("must provide at least one of --text or --file")

    owner, repo, branch = parse_repo_url(args.repo)

    blobs = list(args.text)
    for file_path in args.file:
        path = Path(file_path)
        if not path.exists():
            print(f"warn: file not found, skipping: {file_path}", file=sys.stderr)
            continue
        blobs.append(path.read_text())
    text = "\n".join(blobs)

    hits: list[tuple[str, list[tuple[int, int]]]] = []
    hits.extend(scan_markdown_links(text, owner, repo))
    hits.extend(scan_bare_github_urls(text, owner, repo))
    hits.extend(scan_brace_expansions(text, owner, repo))

    merged = merge_hits(hits)
    modules = group_by_module(merged)

    base_url = f"https://github.com/{owner}/{repo}"
    doc = {
        "repo_url": base_url,
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "modules": modules,
    }

    payload = json.dumps(doc, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n")
        print(f"wrote {args.output} ({len(modules)} modules, {sum(len(m['files']) for m in modules)} files)", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
