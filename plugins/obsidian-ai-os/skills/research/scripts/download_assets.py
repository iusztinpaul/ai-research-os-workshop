# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28.1"]
# ///
"""Download all remote images referenced in a markdown file to the local assets dir.

Used during ingest to make raw sources self-contained — once images live on disk,
the LLM can `Read` them directly and links don't rot when the source URL goes
offline.

Behavior:
  - Scans the markdown file for image references in two forms:
      ![alt](https://example.com/img.png)
      <img src="https://example.com/img.png" ...>
  - Downloads each unique remote URL to <assets-dir>/img-NNN.<ext>.
  - Rewrites every reference in the markdown to the local relative path
    (relative to the markdown file's parent dir).
  - Leaves already-local references alone (anything not starting with
    http:// or https://).
  - Skips downloads that fail (logs them in the manifest, leaves the URL in
    place in the markdown so the user can decide what to do).

Output (printed as a single JSON line on stdout):
  {
    "markdown_path": "<path>",
    "assets_dir": "<path>",
    "downloaded": [
      {"url": "...", "local_path": "<assets_dir>/img-001.png", "bytes": 12345},
      ...
    ],
    "failed": [
      {"url": "...", "error": "..."},
      ...
    ]
  }

Usage:
  uv run --script scripts/download_assets.py \\
    --markdown /path/to/research-<topic>/raw/<slug>.md \\
    --assets-dir /path/to/research-<topic>/raw/assets/<slug>
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

# Markdown image syntax: ![alt](URL) or ![alt](URL "title")
MD_IMG_RE = re.compile(r'!\[([^\]]*)\]\(\s*([^\s)]+)(?:\s+"[^"]*")?\s*\)')

# HTML <img src="..."> (rare but happens in clipped articles)
HTML_IMG_RE = re.compile(r'<img\b[^>]*\bsrc\s*=\s*"([^"]+)"', re.IGNORECASE)

EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
}


def is_remote(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def collect_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in MD_IMG_RE.finditer(text):
        url = match.group(2).strip()
        if is_remote(url) and url not in seen:
            seen.add(url)
            urls.append(url)
    for match in HTML_IMG_RE.finditer(text):
        url = match.group(1).strip()
        if is_remote(url) and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def guess_extension(url: str, content_type: str | None) -> str:
    if content_type:
        ct = content_type.split(";", 1)[0].strip().lower()
        if ct in EXT_BY_CONTENT_TYPE:
            return EXT_BY_CONTENT_TYPE[ct]
        guessed = mimetypes.guess_extension(ct)
        if guessed:
            return guessed
    # Fall back to URL path extension.
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"}:
        return ".jpeg" if ext == ".jpeg" else ext
    return ".bin"


def next_index(assets_dir: Path) -> int:
    """Pick the next img-NNN index based on existing files."""
    max_n = 0
    pattern = re.compile(r"^img-(\d+)\.")
    if assets_dir.is_dir():
        for f in assets_dir.iterdir():
            m = pattern.match(f.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def download(url: str, dest: Path, client: httpx.Client) -> int:
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type")
        # Re-suffix dest if needed based on Content-Type.
        ext = guess_extension(url, content_type)
        if dest.suffix != ext:
            dest = dest.with_suffix(ext)
        size = 0
        with dest.open("wb") as f:
            for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                f.write(chunk)
                size += len(chunk)
    return size


def rewrite_markdown(text: str, url_to_local: dict[str, str]) -> str:
    def replace_md(match: re.Match) -> str:
        alt = match.group(1)
        url = match.group(2).strip()
        local = url_to_local.get(url)
        return f"![{alt}]({local})" if local else match.group(0)

    def replace_html(match: re.Match) -> str:
        url = match.group(1).strip()
        local = url_to_local.get(url)
        if not local:
            return match.group(0)
        return match.group(0).replace(url, local)

    text = MD_IMG_RE.sub(replace_md, text)
    text = HTML_IMG_RE.sub(replace_html, text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", required=True, help="Markdown file to scan + rewrite")
    parser.add_argument("--assets-dir", required=True, help="Where to save downloaded images")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout in seconds")
    args = parser.parse_args()

    md_path = Path(args.markdown)
    assets_dir = Path(args.assets_dir)
    if not md_path.is_file():
        raise SystemExit(f"markdown not found: {md_path}")
    assets_dir.mkdir(parents=True, exist_ok=True)

    text = md_path.read_text()
    urls = collect_urls(text)

    downloaded: list[dict] = []
    failed: list[dict] = []
    url_to_local: dict[str, str] = {}

    if urls:
        idx = next_index(assets_dir)
        with httpx.Client(
            timeout=args.timeout,
            follow_redirects=True,
            headers={"User-Agent": "research-asset-downloader/1.0"},
        ) as client:
            for url in urls:
                ext = guess_extension(url, None)
                dest = assets_dir / f"img-{idx:03d}{ext}"
                try:
                    size = download(url, dest, client)
                    # download() may have re-suffixed; find the actual file.
                    actual = dest if dest.exists() else next(f for f in assets_dir.iterdir() if f.stem == f"img-{idx:03d}")
                    rel = os.path.relpath(actual, md_path.parent)
                    url_to_local[url] = rel
                    downloaded.append({"url": url, "local_path": str(actual), "bytes": size})
                    idx += 1
                except Exception as exc:  # noqa: BLE001 — we want to log everything
                    failed.append({"url": url, "error": str(exc)})

        if url_to_local:
            new_text = rewrite_markdown(text, url_to_local)
            if new_text != text:
                md_path.write_text(new_text)

    print(
        json.dumps(
            {
                "markdown_path": str(md_path),
                "assets_dir": str(assets_dir),
                "downloaded": downloaded,
                "failed": failed,
            }
        )
    )


if __name__ == "__main__":
    main()
