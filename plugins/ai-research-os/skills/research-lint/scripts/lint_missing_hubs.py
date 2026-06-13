# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""Find entity/concept slugs referenced ≥ 3 times across distinct source pages
that don't yet have a wiki page.

Looks for `[[wiki/entities/<slug>]]` and `[[wiki/concepts/<slug>]]` wikilinks
across `wiki/sources/*.md`. For each (type, slug) pair, counts the number of
distinct source pages that reference it. Flags those with count ≥ 3 where
the corresponding wiki page does not exist.

Threshold is 3 (not 2) because the wiki_page_writer already creates a page on
the ≥ 2 threshold during ingest. A missing hub at ≥ 3 means the wiki should
have caught it but didn't (e.g. ingest happened across multiple runs and the
page wasn't created), or the slug uses a non-canonical form across sources.

Output (one JSON line on stdout):
  {
    "check": "missing-hubs",
    "research_dir": "<path>",
    "missing_count": <int>,
    "missing": [
      {"type": "concept", "slug": "agent-loop", "mentioned_in": 4, "sample_sources": ["wiki/sources/abc.md", ...]},
      ...
    ]
  }

Usage: uv run --script scripts/lint_missing_hubs.py --research-dir <path>
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _lintlib import (
    extract_wikilinks,
    find_research_dir,
    iter_wiki_pages,
    normalize_link_target,
    resolve_in_research_dir,
)

THRESHOLD = 3


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", required=True)
    parser.add_argument("--threshold", type=int, default=THRESHOLD)
    args = parser.parse_args()

    research_dir = find_research_dir(Path(args.research_dir))
    pages = iter_wiki_pages(research_dir)

    # (type, slug) -> set of source page relpaths
    mentions: dict[tuple[str, str], set[str]] = defaultdict(set)

    for page in pages:
        if not page.relpath.startswith("wiki/sources/"):
            continue
        for raw_target in extract_wikilinks(page.body):
            target = normalize_link_target(raw_target)
            for prefix, type_name in (("wiki/entities/", "entity"), ("wiki/concepts/", "concept")):
                if target.startswith(prefix):
                    slug = target[len(prefix) :]
                    if slug:
                        mentions[(type_name, slug)].add(page.relpath)
                    break

    missing: list[dict] = []
    for (type_name, slug), source_pages in mentions.items():
        if len(source_pages) < args.threshold:
            continue
        if type_name == "entity":
            target_path = f"wiki/entities/{slug}"
        else:
            target_path = f"wiki/concepts/{slug}"
        if resolve_in_research_dir(research_dir, target_path) is None:
            sample = sorted(source_pages)[:3]
            missing.append(
                {
                    "type": type_name,
                    "slug": slug,
                    "mentioned_in": len(source_pages),
                    "sample_sources": sample,
                }
            )

    missing.sort(key=lambda m: -m["mentioned_in"])

    print(
        json.dumps(
            {
                "check": "missing-hubs",
                "research_dir": str(research_dir),
                "missing_count": len(missing),
                "missing": missing,
            }
        )
    )


if __name__ == "__main__":
    main()
