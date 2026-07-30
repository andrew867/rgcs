"""R10.53 -- the V1 Earth-root lock, and the limits it must keep stating."""

import json
import math

import numpy as np
import pytest

from r1053 import artifacts, kernel, ledger, lock, projector, residuals


# --------------------------------------------------------------- lane

def test_direct_word_is_not_header_stripped():
    """CORRECTION 1. The leading '16' is decimal coincidence, not a field."""
    assert not kernel.decimal_header_table_applies(165879243)
    assert kernel.assert_direct_lane(165879243) == 165879243


def test_wide_envelope_records_are_refused_by_the_direct_lane():
    """CORRECTION 3 + task 6. They exceed 30 bits, so they cannot enter."""
    for w in ledger.GATED_WIDE_ENVELOPE:
        assert int(w).bit_length() > kernel.WORD_BITS
        with pytest.raises(kernel.DirectLaneError):
            kernel.assert_direct_lane(w)
        assert kernel.decimal_header_table_applies(w)
        assert ledger.is_gated(w)


def test_binary_octal_path_comes_first():
    """CORRECTION 2. F5|Q22|S3 reconstructs the word exactly."""
    for w in list(ledger.FIT_ANCHORS) + list(ledger.V1_PROJECTED):
        f5, q22, s3 = kernel.fields(w)
        assert (f5 << 25) | (q22 << 3) | s3 == int(w)
        assert kernel.octal10(w) == format(int(w), "010o")


def test_m3_is_kept_out_of_the_geometry():
    """CORRECTION 10. S3 is the check digit; it must not move a point.

    Two words differing only in S3 must land in the same cell.
    """
    base = 165892763
    for s3 in range(8):
        w = (base & ~7) | s3
        assert np.allclose(kernel.kernel_vector(w),
                           kernel.kernel_vector(base))


def test_split_ratio_is_the_source_ratio_not_the_midpoint():
    assert kernel.SPLIT_T == pytest.approx(10.0 / 19.0)
    a, b, c = kernel.cell(165876523, depth=1)
    mid = kernel.cell(165876523, depth=1, t=0.5)
    assert not np.allclose(np.asarray(a), np.asarray(mid[0]))


def test_depth9_cell_edge_is_the_15km_scale():
    assert kernel.cell_edge_km(9) == pytest.approx(14.989, abs=0.01)
    assert kernel.cell_edge_km(11) == pytest.approx(3.747, abs=0.01)


# ---------------------------------------------------------- projector

def test_three_anchors_leave_two_free_parameters():
    """The central structural fact. Not asserted -- measured by rank."""
    r = projector.underdetermination_report()
    assert r["constraints"] == 6 and r["free_parameters"] == 8
    assert r["constraint_matrix_rank"] == 6
    assert r["genuinely_free_dimensions"] == 2
    assert not r["over_determined"]
    assert not r["anchor_fit_is_evidence"]
    assert r["anchors_needed_to_overdetermine"] == 5


def test_anchor_residuals_are_zero_and_that_is_not_evidence():
    r = projector.anchor_residuals()
    assert r["max_residual_km"] < 1e-6
    assert r["counts_as_evidence"] is False


def test_the_free_family_really_does_move_a_non_anchor_word():
    """Why a zero anchor residual proves nothing.

    Perturb A inside the null space: every anchor stays exact to
    sub-metre, and a non-anchor word walks away without bound. The
    displacement grows with the perturbation, so no finite figure
    bounds it -- which is the whole point of V1-B01/B02.
    """
    rows = list(projector.FIT_ANCHORS.values())
    M = projector._constraint_matrix(rows)
    _, _, Vt = np.linalg.svd(M)
    null = Vt[np.linalg.matrix_rank(M, tol=1e-10):]
    A = projector.fit_matrix()
    base = projector.project(165879243, A)
    walk = []
    for scale in (0.5, 2.0, 8.0):
        far = 0.0
        for basis in null:
            B = A + scale * basis.reshape(3, 3)
            for w, lat, lon in rows:             # anchors stay exact
                plat, plon = projector.project(w, B)
                d = projector.haversine_km(lat, lon, plat, plon)
                # the family satisfies COLLINEARITY e x (Au) = 0, which
                # admits u and -u alike; a large perturbation can send an
                # anchor to its antipode. Resolving that sign is exactly
                # what V1_PINNING does. Either way the anchor is exact.
                assert min(d, math.pi * projector.EARTH_RADIUS_KM - d) < 1e-3
            far = max(far, projector.haversine_km(
                *base, *projector.project(165879243, B)))
        walk.append(far)
    assert walk == sorted(walk)                  # grows with perturbation
    assert walk[0] > 25.0                        # already past every band
    assert walk[-1] > 1000.0                     # and unbounded in practice


