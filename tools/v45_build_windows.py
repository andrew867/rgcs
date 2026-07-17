"""Windows Workbench build (v4.5, P03/P05).

Produces, in order, each gated on the tool actually being present:

  1. the frozen onedir app        (PyInstaller — installed)
  2. a smoke-check of the frozen EXE   (launch it, --smoke-check)
  3. the portable ZIP              (zip of dist/RGCSWorkbench + workbook)
  4. the public Master Workbook    (openpyxl)
  5. the Inno Setup installer EXE  (ONLY if `iscc` is on PATH;
                                    otherwise recorded as a blocker)
  6. SHA256SUMS over every produced asset

Honest gating: absence of a tool is reported, never faked. An
unsigned installer is labelled unsigned. Clean-machine verification is
NOT claimed by this script — it can only be done on a clean machine
by a human (or CI VM).

    python tools/v45_build_windows.py [--version 4.5.0] [--skip-freeze]
Writes release/v45/ and prints a machine-readable status block.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "release" / "v45"
DIST = ROOT / "dist" / "RGCSWorkbench"


def _run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True,
                          text=True, **kw)


def version() -> str:
    if "--version" in sys.argv:
        return sys.argv[sys.argv.index("--version") + 1]
    import re
    m = re.search(r'^version = "([^"]+)"',
                  (ROOT / "pyproject.toml").read_text(
                      encoding="utf-8"), re.M)
    return m.group(1) if m else "0.0.0"


def freeze() -> dict:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        return {"step": "freeze", "ok": False,
                "blocker": "PyInstaller not installed"}
    r = _run([sys.executable, "-m", "PyInstaller",
              "packaging/RGCSWorkbench.spec", "--noconfirm",
              "--distpath", str(ROOT / "dist"),
              "--workpath", str(ROOT / "build" / "pyi")])
    exe = DIST / "RGCSWorkbench.exe"
    return {"step": "freeze", "ok": exe.exists(),
            "exe": str(exe) if exe.exists() else None,
            "returncode": r.returncode,
            "stderr_tail": r.stderr[-600:] if not exe.exists()
            else ""}


def smoke_frozen() -> dict:
    exe = DIST / "RGCSWorkbench.exe"
    if not exe.exists():
        return {"step": "smoke_frozen", "ok": False,
                "blocker": "no frozen exe"}
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([str(exe), "--doctor"], capture_output=True,
                       text=True, env=env, timeout=180)
    ok = r.returncode == 0 and "RGCS Workbench diagnostics" in \
        r.stdout
    return {"step": "smoke_frozen", "ok": ok,
            "doctor_tail": r.stdout[-300:]}


def portable_zip(ver: str) -> dict:
    if not DIST.exists():
        return {"step": "portable_zip", "ok": False,
                "blocker": "no frozen build to zip"}
    OUT.mkdir(parents=True, exist_ok=True)
    zpath = OUT / f"RGCS-Workbench-{ver}-Windows-x64-portable.zip"
    # regenerate the workbook into the portable payload
    from rgcs_workbench.workbook import generate
    wb_path = DIST / "templates"
    wb_path.mkdir(exist_ok=True)
    generate(version=ver).save(
        wb_path / "RGCS_Master_Evidence_Workbook.xlsx")
    (DIST / "PORTABLE_README.txt").write_text(
        "RGCS Workbench (portable). Unzip anywhere and run "
        "RGCSWorkbench.exe. Per-user data goes to your Documents\\"
        "RGCS Workspace. No install, no admin, no telemetry, no "
        "auto-start. UNSIGNED build. Nothing physical is validated.\n",
        encoding="utf-8")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in DIST.rglob("*"):
            if p.is_file():
                z.write(p, Path("RGCSWorkbench") /
                        p.relative_to(DIST))
    return {"step": "portable_zip", "ok": True, "path": str(zpath),
            "size": zpath.stat().st_size}


def workbook_asset(ver: str) -> dict:
    from rgcs_workbench.workbook import generate
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "RGCS_Master_Evidence_Workbook.xlsx"
    generate(version=ver, include_private=False).save(p)
    return {"step": "workbook", "ok": True, "path": str(p),
            "public": True}


def inno_installer(ver: str) -> dict:
    iscc = shutil.which("iscc") or shutil.which("ISCC")
    if not iscc:
        return {"step": "inno_installer", "ok": False,
                "blocker": "Inno Setup (iscc) not on PATH; the "
                           ".iss script is provided but the installer "
                           "EXE cannot be compiled in this "
                           "environment", "signed": False}
    if not DIST.exists():
        return {"step": "inno_installer", "ok": False,
                "blocker": "no frozen build"}
    env = dict(os.environ, RGCS_VERSION=ver,
               RGCS_BUILD_ROOT=str(DIST),
               RGCS_OUTPUT_ROOT=str(OUT))
    r = subprocess.run([iscc, str(ROOT / "packaging" /
                                  "RGCS_Workbench.iss")],
                       cwd=ROOT, capture_output=True, text=True,
                       env=env)
    setup = OUT / (f"RGCS-Workbench-{ver}-Windows-x64-Setup.exe")
    return {"step": "inno_installer", "ok": setup.exists(),
            "path": str(setup) if setup.exists() else None,
            "signed": False, "returncode": r.returncode}


def checksums() -> dict:
    # manifest of the downloadable release deliverables only; the
    # transient build log is not an asset and is excluded.
    skip = {"SHA256SUMS.txt", "build_report.json"}
    lines = []
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name not in skip:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            lines.append(f"{h}  {p.name}")
    (OUT / "SHA256SUMS.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {"step": "checksums", "ok": bool(lines),
            "n_assets": len(lines)}


def main() -> int:
    ver = version()
    steps = []
    if "--skip-freeze" not in sys.argv:
        steps.append(freeze())
    steps.append(smoke_frozen())
    steps.append(portable_zip(ver))
    steps.append(workbook_asset(ver))
    steps.append(inno_installer(ver))
    steps.append(checksums())
    report = {"version": ver, "steps": steps,
              "portable_zip_built": any(
                  s["step"] == "portable_zip" and s["ok"]
                  for s in steps),
              "installer_exe_built": any(
                  s["step"] == "inno_installer" and s["ok"]
                  for s in steps),
              "clean_machine_verified": False,
              "signed": False}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "build_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items()
                      if k != "steps"}, indent=2))
    for s in steps:
        mark = "ok" if s.get("ok") else \
            f"BLOCKED ({s.get('blocker', '?')})"
        print(f"  {s['step']}: {mark}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
