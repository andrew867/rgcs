"""Design Studio shell tests: home cards, navigation, Advanced Mode
preservation, and the guided panel workflows (offscreen)."""
from __future__ import annotations

from rgcs_desktop.services.design_studio import WORKFLOWS


def test_home_opens_by_default(main_window):
    assert main_window.tabs.currentWidget() is \
        main_window.panels["Design Studio"]


def test_home_cards_match_workflow_registry(main_window):
    home = main_window.panels["Design Studio"]
    assert len(home.cards) == len(WORKFLOWS)
    labels = [card.button.text() for card in home.cards]
    assert "Validate a crystal" in labels
    assert "Open Advanced Scientific Workbench" in labels


def test_cards_navigate_to_panels(main_window, qtbot):
    home = main_window.panels["Design Studio"]
    for card in home.cards:
        main_window.open_panel("Design Studio")
        card.button.click()
        target = main_window.panels[card.workflow["panel"]]
        assert main_window.tabs.currentWidget() is target


def test_advanced_mode_opens_existing_workbench(main_window):
    home = main_window.panels["Design Studio"]
    advanced = next(c for c in home.cards
                    if c.workflow["key"] == "advanced")
    advanced.button.click()
    # the Advanced card lands on the existing Workspace browser panel
    assert main_window.tabs.currentWidget() is \
        main_window.panels["Workspace"]
    # and all pre-Design-Studio panels still exist untouched
    for title in ("Specimen editor", "Pulse designer", "Report / export",
                  "Evidence ledger"):
        assert title in main_window.panels


def test_command_palette_covers_design_studio_panels(main_window):
    names = main_window.command_names()
    assert "Open panel: Crystal Validator" in names
    assert "Open panel: Design Studio" in names


def test_crystal_validator_golden_flow(main_window, tmp_path):
    panel = main_window.panels["Crystal Validator"]
    panel.load_example()
    assert panel.validate()
    exports = panel.export_all()
    assert exports["json"].is_file()
    assert exports["svg"].is_file()
    assert exports["pdf"].is_file()
    assert exports["receipt"].is_file()
    # exports land inside the workspace
    ws_root = str(main_window.context.workspace.root)
    assert str(exports["pdf"]).startswith(ws_root)


def test_crystal_validator_blocks_invalid(main_window):
    panel = main_window.panels["Crystal Validator"]
    panel.load_example()
    panel.length.setValue(0.0)              # invalid: no length
    assert not panel.validate()
    assert not panel.export_btn.isEnabled()
    assert panel.export_all() == {}


def test_phryll_v1_retired_from_ui(main_window):
    # v8.5.2: the v1 box-holder designer no longer appears anywhere in
    # the UI — v2 is the only Phryll path (service kept for legacy
    # exports).
    assert "Phyrll Generator Designer" not in main_window.panels
    assert "Phryll Generator v2" in main_window.panels
    cards = [c.workflow["panel"]
             for c in main_window.panels["Design Studio"].cards]
    assert "Phyrll Generator Designer" not in cards
    assert "Phryll Generator v2" in cards


def test_phryll_v2_stl_only_export(main_window):
    panel = main_window.panels["Phryll Generator v2"]
    receipt = panel.export_single()
    assert receipt is not None
    from pathlib import Path
    path = Path(receipt["path"])
    assert path.is_file() and path.suffix == ".stl"
    # single-file export: exactly one artifact, no bundle directory
    out = path.parent
    assert not any(p.name.startswith("phryll_design_")
                   for p in out.iterdir())
    assert [p for p in out.iterdir() if p.is_file()] == [path]


def test_coil_pulse_panel_sidebands(main_window):
    panel = main_window.panels["Coil / Pulse Designer"]
    design = panel.compute()
    assert design is not None
    first = design["sidebands"][0]
    assert first["lower_hz"] == 3171.0      # 4096 - 925
    assert first["upper_hz"] == 5021.0
    sheet = panel.export_build_sheet()
    assert sheet.is_file()


def test_coil_pulse_custom_key_warns(main_window):
    panel = main_window.panels["Coil / Pulse Designer"]
    panel.key_combo.setCurrentIndex(panel.key_combo.count() - 1)  # custom…
    panel.custom_key.setValue(777.7)
    panel.compute()
    assert "custom key" in panel.key_warning.text()


def test_annular_ring_default_fixture(main_window):
    panel = main_window.panels["Annular Ring Designer"]
    design = panel.current_design()
    assert design is not None
    assert design["cell_count"] == 37
    assert design["od_mm"] == 288.0
    assert design["id_mm"] == 188.0
    assert len(design["blanked_cells"]) == 4
    exports = panel.export_all()
    for key in ("svg", "scad", "phase_csv", "mask_csv", "pdf", "receipt"):
        assert exports[key].is_file(), key


def test_annular_ring_refuses_bad_geometry(main_window):
    panel = main_window.panels["Annular Ring Designer"]
    panel.idm.setValue(400.0)               # ID > OD
    assert panel.current_design() is None
    assert "Refused" in panel.status.text()
    panel.idm.setValue(188.0)
    assert panel.compute() is not None


def test_frequency_key_library(main_window):
    panel = main_window.panels["Frequency Key Library"]
    assert panel.table.rowCount() == 17     # required initial keys
    panel.select_key_hz(925.0)
    assert "3171" in panel.sideband_label.text()
    assert "37 * 25" in panel.sideband_label.text()
    rec = panel.add_custom()
    assert rec["source_status"] == "custom"
    assert panel.table.rowCount() == 18


def test_design_studio_inspector_contract(main_window):
    for title in ("Design Studio", "Crystal Validator",
                  "Phryll Generator v2", "Coil / Pulse Designer",
                  "Annular Ring Designer", "Frequency Key Library"):
        info = main_window.panels[title].inspector_info()
        for key in ("properties", "classification", "units", "provenance"):
            assert key in info, f"{title} missing {key}"
