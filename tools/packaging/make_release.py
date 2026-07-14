#!/usr/bin/env python3
"""Build the RGCS v2 release artifacts into release/ (Sub-Agent 09).

Steps (idempotent; run from anywhere):
  1. example workspace + sample analysis via the vertical-slice path
     -> release/example_workspace_bundle.zip
  2. manuscript source bundle WITH CHECKSUMS.json + VERSIONS.json
     (QA-D-10) -> manuscript/rgcs_v2_manuscript_source_bundle.zip,
     copied to release/
  3. manuscript PDF -> release/rgcs_v2.pdf
  4. source zip (excludes .git, build/, release/, __pycache__, egg-info)
     -> release/rgcs-v2-src-<version>.zip
  5. release/PROVENANCE.json (input sha256s from docs/PROVENANCE_REGISTER.csv,
     build environment, package versions, date)
  6. release/SHA256SUMS.txt covering EVERY file under release/ (recursive,
     including the linux build tree)

Test results (release/test_results.xml, release/test_report.md) are
produced by running pytest separately; see docs/RELEASE_CHECKLIST.md.
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
RELEASE = REPO / "release"
VERSION = "2.0.0"
DATE = "2026-07-14"

SRC_EXCLUDE_DIRS = {".git", "build", "release", "__pycache__",
                    "rgcs_v2.egg-info", ".pytest_cache", ".hypothesis"}
SRC_EXCLUDE_SUFFIXES = {".pyc"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def versions_dict() -> dict:
    import numpy, scipy, pydantic, pytest  # noqa: E401
    from rgcs_core.provenance import MODEL_VERSION
    import rgcs_desktop
    vers = {
        "rgcs_v2": VERSION,
        "rgcs_core_model_version": MODEL_VERSION,
        "rgcs_desktop": rgcs_desktop.__version__,
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pydantic": pydantic.__version__,
        "pytest": pytest.__version__,
    }
    try:
        import hypothesis
        vers["hypothesis"] = hypothesis.version.__version__
    except Exception:
        pass
    try:
        import PySide6
        vers["PySide6"] = PySide6.__version__
    except Exception:
        pass
    return vers


# ---------------------------------------------------------------- step 1
def build_example_bundle() -> Path:
    """Create an example workspace via the same path as the vertical-slice
    integration test and export its reproducibility bundle."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import shutil
    import tempfile

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])  # noqa: F841
    from rgcs_desktop.app.context import AppContext
    from rgcs_desktop.app.main_window import MainWindow

    sample_csv = (REPO / "experiments" / "sample_data" / "golden_coherence"
                  / "case_c_decaying_sinusoid.csv")
    sample_manifest = (REPO / "experiments" / "sample_data"
                       / "modal_survey_run_manifest.json")

    tmp = Path(tempfile.mkdtemp(prefix="rgcs_example_"))
    ctx = AppContext()
    ctx.create_workspace(tmp / "example-workspace", "example-workspace")
    win = MainWindow(ctx)
    try:
        # specimen
        ed = win.panels["Specimen editor"]
        ed.specimen_id.setText("SP-EXAMPLE-Q154")
        ed.c_length.setValue(154.05)
        ed.c_dw.setValue(34.0)
        ed.c_dn.setValue(25.0)
        ed.c_measured_mass.setText("154.0")
        ed.save_specimen()
        # source import
        win.panels["Sources"].import_file(str(sample_manifest),
                                          note="sample manifest")
        # spectrum
        sp = win.panels["Compact-mode spectrum"]
        sp.f_b.setValue(4096.0)
        sp.n_max.setValue(6)
        sp.compute()
        sp.save_result()
        # experiment
        b = win.panels["Experiment builder"]
        b.refresh()
        b.run_id.setText("RUN-EXAMPLE-0001")
        b.hypotheses.setText("H-01, H-09")
        b.n_runs.setValue(120)
        b.duration_s.setValue(120.0)
        b.drive_off_s.setValue(30.0)
        b.data_csv.setText(str(sample_csv))
        _m, errors = b.build_and_validate()
        assert errors == [], errors
        b.save_experiment()
        # coherence job
        ca = win.panels["Coherence analyzer"]
        ca.csv_path.setText(str(sample_csv))
        ca.i_col.setText("I")
        ca.q_col.setText("Q")
        job_id = ca.run_analysis()
        rec = ctx.job_manager.wait(job_id, timeout_s=120.0)
        assert rec.status.value == "succeeded", rec.error
        # report + bundle
        rp = win.panels["Report / export"]
        rp.generate()
        bundle_path = rp.export()
        from rgcs_desktop.services.bundle import verify_bundle
        assert verify_bundle(bundle_path)["ok"]
        dest = RELEASE / "example_workspace_bundle.zip"
        shutil.copy2(bundle_path, dest)
        return dest
    finally:
        win.close()
        ctx.shutdown()


