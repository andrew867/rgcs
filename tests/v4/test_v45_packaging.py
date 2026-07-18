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


# --- v4.5.2: --first-run is never a workspace path ----------------------

def test_plan_startup_first_run_flag_is_never_a_path():
    """The v4.5.2 regression contract. `--first-run` must map to the
    wizard, never to creating/opening a workspace literally named
    '--first-run' (the shipped-binary bug)."""
    from rgcs_desktop.app.main import plan_startup
    for argv in (["--first-run"],
                 ["--first-run", "--other"],
                 ["--first-run", "C:/some/path"]):
        action, path = plan_startup(argv, last_workspace=None,
                                    first_run_done=False)
        assert action == "first_run", argv
        assert path is None, argv


def test_plan_startup_never_returns_dash_prefixed_path():
    """No argv of leading-dash flags may ever produce a workspace path."""
    from rgcs_desktop.app.main import plan_startup
    for argv in (["--first-run"], ["--smoke-check"], ["--doctor"],
                 ["--build-info"], ["--print-startup-plan"],
                 ["--first-run", "--print-startup-plan"]):
        _, path = plan_startup(argv, None, True)
        assert path is None or not str(path).startswith("-"), argv
        # specifically, a directory literally named --first-run is banned
        assert path is None or path.name != "--first-run", argv


def test_plan_startup_positional_still_opens_or_creates(tmp_path):
    from rgcs_desktop.app.main import plan_startup
    action, path = plan_startup([str(tmp_path / "ws")], None, True)
    assert action == "create" and path == tmp_path / "ws"
    (tmp_path / "ws2").mkdir()
    (tmp_path / "ws2" / "workspace.db").write_text("x")
    action, path = plan_startup([str(tmp_path / "ws2")], None, True)
    assert action == "open" and path == tmp_path / "ws2"


def test_plan_startup_genuine_first_launch_and_none():
    from rgcs_desktop.app.main import plan_startup
    assert plan_startup([], None, False) == ("first_run", None)
    assert plan_startup([], None, True) == ("none", None)


def test_build_meta_source_hash_deterministic_and_covers_desktop():
    from rgcs_desktop.build_meta import (SOURCE_ROOTS,
                                         compute_source_hash)
    h1 = compute_source_hash(ROOT)
    h2 = compute_source_hash(ROOT)
    assert h1 == h2 and len(h1) == 64
    assert "rgcs_desktop" in SOURCE_ROOTS
    assert "rgcs_workbench" in SOURCE_ROOTS


def test_spec_bundles_build_stamp_for_build_info():
    spec = (ROOT / "packaging" / "RGCSWorkbench.spec").read_text(
        encoding="utf-8")
    assert "_build_stamp.json" in spec


def test_spec_bundles_runtime_data_the_desktop_reads():
    """The desktop viewers read these REPO_ROOT-relative data trees at
    runtime; the frozen build crashed on launch when they were absent
    (model browser -> docs/model_registry.yaml). Guard that the spec
    declares every one so a re-freeze can never silently drop them."""
    spec = (ROOT / "packaging" / "RGCSWorkbench.spec").read_text(
        encoding="utf-8")
    for needed in ("model_registry.yaml", '"references"',
                   "experiments", "rscs_core", "rscs2_core"):
        assert needed in spec, f"spec no longer bundles {needed}"
    # and the source files the spec points at must actually exist
    assert (ROOT / "docs" / "model_registry.yaml").exists()
    assert (ROOT / "references" / "equation_provenance.yaml").exists()
    assert (ROOT / "experiments" / "schemas"
            / "run_manifest.schema.json").exists()


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
