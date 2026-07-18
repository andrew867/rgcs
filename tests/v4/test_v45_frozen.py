"""Packaged (frozen-binary) regression tests for v4.5.2.

These exercise the actual PyInstaller-built ``dist/RGCSWorkbench.exe``.
They are skipped when no frozen build is present (normal CI), and run
during the release build (tools/v45_build_windows.py builds dist/ first)
and locally after a freeze.

The load-bearing test is ``test_installer_launch_creates_no_dashdir``:
it runs the installer's *exact* post-install command
(``RGCSWorkbench.exe --first-run``) and proves no directory named
``--first-run`` is ever created -- the v4.5.0/v4.5.1 shipped-binary bug.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "dist" / "RGCSWorkbench" / "RGCSWorkbench.exe"

pytestmark = pytest.mark.skipif(
    not EXE.exists(),
    reason="no frozen dist/RGCSWorkbench.exe (build it with "
           "tools/v45_build_windows.py)")


def _env():
    return dict(os.environ, QT_QPA_PLATFORM="offscreen")


def test_frozen_build_info_matches_current_source():
    """The frozen binary must carry the current source hash -- proves it
    was not built from stale source (the root cause of v4.5.1)."""
    from rgcs_desktop.build_meta import compute_source_hash
    r = subprocess.run([str(EXE), "--build-info"], capture_output=True,
                       text=True, env=_env(), timeout=120)
    assert r.returncode == 0, r.stderr
    info = json.loads(r.stdout)
    assert info.get("frozen") is True
    assert info.get("source_hash") == compute_source_hash(ROOT)


def test_frozen_startup_plan_first_run_is_wizard_not_path():
    r = subprocess.run(
        [str(EXE), "--print-startup-plan", "--first-run"],
        capture_output=True, text=True, env=_env(), timeout=120)
    assert r.returncode == 0, r.stderr
    action = r.stdout.strip().split("\t")[0]
    assert action == "first_run", r.stdout
    assert "--first-run" not in r.stdout.split("\t")[-1]


def test_installer_launch_creates_no_dashdir(tmp_path):
    """Run the installer's exact post-install command from a temp cwd;
    the old binary created a workspace dir literally named '--first-run'
    (relative to cwd). Launch, let it settle, terminate, assert clean."""
    proc = subprocess.Popen(
        [str(EXE), "--first-run"], cwd=str(tmp_path),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_env())
    time.sleep(8)               # let startup + workspace logic run
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    # nothing named --first-run anywhere under the launch cwd
    offenders = [p for p in tmp_path.rglob("*") if p.name == "--first-run"]
    assert not offenders, f"created junk dir(s): {offenders}"
    assert not (tmp_path / "--first-run").exists()


def test_frozen_smoke_check_constructs_all_panels():
    r = subprocess.run([str(EXE), "--smoke-check"], capture_output=True,
                       text=True, env=_env(), timeout=300)
    assert r.returncode == 0, r.stderr
    assert "13 panels constructed OK" in r.stdout, r.stdout


def test_frozen_first_run_selftest_creates_workspace_and_workbook(
        tmp_path):
    ws = tmp_path / "RGCS Workspace"
    r = subprocess.run(
        [str(EXE), "--first-run-selftest", str(ws)],
        capture_output=True, text=True, env=_env(), timeout=300)
    assert r.returncode == 0, r.stderr + r.stdout
    result = json.loads(r.stdout)
    assert result["workspace_db_exists"] is True
    assert result["workbook_seeded"] is True
    assert result["workspace_name"] != "--first-run"
    assert (ws / "workspace.db").exists()
    assert (ws / "RGCS_Master_Evidence_Workbook.xlsx").exists()


def test_frozen_doctor_reports_boundary():
    r = subprocess.run([str(EXE), "--doctor"], capture_output=True,
                       text=True, env=_env(), timeout=120)
    assert r.returncode == 0
    assert "SOFTWARE only" in r.stdout
