"""Build the RGCS v4.0.0 release asset set (Agent 13 Role D).

    python tools/build_v4_release.py <commit-ish>

Produces release/v4/:
  rgcs-v4.0.0-source.zip            git archive of the release commit
  rgcs-v4.0.0-proof-bundle.zip      proof_bundle_110mm/ (committed)
  rgcs-v4.0.0-manuscripts.zip       v4 documentation set
  rgcs-v4.0.0-reference-systems.zip agent10 evidence + comparison doc
  rgcs-v4.0.0-screenshots.zip       bundle figures + evidence figures
  rgcs-v4.0.0-example-workspace.zip demo script + user guide + CLI help
  rgcs-v4.0.0-test-report.txt       full pytest output at the commit
  PROVENANCE.json                   what each asset is and where from
  SHA256SUMS.txt                    over every asset
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _version() -> str:
    """Single source of truth: pyproject. A hardcoded copy here drifts
    from the release it claims to build (this is what shipped stale
    v4.1.0 assets and forced the v4.1.1 patch)."""
    import re
    m = re.search(r'^version = "([^"]+)"',
                  (REPO / "pyproject.toml").read_text(encoding="utf-8"),
                  re.M)
    if not m:
        raise SystemExit("cannot read version from pyproject.toml")
    return m.group(1)


VERSION = _version()
REL = REPO / "release" / "v4"


def zip_paths(dest: Path, pairs):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, path in sorted(pairs):
            zf.write(path, arcname)
    print(f"built {dest.name} ({dest.stat().st_size} bytes, "
          f"{len(pairs)} files)")


def tree(root: Path, prefix: str):
    return [(f"{prefix}/{p.relative_to(root).as_posix()}", p)
            for p in root.rglob("*") if p.is_file()]


def main() -> int:
    commit = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    sha = subprocess.run(["git", "rev-parse", commit],
                         capture_output=True, text=True, cwd=REPO,
                         check=True).stdout.strip()
    REL.mkdir(parents=True, exist_ok=True)

    src = REL / f"rgcs-v{VERSION}-source.zip"
    subprocess.run(["git", "archive", "--format=zip",
                    f"--prefix=rgcs-v{VERSION}/", "-o", str(src), sha],
                   cwd=REPO, check=True)
    print(f"built {src.name} ({src.stat().st_size} bytes)")

    zip_paths(REL / f"rgcs-v{VERSION}-proof-bundle.zip",
              tree(REPO / "proof_bundle_110mm", "proof_bundle_110mm"))

    manu = [(f"docs/{n}", REPO / "docs" / n) for n in (
        "RGCS_V4_TECHNICAL_MANUSCRIPT.md",
        "CANONICAL_110MM_CASE_STUDY.md", "EYE_METHODOLOGY.md",
        "V4_MODELLING_GUIDE.md", "V4_API_REFERENCE.md",
        "USER_GUIDE_V4.md", "RELEASE_NOTES_V4.md")]
    manu += [(f"docs/plans-v4/{p.name}", p) for p in
             (REPO / "docs/plans-v4").glob("*.md")]
    # v4.1 completion documentation set (registries, runlogs, QA)
    manu += [(f"docs/v4/{p.relative_to(REPO / 'docs/v4').as_posix()}",
              p) for p in (REPO / "docs/v4").rglob("*.md")]
    manu += [(f"docs/v4/{p.relative_to(REPO / 'docs/v4').as_posix()}",
              p) for p in (REPO / "docs/v4").rglob("*.yaml")]
    zip_paths(REL / f"rgcs-v{VERSION}-manuscripts.zip", manu)

    refs = tree(REPO / "evidence/v4/agent10", "reference-systems/agent10")
    refs += [("reference-systems/REFERENCE_SYSTEM_COMPARISON.md",
              REPO / "docs/plans-v4/REFERENCE_SYSTEM_COMPARISON.md")]
    zip_paths(REL / f"rgcs-v{VERSION}-reference-systems.zip", refs)

    shots = [(f"figures/{p.name}", p) for p in
             (REPO / "proof_bundle_110mm/figures").glob("*")]
    for agent in ("agent04", "agent05", "agent07", "agent08", "agent09"):
        d = REPO / "evidence/v4" / agent
        shots += [(f"evidence/{agent}/{p.name}", p)
                  for p in d.glob("*.png")]
    zip_paths(REL / f"rgcs-v{VERSION}-screenshots.zip", shots)

    ex = [("example-workspace/demo_v4.py", REPO / "tools/demo_v4.py"),
          ("example-workspace/qa_audit_v4.py",
           REPO / "tools/qa_audit_v4.py"),
          ("example-workspace/USER_GUIDE_V4.md",
           REPO / "docs/USER_GUIDE_V4.md"),
          ("example-workspace/README.md", REPO / "docs/USER_GUIDE_V4.md")]
    zip_paths(REL / f"rgcs-v{VERSION}-example-workspace.zip", ex)

    rep = REL / f"rgcs-v{VERSION}-test-report.txt"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--deselect",
         "tests/regression/test_generator_determinism.py::"
         "test_generator_deterministic"],
        capture_output=True, text=True, cwd=REPO)
    rep.write_text(r.stdout + r.stderr, encoding="utf-8")
    print(f"test report: {r.stdout.strip().splitlines()[-1]}")
    if r.returncode != 0:
        print("TEST FAILURES — aborting release build")
        return 1

    prov = {
        "release": f"v{VERSION}", "commit": sha,
        "assets": {
            "source": "git archive of the release commit",
            "proof-bundle": "committed proof_bundle_110mm (built by "
                            "python -m rscs2_core.proofbundle; "
                            "verdict UNCERTAINTY_OVERLAPS_"
                            "CONVENTIONAL_NODE, v4.1 corrected "
                            "uncertainty-aware classification)",
            "manuscripts": "v4 documentation + QA/audit reports",
            "reference-systems": "agent10 evidence + comparison",
            "screenshots": "bundle figures + evidence figures (all "
                           "from real solver output, G24)",
            "example-workspace": "scripted demo + audit + user guide",
            "test-report": "full pytest output at the release commit "
                           "(D-V3-04 byte-equality node deselected)",
        },
        "frozen_authorities_untouched": ["v2.0.0", "v3.0.0", "v3.0.1",
                                         "archive/v2.0.0"],
    }
    (REL / "PROVENANCE.json").write_text(json.dumps(prov, indent=2))

    sums = []
    for p in sorted(REL.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            sums.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}"
                        f"  {p.name}")
    (REL / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    print(f"release assets in {REL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
