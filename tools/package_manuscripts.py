#!/usr/bin/env python3
"""Package the four v3 manuscripts (Agent 09): per-manuscript
CHECKSUMS.json (sha256 of pdf/tex/tables/figures), VERSIONS.json
(toolchain), and BUILD.md (exact build instructions).

Run after tools/make_v3_artifacts.py and the XeLaTeX builds.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAN = REPO / "manuscripts"
NAMES = ["rscs_foundations", "rgcs_crystal_application",
         "software_hardware_plan", "historical_source_companion"]

BUILD_MD = """# Build instructions

1. `python tools/make_v3_artifacts.py`   (regenerates tables/ and figures/
   from the tested libraries -- no number in the text is hand-typed)
2. `xelatex -interaction=nonstopmode {name}.tex`
3. `bibtex {name}`
4. `xelatex -interaction=nonstopmode {name}.tex`  (twice, for refs)

Or `latexmk -xelatex {name}.tex` where latexmk/perl is available.
Fonts: TeX Gyre Pagella/Heros + DejaVu Sans Mono, loaded by filename from
the TeX distribution (no OS font registration needed).
Shared preamble: `../common/rgcs_v3_preamble.tex`; bibliography:
`references/references.bib` + `manuscripts/common/handbooks.bib`.
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tool_version(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=60).stdout.splitlines()
        return out[0].strip() if out else "unknown"
    except Exception:
        return "unavailable"


def main() -> int:
    import numpy
    import yaml as _yaml
    versions = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "xelatex": _tool_version(["xelatex", "--version"]),
        "bibtex": _tool_version(["bibtex", "--version"]),
        "generator": "tools/make_v3_artifacts.py",
    }
    try:
        import matplotlib
        versions["matplotlib"] = matplotlib.__version__
    except Exception:
        pass

    for name in NAMES:
        d = MAN / name
        checks = {}
        targets = [d / f"{name}.pdf", d / f"{name}.tex"]
        targets += sorted((d / "tables").glob("*.tex"))
        targets += sorted((d / "figures").glob("*.pdf"))
        for t in targets:
            if t.exists():
                checks[t.relative_to(d).as_posix()] = _sha(t)
        (d / "CHECKSUMS.json").write_text(
            json.dumps(checks, indent=2, sort_keys=True), encoding="utf-8")
        (d / "VERSIONS.json").write_text(
            json.dumps(versions, indent=2, sort_keys=True),
            encoding="utf-8")
        (d / "BUILD.md").write_text(BUILD_MD.format(name=name),
                                    encoding="utf-8")
        print(f"packaged {name}: {len(checks)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
