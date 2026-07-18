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


def _write_stamp(ver: str) -> dict:
    from rgcs_desktop.build_meta import write_stamp
    from datetime import datetime, timezone
    return write_stamp(ROOT, ver,
                       datetime.now(timezone.utc).isoformat(
                           timespec="seconds"))


def _dist_stamp() -> dict | None:
    stamp = DIST / "_internal" / "_build_stamp.json"
    if not stamp.exists():
        return None
    return json.loads(stamp.read_text(encoding="utf-8"))


def dist_is_current() -> tuple[bool, str]:
    """A dist/ tree may only be packaged if its embedded source hash
    matches the current working tree. This is the guard that makes a
    stale --skip-freeze impossible (the v4.5.0/1 failure)."""
    from rgcs_desktop.build_meta import compute_source_hash
    d = _dist_stamp()
    if d is None:
        return False, "dist/ has no _build_stamp.json (never frozen or " \
                      "frozen before build-info existed)"
    cur = compute_source_hash(ROOT)
    if d.get("source_hash") != cur:
        return (False, f"dist/ source_hash {str(d.get('source_hash'))[:12]} "
                f"!= current {cur[:12]} -- source changed since the "
                f"freeze; re-freeze (do NOT --skip-freeze)")
    return True, "dist/ matches current source"


def freeze(ver: str) -> dict:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        return {"step": "freeze", "ok": False,
                "blocker": "PyInstaller not installed"}
    stamp = _write_stamp(ver)   # bundled by the spec, read by --build-info
    r = _run([sys.executable, "-m", "PyInstaller",
              "packaging/RGCSWorkbench.spec", "--noconfirm",
              "--distpath", str(ROOT / "dist"),
              "--workpath", str(ROOT / "build" / "pyi")])
    exe = DIST / "RGCSWorkbench.exe"
    return {"step": "freeze", "ok": exe.exists(),
            "exe": str(exe) if exe.exists() else None,
            "source_hash": stamp["source_hash"][:12],
            "git_commit": stamp["git_commit"][:12],
            "returncode": r.returncode,
            "stderr_tail": r.stderr[-600:] if not exe.exists()
            else ""}


def smoke_frozen() -> dict:
    exe = DIST / "RGCSWorkbench.exe"
    if not exe.exists():
        return {"step": "smoke_frozen", "ok": False,
                "blocker": "no frozen exe"}
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    from rgcs_desktop.build_meta import compute_source_hash
    cur_hash = compute_source_hash(ROOT)
    # --doctor: offline diagnostics; --smoke-check: constructs the full
    # MainWindow (every panel) and runs a real background job, so it
    # catches missing bundled data files that --doctor never touches;
    # --build-info: proves the frozen binary was built from THIS source
    # (source_hash match) -- the anti-stale check.
    doc = subprocess.run([str(exe), "--doctor"], capture_output=True,
                         text=True, env=env, timeout=180)
    smk = subprocess.run([str(exe), "--smoke-check"],
                         capture_output=True, text=True, env=env,
                         timeout=300)
    bi = subprocess.run([str(exe), "--build-info"], capture_output=True,
                        text=True, env=env, timeout=120)
    try:
        info = json.loads(bi.stdout)
    except Exception:  # noqa: BLE001
        info = {}
    hash_ok = info.get("source_hash") == cur_hash
    ok = (doc.returncode == 0
          and "RGCS Workbench diagnostics" in doc.stdout
          and smk.returncode == 0
          and "panels constructed OK" in smk.stdout
          and bi.returncode == 0 and hash_ok)
    return {"step": "smoke_frozen", "ok": ok,
            "frozen_source_hash": info.get("source_hash", "")[:12]
            if isinstance(info.get("source_hash"), str) else "",
            "current_source_hash": cur_hash[:12],
            "source_hash_match": hash_ok,
            "doctor_tail": doc.stdout[-200:],
            "smoke_tail": (smk.stdout or smk.stderr)[-400:]}


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


def _find_iscc() -> str | None:
    iscc = shutil.which("iscc") or shutil.which("ISCC")
    if iscc:
        return iscc
    # Inno Setup installs ISCC.exe here but does not add it to PATH.
    for base in (os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                 os.environ.get("ProgramFiles", r"C:\Program Files")):
        for ver_dir in ("Inno Setup 7", "Inno Setup 6", "Inno Setup 5"):
            cand = Path(base) / ver_dir / "ISCC.exe"
            if cand.exists():
                return str(cand)
    return None


def inno_installer(ver: str) -> dict:
    iscc = _find_iscc()
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
        steps.append(freeze(ver))
    else:
        # refuse to re-package a dist/ that no longer matches the source
        current, why = dist_is_current()
        steps.append({"step": "stale_guard", "ok": current,
                      "detail": why})
        if not current:
            print("REFUSING --skip-freeze: " + why, file=sys.stderr)
            report = {"version": ver, "steps": steps,
                      "portable_zip_built": False,
                      "installer_exe_built": False,
                      "clean_machine_verified": False, "signed": False,
                      "aborted": "stale dist/"}
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "build_report.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8")
            print("  stale_guard: BLOCKED (" + why + ")")
            return 2
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
