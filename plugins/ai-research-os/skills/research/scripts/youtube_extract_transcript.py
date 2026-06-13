# /// script
# requires-python = ">=3.12"
# dependencies = ["youtube-transcript-api>=1.2.0"]
# ///
"""Extract a public YouTube video's captions into research-ready markdown.

The script fetches available public YouTube captions/transcripts without an API
key, writes a durable markdown source for the research raw layer, and prints a
single JSON object with metadata for the builder/index pipeline.

Usage:
  uv run --script scripts/youtube_extract_transcript.py \\
    --url "https://www.youtube.com/watch?v=..." \\
    --output-md /path/to/research/raw/youtube-video.md \\
    --output-json /path/to/research/youtube-video.json
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from youtube_transcript_api import YouTubeTranscriptApi

DEFAULT_LANGUAGES = ("en", "en-US", "en-GB")
DEFAULT_TIMESTAMP_INTERVAL = 30

logger = logging.getLogger("youtube_extract_transcript")


@dataclass
class TranscriptSnippet:
    text: str
    start: float
    duration: float


@dataclass
class TranscriptResult:
    snippets: list[TranscriptSnippet]
    language: str | None
    language_code: str | None
    is_generated: bool | None


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)


def get_video_id(url: str) -> str | None:
    """Extract a YouTube video ID from common URL formats."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "youtube.com" in host:
        query_id = parse_qs(parsed.query).get("v", [None])[0]
        if query_id:
            return query_id

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1]

    if "youtu.be" in host:
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[0]

    return None


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def snippet_value(snippet: Any, field: str, default: Any = None) -> Any:
    if isinstance(snippet, dict):
        return snippet.get(field, default)
    return getattr(snippet, field, default)


def normalize_snippet(snippet: Any) -> TranscriptSnippet:
    return TranscriptSnippet(
        text=clean_text(str(snippet_value(snippet, "text", ""))),
        start=float(snippet_value(snippet, "start", 0.0) or 0.0),
        duration=float(snippet_value(snippet, "duration", 0.0) or 0.0),
    )


def fetch_transcript(video_id: str, languages: list[str], preserve_formatting: bool) -> TranscriptResult:
    """Fetch captions using the current youtube-transcript-api, with a legacy fallback."""
    api = YouTubeTranscriptApi()

    if hasattr(api, "fetch"):
        fetched = api.fetch(
            video_id,
            languages=languages,
            preserve_formatting=preserve_formatting,
        )
        snippets = [normalize_snippet(snippet) for snippet in fetched]
        return TranscriptResult(
            snippets=[snippet for snippet in snippets if snippet.text],
            language=getattr(fetched, "language", None),
            language_code=getattr(fetched, "language_code", None),
            is_generated=getattr(fetched, "is_generated", None),
        )

    raw_snippets = YouTubeTranscriptApi.get_transcript(  # type: ignore[attr-defined]
        video_id,
        languages=languages,
        preserve_formatting=preserve_formatting,
    )
    snippets = [normalize_snippet(snippet) for snippet in raw_snippets]
    return TranscriptResult(
        snippets=[snippet for snippet in snippets if snippet.text],
        language=None,
        language_code=languages[0] if languages else None,
        is_generated=None,
    )


