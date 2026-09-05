#!/usr/bin/env python3
"""
Visual QA Pipeline — 8-stage Playwright data collection for skill HTML files.

Usage:
    python visual_qa.py <html_file> [--skill teach-me|frontend-slides] [--output-dir DIR]

Options:
    html_file       Path to the HTML file to analyze
    --skill         Skill profile to use (default: teach-me)
    --output-dir    Directory for QA output (default: /tmp/teach-me-qa)

Examples:
    python visual_qa.py output.html
    python visual_qa.py slides.html --skill frontend-slides --output-dir /tmp/slides-qa
"""

import argparse
import re
import contextlib
import http.server
import json
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


try:
    from axe_playwright_python.sync_playwright import Axe

    AXE_AVAILABLE = True
except ImportError:
    AXE_AVAILABLE = False


SKILL_CONFIGS = {
    "teach-me": {
        "section_selectors": [
            ".chapter",
            "[id^='concept-']",
            "[id^='chapter-']",
        ],
        "interaction_targets": [
            "button.play",
            "button.pause",
            ".speed-control",
            ".sidebar a",
            ".theme-toggle",
        ],
    },
    # The `explain` skill produces static briefings, not interactive pages, so only two
    # of the eight stages carry signal here: `screenshots` (three viewports plus one shot
    # per figure, which is how mis-coloured diagram elements, orphaned SVG labels and
    # wrapped grid cells get caught) and `console_errors` (a broken inline script).
    # `interactions`, `keyboard_nav` and `overlap` will report PASSES THAT MEAN NOTHING,
    # because stage_overlap only queries interactive elements and a briefing has almost
    # none. Read this profile's report as diagnostic, never as a gate, and do not infer
    # from a green run that the layout was checked.
    #
    # Two measured specifics, so nobody re-derives them:
    #   - On a real briefing, `overlap` returned status "pass" with ZERO boxes examined.
    #     That is the vacuous pass, observed rather than predicted.
    #   - `interactions` returned a stage-level "pass" while its only recorded item held
    #     status "error": clicking the skip link times out with "element is outside of the
    #     viewport". That is a HARNESS FALSE POSITIVE, not a defect - a skip link is
    #     supposed to sit at left:-9999px until focused, which is exactly why Playwright
    #     cannot click it. Do not "fix" the document to satisfy it.
    #
    # Selectors are deliberately semantic HTML rather than class names: the skill mandates
    # a structure but leaves the design entirely free, so any theme-specific selector
    # would silently match nothing on the next document.
    "explain": {
        "section_selectors": [
            "figure",
            "table",
        ],
        "interaction_targets": [
            "a[href^='#']",
        ],
    },
    "frontend-slides": {
        "section_selectors": [
            ".slide",
            "[data-slide]",
        ],
        "interaction_targets": [
            "button",
            "[role=button]",
            "a[href^='#']",
        ],
        "keyboard_tests": [
            "ArrowRight",
            "ArrowLeft",
            "Space",
            "Escape",
            "f",
            "t",
        ],
        "needs_server": True,
    },
}

VIEWPORTS = [
    {"width": 375, "height": 812, "label": "mobile"},
    {"width": 768, "height": 1024, "label": "tablet"},
    {"width": 1440, "height": 900, "label": "desktop"},
]

STAGES = [
    ("dependency_check", "stage_dependency_check"),
    ("screenshots", "stage_screenshots"),
    ("console_errors", "stage_console_errors"),
    ("interactions", "stage_interactions"),
    ("scroll", "stage_scroll"),
    ("overlap", "stage_overlap"),
    ("keyboard_nav", "stage_keyboard_nav"),
    ("accessibility", "stage_accessibility"),
]


def boxes_overlap(a, b):
    """Return True if two AABB rectangles overlap."""
    a_right = a["x"] + a["width"]
    a_bottom = a["y"] + a["height"]
    b_right = b["x"] + b["width"]
    b_bottom = b["y"] + b["height"]
    if a["x"] >= b_right or b["x"] >= a_right:
        return False
    if a["y"] >= b_bottom or b["y"] >= a_bottom:
        return False
    return True


def find_free_port():
    """Bind to port 0 and return the OS-assigned port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def wait_for_server(url, timeout=10):
    """Block until the given URL responds or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(f"Server at {url} did not respond within {timeout}s")


