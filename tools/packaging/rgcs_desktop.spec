# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the RGCS v2 desktop workbench.

Usage (from the repo root):
    pyinstaller tools/packaging/rgcs_desktop.spec --noconfirm

Works on Windows and Linux (build on the target OS — PyInstaller does not
cross-compile). Data files bundled: experiment schemas + validate.py (the
experiment builder validates with the shared registry), the model registry
YAML, and the docs the UI references at runtime.

Note: rgcs_desktop resolves repo files relative to its package location
(services/schemas.py uses parents[2]); the bundled tree reproduces that
layout via the datas entries below.
"""
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

REPO = Path(SPECPATH).resolve().parents[1]  # tools/packaging -> repo root

block_cipher = None

datas = [
    (str(REPO / "experiments" / "schemas"), "experiments/schemas"),
    (str(REPO / "docs" / "model_registry.yaml"), "docs"),
    (str(REPO / "docs" / "NOTATION_AND_UNITS.md"), "docs"),
    (str(REPO / "docs" / "SCIENTIFIC_CLASSIFICATION_POLICY.md"), "docs"),
]

hiddenimports = (
    collect_submodules("rgcs_core")
    + collect_submodules("rgcs_desktop")
    + [
        # spawn-based multiprocessing workers resolve these at child start
        "rgcs_desktop.jobs.workers",
        "multiprocessing.spawn",
        "jsonschema",
        "referencing",
        "rpds",
        "yaml",
        "pyqtgraph",
    ]
)

a = Analysis(
    [str(REPO / "rgcs_desktop" / "__main__.py")],
    pathex=[str(REPO)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore",
        "PySide6.QtQuick3D",
        "PySide6.QtCharts",
        "PySide6.QtMultimedia",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rgcs-workbench",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI app; set True to debug startup issues
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="rgcs-workbench",
)
