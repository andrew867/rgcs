"""C06/C07: BVD extraction + apparatus models (gates G13/G14)."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import apparatus as ap, bvd

TRUE = dict(c0_f=4e-12, r1_ohm=25.0, l1_h=0.012, c1_f=1.6e-14)


def test_bvd_forward_model_resonances():
    d = bvd.derived_parameters(**TRUE)
    f = np.linspace(0.97 * d["fs_hz"], 1.03 * d["fp_hz"], 20001)
    z = np.abs(bvd.bvd_impedance(f, **TRUE))
    assert f[np.argmin(z)] == pytest.approx(d["fs_hz"], rel=1e-4)
    assert f[np.argmax(z)] == pytest.approx(d["fp_hz"], rel=1e-4)
    assert d["fp_hz"] > d["fs_hz"]
    assert 0 < d["k_eff2"] < 1


def test_bvd_synthetic_recovery():
    """Gate G13: parameters recovered from a clean synthetic sweep."""
    d = bvd.derived_parameters(**TRUE)
    f = np.linspace(0.9 * d["fs_hz"], 1.2 * d["fp_hz"], 60001)
    z = np.abs(bvd.bvd_impedance(f, **TRUE))
    out = bvd.extract_bvd(f, z)
    assert out["identifiable"]
    assert out["fs_hz"] == pytest.approx(d["fs_hz"], rel=2e-4)
    assert out["fp_hz"] == pytest.approx(d["fp_hz"], rel=2e-4)
    assert out["c0_f"] == pytest.approx(TRUE["c0_f"], rel=0.05)
    assert out["c1_f"] == pytest.approx(TRUE["c1_f"], rel=0.05)
    assert out["l1_h"] == pytest.approx(TRUE["l1_h"], rel=0.05)
    assert out["k_eff2"] == pytest.approx(d["k_eff2"], rel=0.02)
    assert out["q"] > 0


def test_bvd_identifiability_honesty():
    """A band missing the parallel resonance yields
    INSUFFICIENT_RESOLUTION, never guessed parameters."""
    d = bvd.derived_parameters(**TRUE)
    f = np.linspace(0.9 * d["fs_hz"], 0.999 * d["fs_hz"], 2000)
    z = np.abs(bvd.bvd_impedance(f, **TRUE))
    out = bvd.extract_bvd(f, z)
    assert not out["identifiable"]
    assert out["status"] == "INSUFFICIENT_RESOLUTION"
    assert "c1_f" not in out


def test_bvd_spurious_mode_detection():
    d = bvd.derived_parameters(**TRUE)
    f = np.linspace(0.9 * d["fs_hz"], 1.2 * d["fp_hz"], 60001)
    z = np.abs(bvd.bvd_impedance(f, **TRUE))
    # inject a spurious dip well away from fs
    spur = d["fs_hz"] * 1.12
    z2 = z * (1 - 0.5 * np.exp(-((f - spur) / (0.001 * spur)) ** 2))
    out = bvd.extract_bvd(f, z2)
    assert any(abs(s - spur) / spur < 0.01
               for s in out["spurious_modes_hz"])


def test_wheeler_and_crossed_coils():
    # Wheeler sanity: 40 turns, r=15mm, l=13.2mm -> tens of uH
    l40 = ap.wheeler_inductance_h(40, 0.015, 0.0132)
    assert 1e-5 < l40 < 2e-4
    cc = ap.crossed_coil_coupling()
    assert cc["cross_coupling_ratio"] < 1e-9      # symmetry null
    assert cc["b_axial_of_a_t"] > 0


def test_apparatus_registry_and_artifact_budget():
    reg = ap.apparatus_registry()
    for rid in ("E008", "E009", "E010", "E019", "E004", "E025",
                "E011", "E012", "E013", "E014", "E015", "E016",
                "E017"):
        assert rid in reg, rid
    assert reg["E010"]["status"] == "SOURCE_HYPOTHESIS"   # historical
    art = ap.ordinary_artifact_model(1.0, 4096.0, 1e-6, 2.0, -0.5)
    assert art["em_pickup_peak_v"] == pytest.approx(
        1e-6 * 2 * np.pi * 4096, rel=1e-12)
    assert "no residual claim" in art["rule"]
