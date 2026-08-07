"""Phryll Generator v2 panel UI tests (offscreen)."""
from __future__ import annotations


def test_home_card_navigates_to_phryll_v2(main_window):
    home = main_window.panels["Design Studio"]
    card = next(c for c in home.cards
                if c.workflow["key"] == "phryll_v2")
    card.button.click()
    assert main_window.tabs.currentWidget() is \
        main_window.panels["Phryll Generator v2"]


def test_generate_demo_crystal(main_window):
    panel = main_window.panels["Phryll Generator v2"]
    cone = panel.generate()
    assert cone is not None
    dims = cone.generated_dimensions
    assert round(dims["inner_top_diameter_mm"], 2) == 27.32
    assert round(dims["inner_base_diameter_mm"], 2) == 40.32
    eye = panel._coil["eye_alignment"]
    assert eye["z_cross_mm"] == 62.5
    assert eye["alignment_error_mm"] == 0.0
    assert "PASS" in panel.status.text()


def test_refusal_paths_surface(main_window):
    panel = main_window.panels["Phryll Generator v2"]
    panel.top_d.setValue(80.0)                 # top > base -> refused
    assert panel.generate() is None
    assert "Refused" in panel.status.text()
    panel.top_d.setValue(26.0)
    assert panel.generate() is not None


def test_export_bundle_from_panel(main_window):
    panel = main_window.panels["Phryll Generator v2"]
    panel.generate()
    result = panel.export_bundle()
    assert result is not None
    assert result["verification"]["ok"]
    bundle = result["bundle"]
    assert (bundle / "cad" / "custom_cone.stl").is_file()
    assert (bundle / "pdf" / "build_sheet.pdf").is_file()
    ws_root = str(main_window.context.workspace.root)
    assert str(bundle).startswith(ws_root)
    info = panel.inspector_info()
    assert info["properties"]["Eye residual (mm)"] == 0.0