def test_rotation_only_is_refuted():
    """A rotation would have been testable at 3 anchors. It misses."""
    r = projector.rotation_only_refutation()
    assert not r["rotation_fits_anchors"]
    assert r["best_anchor_rms_km"] > 100.0
    assert r["source_ratio_is_best_t"]


# ------------------------------------------------------------ ledger

def test_relabel_applied_and_montreal_retired():
    r = lock.relabel_status()
    assert r["relabel_applied"]
    assert "Drummondville" in r["active_label"]
    assert r["montreal_retired_to_provenance"]
    assert r["montreal_may_fit_projector"] is False


def test_montreal_never_enters_the_fit():
    """CORRECTION 11. The fit anchor set is exactly the three."""
    assert set(projector.FIT_ANCHORS) == {"Stonehenge", "Erie", "Toronto"}
    assert "165879243" not in {str(w) for w, _, _
                               in projector.FIT_ANCHORS.values()}


def test_distances_reproduce_the_pack_summary():
    d = residuals.anchor_pair_distances()
    for key, expected in (
            ("projected_drummondville_to_city_km", 15.684),
            ("projected_drummondville_to_st_frederic_proxy_km", 15.615),
            ("erie_to_toronto_km", 178.847),
            ("toronto_to_drummondville_projected_km", 582.465),
            ("erie_to_drummondville_projected_km", 721.696)):
        assert d[key] == pytest.approx(expected, abs=0.01)


def test_city_label_is_not_treated_as_an_exact_target():
    r = residuals.drummondville_report()
    assert "!= EXACT TARGET" in r["label_rule"]
    city = next(x for x in r["rows"]
                if x["reference"] == "Drummondville_city")
    assert city["reference_kind"] == "city_centre_label"
    assert city["band"] == "OPERATIONAL_CELL_OR_ADJACENT_CELL_HIT"
    assert 250 < city["bearing_from_reference_deg"] < 260     # WSW


def test_saint_eugene_is_the_nearest_recorded_reference():
    r = residuals.drummondville_report()
    assert r["nearest_reference"] == "Saint_Eugene"
    assert r["nearest_km"] == pytest.approx(4.94, abs=0.05)
    assert r["rows"][0]["band"] == "LOCAL_HIT"


def test_the_branch_conflict_is_recorded_not_buried():
    """V1-B03. Relabelling does not move the wire out of branch 117."""
    r = residuals.drummondville_report()
    assert r["branch_octal"] == "117"
    assert r["branch_conflict"] is True
    assert kernel.branch(165876523) == "117"      # Stonehenge, Britain
    assert kernel.branch(168930443) == "120"      # Toronto, N. America


def test_v1_pinning_agrees_with_the_branch_partition():
    """V1-B01/B03. Two members of the SAME free family disagree about
    which continent 165879243 addresses -- and the repo's pinning is the
    one that agrees with octal branch 117."""
    r = residuals.pinning_divergence()
    assert r["all_branch_117"]
    assert r["all_pinned_land_in_britain"]
    assert r["max_gap_km"] > 5000.0          # 165879243 -> Quebec vs Britain
    assert r["min_gap_km"] > 100.0           # even the triplet diverges
    drum = next(x for x in r["rows"] if x["vector"] == "165879243")
    assert drum["gap_km"] > 5000.0
    assert drum["pinned_lands_in_britain"]


# -------------------------------------------------------------- null

def test_cell_scale_reading_is_reported_with_its_null():
    """V1-B04. At the tolerance it was first stated with, it is automatic."""
    s = residuals.cell_scale_null_sweep()
    loose = next(r for r in s["rows"] if r["tolerance"] == 0.30)
    assert loose["coincidence_rate"] > 0.85
    tight = next(r for r in s["rows"] if r["tolerance"] == 0.05)
    assert tight["coincidence_rate"] < 0.20
    assert s["observed_deviation_from_one_cell"] < 0.05
    assert s["tightest_tolerance_the_observation_survives"] == 0.05
    assert "NOT_EVIDENTIAL" in s["verdict"]


