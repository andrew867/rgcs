"""Agent M14: optical channel ablation + hidden-order tests."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core import optics_channels as oc

RCP = (1 / math.sqrt(2), 1j / math.sqrt(2))
LCP = (1 / math.sqrt(2), -1j / math.sqrt(2))
BASE = oc.OpticalExcitation(propagation=(0, 1, 0), jones=(1.0, 0.0),
                            intensity_w_m2=2.0)


def test_channel_values_and_unregistered_rejected():
    assert BASE.channel("helicity") == 0.0
    rcp = oc.OpticalExcitation(jones=RCP)
    assert rcp.channel("helicity") == pytest.approx(1.0)
    assert oc.OpticalExcitation(jones=LCP).channel(
        "helicity") == pytest.approx(-1.0)
    hk = BASE.channel("hbar_k")
    assert np.linalg.norm(hk) == pytest.approx(
        1.054571817e-34 * 2 * math.pi / 1064e-9, rel=1e-9)
    with pytest.raises(KeyError, match="unregistered"):
        BASE.channel("torsion_field")


def test_ablation_touches_only_declared_fields():
    rev = BASE.ablate("propagation", propagation=(0, -1, 0))
    assert rev.jones == BASE.jones
    assert rev.intensity_w_m2 == BASE.intensity_w_m2
    with pytest.raises(ValueError, match="may only touch"):
        BASE.ablate("propagation", jones=RCP)
    with pytest.raises(KeyError):
        BASE.ablate("hbar_k")        # derived channel: not ablatable


def test_one_channel_at_a_time_responses():
    """Each mechanism responds ONLY to its declared channels."""
    m = oc.MECHANISMS
    # direction reversal: IOME flips, others unchanged
    rev = BASE.ablate("propagation", propagation=(0, -1, 0))
    assert m["iome_linipo4"].respond(rev) == \
        -m["iome_linipo4"].respond(BASE)
    for name in ("inverse_faraday", "inverse_cotton_mouton",
                 "photothermal", "mnf2_annealing"):
        assert m[name].respond(rev) == m[name].respond(BASE), name
    # helicity flip: IFE flips, IOME/thermal unchanged
    r = BASE.ablate("helicity", jones=RCP)
    l = BASE.ablate("helicity", jones=LCP)
    assert m["inverse_faraday"].respond(r) == \
        -m["inverse_faraday"].respond(l) != 0
    assert m["iome_linipo4"].respond(r) == \
        m["iome_linipo4"].respond(l)
    assert m["photothermal"].respond(r) == \
        m["photothermal"].respond(BASE)
    # polarization rotation with fixed direction: ICM/annealing move,
    # IOME and IFE(linear) do not
    y = BASE.ablate("polarization_angle", jones=(0.0, 1.0))
    assert m["inverse_cotton_mouton"].respond(y) == \
        -m["inverse_cotton_mouton"].respond(BASE)
    assert m["mnf2_annealing"].respond(y) != \
        m["mnf2_annealing"].respond(BASE)
    assert m["iome_linipo4"].respond(y) == \
        m["iome_linipo4"].respond(BASE)
    # intensity-only: thermal scales linearly
    hot = BASE.ablate("intensity", intensity_w_m2=4.0)
    assert m["photothermal"].respond(hot) == \
        2 * m["photothermal"].respond(BASE)
    # OAM reversal: only the vortex diagnostic responds
    v = BASE.ablate("oam_index", oam_index=+2)
    assert m["vortex_diagnostic"].respond(v) == 2.0
    assert m["iome_linipo4"].respond(v) == \
        m["iome_linipo4"].respond(BASE)


def test_undeclared_channels_cannot_leak():
    """Mechanical enforcement: the respond() call passes only the
    declared channels; a mechanism function cannot see the rest."""
    seen = {}

    def spy(v):
        seen.update(v)
        return 0.0
    decl = oc.ResponseDeclaration("spy", frozenset({"intensity"}), spy)
    decl.respond(BASE)
    assert set(seen) == {"intensity"}


def test_ablation_matrix_shape_and_selectivity():
    out = oc.ablation_matrix(BASE, {
        "k_reversal": ("propagation", {"propagation": (0, -1, 0)}),
        "helicity_r": ("helicity", {"jones": RCP}),
        "pol_90": ("polarization_angle", {"jones": (0.0, 1.0)}),
        "double_intensity": ("intensity", {"intensity_w_m2": 4.0}),
    })
    ab = out["ablations"]
    assert ab["k_reversal"]["iome_linipo4"] != 0
    assert ab["k_reversal"]["inverse_faraday"] == 0
    assert ab["helicity_r"]["inverse_faraday"] != 0
    assert ab["helicity_r"]["iome_linipo4"] == 0
    assert ab["pol_90"]["inverse_cotton_mouton"] != 0
    assert ab["pol_90"]["photothermal"] == 0
    assert ab["double_intensity"]["photothermal"] != 0


def test_hidden_order_report_and_identity_prohibition():
    rep = oc.hidden_order_report(0.6, 1.0, 15.0, (0, 1, 0), 1400.0,
                                 0.2, 0.5, 1.0)
    assert rep["domain_populations"]["p_plus"] == pytest.approx(0.8)
    assert rep["afm_order_parameter"] == pytest.approx(0.6)
    assert rep["domain_walls_expected"]
    assert rep["writing_bias_retained"] == pytest.approx(0.6)
    assert rep["penetration_uniformity"] == pytest.approx(0.5)
    assert "DISTINCT" in rep["identity_note"]
    # pattern comparison embeds physical_identity: False
    a = np.exp(-np.linspace(-2, 2, 50) ** 2)
    cmp_ = oc.compare_patterns(a, a, "toroidal_moment.magnetic",
                               "circulation.mechanical.displacement")
    assert cmp_["spatial_correlation"] == pytest.approx(1.0)
    assert cmp_["physical_identity"] is False
    from rscs2_core.quantity_registry import (IdentityError,
                                              assert_identity)
    with pytest.raises(IdentityError):
        assert_identity("toroidal_moment.magnetic",
                        "circulation.mechanical.displacement")
