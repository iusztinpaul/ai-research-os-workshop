# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""Find broken [[wikilinks]] across every wiki page.

A wikilink is broken when it doesn't resolve to an existing file under the
research directory. Both `[[target]]` and `[[target.md]]` are tried.

Output (one JSON line on stdout):
  {
    "check": "broken-links",
    "research_dir": "<path>",
    "broken_count": <int>,
    "broken": [
      {"source_page": "wiki/sources/abc.md", "target": "wiki/concepts/foo", "occurrences": 2},
      ...
    ]
  }

External URLs (http://, https://) are ignored. Anchor-only links (#section)
are ignored — they're intra-document. Asset paths like `raw/assets/...` are
checked normally.

Usage: uv run --script scripts/lint_broken_links.py --research-dir <path>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from _lintlib import (
    extract_wikilinks,
    find_research_dir,
    iter_wiki_pages,
    normalize_link_target,
    resolve_in_research_dir,
)


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:"))


def is_anchor_only(target: str) -> bool:
    return target.startswith("#")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", required=True)
    args = parser.parse_args()

    research_dir = find_research_dir(Path(args.research_dir))
    pages = iter_wiki_pages(research_dir)

    # Per-page counter of broken targets (so multiple occurrences in one page
    # collapse into a single finding with a count).
    findings: list[dict] = []
    for page in pages:
        page_broken: Counter[str] = Counter()
        for raw_target in extract_wikilinks(page.body):
            if is_external(raw_target) or is_anchor_only(raw_target):
                continue
            target = normalize_link_target(raw_target)
            if not target:
                continue
            if resolve_in_research_dir(research_dir, target) is None:
                page_broken[target] += 1
        for target, count in page_broken.most_common():
            findings.append(
                {
                    "source_page": page.relpath,
                    "target": target,
                    "occurrences": count,
                }
            )

    # Stable ordering: by source_page, then target.
    findings.sort(key=lambda f: (f["source_page"], f["target"]))

    print(
        json.dumps(
            {
                "check": "broken-links",
                "research_dir": str(research_dir),
                "broken_count": len(findings),
                "broken": findings,
            }
        )
    )


if __name__ == "__main__":
    main()
