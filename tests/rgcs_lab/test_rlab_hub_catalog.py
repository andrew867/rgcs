"""AA-03 closure — hub badge catalog derives from the canonical registry.

The static hub must never hand-write module ids, titles, statuses, or
badge values in JavaScript. Static mode consumes a GENERATED
``assets/catalog.data.js`` (emitted by ``tools/lab/build_static_hub.py``
from ``rgcs_lab.common.status.module_catalog``); server mode asks
``/api/modules`` which returns the same canonical catalog.
"""

from __future__ import annotations

import json
import pathlib
import re

from rgcs_lab.common.status import module_catalog
from rgcs_lab.common.status_schema import MODULES

ROOT = pathlib.Path(__file__).resolve().parents[2]
HUB = ROOT / "static" / "hub"
MIRROR = ROOT / "release" / "lab" / "static-hub"


def _parse_catalog_data_js(path: pathlib.Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.RGCS_CATALOG\s*=\s*(\[.*\]);", text, re.S)
    assert match, "catalog.data.js must assign window.RGCS_CATALOG = [...]"
    return json.loads(match.group(1))


def test_hub_js_has_no_handwritten_catalog():
    js = (HUB / "assets" / "hub.js").read_text(encoding="utf-8")
    # No module entry literals may live in hub.js itself.
    for mid in MODULES:
        assert f'id:"{mid}"' not in js and f"id: \"{mid}\"" not in js
    assert "window.RGCS_CATALOG" in js  # consumes the generated data


def test_catalog_data_js_is_generated_and_canonical():
    path = HUB / "assets" / "catalog.data.js"
    assert path.is_file(), "build_static_hub.py must emit catalog.data.js"
    head = path.read_text(encoding="utf-8").splitlines()[0]
    assert "GENERATED" in head and "module_catalog" in head
    assert _parse_catalog_data_js(path) == module_catalog()


def test_catalog_fixture_matches_canonical_registry():
    fx = json.loads((HUB / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
    assert fx["modules"] == module_catalog()
    assert tuple(m["id"] for m in fx["modules"]) == MODULES


def test_all_nine_entries_resolve_to_pages_fixtures_receipts():
    catalog = _parse_catalog_data_js(HUB / "assets" / "catalog.data.js")
    assert len(catalog) == 9
    for entry in catalog:
        mid = entry["id"]
        assert (HUB / "modules" / f"{mid}.html").is_file()
        assert (HUB / "fixtures" / f"{mid}.json").is_file()
        receipt_path = HUB / "receipts" / f"{mid}.json"
        assert receipt_path.is_file()
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert receipt["module"] == mid
        # badge semantics preserved: statuses come from the registry
        assert entry["status"] in ("GREEN", "YELLOW", "RED")
        assert entry["physical_status"] in ("GREEN", "YELLOW", "RED")


def test_static_mode_wiring_without_server():
    index = (HUB / "index.html").read_text(encoding="utf-8")
    # catalog data must load BEFORE hub.js so file:// mode has it.
    assert index.index("assets/catalog.data.js") < index.index("assets/hub.js")
    js = (HUB / "assets" / "hub.js").read_text(encoding="utf-8")
    assert "window.RGCS_CATALOG" in js


def test_release_mirror_carries_same_generated_catalog():
    if not MIRROR.exists():
        return  # mirror synced at release time; working hub is the source
    assert _parse_catalog_data_js(MIRROR / "assets" / "catalog.data.js") == \
        _parse_catalog_data_js(HUB / "assets" / "catalog.data.js")
