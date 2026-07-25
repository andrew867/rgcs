"""P18 — two-anchor orientation and family calibration fit.

Per-family residuals, closed-form determinism, DOF accounting, the F1==F3
indistinguishability, under-determination (alias set, no silent pick), and the
overparameterised-fit refusal.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cwatlas.r1082 import calibration_fit as C
from cwatlas.r1082 import claims, spatialization, stonehenge_anchor, wilkes


def test_fit_all_ranks_every_family():
    fit = C.fit_all()
    assert len(fit.fits) == spatialization.FAMILY_COUNT == 4
    # Ranked ascending by combined residual.
    rms = [f.combined_rms_rad for f in fit.fits]
    assert rms == sorted(rms)


def test_per_family_residuals_reported():
    fit = C.fit_all()
    for f in fit.fits:
        assert f.wilkes_residual_rad >= 0.0
        assert f.stonehenge_residual_rad >= 0.0
        # combined is the RMS of the two per-anchor residuals.
        expected = math.sqrt((f.wilkes_residual_rad ** 2
                              + f.stonehenge_residual_rad ** 2) / 2.0)
        assert abs(f.combined_rms_rad - expected) < 1e-12
        assert f.well_conditioned is True   # anchors are not antipodal


def test_closed_form_theta_minimizes_residual():
    # The fitted theta must beat neighbouring angles (it is the minimiser).
    anchor = stonehenge_anchor.build_anchor()
    ens = wilkes.default_ensemble()
    fam = spatialization.FAMILIES[3]
    f = C.fit_family(fam, anchor, ens)

    from cwatlas.r1082.partition import build_partition
    ico = build_partition().ico
    c_w = ens.root_face_center_direction()
    c_w = c_w / np.linalg.norm(c_w)
    t_w = ens.selected().centroid_unit_vector()
    c_s = fam.map_route(anchor.tokens, ico=ico).centroid
    c_s = c_s / np.linalg.norm(c_s)
    t_s = anchor.anchor_unit_vector()

    def total(theta):
        # The closed form minimises the sum of squared chord distances
        # ||Rz(theta) c - t||^2 = 2 - 2<Rz(theta) c, t>.
        c, s = math.cos(theta), math.sin(theta)
        rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        def chord2(a, b):
            return float(np.dot(rz @ a - b, rz @ a - b))
        return chord2(c_w, t_w) + chord2(c_s, t_s)

    best = total(f.theta_rad)
    for delta in (-0.2, -0.05, -0.01, 0.01, 0.05, 0.2):
        assert total(f.theta_rad + delta) >= best - 1e-9


def test_f1_and_f3_are_indistinguishable_to_two_anchors():
    # With the default root face, ROOT_RELATIVE == DIRECT, so F1 and F3 fit
    # identically: two anchors CANNOT separate them (genuine under-determination).
    fit = C.fit_all()
    by = {f.family_name: f for f in fit.fits}
    f1, f3 = by["F1_CANONICAL_DIRECT_BE"], by["F3_CANONICAL_ROOTREL_BE"]
    assert abs(f1.combined_rms_rad - f3.combined_rms_rad) < 1e-15
    assert abs(f1.theta_rad - f3.theta_rad) < 1e-15


def test_dof_accounting_is_explicit():
    fit = C.fit_all()
    dof = fit.dof_report()
    assert dof["continuous_parameters_fitted"] == 1
    assert dof["anchor_count"] == 2
    assert dof["scalar_constraints"] == 4
    assert dof["continuous_determination"] == "OVER_DETERMINED"
    assert dof["family_determination"] == "UNDER_DETERMINED"
    assert dof["discrete_family_choices"] == 4


def test_determinism():
    f1 = C.fit_all()
    f2 = C.fit_all()
    assert f1.ranked_names() == f2.ranked_names()
    for a, b in zip(f1.fits, f2.fits):
        assert a.theta_rad == b.theta_rad
        assert a.combined_rms_rad == b.combined_rms_rad


# -- negatives --------------------------------------------------------------

def test_negative_underdetermined_is_alias_set_not_single_pick():
    fit = C.fit_all()
    # Family selection is under-determined: the result is an alias set.
    assert fit.result_class() == "CANDIDATE_ALIAS_SET"
    # The default retained set keeps every family (nothing excluded by 2 anchors).
    assert len(fit.retained()) == 4
    # A tied pair is always retained together: for EVERY band, F1 in the
    # retained set iff F3 is (they are indistinguishable to the anchors).
    for band in (0.0, 0.1, 0.3, 0.5, 1.0, 5.0):
        names = {f.family_name for f in fit.retained(band_rad=band)}
        assert (("F1_CANONICAL_DIRECT_BE" in names)
                == ("F3_CANONICAL_ROOTREL_BE" in names))


def test_negative_refuse_single_measured_pick():
    fit = C.fit_all()
    with pytest.raises(claims.R1082ClaimError):
        fit.refuse_single_measured_pick()


def test_negative_overparameterized_fit_refused():
    # More free parameters than the anchors constrain is refused.
    with pytest.raises(C.CalibrationError):
        C.refuse_overparameterized(5)          # 5 > 4 scalar constraints
    with pytest.raises(C.CalibrationError):
        C.refuse_overparameterized(6, 4)
    # At/under the constraint count is allowed (no raise).
    C.refuse_overparameterized(4)
    C.refuse_overparameterized(1)


def test_report_seals_claims():
    r = C.calibration_fit_report()
    assert r["phase_id"] == "P18"
    assert r["family_result_class"] == "CANDIDATE_ALIAS_SET"
    assert r["silent_single_pick"] == "REFUSED"
    assert r["overparameterized_fit"] == "REFUSED"
    assert r["evidence_class"] == "CALIBRATED_CANDIDATE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
