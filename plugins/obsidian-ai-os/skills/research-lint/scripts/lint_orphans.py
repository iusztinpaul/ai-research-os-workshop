# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""Find orphan sources — entries in index.yaml that no wiki page wikilinks back to.

A source is "orphan" when, for the source's `uri_full` (or `uri_highlights`)
filename and its `uri_source_page` (if set), no wiki page anywhere in `wiki/`
contains a `[[wikilink]]` pointing at it.

Output (one JSON line on stdout):
  {
    "check": "orphans",
    "research_dir": "<path>",
    "total_sources": <int>,
    "orphan_count": <int>,
    "orphans": [
      {"title": "...", "origin": "...", "score": 0.85, "uri_full": "raw/..."},
      ...
    ]
  }

Usage: uv run --script scripts/lint_orphans.py --research-dir <path>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _lintlib import (
    extract_wikilinks,
    find_research_dir,
    iter_wiki_pages,
    load_index,
    normalize_link_target,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", required=True)
    args = parser.parse_args()

    research_dir = find_research_dir(Path(args.research_dir))
    doc = load_index(research_dir)
    sources = doc.get("sources") or []
    pages = iter_wiki_pages(research_dir)

    # Build the set of all wikilink targets across the wiki, normalized.
    all_targets: set[str] = set()
    for page in pages:
        for raw_target in extract_wikilinks(page.body):
            all_targets.add(normalize_link_target(raw_target))

    orphans = []
    for src in sources:
        # Candidate targets that would indicate this source is referenced.
        candidates: list[str] = []
        for field in ("uri_full", "uri_highlights", "uri_source_page"):
            value = src.get(field)
            if value:
                candidates.append(normalize_link_target(value))
        if not candidates:
            continue  # No file => can't be orphan in the wiki sense; skip.
        if not any(c in all_targets for c in candidates):
            orphans.append(
                {
                    "title": src.get("title"),
                    "origin": src.get("origin"),
                    "score": src.get("relevance_score"),
                    "uri_full": src.get("uri_full"),
                    "uri_source_page": src.get("uri_source_page"),
                }
            )

    # Sort orphans by score descending so the most-relevant orphans surface first.
    orphans.sort(key=lambda o: -(o.get("score") or 0.0))

    print(
        json.dumps(
            {
                "check": "orphans",
                "research_dir": str(research_dir),
                "total_sources": len(sources),
                "orphan_count": len(orphans),
                "orphans": orphans,
            }
        )
    )


if __name__ == "__main__":
    main()
