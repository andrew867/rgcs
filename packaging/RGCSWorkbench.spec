# PyInstaller spec for RGCS Workbench (v4.5, P03).
#
# onedir build (a folder, not a single EXE) -> zipped into the
# portable ZIP and installed by Inno Setup. onedir launches faster
# and is transparent (a reviewer can see every bundled file), which
# suits an evidence-first project.
#
# Build:  pyinstaller packaging/RGCSWorkbench.spec --noconfirm
# Output: dist/RGCSWorkbench/RGCSWorkbench.exe
#
# The frozen build carries multiprocessing.freeze_support() (already
# in rgcs_desktop.app.main) so spawn-based background jobs work.

import sys
from pathlib import Path

block_cipher = None

# Paths in a .spec resolve relative to the spec's own directory, so
# anchor everything to the repo root (parent of packaging/) explicitly.
ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 (PyInstaller global)

# data files the app + workbook generator need at runtime.
# The desktop viewers resolve these relative to Path(__file__).parents[2],
# which in a frozen build is the _internal dir; each dest below must
# mirror the in-repo layout so those reads resolve.
datas = [
    (str(ROOT / "rscs_core" / "registry"), "rscs_core/registry"),
    (str(ROOT / "rscs2_core" / "registry"), "rscs2_core/registry"),
    # model browser + provenance graph
    (str(ROOT / "docs" / "model_registry.yaml"), "docs"),
    # provenance graph (equation ledger) + source/reference registries
    (str(ROOT / "references"), "references"),
    # experiment builder / manifest validation schemas
    (str(ROOT / "experiments" / "schemas"), "experiments/schemas"),
]

hiddenimports = [
    "rgcs_workbench.canonical", "rgcs_workbench.workbook",
    "fkey_instrument.relations", "fkey_instrument.crystal_mode",
    "fkey_instrument.optimizer", "fkey_instrument.boards",
    "resonator_platform.campaign",
    "rscs2_core.eye_ladder_analysis",
    "sources.registry.v4x2_source_registry",
    "openpyxl",
]

a = Analysis(
    [str(ROOT / "packaging" / "workbench_entry.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests", "pytest"],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="RGCSWorkbench",
    debug=False, bootloader_ignore_signals=False, strip=False,
    upx=False, console=False,   # GUI app; --doctor prints to a
    #                             console only when launched from one
    disable_windowed_traceback=False,
    icon=None,                  # no icon asset bundled; unsigned
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False, name="RGCSWorkbench",
)