def test_null_sweep_matches_the_analytic_log_coverage():
    """The ladder is geometric with ratio 2, so coverage is computable."""
    for row in residuals.cell_scale_null_sweep()["rows"]:
        assert row["coincidence_rate"] == pytest.approx(
            row["analytic_log_coverage"], abs=0.02)


# ------------------------------------------------------------ verdicts

def test_all_eleven_corrections_hold():
    r = lock.correction_status()
    assert r["all_hold"], [x for x in r["rows"] if not x["holds"]]
    assert len(r["rows"]) == 11


def test_every_required_verdict_is_present():
    required = {
        "R10_53_V1_EARTH_ROOT_ALIGNMENT_OPERATIONAL",
        "R10_53_DIRECT_9DIGIT_OCTAL_LANE_LOCKED",
        "R10_53_FIXED_ROOT_STAGED_PARSER_LOCKED",
        "R10_53_SOURCE_RATIO_10_19_PROJECTOR_LOCKED_AS_V1",
        "R10_53_DRUMMONDVILLE_RELABEL_APPLIED",
        "R10_53_MONTREAL_LABEL_RETIRED_TO_HINT_PROVENANCE",
        "R10_53_WIDE_ENVELOPE_SLEEP_BATCH_GATED",
        "R10_53_WATER_ACCEPTANCE_READY_NOT_SCOREABLE_WITHOUT_COASTLINE",
        "R10_53_V1_CANDIDATE_NOT_FINAL_PHYSICAL_VALIDATION",
    }
    assert required <= set(lock.VERDICTS)


def test_v1_never_claims_final_validation():
    r = lock.v1_lock_report()
    assert r["not_final_physical_validation"] is True
    assert "R10_53_V1_CANDIDATE_NOT_FINAL_PHYSICAL_VALIDATION" in r["verdicts"]
    assert artifacts.BOUNDARY.count("NOT final physical validation") == 1


def test_water_acceptance_is_ready_but_refuses_to_score():
    r = lock.water_acceptance_status()
    assert r["criterion_implemented"]
    assert not r["scoreable_now"]
    assert not r["land_water_mask_present"]
    assert r["attempted_score"]["verdict"] == "NOT_SCOREABLE_NO_COORDINATES"
    assert "71%" in r["baseline_to_beat"]


def test_blockers_are_listed_and_the_structural_ones_named():
    r = lock.v1_lock_report()
    assert r["blocker_count"] >= 7
    assert {"V1-B01", "V1-B02", "V1-B03", "V1-B07"} <= set(
        r["structural_blockers"])
    for key, b in r["blockers"].items():
        assert b["clears_when"] and b["detail"] and b["severity"]


# ----------------------------------------------------------- artifacts

def test_manifest_files_are_all_produced(tmp_path):
    written = artifacts.write_all(str(tmp_path))
    for name in ("rgcs_great_lakes_drummondville_triangle_interactive.html",
                 "rgcs_drummondville_corridor_interactive.html",
                 "rgcs_uk_orange_stonehenge_interactive.html",
                 "rgcs_great_lakes_drummondville_triangle_static.png",
                 "rgcs_drummondville_corridor_static.png",
                 "rgcs_uk_orange_stonehenge_static.png",
                 "rgcs_v1_projected_points.geojson",
                 "rgcs_v1_projected_points.kml",
                 "rgcs_v1_points.csv"):
        assert written[name] > 0, name


def test_every_artifact_carries_the_v1_boundary(tmp_path):
    artifacts.write_all(str(tmp_path))
    for p in tmp_path.iterdir():
        if p.suffix in (".html", ".kml", ".geojson"):
            assert "NOT final physical validation" in p.read_text("utf-8")


def test_geojson_marks_anchors_as_non_evidential():
    gj = artifacts.geojson()
    anchors = [f for f in gj["features"]
               if f["properties"]["role"] == "fit_anchor"]
    assert len(anchors) == 3
    for f in anchors:
        assert "not evidence" in f["properties"]["note"]
    lon, lat = gj["features"][0]["geometry"]["coordinates"]
    assert -180 <= lon <= 180 and -90 <= lat <= 90


def test_geojson_is_valid_json_and_round_trips():
    assert json.loads(json.dumps(artifacts.geojson()))["type"] \
        == "FeatureCollection"
