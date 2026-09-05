import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "visual_qa.py"


# --- Unit tests (no Playwright needed) ---


def test_parse_args_minimal():
    """CLI with just an HTML file uses defaults."""
    from visual_qa import parse_args

    args = parse_args(["test.html"])
    assert args.html_file == "test.html"
    assert args.skill == "teach-me"
    assert args.output_dir == "/tmp/teach-me-qa"


def test_parse_args_full():
    """CLI with all flags parses correctly."""
    from visual_qa import parse_args

    args = parse_args(
        ["page.html", "--skill", "frontend-slides", "--output-dir", "/tmp/out"]
    )
    assert args.html_file == "page.html"
    assert args.skill == "frontend-slides"
    assert args.output_dir == "/tmp/out"


def test_skill_configs_have_required_keys():
    """Both skill configs have section_selectors and interaction_targets."""
    from visual_qa import SKILL_CONFIGS

    for skill in ("teach-me", "frontend-slides"):
        config = SKILL_CONFIGS[skill]
        assert "section_selectors" in config
        assert "interaction_targets" in config


def test_boxes_overlap_true():
    """Two overlapping rectangles are detected."""
    from visual_qa import boxes_overlap

    a = {"x": 0, "y": 0, "width": 100, "height": 100}
    b = {"x": 50, "y": 50, "width": 100, "height": 100}
    assert boxes_overlap(a, b) is True


def test_boxes_overlap_false():
    """Two non-overlapping rectangles are not flagged."""
    from visual_qa import boxes_overlap

    a = {"x": 0, "y": 0, "width": 100, "height": 100}
    b = {"x": 200, "y": 200, "width": 100, "height": 100}
    assert boxes_overlap(a, b) is False


def test_find_free_port():
    """find_free_port returns a usable port number."""
    from visual_qa import find_free_port

    port = find_free_port()
    assert isinstance(port, int)
    assert 1024 < port < 65536


# --- Integration tests (need Playwright) ---


def test_screenshot_capture(page, simple_html, output_dir):
    """Screenshot stage produces PNG files."""
    from visual_qa import stage_screenshots, SKILL_CONFIGS

    report = {"screenshots": []}
    page.goto(f"file://{simple_html.resolve()}", wait_until="networkidle")
    stage_screenshots(page, SKILL_CONFIGS["teach-me"], report, output_dir)
    pngs = list(output_dir.glob("*.png"))
    assert len(pngs) >= 1
    assert len(report["screenshots"]) >= 1


def test_console_error_capture(browser, tmp_path, output_dir):
    """Console errors are captured when listener is registered before navigation."""
    html = tmp_path / "errors.html"
    html.write_text(
        "<!DOCTYPE html><html><body>"
        '<script>console.error("test error");</script>'
        "</body></html>"
    )
    from visual_qa import stage_console_errors, SKILL_CONFIGS

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    report = {"console_errors": []}
    stage_console_errors(
        page,
        SKILL_CONFIGS["teach-me"],
        report,
        output_dir,
        url=f"file://{html.resolve()}",
    )
    context.close()
    errors = [e for e in report["console_errors"] if e.get("type") == "error"]
    assert len(errors) >= 1
    assert "test error" in errors[0].get("text", "")


def test_report_structure(browser, simple_html, output_dir):
    """Completed report has required top-level keys including per-stage status."""
    from visual_qa import run_qa_pipeline, SKILL_CONFIGS

    report = run_qa_pipeline(
        simple_html, SKILL_CONFIGS["teach-me"], output_dir, browser
    )
    for key in (
        "meta",
        "console_errors",
        "interactions",
        "overlaps",
        "focus_order",
        "stages",
    ):
        assert key in report, f"Missing key: {key}"
    assert report["meta"]["screenshots_captured"] >= 1
    assert isinstance(report["stages"], dict)
    for stage_name, stage_info in report["stages"].items():
        assert "status" in stage_info, f"Stage {stage_name} missing status"
        assert stage_info["status"] in ("pass", "error")


def test_stage_runner_isolation(browser, tmp_path, output_dir):
    """A crashing stage does not prevent other stages from running."""
    html = tmp_path / "ok.html"
    html.write_text("<!DOCTYPE html><html><body><h1>OK</h1></body></html>")
    from visual_qa import run_qa_pipeline, SKILL_CONFIGS

    report = run_qa_pipeline(html, SKILL_CONFIGS["teach-me"], output_dir, browser)
    completed = [
        k for k, v in report["stages"].items() if v["status"] in ("pass", "error")
    ]
    assert len(completed) >= 2


def test_cli_exit_code(simple_html, output_dir):
    """Script exits 0 on valid input."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(simple_html),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_missing_file(output_dir):
    """Script exits 1 when HTML file doesn't exist."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "/nonexistent/file.html",
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
