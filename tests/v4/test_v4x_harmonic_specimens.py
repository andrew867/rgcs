"""C03/C05: harmonic family + specimen registry (gates G09/G12)."""
from __future__ import annotations

import pytest

from rscs2_core import harmonic_family as hf


def test_family_lengths_exact_and_n7_anchor():
    """Gate G09: N=5..12 generated; N=7 reproduces the frozen
    canonical ideal length exactly."""
    assert hf.family_length_mm(7) == 770.263671875 / 7.0
    from rscs2_core.crystal110 import IDEAL_LENGTH_MM
    assert hf.family_length_mm(7) == IDEAL_LENGTH_MM
    lengths = [hf.family_length_mm(n) for n in hf.FAMILY_N]
    assert len(lengths) == 8
    assert all(a > b for a, b in zip(lengths, lengths[1:]))
    with pytest.raises(ValueError):
        hf.family_length_mm(4)


def test_family_members_valid_geometry():
    rows = hf.family_table()
    assert [r["n"] for r in rows] == list(range(5, 13))
    for r in rows:
        assert r["shaft_length_mm"] > 0          # caps fit
        assert r["wide_diameter_mm"] == pytest.approx(
            r["length_mm"] * 40 / 154, rel=1e-12)
        assert "PROSPECTIVE" in r["status"]


def test_tolerance_model_first_order():
    t = hf.tolerance_sensitivity(7, dl_mm=0.1)
    assert t["rel_frequency_band"] == pytest.approx(
        0.1 / hf.family_length_mm(7), rel=1e-12)
    # cross-check against the frozen ideal/nominal pair: dL = 0.037667
    dl = hf.family_length_mm(7) - 110.0
    t2 = hf.tolerance_sensitivity(7, dl_mm=dl)
    assert t2["rel_frequency_band"] == pytest.approx(
        dl / hf.family_length_mm(7), rel=1e-12)


def test_angle_registry_distinct_forms_never_conflated():
    sep = hf.angle_separations()
    # 51.843 vs 51deg51'51" differ by ~0.0212 deg — recorded exactly
    assert sep["G001_vs_G002_deg"] == pytest.approx(
        (51 + 51 / 60 + 51 / 3600) - 51.843, rel=1e-9)
    assert sep["G001_vs_G002_deg"] > 0.02
    assert sep["G001_vs_G005_deg"] == pytest.approx(0.016, abs=2e-3)
    assert "never silently substitute" in sep["rule"]


def test_specimen_registry_complete_g001_g030():
    """Gate G12: every G001-G030 id present with typed records."""
    reg = hf.specimen_registry()
    expected = {f"G{i:03d}" for i in range(1, 31)}
    assert expected <= set(reg)
    # catalog specimens are SRC until measured
    for rid in ("G015", "G019", "G023", "G025"):
        assert reg[rid]["status"] == "SOURCE_HYPOTHESIS"
        assert "SRC" in reg[rid]["evidence_tags"]
    # the vendor 100 nm claim is not accepted fact
    assert reg["G012"]["status"] == "SOURCE_HYPOTHESIS"
    # facet families in the catalog cover 8/12/24; family adds 6
    facets = {reg[r].get("facets") for r in
              ("G015", "G016", "G024")}
    assert facets == {24, 8, 12}
    # canonical distinctness is CORE
    assert reg["G013"]["status"] == "CORE_VALIDATED"
