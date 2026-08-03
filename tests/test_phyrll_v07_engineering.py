"""v0.7 engineering package -- the three mandated proofs and the rest.

Mandated: no wall-power thrust, no exact 67.3 identity, no force in the
Brown proxy. Everything else supports the optimizer and measurement-prep
role of the package.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from rgcs_phyrll_v07 import SOURCE_LOCKS
from rgcs_phyrll_v07 import annular_upgrade as AU
from rgcs_phyrll_v07 import firewall_v07 as FW
from rgcs_phyrll_v07 import force_boundary as FB
from rgcs_phyrll_v07 import resonator as RZ
from rgcs_phyrll_v07 import roles
from rgcs_phyrll_v07 import steering_optimizer as SO


# ============================= MANDATED PROOF 1: no exact 67.3 identity

def test_67_3_is_display_not_identity():
    """673/10 - 64672/961 = 33/9610, asserted exactly."""
    assert F(673, 10) - F(64672, 961) == F(33, 9610)
    assert F(673, 10) != F(64672, 961)
    d = roles.display_vs_exact()
    assert d["not"] == "exact equality"
    assert d["gap_is_33_over_9610"] is True


def test_display_and_exact_carry_different_role_classes():
    by_name = {c.name: c for c in roles.REGISTRY}
    assert by_name["eta_F_display"].role == "SOURCE_DISPLAY"
    assert by_name["eta_F_exact_candidate"].role == "EXACT_ARITHMETIC"


def test_rounding_is_the_only_relation():
    assert round(float(F(64672, 961)), 1) == round(float(F(673, 10)), 1)


# ============================= MANDATED PROOF 2: no wall-power thrust

def test_wall_power_cannot_reach_the_force_boundary():
    """Wall power must pass ring_power_from_wall, which raises without a
    declared eta_couple -- so no wall-watt can become a candidate newton."""
    from rgcs_phyrll_v06.resonance import ring_power_from_wall
    with pytest.raises(ValueError):
        ring_power_from_wall(100.0)


def test_thrust_claim_refused_without_a_measurement():
    with pytest.raises(FB.ThrustClaimRefused):
        FB.thrust_claim(None, 10.0)
    with pytest.raises(FB.ThrustClaimRefused):
        FB.thrust_claim(FB.ETA_EXACT_CANDIDATE, 10.0)   # a Fraction is not
        # a measurement


def test_no_registry_entry_may_currently_claim_performance():
    assert roles.performance_claimants() == []
    assert FB.no_claimant_exists() is True


def test_a_lane_b_coefficient_cannot_be_smuggled_in():
    """Even wrapped as a Coefficient, lane B is refused."""
    fake = roles.Coefficient("eta_smuggled", "B", "EXACT_ARITHMETIC",
                             F(64672, 961))
    with pytest.raises(FB.ThrustClaimRefused):
        FB.thrust_claim(fake, 10.0)


def test_candidate_force_is_tagged_and_not_a_claim():
    r = FB.candidate_force(2.0)
    assert r["claim"] == "BENCH_REQUIRED"
    assert r["is_thrust_claim"] is False
    assert r["F_candidate_N"] == pytest.approx(float(F(64672, 961)) * 2.0)


def test_a_proper_measurement_would_be_accepted():
    """The gate opens for exactly the right object -- proving the refusal
    tests exercise the gate, not a stub."""
    measured = roles.Coefficient("eta_F_measured", "D",
                                 "PHYSICAL_MEASUREMENT",
                                 measured_value=0.5, uncertainty=0.1)
    r = FB.thrust_claim(measured, 2.0)
    assert r["F_N"] == pytest.approx(1.0)
    assert r["is_thrust_claim"] is True


# ============================= MANDATED PROOF 3: no force in the proxy

def test_brown_proxy_modules_expose_no_force_function():
    import rgcs_phyrll_v06.brown_annular_proxy as B
    for mod in (B, AU):
        for name in dir(mod):
            if not name.startswith("_"):
                assert "force" not in name.lower()
                assert "thrust" not in name.lower()


def test_weighted_comparison_reports_ratios_not_forces(shared_cmp):
    assert shared_cmp["no_force_function"] is True
    for key in ("binary_mask_displacement", "weighted_mask_displacement"):
        assert shared_cmp[key]["is_a_force"] is False
        assert 0.0 < shared_cmp[key]["ratio_to_physical"] < 1.0


# ============================= optimizer

@pytest.fixture(scope="module")
def opt():
    return SO.optimize(trials=150)


@pytest.fixture(scope="module")
def shared_cmp():
    return AU.compare_with_weighted(n=31, iters=350)


def test_locks_are_never_varied(opt):
    assert SOURCE_LOCKS["ring_family"] == 37
    assert SOURCE_LOCKS["carrier_hz"] == 4096 * 411
    assert SOURCE_LOCKS["aux_ratio_188_288"] == F(188, 288) == F(47, 72)
    for row in opt["rows"]:
        if row["lock_compliant_33"]:
            assert row["active_cells"] == 33


def test_every_family_is_rotation_invariant(opt):
    assert all(r["rotation_invariant"] for r in opt["rows"])


def test_no_family_computes_force(opt):
    assert all(r["computes_force"] is False for r in opt["rows"])
    assert "force" not in opt["success_metric"].lower().replace(
        "not force", "")


def test_graded_families_beat_binary_blanking(opt):
    rows = {r["family"]: r for r in opt["rows"]}
    binary33 = None  # binary 4-blank baseline is not in FAMILIES; compare
    # graded against the best binary family instead
    best_binary = max(r["abs_d_eff"] for r in opt["rows"]
                      if r["family"].endswith("blanks")
                      or r["family"] == "single_blank")
    for fam in ("graded_current_taper", "capacitive_gap_weighting"):
        assert rows[fam]["abs_d_eff"] > best_binary


def test_lock_compliant_families_beat_their_own_null(opt):
    for r in opt["rows"]:
        if r["lock_compliant_33"]:
            assert r["beats_null_p95"] is True


def test_single_blank_null_is_degenerate_and_not_a_win(opt):
    row = {r["family"]: r for r in opt["rows"]}["single_blank"]
    assert row["null_degenerate"] is True
    assert row["beats_null_p95"] is False


def test_near_opposite_is_the_weakest_binary_family(opt):
    rows = {r["family"]: r for r in opt["rows"]}
    assert rows["near_opposite_blanks"]["abs_d_eff"] < \
        rows["two_adjacent_blanks"]["abs_d_eff"] / 10.0


def test_amplitude_families_are_anti_aligned_with_S(opt):
    """d_eff points at surviving current, S at the blanks: 180 apart."""
    rows = {r["family"]: r for r in opt["rows"]}
    for fam in ("two_adjacent_blanks", "graded_current_taper",
                "capacitive_gap_weighting"):
        assert rows[fam]["anti_alignment_error_deg"] == pytest.approx(
            0.0, abs=1.0)


def test_best_lock_compliant_is_reported(opt):
    assert opt["best_lock_compliant"]["family"] in \
        opt["lock_compliant_ranking"]
    assert opt["best_lock_compliant"]["lock_compliant_33"] is True


# ============================= weighted proxy

def test_centered_stays_zero(shared_cmp):
    assert shared_cmp["centered_symmetric"]["asymmetry_scalar"] < 1e-3


def test_weighted_mask_recovers_more_than_binary(shared_cmp):
    b = shared_cmp["binary_mask_displacement"]["ratio_to_physical"]
    w = shared_cmp["weighted_mask_displacement"]["ratio_to_physical"]
    assert w > 2.0 * b


# ============================= resonator

def test_lc_product_is_pinned_by_the_carrier_lock():
    lc = RZ.lc_product_from_lock()
    f0 = RZ.f0_from_lc(1e-9, lc / 1e-9)
    assert f0 == pytest.approx(4096 * 411, rel=1e-12)


def test_design_point_is_self_consistent():
    dp = RZ.design_point(c_eff=1e-9, q_l=100.0)
    assert RZ.f0_from_lc(dp["L_eff_H"], dp["C_eff_F"]) == pytest.approx(
        4096 * 411, rel=1e-12)
    assert dp["R_loss_ohm"] == pytest.approx(
        2 * math.pi * 4096 * 411 * dp["L_eff_H"] / 100.0)


def test_every_unknown_has_a_measurement_row():
    plan = RZ.measurement_plan()
    assert {p["unknown"] for p in plan} == set(RZ.UNKNOWNS)
    assert all(p["claim"] == "BENCH_REQUIRED" for p in plan)


# ============================= firewall v0.7

def test_missing_controls_void_the_residual():
    terms = {t: 0.0 for t in FW.TERMS}
    out = FW.decompose(1.0, terms, controls={})
    assert out["residual_quotable"] is False
    assert math.isnan(out["F_residual_N"])
    assert set(out["missing_controls"]) == set(FW.REQUIRED_CONTROLS)


def test_full_controls_and_terms_quote_the_residual():
    terms = {t: 0.1 for t in FW.TERMS}
    controls = {c: {"receipt": "run-001"} for c in FW.REQUIRED_CONTROLS}
    out = FW.decompose(1.0, terms, controls)
    assert out["residual_quotable"] is True
    assert out["F_residual_N"] == pytest.approx(0.5)
    assert out["interpretation"] == \
        "RESIDUAL_IS_NOT_EVIDENCE_OF_NEW_PHYSICS"


def test_an_unmeasured_term_also_voids_the_residual():
    terms = {t: 0.1 for t in FW.TERMS}
    terms["F_Maxwell"] = float("nan")
    controls = {c: True for c in FW.REQUIRED_CONTROLS}
    out = FW.decompose(1.0, terms, controls)
    assert out["residual_quotable"] is False
    assert "F_Maxwell" in out["missing_terms"]


def test_checklist_covers_all_required_controls():
    assert {r["control"] for r in FW.control_checklist()} == \
        set(FW.REQUIRED_CONTROLS)


# ============================= Bermuda retag

def test_bermuda_lane_statuses_are_fixed():
    from rgcs_terra_release.miami_bermuda_calibration import LANE_STATUS
    assert LANE_STATUS["236805/142"] == "RECORDED_POSTHOC_LEAD"
    assert "NO_SUPPORTING_PARSE" in LANE_STATUS["1680769543"]
    assert LANE_STATUS["projector_fitting"] == "FORBIDDEN"
    assert LANE_STATUS["release_as_solved"] == "FORBIDDEN"


# ============================= registry hygiene

def test_registry_serialises_and_lanes_are_typed():
    import json
    rows = json.loads(roles.registry_json())
    assert all(r["lane"] in roles.LANES for r in rows)
    assert all(r["role"] in
               ("SOURCE_DISPLAY", "EXACT_ARITHMETIC", "GEOMETRY_DESIGN",
                "PHYSICAL_MEASUREMENT", "BENCH_REQUIRED") for r in rows)


def test_unknown_role_or_lane_is_rejected():
    with pytest.raises(ValueError):
        roles.Coefficient("x", "A", "MADE_UP_ROLE")
    with pytest.raises(ValueError):
        roles.Coefficient("x", "Z", "SOURCE_DISPLAY")
