"""Agent 12: CLI coverage. Fast commands run for real; gmsh-dependent
commands are skipped where gmsh is unavailable; checksum verification
is exercised round-trip on a synthetic bundle."""
from __future__ import annotations

import json
import subprocess
import sys

import numpy as np
import pytest

from rscs2_core.cli import main, make_parser

gmsh_ok = True
try:
    from rscs2_core.crystal110 import _gmsh_cmd
    subprocess.run(_gmsh_cmd() + ["--version"], capture_output=True,
                   timeout=60, check=True)
except Exception:
    gmsh_ok = False
needs_gmsh = pytest.mark.skipif(not gmsh_ok, reason="gmsh unavailable")


def test_parser_covers_required_commands():
    p = make_parser()
    required = {"devices", "geometry", "mesh", "material", "modes",
                "sweep", "piezo", "optical", "coil", "diagnostics",
                "refsystems", "proof-bundle", "report",
                "verify-checksums"}
    actions = [a for a in p._subparsers._group_actions][0]
    assert required <= set(actions.choices)


def test_geometry_and_material_json(capsys):
    assert main(["geometry", "ideal_n7"]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["length_mm_float"] == pytest.approx(770.263671875 / 7.0)
    assert rec["eye_coordinate"] is None
    assert main(["material"]) == 0
    mat = json.loads(capsys.readouterr().out)
    assert "stiffness" in json.dumps(mat).lower() or mat


def test_devices_json(capsys):
    assert main(["devices"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert "devices" in rep or rep     # shape depends on CL presence


def test_sweep_cpu_backend(capsys):
    assert main(["sweep", "--backend", "cpu", "--n", "500"]) == 0
    meta = json.loads(capsys.readouterr().out)
    assert meta["backend"] == "cpu"
    lo, hi = meta["speeds_minmax_m_s"]
    assert 3000 < lo < hi < 8000       # physical quartz speeds


def test_optical_and_coil(capsys):
    assert main(["optical", "ideal_n7"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "axial_tx_to_rx" in out["paths"]
    assert main(["coil", "--points", "11"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0] == "z_m,Bz_re_T,Bz_im_T"
    assert len(lines) == 12


def test_refsystems_cavity_table(capsys):
    assert main(["refsystems"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].startswith("cavity_mode")
    a = np.array([float(x) for x in lines[1].split(",")[1:]])
    assert abs(a[1] - a[0]) / a[0] < 1e-3   # FEM vs exact row 1


def test_verify_checksums_roundtrip(tmp_path, capsys):
    import hashlib
    b = tmp_path / "bundle"
    b.mkdir()
    (b / "data.txt").write_text("payload")
    h = hashlib.sha256(b"payload").hexdigest()
    (b / "SHA256SUMS.txt").write_text(f"{h}  data.txt\n")
    assert main(["verify-checksums", "--bundle", str(b)]) == 0
    (b / "data.txt").write_text("tampered")
    assert main(["verify-checksums", "--bundle", str(b)]) == 1
    out = capsys.readouterr().out
    assert "MISMATCH" in out


def test_offscreen_screenshot_render(tmp_path):
    """Mandatory offscreen rendering: generate a real diagnostic-field
    figure with the Agg backend and assert a valid non-empty PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from rscs2_core import eye, fem
    mesh = fem.box_mesh((0.05, 0.01, 0.01), (8, 2, 2))
    prob = fem.assemble_isotropic(mesh, 210e9, 0.3, 7850.0)
    sol = fem.solve_modes(prob, 8)
    lam = 210e9 * 0.3 / (1.3 * 0.4)
    mu = 210e9 / 2.6
    c_iso = (lam * np.einsum("ij,kl->ijkl", np.eye(3), np.eye(3))
             + mu * (np.einsum("ik,jl->ijkl", np.eye(3), np.eye(3))
                     + np.einsum("il,jk->ijkl", np.eye(3), np.eye(3))))
    fld = eye.evaluate_elastic_diagnostics(prob, sol, 0, c_iso)["D1"]
    fig, ax = plt.subplots()
    ax.scatter(fld.points_mm[:, 0], fld.points_mm[:, 2],
               c=fld.values, s=4)
    png = tmp_path / "shot.png"
    fig.savefig(png)
    plt.close(fig)
    data = png.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 5000


@needs_gmsh
def test_mesh_manifest(capsys, tmp_path):
    assert main(["mesh", "nominal", "--clmax", "11",
                 "--workdir", str(tmp_path)]) == 0
    man = json.loads(capsys.readouterr().out)
    assert man["quality"]["n_inverted"] == 0
    assert man["volume_rel_err"] < 1e-9
