#!/usr/bin/env python3
"""
Screenshot capture script for markdown and Google Docs visual comparison.

Uses Playwright to:
1. Render markdown as HTML with Google Docs-like styling
2. Capture screenshot of rendered markdown
3. Capture screenshot of Google Doc (requires authentication)
"""

import argparse
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess


def render_markdown_to_html(markdown_path):
    """
    Converts markdown to HTML using Python's markdown library.
    Falls back to reading raw markdown if markdown library not available.
    """
    try:
        from markdown_it import MarkdownIt

        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()

        md = MarkdownIt('commonmark', {'breaks': True, 'html': True})
        html_body = md.render(markdown_text)

    except ImportError:
        # Fallback: Use pandoc if markdown-it not available
        print("Warning: markdown-it-py not installed, using pandoc for conversion")
        result = subprocess.run(
            ['pandoc', str(markdown_path), '-t', 'html'],
            capture_output=True,
            text=True,
            check=True
        )
        html_body = result.stdout

    # Create full HTML with Google Docs-like styling
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Proxima Nova', Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: white;
        }}
        h1 {{
            font-size: 24pt;
            font-weight: bold;
            margin-top: 24px;
            margin-bottom: 12px;
        }}
        h2 {{
            font-size: 18pt;
            font-weight: bold;
            margin-top: 18px;
            margin-bottom: 10px;
        }}
        h3 {{
            font-size: 14pt;
            font-weight: bold;
            margin-top: 14px;
            margin-bottom: 8px;
        }}
        code {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 12px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #e6e6e6;
            font-weight: bold;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            padding-left: 16px;
            margin-left: 0;
            font-style: italic;
            color: #666;
        }}
        ul, ol {{
            margin: 12px 0;
            padding-left: 24px;
        }}
        li {{
            margin: 6px 0;
        }}
    </style>
</head>
<body>{html_body}</body>
</html>"""

    return full_html


def capture_markdown_screenshot(markdown_path, output_path):
    """Renders markdown as HTML and captures screenshot."""
    print(f"Rendering markdown: {markdown_path}")
    html_content = render_markdown_to_html(markdown_path)

    print("Capturing markdown screenshot...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 800})
        page.set_content(html_content)
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(output_path), full_page=True)
        browser.close()

    print(f"✓ Saved markdown screenshot: {output_path}")


def capture_gdoc_screenshot(gdoc_url, output_path):
    """Captures screenshot of Google Doc (requires browser auth)."""
    print(f"Capturing Google Doc screenshot: {gdoc_url}")

    with sync_playwright() as p:
        # Use persistent context to access existing Google auth cookies
        user_data_dir = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'

        try:
            context = p.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=False,  # Must be non-headless to use persistent context
                viewport={'width': 1200, 'height': 800}
            )
            page = context.pages[0] if context.pages else context.new_page()

            page.goto(gdoc_url)
            page.wait_for_load_state('networkidle')

            # Wait for Google Docs editor to load
            page.wait_for_selector('.kix-page', timeout=30000)

            page.screenshot(path=str(output_path), full_page=True)
            context.close()

            print(f"✓ Saved Google Doc screenshot: {output_path}")

        except Exception as e:
            print(f"Error capturing Google Doc screenshot: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure you're logged into Google in Chrome")
            print("2. Open the Google Doc URL in Chrome first to verify access")
            print("3. Check that the document URL is correct")
            raise


def main():
    parser = argparse.ArgumentParser(
        description='Capture screenshots of rendered markdown and Google Docs for visual comparison'
    )
    parser.add_argument('--markdown', required=True, help='Path to markdown file')
    parser.add_argument('--gdoc-url', required=True, help='Google Doc URL')
    parser.add_argument('--output-dir', required=True, help='Output directory for screenshots')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Capture screenshots
    markdown_screenshot = output_dir / 'markdown.png'
    gdoc_screenshot = output_dir / 'gdoc.png'

    try:
        capture_markdown_screenshot(args.markdown, markdown_screenshot)
        capture_gdoc_screenshot(args.gdoc_url, gdoc_screenshot)

        print("\n✓ Screenshot capture complete!")
        print(f"  Markdown: {markdown_screenshot}")
        print(f"  Google Doc: {gdoc_screenshot}")

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
