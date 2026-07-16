"""C01/C13: polariton model + future interfaces (gates G06/G15)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core import interfaces_future as fi
from rscs2_core.refmodels import polariton as pol

MAT = "reference.exciton_magnon"


def test_hopfield_2x2_analytic_limits():
    """Gate G06: zero coupling -> bare states; resonance -> splitting
    exactly Omega and 50/50 Hopfield fractions; sum rule."""
    bare = pol.hopfield_2x2(2.0, 2.1, 0.0)
    assert bare["lower_ev"] == pytest.approx(2.0)
    assert bare["upper_ev"] == pytest.approx(2.1)
    res = pol.hopfield_2x2(2.0, 2.0, 0.05)
    assert res["splitting_ev"] == pytest.approx(0.05, rel=1e-12)
    for b in (0, 1):
        assert res["hopfield_exciton_fraction"][b] == \
            pytest.approx(0.5, abs=1e-9)
        assert res["hopfield_exciton_fraction"][b] + \
            res["hopfield_photon_fraction"][b] == \
            pytest.approx(1.0, abs=1e-12)
    # linewidth mixing on resonance: average of bare widths
    lw = pol.hopfield_2x2(2.0, 2.0, 0.05, 0.004, 0.001)
    assert lw["lower_linewidth_ev"] == pytest.approx(0.0025,
                                                     rel=1e-6)


def test_angle_dispersion_and_min_splitting():
    """Gate G06/A03: cavity blue-shifts with angle; the minimum
    polariton splitting over the sweep equals the Rabi energy."""
    th = np.linspace(0, 40, 161)
    out = pol.polariton_dispersion(MAT, 2.05, 2.00, 0.04, 1.5, th)
    assert np.all(np.diff(out["cavity_ev"]) > 0)        # blue shift
    assert out["value"]["min_splitting_ev"] == pytest.approx(
        0.04, rel=1e-3)
    # anticrossing: lower branch approaches exciton at large angle
    assert out["lower_ev"][-1] < 2.05 + 1e-9
    assert out["upper_ev"][-1] > out["cavity_ev"][-1] - 1e-9


def test_magnon_third_mode_and_field_channel():
    """A04/A05: three branches; B field moves the magnon-dominated
    branch through the crossing."""
    b0 = pol.hopfield_3x3(2.0, 2.0, 1.99, 0.04, 0.01, b_field_t=0.0,
                          magnon_shift_ev_per_t=0.002)
    b5 = pol.hopfield_3x3(2.0, 2.0, 1.99, 0.04, 0.01, b_field_t=5.0,
                          magnon_shift_ev_per_t=0.002)
    assert len(b0["branches_ev"]) == 3
    assert b5["magnon_level_ev"] == pytest.approx(2.0, abs=1e-12)
    assert b5["branches_ev"] != b0["branches_ev"]
    # fractions normalized per branch
    fr = np.array(b0["fractions"])
    assert np.allclose(fr.sum(axis=0), 1.0)


def test_polarization_channel_rule():
    assert pol.polarization_channel(0.04, 0.5, "TE") == 0.04
    assert pol.polarization_channel(0.04, 0.5, "TM") == \
        pytest.approx(0.04 * math.cos(0.5))
    with pytest.raises(ValueError):
        pol.polarization_channel(0.04, 0.5, "circular")


def test_quartz_rejected_and_transduction_interface_only():
    out = pol.polariton_dispersion("material.alpha_quartz", 2.0, 2.0,
                                   0.04, 1.5, np.array([0.0]))
    assert out["classification"] == "NOT_APPLICABLE"
    tr = pol.transduction_interface(MAT)
    assert tr["classification"] == "INTERFACE_ONLY"
    assert tr["value"] is None
    assert "NOT COMPUTED" in " ".join(tr["declares"])


def test_future_interfaces_emit_no_fake_results():
    """Gate G15: all 11 interfaces registered; every request refuses."""
    assert len(fi.INTERFACES) == 11
    for iid in fi.INTERFACES:
        rec = fi.interface_record(iid)
        assert rec["classification"] == "INTERFACE_ONLY"
        assert rec["value"] is None
        with pytest.raises(fi.FutureInterfaceError,
                           match="no fake result"):
            fi.request_computation(iid, anything=123)
