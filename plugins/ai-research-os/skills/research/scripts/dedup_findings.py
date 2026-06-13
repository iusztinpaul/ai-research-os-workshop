"""Deduplicate research subagent findings across one or more round-query JSON files.

Each input file has the shape:
    {"query": "...", "findings": [ {"original_path": "...", "summary": "...", ...}, ... ]}

Dedup key is `original_path`. When the same `original_path` appears in multiple findings,
the entry with the longest `summary` wins. Non-summary fields from the winning entry are
preserved verbatim.

With `--as-results`, the merged output is wrapped as `{"results": [...]}` (the shape
`build_index_yaml.py` consumes) and each finding gets a numeric `relevance_score` derived
from the researcher's `relevance` tag (`high → 0.8`, `medium → 0.5`, anything else → 0.5).
This replaces the old reranker pass: discovery findings are deduped and scored deterministically
instead of being re-read and re-scored by an LLM. Use it only on the final cross-round merge;
per-round calls keep the default `{"findings": [...]}` shape.

Usage:
    uv run --script scripts/dedup_findings.py --inputs round1-q1.json round1-q2.json --output round1-deduped.json
    uv run --script scripts/dedup_findings.py --inputs round-*-deduped.json --as-results --output discovery-results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Researcher `relevance` tag → numeric `relevance_score`. Seeds (1.0) are handled
# separately by build_index_yaml.py and never flow through here.
RELEVANCE_SCORES = {"high": 0.8, "medium": 0.5}
DEFAULT_SCORE = 0.5


def score_from_relevance(finding: dict) -> float:
    """Map the researcher's high/medium relevance tag to a numeric score."""
    return RELEVANCE_SCORES.get(finding.get("relevance"), DEFAULT_SCORE)


def load_findings(paths: list[Path]) -> list[dict]:
    findings: list[dict] = []
    for p in paths:
        data = json.loads(p.read_text())
        findings.extend(data.get("findings", []))
    return findings


def dedup(findings: list[dict]) -> list[dict]:
    by_path: dict[str, dict] = {}
    for f in findings:
        key = f.get("original_path")
        if not key:
            continue
        existing = by_path.get(key)
        if existing is None or len(f.get("summary", "") or "") > len(existing.get("summary", "") or ""):
            by_path[key] = f
    return list(by_path.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, help="Round-query JSON files to merge")
    parser.add_argument("--output", required=True, help="Deduped JSON output path")
    parser.add_argument(
        "--as-results",
        action="store_true",
        help="Wrap output as {'results': [...]} and add relevance_score from each finding's "
        "relevance tag (high=0.8, medium=0.5, else 0.5). Use on the final cross-round merge.",
    )
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.inputs]
    findings = load_findings(input_paths)
    deduped = dedup(findings)

    if args.as_results:
        for f in deduped:
            f["relevance_score"] = score_from_relevance(f)
        Path(args.output).write_text(json.dumps({"results": deduped}, indent=2))
        print(f"merged {len(findings)} findings from {len(input_paths)} files -> {len(deduped)} scored results")
    else:
        Path(args.output).write_text(json.dumps({"findings": deduped}, indent=2))
        print(f"merged {len(findings)} findings from {len(input_paths)} files -> {len(deduped)} unique")


if __name__ == "__main__":
    main()
