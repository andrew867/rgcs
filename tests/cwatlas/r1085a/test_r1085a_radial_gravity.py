"""R10.8.5A locks — shell stack, land zero, gravity field line, magnetics.

Every required behaviour of the corrected outer-in radial machinery:
the outer-in/inner-out invariant, the average-land-height shell-3 zero
(with every banned substitute refused), gravity-path deviation from the
geometric radial where the model predicts it, epoch-dependent magnetic
boundary deformation, and the ban on the core-centred spherical
shortcut in the production path."""

import math

import numpy as np
import pytest

from cwatlas.claims import ClaimError
from cwatlas.r1085a import gravity_field_line as gfl
from cwatlas.r1085a import land_zero as lz
from cwatlas.r1085a import magnetic_shell as ms
from cwatlas.r1085a import outer_in_radial as oir
from cwatlas.r1085a import shell_profile as sp


# --- ShellProfile ------------------------------------------------------

def test_profiles_cover_operational_stack_and_are_epoch_dependent():
    for p in sp.CANDIDATE_PROFILES:
        t = p.thicknesses_km(2025.0)
        assert tuple(t) == sp.OPERATIONAL_SHELLS
        assert all(v > 0 for v in t.values())
    ladder = sp.profile("ATMOSPHERIC_LADDER_V1")
    assert ladder.band(6).thickness_km(2035.0) != \
        ladder.band(6).thickness_km(2025.0)


def test_fitted_thickness_refused():
    with pytest.raises(ClaimError, match="never fitted"):
        sp.refuse_fitted_thickness()


def test_below_stack_shells_refused():
    p = sp.profile("UNIFORM_100KM_V1")
    with pytest.raises(ClaimError, match="below the land-zero"):
        p.band(2)


# --- outer-in / inner-out invariant ------------------------------------

def test_outer_in_and_inner_out_agree_everywhere():
    for p in sp.CANDIDATE_PROFILES:
        for s in sp.OPERATIONAL_SHELLS:
            for zeta in (0.0, 0.25, 0.9014, 1.0):
                r = oir.decode(s, zeta, p, 2025.0)
                assert r.invariant_residual_km < 1e-9
                # and the identity holds by construction:
                assert math.isclose(
                    r.stack_height_km - r.d_in_km,
                    p.inner_stack_below_km(s, 2025.0) + r.d_local_km,
                    abs_tol=1e-9)


def test_zeta_zero_is_inner_boundary_and_one_is_outer():
    p = sp.profile("UNIFORM_100KM_V1")
    lo = oir.decode(3, 0.0, p, 2025.0)
    hi = oir.decode(3, 1.0, p, 2025.0)
    assert lo.height_above_land_zero_km == 0.0          # shell-3 inner
    assert hi.height_above_land_zero_km == 100.0        # shell-3 outer
    assert hi.d_in_km < lo.d_in_km                      # Z inner -> outer


def test_zeta_from_octree_z():
    assert oir.zeta_from_octree_z(461) == pytest.approx(461.5 / 512.0)
    with pytest.raises(ClaimError):
        oir.zeta_from_octree_z(512)
    assert oir.zeta_under("ZETA_MIDBAND_V1", None) == 0.5


def test_core_centred_spherical_shortcut_refused_and_not_in_production():
    with pytest.raises(ClaimError, match="outer-shell geometry"):
        oir.refuse_geocentric_spherical_shortcut()
    r = oir.decode(3, 0.5, sp.profile("UNIFORM_100KM_V1"), 2025.0)
    assert r.radial_mode == "OUTER_IN_GRAVITY_FIELD_LINE"


# --- shell-3 zero: average land height ---------------------------------

