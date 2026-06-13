# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""Flag entity/concept page pairs with strong mutual references and no comparison page.

Two pages A and B are "mutually referenced" when A's body wikilinks B and B's
body wikilinks A. If both pages have such cross-references, AND
`wiki/comparisons/<a-slug>-vs-<b-slug>.md` (or the alphabetized variant) does
not exist, the pair is a candidate for a comparison page.

Output (one JSON line on stdout):
  {
    "check": "missing-comparisons",
    "research_dir": "<path>",
    "missing_count": <int>,
    "missing": [
      {"a": "wiki/concepts/bm25", "b": "wiki/concepts/hybrid-retrieval", "expected_path": "wiki/comparisons/bm25-vs-hybrid-retrieval.md"},
      ...
    ]
  }

Usage: uv run --script scripts/lint_missing_comparisons.py --research-dir <path>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _lintlib import (
    extract_wikilinks,
    find_research_dir,
    iter_wiki_pages,
    normalize_link_target,
    resolve_in_research_dir,
)

HUB_PREFIXES = ("wiki/entities/", "wiki/concepts/")


def is_hub_path(relpath: str) -> bool:
    return any(relpath.startswith(p) for p in HUB_PREFIXES) and relpath.endswith(".md")


def slug_of(relpath: str) -> str:
    """`wiki/entities/foo.md` -> `foo`."""
    name = Path(relpath).stem
    return name


def comparison_path_for(a_relpath: str, b_relpath: str) -> str:
    """Alphabetize the two slugs and produce the canonical comparison path."""
    a_slug = slug_of(a_relpath)
    b_slug = slug_of(b_relpath)
    first, second = sorted([a_slug, b_slug])
    return f"wiki/comparisons/{first}-vs-{second}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", required=True)
    args = parser.parse_args()

    research_dir = find_research_dir(Path(args.research_dir))
    pages = iter_wiki_pages(research_dir)

    # Build a map: hub_relpath (without .md) -> set of hub relpaths it wikilinks to.
    hub_pages = [p for p in pages if is_hub_path(p.relpath)]
    hub_keys = {p.relpath.removesuffix(".md") for p in hub_pages}

    refs: dict[str, set[str]] = {key: set() for key in hub_keys}
    for page in hub_pages:
        page_key = page.relpath.removesuffix(".md")
        for raw_target in extract_wikilinks(page.body):
            target = normalize_link_target(raw_target)
            if target in hub_keys and target != page_key:
                refs[page_key].add(target)

    # Find mutual pairs (a refs b AND b refs a).
    seen_pairs: set[tuple[str, str]] = set()
    missing: list[dict] = []
    for a_key, a_targets in refs.items():
        for b_key in a_targets:
            if a_key in refs.get(b_key, set()):
                pair = tuple(sorted([a_key, b_key]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                expected = comparison_path_for(pair[0] + ".md", pair[1] + ".md")
                if resolve_in_research_dir(research_dir, expected) is None:
                    missing.append(
                        {
                            "a": pair[0],
                            "b": pair[1],
                            "expected_path": expected + ".md",
                        }
                    )

    missing.sort(key=lambda m: (m["a"], m["b"]))

    print(
        json.dumps(
            {
                "check": "missing-comparisons",
                "research_dir": str(research_dir),
                "missing_count": len(missing),
                "missing": missing,
            }
        )
    )


if __name__ == "__main__":
    main()
