"""Browser-oriented static hub checks (no network, no telemetry)."""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
HUB = ROOT / "static" / "hub"


def test_hub_pages_are_accessible_markup():
    index = (HUB / "index.html").read_text(encoding="utf-8")
    assert 'lang="en"' in index
    assert "color-scheme" in index
    assert 'href="#main"' in index
    assert "Toggle theme" in index
    for path in (HUB / "modules").glob("*.html"):
        text = path.read_text(encoding="utf-8")
        for heading in (
            "WHAT THIS DOES",
            "WHAT THIS DOES NOT DO",
            "STATUS",
            "INPUT",
            "TRACE",
            "TESTS",
            "SOURCE",
        ):
            assert heading in text, f"{path.name} missing {heading}"
        assert "Download receipt" in text or "receipt" in text.lower()


def test_static_hub_has_no_telemetry_hooks():
    for path in HUB.rglob("*"):
        if path.suffix.lower() not in {".html", ".js", ".css"}:
            continue
        text = path.read_text(encoding="utf-8")
        for banned in ("googletagmanager", "analytics", "sentry.io",
                       "posthog", "mixpanel", "segment.io"):
            assert banned not in text.lower()


def test_fixture_receipts_are_json():
    for path in (HUB / "fixtures").glob("*.json"):
        data = path.read_text(encoding="utf-8")
        assert data.strip().startswith("{")
    for path in (HUB / "receipts").glob("*.json"):
        assert '"module"' in path.read_text(encoding="utf-8") or "modules" in path.read_text(encoding="utf-8")


def test_css_supports_light_and_dark():
    css = (HUB / "assets" / "hub.css").read_text(encoding="utf-8")
    assert "color-scheme: light dark" in css
    assert 'data-theme="dark"' in css
    assert re.search(r"@media", css) or "auto-fit" in css
