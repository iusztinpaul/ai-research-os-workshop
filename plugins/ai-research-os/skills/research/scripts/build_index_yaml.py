# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""Build `index.yaml` for a research directory from discovery results + seed URI JSON.

Inputs:
  --results <path>    JSON of deduped, scored discovery findings, shape:
                      {"results": [ {...}, ... ]} (produced by
                      `dedup_findings.py --as-results`). Each result must already carry all
                      metadata fields (author, published_date, publication, source_url,
                      origin-specific fields) plus a numeric `relevance_score`. If a result
                      lacks `relevance_score` but carries the researcher's `relevance` tag,
                      it is derived here (high=0.8, medium=0.5, else 0.5) as a safety net.
  --seeds <path>      JSON with seed URIs (score 1.0, user-provided), shape:
                      {"seeds": [ {...}, ... ]}. Same field schema as results. Optional.
  --research-dir <p>  Research directory (e.g. working-dir/research-<slug>/).
                      Holds raw/, wiki/, and the emitted index.yaml. Used to resolve
                      the `wiki/` path for cross-checks; this script does NOT touch
                      the files themselves.
  --topic <str>       Research topic (the user's words).
  --input-summary <str>
                      1-2 sentence summary of the user's brain dump.
  --rounds <int>      Rounds completed.
  --output <path>     Where to write index.yaml (usually <research_dir>/index.yaml).
  --existing-index <path>
                      Prior index.yaml to merge on append runs. Its `sources` are
                      carried forward and unioned with the new seeds/results, deduped
                      by `original_path` (a freshly-ingested source supersedes the
                      stale entry). Omit on init runs. Reading happens fully in memory
                      before writing, so --output may point at the same file.

Behavior:
  - Seed URIs (score 1.0) come first.
  - Remaining sources (new results + carried-forward existing) sorted by
    `relevance_score` descending.
  - On append (--existing-index), prior sources are preserved unless superseded by a
    new source sharing the same `original_path`.
  - Emits a fixed schema regardless of which optional fields are null.
  - Null values stay as `null` in YAML (pyyaml default). Missing fields are filled
    with null so the output schema is stable.

Usage:
  uv run --script scripts/build_index_yaml.py \\
    --results discovery-results.json \\
    --seeds seed-uris.json \\
    --research-dir /path/to/research-topic \\
    --topic "Scaling vertical AI agents" \\
    --input-summary "How to distribute agent workloads with queues" \\
    --rounds 3 \\
    --output /path/to/research-topic/index.yaml
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Stable field order for `sources` entries. Fields absent on a given source get null.
BASE_FIELDS = [
    "uri_highlights",
    "uri_full",
    "uri_source_page",  # wiki/sources/<slug>.md — Layer 1.5 (extended LLM summary)
    "assets",  # list of paths under raw/assets/<slug>/ (images + original PDF)
    "original_path",
    "origin",
    "title",
    "authors",
    "published_date",
    "publication",
    "source_url",
    "relevance_score",
    "summary",
    "tags",
    "wiki_refs",  # list of wiki page paths that cite this source (populated by wiki_updater)
]

OPTIONAL_FIELDS = [
    "text_quality",  # pdf only — "high" | "low" (scanned PDFs without OCR)
    "readwise_location",  # readwise only
    "nlm_source_id",  # notebooklm only
    "nlm_notebook_id",  # notebooklm only
    "nlm_notebook_title",  # notebooklm only
    "nlm_content_type",  # notebooklm only
    "github_repo_url",  # github only
    "github_commit_sha",  # github only
    "github_branch",  # github only
    "github_files",  # github only (union of referenced paths across all module docs)
    "youtube_video_id",  # youtube only
    "youtube_url",  # youtube only
    "youtube_channel",  # youtube only
    "duration_seconds",  # youtube only
    "transcript_source",  # youtube only - transcript_api | manual
    "transcript_language",  # youtube only
    "transcript_language_code",  # youtube only
    "transcript_is_generated",  # youtube only
    "timestamps_available",  # youtube only
]


def normalize_authors(entry: dict) -> list[str]:
    """Convert `author` (string) or `authors` (list) into the canonical `authors` list."""
    if "authors" in entry and entry["authors"] is not None:
        authors = entry["authors"]
        return authors if isinstance(authors, list) else [authors]
    author = entry.get("author")
    if author is None:
        return []
    return [author] if isinstance(author, str) else list(author)


_LIST_FIELDS = {"assets", "wiki_refs"}

# Fallback map for results that carry the researcher's `relevance` tag but no numeric
# `relevance_score` (normally dedup_findings.py --as-results sets the score upstream).
_RELEVANCE_SCORES = {"high": 0.8, "medium": 0.5}
_DEFAULT_RELEVANCE_SCORE = 0.5


def resolve_relevance_score(entry: dict) -> float | None:
    """Use the numeric score if present; otherwise derive it from the `relevance` tag."""
    score = entry.get("relevance_score")
    if score is not None:
        return score
    if "relevance" in entry:
        return _RELEVANCE_SCORES.get(entry.get("relevance"), _DEFAULT_RELEVANCE_SCORE)
    return None


def normalize_source(entry: dict) -> dict:
    """Project a discovery-result or seed entry onto the index.yaml source schema."""
    out: dict[str, Any] = {}
    for field in BASE_FIELDS:
        if field == "authors":
            out[field] = normalize_authors(entry)
        elif field == "tags":
            out[field] = entry.get("tags", entry.get("key_concepts", []) or [])
        elif field == "relevance_score":
            out[field] = resolve_relevance_score(entry)
        elif field in _LIST_FIELDS:
            value = entry.get(field)
            out[field] = list(value) if isinstance(value, list) else []
        else:
            out[field] = entry.get(field)

    # Attach origin-specific optional fields only when the source carries them.
    for field in OPTIONAL_FIELDS:
        if field in entry and entry[field] is not None:
            out[field] = entry[field]

    return out


def load_existing_sources(existing_index_path: Path | None) -> list[dict]:
    """Load `sources` from a prior index.yaml for append runs. Empty if absent."""
    if existing_index_path is None or not existing_index_path.exists():
        return []
    doc = yaml.safe_load(existing_index_path.read_text()) or {}
    return doc.get("sources", []) or []


def load_sources(
    results_path: Path,
    seeds_path: Path | None,
    existing_index_path: Path | None = None,
) -> list[dict]:
    results = json.loads(results_path.read_text()).get("results", [])
    seeds = []
    if seeds_path is not None and seeds_path.exists():
        seeds = json.loads(seeds_path.read_text()).get("seeds", [])

    seed_rows = [normalize_source(s) for s in seeds]
    # Seeds always score 1.0 per the skill's rules; enforce it in case the input lied.
    for row in seed_rows:
        row["relevance_score"] = 1.0

    ranked_rows = [normalize_source(r) for r in results]

    # Carry forward sources from a prior index.yaml (append runs). A freshly-ingested
    # source — whether seed or ranked — supersedes the stale entry sharing its path.
    new_paths = {row.get("original_path") for row in seed_rows + ranked_rows if row.get("original_path")}
    carried_rows = [
        normalize_source(s)
        for s in load_existing_sources(existing_index_path)
        if s.get("original_path") not in new_paths
    ]

    # New ranked results join carried-forward existing sources, all sorted by score.
    # Stable sort keeps seeds (1.0) ahead of lower-scored carried sources; carried
    # sources that were themselves seeds (1.0) cluster just below this run's seeds.
    rest = ranked_rows + carried_rows
    rest.sort(key=lambda r: r.get("relevance_score") or 0.0, reverse=True)

    # De-dupe by original_path: a seed always wins over a ranked/carried row.
    seen = {row.get("original_path") for row in seed_rows if row.get("original_path")}
    rest = [r for r in rest if r.get("original_path") not in seen]

    return seed_rows + rest


def count_wiki_pages(wiki_dir: Path | None) -> int:
    """Count markdown files under wiki/ recursively. Returns 0 if dir is missing."""
    if wiki_dir is None or not wiki_dir.is_dir():
        return 0
    return sum(1 for p in wiki_dir.rglob("*.md") if p.is_file())


def build_doc(
    topic: str,
    input_summary: str,
    rounds: int,
    sources: list[dict],
    wiki_dir: Path | None = None,
    existing_created: str | None = None,
) -> dict:
    """Build the index.yaml document.

    `existing_created` preserves the original `created` timestamp on append runs
    (the orchestrator passes the previous value); on init it's None and we use now().
    `last_updated` is always set to now.
    """
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "topic": topic,
        "created": existing_created or now_iso,
        "last_updated": now_iso,
        "input_summary": input_summary,
        "rounds_completed": rounds,
        "total_sources": len(sources),
        "total_wiki_pages": count_wiki_pages(wiki_dir),
        "sources": sources,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, help="Deduped, scored discovery findings JSON ({'results': [...]}).")
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--research-dir", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--input-summary", required=True)
    parser.add_argument("--rounds", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--existing-created",
        default=None,
        help="ISO-8601 created timestamp from a prior index.yaml. Used on append runs to preserve the original created date.",
    )
    parser.add_argument(
        "--existing-index",
        default=None,
        help="Path to a prior index.yaml whose sources are merged on append runs (union by original_path; new sources win). Omit on init.",
    )
    args = parser.parse_args()

    research_dir = Path(args.research_dir)
    if not research_dir.is_dir():
        raise SystemExit(f"research-dir does not exist: {research_dir}")

    results_path = Path(args.results)
    seeds_path = Path(args.seeds) if args.seeds else None
    existing_index_path = Path(args.existing_index) if args.existing_index else None

    sources = load_sources(results_path, seeds_path, existing_index_path)
    doc = build_doc(
        args.topic,
        args.input_summary,
        args.rounds,
        sources,
        wiki_dir=research_dir / "wiki",
        existing_created=args.existing_created,
    )

    Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=1000))
    print(f"wrote {args.output} ({len(sources)} sources)")


if __name__ == "__main__":
    main()