def test_shell3_zero_uses_average_land_height_not_substitutes():
    ref = lz.land_zero()
    assert ref.vertical == "GRAVITY_VERTICAL"
    assert ref.mean_land_elevation_m in (840.0, 797.0)
    for banned in (lz.refuse_mean_sea_level_zero,
                   lz.refuse_spherical_radius_zero,
                   lz.refuse_geocentric_distance_zero,
                   lz.refuse_wgs84_altitude_zero):
        with pytest.raises(ClaimError, match="refused"):
            banned()
    # an untested MSL substitution would shift the zero by the mean
    # land elevation itself — declared, not hidden
    assert lz.msl_substitution_delta_m() == 840.0
    assert len(lz.all_land_zero_candidates()) == 2


# --- gravity field line ------------------------------------------------

def test_gravity_path_deviates_from_radial_where_predicted():
    """At mid-latitude the J2+centrifugal model predicts a bent field
    line; on the spin axis and in the equatorial plane, symmetry keeps
    it radial. Both predictions are checked, not asserted."""
    epoch = 2025.0
    r0 = 6.5e6
    mid = np.array([r0 * math.cos(math.radians(45.0)), 0.0,
                    r0 * math.sin(math.radians(45.0))])
    line = gfl.integrate_inward(mid, epoch, 100_000.0, step_m=1000.0)
    assert line.lateral_deviation_m > 50.0
    eq = gfl.integrate_inward(np.array([r0, 0.0, 0.0]), epoch,
                              100_000.0, step_m=1000.0)
    assert eq.lateral_deviation_m < 5.0
    assert gfl.deflection_from_radial_rad(mid, epoch) > \
        gfl.deflection_from_radial_rad(np.array([r0, 0.0, 0.0]), epoch)


def test_vertical_is_gravity_not_ellipsoid_normal():
    with pytest.raises(ClaimError, match="GRAVITY_VERTICAL"):
        gfl.refuse_ellipsoid_normal_vertical()
    assert gfl.GRAVITY_VERTICAL == "GRAVITY_VERTICAL"


def test_j2_is_epoch_dependent():
    assert gfl.j2(2025.0) != gfl.j2(1975.0)


# --- magnetic shell geometry -------------------------------------------

def test_magnetic_correction_is_epoch_dependent():
    m = ms.member("DIPOLE_B_MAGNITUDE")
    u = np.array([0.5, 0.5, math.sqrt(0.5)])
    r_2025 = ms.boundary_radius_m(u, 2025.0, 6.5e6, m)
    r_1975 = ms.boundary_radius_m(u, 1975.0, 6.5e6, m)
    assert abs(r_2025 - r_1975) > 1.0     # metres — the drift is real
    assert ms.dipole_moment(1975.0) != ms.dipole_moment(2025.0)
    assert not np.allclose(ms.dipole_axis(1975.0), ms.dipole_axis(2025.0))


def test_magnetic_family_is_bounded_and_blocked_members_refuse():
    active = ms.active_members()
    assert {m.member_id for m in active} == {
        "GRAVITY_ONLY", "DIPOLE_B_MAGNITUDE",
        "DIPOLE_SCALAR_POTENTIAL", "DIPOLE_INCLINATION"}
    for blocked in ("CRUST_CORRECTED", "CORE_PLUS_LITHOSPHERE"):
        m = ms.member(blocked)
        assert m.status == "BLOCKED_MISSING_DATA"
        with pytest.raises(ClaimError, match="none is fabricated"):
            m.m_scalar(np.array([6.4e6, 0, 0]), 2025.0)


def test_post_reveal_scalar_selection_refused():
    with pytest.raises(ClaimError, match="post-reveal"):
        ms.refuse_post_reveal_scalar_selection()


def test_magnetic_correction_takes_no_per_vector_argument():
    """The correction is a function of (position, epoch, member) only —
    there is no per-vector parameter anywhere in its signature."""
    import inspect
    params = set(inspect.signature(ms.boundary_radius_m).parameters)
    assert params == {"direction", "epoch_year", "nominal_radius_m",
                      "correction", "window_m"}
