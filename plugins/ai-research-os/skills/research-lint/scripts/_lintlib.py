"""Shared helpers for research-lint scripts.

Read-only utilities for parsing a v4 research directory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

# Obsidian wikilinks: [[target]] or [[target|label]] or [[target#anchor]] or [[target#anchor|label]]
WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]+)?(?:\|[^\]]+)?\]\]")

YAML_FENCE_RE = re.compile(r"^---\s*$", re.MULTILINE)


@dataclass
class WikiPage:
    path: Path
    relpath: str  # path relative to research_dir (e.g., "wiki/entities/foo.md")
    type: str | None  # from frontmatter `type:` field, if present
    body: str
    frontmatter: dict


def find_research_dir(path: Path) -> Path:
    """Validate and return research_dir. Raises SystemExit if invalid."""
    if not path.is_dir():
        raise SystemExit(f"research dir does not exist: {path}")
    if not (path / "index.yaml").is_file():
        raise SystemExit(f"index.yaml not found in {path}")
    if not (path / "wiki").is_dir():
        raise SystemExit(f"wiki/ not found in {path} — run scripts/migrate_layout.py first")
    return path


def load_index(research_dir: Path) -> dict:
    return yaml.safe_load((research_dir / "index.yaml").read_text()) or {}


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Empty dict if no frontmatter."""
    if not text.startswith("---"):
        return {}, text
    parts = YAML_FENCE_RE.split(text, maxsplit=2)
    # split on first '---' yields ['', fm_text, body_text]
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    body = parts[2].lstrip("\n")
    try:
        fm = yaml.safe_load(fm_text) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
    return fm, body


def iter_wiki_pages(research_dir: Path) -> list[WikiPage]:
    """Walk all .md files under wiki/ and parse frontmatter."""
    wiki_dir = research_dir / "wiki"
    pages: list[WikiPage] = []
    for f in sorted(wiki_dir.rglob("*.md")):
        if not f.is_file():
            continue
        relpath = str(f.relative_to(research_dir))
        text = f.read_text(errors="replace")
        fm, body = split_frontmatter(text)
        pages.append(
            WikiPage(
                path=f,
                relpath=relpath,
                type=fm.get("type"),
                body=body,
                frontmatter=fm,
            )
        )
    return pages


def extract_wikilinks(text: str) -> list[str]:
    """Return canonicalized wikilink targets from a page body. No anchors, no labels."""
    out: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        out.append(target)
    return out


def normalize_link_target(target: str) -> str:
    """Strip trailing .md and leading ./ from a wikilink target."""
    target = target.strip()
    if target.startswith("./"):
        target = target[2:]
    if target.endswith(".md"):
        target = target[:-3]
    return target


def resolve_in_research_dir(research_dir: Path, target: str) -> Path | None:
    """Try to resolve a wikilink target to a file under research_dir.

    Returns the resolved Path if the file exists, None otherwise. Tries the
    target both with and without .md.
    """
    target = normalize_link_target(target)
    candidates = [
        research_dir / f"{target}.md",
        research_dir / target,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None
