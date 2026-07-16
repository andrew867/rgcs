"""Agent M7: metacrystal g2 transfer tests (gates G1-G4)."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core.refmodels.metacrystal import (FIXTURES,
                                              MetaAtomGeometry,
                                              inverse_query,
                                              transfer_g2)

MAT = "reference.metacrystal"
GEO = MetaAtomGeometry(100.0, 16, 0.0, "ring", 0.6)


def test_fixture_values_and_identity_limit():
    """Gate G1: coherent/thermal/sub/superthermal fixtures; zero
    coupling is the exact identity."""
    assert FIXTURES["coherent"] == 1.0 and FIXTURES["thermal"] == 2.0
    ident = MetaAtomGeometry(100.0, 16, 0.0, "ring", 0.0)
    for name, g2 in FIXTURES.items():
        out = transfer_g2(MAT, g2, ident)
        assert out["value"]["g2_out"] == pytest.approx(g2, rel=1e-12)


def test_band_membership_and_boundedness():
    """Gate G2: outputs respect the geometry's registered band."""
    for g2 in (0.0, 0.5, 1.0, 1.7, 2.0, 3.5, 10.0):
        out = transfer_g2(MAT, g2, GEO)
        lo, hi = out["value"]["band"]
        g2o = out["value"]["g2_out"]
        # declared partial-pull bound: between input and band
        assert min(g2, lo) - 1e-9 <= g2o <= max(g2, hi) + 1e-9
        assert g2o >= 0.0
        # the pull moves TOWARD the band, never away from it
        if g2 < lo:
            assert g2o >= g2
        if g2 > hi:
            assert g2o <= g2
    # in-band inputs stay in band
    mid = transfer_g2(MAT, 1.7, GEO)["value"]
    assert mid["in_band"]


def test_invalid_inputs_and_uncertainty():
    with pytest.raises(ValueError, match="finite"):
        transfer_g2(MAT, -0.1, GEO)
    with pytest.raises(ValueError, match="sigma"):
        transfer_g2(MAT, 1.0, GEO, sigma_g2=-1.0)
    with pytest.raises(ValueError, match="coupling"):
        MetaAtomGeometry(100.0, 16, 0.0, "ring", 1.5)
    out = transfer_g2(MAT, 1.5, GEO, sigma_g2=0.1)
    assert out["uncertainty"]["sigma_g2_out"] > 0


def test_deterministic_and_monotone_in_input():
    a = transfer_g2(MAT, 1.5, GEO)["value"]["g2_out"]
    b = transfer_g2(MAT, 1.5, GEO)["value"]["g2_out"]
    assert a == b
    outs = [transfer_g2(MAT, g, GEO)["value"]["g2_out"]
            for g in np.linspace(0.2, 3.0, 15)]
    assert all(x <= y + 1e-12 for x, y in zip(outs, outs[1:]))


def test_inverse_nonuniqueness_reported():
    inv = inverse_query(MAT, g2_target=1.5, g2_in=1.5)
    assert inv["candidates"]
    # identity (c=0) always matches g2_target == g2_in; typically more
    assert inv["nonunique"] or len(inv["candidates"]) == 1
    assert "nonunique" in inv


def test_quartz_separation():
    """Gate G3: the model cannot run as bulk quartz."""
    out = transfer_g2("material.alpha_quartz", 1.0, GEO)
    assert out["classification"] == "NOT_APPLICABLE"
    inv = inverse_query("material.alpha_quartz", 1.5, 1.5)
    assert inv["classification"] == "NOT_APPLICABLE"
    ok = transfer_g2(MAT, 1.0, GEO)
    assert "NOT bulk quartz" in " ".join(ok["assumptions"])
