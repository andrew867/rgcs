"""v0.6 coefficient spine -- the must-pass exact arithmetic."""

from __future__ import annotations

from fractions import Fraction as F
from math import acos, asin, degrees

import pytest

from rgcs_phyrll_v06 import CLAIM_TAGS, FORBIDDEN_CLAIMS
from rgcs_phyrll_v06 import coefficients as C


def test_the_mandated_eta_identity():
    """The spec's literal must-pass block."""
    eta_src = F(673, 10)
    q = F(27, 93)
    assert q == F(9, 31)
    sigma = F(47, 63)
    a = F(311, 1)
    eta_calc = sigma * q * (a - q)
    assert eta_calc == F(64672, 961)
    assert round(float(eta_calc), 1) == 67.3
    assert C.ETA_F_CALC == eta_calc and C.ETA_F_SOURCE == eta_src


def test_source_and_calc_are_not_the_same_number():
    """They agree at 1 dp and differ by exactly 33/9610."""
    r = C.eta_source_vs_calc()
    assert r["identical"] is False
    assert r["agree_at_1dp"] is True
    assert F(r["exact_gap"]) == F(33, 9610)


def test_the_three_cg_angle_readings_are_distinct_and_unselected():
    r = C.theta_readings_cg()
    vals = (r["acos_deg"], r["asin_deg"], r["times_57p3_deg"])
    assert len({round(v, 6) for v in vals}) == 3
    assert r["selected"] is None and r["claim"] == "UNRESOLVED"
    cg = float(C.GEOMETRY_CG)
    assert r["acos_deg"] == pytest.approx(degrees(acos(cg)))
    assert r["asin_deg"] == pytest.approx(degrees(asin(cg)))


def test_573_over_10_is_not_180_over_pi():
    """57.3 is the source's shorthand, not the exact conversion."""
    import math
    assert float(C.DEG_PER_RAD_SRC) != pytest.approx(180.0 / math.pi,
                                                     abs=1e-6)


def test_family_c_candidates_compute_exactly():
    assert C.STATE47_CANDIDATE == F(297) * F(142, 897)
    assert C.SMALL_ANGLE_CANDIDATE_DEG == F(142, 897) * F(573, 10)
    assert C.MIAMI_BERMUDA_CANDIDATE_KM == F(236805, 142)


def test_every_coefficient_row_is_claim_tagged_and_typed():
    for row in C.coefficient_table():
        assert row["claim"] in CLAIM_TAGS
        assert row["role"].startswith(("A_", "B_", "C_"))
        assert F(row["exact"]) is not None       # parses exactly


def test_no_candidate_is_silently_promoted():
    """Every family-C entry stays UNRESOLVED or MODEL_OUTPUT."""
    for row in C.coefficient_table():
        if row["role"] == "C_calibration":
            assert row["claim"] in ("UNRESOLVED", "MODEL_OUTPUT")


def test_forbidden_claims_are_declared():
    for c in ("antigravity", "reactionless_propulsion", "free_energy",
              "flight_validation"):
        assert c in FORBIDDEN_CLAIMS
