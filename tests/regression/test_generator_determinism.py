"""Slow regression test: regenerating the golden datasets reproduces the
checked-in CSVs byte-identically (COHERENCE_TEST_MATRIX cross-cutting
requirement `test_generator_deterministic`)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest


@pytest.mark.slow
def test_generator_deterministic(repo_root, golden_dir, tmp_path):
    tool_src = os.path.join(repo_root, "tools",
                            "generate_golden_coherence.py")
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    shutil.copy(tool_src, tools_dir / "generate_golden_coherence.py")
    subprocess.run([sys.executable,
                    str(tools_dir / "generate_golden_coherence.py"),
                    "--no-plots"], check=True, cwd=tmp_path,
                   capture_output=True)
    outdir = tmp_path / "experiments" / "sample_data" / "golden_coherence"

    csvs = sorted(f for f in os.listdir(golden_dir) if f.endswith(".csv"))
    assert csvs, "no golden CSVs found"
    for name in csvs:
        with open(os.path.join(golden_dir, name), "rb") as fh:
            ref = fh.read()
        with open(outdir / name, "rb") as fh:
            new = fh.read()
        assert new == ref, f"regenerated {name} differs from checked-in copy"

    # Manifest datasets section must match exactly (the top-level 'plots'
    # key differs under --no-plots).
    with open(os.path.join(golden_dir, "manifest.json")) as fh:
        ref_m = json.load(fh)
    with open(outdir / "manifest.json") as fh:
        new_m = json.load(fh)
    assert new_m["datasets"] == ref_m["datasets"]
    assert new_m["master_seed"] == ref_m["master_seed"]
