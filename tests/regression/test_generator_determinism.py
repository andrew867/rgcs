"""Slow regression tests: regenerating the golden datasets reproduces the
checked-in CSVs (COHERENCE_TEST_MATRIX cross-cutting requirement).

Two tiers (NR3-001 / D-V3-04 policy):

* ``test_generator_numerically_equivalent`` — PORTABLE. Regenerated CSVs
  must match the checked-in goldens to the PRINTED precision: the CSVs
  serialize 8 decimal places, so cross-platform last-ulp float drift can
  move a printed value by at most one unit in the 8th decimal (1e-8).
  Numeric cells must agree within atol 2e-8 (rtol 0); string cells,
  headers, shapes, and the manifest datasets/seed must match exactly.
  Runs on every platform and every CI job.

* ``test_generator_deterministic`` — BYTE EQUALITY. Requires the archived
  v2 build environment (Python 3.11.15/GCC 13.3.0, numpy 2.4.4, scipy
  1.17.1, and its libm: archive/v2.0.0/release/PROVENANCE.json); hosted
  runners drift at the last digit even with the libraries pinned
  (D-V3-04), so hosted CI deselects exactly this node id. The
  byte-exactness of the shipped goldens was verified at v2 release and is
  recorded by checksum in the v2 provenance.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

# One unit in the last printed decimal: the goldens serialize 8 decimal
# places, so platform last-ulp drift moves a printed cell by <= 1e-8.
PRINT_ATOL = 2e-8


@pytest.fixture(scope="module")
def regenerated(repo_root, tmp_path_factory):
    """Run the golden generator once into a temp tree; share the output."""
    tmp_path = tmp_path_factory.mktemp("golden_regen")
    tool_src = os.path.join(repo_root, "tools",
                            "generate_golden_coherence.py")
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    shutil.copy(tool_src, tools_dir / "generate_golden_coherence.py")
    subprocess.run([sys.executable,
                    str(tools_dir / "generate_golden_coherence.py"),
                    "--no-plots"], check=True, cwd=tmp_path,
                   capture_output=True)
    return tmp_path / "experiments" / "sample_data" / "golden_coherence"


def _read_csv(path):
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def _cell_equal(ref: str, new: str) -> bool:
    if ref == new:
        return True
    try:
        return abs(float(new) - float(ref)) <= PRINT_ATOL
    except ValueError:
        return False       # non-numeric cells must match exactly


def _deep_equal(ref, new) -> bool:
    """Recursive manifest comparison: floats within PRINT_ATOL (computed
    'expected' values drift at the last digits across platforms exactly
    like the CSV cells); every other type exact."""
    if isinstance(ref, float) or isinstance(new, float):
        try:
            return abs(float(new) - float(ref)) <= PRINT_ATOL
        except (TypeError, ValueError):
            return False
    if isinstance(ref, dict) and isinstance(new, dict):
        return (ref.keys() == new.keys()
                and all(_deep_equal(ref[k], new[k]) for k in ref))
    if isinstance(ref, list) and isinstance(new, list):
        return (len(ref) == len(new)
                and all(_deep_equal(r, n) for r, n in zip(ref, new)))
    return ref == new


@pytest.mark.slow
def test_generator_numerically_equivalent(golden_dir, regenerated):
    """Portable determinism: string cells exact, numeric cells within one
    unit of the printed precision, manifest datasets/seed identical."""
    csvs = sorted(f for f in os.listdir(golden_dir) if f.endswith(".csv"))
    assert csvs, "no golden CSVs found"
    for name in csvs:
        ref_header, ref = _read_csv(os.path.join(golden_dir, name))
        new_header, new = _read_csv(regenerated / name)
        assert new_header == ref_header, f"{name}: header drift"
        assert len(new) == len(ref), f"{name}: row-count drift"
        for i, (rrow, nrow) in enumerate(zip(ref, new)):
            assert len(nrow) == len(rrow), f"{name}: row {i} column drift"
            for j, (rc, nc) in enumerate(zip(rrow, nrow)):
                assert _cell_equal(rc, nc), (
                    f"{name}: row {i} col {j} drift beyond printed "
                    f"precision ({rc!r} vs {nc!r})")

    with open(os.path.join(golden_dir, "manifest.json")) as fh:
        ref_m = json.load(fh)
    with open(regenerated / "manifest.json") as fh:
        new_m = json.load(fh)
    assert _deep_equal(ref_m["datasets"], new_m["datasets"]), \
        "manifest datasets drift beyond printed precision"
    assert new_m["master_seed"] == ref_m["master_seed"]


@pytest.mark.slow
def test_generator_deterministic(golden_dir, regenerated):
    """Byte equality — archived v2 reference environment ONLY (see module
    docstring; hosted CI deselects exactly this node id per D-V3-04)."""
    csvs = sorted(f for f in os.listdir(golden_dir) if f.endswith(".csv"))
    assert csvs, "no golden CSVs found"
    for name in csvs:
        with open(os.path.join(golden_dir, name), "rb") as fh:
            ref = fh.read()
        with open(regenerated / name, "rb") as fh:
            new = fh.read()
        assert new == ref, f"regenerated {name} differs from checked-in copy"
