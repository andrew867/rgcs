#!/usr/bin/env python3
"""Capture screenshot proofs of the Design Studio workflows.

Constructs the real application (MainWindow + workspace + job manager),
walks the golden path with real data — validate example specimen,
derive the Phyrll holder, compute coil/pulse estimates, validate the
37-cell ring, select the 925 Hz key — exports the real artifacts, and
saves a rendered screenshot of every panel plus the home screen.

Run: python tools/design_studio_screenshots.py [out_dir]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    out = (Path(sys.argv[1]) if len(sys.argv) > 1
           else REPO / "docs" / "assets" / "design-studio" / "screenshots")
    out.mkdir(parents=True, exist_ok=True)

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from rgcs_desktop.app.context import AppContext
    from rgcs_desktop.app.main_window import MainWindow
    from rgcs_desktop.workspaces import Workspace

    tmp = Path(tempfile.mkdtemp(prefix="rgcs-shots-"))
    ws = Workspace.create(tmp / "ws", "screenshot-proof")
    context = AppContext(workspace=ws)
    window = MainWindow(context)
    window.resize(1440, 900)

    captured: list[str] = []

    def shot(name: str) -> None:
        app.processEvents()
        pixmap = window.grab()
        path = out / f"{name}.png"
        pixmap.save(str(path), "PNG")
        captured.append(path.name)
        print(f"captured {path}")

    # 1. home
    window.open_panel("Design Studio")
    shot("01_design_studio_home")

    # 2. crystal validator with the example specimen validated
    validator = window.panels["Crystal Validator"]
    window.open_panel("Crystal Validator")
    validator.load_example()
    assert validator.validate(), "example specimen must validate"
    exports = validator.export_all()
    assert exports["pdf"].is_file()
    shot("02_crystal_validator")

    # 3. phyrll generator inheriting the validated specimen
    phyrll = window.panels["Phyrll Generator Designer"]
    window.open_panel("Phyrll Generator Designer")
    phyrll.use_current_specimen()
    assert phyrll.current_design() is not None
    scad = phyrll.generate_scad()
    assert scad.is_file()
    sheet = phyrll.export_build_sheet()
    assert sheet.is_file()
    shot("03_phyrll_generator_designer")

    # 4. coil / pulse designer (925 key selected by default)
    coil = window.panels["Coil / Pulse Designer"]
    window.open_panel("Coil / Pulse Designer")
    design = coil.compute()
    assert design["sidebands"][0]["lower_hz"] == 3171.0
    cp_sheet = coil.export_build_sheet()
    assert cp_sheet.is_file()
    shot("04_coil_pulse_designer")

    # 5. annular ring designer, default 37-cell fixture exported
    ring = window.panels["Annular Ring Designer"]
    window.open_panel("Annular Ring Designer")
    assert ring.current_design()["cell_count"] == 37
    ring_exports = ring.export_all()
    assert ring_exports["pdf"].is_file()
    shot("05_annular_ring_designer")

    # 6. frequency key library with 925 selected
    keys = window.panels["Frequency Key Library"]
    window.open_panel("Frequency Key Library")
    keys.select_key_hz(925.0)
    shot("06_frequency_key_library")

    # 7. advanced mode (existing workbench preserved)
    window.open_panel("Workspace")
    shot("07_advanced_mode_workspace")

    # 8. the export ledger view (report/export panel of Advanced Mode)
    window.open_panel("Report / export")
    shot("08_reports_and_exports")

    n_exports = len(ws.list_exports())
    print(f"workspace export ledger rows: {n_exports}")
    assert n_exports >= 5, "exports were not recorded in the workspace"

    window.close()
    context.shutdown()
    print(f"done: {len(captured)} screenshots in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