@contextlib.contextmanager
def serve_if_needed(html_file, config):
    """Yield a URL to the HTML file; starts an HTTP server if config requires it."""
    html_path = Path(html_file).resolve()
    if config.get("needs_server"):
        port = find_free_port()
        directory = str(html_path.parent)
        handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
            *args,
            directory=directory,
            **kwargs,
        )
        server = http.server.HTTPServer(("127.0.0.1", port), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{port}/{html_path.name}"
        try:
            wait_for_server(url)
            yield url
        finally:
            server.shutdown()
    else:
        yield f"file://{html_path}"


def stage_dependency_check(page, config, report, output_dir):
    """Verify the HTML page loaded and has a body element."""
    body = page.locator("body")
    assert body.count() == 1, "Page must have exactly one <body>"


def stage_screenshots(page, config, report, output_dir):
    """Capture screenshots at multiple viewports and per-section."""
    output = Path(output_dir)
    report.setdefault("screenshots", [])

    for vp in VIEWPORTS:
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        page.wait_for_timeout(300)
        filename = f"viewport-{vp['label']}-{vp['width']}x{vp['height']}.png"
        filepath = output / filename
        page.screenshot(path=str(filepath), full_page=True)
        report["screenshots"].append({"file": filename, "viewport": vp["label"]})

    # Per-section screenshots
    for selector in config.get("section_selectors", []):
        elements = page.locator(selector)
        count = elements.count()
        for i in range(count):
            el = elements.nth(i)
            if el.is_visible():
                filename = f"section-{re.sub(r'[.\[\]^=]', '', selector)}-{i}.png"
                filepath = output / filename
                el.screenshot(path=str(filepath))
                report["screenshots"].append(
                    {
                        "file": filename,
                        "selector": selector,
                        "index": i,
                    }
                )

    # Full-page screenshot at desktop viewport
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(200)
    fullpage_path = output / "full-page.png"
    page.screenshot(path=str(fullpage_path), full_page=True)
    report["screenshots"].append({"file": "full-page.png", "type": "full-page"})


def stage_console_errors(page, config, report, output_dir, url=None):
    """Capture console errors. When url is provided, create a fresh page with listener before goto."""
    report.setdefault("console_errors", [])

    if url is not None:
        context = page.context
        new_page = context.new_page()
        captured = []

        def on_console(msg):
            captured.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                    "location": str(msg.location) if msg.location else None,
                }
            )

        new_page.on("console", on_console)
        new_page.goto(url, wait_until="networkidle")
        new_page.wait_for_timeout(500)
        report["console_errors"].extend(captured)
        new_page.close()
    else:
        # Assume console messages were already captured by run_qa_pipeline
        pass


def stage_interactions(page, config, report, output_dir):
    """Click interactive elements and record results."""
    report.setdefault("interactions", [])
    for selector in config.get("interaction_targets", []):
        elements = page.locator(selector)
        count = elements.count()
        for i in range(count):
            el = elements.nth(i)
            if el.is_visible():
                try:
                    el.click(timeout=2000)
                    report["interactions"].append(
                        {
                            "selector": selector,
                            "index": i,
                            "status": "clicked",
                        }
                    )
                except Exception as exc:
                    report["interactions"].append(
                        {
                            "selector": selector,
                            "index": i,
                            "status": "error",
                            "error": str(exc),
                        }
                    )


def stage_scroll(page, config, report, output_dir):
    """Scroll through the page and capture scroll metrics."""
    report.setdefault("scroll", {})
    scroll_height = page.evaluate("document.documentElement.scrollHeight")
    viewport_height = page.evaluate("window.innerHeight")
    report["scroll"]["page_height"] = scroll_height
    report["scroll"]["viewport_height"] = viewport_height

    # Scroll to bottom and back
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(300)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)


def stage_overlap(page, config, report, output_dir):
    """Check for overlapping interactive elements."""
    report.setdefault("overlaps", [])
    boxes = page.evaluate("""() => {
        const els = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        return Array.from(els).map(el => {
            const rect = el.getBoundingClientRect();
            return {
                tag: el.tagName,
                text: el.textContent.substring(0, 50),
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            };
        }).filter(b => b.width > 0 && b.height > 0);
    }""")

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes_overlap(boxes[i], boxes[j]):
                report["overlaps"].append(
                    {
                        "element_a": boxes[i],
                        "element_b": boxes[j],
                    }
                )


def stage_keyboard_nav(page, config, report, output_dir):
    """Test keyboard navigation and focus order."""
    report.setdefault("focus_order", [])
    keys = config.get("keyboard_tests", ["Tab", "Shift+Tab", "Enter", "Escape"])

    # Tab through focusable elements and record order
    for _ in range(10):
        page.keyboard.press("Tab")
        page.wait_for_timeout(100)
        focused = page.evaluate("""() => {
            const el = document.activeElement;
            if (!el || el === document.body) return null;
            return {
                tag: el.tagName,
                text: (el.textContent || '').substring(0, 50),
                role: el.getAttribute('role'),
                tabindex: el.getAttribute('tabindex')
            };
        }""")
        if focused:
            report["focus_order"].append(focused)

    # Test specific keys
    for key in keys:
        try:
            page.keyboard.press(key)
            page.wait_for_timeout(100)
        except Exception:
            pass


