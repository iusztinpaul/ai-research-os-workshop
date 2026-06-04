# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf>=1.24.0", "pymupdf4llm>=0.0.17"]
# ///
"""Extract a PDF to markdown + images for the research wiki pattern.

Behavior:
  - Reads <pdf-path>.
  - Writes markdown text to <output-md>.
  - Extracts all images to <assets-dir>/img-NNN.<ext> and rewrites image
    references in the markdown to local paths.
  - Copies the original PDF to <assets-dir>/original.pdf so the source is
    preserved in raw/assets/.
  - Detects scanned PDFs (no extractable text) and prints a JSON line with
    `text_quality: "low"`, so the caller can flag the source page accordingly.

Output (printed as a single JSON line on stdout):
  {
    "output_md": "<path>",
    "assets_dir": "<path>",
    "original_pdf": "<path>",
    "image_count": <int>,
    "page_count": <int>,
    "text_quality": "high" | "low",
    "extractor": "pymupdf4llm",
    "extractor_version": "<version>"
  }

Usage:
  uv run --script scripts/extract_pdf.py \\
    --pdf /path/to/source.pdf \\
    --output-md /path/to/research-<topic>/raw/<slug>.md \\
    --assets-dir /path/to/research-<topic>/raw/assets/<slug>
"""

from __future__ import annotations

import argparse
import json
import shutil
from importlib.metadata import version as _pkg_version
from pathlib import Path

import pymupdf
import pymupdf4llm

LOW_TEXT_THRESHOLD = 100  # chars per page; below this, treat as scanned/low-quality


def extract(pdf_path: Path, output_md: Path, assets_dir: Path) -> dict:
    assets_dir.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    # Preserve the original PDF alongside extracted assets.
    original_dest = assets_dir / "original.pdf"
    if pdf_path.resolve() != original_dest.resolve():
        shutil.copy2(pdf_path, original_dest)

    # pymupdf4llm.to_markdown writes images to write_images_path and returns markdown
    # with relative image references. We then rewrite refs to the assets_dir paths.
    md_text = pymupdf4llm.to_markdown(
        str(pdf_path),
        write_images=True,
        image_path=str(assets_dir),
        image_format="png",
        dpi=150,
    )

    # Count pages + assess text quality.
    with pymupdf.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        text_chars = sum(len(p.get_text("text") or "") for p in doc)
    avg_chars_per_page = (text_chars / page_count) if page_count else 0
    text_quality = "low" if avg_chars_per_page < LOW_TEXT_THRESHOLD else "high"

    # Count images extracted.
    image_files = sorted(p for p in assets_dir.iterdir() if p.is_file() and p.name != "original.pdf")
    # Rename images to a stable scheme (img-001.png, ...).
    for idx, img in enumerate(image_files, start=1):
        new_name = f"img-{idx:03d}{img.suffix.lower()}"
        new_path = assets_dir / new_name
        if img.name != new_name:
            # If a file with new_name already exists from a prior run, remove it.
            if new_path.exists():
                new_path.unlink()
            img.rename(new_path)
            # Rewrite all references in markdown (path or just basename).
            md_text = md_text.replace(img.name, new_name)
            md_text = md_text.replace(str(img), str(new_path))

    output_md.write_text(md_text)

    return {
        "output_md": str(output_md),
        "assets_dir": str(assets_dir),
        "original_pdf": str(original_dest),
        "image_count": len(image_files),
        "page_count": page_count,
        "text_quality": text_quality,
        "extractor": "pymupdf4llm",
        "extractor_version": _pkg_version("pymupdf4llm"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, help="Path to source PDF")
    parser.add_argument("--output-md", required=True, help="Where to write extracted markdown")
    parser.add_argument("--assets-dir", required=True, help="Where to write images + original.pdf")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    result = extract(pdf_path, Path(args.output_md), Path(args.assets_dir))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
