"""Deduplicate research subagent findings across one or more round-query JSON files.

Each input file has the shape:
    {"query": "...", "findings": [ {"original_path": "...", "summary": "...", ...}, ... ]}

Dedup key is `original_path`. When the same `original_path` appears in multiple findings,
the entry with the longest `summary` wins. Non-summary fields from the winning entry are
preserved verbatim.

Usage:
    uv run --script scripts/dedup_findings.py --inputs round1-q1.json round1-q2.json --output round1-deduped.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.inputs]
    findings = load_findings(input_paths)
    deduped = dedup(findings)

    Path(args.output).write_text(json.dumps({"findings": deduped}, indent=2))
    print(f"merged {len(findings)} findings from {len(input_paths)} files -> {len(deduped)} unique")


if __name__ == "__main__":
    main()