def stage_accessibility(page, config, report, output_dir):
    """Run accessibility checks using axe-core if available, plus aria snapshot."""
    report.setdefault("accessibility", {})

    if AXE_AVAILABLE:
        try:
            axe = Axe()
            results = axe.run(page)
            report["accessibility"]["axe_violations"] = len(
                results.response.get("violations", []),
            )
            report["accessibility"]["axe_results"] = results.response
        except Exception as exc:
            report["accessibility"]["axe_error"] = str(exc)

    # aria_snapshot via locator form (v1.58)
    try:
        snapshot = page.locator("body").aria_snapshot()
        report["accessibility"]["aria_snapshot"] = snapshot
    except Exception as exc:
        report["accessibility"]["aria_snapshot_error"] = str(exc)


def run_stages(page, config, report, output_dir):
    """Run all stages with per-stage isolation; failures do not block subsequent stages."""
    report.setdefault("stages", {})
    stage_funcs = {
        "dependency_check": stage_dependency_check,
        "screenshots": stage_screenshots,
        "console_errors": stage_console_errors,
        "interactions": stage_interactions,
        "scroll": stage_scroll,
        "overlap": stage_overlap,
        "keyboard_nav": stage_keyboard_nav,
        "accessibility": stage_accessibility,
    }
    for name, func_name in STAGES:
        func = stage_funcs[name]
        try:
            func(page, config, report, output_dir)
            report["stages"][name] = {"status": "pass"}
        except Exception as exc:
            report["stages"][name] = {"status": "error", "error": str(exc)}


def run_qa_pipeline(html_path, config, output_dir, browser):
    """Run the full QA pipeline and return the report dict."""
    html_path = Path(html_path).resolve()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    report = {
        "meta": {
            "html_file": str(html_path),
            "skill": None,
            "screenshots_captured": 0,
        },
        "console_errors": [],
        "interactions": [],
        "overlaps": [],
        "focus_order": [],
        "screenshots": [],
        "stages": {},
    }

    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    # Register console listener BEFORE navigation
    def on_console(msg):
        report["console_errors"].append(
            {
                "type": msg.type,
                "text": msg.text,
                "location": str(msg.location) if msg.location else None,
            }
        )

    page.on("console", on_console)
    page.goto(f"file://{html_path}", wait_until="networkidle")

    run_stages(page, config, report, output)

    # Update meta
    report["meta"]["screenshots_captured"] = len(report.get("screenshots", []))

    context.close()
    return report


def screenshot_only_fallback(html_path, output_dir):
    """Minimal fallback: just take a screenshot without running stages."""
    from playwright.sync_api import sync_playwright

    html_path = Path(html_path).resolve()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    report = {
        "meta": {
            "html_file": str(html_path),
            "fallback": True,
            "screenshots_captured": 0,
        },
        "console_errors": [],
        "interactions": [],
        "overlaps": [],
        "focus_order": [],
        "screenshots": [],
        "stages": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{html_path}", wait_until="networkidle")
        filepath = output / "fallback-screenshot.png"
        page.screenshot(path=str(filepath), full_page=True)
        report["screenshots"].append(
            {"file": "fallback-screenshot.png", "type": "fallback"}
        )
        report["meta"]["screenshots_captured"] = 1
        browser.close()

    return report


def write_report(report, output_dir):
    """Write the report dict to qa_report.json in the output directory."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "qa_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)


def parse_args(argv=None):
    """Parse CLI arguments and return Namespace."""
    parser = argparse.ArgumentParser(
        description="Visual QA Pipeline for skill HTML files",
    )
    parser.add_argument(
        "html_file",
        help="Path to the HTML file to analyze",
    )
    parser.add_argument(
        "--skill",
        default="teach-me",
        choices=list(SKILL_CONFIGS.keys()),
        help="Skill profile to use (default: teach-me)",
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp/teach-me-qa",
        help="Directory for QA output (default: /tmp/teach-me-qa)",
    )
    return parser.parse_args(argv)


def main():
    """Entry point: parse args, launch browser, run pipeline, write report."""
    args = parse_args()
    html_path = Path(args.html_file)

    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    config = SKILL_CONFIGS[args.skill]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    success = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                with serve_if_needed(html_path, config) as url:
                    report = run_qa_pipeline(
                        html_path,
                        config,
                        output_dir,
                        browser,
                    )
                    report["meta"]["skill"] = args.skill
                    write_report(report, output_dir)
                    success = True
            except Exception as exc:
                print(f"Pipeline failed: {exc}", file=sys.stderr)
                print("Attempting screenshot-only fallback...", file=sys.stderr)
                try:
                    report = screenshot_only_fallback(html_path, output_dir)
                    report["meta"]["skill"] = args.skill
                    write_report(report, output_dir)
                    success = True
                except Exception as fallback_exc:
                    print(f"Fallback also failed: {fallback_exc}", file=sys.stderr)
            finally:
                browser.close()
    except Exception as exc:
        print(f"Could not launch browser: {exc}", file=sys.stderr)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
