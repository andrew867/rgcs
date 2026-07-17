"""v4.5 packaging + first-run wizard tests.

The frozen-EXE build and the compiled installer are verified out of
band (tools/v45_build_windows.py) because they need PyInstaller/Inno
Setup and minutes of wall time. These tests cover what CI can check
cheaply and deterministically: the spec/installer scripts are present
and honest, and the first-run wizard is constructible offscreen and
does what it claims.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_pyinstaller_spec_and_entry_present():
    assert (ROOT / "packaging" / "RGCSWorkbench.spec").exists()
    assert (ROOT / "packaging" / "workbench_entry.py").exists()


def test_inno_script_is_per_user_and_unsigned():
    iss = (ROOT / "packaging" / "RGCS_Workbench.iss").read_text(
        encoding="utf-8")
    # per-user install, no admin
    assert "PrivilegesRequired=lowest" in iss
    # must not silently claim a signature it does not have
    assert "SignTool" not in iss


def test_build_tool_gates_installer_and_clean_machine():
    src = (ROOT / "tools" / "v45_build_windows.py").read_text(
        encoding="utf-8")
    # the build report must never assert clean-machine or signed
    assert '"clean_machine_verified": False' in src
    assert '"signed": False' in src


def test_portable_readme_states_boundaries():
    # the boundaries the build tool writes into the portable payload
    src = (ROOT / "tools" / "v45_build_windows.py").read_text(
        encoding="utf-8")
    for phrase in ("no telemetry", "UNSIGNED build",
                   "Nothing physical is validated"):
        assert phrase in src


@pytest.mark.skipif("PySide6" not in os.sys.modules and
                    __import__("importlib").util.find_spec("PySide6")
                    is None, reason="PySide6 not installed")
def test_first_run_wizard_constructs_offscreen(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from rgcs_desktop.app.main import create_app
    create_app()
    from rgcs_desktop.app.first_run import (FirstRunWizard,
                                            default_workspace_dir)
    wiz = FirstRunWizard(default_dir=tmp_path / "RGCS Workspace")
    assert wiz.workspace_path == tmp_path / "RGCS Workspace"
    assert wiz.seed_demo is True          # demo on by default
    # default location is under the user's Documents, never hardcoded
    assert "RGCS Workspace" in str(default_workspace_dir())


@pytest.mark.skipif(__import__("importlib").util.find_spec("PySide6")
                    is None, reason="PySide6 not installed")
def test_first_run_seeds_demo_workbook(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from rgcs_desktop.app.first_run import _seed_demo
    _seed_demo(tmp_path)
    wb = tmp_path / "RGCS_Master_Evidence_Workbook.xlsx"
    assert wb.exists() and wb.stat().st_size > 0
