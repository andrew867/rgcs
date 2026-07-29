"""R10.17 - hedron + shell calibration tests."""

import pytest

from r1017.points import SEED_POINTS, height_span_m, training_points
from r1017.shells import build_models, invariant_check


def _model(mid, did):
    return [m for m in build_models(SEED_POINTS)
            if m.model_id == mid and m.datum_id == did][0]


def test_recorded_land_zero_is_above_every_point():
    """The mechanical cause of every prior 'radial unresolved'."""
    m = _model("REPO_ATMOSPHERIC_LADDER_V1", "RECORDED_LAND_ZERO_840M")
    for p in SEED_POINTS:
        if p.has_height:
            c = m.classify(p.height_m)
            assert c["status"] == "BELOW_SHELL3_INNER_BOUNDARY", p.name
            assert c["below_by_m"] > 0


def test_msl_datum_puts_land_anchors_in_shell_3():
    m = _model("REPO_ATMOSPHERIC_LADDER_V1",
               "DECLARED_ALTERNATIVE_MSL_0M")
    for p in SEED_POINTS:
        if p.has_height and p.height_m > 0:
            c = m.classify(p.height_m)
            assert c["status"] == "IN_OPERATIONAL_STACK", p.name
            assert c["shell"] == 3
            assert 0.0 <= c["zeta"] <= 1.0


def test_baltic_separates_as_a_benthic_monitor():
    m = _model("REPO_ATMOSPHERIC_LADDER_V1",
               "DECLARED_ALTERNATIVE_MSL_0M")
    for depth in (-91.0, -82.0):
        c = m.classify(depth)
        assert c["status"] == "BELOW_SHELL3_INNER_BOUNDARY"
        assert c["shell"] is None


def test_zeta_values_are_exact_and_ordered_by_height():
    m = _model("REPO_ATMOSPHERIC_LADDER_V1",
               "DECLARED_ALTERNATIVE_MSL_0M")
    assert abs(m.classify(101.0)["zeta"] - 101.0 / 12000.0) < 1e-12
    assert abs(m.classify(760.0)["zeta"] - 760.0 / 12000.0) < 1e-12
    hs = sorted(p.height_m for p in SEED_POINTS
                if p.has_height and p.height_m > 0)
    zs = [m.classify(h)["zeta"] for h in hs]
    assert zs == sorted(zs)


def test_outer_in_equals_inner_out_for_every_model_and_point():
    checked = 0
    for m in build_models(SEED_POINTS):
        for p in SEED_POINTS:
            if not p.has_height:
                continue
            c = m.classify(p.height_m)
            if c["status"] != "IN_OPERATIONAL_STACK":
                continue
            iv = invariant_check(m, c["shell"], c["zeta"])
            assert iv["invariant_holds"], (m.model_id, p.name,
                                           iv["residual_m"])
            checked += 1
    assert checked > 20


def test_d_in_and_d_s_match_the_declared_equations():
    m = _model("REPO_ATMOSPHERIC_LADDER_V1",
               "DECLARED_ALTERNATIVE_MSL_0M")
    c = m.classify(101.0)
    outer_sum = sum(m.thickness_m[k] for k in m.shells if k > 3)
    assert abs(c["d_in_m"] - (outer_sum
                              + (1 - c["zeta"]) * m.thickness_m[3])) < 1e-9
    assert abs(c["d_s_m"] - c["zeta"] * m.thickness_m[3]) < 1e-9


def test_shell_boundaries_are_contiguous_and_ordered():
    for m in build_models(SEED_POINTS):
        b = m.boundaries_m()
        shells = m.shells
        for i in range(len(shells) - 1):
            assert abs(b[shells[i]][1] - b[shells[i + 1]][0]) < 1e-9
        for s in shells:
            assert b[s][1] > b[s][0]


def test_shells_0_to_2_carry_no_declared_thickness():
    m = _model("REPO_UNIFORM_100KM_V1", "DECLARED_ALTERNATIVE_MSL_0M")
    assert set(m.shells) == {3, 4, 5, 6, 7, 8}
    assert 0 not in m.thickness_m and 2 not in m.thickness_m


def test_user_777_profile_is_present_and_named():
    ids = {m.model_id for m in build_models(SEED_POINTS)}
    assert "USER_7_7_7_PROFILE_DIAGNOSTIC" in ids
    assert "OUTER_IN_GEOMETRIC_RATIO_7_DIAGNOSTIC" in ids
    assert "S3_SURFACE_BAND_FIT_FROM_ANCHOR_HEIGHTS" in ids


def test_epoch_window_is_bounded():
    from r1017.shells import EPOCH_WINDOW_BP
    assert EPOCH_WINDOW_BP == (10000, 50000)


def test_geometry_partitions_anchors_like_the_addresses():
    import numpy as np

    from cwatlas.r1085a import final_projection as fp
    from r1017.angular import classify_point, surface_word_face
    frame, _ = fp.training_alignment(2025.0)
    rot = np.asarray(frame.rotation, float)
    geo, addr = {}, {}
    for p in training_points():
        geo[p.point_id] = classify_point(p.lat, p.lon, rot)["root_face"]
        addr[p.point_id] = surface_word_face(p.surface_word)
    na = ["MONTREAL_CORRECTED_ANCHOR", "ERIE_ANCHOR", "TORONTO_ANCHOR"]
    assert len({geo[k] for k in na}) == 1
    assert len({addr[k] for k in na}) == 1
    assert geo["STONEHENGE_ANCHOR"] not in {geo[k] for k in na}
    assert addr["STONEHENGE_ANCHOR"] not in {addr[k] for k in na}


def test_face_relabeling_is_a_consistent_function():
    import numpy as np

    from cwatlas.r1085a import final_projection as fp
    from r1017.angular_search import _fit_permutation
    frame, _ = fp.training_alignment(2025.0)
    perm = _fit_permutation(training_points(),
                            np.asarray(frame.rotation, float),
                            "right", "south_up")
    assert perm is not None
    assert perm == {4: 4, 1: 5}


def test_angular_has_no_full_agreement_survivor():
    from r1017.angular_search import search
    res = search(training_points())
    assert res["variants_evaluated"] == 480
    assert res["full_agreement_variants"] == []
    assert res["best"]["total_score"] < res["best"]["max_score"]


def test_height_span_is_small_against_shell_thickness():
    m = _model("REPO_ATMOSPHERIC_LADDER_V1",
               "DECLARED_ALTERNATIVE_MSL_0M")
    assert height_span_m()["span_m"] / m.thickness_m[3] < 0.10


def test_montreal_shell_assignment_is_flagged_marginal():
    """Honest limitation: Montreal straddles the datum at 3 sigma."""
    m = _model("REPO_ATMOSPHERIC_LADDER_V1",
               "DECLARED_ALTERNATIVE_MSL_0M")
    p = [x for x in SEED_POINTS
         if x.point_id == "MONTREAL_CORRECTED_ANCHOR"][0]
    lo = m.classify(p.height_m - 3 * p.height_sigma_m)
    hi = m.classify(p.height_m + 3 * p.height_sigma_m)
    assert lo["status"] != hi["status"]
