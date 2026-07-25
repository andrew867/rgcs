"""P11 -- Earth body-fixed root and orientation profiles: focused/negative."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import earth_frame as E


def test_body_fixed_root_defaults_are_canonical():
    root = E.EarthBodyFixedRoot()
    assert root.geocentre_m == (0.0, 0.0, 0.0)
    assert root.rotation_axis == (0.0, 0.0, 1.0)
    assert root.prime_meridian_dir == (1.0, 0.0, 0.0)
    assert root.crustal_anchor_m is None


def test_optional_crustal_anchor_is_accepted():
    root = E.EarthBodyFixedRoot(crustal_anchor_m=(6378137.0, 0.0, 0.0))
    assert root.crustal_anchor_m == (6378137.0, 0.0, 0.0)


def test_bad_root_axes_are_rejected():
    with pytest.raises(E.OrientationError):
        E.EarthBodyFixedRoot(rotation_axis=(0.0, 0.0, 0.0))
    with pytest.raises(E.OrientationError):
        E.EarthBodyFixedRoot(prime_meridian_dir=(0.0, 0.0, 0.0))


def test_identity_profile_is_the_identity_mapping():
    prof = E.get_profile("IDENTITY@1.0.0")
    v = (1234.0, -5678.0, 9012.0)
    app = E.apply_orientation(v, prof)
    assert np.allclose(app.output_vector, v)
    assert np.allclose(prof.rotation_matrix(), np.eye(3))


def test_switching_profile_changes_the_mapping_deterministically():
    v = (6378137.0, 0.0, 0.0)
    identity = E.apply_orientation(v, E.get_profile("IDENTITY@1.0.0"))
    nominal = E.apply_orientation(v, E.get_profile("IERS-NOMINAL@1.0.0"))
    v2 = E.apply_orientation(v, E.get_profile("IERS-NOMINAL@2.0.0"))
    # A different profile yields a different result...
    assert not np.allclose(identity.output_vector, nominal.output_vector)
    assert not np.allclose(nominal.output_vector, v2.output_vector)
    # ...and the same profile is deterministic and recorded.
    again = E.apply_orientation(v, E.get_profile("IERS-NOMINAL@1.0.0"))
    assert nominal.output_vector == again.output_vector
    assert nominal.matrix_hash == again.matrix_hash
    assert nominal.profile_key == "IERS-NOMINAL@1.0.0"


def test_versioned_profiles_are_distinct_records():
    assert "IERS-NOMINAL@1.0.0" in E.ORIENTATION_PROFILES
    assert "IERS-NOMINAL@2.0.0" in E.ORIENTATION_PROFILES
    m1 = E.get_profile("IERS-NOMINAL@1.0.0").matrix_hash()
    m2 = E.get_profile("IERS-NOMINAL@2.0.0").matrix_hash()
    assert m1 != m2


def test_orientation_is_reversible_round_trip():
    prof = E.get_profile("IERS-NOMINAL@2.0.0")
    v = (4000000.0, 3000000.0, 3000000.0)
    app = E.apply_orientation(v, prof)
    back = E.invert_orientation(app.output_vector, prof)
    assert np.allclose(back, v, atol=1e-6)


def test_unknown_profile_and_bad_vector_fail_safe():
    with pytest.raises(E.OrientationError):
        E.get_profile("NO-SUCH-PROFILE@9.9.9")
    with pytest.raises(E.OrientationError):
        E.apply_orientation((1.0, 2.0), E.get_profile("IDENTITY@1.0.0"))
    with pytest.raises(E.OrientationError):
        E.apply_orientation((1.0, float("nan"), 3.0),
                            E.get_profile("IDENTITY@1.0.0"))


def test_report_claims_nothing_physical():
    r = E.earth_frame_report()
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