# ---------------------------------------------------------------- step 2
def build_manuscript_source_bundle() -> Path:
    man = REPO / "manuscript"
    members = [man / "rgcs_v2.tex", man / "references.bib"]
    members += sorted((man / "tables").glob("*.tex"))
    members += sorted((man / "figures").glob("*.pdf"))
    members += sorted((man / "figures").glob("*.json"))
    checksums = {}
    out = man / "rgcs_v2_manuscript_source_bundle.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in members:
            arc = str(p.relative_to(REPO))
            zf.write(p, arc)
            checksums[arc] = sha256_file(p)
        zf.writestr("CHECKSUMS.json",
                    json.dumps(checksums, indent=2, sort_keys=True))
        zf.writestr("VERSIONS.json",
                    json.dumps({**versions_dict(), "date": DATE,
                                "builder": "tools/packaging/make_release.py"},
                               indent=2, sort_keys=True))
    import shutil
    shutil.copy2(out, RELEASE / out.name)
    return out


# ---------------------------------------------------------------- step 4
def build_source_zip() -> Path:
    out = RELEASE / f"rgcs-v2-src-{VERSION}.zip"
    if out.exists():
        out.unlink()
    files = []
    for root, dirs, names in os.walk(REPO):
        dirs[:] = sorted(d for d in dirs if d not in SRC_EXCLUDE_DIRS)
        for n in sorted(names):
            p = Path(root) / n
            if p.suffix in SRC_EXCLUDE_SUFFIXES:
                continue
            files.append(p)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, f"rgcs-v2/{p.relative_to(REPO)}")
    return out


# ---------------------------------------------------------------- step 5
def build_provenance() -> Path:
    inputs = []
    with open(REPO / "docs" / "PROVENANCE_REGISTER.csv", newline="",
              encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            inputs.append({"path": row["path"], "sha256": row["sha256"],
                           "size_bytes": int(row["size_bytes"]),
                           "role": row["role"], "version": row["version"]})
    prov = {
        "project": "RGCS v2",
        "version": VERSION,
        "date": DATE,
        "builder": "tools/packaging/make_release.py (Sub-Agent 09)",
        "build_environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version,
        },
        "package_versions": versions_dict(),
        "input_sources": inputs,
        "notes": [
            "input_sources sha256s are copied from docs/PROVENANCE_REGISTER.csv "
            "(18 entries, verified 18/18 by independent QA on 2026-07-14)",
            "release file checksums: release/SHA256SUMS.txt",
            "test results: release/test_results.xml (JUnit) and "
            "release/test_report.md",
        ],
    }
    out = RELEASE / "PROVENANCE.json"
    out.write_text(json.dumps(prov, indent=2, sort_keys=False))
    return out


# ---------------------------------------------------------------- step 6
def build_sha256sums() -> Path:
    out = RELEASE / "SHA256SUMS.txt"
    if out.exists():
        out.unlink()
    lines = []
    for p in sorted(RELEASE.rglob("*")):
        if p.is_file() and p != out:
            lines.append(f"{sha256_file(p)}  {p.relative_to(RELEASE)}")
    out.write_text("\n".join(lines) + "\n")
    return out


def main() -> int:
    RELEASE.mkdir(exist_ok=True)
    import shutil
    print("1. example workspace bundle ...")
    print("   ->", build_example_bundle())
    print("2. manuscript source bundle (with checksums/versions) ...")
    print("   ->", build_manuscript_source_bundle())
    print("3. manuscript PDF ...")
    shutil.copy2(REPO / "manuscript" / "rgcs_v2.pdf", RELEASE / "rgcs_v2.pdf")
    print("   ->", RELEASE / "rgcs_v2.pdf")
    print("4. source zip ...")
    print("   ->", build_source_zip())
    print("5. provenance manifest ...")
    print("   ->", build_provenance())
    print("6. SHA256SUMS ...")
    print("   ->", build_sha256sums())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
