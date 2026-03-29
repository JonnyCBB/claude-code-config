#!/usr/bin/env python3
"""
Embed small media files as base64 data URIs in an HTML file.

Usage:
    python3 embed_media.py <html_file> [options]

Options:
    --max-size BYTES    Maximum file size to embed (default: 500000 = 500KB)
    --dry-run           Show what would be embedded without modifying the file
    --help              Show this help message

Examples:
    python3 embed_media.py index.html
    python3 embed_media.py index.html --max-size 200000
    python3 embed_media.py index.html --dry-run
"""

import argparse
import base64
import re
import sys
from pathlib import Path


MIME_TYPES = {
    ".gif": "image/gif",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".webm": "video/webm",
    ".mp4": "video/mp4",
}


def embed_media_in_html(html_path, max_size=500000, dry_run=False):
    """Scan HTML for media references and embed small files as base64."""
    html_path = Path(html_path)
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}", file=sys.stderr)
        return False

    html_dir = html_path.parent
    content = html_path.read_text()

    # Find img src and video/source src attributes pointing to local files
    patterns = [
        (r'(<img[^>]*\ssrc=")([^"]*media/[^"]+)(")', "img"),
        (r'(<source[^>]*\ssrc=")([^"]*media/[^"]+)(")', "source"),
    ]

    embedded_count = 0
    skipped_count = 0

    for pattern, _tag_type in patterns:
        def replace_match(match):
            nonlocal embedded_count, skipped_count
            prefix = match.group(1)
            src = match.group(2)
            suffix = match.group(3)

            file_path = html_dir / src
            if not file_path.exists():
                print(f"  Skip (not found): {src}")
                skipped_count += 1
                return match.group(0)

            file_size = file_path.stat().st_size
            ext = file_path.suffix.lower()
            mime = MIME_TYPES.get(ext)

            if mime is None:
                print(f"  Skip (unknown type): {src}")
                skipped_count += 1
                return match.group(0)

            if file_size > max_size:
                print(f"  Skip (too large {file_size:,} bytes): {src}")
                skipped_count += 1
                return match.group(0)

            if dry_run:
                print(f"  Would embed ({file_size:,} bytes): {src}")
                embedded_count += 1
                return match.group(0)

            # Read and encode
            data = file_path.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            data_uri = f"data:{mime};base64,{b64}"

            print(f"  Embedded ({file_size:,} bytes): {src}")
            embedded_count += 1
            return f"{prefix}{data_uri}{suffix}"

        content = re.sub(pattern, replace_match, content)

    if not dry_run and embedded_count > 0:
        html_path.write_text(content)

    action = "Would embed" if dry_run else "Embedded"
    print(f"\n{action}: {embedded_count} file(s), Skipped: {skipped_count} file(s)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Embed small media files as base64 data URIs in HTML"
    )
    parser.add_argument("html_file", help="Path to the HTML file")
    parser.add_argument(
        "--max-size",
        type=int,
        default=500000,
        help="Max file size in bytes to embed (default: 500000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be embedded without modifying",
    )

    args = parser.parse_args()
    success = embed_media_in_html(args.html_file, args.max_size, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