def fetch_oembed_metadata(url: str) -> dict[str, str]:
    """Fetch lightweight public title/channel metadata without an API key."""
    endpoint = "https://www.youtube.com/oembed?" + urlencode({"url": url, "format": "json"})
    request = Request(endpoint, headers={"User-Agent": "ai-research-os/0.1"})
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        logger.debug("Could not fetch YouTube oEmbed metadata for %s: %s", url, exc)
        return {}

    return {
        "title": str(data.get("title") or "").strip(),
        "author_name": str(data.get("author_name") or "").strip(),
    }


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def transcript_chunks(snippets: list[TranscriptSnippet], timestamp_interval: int) -> list[tuple[int, list[TranscriptSnippet]]]:
    if timestamp_interval <= 0:
        timestamp_interval = DEFAULT_TIMESTAMP_INTERVAL

    chunks: list[tuple[int, list[TranscriptSnippet]]] = []
    current_bucket: int | None = None
    current_snippets: list[TranscriptSnippet] = []

    for snippet in sorted(snippets, key=lambda item: item.start):
        bucket = int(snippet.start // timestamp_interval) * timestamp_interval
        if current_bucket is None:
            current_bucket = bucket
        if bucket != current_bucket:
            chunks.append((current_bucket, current_snippets))
            current_bucket = bucket
            current_snippets = []
        current_snippets.append(snippet)

    if current_bucket is not None and current_snippets:
        chunks.append((current_bucket, current_snippets))

    return chunks


def first_excerpt(snippets: list[TranscriptSnippet], max_chars: int = 240) -> str:
    text = " ".join(snippet.text for snippet in snippets[:12])
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def build_markdown(
    *,
    url: str,
    video_id: str,
    title: str,
    channel: str | None,
    result: TranscriptResult,
    timestamp_interval: int,
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    language = result.language or "unknown"
    language_code = result.language_code or "unknown"
    generated_label = (
        "unknown"
        if result.is_generated is None
        else str(result.is_generated).lower()
    )

    metadata = [
        "<!--",
        "source_type: youtube",
        f"youtube_url: {url}",
        f"youtube_video_id: {video_id}",
        f"youtube_channel: {channel or 'unknown'}",
        "transcript_source: transcript_api",
        f"transcript_language: {language}",
        f"transcript_language_code: {language_code}",
        f"transcript_is_generated: {generated_label}",
        f"timestamp_interval_seconds: {timestamp_interval}",
        f"generated_at: {generated}",
        "-->",
        "",
    ]

    lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        "This raw source contains the public YouTube caption transcript. It is not an LLM summary and may omit visual-only context that is not spoken in the video.",
        "",
        "## Metadata",
        "",
        f"- URL: {url}",
        f"- Video ID: {video_id}",
        f"- Channel: {channel or 'unknown'}",
        f"- Transcript language: {language} ({language_code})",
        f"- Auto-generated captions: {generated_label}",
        f"- Snippets: {len(result.snippets)}",
        "",
        "## Transcript",
        "",
    ]

    for bucket_start, snippets in transcript_chunks(result.snippets, timestamp_interval):
        lines.append(f"### {format_timestamp(bucket_start)}")
        lines.append("")
        for snippet in snippets:
            lines.append(f"- [{format_timestamp(snippet.start)}] {snippet.text}")
        lines.append("")

    return "\n".join(metadata + lines).rstrip() + "\n"


def write_json(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_languages(raw: str) -> list[str]:
    return [language.strip() for language in raw.split(",") if language.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Public YouTube URL to process.")
    parser.add_argument("--output-md", required=True, help="Where to write the raw markdown source.")
    parser.add_argument("--output-json", default=None, help="Optional metadata JSON output path.")
    parser.add_argument(
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated transcript language preferences, ordered by priority.",
    )
    parser.add_argument(
        "--timestamp-interval",
        type=int,
        default=DEFAULT_TIMESTAMP_INTERVAL,
        help="Transcript heading interval in seconds.",
    )
    parser.add_argument("--preserve-formatting", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    url = args.url.strip()
    video_id = get_video_id(url)
    output_md = Path(args.output_md)
    output_json = Path(args.output_json) if args.output_json else None

    if video_id is None:
        payload = {
            "success": False,
            "url": url,
            "error": "URL is not a supported YouTube video URL.",
        }
        print(json.dumps(payload, sort_keys=True))
        write_json(output_json, payload)
        return 2

    start = time.monotonic()
    languages = parse_languages(args.languages)

    try:
        logger.info("Fetching YouTube transcript: %s", url)
        result = fetch_transcript(
            video_id=video_id,
            languages=languages,
            preserve_formatting=args.preserve_formatting,
        )
        if not result.snippets:
            raise RuntimeError("Transcript fetch succeeded but returned no text snippets.")
    except Exception as exc:
        payload = {
            "success": False,
            "url": url,
            "youtube_video_id": video_id,
            "transcript_source": "transcript_api",
            "requested_languages": languages,
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(json.dumps(payload, sort_keys=True))
        write_json(output_json, payload)
        return 1

    metadata = fetch_oembed_metadata(url)
    title = metadata.get("title") or f"YouTube video {video_id}"
    channel = metadata.get("author_name") or None

    markdown = build_markdown(
        url=url,
        video_id=video_id,
        title=title,
        channel=channel,
        result=result,
        timestamp_interval=args.timestamp_interval,
    )
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding="utf-8")

    elapsed = time.monotonic() - start
    payload = {
        "success": True,
        "url": url,
        "youtube_video_id": video_id,
        "title": title,
        "summary": f"YouTube caption transcript. First excerpt: {first_excerpt(result.snippets)}",
        "output_md": str(output_md),
        "uri_full": f"raw/{output_md.name}",
        "youtube_channel": channel,
        "transcript_source": "transcript_api",
        "transcript_language": result.language,
        "transcript_language_code": result.language_code,
        "transcript_is_generated": result.is_generated,
        "timestamps_available": True,
        "snippet_count": len(result.snippets),
        "elapsed_seconds": round(elapsed, 2),
    }

    print(json.dumps(payload, sort_keys=True))
    write_json(output_json, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
