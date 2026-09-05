import sys
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def browser():
    """Launch headless Chromium for the test session."""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    """Fresh page for each test."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    p = context.new_page()
    yield p
    context.close()


@pytest.fixture
def simple_html(tmp_path):
    """Minimal valid HTML file for testing."""
    html = tmp_path / "test.html"
    html.write_text(
        "<!DOCTYPE html><html><head><title>Test</title></head>"
        "<body><h1>Hello</h1><button>Click</button></body></html>"
    )
    return html


@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory for QA results."""
    d = tmp_path / "qa-output"
    d.mkdir()
    return d
