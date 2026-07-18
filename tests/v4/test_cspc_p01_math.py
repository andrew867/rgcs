"""P01 (A01-A03): provenance, dimensional/precision audit, exact
arithmetic.

Positive tests: every derivation reproduces its frozen fixture; units
compose correctly. Negative tests: floats are refused, dimensions
cannot be mixed, source precision cannot become measurement precision,
and a claim cannot climb the evidence ladder without evidence.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK = (ROOT / "internal-docs" / "plans-v4" /
        "RGCS_v4_6_Crystalline_Spacetime_Coordinate_Prompt_Pack")


# --- A03 exact arithmetic ------------------------------------------------

def test_every_candidate_matches_its_frozen_fixture():
    from cspc.exact import verify_all
    rep = verify_all()
    assert rep["ok"], f"fixture drift: {rep['failures']}"
    assert rep["checked"] >= 17


def test_fold_family_is_exact_powers_of_eight():
    from cspc.exact import FOLDS, SOURCE_2_45_GHZ
    src = SOURCE_2_45_GHZ.in_unit("Hz")
    for n, cand in FOLDS.items():
        assert cand.exact_hz == src / Fraction(8) ** n
    # the primary candidate, exactly
    assert FOLDS[9].exact_hz == Fraction("18.25392246246337890625")


def test_optical_candidate_is_two_to_the_49():
    from cspc.exact import OPTICAL_HZ
    assert OPTICAL_HZ.exact_hz == 2 ** 49 == 562949953421312


def test_optical_wavelength_matches_pack_to_quoted_digits():
    from cspc.exact import OPTICAL_WAVELENGTH
    exact = OPTICAL_WAVELENGTH.quantity.exact_str("nm")
    assert exact.startswith("532.5383831689123")


def test_dds_period_is_exact_rational():
    from cspc.exact import dds_period_s
    p = dds_period_s()
    assert p == Fraction(536870912, 19140625)
    assert abs(float(p) - 28.0487660147) < 1e-9


def test_common_532nm_laser_is_not_the_candidate():
    """A stock green laser is a near neighbour, not the target."""
    from cspc.exact import common_532nm_offset
    off = common_532nm_offset()
    assert off["common_laser_hz"] != off["candidate_hz"]
    assert 0.101 < off["percent"] < 0.102


def test_powers_of_eight_are_thirty_three_octaves_not_eleven():
    """CSPC-CORR-003 as arithmetic: 8^11 == 2^33."""
    assert Fraction(8) ** 11 == Fraction(2) ** 33


# --- A02 dimensional / precision ----------------------------------------

def test_floats_are_refused_at_the_parse_boundary():
    from cspc.units import exact
    with pytest.raises(ValueError):
        exact(2.45e9)
    assert exact("2450000000") == Fraction(2450000000)


def test_dimensions_cannot_be_mixed():
    from cspc.units import DimensionError, Quantity
    hz = Quantity.of(10, "Hz")
    sec = Quantity.of(10, "s")
    with pytest.raises(DimensionError):
        hz + sec
    with pytest.raises(DimensionError):
        hz.in_unit("s")


def test_frequency_times_time_is_dimensionless():
    from cspc.units import Quantity
    cycles = Quantity.of(50, "Hz") * Quantity.of(4, "s")
    assert cycles.dimension.dimensionless
    assert cycles.value == 200


def test_wavelength_from_c_over_frequency_has_length_dimension():
    from cspc.units import C_VACUUM, Quantity, unit_dimension
    lam = C_VACUUM / Quantity.of(2 ** 49, "Hz")
    assert lam.dimension == unit_dimension("m")


def test_precision_audit_flags_source_precision_overclaim():
    """Transfer firewall 8, mechanically: the fold value is exact
    arithmetic but only 3 s.f. of physics."""
    from cspc.exact import FOLDS
    audit = FOLDS[9].quantity.precision_audit("Hz")
    assert audit["exact"] == "18.25392246246337890625"
    assert audit["supported"] == "18.3"
    assert audit["sig_figs"] == 3
    assert audit["overclaims_if_quoted_exactly"] is True


def test_exact_by_definition_values_do_not_overclaim():
    """The optical wavelength descends from exact integers and the
    SI-defined c, so its long expansion is not an overclaim."""
    from cspc.exact import OPTICAL_WAVELENGTH
    audit = OPTICAL_WAVELENGTH.quantity.precision_audit("nm")
    assert audit["sig_figs"] is None
    assert audit["overclaims_if_quoted_exactly"] is False


def test_significance_propagates_through_arithmetic():
    from cspc.units import Quantity
    nominal = Quantity.of("2450000000", "Hz", 3)
    exact_div = Quantity.of(512, "", None)
    assert (nominal / exact_div).sig_figs == 3


# --- A01 provenance ------------------------------------------------------

def test_source_record_preserves_wording_and_dates():
    from cspc.provenance import source_record
    rec = source_record()
    assert rec.evidence_class == "SOURCE_CLAIM"
    assert "2.45 GHz is described as the frequency of water." in rec.claims
    assert "2024-04-21" in rec.dates


def test_pack_source_file_is_preserved_without_drift():
    from cspc.provenance import load_pack_source
    p = PACK / "data" / "source_claim.json"
    if not p.exists():
        pytest.skip("pack not present in this checkout")
    rep = load_pack_source(p)
    assert rep["matches_id"] and rep["matches_dates"] and \
        rep["matches_claims"]


def test_all_five_standing_corrections_present():
    from cspc.provenance import CORRECTIONS, correction
    ids = {c.id for c in CORRECTIONS}
    assert {"CSPC-CORR-001", "CSPC-CORR-002", "CSPC-CORR-003",
            "CSPC-CORR-004", "CSPC-CORR-005"} <= ids
    assert "unique fundamental resonance" in \
        correction("CSPC-CORR-001").correction
    assert "HERTZ" in correction("CSPC-CORR-002").correction


def test_source_claim_cannot_be_promoted_without_evidence():
    """The load-bearing refusal: repetition is not evidence."""
    from cspc import ClaimBoundaryError
    from cspc.provenance import promote
    with pytest.raises(ClaimBoundaryError):
        promote("water-2.45GHz", "SOURCE_CLAIM", "BENCH_MEASUREMENT")


def test_promotion_requires_the_right_evidence_and_direction():
    from cspc import ClaimBoundaryError
    from cspc.provenance import promote
    ok = promote("fold-9", "SOURCE_CLAIM", "DERIVED_ARITHMETIC",
                 evidence="2.45e9/8^9 exact in cspc.exact")
    assert ok["to"] == "DERIVED_ARITHMETIC"
    # cannot move down or sideways
    with pytest.raises(ClaimBoundaryError):
        promote("x", "ANALYTIC_MODEL", "SOURCE_CLAIM", evidence="n/a")
