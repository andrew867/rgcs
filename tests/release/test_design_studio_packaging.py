"""Design Studio installer/packaging guards (plan pack 09_INSTALLERS)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_linux_installer_present_and_sane():
    script = ROOT / "scripts" / "install_linux.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert 'python -m pip install -e ".[desktop]"' in text
    assert "--smoke-check" in text
    assert "install_receipt.txt" in text


def test_launcher_present():
    launcher = ROOT / "scripts" / "run_rgcs_workbench.sh"
    assert launcher.is_file()
    text = launcher.read_text(encoding="utf-8")
    assert "rgcs-workbench" in text


def test_windows_build_script_reuses_existing_spec():
    ps1 = ROOT / "tools" / "packaging" / "windows" / "build_windows.ps1"
    assert ps1.is_file()
    text = ps1.read_text(encoding="utf-8")
    assert "rgcs_desktop.spec" in text          # one spec, reused
    assert "--smoke-check" in text
    assert "SHA256" in text
    assert "release_manifest.py" in text
    # the spec it points at exists
    assert (ROOT / "tools" / "packaging" / "rgcs_desktop.spec").is_file()


def test_both_specs_bundle_frequency_keys_data():
    """The Frequency Key Library loads rgcs_desktop/data at startup; a
    frozen build without it fails its own smoke check."""
    for spec in (ROOT / "tools" / "packaging" / "rgcs_desktop.spec",
                 ROOT / "packaging" / "RGCSWorkbench.spec"):
        text = spec.read_text(encoding="utf-8")
        assert "rgcs_desktop/data" in text, spec
    assert (ROOT / "rgcs_desktop" / "data"
            / "frequency_keys.json").is_file()


def test_release_manifest_schema_valid_and_generator_round_trips(tmp_path):
    schema_path = (ROOT / "schemas" / "release"
                   / "release_manifest.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"rgcs artifact")
    out = tmp_path / "manifest.json"
    proc = subprocess.run(
        [sys.executable,
         str(ROOT / "tools" / "packaging" / "release_manifest.py"),
         "--platform", "test",
         "--build-command", "pytest",
         "--smoke-command", "rgcs-workbench --smoke-check",
         "--smoke-status", "passed",
         "--artifact", str(artifact),
         "--out", str(out)],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads(out.read_text(encoding="utf-8"))

    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(schema).validate(manifest)
    assert manifest["platform"] == "test"
    assert manifest["smoke"]["status"] == "passed"
    assert len(manifest["artifacts"][0]["sha256"]) == 64


def test_release_manifest_generator_refuses_missing_artifact(tmp_path):
    proc = subprocess.run(
        [sys.executable,
         str(ROOT / "tools" / "packaging" / "release_manifest.py"),
         "--platform", "test",
         "--smoke-command", "x", "--smoke-status", "skipped",
         "--artifact", str(tmp_path / "nope.bin"),
         "--out", str(tmp_path / "m.json")],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1
    assert "missing artifact" in proc.stderr


def test_install_docs_reference_real_paths():
    install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
    assert "scripts/install_linux.sh" in install
    assert "build_windows.ps1" in install
    packaging_doc = (ROOT / "docs" / "developer"
                     / "PACKAGING.md").read_text(encoding="utf-8")
    assert "release_manifest" in packaging_doc
