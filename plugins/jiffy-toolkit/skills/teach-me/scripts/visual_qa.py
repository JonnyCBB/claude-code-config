#!/usr/bin/env python3
"""
Visual QA screenshot capture for teach-me HTML pages.

Uses Playwright to render the HTML in headless Chromium and capture
screenshots at multiple levels: full page, per chapter, and per
SVG/canvas visualization. The screenshots are then reviewed by Claude
using the Read tool to detect visual defects.

Usage:
    python3 visual_qa.py <html_file> [options]

Options:
    --output-dir DIR    Directory for screenshots (default: /tmp/teach-me-qa)
    --width WIDTH       Viewport width (default: 1280)
    --help              Show this help message

Examples:
    python3 visual_qa.py ~/.claude/teach-me/adam-optimizer/index.html
    python3 visual_qa.py index.html --output-dir /tmp/my-qa --width 1440
"""

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def capture_screenshots(html_path, output_dir="/tmp/teach-me-qa", width=1280):
    """Capture full-page, per-chapter, and per-visualization screenshots."""
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}", file=sys.stderr)
        return False

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_url = f"file://{html_path}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.goto(file_url, wait_until="networkidle")
        # Allow GSAP/D3 to initialize and animations to reach rest state
        page.wait_for_timeout(2000)

        # 1. Full page screenshot
        full_path = output_dir / "full-page.png"
        page.screenshot(path=str(full_path), full_page=True)
        print(f"  Captured: {full_path}")

        # 2. Per-chapter screenshots (scroll each chapter into view)
        chapters = page.query_selector_all(
            ".chapter, [id^='concept-'], [id^='chapter-']"
        )
        for i, ch in enumerate(chapters):
            ch.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            ch_path = output_dir / f"chapter-{i}.png"
            page.screenshot(path=str(ch_path))
            print(f"  Captured: {ch_path}")

        # 3. Individual SVG/canvas visualization screenshots
        visuals = page.query_selector_all("svg, canvas, .animation-container")
        for i, v in enumerate(visuals):
            box = v.bounding_box()
            if box and box["width"] > 50 and box["height"] > 50:
                v.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                vis_path = output_dir / f"visual-{i}.png"
                v.screenshot(path=str(vis_path))
                print(f"  Captured: {vis_path}")

        browser.close()

    screenshots = sorted(output_dir.glob("*.png"))
    print(f"\n{len(screenshots)} screenshot(s) saved to {output_dir}/")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Capture visual QA screenshots of teach-me HTML pages"
    )
    parser.add_argument("html_file", help="Path to the teach-me HTML file")
    parser.add_argument(
        "--output-dir",
        default="/tmp/teach-me-qa",
        help="Output directory for screenshots (default: /tmp/teach-me-qa)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Viewport width in pixels (default: 1280)",
    )

    args = parser.parse_args()
    success = capture_screenshots(args.html_file, args.output_dir, args.width)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
